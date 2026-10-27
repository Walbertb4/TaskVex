"""Private durable execution receipts; payloads belong to the current RAM owner.

One profile lock and FULL SQLite transactions preserve replay/UNKNOWN protection.
Schema 1 migration removes payloads without rerunning tools or making raw backups.
"""

from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import re
import sqlite3

from app.core.contracts import Task, TaskStatus, ToolError, ToolRequest, ToolResult, request_fingerprint
from app.storage.instance_lock import SingleInstance


class JournalError(RuntimeError):
    """Storage failed closed; never expose SQL, user paths or payloads."""


def _summary(task: Task) -> Task:
    """Retain identity/outcome without arguments, returned content or free-form errors."""
    result = None
    if task.status.terminal:
        result = ToolResult(task_id=task.task_id, status=task.status,
            verified=task.status == TaskStatus.SUCCEEDED,
            error=None if task.status == TaskStatus.SUCCEEDED else ToolError(
                code='historical_result', message='Historical outcome; original content is not retained'),
            evidence={'historical': True, 'content_available': False})
    return replace(task, request=replace(task.request, arguments={}), result=result)


def _encode(task: Task) -> str:
    """Persist only the fixed, content-free receipt contract."""
    return json.dumps(_summary(task).to_dict(), sort_keys=True, ensure_ascii=True, allow_nan=False)


def _decode_legacy(row) -> Task:
    """Read strict schema 1 only during migration; never execute its request."""
    principal, request_id, task_id, status, document = row
    data = json.loads(document)
    data['request'] = ToolRequest(**data['request'])
    data['status'] = TaskStatus(data['status'])
    if data['result'] is not None:
        result = data['result']
        result['status'] = TaskStatus(result['status'])
        if result['error'] is not None:
            result['error'] = ToolError(**result['error'])
        data['result'] = ToolResult(**result)
    task = Task(**data)
    if (principal, request_id, task_id, status) != (
            task.request.principal, task.request.request_id, task.task_id, task.status.value
    ) or json.dumps(task.to_dict(), sort_keys=True, ensure_ascii=True, allow_nan=False) != document:
        raise ValueError('Invalid task journal record')
    return task


def _decode(row) -> Task:
    """Reject malformed/non-private receipts rather than accepting a partial record."""
    *fields, fingerprint = row
    if type(fingerprint) is not str or re.fullmatch(r'sha256-v1:[0-9a-f]{64}', fingerprint) is None:
        raise ValueError('Invalid journal fingerprint')
    task = _decode_legacy(fields)
    if _encode(task) != fields[-1]:
        raise ValueError('Invalid private receipt')
    return task


def _create_tasks(db) -> None:
    """Use the same receipt schema for fresh profiles and atomic migration."""
    db.execute('CREATE TABLE tasks (principal TEXT NOT NULL, request_id TEXT NOT NULL, '
               'task_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, document TEXT NOT NULL, '
               'fingerprint TEXT NOT NULL, PRIMARY KEY (principal, request_id))')


class TaskJournal:
    """Single profile owner with bounded page cache and per-call connections.

    Calls are serialized by TaskManager. Disk receipts cannot restore RAM payloads.
    Closing releases the profile lock only after the execution worker has stopped.
    """

    def __init__(self, home: Path) -> None:
        self.path = home / 'tasks.sqlite3'
        self._owner = SingleInstance(home)
        self._owner.__enter__()
        try:
            fresh = not self.path.exists()
            with self._connect(create=fresh) as db:
                version = db.execute('PRAGMA user_version').fetchone()[0]
                if not fresh and version not in (1, 2):
                    raise ValueError('Unsupported journal version')
                if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('Corrupt journal')
                # Checkpoint legacy WAL before migration; new receipts use rollback journals.
                if db.execute('PRAGMA journal_mode').fetchone()[0] != 'delete':
                    db.execute('PRAGMA journal_mode=DELETE')
                db.execute('BEGIN IMMEDIATE')
                if fresh:
                    _create_tasks(db)
                elif version == 1:
                    db.execute('ALTER TABLE tasks RENAME TO legacy_tasks')
                    _create_tasks(db)
                    for row in db.execute('SELECT principal,request_id,task_id,status,document FROM legacy_tasks'):
                        task = _decode_legacy(row)
                        db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?)',
                            (*row[:4], _encode(task), request_fingerprint(task.request)))
                    db.execute('DROP TABLE legacy_tasks')
                if fresh or version == 1:
                    db.execute('CREATE TABLE privacy_state (id INTEGER PRIMARY KEY CHECK(id=1), '
                               'needs_vacuum INTEGER NOT NULL CHECK(needs_vacuum IN (0,1)))')
                    db.execute('INSERT INTO privacy_state VALUES (1,?)', (int(not fresh),))
                    db.execute('PRAGMA user_version=2')
                state = db.execute('SELECT id,needs_vacuum FROM privacy_state').fetchall()
                if state not in ([(1, 0)], [(1, 1)]):
                    raise ValueError('Invalid privacy state')
                needs_vacuum = bool(state[0][1])
                db.execute('CREATE TABLE IF NOT EXISTS task_acknowledgements '
                           '(task_id TEXT PRIMARY KEY, acknowledged_at TEXT NOT NULL)')
                if db.execute('SELECT 1 FROM task_acknowledgements a LEFT JOIN tasks t '
                              'ON t.task_id=a.task_id WHERE t.task_id IS NULL OR t.status!=? LIMIT 1',
                              (TaskStatus.UNKNOWN.value,)).fetchone():
                    raise ValueError('Invalid task acknowledgement')
                # Validate history one record at a time, without loading it all into RAM.
                for row in db.execute('SELECT principal,request_id,task_id,status,document,fingerprint FROM tasks'):
                    task = _decode(row)
                    if not task.status.terminal:
                        status = (TaskStatus.CANCELLED if task.status == TaskStatus.QUEUED
                                  else TaskStatus.UNKNOWN)
                        result = ToolResult(task_id=task.task_id, status=status,
                            error=ToolError(code='process_interrupted',
                                            message='Previous process ended before completion'))
                        task = replace(task, status=status, result=result)
                        db.execute('UPDATE tasks SET status=?, document=? WHERE task_id=?',
                                   (status.value, _encode(task), task.task_id))
                self.uncertain = db.execute('SELECT 1 FROM tasks t WHERE status=? AND NOT EXISTS '
                    '(SELECT 1 FROM task_acknowledgements a WHERE a.task_id=t.task_id) LIMIT 1',
                    (TaskStatus.UNKNOWN.value,)).fetchone() is not None
            if needs_vacuum:
                # A durable pending flag makes cleanup retryable after failure/crash.
                with self._connect() as db:
                    db.execute('VACUUM')
                with self._connect() as db:
                    db.execute('UPDATE privacy_state SET needs_vacuum=0 WHERE id=1')
        except BaseException:
            self.close()
            raise

    @contextmanager
    def _connect(self, *, create: bool = False):
        """Recreating the missing file at runtime; silent dedup loss prohibited."""
        try:
            db = sqlite3.connect(self.path.as_uri() + ('?mode=rwc' if create else '?mode=rw'),
                                 uri=True, timeout=2)
            try:
                db.execute('PRAGMA synchronous=FULL')
                db.execute('PRAGMA cache_size=-1024')
                db.execute('PRAGMA secure_delete=ON')
                with db:
                    yield db
            finally:
                db.close()
        except (sqlite3.Error, ValueError, TypeError, KeyError, RecursionError):
            raise JournalError('Task journal could not be verified or saved') from None

    def find(self, principal: str, request_id: str) -> tuple[Task, str] | None:
        """Return the private receipt and original equality digest, never its payload."""
        with self._connect() as db:
            row = db.execute('SELECT principal,request_id,task_id,status,document,fingerprint FROM tasks '
                             'WHERE principal=? AND request_id=?', (principal, request_id)).fetchone()
            return (_decode(row), row[-1]) if row else None

    def has_requests(self, principal: str, prefix: str) -> bool:
        """Indexed history probe prevents a lost logical plan from blindly restarting."""
        with self._connect() as db:
            return db.execute('SELECT 1 FROM tasks WHERE principal=? AND request_id>=? '
                              'AND request_id<? LIMIT 1', (principal, prefix, prefix + '\uffff')).fetchone() is not None

    def get(self, task_id: str) -> Task | None:
        """Query RAM allocated terminal tasks with actual task_id."""
        with self._connect() as db:
            row = db.execute('SELECT principal,request_id,task_id,status,document,fingerprint FROM tasks '
                             'WHERE task_id=?', (task_id,)).fetchone()
            return _decode(row) if row else None

    def unresolved(self) -> list[Task]:
        """Return a bounded review page; never change original task documents."""
        with self._connect() as db:
            rows = db.execute('SELECT principal,request_id,t.task_id,status,document,fingerprint FROM tasks t '
                'WHERE status=? AND NOT EXISTS (SELECT 1 FROM task_acknowledgements a '
                'WHERE a.task_id=t.task_id) ORDER BY t.task_id LIMIT 256', (TaskStatus.UNKNOWN.value,))
            return [_decode(row) for row in rows]

    def acknowledge(self, task_ids: list[str]) -> None:
        """Durably record explicit acceptance of uncertainty, never success or replay."""
        with self._connect() as db:
            for task_id in task_ids:
                row = db.execute('SELECT status FROM tasks WHERE task_id=?', (task_id,)).fetchone()
                if row is None or row[0] != TaskStatus.UNKNOWN.value:
                    raise ValueError('Only unknown tasks can be acknowledged')
                db.execute("INSERT OR IGNORE INTO task_acknowledgements VALUES (?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                           (task_id,))

    def save(self, task: Task) -> None:
        """Atomic save single task state while preserving identities; commit error goes up."""
        with self._connect() as db:
            changed = db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?) ON CONFLICT(task_id) '
                       'DO UPDATE SET status=excluded.status, document=excluded.document '
                       'WHERE tasks.principal=excluded.principal AND tasks.request_id=excluded.request_id '
                       'AND tasks.fingerprint=excluded.fingerprint',
                       (task.request.principal, task.request.request_id, task.task_id,
                        task.status.value, _encode(task), request_fingerprint(task.request)))
            if changed.rowcount != 1:
                raise ValueError('Journal identity/content conflict')

    def close(self) -> None:
        """Release the lock after the worker actually stops; deleting files."""
        self._owner.__exit__(None, None, None)
