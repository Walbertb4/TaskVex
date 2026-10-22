"""Gerçek Gemini SDK ve HTTP seri hale getirmesiyle, dış ağa çıkmadan dene.

Yalnız HTTP taşıması MockTransport'tur; SDK modelleri, şemalar, registry,
policy, worker ve geçici not dosyası gerçektir. Bu testler canlı hesap kabulü
değildir. Sahte hata içindeki SECRET sonucu/logu kirletmemelidir.
"""

import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import httpx
import pytest

from app.bootstrap import create_core
from app.core.contracts import ContractError
from app.session import gemini
from app.session.model_tools import ModelTools
from app.session.text_chat import TextChat
from app.session.catalog import load_live_catalog
from app.storage.json_store import JsonStore


def reply(parts, finish="STOP"):
    """SDK'nin gerçekten ayrıştıracağı Gemini REST yanıtını oluştur."""
    return {"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": finish}]}


def call(name="notes.add", args=None, call_id="provider-1"):
    """Düşünme imzası sonraki istekte aynen taşınmalı; çağrı id'si isteğe bağlı."""
    data = {"name": name, "args": {"text": "Test note"} if args is None else args}
    if call_id is not None:
        data["id"] = call_id
    return {"functionCall": data, "thoughtSignature": "c2ln"}


@pytest.fixture
def transport(monkeypatch):
    """Gerçek SDK istemcisine yalnız bellek içi HTTP taşıması tak."""
    state = SimpleNamespace(responses=[], requests=[], clients=[], options=[], urls=[], delays=[])
    original = gemini.genai.Client
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini.GeminiText, "_wait_retry", lambda self, seconds: state.delays.append(seconds))

    def handle(request):
        state.requests.append(json.loads(request.content) if request.content else None)
        state.urls.append(str(request.url))
        assert state.responses, "Unexpected extra HTTP request / retry"
        response = state.responses.pop(0)
        if callable(response):
            response = response(request)
        if isinstance(response, Exception):
            raise response
        if isinstance(response, httpx.Response):
            return response
        return httpx.Response(200, json=response)

    def create(**kwargs):
        options = kwargs["http_options"]
        state.options.append(options)
        options.client_args = {"transport": httpx.MockTransport(handle)}
        client = original(**kwargs)
        state.clients.append(client)
        return client

    monkeypatch.setattr(gemini.genai, "Client", create)
    return state


def tools(core):
    """Gerçek yerel policy altında yalnız bu denemeye gereken araçları aç."""
    return ModelTools(core, principal="local-user", session_id="test-session",
                      allowed_tools=("apps.catalog", "notes.add", "notes.list"))


def stored_notes(home):
    """Not dosyasının gerçekten var olduğunu doğrula; eksik dosyayı boş sayma."""
    document = JsonStore(home / "notes.json").read()
    assert document is not None
    return document["notes"]


def test_text_only_and_closed_client(transport):
    transport.responses = [reply([{"text": "Merhaba"}])]
    with create_core() as core:
        with gemini.GeminiText(tools(core)) as model:
            response = model.run("Merhaba")
    assert response.pop("elapsed_ms") >= 0
    details = response.pop("model_attempt_details")
    assert len(details) == 1 and details[0]["outcome"] == "response" and details[0]["elapsed_ms"] >= 0
    assert response == {"ok": True, "text": "Merhaba", "tool_results": [],
                        "model": gemini.DEFAULT_MODEL, "model_attempts": [gemini.DEFAULT_MODEL]}
    assert transport.clients[0]._api_client._httpx_client.is_closed
    assert transport.options[0].timeout == 30_000
    assert transport.options[0].retry_options.attempts == 1


@pytest.mark.parametrize("call_id", ["provider-1", None])
def test_sdk_tool_roundtrip_preserves_signature_and_core_schema(transport, taskvex_home, call_id):
    transport.responses = [reply([call(call_id=call_id)]), reply([{"text": "Not kaydedildi."}])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Test note notunu ekle")
    assert result["ok"] and result["tool_results"][0]["result"]["verified"]
    assert len(stored_notes(taskvex_home)) == 1
    first, second = transport.requests
    assert "automaticFunctionCalling" not in first  # İstemci ayarı sunucuya araç yürütücüsü göndermez.
    declarations = first["tools"][0]["functionDeclarations"]
    note = next(item for item in declarations if item["name"] == "notes.add")
    schema = note.get("parametersJsonSchema", note.get("parameters_json_schema"))
    assert schema["additionalProperties"] is False
    assert second["contents"][1]["parts"][0]["thoughtSignature"] == "c2ln"
    outcome = second["contents"][2]["parts"][0]["functionResponse"]
    assert outcome["response"]["status"] == "succeeded"
    if call_id is not None:
        assert outcome["id"] == call_id and outcome["response"]["id"] == call_id
    else:
        assert outcome["response"]["id"].startswith("local:")


def test_repeated_provider_call_does_not_add_second_note(transport, taskvex_home):
    transport.responses = [reply([call()]), reply([call()]), reply([{"text": "Bitti"}])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Bir not ekle")
    assert result["ok"]
    assert result["tool_results"][0]["task_id"] == result["tool_results"][1]["task_id"]
    assert len(stored_notes(taskvex_home)) == 1


def test_independent_user_turns_can_reuse_a_provider_call_id(transport, taskvex_home):
    """Yeni kullanıcı isteğini, önceki turun aynı id'li çağrısının replay'i sanma."""
    transport.responses = [reply([call()]), reply([{"text": "İlk not eklendi"}]),
                           reply([call()]), reply([{"text": "İkinci not eklendi"}])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        first = model.run("Bir Test note ekle")
        second = model.run("Bir Test note daha ekle")
    assert first["ok"] and second["ok"]
    assert len(stored_notes(taskvex_home)) == 2
    assert first["tool_results"][0]["task_id"] != second["tool_results"][0]["task_id"]
    assert first["tool_results"][0]["id"] == second["tool_results"][0]["id"] == "provider-1"


@pytest.mark.parametrize("part", [call(name="shell.run"), call(args={"text": 7}),
                                  call(args={"text": "ok", "path": "SECRET"}),
                                  call(call_id=" ")])
def test_invalid_or_unexposed_call_never_writes(transport, taskvex_home, part):
    transport.responses = [reply([part])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Bir şey yap")
    assert not result["ok"] and "SECRET" not in json.dumps(result)
    assert not (taskvex_home / "notes.json").exists()
    assert len(transport.requests) == 1


@pytest.mark.parametrize("code,expected", [(400, "invalid_request"), (401, "authentication_failed"),
                                          (402, "billing_required"), (403, "permission_denied"),
                                          (404, "model_unavailable"), (429, "quota_exceeded")])
def test_http_errors_are_redacted_and_not_retried(transport, code, expected):
    transport.responses = [httpx.Response(code, json={"error": {"code": code, "message": "SECRET"}})]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Merhaba")
    assert result["code"] == expected and "SECRET" not in json.dumps(result)
    assert result["http_status"] == code
    assert len(transport.requests) == 1


@pytest.mark.parametrize("status,reason", [("INVALID_ARGUMENT", "API_KEY_INVALID"),
                                          ("PERMISSION_DENIED", "API_KEY_SERVICE_BLOCKED"),
                                          ("SECRET", "SECRET")])
def test_provider_diagnostics_allow_only_known_codes(transport, status, reason):
    transport.responses = [httpx.Response(400, json={"error": {
        "code": 400, "status": status, "message": "SECRET",
        "details": [{"reason": reason, "metadata": {"key": "SECRET"}}],
    }})]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        report = model.run("Katalog")
    assert "SECRET" not in json.dumps(report)
    if reason != "SECRET":
        assert report["provider_status"] == status and report["provider_reason"] == reason
    else:
        assert "provider_status" not in report and "provider_reason" not in report


def test_malformed_provider_details_do_not_break_error_reporting(transport):
    transport.responses = [httpx.Response(400, json={"error": {
        "code": 400, "message": "SECRET", "details": [None, "SECRET", {"reason": ["SECRET"]}],
    }})]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        report = model.run("Katalog")
    assert report["http_status"] == 400 and "SECRET" not in json.dumps(report)


@pytest.mark.parametrize("error,expected", [(httpx.ReadTimeout("SECRET"), "network_timeout"),
                                           (httpx.ConnectError("SECRET"), "network_error")])
def test_network_errors_stop_at_retry_limit(transport, error, expected):
    transport.responses = [error, error, error]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Merhaba")
    assert result["code"] == expected and "SECRET" not in json.dumps(result)
    assert len(transport.requests) == 3 and len(transport.delays) == 2


def test_network_failure_after_commit_keeps_known_result(transport, taskvex_home):
    transport.responses = [reply([call()]), httpx.ReadTimeout("SECRET")]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Bir not ekle")
    assert not result["ok"] and result["tool_results"][0]["status"] == "succeeded"
    assert len(stored_notes(taskvex_home)) == 1
    assert len(transport.requests) == 2 and transport.delays == []


@pytest.mark.parametrize("status", [408, 500, 502, 503, 504])
def test_transient_error_retries_primary_before_fallback(transport, status):
    """İlk hata sonrası aynı model başarılıysa alternatif çağrılmamalı."""
    transport.responses = [httpx.Response(status, json={"error": {"code": status}}),
                           reply([{"text": "Bitti"}])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Merhaba")
    assert result["ok"] and result["model_attempts"] == [gemini.DEFAULT_MODEL] * 2
    assert transport.requests[0] == transport.requests[1]
    assert 1 <= transport.delays[0] <= 1.25


def test_fallback_executes_note_once_and_keeps_model_for_tool_response(transport, taskvex_home):
    """Fallback öncesi araç yok; sonrası imzalar yalnız aynı modele gönderilir."""
    transport.responses = [httpx.Response(503, json={"error": {"code": 503}}),
                           httpx.ReadTimeout("SECRET"), reply([call()]), reply([{"text": "Bitti"}])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Bir not ekle")
    assert result["ok"] and len(stored_notes(taskvex_home)) == 1
    assert result["model"] == gemini.FALLBACK_MODEL
    assert result["model_attempts"] == [gemini.DEFAULT_MODEL] * 2 + [gemini.FALLBACK_MODEL] * 2
    assert all(name in url for name, url in zip(result["model_attempts"], transport.urls))
    assert transport.requests[0] == transport.requests[1] == transport.requests[2]
    assert transport.requests[3]["contents"][1]["parts"][0]["thoughtSignature"] == "c2ln"
    assert 1 <= transport.delays[0] <= 1.25 and 2 <= transport.delays[1] <= 2.25


def test_exhausted_fallback_stops_and_next_run_starts_with_primary(transport):
    transport.responses = [*[httpx.Response(503, json={"error": {"code": 503}}) for _ in range(3)],
                           reply([{"text": "Bitti"}])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        failed = model.run("Merhaba")
        next_run = model.run("Tekrar merhaba")
    assert failed["http_status"] == 503 and failed["model"] == gemini.FALLBACK_MODEL
    assert len(failed["model_attempts"]) == 3
    assert next_run["ok"] and next_run["model_attempts"] == [gemini.DEFAULT_MODEL]


@pytest.mark.parametrize("status", [401, 403, 429, 503])
def test_error_after_note_commit_never_retries_or_switches(transport, taskvex_home, status):
    transport.responses = [reply([call()]), httpx.Response(status, json={"error": {"code": status}})]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Bir not ekle")
    assert not result["ok"] and result["tool_results"][0]["status"] == "succeeded"
    assert len(stored_notes(taskvex_home)) == 1
    assert result["model_attempts"] == [gemini.DEFAULT_MODEL] * 2
    assert transport.delays == []


def test_explicit_model_retries_without_switching_to_another_model(transport):
    transport.responses = [httpx.Response(503, json={"error": {"code": 503}}) for _ in range(2)]
    with create_core() as core, gemini.GeminiText(tools(core), model=gemini.FALLBACK_MODEL) as model:
        result = model.run("Merhaba")
    assert not result["ok"] and result["model_attempts"] == [gemini.FALLBACK_MODEL] * 2


def test_smoke_report_preserves_actual_fallback_model(transport, monkeypatch, capsys):
    """CLI istenen modeli, gerçekten yanıtlayan modelin üzerine yazmamalı."""
    transport.responses = [httpx.Response(503, json={"error": {"code": 503}}),
                           httpx.Response(503, json={"error": {"code": 503}}),
                           reply([call("apps.catalog", {})]), reply([{"text": "Bitti"}])]
    monkeypatch.setattr("sys.argv", ["gemini_smoke"])
    entry = runpy.run_path(str(Path(__file__).with_name("gemini_smoke.py")))
    assert entry["main"]() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["requested_model"] == gemini.DEFAULT_MODEL
    assert report["model"] == gemini.FALLBACK_MODEL and report["acceptance_verified"]


@pytest.mark.parametrize("text", [None, {}, "", "  ", "a" * 20001])
def test_native_chat_rejects_invalid_text_without_network(transport, text):
    with create_core() as core:
        chat = TextChat(core)
        assert not chat.run(text, gemini.DEFAULT_MODEL)["ok"]
    assert transport.requests == [] and transport.clients == []


def test_native_chat_uses_host_allowlist_and_releases_client(transport, taskvex_home):
    transport.responses = [reply([call()]), reply([{"text": "Bitti"}])]
    with create_core() as core:
        chat = TextChat(core)
        report = chat.run("Bir not ekle", gemini.DEFAULT_MODEL)
        assert not chat.busy and report["ok"] and report["completed"]
        assert chat.close() and not chat.run("Merhaba", gemini.DEFAULT_MODEL)["ok"]
    assert len(stored_notes(taskvex_home)) == 1
    declarations = transport.requests[0]["tools"][0]["functionDeclarations"]
    assert {item["name"] for item in declarations} == {"apps.catalog", "system.status", "notes.add", "notes.list", "notes.update", "notes.delete"}
    assert transport.clients[0]._api_client._httpx_client.is_closed


def test_native_chat_missing_key_and_unknown_exception_are_safe(transport, monkeypatch):
    with create_core() as core:
        chat = TextChat(core)
        monkeypatch.setenv("GEMINI_API_KEY", "")
        assert "Save it in Settings" in chat.run("Merhaba", gemini.DEFAULT_MODEL)["error"]
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        transport.responses = [RuntimeError("SECRET")]
        report = chat.run("Merhaba", gemini.DEFAULT_MODEL)
        assert report["unknown"] and "SECRET" not in json.dumps(report)
        assert not chat.busy


def test_native_chat_rejects_concurrent_work_and_close_without_blocking(transport):
    with create_core() as core:
        chat = TextChat(core)
        with chat._lock:
            assert not chat.run("Merhaba", gemini.DEFAULT_MODEL)["ok"]
            assert not chat.close()
        assert not chat.run("Merhaba", "unsupported-model")["ok"]
    assert transport.requests == []


def test_chat_without_notes_confirmation_still_answers_with_restricted_tools(transport):
    transport.responses = [reply([{"text": "Merhaba"}])]
    with create_core() as core:
        report = TextChat(core).run("Merhaba", gemini.DEFAULT_MODEL, notes_ready=False)
    assert report["ok"]
    assert {d["name"] for d in transport.requests[0]["tools"][0]["functionDeclarations"]} == {"apps.catalog", "system.status"}


def test_unconfirmed_notes_cannot_be_written_by_model(transport, taskvex_home):
    transport.responses = [reply([call()])]
    with create_core() as core:
        report = TextChat(core).run("Bir not ekle", gemini.DEFAULT_MODEL, notes_ready=False)
    assert not report["ok"] and not (taskvex_home / "notes.json").exists()


def test_live_catalog_filters_capabilities_and_loads_all_pages(transport):
    transport.responses = [{"models": [
        {"name": "models/text-only", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/fake-live-name", "supportedGenerationMethods": []},
        {"name": "models/future-live-a", "displayName": "Future A", "supportedGenerationMethods": ["bidiGenerateContent"]},
    ], "nextPageToken": "second"}, {"models": [
        {"name": "models/future-live-b", "supportedGenerationMethods": ["bidiGenerateContent"]},
        {"name": "models/future-live-a", "displayName": "Future A", "supportedGenerationMethods": ["bidiGenerateContent"]},
        {"name": "models/invalid/path", "supportedGenerationMethods": ["bidiGenerateContent"]},
    ]}]
    result = load_live_catalog()
    assert result["ok"] and [item["id"] for item in result["models"]] == ["future-live-a", "future-live-b"]
    assert all(item["live"] for item in result["models"])
    assert "pageToken=second" in transport.urls[-1]
    assert transport.clients[0]._api_client._httpx_client.is_closed


@pytest.mark.parametrize("response", [{"models": []}, {"models": [{"name": "models/a-live-name"}]}])
def test_empty_live_catalog_never_invents_models(transport, response):
    transport.responses = [response]
    assert load_live_catalog() == {"ok": True, "completed": True, "models": []}


@pytest.mark.parametrize("error", [httpx.Response(403, json={"error": {"code": 403, "message": "SECRET"}}),
                                  httpx.ReadTimeout("SECRET")])
def test_catalog_error_is_redacted_and_client_closed(transport, error):
    transport.responses = [error]
    report = load_live_catalog()
    assert not report["ok"] and "SECRET" not in json.dumps(report) and "models" not in report
    assert len(transport.requests) == 1 and transport.clients[0]._api_client._httpx_client.is_closed


def test_catalog_page_limit_rejects_partial_list(transport):
    transport.responses = [{"models": [{"name": "models/live-model", "supportedGenerationMethods": ["bidiGenerateContent"]}],
                            "nextPageToken": f"page-{i}"} for i in range(5)]
    report = load_live_catalog()
    assert not report["ok"] and "models" not in report and len(transport.requests) == 5


def test_provider_failure_exposes_safe_timing_and_http_code(transport, monkeypatch):
    """Bir HTTP denemesi ile toplam süre farklıdır; ham hata saklanmaz."""
    ticks = iter([10, 11, 13, 14])
    monkeypatch.setattr(gemini, "perf_counter", lambda: next(ticks))
    transport.responses = [httpx.Response(429, json={"error": {"code": 429, "message": "SECRET"}})]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        report = model.run("Merhaba")
    assert report["elapsed_ms"] == 4000
    assert report["model_attempt_details"] == [{"model": gemini.DEFAULT_MODEL,
        "outcome": "http_error", "http_status": 429, "elapsed_ms": 2000}]
    assert "SECRET" not in json.dumps(report) and len(transport.requests) == 1


def test_add_delete_add_works_with_reused_provider_id_in_independent_turns(transport, taskvex_home):
    """Son not silinince yeni model isteği eski tamamlanmış göreve karışmasın."""
    from app.core.contracts import ToolRequest
    transport.responses = [reply([call()]), reply([{"text": "Saved"}]),
                           reply([call(args={"text": "Second note"})]), reply([{"text": "Saved again"}])]
    with create_core() as core:
        chat = TextChat(core)
        assert chat.run("Add first note", gemini.DEFAULT_MODEL)["ok"]
        original = stored_notes(taskvex_home)[0]
        deleted = core.submit(ToolRequest(request_id="delete-between-model-turns", source="desktop",
            principal="local-user", tool="notes.delete", arguments={"id": original["id"]}))
        finished = core.wait(deleted.task_id, timeout=3)
        assert finished.result is not None and finished.result.verified
        assert stored_notes(taskvex_home) == []
        assert chat.run("Add second note", gemini.DEFAULT_MODEL)["ok"]
    current = stored_notes(taskvex_home)
    assert len(current) == 1 and current[0]["text"] == "Second note" and current[0]["id"] != original["id"]


@pytest.mark.parametrize("payload", [{}, reply([]), reply([{"text": "Kısmi"}], "MAX_TOKENS"),
                                     reply([{"text": "Gizli düşünce", "thought": True}])])
def test_incomplete_or_empty_model_output_is_not_success(transport, payload):
    transport.responses = [payload]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        assert not model.run("Merhaba")["ok"]


def test_turn_limit_stops_before_more_tools_execute(transport, monkeypatch):
    monkeypatch.setattr(gemini, "MAX_REQUESTS", 2)
    transport.responses = [reply([call("apps.catalog", {}, "c1")]),
                           reply([call("apps.catalog", {}, "c2")])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        result = model.run("Kataloğu oku")
    assert result["code"] == "turn_limit" and len(result["tool_results"]) == 1


def test_missing_key_fails_before_creating_client(transport, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY")
    with create_core() as core, pytest.raises(ContractError, match="missing"):
        gemini.GeminiText(tools(core))
    assert transport.clients == [] and transport.requests == []


@pytest.mark.parametrize("status,expected", [("running", "task_pending"),
                                            ("cancel_requested", "task_pending"),
                                            ("unknown", "tool_unknown"),
                                            ("cancelled", "tool_cancelled")])
def test_unfinished_or_uncertain_tool_does_not_continue_model_turn(transport, monkeypatch, status, expected):
    """Zamanlama sınırını değiştir; adaptörün sahte final sonuç göndermediğini dene."""
    transport.responses = [reply([call("apps.catalog", {})])]
    with create_core() as core:
        bound = tools(core)
        original = bound.result

        def result(task_id, **kwargs):
            outcome = original(task_id, timeout=2)
            outcome["status"] = status
            outcome["result"] = None if status in {"running", "cancel_requested"} else {
                "status": status, "verified": False,
            }
            return outcome

        monkeypatch.setattr(bound, "result", result)
        with gemini.GeminiText(bound) as model:
            report = model.run("Katalog")
    assert report["code"] == expected and report["tool_results"][0]["status"] == status
    assert len(transport.requests) == 1


def test_tool_call_limit_rejects_entire_oversized_batch(transport, monkeypatch, taskvex_home):
    monkeypatch.setattr(gemini, "MAX_TOOL_CALLS", 1)
    transport.responses = [reply([call(call_id="one"), call(call_id="two")])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        report = model.run("Not ekle")
    assert report["code"] == "turn_limit" and report["tool_results"] == []
    assert not (taskvex_home / "notes.json").exists()


def test_changed_provider_call_id_content_is_not_reexecuted(transport, taskvex_home):
    transport.responses = [reply([call()]), reply([call(args={"text": "Different"})])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        report = model.run("Bir not ekle")
    assert report["code"] == "request_conflict"
    assert len(stored_notes(taskvex_home)) == 1


def test_parallel_calls_are_run_through_core_in_received_order(transport):
    transport.responses = [reply([call(), call("notes.list", {}, "read")]), reply([{"text": "Bitti"}])]
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        report = model.run("Not ekle ve listele")
    assert report["ok"] and len(report["tool_results"]) == 2
    assert len(report["tool_results"][1]["result"]["data"]["notes"]) == 1


def test_invalid_text_does_not_make_network_request(transport):
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        assert model.run(" ")["code"] == "invalid_text"
    assert transport.requests == []


@pytest.mark.parametrize("scenario", ["missing_key", "catalog", "notes", "notes_before_add"])
def test_smoke_entrypoint_isolated_and_checks_actual_tool_use(transport, monkeypatch, taskvex_home, scenario):
    """Kabul betiği gerçek kullanıcı dizinine dokunmasın, yalnız söze inanmasın."""
    args = ["gemini_smoke"]
    if scenario == "missing_key":
        monkeypatch.delenv("GEMINI_API_KEY")
    elif scenario == "catalog":
        # Akıcı yanıt var ama araç kullanılmadı: kabul testi geçmemelidir.
        transport.responses = [reply([{"text": "Notepad"}])]
    else:
        args.append("--notes")
        parts = [call(args={"text": "TaskVex API acceptance"}), call("notes.list", {}, "read")]
        if scenario == "notes_before_add":
            parts.reverse()
        transport.responses = [reply(parts), reply([{"text": "Bitti"}])]
    monkeypatch.setattr("sys.argv", args)
    entry = runpy.run_path(str(Path(__file__).with_name("gemini_smoke.py")))
    assert entry["main"]() == (0 if scenario == "notes" else 1)
    import os
    assert os.environ["TASKVEX_HOME"] == str(taskvex_home)
    assert not (taskvex_home / "notes.json").exists()
