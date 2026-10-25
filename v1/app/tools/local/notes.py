"""Add/list/update/delete notes; here is the schema of the notes file.

JSON store controls file integrity, registry controls entry format, and policy controls permission.
This module does not import UI and does not start its own worker. All mutations are single
Must be sorted via TaskManager; Parallel writes to the same file are not supported.
Legacy UI notes are only given to initialize via the host's explicit transport stream.
"""

from uuid import uuid4
from datetime import datetime, timezone
from hashlib import sha256
from dataclasses import replace
import json

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult
from app.storage.json_store import JsonStore, StoreError


MAX_NOTE_LENGTH = 10_000
SNAPSHOT_SCHEMA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
CREATED_AT_SCHEMA = {"anyOf": [{"type": "null"}, {"type": "string",
    "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"}]}
ADD_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string", "minLength": 1,
                              "maxLength": MAX_NOTE_LENGTH, "pattern": r"\S"}},
    "required": ["text"],
    "additionalProperties": False,
}
UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "pattern": r"\S"},
        "text": ADD_SCHEMA["properties"]["text"],
        "done": {"type": "boolean"},
        "expected_snapshot": SNAPSHOT_SCHEMA,
    },
    "required": ["id"],
    "anyOf": [{"required": ["text"]}, {"required": ["done"]}],
    "additionalProperties": False,
}
DELETE_SCHEMA = {
    "type": "object",
    "properties": {"id": {"type": "string", "pattern": r"\S"}, "expected_snapshot": SNAPSHOT_SCHEMA},
    "required": ["id"],
    "additionalProperties": False,
}
DELETE_MANY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"ids": {"type": "array", "minItems": 1, "uniqueItems": True,
        "items": {"type": "string", "pattern": r"\S"}}, "expected_snapshot": SNAPSHOT_SCHEMA},
    "required": ["ids", "expected_snapshot"],
}
COMPLETE_MANY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {**DELETE_MANY_SCHEMA["properties"], "done": {"type": "boolean"}},
    "required": ["ids", "expected_snapshot", "done"],
}
SELECT_SCHEMA = {"type": "object", "properties": {
    "kind": {"enum": ["ids", "text", "contains", "latest", "all"]},
    "cardinality": {"enum": ["one", "many"]},
    "ids": DELETE_MANY_SCHEMA["properties"]["ids"], "text": ADD_SCHEMA["properties"]["text"],
    "count": {"type": "integer", "minimum": 1}}, "required": ["kind", "cardinality"], "anyOf": [
    {"type": "object", "additionalProperties": False, "properties": {
        "kind": {"enum": ["ids"]}, "ids": DELETE_MANY_SCHEMA["properties"]["ids"],
        "cardinality": {"enum": ["one", "many"]}}, "required": ["kind", "ids", "cardinality"]},
    {"type": "object", "additionalProperties": False, "properties": {
        "kind": {"enum": ["text", "contains"]}, "text": ADD_SCHEMA["properties"]["text"],
        "cardinality": {"enum": ["one", "many"]}}, "required": ["kind", "text", "cardinality"]},
    {"type": "object", "additionalProperties": False, "properties": {
        "kind": {"enum": ["latest"]}, "count": {"type": "integer", "minimum": 1},
        "cardinality": {"enum": ["one", "many"]}}, "required": ["kind", "count", "cardinality"]},
    {"type": "object", "additionalProperties": False, "properties": {
        "kind": {"enum": ["all"]}, "cardinality": {"enum": ["many"]}}, "required": ["kind", "cardinality"]},
]}
INITIALIZE_SCHEMA = {
    "type": "object",
    "properties": {"notes": {"anyOf": [
        {"type": "null"},
        {"type": "array", "items": {
            "type": "object", "properties": {
                "text": ADD_SCHEMA["properties"]["text"], "done": {"type": "boolean"},
                "created_at": CREATED_AT_SCHEMA},
            "required": ["text", "done"], "additionalProperties": False,
        }},
    ]}},
    "required": ["notes"], "additionalProperties": False,
}
REPLACE_SCHEMA = {
    "type": "object", "properties": {"notes": {"type": "array", "items": {
        "type": "object", "properties": {
            "id": {"type": "string", "pattern": r"\S"},
            "text": ADD_SCHEMA["properties"]["text"], "done": {"type": "boolean"},
            "created_at": CREATED_AT_SCHEMA},
        "required": ["id", "text", "done"], "additionalProperties": False,
    }}}, "required": ["notes"], "additionalProperties": False,
}


def _valid_text(value) -> bool:
    """Empty/alone reject spaces or excessively long text; change the original text."""
    return isinstance(value, str) and bool(value.strip()) and len(value) <= MAX_NOTE_LENGTH


def notes_snapshot(notes: list[dict]) -> str:
    """Generate the repository fingerprint that captures the change ID/content/date/status.

    It is not a secret authorization key. ModelTools checks the owner of the fresh selection;
    This value verifies in the worker that the data has not changed after the selection.
    """
    return sha256(json.dumps(notes, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def _fold_text(value: str) -> str:
    """Literal text comparison; It does not parse natural language intent or regex."""
    return ' '.join(value.casefold().replace('i\u0307', 'i').split())


def _valid_created_at(value) -> bool:
    """Verify UTC date with real calendar; The unknown date of the old record may be null.

    Only YYYY-MM-DDTHH:mm:ss.sssZ format is used. Day/month overflow and local
    time uncertainty is not accepted; When reading a record, no artificial history is written into the past.
    """
    if value is None:
        return True
    if not isinstance(value, str) or len(value) != 24 or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.isoformat(timespec="milliseconds").replace("+00:00", "Z") == value
    except ValueError:
        return False


def _error(context: ToolContext, code: str, message: str,
           status: TaskStatus = TaskStatus.FAILED) -> ToolResult:
    """Internalerik/file Convert the expected error to the common result without leaking the path."""
    return ToolResult(task_id=context.task_id, status=status,
                      error=ToolError(code=code, message=message))


class NotesTools:
    """It executes not CRUD operations on the single JsonStore provided by the host.

    Persistent format: {notes: [{id, text, done, created_at?}]}.
    created_at is the UTC time of the backend in the new record; missing/null in old record
    This means that the actual creation time is unknown.
    id is generated when the record is created and does not change on restart. UI is outdated
    The native adapter converts {t,d} format. ui_migrated flag of migration
    keeps its completion in the same atomic file as the notes; There is no separate flag file.
    """

    def __init__(self, store: JsonStore) -> None:
        """The host chooses the file path; The file path is not taken with the tool parameter."""
        self._store = store

    def _load_document(self) -> dict:
        """Deleting corrupt note records as empty even if the JSON is valid.

        Missing file means new repository. The notes list is mandatory in the existing file;
        We explicitly reject unrecognized areas so as not to overwrite them and lose them.
        """
        data = self._store.read()
        if data is None:
            return {"notes": []}
        if (not {"notes"} <= set(data) <= {"notes", "ui_migrated"}
                or type(data["notes"]) is not list
                or ("ui_migrated" in data and type(data["ui_migrated"]) is not bool)):
            raise StoreError("invalid_notes", "Stored notes have an invalid shape")
        seen = set()
        for note in data["notes"]:
            if (type(note) is not dict or not {"id", "text", "done"} <= set(note) <= {"id", "text", "done", "created_at"}
                    or not isinstance(note["id"], str) or not note["id"].strip()
                    or note["id"] in seen or not _valid_text(note["text"])
                    or type(note["done"]) is not bool or not _valid_created_at(note.get("created_at"))):
                raise StoreError("invalid_notes", "Stored notes have an invalid record")
            seen.add(note["id"])
        return data

    def _load(self) -> list[dict]:
        """For CRUD callers, get only the list of notes from the validated document."""
        return self._load_document()["notes"]

    def initialize(self, arguments: dict, context: ToolContext) -> ToolResult:
        """read with notes:null; add old notes once in open transfer.

        Old core notes are preserved; old UI notes with same text also separate UUID
        takes. ui_migrated and added notes are written with a single replace. writing
        There is no auto-repeat if post-verification is unclear. On reopening
        If there is a check, the old list sent will not be re-added. This sign is normal
        With operations add/update/delete, the last note is preserved even if it is deleted.
        """
        incoming = arguments.get("notes")
        if (set(arguments) != {"notes"} or (incoming is not None and (
                type(incoming) is not list or any(
                    type(item) is not dict or not {"text", "done"} <= set(item) <= {"text", "done", "created_at"}
                    or not _valid_text(item["text"]) or type(item["done"]) is not bool
                    or not _valid_created_at(item.get("created_at"))
                    for item in incoming)))):
            return _error(context, "invalid_arguments", "Expected valid legacy notes or null")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            document = self._load_document()
            if incoming is not None and not document.get("ui_migrated", False):
                updated = [*document["notes"], *[{"id": uuid4().hex, **item} for item in incoming]]
                return self._commit(updated, None, context, migrated=True)
        except StoreError as error:
            return _error(context, error.code, str(error))
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                          data={"notes": document["notes"],
                                "migrated": document.get("ui_migrated", False)},
                          evidence={"store_read": True})

    def replace(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Replace full list with single atomic write in open backup import.

        Identities are protected; Generates ID UI adapter to old IDless replacement.
        Duplicate id and corrupted records are rejected before any write. broken
        The existing store will not be crushed again; The reset/repair is not a replacement.
        """
        items = arguments.get("notes")
        if (set(arguments) != {"notes"} or type(items) is not list or any(
                type(n) is not dict or not {"id", "text", "done"} <= set(n) <= {"id", "text", "done", "created_at"}
                or not isinstance(n["id"], str) or not n["id"].strip()
                or not _valid_text(n["text"]) or type(n["done"]) is not bool
                or not _valid_created_at(n.get("created_at")) for n in items)
                or len({n["id"] for n in items}) != len(items)):
            return _error(context, "invalid_arguments", "Expected valid notes with unique ids")
        return self._commit(items, None, context, migrated=True)

    def list(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Return the current list on disk; Creating file while reading missing repository."""
        if arguments:
            return _error(context, "invalid_arguments", "Notes list accepts no arguments")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED,
                          verified=True, data={"notes": notes}, evidence={"store_read": True})

    def select(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Apply the model's structured criteria deterministically on real records.

        Sentence, language or word order is not interpreted. zero/multiple in single selection
        mating does not produce mutation authority; candidates return for clarification. Latest
        Unknown date in the ranking or equality at the cutoff limit is guessed
        does not dissolve. Snapshot prevents action on the file that has changed after selection.
        """
        kind, cardinality = arguments.get('kind'), arguments.get('cardinality')
        fields = {'ids': {'ids'}, 'text': {'text'}, 'contains': {'text'}, 'latest': {'count'}, 'all': set()}
        if (not isinstance(kind, str) or kind not in fields or cardinality not in ('one', 'many')
                or set(arguments) != {'kind', 'cardinality'} | fields[kind]
                or kind == 'all' and cardinality != 'many'
                or kind in ('text', 'contains') and not _valid_text(arguments.get('text'))
                or kind == 'latest' and (type(arguments.get('count')) is not int or arguments['count'] < 1)
                or kind == 'ids' and (type(arguments.get('ids')) is not list or not arguments['ids']
                    or any(not isinstance(i, str) or not i.strip() for i in arguments['ids'])
                    or len(set(arguments['ids'])) != len(arguments['ids']))):
            return _error(context, 'invalid_arguments', 'Expected one structured note selector')
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        if kind == 'ids':
            targets = set(arguments['ids'])
            selected = [note for note in notes if note['id'] in targets]
            if len(selected) != len(arguments['ids']):
                return _error(context, 'not_found', 'One or more requested notes were not found; no selection was approved')
        elif kind in ('text', 'contains'):
            value = _fold_text(arguments['text'])
            selected = [note for note in notes if
                (_fold_text(note['text']) == value if kind == 'text' else value in _fold_text(note['text']))]
        elif kind == 'latest':
            count = arguments['count']
            if any(not note.get('created_at') for note in notes):
                return _error(context, 'note_target_required', 'Creation time is unknown; ask for actual note IDs')
            if count > len(notes):
                return _error(context, 'note_target_required', 'Fewer notes exist than requested; clarify the count')
            ordered = sorted(notes, key=lambda note: note['created_at'], reverse=True)
            if count < len(ordered) and ordered[count - 1]['created_at'] == ordered[count]['created_at']:
                return _error(context, 'note_target_required', 'Creation times tie at the selection boundary; ask for IDs')
            selected = ordered[:count]
        else:
            selected = notes
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
            data={'notes': selected, 'cardinality': cardinality,
                  'selection_ready': cardinality == 'many' or len(selected) == 1,
                  'snapshot': notes_snapshot(notes)}, evidence={'store_read': True})

    def add(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Save the note and verify by reading it back; Stay in limbo after registration.

        If canceled before writing, the file will remain untouched. After writing is finished
        Late cancellation will not be deemed to revoke the actual registration. Again while recording
        If the read is unsuccessful, UNKNOWN is returned, not FAILED; There is no automatic repeat.
        """
        if set(arguments) != {"text"} or not _valid_text(arguments["text"]):
            return _error(context, "invalid_arguments", "Expected non-blank note text")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
            note = {"id": uuid4().hex, "text": arguments["text"], "done": False,
                    "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")}
            updated = [*notes, note]
        except StoreError as error:
            return _error(context, error.code, str(error))
        return self._commit(updated, note, context)

    def update(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Replace text and/or completion status with fixed id.

        The missing area is preserved; done=False reopens the note. text equality or
        The list order does not select targets, so two notes with the same text will not get mixed up. target
        Otherwise, no new note will be created; not_found is returned and the file is left untouched.
        """
        if (not self._valid_target(arguments)
                or not set(arguments) <= {"id", "text", "done", "expected_snapshot"}
                or not ({"text", "done"} & set(arguments))
                or ("text" in arguments and not _valid_text(arguments["text"]))
                or ("done" in arguments and type(arguments["done"]) is not bool)):
            return _error(context, "invalid_arguments", "Expected id and valid text or done")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        if 'expected_snapshot' in arguments and arguments['expected_snapshot'] != notes_snapshot(notes):
            return _error(context, 'notes_changed', 'Notes changed after selection; no update was applied')
        original = next((note for note in notes if note["id"] == arguments["id"]), None)
        if original is None:
            return _error(context, "not_found", "Note was not found")
        note = {**original, **{k: v for k, v in arguments.items() if k != 'expected_snapshot'}}
        updated = [note if item["id"] == note["id"] else item for item in notes]
        return self._commit(updated, note, context)

    def delete(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Just delete the given id; keep other notes with the same text intact.

        A target not found gives an error. Duplicate the same request_id in TaskManager
        prevents in the current session; This handler does not retry on its own.
        """
        if not self._valid_target(arguments) or not set(arguments) <= {"id", "expected_snapshot"}:
            return _error(context, "invalid_arguments", "Expected a note id")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        if 'expected_snapshot' in arguments and arguments['expected_snapshot'] != notes_snapshot(notes):
            return _error(context, 'notes_changed', 'Notes changed after selection; no deletion was applied')
        note = next((item for item in notes if item["id"] == arguments["id"]), None)
        if note is None:
            return _error(context, "not_found", "Note was not found")
        updated = [item for item in notes if item["id"] != note["id"]]
        return self._commit(updated, note, context)

    def delete_many(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Delete full ID set with single text; missing/stale delete none on target.

        A separate task/delete loop is not established for each record. Same _commit cancel,
        It implements atomic file replacement and readback. Late Stop completed
        does not undo deletion; Authentication loss is preserved as UNKNOWN.
        """
        ids = arguments.get('ids')
        if (set(arguments) != {'ids', 'expected_snapshot'} or type(ids) is not list or not ids
                or any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids)):
            return _error(context, 'invalid_arguments', 'Expected unique note IDs and the selected snapshot')
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        if arguments['expected_snapshot'] != notes_snapshot(notes):
            return _error(context, 'notes_changed', 'Notes changed after selection; no deletion was applied')
        targets = set(ids)
        if not targets <= {note['id'] for note in notes}:
            return _error(context, 'not_found', 'One or more notes were not found; none were deleted')
        result = self._commit([note for note in notes if note['id'] not in targets], None, context)
        if result.verified:
            return replace(result, data={**result.data, 'deleted_ids': ids, 'deleted_count': len(ids)})
        return result

    def complete_many(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Change only done in the selected full group; text/identity/date is protected.

        done=True completes, False reopens. Missing ID or changed snapshot
        If there is, no record is written. Same atomicity as single _commit bulk delete
        applies writing, late cancellation and indefinite readback rules.
        """
        ids = arguments.get('ids')
        if (set(arguments) != {'ids', 'expected_snapshot', 'done'} or type(ids) is not list or not ids
                or any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids)
                or type(arguments.get('done')) is not bool):
            return _error(context, 'invalid_arguments', 'Expected unique IDs, selected snapshot and boolean done')
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        if arguments['expected_snapshot'] != notes_snapshot(notes):
            return _error(context, 'notes_changed', 'Notes changed after selection; no completion was applied')
        targets = set(ids)
        if not targets <= {note['id'] for note in notes}:
            return _error(context, 'not_found', 'One or more notes were not found; none were changed')
        updated = [{**note, 'done': arguments['done']} if note['id'] in targets else note for note in notes]
        result = self._commit(updated, None, context)
        if result.verified:
            return replace(result, data={**result.data, 'updated_ids': ids,
                'updated_count': len(ids), 'done': arguments['done']})
        return result

    @staticmethod
    def _valid_target(arguments: dict) -> bool:
        """Also reject ID is empty/wrong in direct call outside registry."""
        return isinstance(arguments.get("id"), str) and bool(arguments["id"].strip())

    def _commit(self, updated: list[dict], note: dict | None, context: ToolContext,
                *, migrated: bool = False) -> ToolResult:
        """Apply the same cancel/write/re-read contract to all note mutations.

        Note on success, new record on adding/updating; It is the record deleted in deletion.
        note=None is for batch transfer/restore/delete; Returns the fully verified list.
        If readback fails, the written data is not retrieved and UNKNOWN is returned.
        """
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            # The transfer token is metadata; old UI if ordinary CRUD drops it
            # cache can be added a second time on reboot. Keep it the same.
            document = {**self._load_document(), "notes": updated}
            if migrated:
                document["ui_migrated"] = True
            if context.cancel_event.is_set():
                return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
            self._store.write(document)
        except StoreError as error:
            return _error(context, error.code, str(error))
        try:
            if self._load_document() != document:
                raise StoreError("commit_unverified", "Saved notes could not be verified")
        except StoreError:
            return _error(context, "commit_unverified", "Saved notes could not be verified",
                          TaskStatus.UNKNOWN)
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED,
                          verified=True,
                          data={"note": note} if note is not None else {"notes": updated, "migrated": document.get('ui_migrated', False)},
                          evidence={"persisted": True, "read_back": True,
                                    **({"note_id": note["id"]} if note is not None else {})})
