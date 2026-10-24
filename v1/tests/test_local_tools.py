"""Gerçek araçları registry/policy/worker/dosya hattında uçtan uca doğrula.

Her testin TASKVEX_HOME'u geçicidir; gerçek kullanıcı notları kullanılmaz.
Sistem testleri salt okunurdur. Hata testleri belirli dosya/sistem çağrılarını
kontrollü bozar; beklenmeyen başarı veya çift not oluşmamalıdır.
"""

from concurrent.futures import ThreadPoolExecutor
import json
from threading import Event

import pytest

from app.bootstrap import create_core
from app.config import get_data_home
from app.core.contracts import TaskStatus, ToolContext, ToolRequest
from app.session.tool_registry import RegistryError
from app.storage.json_store import JsonStore, StoreError
from app.tasks.manager import TaskManagerError
from app.tools.local.notes import NotesTools
from app.tools.local import telemetry


def request(tool, request_id="r1", arguments=None, **identity):
    """Güvenilir yerel girişte üretilecek isteği test için oluştur."""
    return ToolRequest(tool=tool, request_id=request_id,
                       source=identity.get("source", "desktop"),
                       principal=identity.get("principal", "local-user"),
                       arguments={} if arguments is None else arguments)


def run(manager, req):
    """Testi yalnız başvuru kabulünde bırakma; terminal sonucu bekle."""
    return manager.wait(manager.submit(req).task_id, 3)


def test_add_list_and_reopen_keep_stable_note_identity():
    path = get_data_home() / "notes.json"
    with create_core() as manager:
        empty = run(manager, request("notes.list"))
        assert empty.status == TaskStatus.SUCCEEDED
        assert empty.result.data == {"notes": []}
        assert not path.exists()
        added = run(manager, request("notes.add", "add", {"text": "Türkçe not 📝"}))
        assert added.status == TaskStatus.SUCCEEDED
        note = added.result.data["note"]
        assert note["text"] == "Türkçe not 📝" and note["done"] is False
        assert len(note["id"]) == 32
        assert added.result.evidence == {"persisted": True, "read_back": True, "note_id": note["id"]}
        assert json.loads(path.read_text("utf-8"))["data"] == {"notes": [note]}
    with create_core() as manager:
        listed = run(manager, request("notes.list", "reopen-list"))
        assert listed.result.data == {"notes": [note]}


def test_concurrent_replays_add_only_one_real_note():
    req = request("notes.add", arguments={"text": "Bir kere"})
    with create_core() as manager:
        with ThreadPoolExecutor(max_workers=4) as pool:
            tasks = list(pool.map(lambda _: manager.submit(req), range(12)))
        assert len({task.task_id for task in tasks}) == 1
        first = manager.wait(tasks[0].task_id, 3)
        assert first.status == TaskStatus.SUCCEEDED
        assert manager.submit(req).task_id == first.task_id
        with pytest.raises(TaskManagerError) as caught:
            manager.submit(request("notes.add", arguments={"text": "Farklı içerik"}))
        assert caught.value.code == "request_conflict"
        listed = run(manager, request("notes.list", "list"))
        assert listed.result.data["notes"] == [first.result.data["note"]]


def test_same_text_with_different_request_ids_creates_distinct_notes():
    with create_core() as manager:
        first = run(manager, request("notes.add", "a", {"text": "Aynı metin"}))
        second = run(manager, request("notes.add", "b", {"text": "Aynı metin"}))
        assert first.result.data["note"]["id"] != second.result.data["note"]["id"]
        assert len(run(manager, request("notes.list", "list")).result.data["notes"]) == 2


def test_update_reopen_and_delete_target_only_stable_id():
    """Aynı metinli iki not arasında hedef karışmaz; yeniden açılışta id korunur."""
    with create_core() as manager:
        first = run(manager, request("notes.add", "a", {"text": "Aynı"})).result.data["note"]
        second = run(manager, request("notes.add", "b", {"text": "Aynı"})).result.data["note"]
        note_id = first["id"]
        changed = run(manager, request("notes.update", "edit", {"id": note_id, "text": "Yeni", "done": True}))
        assert changed.status == TaskStatus.SUCCEEDED
        assert changed.result.verified is True
        assert changed.result.data["note"] == {**first, "text": "Yeni", "done": True}
        reopened = run(manager, request("notes.update", "undo-done", {"id": note_id, "done": False}))
        assert reopened.result.data["note"] == {**first, "text": "Yeni", "done": False}
    with create_core() as manager:
        assert run(manager, request("notes.list", "list")).result.data["notes"] == [
            {**first, "text": "Yeni", "done": False}, second,
        ]
        req = request("notes.delete", "delete", {"id": note_id})
        deleted = run(manager, req)
        assert deleted.status == TaskStatus.SUCCEEDED and deleted.result.verified is True
        assert deleted.result.data["note"]["id"] == note_id
        assert deleted.result.evidence["read_back"] is True
        assert manager.submit(req).task_id == deleted.task_id
        assert run(manager, request("notes.list", "remaining")).result.data == {"notes": [second]}


def test_ui_transfer_is_atomic_once_and_survives_all_notes_deleted():
    """Ayrı manager'da tekrar aktarım yeni kimlikle ikinci kayıt yaratmamalı."""
    legacy = [{"text": "Same", "done": False}, {"text": "Same", "done": True}]
    with create_core() as manager:
        existing = run(manager, request("notes.add", "existing", {"text": "Core"})).result.data["note"]
        migrated = run(manager, request("notes.initialize", "transfer", {"notes": legacy}))
        assert migrated.status == TaskStatus.SUCCEEDED
        first = migrated.result.data["notes"]
        assert first[0] == existing and len({n["id"] for n in first}) == 3
        assert [n["done"] for n in first] == [False, False, True]
    with create_core() as manager:
        again = run(manager, request("notes.initialize", "again", {"notes": legacy}))
        assert again.result.data == {"notes": first, "migrated": True}
        for note in first:
            assert run(manager, request("notes.delete", note["id"], {"id": note["id"]})).status == TaskStatus.SUCCEEDED
    with create_core() as manager:
        assert run(manager, request("notes.initialize", "last", {"notes": legacy})).result.data == {"notes": [], "migrated": True}


@pytest.mark.parametrize("tool,arguments", [
    ("notes.initialize", {"notes": [{"text": "x", "done": 1}]}),
    ("notes.initialize", {"notes": [None]}),
    ("notes.initialize", {"notes": [{"text": " ", "done": False}]}),
    ("notes.replace", {"notes": [{"id": "a", "text": "x", "done": False}] * 2}),
    ("notes.replace", {"notes": [None]}), ("notes.replace", {"notes": None}),
])
def test_bad_bulk_notes_never_change_existing_store(tool, arguments):
    store = JsonStore(get_data_home() / "notes.json")
    store.write({"notes": [{"id": "keep", "text": "Keep", "done": False}]})
    original = store.path.read_bytes()
    with create_core() as manager:
        try:
            task = run(manager, request(tool, "bad", arguments))
        except RegistryError:
            pass
        else:
            assert task.status == TaskStatus.FAILED
    assert store.path.read_bytes() == original


def test_backup_replace_keeps_ids_and_migration_marker():
    notes = [{"id": "from-backup", "text": "Restored", "done": True}]
    with create_core() as manager:
        result = run(manager, request("notes.replace", "restore", {"notes": notes}))
        assert result.status == TaskStatus.SUCCEEDED and result.result.verified
        assert result.result.data == {"notes": notes, "migrated": True}
        assert run(manager, request("notes.initialize", "read", {"notes": None})).result.data == result.result.data
        assert run(manager, request("notes.update", "update", {"id": "from-backup", "done": False})).status == TaskStatus.SUCCEEDED
    assert JsonStore(get_data_home() / "notes.json").read()["ui_migrated"] is True


@pytest.mark.parametrize("tool", ["notes.initialize", "notes.replace"])
@pytest.mark.parametrize("failure", ["write", "readback", "corrupt"])
def test_bulk_transfer_failure_preserves_source_or_reports_unknown(monkeypatch, tool, failure):
    store = JsonStore(get_data_home() / "notes.json")
    note = {"id": "existing", "text": "Keep", "done": False}
    store.write({"notes": [note]})
    if failure == "corrupt":
        store.path.write_bytes(b"{broken")
    original = store.path.read_bytes()
    real_write = JsonStore.write

    def write(self, data):
        if failure == "write":
            raise StoreError("write_failed", "Could not save")
        real_write(self, data)
        if failure == "readback":
            monkeypatch.setattr(JsonStore, "read", lambda self: {"notes": [note]})

    monkeypatch.setattr(JsonStore, "write", write)
    incoming = [{"text": "UI", "done": False}]
    if tool == "notes.replace":
        incoming[0]["id"] = "restored"
    with create_core() as manager:
        result = run(manager, request(tool, arguments={"notes": incoming}))
        assert result.status == (TaskStatus.UNKNOWN if failure == "readback" else TaskStatus.FAILED)
    if failure != "readback":
        assert store.path.read_bytes() == original
    else:
        assert json.loads(store.path.read_text("utf-8"))["data"]["ui_migrated"] is True


@pytest.mark.parametrize("tool,arguments", [
    ("notes.update", {"id": "missing", "done": True}), ("notes.delete", {"id": "missing"}),
])
@pytest.mark.parametrize("existing", [False, True])
def test_missing_note_does_not_create_or_rewrite_store(tool, arguments, existing):
    path = get_data_home() / "notes.json"
    with create_core() as manager:
        if existing:
            run(manager, request("notes.add", "first", {"text": "Keep"}))
        before = path.read_bytes() if existing else None
        failed = run(manager, request(tool, "missing", arguments))
        assert failed.status == TaskStatus.FAILED
        assert failed.result.error.code == "not_found"
        assert (path.read_bytes() if path.exists() else None) == before


@pytest.mark.parametrize("operation", ["update", "delete"])
@pytest.mark.parametrize("failure", ["write", "readback", "cancel_before", "cancel_after"])
def test_note_mutations_keep_commit_and_cancellation_contract(monkeypatch, operation, failure):
    """Gerçek dosyada hata/iptal sınırlarını dene; yazılmış veri yok sayılmasın."""
    store = JsonStore(get_data_home() / "notes.json")
    original = {"id": "stable-id", "text": "Keep", "done": False}
    store.write({"notes": [original]})
    before = store.path.read_bytes()
    arguments = {"id": original["id"]}
    if operation == "update":
        arguments["done"] = True
    req = request("notes." + operation, arguments=arguments)
    context = ToolContext(task_id="mutation-test", request=req)
    real_write, real_read = store.write, store.read

    def write(data):
        if failure == "write":
            raise StoreError("write_failed", "Could not save")
        real_write(data)
        if failure == "readback":
            monkeypatch.setattr(store, "read", lambda: {"notes": [original]})
        elif failure == "cancel_after":
            context.cancel_event.set()

    def read():
        data = real_read()
        if failure == "cancel_before":
            context.cancel_event.set()
        return data

    monkeypatch.setattr(store, "write", write)
    monkeypatch.setattr(store, "read", read)
    result = getattr(NotesTools(store), operation)(arguments, context)
    expected = {"write": TaskStatus.FAILED, "readback": TaskStatus.UNKNOWN,
                "cancel_before": TaskStatus.CANCELLED, "cancel_after": TaskStatus.SUCCEEDED}
    assert result.status == expected[failure]
    if failure in {"write", "cancel_before"}:
        assert store.path.read_bytes() == before
    else:
        saved = json.loads(store.path.read_text("utf-8"))["data"]["notes"]
        assert saved == ([{**original, "done": True}] if operation == "update" else [])
    if failure == "readback":
        assert result.error.code == "commit_unverified"


@pytest.mark.parametrize("tool,arguments", [
    ("notes.add", {}), ("notes.add", {"text": ""}),
    ("notes.add", {"text": " \n\t"}), ("notes.add", {"text": None}),
    ("notes.add", {"text": 0}), ("notes.add", {"text": "x" * 10_001}),
    ("notes.add", {"text": "x", "path": "other.json"}),
    ("notes.update", {}), ("notes.update", {"id": "x"}),
    ("notes.update", {"id": "x", "done": 0}),
    ("notes.update", {"id": " ", "done": True}),
    ("notes.update", {"id": "x", "text": ""}),
    ("notes.update", {"id": "x", "text": None}),
    ("notes.update", {"id": "x", "text": "x" * 10_001}),
    ("notes.update", {"id": "x", "done": True, "path": "other.json"}),
    ("notes.delete", {}), ("notes.delete", {"id": None}),
    ("notes.delete", {"id": " "}),
    ("notes.delete", {"id": "x", "text": "x"}),
    ("notes.list", {"anything": True}), ("system.status", {"anything": True}),
])
def test_bad_arguments_never_reach_local_handlers(tool, arguments, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid request reached a handler")

    monkeypatch.setattr(NotesTools, "add", forbidden)
    monkeypatch.setattr(NotesTools, "list", forbidden)
    monkeypatch.setattr(NotesTools, "update", forbidden)
    monkeypatch.setattr(NotesTools, "delete", forbidden)
    monkeypatch.setattr("app.bootstrap.system_status", forbidden)
    with create_core() as manager:
        with pytest.raises(RegistryError) as caught:
            manager.submit(request(tool, arguments=arguments))
        assert caught.value.code == "invalid_arguments"
    # Core başlangıcı artık yalnız kalıcı görev günlüğünü oluşturur.
    assert {p.name for p in get_data_home().iterdir()} == {'tasks'}


@pytest.mark.parametrize("identity", [{"principal": "other-user"}, {"source": "telegram"}])
@pytest.mark.parametrize("tool,arguments", [
    ("notes.add", {"text": "Denied"}),
    ("notes.update", {"id": "a", "done": True}), ("notes.delete", {"id": "a"}),
])
def test_real_note_tool_denies_wrong_identity_without_creating_file(identity, tool, arguments):
    with create_core() as manager:
        denied = run(manager, request(tool, arguments=arguments, **identity))
        assert denied.status == TaskStatus.FAILED
        assert denied.result.error.code == "permission_denied"
    # Core başlangıcı artık yalnız kalıcı görev günlüğünü oluşturur.
    assert {p.name for p in get_data_home().iterdir()} == {'tasks'}


@pytest.mark.parametrize("data", [
    {}, {"notes": None}, {"notes": [None]},
    {"notes": [{"id": "a", "text": "x", "done": 0}]},
    {"notes": [{"id": "a", "text": "x", "done": False}] * 2},
    {"notes": [], "unrecognized": "preserve this"},
])
def test_invalid_note_records_are_preserved_without_partial_append(data):
    store = JsonStore(get_data_home() / "notes.json")
    store.write(data)
    original = store.path.read_bytes()
    with create_core() as manager:
        for tool, args in [("notes.list", {}), ("notes.add", {"text": "Do not append"}),
                           ("notes.update", {"id": "a", "done": True}),
                           ("notes.delete", {"id": "a"})]:
            result = run(manager, request(tool, tool, args))
            assert result.status == TaskStatus.FAILED
            assert result.result.error.code == "invalid_notes"
    assert store.path.read_bytes() == original


def test_corrupt_json_is_explicitly_preserved_and_recoverable_through_real_tools():
    store = JsonStore(get_data_home() / "notes.json")
    store.path.parent.mkdir(parents=True)
    store.path.write_bytes(b"{broken")
    with create_core() as manager:
        failed = run(manager, request("notes.add", "bad", {"text": "Not saved"}))
        assert failed.status == TaskStatus.FAILED
        assert failed.result.error.code == "corrupt_data"
        assert store.path.read_bytes() == b"{broken"
        backup = store.recover_corrupt()
        added = run(manager, request("notes.add", "after-recovery", {"text": "Saved"}))
        assert added.status == TaskStatus.SUCCEEDED
        assert backup.read_bytes() == b"{broken"


def test_write_failure_reports_failure_and_keeps_existing_notes(monkeypatch):
    from app.storage import json_store

    with create_core() as manager:
        assert run(manager, request("notes.add", "first", {"text": "Keep"})).status == TaskStatus.SUCCEEDED
        path = get_data_home() / "notes.json"
        original = path.read_bytes()

        def fail(*args):
            raise PermissionError("private details")

        monkeypatch.setattr(json_store.os, "replace", fail)
        failed = run(manager, request("notes.add", "second", {"text": "Not saved"}))
        assert failed.status == TaskStatus.FAILED
        assert failed.result.error.code == "write_failed"
        assert path.read_bytes() == original
        assert "private" not in str(failed.result.to_dict())
        assert run(manager, request("notes.list", "list")).status == TaskStatus.SUCCEEDED


@pytest.mark.parametrize("mode", ["read_error", "mismatch"])
def test_unverified_commit_is_unknown_and_not_repeated(monkeypatch, mode):
    real_write = JsonStore.write

    def uncertain_write(store, data):
        real_write(store, data)

        def unconfirmed_read(self):
            if mode == "read_error":
                raise StoreError("read_failed", "Unavailable")
            return {"notes": []}

        monkeypatch.setattr(JsonStore, "read", unconfirmed_read)

    monkeypatch.setattr(JsonStore, "write", uncertain_write)
    with create_core() as manager:
        req = request("notes.add", arguments={"text": "Actually saved"})
        result = run(manager, req)
        assert result.status == TaskStatus.UNKNOWN
        assert result.result.error.code == "commit_unverified"
        assert manager.submit(req).task_id == result.task_id
        with pytest.raises(TaskManagerError) as caught:
            manager.submit(request("notes.add", "new", {"text": "Must not run"}))
        assert caught.value.code == "uncertain_state"
    saved = json.loads((get_data_home() / "notes.json").read_text("utf-8"))
    assert len(saved["data"]["notes"]) == 1


def test_queued_real_note_cancellation_never_writes_second_note(monkeypatch):
    entered, release = Event(), Event()
    real_read = JsonStore.read

    def blocked_read(store):
        if not entered.is_set():
            entered.set()
            assert release.wait(3)
        return real_read(store)

    monkeypatch.setattr(JsonStore, "read", blocked_read)
    with create_core() as manager:
        try:
            first = manager.submit(request("notes.add", "first", {"text": "Keep"}))
            assert entered.wait(3)
            second = manager.submit(request("notes.add", "second", {"text": "Cancelled"}))
            assert manager.cancel(second.task_id).status == TaskStatus.CANCELLED
        finally:
            release.set()
        assert manager.wait(first.task_id, 3).status == TaskStatus.SUCCEEDED
        listed = run(manager, request("notes.list", "list"))
        assert [n["text"] for n in listed.result.data["notes"]] == ["Keep"]


def test_late_cancellation_does_not_erase_a_verified_write(monkeypatch):
    req = request("notes.add", arguments={"text": "Saved before cancellation"})
    context = ToolContext(task_id="direct-test", request=req)
    store = JsonStore(get_data_home() / "notes.json")
    real_write = store.write

    def write_then_cancel(data):
        real_write(data)
        context.cancel_event.set()

    monkeypatch.setattr(store, "write", write_then_cancel)
    assert NotesTools(store).add(req.arguments, context).status == TaskStatus.SUCCEEDED
    assert len(store.read()["notes"]) == 1


def test_running_note_cancelled_after_read_does_not_write(monkeypatch):
    """Handler başladıktan sonra, disk yazımı öncesindeki iptal noktasını dene."""
    req = request("notes.add", arguments={"text": "Do not save"})
    context = ToolContext(task_id="direct-cancel", request=req)
    store = JsonStore(get_data_home() / "notes.json")
    real_read = store.read

    def read_then_cancel():
        data = real_read()
        context.cancel_event.set()
        return data

    monkeypatch.setattr(store, "read", read_then_cancel)
    assert NotesTools(store).add(req.arguments, context).status == TaskStatus.CANCELLED
    assert not store.path.exists()


def test_system_status_uses_real_read_only_system_calls():
    with create_core() as manager:
        result = run(manager, request("system.status"))
        assert result.status == TaskStatus.SUCCEEDED
        assert result.result.data["os"] == telemetry.platform.system()
        assert result.result.data["logical_cpu_count"] == telemetry.os.cpu_count()
        assert result.result.data["cpu_percent"] is None
        assert result.result.data["memory_percent"] is None
    # Core başlangıcı artık yalnız kalıcı görev günlüğünü oluşturur.
    assert {p.name for p in get_data_home().iterdir()} == {'tasks'}


@pytest.mark.parametrize("count", [None, 0])
def test_system_unavailable_cpu_count_is_not_replaced_with_fake_value(monkeypatch, count):
    monkeypatch.setattr(telemetry.os, "cpu_count", lambda: count)
    with create_core() as manager:
        result = run(manager, request("system.status"))
        assert result.status == TaskStatus.SUCCEEDED
        assert result.result.data["logical_cpu_count"] is count


def test_system_read_failure_is_not_a_fake_success(monkeypatch):
    def fail():
        raise OSError("private details")

    monkeypatch.setattr(telemetry.platform, "system", fail)
    with create_core() as manager:
        result = run(manager, request("system.status"))
        assert result.status == TaskStatus.FAILED
        assert result.result.error.code == "system_unavailable"
        assert "private" not in str(result.result.to_dict())
