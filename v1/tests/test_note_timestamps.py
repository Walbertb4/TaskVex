"""Try the permanence of note time and its compatibility with old records in real core.

Only temporary TASKVEX_HOME is used. The creation time is added to the file;
History that is not in the old record is not invented. Model/UI with ordinary update
cannot change history; Open backup restoration, on the other hand, preserves verified metadata.
"""

from datetime import datetime, timezone, timedelta

import pytest

from app.bootstrap import create_core
from app.session.tool_registry import RegistryError
from app.storage.json_store import JsonStore
from test_local_tools import request, run


def confirmed(core, req):
    """Request verified terminal result, not acceptance; Do not continue with None results."""
    task = run(core, req)
    assert task.result is not None and task.result.verified
    return task.result


def test_new_note_time_survives_replay_edit_complete_and_reopen(taskvex_home):
    before = datetime.now(timezone.utc) - timedelta(milliseconds=1)
    with create_core() as core:
        add = request("notes.add", "add", {"text": "Temporary dated note"})
        first = confirmed(core, add).data["note"]
        created = datetime.fromisoformat(first["created_at"])
        assert before <= created <= datetime.now(timezone.utc)
        assert first["created_at"].endswith("Z") and len(first["created_at"]) == 24
        assert confirmed(core, add).data["note"] == first
        changed = confirmed(core, request("notes.update", "edit", {"id": first["id"], "text": "Edited", "done": True})).data["note"]
        assert changed == {**first, "text": "Edited", "done": True}
    with create_core() as core:
        assert confirmed(core, request("notes.list", "list")).data["notes"] == [changed]
        stored = JsonStore(taskvex_home / "notes.json").read()
        assert stored is not None and stored["notes"] == [changed]


@pytest.mark.parametrize("metadata", [{}, {"created_at": None}])
def test_legacy_note_unknown_time_is_not_invented_or_rewritten(taskvex_home, metadata):
    old = {"id": "old-id", "text": "Old note", "done": False, **metadata}
    store = JsonStore(taskvex_home / "notes.json")
    store.write({"notes": [old]})
    original = store.path.read_bytes()
    with create_core() as core:
        assert confirmed(core, request("notes.list", "read")).data["notes"] == [old]
        assert store.path.read_bytes() == original
        result = confirmed(core, request("notes.update", "edit", {"id": old["id"], "done": True}))
        assert result.data["note"] == {**old, "done": True}


@pytest.mark.parametrize("tool", ["notes.initialize", "notes.replace"])
def test_import_keeps_known_time_and_leaves_unknown_time_unknown(tool, taskvex_home):
    dated = {"text": "Imported", "done": False, "created_at": "2024-02-29T12:34:56.789Z"}
    unknown = {"text": "Legacy", "done": False}
    if tool == "notes.replace":
        dated["id"], unknown["id"] = "backup-id", "legacy-id"
    with create_core() as core:
        result = confirmed(core, request(tool, "import", {"notes": [dated, unknown]}))
        saved = result.data["notes"]
        assert saved[0]["created_at"] == dated["created_at"] and "created_at" not in saved[1]
        if tool == "notes.replace":
            assert saved == [dated, unknown]
    with create_core() as core:
        assert confirmed(core, request("notes.list", "reopen")).data["notes"] == saved


@pytest.mark.parametrize("value", [1, {}, [], "yesterday", "2026-02-30T12:00:00.000Z",
    "2026-10-22T12:00:00", "2026-10-22T12:00:00.000+03:00", "0000-01-01T00:00:00.000Z"])
def test_invalid_timestamp_rejected_before_import_writes(value, taskvex_home):
    store = JsonStore(taskvex_home / "notes.json")
    store.write({"notes": [{"id": "keep", "text": "Keep", "done": False}]})
    before = store.path.read_bytes()
    with create_core() as core:
        for name in ["notes.initialize", "notes.replace"]:
            note = {"text": "Invalid", "done": False, "created_at": value}
            if name == "notes.replace":
                note["id"] = "new-id"
            try:
                result = run(core, request(name, name, {"notes": [note]}))
            except RegistryError:
                pass
            else:
                assert result.status.value == "failed"
            assert store.path.read_bytes() == before


@pytest.mark.parametrize("tool", ["notes.add", "notes.update"])
def test_normal_mutation_cannot_supply_or_change_creation_time(tool):
    with create_core() as core:
        args = {"text": "Do not forge", "created_at": "2024-01-01T00:00:00.000Z"}
        if tool == "notes.update":
            args["id"] = "guessed"
        with pytest.raises(RegistryError):
            core.submit(request(tool, "forged", args))
