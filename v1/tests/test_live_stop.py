"""Live Stop kabulü ile gerçek bitişi ayrı doğrula; ağ taşıması sentetiktir.

Gerçek SDK, core worker ve geçici not kaydı kullanılır. Event kapıları iptali
tam ağ/araç beklemesinde gönderir; kullanıcı hesabı veya donanım kullanılmaz.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from app.bootstrap import create_core
from app.core.contracts import TaskStatus, ToolResult, ToolSpec
from app.session.live_probe import probe_live_text
from app.session.live_session import PersistentLive
from app.session.model_tools import ModelTools
from app.session.tool_registry import ToolRegistry
from app.tasks.manager import TaskManager
from test_live_probe import socket, frame
from test_live_tools import call, notes, tools


@pytest.mark.parametrize("committed", [False, True])
def test_stop_waiting_live_closes_socket_and_preserves_completed_actions(socket, taskvex_home, committed):
    host = PersistentLive()
    socket.frames = [{"setupComplete": {}}, *([call()] if committed else [])]
    socket.stall = True
    with create_core() as core, ThreadPoolExecutor(max_workers=1) as pool:
        try:
            running = pool.submit(host.ask, "Add", "future-live", tools(core), request_id="first")
            assert socket.waiting.wait(3)
            assert not host.stop("old")
            assert host.stop("first") and host.stop("first")
            report = running.result(3)
            assert report["stopped"] and report["completed"] and not report["ok"]
            assert socket.closed and len(notes(taskvex_home)) == int(committed)
            if committed:
                assert report["tool_results"][0]["result"]["verified"]
            assert not host.stop("first")
            socket.stall = False
            socket.frames = [{"setupComplete": {}}, frame("Fresh", complete=True)]
            report = host.ask("Hi", "future-live", tools(core), request_id="second")
            assert report["ok"] and not report["session_reused"] and socket.opened == 2
        finally:
            host.close()


def test_stop_before_live_io_performs_no_provider_request(socket):
    stop = Event()
    stop.set()
    report = asyncio.run(probe_live_text("Hi", "future-live", stop_event=stop))
    assert report["stopped"] and socket.opened == 0


@pytest.mark.parametrize("finishes_successfully", [False, True])
def test_stop_waits_for_actual_core_completion(socket, finishes_successfully):
    """Çalışan iş geç iptale rağmen doğrulanmış dönebilir; başarı geri alınmaz."""
    entered, cancel_seen, release = Event(), Event(), Event()
    def handler(args, context):
        entered.set()
        assert context.cancel_event.wait(3)
        cancel_seen.set()
        assert release.wait(3)
        return ToolResult(task_id=context.task_id,
            status=TaskStatus.SUCCEEDED if finishes_successfully else TaskStatus.CANCELLED,
            verified=finishes_successfully)
    registry = ToolRegistry()
    registry.register(ToolSpec(name="test.run", description="Controlled test",
        input_schema={"type": "object"}, handler=handler))
    host = PersistentLive()
    socket.frames = [{"setupComplete": {}}, call("test.run", {})]
    with TaskManager(registry, authorize=lambda request, spec: True) as core, ThreadPoolExecutor(max_workers=1) as pool:
        bound = ModelTools(core, principal="test-user", session_id="stop", allowed_tools=("test.run",))
        try:
            running = pool.submit(host.ask, "Run", "future-live", bound, request_id="tool")
            assert entered.wait(3) and host.stop("tool") and cancel_seen.wait(3)
            assert not running.done()  # kabul edildi, fakat araç henüz durmadı
            assert host.stop("tool")  # ikinci Stop sonuç beklemesini kesmemeli
            release.set()
            report = running.result(3)
            assert report["stopped"] and not report["unknown"]
            assert report["tool_results"][0]["status"] == ("succeeded" if finishes_successfully else "cancelled")
            assert not any("tool_response" in message for message in socket.sent)
        finally:
            release.set()
            host.close()


@pytest.mark.parametrize("broken_cancel", [False, True])
def test_unresolved_tool_after_stop_remains_unknown(socket, monkeypatch, broken_cancel):
    host = PersistentLive()
    socket.frames = [{"setupComplete": {}}, call("apps.catalog", {})]
    socket.stall = True
    with create_core() as core, ThreadPoolExecutor(max_workers=1) as pool:
        bound = tools(core)
        original = bound.result
        def unresolved(task_id, *, timeout=0):
            record = original(task_id, timeout=timeout)
            if socket.waiting.is_set():
                record.update(status="running", result=None)
            return record
        monkeypatch.setattr(bound, "result", unresolved)
        if broken_cancel:
            def broken(task_id):
                raise RuntimeError("SECRET")
            monkeypatch.setattr(bound, "cancel", broken)
        try:
            running = pool.submit(host.ask, "Catalog", "future-live", bound, request_id="pending")
            assert socket.waiting.wait(3) and host.stop("pending")
            report = running.result(3)
            assert report["unknown"] and not report["stopped"]
            assert "SECRET" not in str(report)
        finally:
            host.close()


def test_unexpected_live_host_failure_does_not_allow_blind_retry(monkeypatch):
    from app.session.text_chat import TextChat
    with create_core() as core:
        chat = TextChat(core)
        def fail(*args, **kwargs):
            raise RuntimeError("SECRET")
        monkeypatch.setattr(chat._live, "ask", fail)
        report = chat.run_live("Hi", "future-live")
        assert report["unknown"] and "SECRET" not in str(report) and not chat.busy
        assert chat.close()
