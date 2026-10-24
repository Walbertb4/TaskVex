"""Gerçek Live SDK protokolünü sentetik WebSocket ile dene; dış ağ/ses yoktur.

Yalnız socket taşıması taklittir. Kurulum, metin gönderimi, yanıt ayrıştırma ve
SDK kaynak kapanışı gerçek koddan geçer. Canlı hesap gecikmesini kanıtlamaz.
"""

import asyncio
from contextlib import asynccontextmanager
import json
from types import SimpleNamespace
from threading import Event

from google.genai import live
import pytest

from app.session import live_probe


@pytest.fixture
def socket(monkeypatch):
    state = SimpleNamespace(frames=[], sent=[], closed=False, opened=0, error=None, stall=False, waiting=Event(), turn_open=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class Socket:
        async def send(self, message):
            payload = json.loads(message)
            state.sent.append(payload)
            if "realtime_input" in payload and 'activityStart' not in payload['realtime_input']:
                state.turn_open = True

        async def recv(self, **kwargs):
            # Gelecekteki kullanıcı turunun sentetik içeriği idle preflight'a
            # sızmamalı. Gerçek sunucu da bu metin gelmeden yanıt üretmez.
            head = state.frames[0] if state.frames else {}
            while not state.turn_open and not any(k in head for k in ("setupComplete", "sessionResumptionUpdate", "goAway")):
                await asyncio.sleep(.001)
            if state.stall and not state.frames and state.sent and len(state.sent) > 1:
                state.waiting.set()
                await asyncio.sleep(3600)
            if not state.frames:
                raise RuntimeError("SECRET: unexpected extra receive")
            payload = state.frames.pop(0)
            content = payload.get("serverContent", {})
            if content.get("interactionStatus") == "IDLE" or content.get("turnComplete") and content.get("interactionStatus") != "IN_PROGRESS":
                state.turn_open = False
            return json.dumps(payload).encode()

    @asynccontextmanager
    async def connect(*args, **kwargs):
        state.opened += 1
        state.turn_open = False
        try:
            if state.error:
                raise state.error
            yield Socket()
        finally:
            state.closed = True

    monkeypatch.setattr(live, "ws_connect", connect)
    return state


def frame(text=None, *, complete=False, status=None, audio=False):
    """Aynı event transkript ve ses taşıyabilir; bütün parçalar okunmalı."""
    content: dict = {"turnComplete": complete}
    if text is not None:
        content["outputTranscription"] = {"text": text}
    if status:
        content["interactionStatus"] = status
    if audio:
        content["modelTurn"] = {"role": "model", "parts": [
            {"inlineData": {"mimeType": "audio/pcm;rate=24000", "data": "AAAA"}},
            {"inlineData": {"mimeType": "audio/pcm;rate=24000", "data": "AAAA"}},
        ]}
    return {"serverContent": content}


def test_live_probe_uses_audio_transcript_without_playback_or_tools(socket):
    socket.frames = [{"setupComplete": {}}, frame("Mer", audio=True), frame("haba", complete=True)]
    report = asyncio.run(live_probe.probe_live_text("Merhaba", "future-live"))
    assert report["ok"] and report["text"] == "Merhaba" and report["tool_results"] == []
    assert report["audio_bytes_discarded"] == 6
    assert 0 <= report["first_event_ms"] <= report["elapsed_ms"]
    assert 0 <= report["first_text_ms"] <= report["elapsed_ms"]
    assert socket.closed and socket.opened == 1
    setup, message = socket.sent
    assert setup["setup"]["model"] == "models/future-live"
    assert setup["setup"]["generationConfig"]["responseModalities"] == ["AUDIO"]
    assert "outputAudioTranscription" in setup["setup"] and not setup["setup"].get("tools")
    assert message == {"realtime_input": {"text": "Merhaba"}}
    assert "test-key" not in json.dumps(report)


def test_live_probe_waits_for_idle_despite_intermediate_turn_complete(socket):
    socket.frames = [{"setupComplete": {}}, frame("Bir ", complete=True, status="IN_PROGRESS"),
                     frame("yanıt", status="IDLE")]
    report = asyncio.run(live_probe.probe_live_text("Merhaba", "future-live"))
    assert report["ok"] and report["text"] == "Bir yanıt" and not socket.frames


@pytest.mark.parametrize("payload,code", [
    ({"toolCall": {"functionCalls": [{"name": "notes.add", "args": {"text": "No"}, "id": "x"}]}}, "live_protocol"),
    ({"serverContent": {"interrupted": True}}, "live_interrupted"),
    (frame(complete=True, audio=True), "live_incomplete"),
    (frame("x" * 32001), "live_response_limit"),
    ({"goAway": {"timeLeft": "1s"}}, "live_go_away"),
])
def test_live_probe_rejects_incomplete_or_unexpected_output(socket, payload, code):
    socket.frames = [{"setupComplete": {}}, payload]
    report = asyncio.run(live_probe.probe_live_text("Test", "future-live"))
    assert not report["ok"] and report["code"] == code and report["tool_results"] == []
    assert socket.closed and socket.opened == 1


def test_live_probe_timeout_closes_socket_without_retry(socket, monkeypatch):
    original = asyncio.timeout
    monkeypatch.setattr(live_probe.asyncio, "timeout", lambda seconds: original(0.01))
    socket.frames = [{"setupComplete": {}}]
    socket.stall = True
    report = asyncio.run(live_probe.probe_live_text("Test", "future-live"))
    assert report["code"] == "live_timeout" and socket.closed and socket.opened == 1


def test_live_probe_exception_does_not_expose_secrets(socket):
    class Closed(RuntimeError):
        rcvd = SimpleNamespace(code=1008)
        @property
        def code(self):
            raise AssertionError("Deprecated websocket code property was accessed")
    socket.error = Closed("SECRET")
    report = asyncio.run(live_probe.probe_live_text("Test", "future-live"))
    assert report["code"] == "live_connection_error" and "SECRET" not in json.dumps(report)
    assert report["websocket_code"] == 1008
    assert socket.closed and socket.opened == 1


def test_live_probe_missing_key_makes_no_connection(socket, monkeypatch):
    monkeypatch.setattr(live_probe, "load_gemini_key", lambda: None)
    report = asyncio.run(live_probe.probe_live_text("Test", "future-live"))
    assert report["code"] == "missing_api_key" and socket.opened == 0


def test_live_probe_uses_same_busy_and_closed_guard_as_rest(socket):
    from app.bootstrap import create_core
    from app.session.text_chat import TextChat
    with create_core() as core:
        chat = TextChat(core)
        assert not chat.run_live("", "future-live")["ok"]
        with chat._lock:
            assert not chat.run_live("Test", "future-live")["ok"]
        assert chat.close() and not chat.run_live("Test", "future-live")["ok"]
    assert socket.opened == 0


def test_persistent_live_reuses_socket_and_disconnect_opens_fresh_session(socket):
    from app.session.live_session import PersistentLive
    host = PersistentLive()
    try:
        socket.frames = [{"setupComplete": {}}, frame("First", complete=True), frame("Second", complete=True)]
        first = host.ask("First", "future-live")
        second = host.ask("Second", "future-live")
        assert first["ok"] and not first["session_reused"]
        assert second["ok"] and second["session_reused"] and second["text"] == "Second"
        assert socket.opened == 1 and not socket.closed
        thread = host._thread
        assert thread is not None
        assert host.close() and socket.closed and not thread.is_alive()
        socket.frames = [{"setupComplete": {}}, frame("New", complete=True)]
        third = host.ask("New", "future-live")
        assert third["ok"] and not third["session_reused"] and socket.opened == 2
    finally:
        assert host.close()


@pytest.mark.parametrize("change", ["model", "key"])
def test_persistent_live_replaces_connection_on_identity_change(socket, monkeypatch, change):
    from app.session.live_session import PersistentLive
    host = PersistentLive()
    try:
        socket.frames = [{"setupComplete": {}}, frame("First", complete=True)]
        assert host.ask("First", "future-live")["ok"]
        if change == "key":
            monkeypatch.setenv("GEMINI_API_KEY", "new-test-key")
        socket.frames = [{"setupComplete": {}}, frame("Second", complete=True)]
        second = host.ask("Second", "new-live" if change == "model" else "future-live")
        assert second["ok"] and not second["session_reused"] and socket.opened == 2
    finally:
        assert host.close()


def test_persistent_live_error_is_not_replayed_and_next_message_is_fresh(socket):
    from app.session.live_session import PersistentLive
    host = PersistentLive()
    try:
        socket.frames = [{"setupComplete": {}}, frame("First", complete=True)]
        assert host.ask("First", "future-live")["ok"]
        # Sonraki okumada socket hatası: aynı mesaj otomatik yeniden gönderilmez.
        failed = host.ask("Failed", "future-live")
        assert not failed["ok"] and socket.closed and socket.opened == 1
        socket.frames = [{"setupComplete": {}}, frame("Fresh", complete=True)]
        fresh = host.ask("New user message", "future-live")
        assert fresh["ok"] and not fresh["session_reused"] and socket.opened == 2
    finally:
        assert host.close()


@pytest.mark.parametrize('count', [0, 123, -1, 9007199254740992, None])
def test_live_usage_is_last_provider_report_not_sum_or_quota(socket, count):
    socket.frames = [{'setupComplete':{}}, {'usageMetadata':{'totalTokenCount':50}},
        {**frame('Hello', complete=True),'usageMetadata':{'totalTokenCount':count}}]
    report = asyncio.run(live_probe.probe_live_text('Hello','future-live'))
    assert report['ok']
    assert report['usage_tokens'] == (count if type(count) is int and 0 <= count <= 9007199254740991 else None)


def test_live_missing_usage_stays_unknown(socket):
    socket.frames = [{'setupComplete':{}},frame('Hello',complete=True)]
    report = asyncio.run(live_probe.probe_live_text('Hello','future-live'))
    assert 'usage_tokens' not in report



def test_live_usage_snapshots_replace_within_generation_and_sum_tool_rounds(socket):
    from app.bootstrap import create_core
    from test_live_tools import tools,call
    socket.frames=[{'setupComplete':{}},{'usageMetadata':{'totalTokenCount':5}},
        {**call('apps.catalog',{},'catalog'),'usageMetadata':{'totalTokenCount':10}},
        {'usageMetadata':{'totalTokenCount':3}},
        {**frame('Done',complete=True),'usageMetadata':{'totalTokenCount':7}}]
    with create_core() as core:
        result=asyncio.run(live_probe.probe_live_text('Catalog','future-live',tools=tools(core,notes=False)))
    assert result['ok'] and result['usage_tokens']==17 and not result['usage_partial']
