"""Modelden not değiştirmeyi gerçek core/SDK ve geçici kayıtlarla doğrula.

REST HTTP ve Live WebSocket taşıması sentetiktir; hesap/kota kullanılmaz.
Hedef seçiminin sağlayıcıya bırakılmadığı, kimliklerin korunduğu ve kabulün
dosyada doğrulanmış başarıdan ayrı kaldığı iki taşıma için birlikte denenir.
"""

from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import httpx
import pytest

from app.bootstrap import create_core
from app.config import get_data_home
from app.tools.local.notes import notes_snapshot
from app.core.contracts import ContractError, ToolRequest
from app.session import gemini
from app.session.model_tools import ModelTools, NoteTargetError
from app.session.text_chat import TextChat
from app.storage.json_store import JsonStore, StoreError
from test_gemini import transport, reply, call as rest_call
from test_live_probe import socket, frame
from test_live_tools import call as live_call, notes
from test_live_resume import wire, checkpoint, GOAWAY


def seed(core, text="Temporary note"):
    """Üretim CRUD'uyla geçici bir kayıt oluştur; gerçek UUID'yi geri ver."""
    task = core.submit(ToolRequest(request_id=uuid4().hex,
        source="desktop", principal="local-user", tool="notes.add", arguments={"text": text}))
    result = core.wait(task.task_id, 2).result
    assert result is not None and result.verified
    return result.to_dict()["data"]["note"]


def gateway(core):
    """Modelin gördüğü dar CRUD kapsamı; initialize/replace hâlâ kapalıdır."""
    return ModelTools(core, principal="local-user", session_id="mutation-test",
                      allowed_tools=("notes.add", "notes.list", "notes.select", "notes.update", "notes.delete", "notes.delete_many", "notes.complete_many"))


def current_snapshot():
    """Sentetik sağlayıcının bilinen geçici veri snapshot'ı; üretim verisi okunmaz."""
    data = JsonStore(get_data_home() / 'notes.json').read()
    return notes_snapshot(data['notes'] if data else [])


def read(tools, call_id="read"):
    task = tools.submit({"id": call_id, "name": "notes.select", "arguments": {"kind":"text","text":"Temporary note","cardinality":"one"}})
    assert tools.result(task.task_id, timeout=2)["result"]["verified"]
    return task


def execute(chat, mode, prompt, calls, transport, socket, *, ready=True, ending="ok"):
    """Aynı çağrı planını iki gerçek SDK hattından geçir; otomatik model yoktur."""
    # Sağlayıcı taklidi seçimin döndüreceği bilinen hash'i kullanır. İstek
    # metni yorumlanmaz; seçici her test planında açıkça tanımlıdır.
    snapshot = current_snapshot()
    calls = [(n, {**a, 'expected_snapshot': a.get('expected_snapshot', snapshot)}
              if n in {'notes.update','notes.delete','notes.delete_many','notes.complete_many'} else a, i) for n,a,i in calls]
    if mode == "rest":
        transport.responses = [reply([rest_call(name, args, call_id)]) for name, args, call_id in calls]
        transport.responses += ([reply([{"text": "Verified"}])] if ending == "ok" else
                                [httpx.Response(503, json={"error": {"code": 503}})])
        return chat.run(prompt, gemini.DEFAULT_MODEL, notes_ready=ready)
    socket.frames = [{"setupComplete": {}}, *[live_call(name, args, call_id) for name, args, call_id in calls]]
    if ending == "ok":
        socket.frames.append(frame("Verified", complete=True))
    return chat.run_live(prompt, "future-live", notes_ready=ready)


@pytest.mark.parametrize("mode", ["rest", "live"])
@pytest.mark.parametrize("change", ["text", "done", "delete"])
def test_model_updates_completes_deletes_real_id(mode, change, transport, socket, taskvex_home):
    with create_core() as core:
        original = seed(core)
        other = seed(core, "Keep this")
        chat = TextChat(core)
        try:
            name = "notes.delete" if change == "delete" else "notes.update"
            args = {"id": original["id"], **({} if change == "delete" else
                    {"text": "Edited note"} if change == "text" else {"done": True})}
            report = execute(chat, mode, "Temporary note adlı notu değiştir", [
                ("notes.select", {"kind":"text","text":"Temporary note","cardinality":"one"}, "read"), (name, args, "mutate")], transport, socket)
            assert report["ok"]
            final = report["tool_results"][-1]
            assert final["status"] == "succeeded" and final["result"]["verified"]
            assert final["result"]["evidence"]["read_back"]
            assert final["result"]["data"]["note"]["id"] == original["id"]
            saved = notes(taskvex_home)
            assert other in saved
            if change == "delete":
                assert saved == [other]
            else:
                assert saved[0] == {**original, **args}
        finally:
            assert chat.close()


@pytest.mark.parametrize("mode", ["rest", "live"])
@pytest.mark.parametrize("reason", ["no_list", "missing_target", "duplicate", "wrong_target", "multiple_ids"])
def test_unclear_target_does_not_change_any_record(mode, reason, transport, socket, taskvex_home):
    with create_core() as core:
        original = seed(core)
        other = seed(core, "Temporary note" if reason == "duplicate" else "Other note")
        before = (taskvex_home / "notes.json").read_bytes()
        prompt = {"missing_target": "Bir notu sil", "wrong_target": "Other note sil",
                  "multiple_ids": original["id"] + " " + other["id"]}.get(reason, "Temporary note sil")
        chat = TextChat(core)
        try:
            selector = ({'kind':'ids','ids':[original['id'],other['id']],'cardinality':'one'} if reason == 'multiple_ids' else
                {'kind':'text','text':'Other note' if reason == 'wrong_target' else 'Temporary note','cardinality':'one'})
            calls = [] if reason in {'no_list','missing_target'} else [('notes.select', selector, 'read')]
            report = execute(chat, mode, prompt, [*calls,
                ("notes.delete", {"id": original["id"]}, "delete")], transport, socket)
            assert not report["ok"] and report["code"] == "note_target_required"
            assert "Hangi notu" in report["error"] and not report.get("unknown")
            assert (taskvex_home / "notes.json").read_bytes() == before
        finally:
            assert chat.close()


@pytest.mark.parametrize("mode", ["rest", "live"])
def test_explicit_user_id_disambiguates_duplicate_text(mode, transport, socket, taskvex_home):
    with create_core() as core:
        first, second = seed(core), seed(core)
        chat = TextChat(core)
        try:
            report = execute(chat, mode, f"ID {second['id']} olan notu sil", [
                ("notes.select", {"kind":"ids","ids":[second["id"]],"cardinality":"one"}, "read"), ("notes.delete", {"id": second["id"]}, "delete")], transport, socket)
            assert report["ok"] and notes(taskvex_home) == [first]
        finally:
            assert chat.close()


@pytest.mark.parametrize("mode", ["rest", "live"])
@pytest.mark.parametrize("name", ["notes.update", "notes.delete"])
def test_mutation_replay_keeps_original_task_without_second_write(mode, name, transport, socket, taskvex_home, monkeypatch):
    with create_core() as core:
        original = seed(core)
        args = {"id": original["id"], **({"done": True} if name == "notes.update" else {})}
        writes = []
        original_write = JsonStore.write
        def write(store, data):
            writes.append(store.path)
            return original_write(store, data)
        monkeypatch.setattr(JsonStore, "write", write)
        chat = TextChat(core)
        try:
            report = execute(chat, mode, "Temporary note değiştir", [("notes.select", {"kind":"text","text":"Temporary note","cardinality":"one"}, "read"),
                (name, args, "mutate"), (name, args, "mutate")], transport, socket)
            assert report["ok"] and len(writes) == 1
            assert report["tool_results"][1]["task_id"] == report["tool_results"][2]["task_id"]
        finally:
            assert chat.close()


@pytest.mark.parametrize("mode", ["rest", "live"])
def test_disconnect_after_mutation_preserves_verified_result(mode, transport, socket, taskvex_home):
    with create_core() as core:
        original = seed(core)
        chat = TextChat(core)
        try:
            report = execute(chat, mode, "Temporary note sil", [("notes.select", {"kind":"text","text":"Temporary note","cardinality":"one"}, "read"),
                ("notes.delete", {"id": original["id"]}, "delete")], transport, socket, ending="disconnect")
            assert not report["ok"] and notes(taskvex_home) == []
            assert report["tool_results"][-1]["result"]["verified"]
            assert len(transport.requests) == 3 if mode == "rest" else socket.opened == 1
        finally:
            assert chat.close()


@pytest.mark.parametrize("mode", ["rest", "live"])
def test_unknown_write_is_not_retried_or_claimed_success(mode, transport, socket, monkeypatch, taskvex_home):
    with create_core() as core:
        original = seed(core)
        written = False
        original_write, original_read = JsonStore.write, JsonStore.read
        def write(store, data):
            nonlocal written
            original_write(store, data)
            written = True
        def read_store(store):
            if written:
                raise StoreError("read_failed", "Synthetic readback failure")
            return original_read(store)
        chat = TextChat(core)
        try:
            with monkeypatch.context() as patch:
                patch.setattr(JsonStore, "write", write)
                patch.setattr(JsonStore, "read", read_store)
                report = execute(chat, mode, "Temporary note sil", [("notes.select", {"kind":"text","text":"Temporary note","cardinality":"one"}, "read"),
                    ("notes.delete", {"id": original["id"]}, "delete")], transport, socket)
            assert not report["ok"] and report["code"] == "tool_unknown"
            assert report["tool_results"][-1]["status"] == "unknown"
            assert notes(taskvex_home) == []  # Yazı oldu; readback olmadığından başarı iddia edilmez.
        finally:
            assert chat.close()


@pytest.mark.parametrize("mode", ["rest", "live"])
def test_all_note_tools_hidden_until_native_transfer_confirmed(mode, transport, socket):
    with create_core() as core:
        chat = TextChat(core)
        try:
            report = execute(chat, mode, "Hello", [], transport, socket, ready=False)
            assert report["ok"]
            setup = transport.requests[0] if mode == "rest" else socket.sent[0]["setup"]
            assert {item["name"] for item in setup["tools"][0]["functionDeclarations"]} == {"apps.catalog", "system.status", "assistant.request_sleep_mode", "assistant.request_shutdown", "clocks.create", "clocks.control", "clocks.list"}
        finally:
            assert chat.close()


def test_old_list_or_repolled_result_cannot_authorize_new_mutation():
    with create_core() as core:
        original = seed(core)
        tools = gateway(core)
        tools.begin_turn("Temporary note done")
        previous = read(tools)
        task = tools.submit({"id": "update", "name": "notes.update", "arguments": {"id": original["id"], "done": True, "expected_snapshot": current_snapshot()}})
        assert tools.result(task.task_id, timeout=2)["result"]["verified"]
        tools.result(previous.task_id)
        with pytest.raises(NoteTargetError):
            tools.submit({"id": "delete", "name": "notes.delete", "arguments": {"id": original["id"]}})
        tools.begin_turn("Temporary note sil")
        tools.result(previous.task_id)
        with pytest.raises(NoteTargetError):
            tools.submit({"id": "delete", "name": "notes.delete", "arguments": {"id": original["id"]}})


def test_failed_fresh_read_cannot_leave_previous_target_authorized(monkeypatch):
    with create_core() as core:
        original = seed(core)
        tools = gateway(core)
        tools.begin_turn("Temporary note sil")
        read(tools)
        def failed_read(store):
            raise StoreError("read_failed", "Synthetic failure")
        monkeypatch.setattr(JsonStore, "read", failed_read)
        task = tools.submit({"id": "read-again", "name": "notes.select", "arguments": {"kind":"text","text":"Temporary note","cardinality":"one"}})
        assert tools.result(task.task_id, timeout=2)["status"] == "failed"
        with pytest.raises(NoteTargetError):
            tools.submit({"id": "delete", "name": "notes.delete", "arguments": {"id": original["id"]}})


def test_delete_replay_after_live_resume_preserves_ids_and_single_mutation(wire, taskvex_home):
    with create_core() as core:
        original = seed(core)
        delete = live_call("notes.delete", {"id": original["id"], "expected_snapshot": current_snapshot()}, "delete")
        wire.plans = [{"turns": [[live_call("notes.select", {"kind":"text","text":"Temporary note","cardinality":"one"}, "read"), delete, frame("Deleted", complete=True)]],
                       "idle": [[checkpoint(), GOAWAY]]},
                      {"turns": [[delete, frame("Same completed result", complete=True)]]}]
        chat = TextChat(core)
        try:
            first = chat.run_live("Temporary note sil", "future-live", notes_ready=True)
            second = chat.run_live("Replay check", "future-live", notes_ready=True)
            assert first["ok"] and second["ok"] and second["session_resumed"]
            assert first["logical_session_id"] == second["logical_session_id"]
            assert first["tool_results"][-1]["task_id"] == second["tool_results"][0]["task_id"]
            assert notes(taskvex_home) == []
        finally:
            assert chat.close() and wire.opened == wire.closed


@pytest.mark.parametrize("arguments", [{"done": "true"}, {"text": ""}, {"done": True, "principal": "admin"}])
def test_target_guard_does_not_replace_registry_validation(arguments):
    with create_core() as core:
        original = seed(core)
        tools = gateway(core)
        tools.begin_turn("Temporary note güncelle")
        read(tools)
        with pytest.raises(ContractError):
            tools.submit({"id": "bad", "name": "notes.update", "arguments": {"id": original["id"], "expected_snapshot": current_snapshot(), **arguments}})


@pytest.mark.parametrize("mode", ["rest", "live"])
@pytest.mark.parametrize("name", ["notes.update", "notes.delete"])
def test_stop_after_verified_mutation_keeps_the_real_result(mode, name, transport, socket, taskvex_home):
    """İşlemden sonraki model beklemesini durdurmak dosya yazısını geri alamaz."""
    entered, release = Event(), Event()
    def blocked(request):
        entered.set()
        assert release.wait(5)
        return reply([{"text": "Late answer"}])
    with create_core() as core, ThreadPoolExecutor(max_workers=1) as pool:
        original = seed(core)
        args = {"id": original["id"], "expected_snapshot": current_snapshot(), **({"done": True} if name == "notes.update" else {})}
        chat = TextChat(core)
        try:
            calls = [("notes.select", {"kind":"text","text":"Temporary note","cardinality":"one"}, "read"), (name, args, "mutation")]
            if mode == "rest":
                transport.responses = [*[reply([rest_call(n, a, i)]) for n, a, i in calls], blocked]
                running = pool.submit(chat.run, "Temporary note değiştir", gemini.DEFAULT_MODEL, request_id="stop-mutation")
                assert entered.wait(3)
            else:
                socket.frames = [{"setupComplete": {}}, *[live_call(n, a, i) for n, a, i in calls]]
                socket.stall = True
                running = pool.submit(chat.run_live, "Temporary note değiştir", "future-live",
                                      notes_ready=True, request_id="stop-mutation")
                assert socket.waiting.wait(3)
            accepted = chat.stop("stop-mutation")
            assert accepted["ok"] and not accepted["completed"]
            release.set()
            report = running.result(5)
            assert report["stopped"] and not report["ok"] and report["completed"]
            assert report["tool_results"][-1]["result"]["verified"]
            assert notes(taskvex_home) == ([{**original, "done": True}] if name == "notes.update" else [])
            assert not chat.stop("stop-mutation")["ok"]
        finally:
            release.set()
            assert chat.close()
