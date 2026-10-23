"""Köprü doğrulaması; fake pencere testi gerçek WebView2 testi sayılmaz.

Gerçek core ve geçici kayıt kullanılır. JS serileştirmesi gözlenir; ayrı native
smoke betiği gerçek pencere, ES modülleri ve çift yönlü köprüyü çalıştırır.
"""

import json
from types import SimpleNamespace

import pytest

from app.bootstrap import create_core
from app.bridge.webview_bridge import NativeBridge
from app.config import get_data_home
from app.core.contracts import ContractError
from app.storage.json_store import JsonStore, StoreError
from app.storage.credentials import CredentialError


class FakeWindow:
    """İzinli çağrı ve JSON argümanlarını yakala; DOM yürütüyormuş gibi davranma."""

    def __init__(self):
        from webview.event import Event
        self.events = SimpleNamespace(closing=Event(self))
        self.calls = []
        self.fullscreen = False
        self.closed = False
        self.on_top = False

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

    def destroy(self):
        self.closed = True

    def evaluate_js(self, script):
        method, args = script.removeprefix("window.vex[").split("](...", 1)
        self.calls.append((json.loads(method), json.loads(args[:-1])))
        return True


@pytest.fixture
def bridge(monkeypatch):
    with create_core() as core:
        api = NativeBridge(core, JsonStore(get_data_home() / "settings.json"))
        # Test nesnesini açıkça enjekte et; üretimdeki Window tipini gevşetme.
        monkeypatch.setattr(api, "_window", FakeWindow())
        yield api


def ready(bridge):
    """Üretim UI'ın gönderdiği sürümlü bildirimi kullan."""
    return bridge.event("ui_ready", {"version": "1.0"})


def test_new_chat_clears_memory_only_after_ready_and_preserves_notes(bridge):
    """Yeni sohbet yanlış payload'da silmez; açık onay ayrı UI işidir."""
    bridge._chat._memory.remember('Synthetic fact', {'ok':True, 'text':'Understood'})
    assert not bridge.event('new_chat')['ok']
    assert ready(bridge)['ok']
    assert not bridge.event('new_chat', {})['ok']
    assert bridge._chat._memory.snapshot()
    assert bridge.event('new_chat') == {'ok':True, 'completed':True, 'memory_cleared':True}
    assert not bridge._chat._memory.snapshot()


def test_key_update_clears_memory_but_disconnect_preserves_it(bridge):
    """Aynı sohbet yeniden bağlanabilir; farklı hesap/anahtara tarihçe taşınmaz."""
    assert ready(bridge)['ok']
    bridge._chat._memory.remember('Synthetic fact', {'ok':True, 'text':'Understood'})
    assert bridge.event('disconnect')['ok'] and bridge._chat._memory.snapshot()
    assert bridge.event('apikey', 'SYNTHETIC-MEMORY-KEY')['ok']
    assert not bridge._chat._memory.snapshot()


@pytest.mark.parametrize('payload', [None, {}, 'text', {'request_id':''}, {'request_id':'x' * 129},
    {'request_id':'x', 'text':'UI cannot choose speech text'}])
def test_read_reply_accepts_only_host_reply_identity(bridge, payload):
    """Serbest metin/ek alan ve hazır olmayan host ses isteği başlatamaz."""
    assert bridge.event('read_reply', {'request_id':'missing'})['audio_error'] == 'invalid_speech_request'
    assert ready(bridge)['ok']
    assert bridge.event('read_reply', payload)['audio_error'] == 'invalid_speech_request'
    assert bridge.event('read_reply', {'request_id':'missing'})['audio_error'] == 'speech_not_pending'


def test_ready_is_idempotent_and_snapshot_omits_collections(bridge):
    assert ready(bridge)["ok"]
    before = list(bridge._window.calls)
    assert ready(bridge)["ok"]
    assert bridge._window.calls == before
    assert ("initApp", [{}]) in before
    assert ("online", [False, "MODEL OFFLINE"]) in before
    assert not bridge._store.path.exists()


def test_text_before_notes_confirmation_is_restricted_and_live_selection_is_separate(bridge, monkeypatch):
    """İlk not onayı sohbeti kapatmaz; Live tercihi REST modele gönderilmez."""
    assert not bridge.event("text", "Merhaba")["ok"]
    assert ready(bridge)["ok"]
    seen = []
    def chat(text, model, **kwargs):
        seen.append(kwargs["notes_ready"])
        return {"ok": True, "model": model}
    monkeypatch.setattr(bridge._chat, "run", chat)
    assert bridge.event("text", "Merhaba")["ok"] and seen == [False]
    bridge._live_models = {"future-live": {"id": "future-live"}}
    before = list(bridge._window.calls)
    assert bridge.event("model", "future-live")["completed"]
    assert bridge._window.calls == before
    assert bridge.event("text", "Merhaba")["model"] == "gemini-3.8-flash"
    assert not bridge.event("model", "unsupported")["ok"]


def test_live_catalog_error_invalidates_cached_choices(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    from app.bridge import webview_bridge
    monkeypatch.setattr(webview_bridge, "load_live_catalog", lambda: {"ok": True, "models": [{"id": "new-live"}]})
    assert bridge.event("query_catalog")["currentModel"] == "new-live"
    assert bridge.event("model", "new-live")["ok"]
    monkeypatch.setattr(webview_bridge, "load_live_catalog", lambda: {"ok": False, "error": "Not available"})
    assert not bridge.event("query_catalog")["ok"]
    assert not bridge.event("model", "new-live")["ok"]


def test_key_cannot_change_during_live_catalog_query(bridge, monkeypatch):
    """Başka hesaba ait katalog yeni anahtarın listesi diye önbelleğe girmesin."""
    from app.bridge import webview_bridge
    assert ready(bridge)["ok"]
    writes = []
    monkeypatch.setattr(bridge._credentials, "write", writes.append)
    def fetch():
        assert not bridge.event("apikey", "TEST-SECRET")["ok"]
        assert not bridge.event("query_catalog")["ok"]
        return {"ok": True, "completed": True, "models": []}
    monkeypatch.setattr(webview_bridge, "load_live_catalog", fetch)
    assert bridge.event("query_catalog")["ok"]
    assert writes == [] and not bridge._catalog_lock.locked()


def test_live_test_routes_selected_catalog_model_without_rest_fallback(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    assert not bridge.event("live_text", "Merhaba")["ok"]
    bridge._live_models = {"future-live": {"id": "future-live"}}
    assert bridge.event("model", "future-live")["ok"]
    seen = []
    def probe(text, model, **kwargs):
        seen.append((text, model))
        return {"ok": True, "mode": "live_latency_test"}
    monkeypatch.setattr(bridge._chat, "run_live", probe)
    assert bridge.event("live_text", "Merhaba")["ok"]
    assert seen == [("Merhaba", "future-live")] and bridge._model == "gemini-3.8-flash"


@pytest.mark.parametrize("payload", [None, {}, {"request_id": 3}, {"request_id": ""}, {"request_id": "x", "all": True}])
def test_stop_requires_explicit_live_request_identity(bridge, payload):
    assert not bridge.event("stop_task", payload)["ok"]


def test_live_envelope_and_stop_routing_do_not_wait_for_chat_lock(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    bridge._live_models = {"future-live": {"id": "future-live"}}
    bridge._live_model = "future-live"
    captured = []
    monkeypatch.setattr(bridge._chat, "run_live", lambda text, model, **kw: captured.append((text, kw)) or {"ok": True})
    assert bridge.event("live_text", {"text": "Hi", "request_id": "ui-1"})["ok"]
    assert captured[0][1]["request_id"] == "ui-1"
    assert not bridge.event("live_text", {"text": "Hi", "request_id": None})["ok"]
    with bridge._chat._lock:
        assert not bridge.event("stop_task", {"request_id": "old"})["ok"]


def test_rest_envelope_preserves_request_identity_and_rejects_malformed_data(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    captured = []
    monkeypatch.setattr(bridge._chat, "run", lambda text, model, **kw: captured.append((text, kw)) or {"ok": True})
    assert bridge.event("text", {"text": "Hi", "request_id": "rest-ui"})["ok"]
    assert captured == [("Hi", {"notes_ready": False, "request_id": "rest-ui", "profile": {}})]
    assert not bridge.event("text", {"text": "Hi", "request_id": None})["ok"]
    assert not bridge.event("text", {"text": "Hi", "request_id": "a", "principal": "other"})["ok"]


def test_active_chat_does_not_hold_bridge_lock_but_blocks_conflicting_actions(bridge):
    assert ready(bridge)["ok"]
    bridge._notes_ready = True
    with bridge._chat._lock:
        assert bridge.event("save", {"vol": 0.5})["ok"]
        assert not bridge.event("model", "gemini-3.5-flash-lite")["ok"]
        assert not bridge.event("retry_startup")["ok"]
        assert not bridge.event("shutdown")["ok"]
        result = bridge.event("notes_init", {"version": 1, "request_id": "blocked", "arguments": {"notes": None}})
        assert not result["ok"]
    assert not bridge._window.closed


def test_save_projects_settings_and_reloads_in_fresh_bridge(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    payload = {"theme": "#4fd8ff", "vol": 0, "sfx": False,
               "prof": {"pIns": "Türkçe </script> ' \\ 📝"},
               "notes": [{"t": "LOCAL ONLY"}], "skills": [], "routines": [], "apikey": "never-persist"}
    result = bridge.event("save", payload)
    assert result == {"ok": True, "completed": True, "saved": True}
    saved = bridge._store.read()
    assert saved["vol"] == 0 and saved["sfx"] is False
    assert not {"notes", "skills", "routines", "apikey"} & saved.keys()
    fresh = NativeBridge(bridge._core, bridge._store)
    window = FakeWindow()
    monkeypatch.setattr(fresh, "_window", window)
    assert ready(fresh)["ok"]
    assert ("initApp", [saved]) in window.calls


@pytest.mark.parametrize("payload", [None, [], {"vol": 2}, {"sfx": 1},
    {"prof": {"pApp": "yes"}}, {"conn": {"apikey": "secret"}},
    {"theme": "<img>"}, {"layout": [{"id": "evil"}]},
    {"layout": [{"id": "time", "c": "L", "on": 1, "sz": 1}] * 2}])
def test_bad_save_does_not_poison_file(bridge, payload):
    assert ready(bridge)["ok"]
    assert bridge.event("save", {"theme": "#4fd8ff"})["ok"]
    previous = bridge._store.path.read_bytes()
    assert bridge.event("save", payload)["ok"] is False
    assert bridge._store.path.read_bytes() == previous


def test_invalid_disk_settings_are_preserved_and_not_marked_ready(bridge):
    bridge._store.write({"vol": 5})
    previous = bridge._store.path.read_bytes()
    assert ready(bridge)["ok"] is False
    assert bridge._ready is False
    assert bridge.event("save", {"vol": 0.5})["ok"] is False
    assert bridge._store.path.read_bytes() == previous


def test_write_error_returns_no_fake_confirmation(bridge, monkeypatch):
    assert ready(bridge)["ok"]

    def fail(data):
        raise StoreError("write_failed", "secret")

    monkeypatch.setattr(bridge._store, "write", fail)
    result = bridge.event("save", {"theme": "#4fd8ff"})
    assert result["ok"] is False and "saved" not in result
    assert "secret" not in result["error"]


def test_unsupported_events_and_bad_handshake_are_rejected(bridge):
    for name, data in [("ui_ready", {}), ("note_add", "do not write"),
                       ("text", "hello"), ("apikey", "secret"), ("system_status", {})]:
        assert bridge.event(name, data)["ok"] is False
    assert not get_data_home().exists()


def test_api_key_storage_returns_only_status_and_does_not_mark_online(bridge, monkeypatch):
    memory = {"key": None}
    monkeypatch.setattr(bridge._credentials, "read", lambda: memory["key"])
    monkeypatch.setattr(bridge._credentials, "write", lambda value: memory.update(key=value))
    assert ready(bridge)["ok"]
    before = list(bridge._window.calls)
    assert bridge.event("query_apikey")["configured"] is False
    result = bridge.event("apikey", "TEST-SECRET")
    assert result == {"ok": True, "completed": True, "saved": True, "configured": True}
    assert bridge.event("query_apikey")["configured"] is True
    assert bridge._window.calls == before
    assert "TEST-SECRET" not in json.dumps(result)
    assert not bridge._store.path.exists()


def test_credential_error_and_bad_status_payload_do_not_expose_key(bridge, monkeypatch):
    assert ready(bridge)["ok"]

    def fail(value):
        raise CredentialError("TEST-SECRET")

    monkeypatch.setattr(bridge._credentials, "write", fail)
    result = bridge.event("apikey", "TEST-SECRET")
    assert result["ok"] is False and "TEST-SECRET" not in json.dumps(result)
    assert bridge.event("query_apikey", "TEST-SECRET")["ok"] is False
    assert bridge.event("apikey", None)["ok"] is False


def test_system_status_passes_real_core_and_safe_js_boundary(bridge):
    assert ready(bridge)["ok"]
    result = bridge.event("system_status")
    assert result["ok"] and result["data"]["cpu_percent"] is None
    with pytest.raises(ValueError):
        bridge._push("eval", "malicious")


def note_command(bridge, name, request_id, arguments):
    """UI'ın sürümlü zarfını kullan; test kimliği/araç adı payload'a eklenmez."""
    return bridge.event(name, {"version": 1, "request_id": request_id, "arguments": arguments})


def test_native_notes_require_transfer_and_survive_fresh_bridge(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    assert note_command(bridge, "note_add", "blocked", {"text": "No"})["ok"] is False
    initial = note_command(bridge, "notes_init", "read", {"notes": None})
    assert initial["data"] == {"notes": [], "migrated": False}
    assert not (get_data_home() / "notes.json").exists()
    migrated = note_command(bridge, "notes_init", "transfer", {"notes": [{"text": "Old", "done": True}]})
    assert migrated["ok"] and migrated["verified"] and migrated["completed"]
    old = migrated["data"]["notes"][0]
    added = note_command(bridge, "note_add", "add", {"text": "Old"})
    assert added["ok"] and added["data"]["note"]["id"] != old["id"]
    assert note_command(bridge, "note_add", "add", {"text": "Old"}) == added
    assert note_command(bridge, "note_done", "done", {"id": old["id"], "done": False})["data"]["note"]["done"] is False
    assert note_command(bridge, "note_del", "delete", {"id": old["id"]})["ok"]
    fresh = NativeBridge(bridge._core, bridge._store)
    monkeypatch.setattr(fresh, "_window", FakeWindow())
    assert ready(fresh)["ok"]
    reread = note_command(fresh, "notes_init", "fresh", {"notes": None})
    assert reread["data"] == {"migrated": True, "notes": [added["data"]["note"]]}


@pytest.mark.parametrize("payload", [None, {}, {"version": True, "request_id": "a", "arguments": {}},
    {"version": 1, "request_id": "a", "arguments": {}, "principal": "other"},
    {"version": 1, "request_id": "", "arguments": {"notes": []}}])
def test_note_command_rejects_bad_envelope_without_creating_store(bridge, payload):
    assert ready(bridge)["ok"]
    assert bridge.event("notes_init", payload)["ok"] is False
    assert not (get_data_home() / "notes.json").exists()


def test_note_timeout_is_unknown_and_does_not_resubmit(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    calls = []
    original = bridge._core.submit

    def submit(request):
        calls.append(request.request_id)
        return original(request)

    def timeout(*args, **kwargs):
        raise TimeoutError()

    monkeypatch.setattr(bridge._core, "submit", submit)
    monkeypatch.setattr(bridge._core, "wait", timeout)
    response = note_command(bridge, "notes_init", "timeout", {"notes": []})
    assert response["ok"] is False and response["unknown"] is True
    assert calls == ["timeout"]


def test_fullscreen_toggles_and_does_not_modify_saved_settings(bridge):
    assert bridge.event("fullscreen")["ok"]
    assert bridge._window.fullscreen is True
    assert bridge.event("fullscreen")["ok"]
    assert bridge._window.fullscreen is False
    assert not bridge._store.path.exists()


def test_shutdown_closes_worker_and_window(bridge):
    assert bridge.event("shutdown")["ok"]
    assert bridge._window.closed is True
    assert not bridge._core._worker.is_alive()


def test_busy_shutdown_preserves_window_and_reports_failure(bridge, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(bridge._core, "close", lambda: False)
        assert bridge.event("shutdown")["ok"] is False
        assert bridge._window.closed is False


@pytest.mark.parametrize("name", ["fullscreen", "shutdown", "restart"])
def test_window_controls_reject_payloads(bridge, name):
    assert bridge.event(name, {"unexpected": True})["ok"] is False
    assert bridge._window.closed is False and bridge._window.fullscreen is False


def test_restart_requests_new_process_only_after_worker_stops(bridge):
    assert bridge.event("restart")["ok"]
    assert bridge._restart_requested is True and bridge._window.closed is True
    assert not bridge._core._worker.is_alive()


def test_failed_restart_close_does_not_leave_a_deferred_restart(bridge, monkeypatch):
    def fail():
        raise RuntimeError("Window close failed")

    monkeypatch.setattr(bridge._window, "destroy", fail)
    assert bridge.event("restart")["ok"] is False
    assert bridge._restart_requested is False


@pytest.mark.parametrize("semantic", [False, True])
def test_startup_repair_preserves_original_and_valid_profile(bridge, semantic):
    bridge._store.path.parent.mkdir(parents=True, exist_ok=True)
    if semantic:
        bridge._store.write({"vol": 9, "theme": "#4fd8ff", "prof": {"pIns": "Keep profile"}})
    else:
        bridge._store.path.write_bytes(b'{broken private data')
    original = bridge._store.path.read_bytes()
    issue = ready(bridge)
    assert issue["ok"] is False and issue["recoverable"] is True
    assert bridge._ready is False
    assert ("startupStatus", [{k: issue[k] for k in ["ok", "code", "message", "recoverable"]}]) in bridge._window.calls
    assert "private" not in issue["message"]
    assert bridge.event("retry_startup")["ok"] is False
    assert bridge._store.path.read_bytes() == original
    assert bridge.event("recover_settings", {"confirmed": True})["ok"] is True
    backups = list(bridge._store.path.parent.glob("settings.json.*.corrupt"))
    assert len(backups) == 1 and backups[0].read_bytes() == original
    repaired = bridge._store.read()
    assert repaired["vol"] == 0.8
    if semantic:
        assert repaired["prof"] == {"pIns": "Keep profile"} and repaired["theme"] == "#4fd8ff"
    assert bridge._ready is True
    assert ("startupStatus", [{"ok": True}]) in bridge._window.calls


@pytest.mark.parametrize("confirmation", [None, {}, {"confirmed": False}, {"confirmed": 1}, True])
def test_repair_requires_explicit_confirmation(bridge, confirmation):
    bridge._store.path.parent.mkdir(parents=True)
    bridge._store.path.write_bytes(b"broken")
    assert not ready(bridge)["ok"]
    assert not bridge.event("recover_settings", confirmation)["ok"]
    assert bridge._store.path.read_bytes() == b"broken"
    assert not list(bridge._store.path.parent.glob("*.corrupt"))


def test_newer_settings_version_cannot_be_repaired_as_corruption(bridge):
    bridge._store.path.parent.mkdir(parents=True)
    original = b'{"version":2,"data":{"new_feature":true}}'
    bridge._store.path.write_bytes(original)
    issue = ready(bridge)
    assert issue["code"] == "unsupported_version" and issue["recoverable"] is False
    assert not bridge.event("recover_settings", {"confirmed": True})["ok"]
    assert bridge._store.path.read_bytes() == original
    assert not list(bridge._store.path.parent.glob("*.corrupt"))


def test_access_error_is_retryable_but_not_destructively_repairable(bridge, monkeypatch):
    real_read = bridge._store.read

    def fail():
        raise StoreError("read_failed", "private path")

    monkeypatch.setattr(bridge._store, "read", fail)
    issue = ready(bridge)
    assert issue["recoverable"] is False and issue["code"] == "read_failed"
    assert not bridge.event("recover_settings", {"confirmed": True})["ok"]
    assert not bridge._store.path.exists()
    monkeypatch.setattr(bridge._store, "read", real_read)
    assert bridge.event("retry_startup")["ok"] is True


def test_backup_failure_never_resets_corrupt_file(bridge, monkeypatch):
    bridge._store.path.parent.mkdir(parents=True)
    bridge._store.path.write_bytes(b"broken")
    assert not ready(bridge)["ok"]

    def fail(**kwargs):
        raise StoreError("recovery_failed", "private path")

    monkeypatch.setattr(bridge._store, "recover_corrupt", fail)
    assert not bridge.event("recover_settings", {"confirmed": True})["ok"]
    assert bridge._store.path.read_bytes() == b"broken"


def test_write_failure_after_backup_keeps_original_backup(bridge, monkeypatch):
    bridge._store.path.parent.mkdir(parents=True)
    bridge._store.path.write_bytes(b"broken")
    assert not ready(bridge)["ok"]

    def fail(data):
        raise StoreError("write_failed", "private path")

    monkeypatch.setattr(bridge._store, "write", fail)
    assert not bridge.event("recover_settings", {"confirmed": True})["ok"]
    assert list(bridge._store.path.parent.glob("*.corrupt"))[0].read_bytes() == b"broken"
    assert bridge._ready is False


def test_run_reports_startup_failure_without_resetting_data(monkeypatch):
    from app import main as entry
    captured = []

    def fail():
        raise OSError("private details")

    monkeypatch.setattr(entry, "main", fail)
    monkeypatch.setattr(entry, "_show_startup_error", lambda error: captured.append(type(error)))
    with pytest.raises(SystemExit) as caught:
        entry.run()
    assert caught.value.code == 1 and captured == [OSError]


@pytest.mark.parametrize("error", [ModuleNotFoundError("secret"), ContractError("secret"),
    FileNotFoundError("secret"), PermissionError("secret"), RuntimeError("secret")])
def test_startup_message_does_not_leak_raw_exception(error, monkeypatch, capsys):
    import ctypes
    from app import main as entry
    displayed = []
    monkeypatch.setattr(ctypes.windll.user32, "MessageBoxW", lambda owner, text, title, flags: displayed.append(text))
    entry._show_startup_error(error)
    assert "secret" not in capsys.readouterr().err
    assert displayed and "secret" not in displayed[0]


def test_on_top_is_applied_then_persisted_only_by_save(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    assert bridge.event("ontop", True) == {"ok": True, "completed": True, "onTop": True}
    assert bridge._window.on_top is True and not bridge._store.path.exists()
    assert bridge.event("save", {"onTop": True})["ok"]
    fresh = NativeBridge(bridge._core, bridge._store)
    window = FakeWindow()
    monkeypatch.setattr(fresh, "_window", window)
    assert ready(fresh)["ok"] and window.on_top is True


@pytest.mark.parametrize("value", [None, 0, 1, "true", {}])
def test_on_top_rejects_non_boolean_values(bridge, value):
    assert ready(bridge)["ok"]
    assert not bridge.event("ontop", value)["ok"]
    assert bridge._window.on_top is False


def test_reset_preserves_profile_connections_and_core_notes(bridge):
    assert ready(bridge)["ok"]
    preferences = {"theme": "#4fd8ff", "vol": 0.2, "onTop": True,
                   "prof": {"pIns": "Keep profile"}, "devs": {"dIn": "7"}, "conn": {"model": "keep-model"}}
    assert bridge.event("save", preferences)["ok"]
    notes = JsonStore(get_data_home() / "notes.json")
    notes.write({"notes": [{"id": "keep", "text": "Keep note", "done": False}]})
    previous = notes.path.read_bytes()
    response = bridge.event("reset")
    assert response["ok"] and response["saved"]
    saved = bridge._store.read()
    assert saved["theme"] == "#a78bfa" and saved["vol"] == 0.8 and saved["onTop"] is False
    for key in ["prof", "devs", "conn"]:
        assert saved[key] == preferences[key]
    assert notes.path.read_bytes() == previous
    assert bridge._window.on_top is False


def test_reset_error_preserves_original_preferences_and_window(bridge, monkeypatch):
    assert ready(bridge)["ok"]
    assert bridge.event("save", {"theme": "#4fd8ff", "onTop": True})["ok"]
    previous = bridge._store.path.read_bytes()

    def fail(data):
        raise StoreError("write_failed", "Cannot write")

    monkeypatch.setattr(bridge._store, "write", fail)
    assert bridge.event("reset")["ok"] is False
    assert bridge._store.path.read_bytes() == previous
    assert bridge._window.on_top is True


@pytest.mark.parametrize("debug", [False, True])
def test_main_restart_launches_trusted_command_after_cleanup(monkeypatch, debug):
    """Süreç açma çağrısını gözle; test masaüstünde yeni uygulama bırakmasın."""
    from app import main as entry
    import webview

    captured, launched = {}, []
    monkeypatch.setenv("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "")
    monkeypatch.setattr(entry.sys, "argv", ["taskvex", *(["--debug"] if debug else [])])

    def create(*args, **kwargs):
        captured["api"] = kwargs["js_api"]
        return FakeWindow()

    def start(**kwargs):
        assert captured["api"].event("restart")["ok"]

    def launch(command, **kwargs):
        assert not captured["api"]._core._worker.is_alive()
        launched.append((command, kwargs))

    monkeypatch.setattr(webview, "create_window", create)
    monkeypatch.setattr(webview, "start", start)
    monkeypatch.setattr(entry.subprocess, "Popen", launch)
    entry.main()
    assert launched[0][0] == [entry.sys.executable, "-m", "app.main", *(["--debug"] if debug else [])]
    assert "shell" not in launched[0][1]


def test_main_missing_window_stops_core_without_starting_gui(monkeypatch):
    """Pencere oluşmazsa GUI döngüsüne girme; açılmış worker'ı kapat."""
    from app import main as entry
    import webview

    captured = {}
    monkeypatch.setattr(entry.sys, "argv", ["taskvex"])

    def create(*args, **kwargs):
        captured["core"] = kwargs["js_api"]._core
        return None

    def start(**kwargs):
        pytest.fail("GUI must not start without a window")

    monkeypatch.setattr(webview, "create_window", create)
    monkeypatch.setattr(webview, "start", start)
    with pytest.raises(RuntimeError, match="window could not be created"):
        entry.main()
    assert not captured["core"]._worker.is_alive()


def test_saved_live_model_is_restored_before_automatic_catalog(bridge, monkeypatch):
    from app.bridge import webview_bridge
    assert ready(bridge)['ok']
    assert bridge.event('save',{'conn':{'model':'saved-live'}})['ok']
    reopened=NativeBridge(bridge._core, bridge._store)
    monkeypatch.setattr(reopened,'_window',FakeWindow())
    assert ready(reopened)['ok']
    monkeypatch.setattr(webview_bridge,'load_live_catalog',lambda:{'ok':True,'completed':True,'models':[{'id':'first-live'},{'id':'saved-live'}]})
    assert reopened.event('query_catalog')['currentModel']=='saved-live'
