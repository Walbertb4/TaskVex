"""Live araç entegrasyonu: gerçek SDK/core/kayıt, sentetik WebSocket taşıması.

ModelTools izin/sözleşme hattı atlanmamalı; replay tek dosya yazımı üretmeli.
Bu testler gerçek hesap, mikrofon veya ses çıkışı kabulü değildir.
"""

import asyncio
import json

import pytest

from app.bootstrap import create_core
from app.session.live_probe import probe_live_text
from app.session.live_session import PersistentLive
from app.session.model_tools import ModelTools
from app.storage.json_store import JsonStore
from test_live_probe import socket, frame


def tools(core, *, session="live-tools", notes=True):
    """Kaynak ve kullanıcı model payload'ından alınmaz; host bu listeyi seçer."""
    names = ("apps.catalog", "system.status") + (("notes.add", "notes.list") if notes else ())
    return ModelTools(core, principal="local-user", session_id=session, allowed_tools=names)


def call(name="notes.add", args=None, call_id: str | None = "call-1"):
    return {"toolCall": {"functionCalls": [{"id": call_id, "name": name,
        "args": {"text": "Live synthetic note"} if args is None else args}]}}


def notes(home):
    document = JsonStore(home / "notes.json").read()
    return document["notes"] if document else []


def test_live_note_add_list_through_real_core_and_function_responses(socket, taskvex_home):
    socket.frames = [{"setupComplete": {}}, call(), call("notes.list", {}, "read"), frame("Saved", complete=True)]
    with create_core() as core:
        report = asyncio.run(probe_live_text("Add and read", "future-live", tools=tools(core)))
    assert report["ok"] and len(notes(taskvex_home)) == 1
    assert [r["status"] for r in report["tool_results"]] == ["succeeded", "succeeded"]
    responses = [m["tool_response"]["functionResponses"][0] for m in socket.sent if "tool_response" in m]
    assert responses[0]["id"] == "call-1" and responses[0]["response"]["result"]["verified"]
    assert responses[1]["response"]["result"]["data"]["notes"] == notes(taskvex_home)
    declarations = socket.sent[0]["setup"]["tools"][0]["functionDeclarations"]
    assert {d["name"] for d in declarations} == {"apps.catalog", "system.status", "notes.add", "notes.list"}
    assert all(d["behavior"] == "BLOCKING" for d in declarations)


@pytest.mark.parametrize("changed", [False, True])
def test_live_duplicate_call_reuses_task_or_rejects_changed_arguments(socket, taskvex_home, changed):
    socket.frames = [{"setupComplete": {}}, call(),
        call(args={"text": "Changed"} if changed else None), frame("Saved", complete=True)]
    with create_core() as core:
        report = asyncio.run(probe_live_text("Add", "future-live", tools=tools(core)))
    assert len(notes(taskvex_home)) == 1
    if changed:
        assert not report["ok"] and report["code"] == "request_conflict"
    else:
        assert report["ok"] and report["tool_results"][0]["task_id"] == report["tool_results"][1]["task_id"]


@pytest.mark.parametrize("payload", [call("apps.open", {"app_id": "notepad"}),
    call(args={"text": 4}), call(call_id=None), call(args={"text": "X", "principal": "admin"})])
def test_live_rejects_unexposed_invalid_or_identity_injected_calls(socket, taskvex_home, payload):
    socket.frames = [{"setupComplete": {}}, payload]
    with create_core() as core:
        report = asyncio.run(probe_live_text("Test", "future-live", tools=tools(core)))
    assert not report["ok"] and notes(taskvex_home) == []


def test_live_without_notes_confirmation_has_no_note_tool(socket, taskvex_home):
    socket.frames = [{"setupComplete": {}}, call()]
    with create_core() as core:
        report = asyncio.run(probe_live_text("Add", "future-live", tools=tools(core, notes=False)))
    assert not report["ok"] and notes(taskvex_home) == []


def test_live_transport_error_after_note_commit_preserves_result(socket, taskvex_home):
    socket.frames = [{"setupComplete": {}}, call()]
    with create_core() as core:
        report = asyncio.run(probe_live_text("Add", "future-live", tools=tools(core)))
    assert not report["ok"] and len(notes(taskvex_home)) == 1
    assert report["tool_results"][0]["result"]["verified"]
    assert socket.opened == 1 and "SECRET" not in json.dumps(report)


def test_persistent_connection_keeps_replay_scope_between_user_turns(socket, taskvex_home):
    host = PersistentLive()
    with create_core() as core:
        try:
            socket.frames = [{"setupComplete": {}}, call(), frame("Saved", complete=True)]
            first = host.ask("Add", "future-live", tools(core, session="first"))
            socket.frames = [call(), frame("Same result", complete=True)]
            second = host.ask("Test replay", "future-live", tools(core, session="second"))
            assert second["ok"] and second["session_reused"] and socket.opened == 1
            assert first["tool_results"][0]["task_id"] == second["tool_results"][0]["task_id"]
            assert len(notes(taskvex_home)) == 1
        finally:
            assert host.close()


def test_pending_live_tool_is_not_sent_as_completed(socket, monkeypatch):
    socket.frames = [{"setupComplete": {}}, call("apps.catalog", {})]
    with create_core() as core:
        bound = tools(core)
        original = bound.result
        def result(task_id, *, timeout=0):
            record = original(task_id, timeout=timeout)
            record.update(status="running", result=None)
            return record
        monkeypatch.setattr(bound, "result", result)
        report = asyncio.run(probe_live_text("Catalog", "future-live", tools=bound))
    assert not report["ok"] and report["unknown"] and report["code"] == "task_pending"
    assert not any("tool_response" in m for m in socket.sent)


def test_server_cancellation_does_not_undo_committed_note(socket, taskvex_home):
    socket.frames = [{"setupComplete": {}}, call(), {"toolCallCancellation": {"ids": ["call-1"]}}]
    with create_core() as core:
        report = asyncio.run(probe_live_text("Add", "future-live", tools=tools(core)))
    assert report["code"] == "tool_cancelled" and len(notes(taskvex_home)) == 1
    assert report["tool_results"][0]["result"]["verified"]


@pytest.mark.parametrize("idle", [False, True])
def test_extended_tool_completion_requires_idle(socket, taskvex_home, idle):
    ending = [frame("Done", complete=True, status="IDLE")] if idle else []
    socket.frames = [{"setupComplete": {}}, call(),
        frame("Working", complete=True, status="IN_PROGRESS"), *ending]
    with create_core() as core:
        report = asyncio.run(probe_live_text("Add", "future-live-extended-thinking", tools=tools(core)))
    assert report["ok"] is idle and len(notes(taskvex_home)) == 1
    declarations = socket.sent[0]["setup"]["tools"][0]["functionDeclarations"]
    assert all(item["behavior"] == "NON_BLOCKING" for item in declarations)


def test_live_note_permission_change_reopens_socket(socket):
    host = PersistentLive()
    with create_core() as core:
        try:
            socket.frames = [{"setupComplete": {}}, frame("Hi", complete=True)]
            assert host.ask("Hi", "future-live", tools(core, notes=False))["ok"]
            socket.frames = [{"setupComplete": {}}, frame("Ready", complete=True)]
            report = host.ask("Ready", "future-live", tools(core))
            assert report["ok"] and not report["session_reused"] and socket.opened == 2
        finally:
            assert host.close()
