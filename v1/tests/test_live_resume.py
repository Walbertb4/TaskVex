"""Live devam ettirmeyi gerçek SDK/core ve planlı sentetik socket'lerle dene.

Her bağlantının setup, aktif tur ve idle mesajları ayrıdır. Böylece eski kullanıcı
metninin yeniden gönderilmediği ve yalnız güvenli checkpoint'in kullanıldığı
taşıma sınırında gözlenir. Gerçek hesap/ücretli API kullanılmaz.
"""

import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import itertools
import json
from threading import Event
from types import SimpleNamespace

from google.genai import errors, live
import pytest

from app.bootstrap import create_core
from app.session import live_session
from app.session.live_session import PersistentLive
from test_live_probe import frame
from test_live_tools import call, notes, tools


TOKEN = "SECRET_RESUME_TOKEN"
GOAWAY = {"goAway": {"timeLeft": "10s"}}


def checkpoint(*, resumable=True, token=TOKEN):
    return {"sessionResumptionUpdate": {"resumable": resumable, "newHandle": token}}


@pytest.fixture
def wire(monkeypatch):
    """Boş socket bekler; yalnız planda belirtilen idle kopma hata üretir."""
    state = SimpleNamespace(plans=[], sent=[], opened=0, closed=0, waiting=Event())
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-key")
    @asynccontextmanager
    async def connect(*args, **kwargs):
        assert state.plans, "Unexpected reconnect"
        plan = state.plans.pop(0)
        state.opened += 1
        number = state.opened
        frames = deque([plan.get("setup", {"setupComplete": {"sessionId": "provider-private"}})])
        turns = deque(plan.get("turns", []))
        idle = deque(plan.get("idle", []))
        completed = False
        class Socket:
            async def send(self, value):
                message = json.loads(value)
                state.sent.append((number, message))
                if "setup" in message and plan.get("error"):
                    raise plan["error"]
                if "realtime_input" in message:
                    assert turns, "User message was replayed or sent unexpectedly"
                    frames.extend(turns.popleft())
            async def recv(self, **kwargs):
                nonlocal completed
                if plan.get("hold_setup") or not frames:
                    if completed and plan.get("drop_idle"):
                        raise RuntimeError("SECRET transport closed")
                    state.waiting.set()
                    await asyncio.sleep(3600)
                message = frames.popleft()
                if "_drop" in message:
                    raise RuntimeError("SECRET active transport closed")
                content = message.get("serverContent", {})
                if content.get("interactionStatus") == "IDLE" or content.get("turnComplete") and content.get("interactionStatus") != "IN_PROGRESS":
                    completed = True
                    if idle:
                        frames.extend(idle.popleft())
                return json.dumps(message).encode()
        try:
            yield Socket()
        finally:
            state.closed += 1
    monkeypatch.setattr(live, "ws_connect", connect)
    return state


def setups(wire):
    return [message["setup"] for _, message in wire.sent if "setup" in message]


def inputs(wire):
    return [message["realtime_input"]["text"] for _, message in wire.sent if "realtime_input" in message]


def test_goaway_finishes_turn_then_resume_preserves_logical_scope_and_replay(wire, taskvex_home):
    wire.plans = [
        {"turns": [[GOAWAY, call(), frame("Saved", complete=True)]], "idle": [[checkpoint()]]},
        {"turns": [[call(), frame("Same task", complete=True)], [frame("Third", complete=True)]]},
    ]
    host = PersistentLive()
    with create_core() as core:
        try:
            first = host.ask("Add", "future-live", tools(core, session="first"))
            second = host.ask("Replay check", "future-live", tools(core, session="second"))
            third = host.ask("Hi", "future-live", tools(core, session="third"))
            assert first["ok"] and first["goaway_received"]
            assert second["ok"] and second["session_resumed"] and not second["session_reused"]
            assert second["logical_session_id"] == first["logical_session_id"]
            assert second["context_reset_reason"] is None
            assert first["tool_results"][0]["task_id"] == second["tool_results"][0]["task_id"]
            assert third["ok"] and third["session_reused"] and not third["session_resumed"]
            assert len(notes(taskvex_home)) == 1 and wire.opened == 2
            assert setups(wire)[1]["sessionResumption"]["handle"] == TOKEN
            assert inputs(wire) == ["Add", "Replay check", "Hi"]
            assert TOKEN not in json.dumps([first, second, third]) and "provider-private" not in json.dumps(second)
        finally:
            assert host.close() and wire.closed == wire.opened


@pytest.mark.parametrize("has_checkpoint", [False, True])
def test_idle_transport_drop_resumes_only_with_safe_checkpoint(wire, has_checkpoint):
    wire.plans = [{"turns": [[frame("First", complete=True)]],
        "idle": [[checkpoint()]] if has_checkpoint else [], "drop_idle": True},
        {"turns": [[frame("Next", complete=True)]]}]
    host = PersistentLive()
    try:
        first = host.ask("First", "future-live")
        second = host.ask("Next", "future-live")
        assert second["ok"] and second["session_resumed"] is has_checkpoint
        assert (first["logical_session_id"] == second["logical_session_id"]) is has_checkpoint
        assert second["context_reset_reason"] == (None if has_checkpoint else "idle_disconnect")
        assert inputs(wire) == ["First", "Next"]
    finally:
        assert host.close() and wire.closed == wire.opened


@pytest.mark.parametrize("status", [400, 404, 1008])
def test_rejected_resume_has_one_fresh_fallback_before_sending_new_text(wire, status):
    wire.plans = [{"turns": [[frame("First", complete=True)]], "idle": [[checkpoint(), GOAWAY]]},
        {"error": errors.APIError(status, {"error": {"message": "SECRET"}})},
        {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    try:
        first = host.ask("First", "future-live")
        second = host.ask("New request", "future-live")
        assert second["ok"] and not second["session_resumed"]
        assert second["context_reset_reason"] == "resume_rejected"
        assert second["logical_session_id"] != first["logical_session_id"]
        assert wire.opened == 3 and "handle" not in setups(wire)[2]["sessionResumption"]
        assert inputs(wire) == ["First", "New request"] and "SECRET" not in json.dumps(second)
    finally:
        assert host.close() and wire.closed == wire.opened


@pytest.mark.parametrize("status", [403, 429, 503])
def test_resume_auth_quota_or_service_error_is_not_retried(wire, status):
    wire.plans = [{"turns": [[frame("First", complete=True)]], "idle": [[checkpoint(), GOAWAY]]},
        {"error": errors.APIError(status, {"error": {"message": "SECRET"}})}]
    host = PersistentLive()
    try:
        assert host.ask("First", "future-live")["ok"]
        result = host.ask("New request", "future-live")
        assert not result["ok"] and wire.opened == 2 and inputs(wire) == ["First"]
        assert TOKEN not in json.dumps(result) and "SECRET" not in json.dumps(result)
    finally:
        assert host.close() and wire.closed == wire.opened


@pytest.mark.parametrize("update", [checkpoint(resumable=False, token=""), checkpoint(token="")])
def test_nonresumable_or_empty_update_forgets_previous_handle(wire, update):
    wire.plans = [{"turns": [[frame("First", complete=True)]], "idle": [[checkpoint(), update, GOAWAY]]},
        {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    try:
        assert host.ask("First", "future-live")["ok"]
        result = host.ask("Next", "future-live")
        assert result["ok"] and result["context_reset_reason"] == "no_checkpoint"
        assert "handle" not in setups(wire)[1]["sessionResumption"]
    finally:
        assert host.close()


def test_expired_checkpoint_is_not_used(wire, monkeypatch):
    times = itertools.count(0, 7201)
    monkeypatch.setattr(live_session, "monotonic", lambda: next(times))
    wire.plans = [{"turns": [[frame("First", complete=True)]], "idle": [[checkpoint(), GOAWAY]]},
        {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    try:
        assert host.ask("First", "future-live")["ok"]
        result = host.ask("Next", "future-live")
        assert result["ok"] and result["context_reset_reason"] == "checkpoint_expired"
        assert "handle" not in setups(wire)[1]["sessionResumption"]
    finally:
        assert host.close()


def test_active_checkpoint_is_not_reused_after_goaway(wire):
    wire.plans = [{"turns": [[checkpoint(), GOAWAY, frame("Done", complete=True)]]},
        {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    try:
        assert host.ask("First", "future-live")["ok"]
        result = host.ask("Next", "future-live")
        assert result["ok"] and result["context_reset_reason"] == "no_checkpoint"
        assert "handle" not in setups(wire)[1]["sessionResumption"]
    finally:
        assert host.close()


def test_active_failure_after_commit_is_not_replayed_or_resumed(wire, taskvex_home):
    wire.plans = [{"turns": [[frame("First", complete=True)], [call(), {"_drop": True}]],
        "idle": [[checkpoint()]]}, {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    with create_core() as core:
        try:
            assert host.ask("First", "future-live", tools(core))["ok"]
            failed = host.ask("Add", "future-live", tools(core))
            assert not failed["ok"] and failed["tool_results"][0]["result"]["verified"]
            assert wire.opened == 1 and len(notes(taskvex_home)) == 1
            fresh = host.ask("Different request", "future-live", tools(core))
            assert fresh["ok"] and fresh["context_reset_reason"] == "previous_turn_failed"
            assert "handle" not in setups(wire)[1]["sessionResumption"]
            assert inputs(wire) == ["First", "Add", "Different request"] and len(notes(taskvex_home)) == 1
        finally:
            assert host.close()


@pytest.mark.parametrize("change", ["model", "key", "tools", "disconnect"])
def test_scope_or_disconnect_discards_resume_information(wire, monkeypatch, change):
    wire.plans = [{"turns": [[frame("First", complete=True)]], "idle": [[checkpoint(), GOAWAY]]},
        {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    with create_core() as core:
        try:
            first = host.ask("First", "future-live", tools(core))
            if change == "key":
                monkeypatch.setenv("GEMINI_API_KEY", "new-synthetic-key")
            if change == "disconnect":
                assert host.close()
            second = host.ask("Next", "other-live" if change == "model" else "future-live",
                tools(core, notes=change != "tools"))
            assert second["ok"] and second["logical_session_id"] != first["logical_session_id"]
            assert not second["session_resumed"] and "handle" not in setups(wire)[1]["sessionResumption"]
        finally:
            assert host.close()


def test_stop_during_resume_setup_discards_checkpoint_and_ledger(wire):
    wire.plans = [{"turns": [[frame("First", complete=True)]], "idle": [[checkpoint(), GOAWAY]]},
        {"hold_setup": True}, {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            assert host.ask("First", "future-live")["ok"]
            running = pool.submit(host.ask, "Stop before send", "future-live", request_id="resume")
            # İlk preflight da waiting'i ayarlar; setup gerçekten başladıktan
            # sonra iptal ver ki test yalnız erken sinyali ölçmesin.
            for _ in range(300):
                if wire.opened == 2:
                    break
                Event().wait(0.01)
            assert wire.opened == 2 and host.stop("resume")
            assert running.result(3)["stopped"]
            assert host.ask("Fresh", "future-live")["ok"]
            assert inputs(wire) == ["First", "Fresh"]
            assert "handle" not in setups(wire)[2]["sessionResumption"]
        finally:
            assert host.close()


def test_idle_tool_call_is_not_executed_or_resumed(wire, taskvex_home):
    wire.plans = [{"turns": [[frame("First", complete=True)]], "idle": [[checkpoint(), call()]]},
        {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    with create_core() as core:
        try:
            assert host.ask("First", "future-live", tools(core))["ok"]
            second = host.ask("Next", "future-live", tools(core))
            assert second["ok"] and second["context_reset_reason"] == "unsafe_idle_output"
            assert notes(taskvex_home) == [] and "handle" not in setups(wire)[1]["sessionResumption"]
        finally:
            assert host.close()


def test_resume_setup_must_be_confirmed_before_sending_text(wire):
    wire.plans = [{"turns": [[frame("First", complete=True)]], "idle": [[checkpoint(), GOAWAY]]},
        {"setup": {"usageMetadata": {}}}, {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    try:
        assert host.ask("First", "future-live")["ok"]
        second = host.ask("Next", "future-live")
        assert second["ok"] and second["context_reset_reason"] == "resume_rejected"
        assert inputs(wire) == ["First", "Next"] and wire.opened == 3
    finally:
        assert host.close()


def test_fresh_setup_without_ack_does_not_send_user_text(wire):
    wire.plans = [{"setup": {"usageMetadata": {}}}]
    host = PersistentLive()
    try:
        result = host.ask("Must not send", "future-live")
        assert not result["ok"] and inputs(wire) == [] and wire.opened == 1
    finally:
        assert host.close() and wire.closed == 1


def test_idle_control_flood_is_bounded_and_starts_fresh(wire):
    wire.plans = [{"turns": [[frame("First", complete=True)]],
        "idle": [[checkpoint() for _ in range(40)]]},
        {"turns": [[frame("Fresh", complete=True)]]}]
    host = PersistentLive()
    try:
        assert host.ask("First", "future-live")["ok"]
        result = host.ask("Next", "future-live")
        assert result["ok"] and result["context_reset_reason"] == "unsafe_idle_output"
        assert wire.opened == 2 and "handle" not in setups(wire)[1]["sessionResumption"]
    finally:
        assert host.close()



def test_application_usage_survives_reused_live_and_disconnect(wire):
    from app.session.text_chat import TextChat
    def counted(n):
        return {**frame('Hello',complete=True),'usageMetadata':{'totalTokenCount':n}}
    wire.plans=[{'turns':[[counted(10)],[counted(10)]]},{'turns':[[counted(5)]]}]
    with create_core() as core:
        chat=TextChat(core)
        try:
            assert chat.run_live('First','future-live')['usage_tokens']==10
            assert chat.run_live('Second','future-live')['usage_tokens']==20
            assert chat.reset_live()
            assert chat.run_live('Third','future-live')['usage_tokens']==25
            assert wire.opened==2
        finally:
            assert chat.close()
