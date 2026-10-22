"""REST iptalini gerçek SDK/core ve sentetik HTTP kapılarıyla doğrula.

Event kapıları Stop'u ağ veya araç beklemesinde kabul ettirir. HTTP cevabı
gelmeden bitiş iddia edilmemeli; sonra yeni araç/retry/fallback başlamamalı.
Kullanıcı verisi ve ücretli API kullanılmaz.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import httpx
import pytest

from app.bootstrap import create_core
from app.core.contracts import TaskStatus, ToolResult
from app.session import gemini
from app.session.model_tools import ModelTools
from app.session.text_chat import TextChat
from app.tasks.manager import TaskManager
from test_gemini import transport, reply, call, tools, stored_notes
from test_task_manager import registry_with

REAL_WAIT_RETRY = gemini.GeminiText._wait_retry


@pytest.mark.parametrize("prefix", [0, 1, 2])
@pytest.mark.parametrize("ending", ["tool", "503", "timeout"])
def test_rest_stop_during_http_waits_then_blocks_tools_retry_and_fallback(transport, taskvex_home, prefix, ending):
    entered, release = Event(), Event()
    def blocked(request):
        entered.set()
        assert release.wait(5)
        if ending == "timeout":
            return httpx.ReadTimeout("SECRET")
        if ending == "503":
            return httpx.Response(503, json={"error": {"code": 503}})
        return reply([call()])
    transport.responses = [*[httpx.Response(503, json={"error": {"code": 503}}) for _ in range(prefix)], blocked]
    with create_core() as core, ThreadPoolExecutor(max_workers=1) as pool:
        chat = TextChat(core)
        try:
            running = pool.submit(chat.run, "Add", gemini.DEFAULT_MODEL, request_id="rest-1")
            assert entered.wait(3) and not chat.stop("old")["ok"]
            accepted = chat.stop("rest-1")
            assert accepted["ok"] and not accepted["completed"] and accepted["waiting_for"] == "http_response"
            assert chat.stop("rest-1")["ok"]  # aynı sinyal; ikinci işlem değildir
            assert chat.busy and not running.done() and not chat.close()
            assert not chat.run("Other", gemini.DEFAULT_MODEL)["ok"]
            release.set()
            report = running.result(3)
            assert report["stopped"] and report["completed"] and not report["ok"]
            assert report["request_id"] == "rest-1" and report["tool_results"] == []
            assert not chat.busy and not chat.stop("rest-1")["ok"]
            assert not (taskvex_home / "notes.json").exists()
            assert len(transport.requests) == prefix + 1 and "SECRET" not in str(report)
            assert transport.clients[0]._api_client._httpx_client.is_closed
        finally:
            release.set()
            chat.close()


def test_rest_stop_before_first_request_performs_no_http(transport):
    with create_core() as core, gemini.GeminiText(tools(core)) as model:
        assert model.stop() == "turn_completion"
        assert model.run("Hi")["stopped"]
    assert transport.requests == []


def test_rest_stop_wakes_backoff_without_next_attempt(transport, monkeypatch):
    waiting = Event()
    def wait_retry(self, seconds):
        waiting.set()
        REAL_WAIT_RETRY(self, 5)
    monkeypatch.setattr(gemini.GeminiText, "_wait_retry", wait_retry)
    transport.responses = [httpx.Response(503, json={"error": {"code": 503}})]
    with create_core() as core, gemini.GeminiText(tools(core)) as model, ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(model.run, "Hi")
        assert waiting.wait(3) and model.stop() == "turn_completion"
        assert running.result(2)["stopped"]
    assert len(transport.requests) == 1


def test_rest_stop_after_note_commit_preserves_verified_result(transport, taskvex_home):
    entered, release = Event(), Event()
    def blocked(request):
        entered.set()
        assert release.wait(5)
        return reply([call(args={"text": "Must not run"}, call_id="second")])
    transport.responses = [reply([call()]), blocked]
    with create_core() as core, ThreadPoolExecutor(max_workers=1) as pool:
        chat = TextChat(core)
        try:
            running = pool.submit(chat.run, "Add", gemini.DEFAULT_MODEL, request_id="committed")
            assert entered.wait(3) and len(stored_notes(taskvex_home)) == 1
            assert chat.stop("committed")["ok"]
            release.set()
            report = running.result(3)
            assert report["stopped"] and report["tool_results"][0]["result"]["verified"]
            assert report["tool_results"][0]["id"] == "provider-1"
            assert len(stored_notes(taskvex_home)) == 1 and len(transport.requests) == 2
        finally:
            release.set()
            chat.close()


@pytest.mark.parametrize("status", ["cancelled", "succeeded", "unresolved", "cancel_error"])
def test_rest_stop_preserves_actual_tool_outcome_and_prevents_next_batch_call(transport, monkeypatch, status):
    entered, release = Event(), Event()
    executed = []
    def handler(args, context):
        entered.set()
        assert release.wait(5)
        executed.append(context.task_id)
        return ToolResult(task_id=context.task_id,
            status=TaskStatus.CANCELLED if status == "cancelled" else TaskStatus.SUCCEEDED,
            verified=status != "cancelled")
    transport.responses = [reply([call("test.run", {}, "first"), call("test.run", {}, "second")])]
    with TaskManager(registry_with(handler), authorize=lambda req, spec: True) as core, ThreadPoolExecutor(max_workers=1) as pool:
        bound = ModelTools(core, principal="test", session_id="rest-stop", allowed_tools=("test.run",))
        original = bound.result
        def result(task_id, **kwargs):
            record = original(task_id, **kwargs)
            if status == "unresolved":
                record.update(status="running", result=None)
            return record
        monkeypatch.setattr(bound, "result", result)
        if status == "cancel_error":
            def broken(task_id):
                raise RuntimeError("SECRET")
            monkeypatch.setattr(bound, "cancel", broken)
        with gemini.GeminiText(bound) as model:
            try:
                running = pool.submit(model.run, "Run")
                assert entered.wait(3) and model.stop() == "tool_result"
                assert not running.done()
                release.set()
                report = running.result(3)
                uncertain = status in {"unresolved", "cancel_error"}
                assert report["unknown"] is uncertain and report["stopped"] is not uncertain
                assert len(report["tool_results"]) == 1 and len(executed) == 1
                assert len(transport.requests) == 1 and "SECRET" not in str(report)
                if status == "succeeded":
                    assert report["tool_results"][0]["result"]["verified"]
            finally:
                release.set()


def test_old_rest_stop_does_not_affect_next_turn(transport):
    entered, release = Event(), Event()
    def blocked(request):
        entered.set()
        assert release.wait(5)
        return reply([{"text": "Second answer"}])
    transport.responses = [reply([{"text": "First answer"}]), blocked]
    with create_core() as core, ThreadPoolExecutor(max_workers=1) as pool:
        chat = TextChat(core)
        try:
            assert chat.run("Hi", gemini.DEFAULT_MODEL, request_id="first")["ok"]
            running = pool.submit(chat.run, "Hi again", gemini.DEFAULT_MODEL, request_id="second")
            assert entered.wait(3) and not chat.stop("first")["ok"]
            release.set()
            report = running.result(3)
            assert report["ok"] and report["request_id"] == "second" and not report.get("stopped")
        finally:
            release.set()
            chat.close()
