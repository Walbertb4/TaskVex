"""It keeps the TaskManager's replay protection persistent with SQLite transactions.

This store does not operate tools. A single administrator of the same profile maintains OS lock;
The executor does not proceed until each write is completed with a FULL synchronous transaction.
On restart, queued jobs are canceled and started jobs become unknown; not replayable.
Records are not deleted from disk: RAM cleaning cannot turn old request into new job.
"""

from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import sqlite3

from app.core.contracts import Task, TaskStatus, ToolError, ToolRequest, ToolResult
from app.storage.instance_lock import SingleInstance


class JournalError(RuntimeError):
    """The repository is unreliable; leaking raw SQL, file path or user data."""


def _encode(task: Task) -> str:
    """Generate single task format on disk with fixed field order and strict JSON."""
    return json.dumps(task.to_dict(), sort_keys=True, ensure_ascii=True, allow_nan=False)


def _decode(row) -> Task:
    """Validate index IDs together with JSON; corrupt record is not considered empty."""
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
    ) or _encode(task) != document:
        raise ValueError('Invalid task journal record')
    return task


class TaskJournal:
    """Single printer and limited SQLite page cache in the directory chosen by the trusted host.

    Closes each transaction connection; SQLite objects are not shared between threads.
    Calls are queued under the TaskManager Condition lock. close solo possession
    leaves; Result-only queries of the closed manager can continue to run.
    """

    def __init__(self, home: Path) -> None:
        self.path = home / 'tasks.sqlite3'
        self._owner = SingleInstance(home)
        self._owner.__enter__()
        try:
            fresh = not self.path.exists()
            with self._connect(create=fresh) as db:
                if fresh:
                    db.execute('CREATE TABLE tasks (principal TEXT NOT NULL, request_id TEXT NOT NULL, '
                               'task_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, document TEXT NOT NULL, '
                               'PRIMARY KEY (principal, request_id))')
                    db.execute('PRAGMA user_version=1')
                if db.execute('PRAGMA user_version').fetchone()[0] != 1:
                    raise ValueError('Unsupported journal version')
                if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('Corrupt journal')
                # Verify all records one by one; Loading the entire history into RAM.
                self.uncertain = False
                for row in db.execute('SELECT principal, request_id, task_id, status, document FROM tasks'):
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
                    self.uncertain |= task.status == TaskStatus.UNKNOWN
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
                with db:
                    yield db
            finally:
                db.close()
        except (sqlite3.Error, ValueError, TypeError, KeyError, RecursionError):
            raise JournalError('Task journal could not be verified or saved') from None

    def find(self, principal: str, request_id: str) -> Task | None:
        """Read the same user/request old record from disk index; do not execute."""
        with self._connect() as db:
            row = db.execute('SELECT principal, request_id, task_id, status, document FROM tasks '
                             'WHERE principal=? AND request_id=?', (principal, request_id)).fetchone()
            return _decode(row) if row else None

    def get(self, task_id: str) -> Task | None:
        """Query RAM allocated terminal tasks with actual task_id."""
        with self._connect() as db:
            row = db.execute('SELECT principal, request_id, task_id, status, document FROM tasks '
                             'WHERE task_id=?', (task_id,)).fetchone()
            return _decode(row) if row else None

    def save(self, task: Task) -> None:
        """Atomic save single task state while preserving identities; commit error goes up."""
        with self._connect() as db:
            db.execute('INSERT INTO tasks VALUES (?, ?, ?, ?, ?) ON CONFLICT(task_id) '
                       'DO UPDATE SET status=excluded.status, document=excluded.document',
                       (task.request.principal, task.request.request_id, task.task_id,
                        task.status.value, _encode(task)))

    def close(self) -> None:
        """Release the lock after the worker actually stops; deleting files."""
        self._owner.__exit__(None, None, None)
