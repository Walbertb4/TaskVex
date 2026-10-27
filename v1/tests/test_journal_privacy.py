"""Private receipt storage/migration checks with synthetic content and profiles."""

from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from app.core.contracts import Task, TaskStatus, ToolError, ToolResult
from app.session.model_tools import ModelTools
from app.storage import task_journal
from app.storage.task_journal import JournalError, TaskJournal
from test_task_journal import assert_history, manager
from test_task_manager import request, done


SECRET = 'PRIVATE_JOURNAL_CONTENT_45fdbe83'


def legacy(home, tasks, acknowledged=()):
    """Create the exact old schema with raw content; do not call the new writer."""
    path = home / 'tasks.sqlite3'
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('CREATE TABLE tasks (principal TEXT NOT NULL, request_id TEXT NOT NULL, '
                   'task_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, document TEXT NOT NULL, '
                   'PRIMARY KEY (principal,request_id))')
        db.execute('CREATE TABLE task_acknowledgements (task_id TEXT PRIMARY KEY, acknowledged_at TEXT NOT NULL)')
        for task in tasks:
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?)', (task.request.principal,
                task.request.request_id, task.task_id, task.status.value,
                json.dumps(task.to_dict(), sort_keys=True, ensure_ascii=True, allow_nan=False)))
        for task_id in acknowledged:
            db.execute('INSERT INTO task_acknowledgements VALUES (?,?)', (task_id, 'synthetic-review'))
        db.execute('PRAGMA user_version=1')
    return path


def old_task(task_id='old', status=TaskStatus.SUCCEEDED):
    return Task(task_id=task_id, request=request(task_id, value=SECRET), status=status,
        result=ToolResult(task_id=task_id, status=status, verified=status == TaskStatus.SUCCEEDED,
            data={'message': SECRET}, evidence={'screenshot': SECRET},
            error=None if status == TaskStatus.SUCCEEDED else ToolError(
                code=SECRET, message=SECRET, details={'body': SECRET})))


def assert_no_private_bytes(home):
    """Check the database and any SQLite sidecars, not only SELECT-visible values."""
    for path in home.glob('tasks.sqlite3*'):
        assert SECRET.encode() not in path.read_bytes(), path.name


def test_current_results_stay_in_ram_but_disk_and_eviction_are_private(tmp_path):
    calls = []
    with manager(tmp_path, lambda a, c: (calls.append(c.task_id), done(c, {'body': SECRET}))[1], capacity=1) as core:
        original = core.wait(core.submit(request(value=SECRET)).task_id, 5)
        assert original.result is not None
        assert original.result.data == {'body': SECRET}
        assert core.submit(request(value=SECRET)) == original
        assert_no_private_bytes(tmp_path)
        core.wait(core.submit(request('evict')).task_id, 5)
        assert_history(core.submit(request(value=SECRET)), original)
    with manager(tmp_path, lambda a, c: pytest.fail('historical request executed')) as core:
        assert_history(core.submit(request(value=SECRET)), original)
    assert len(calls) == 2
    assert_no_private_bytes(tmp_path)


def test_legacy_migration_preserves_replay_review_and_removes_raw_content(tmp_path):
    tasks = [old_task(), old_task('unknown', TaskStatus.UNKNOWN)]
    path = legacy(tmp_path, tasks, acknowledged=['unknown'])
    assert SECRET.encode() in path.read_bytes()
    with manager(tmp_path, lambda a, c: pytest.fail('migration executed a handler')) as core:
        assert not core.uncertain
        for task in tasks:
            assert_history(core.submit(task.request), task)
        with closing(sqlite3.connect(path)) as db:
            assert db.execute('PRAGMA user_version').fetchone()[0] == 2
            assert db.execute('SELECT needs_vacuum FROM privacy_state').fetchone()[0] == 0
            assert db.execute('SELECT task_id FROM task_acknowledgements').fetchall() == [('unknown',)]
    assert_no_private_bytes(tmp_path)
    assert not list(tmp_path.glob('*.bak'))


def test_migration_failure_rolls_back_all_receipts_and_releases_lock(tmp_path, monkeypatch):
    tasks = [old_task(), old_task('other')]
    path = legacy(tmp_path, tasks)
    original = task_journal._encode
    count = 0

    def fail_second(task):
        nonlocal count
        count += 1
        if count == 2:
            raise ValueError('synthetic migration failure')
        return original(task)

    with monkeypatch.context() as patch:
        patch.setattr(task_journal, '_encode', fail_second)
        with pytest.raises(JournalError):
            TaskJournal(tmp_path)
    with closing(sqlite3.connect(path)) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 1
        assert db.execute('SELECT count(*) FROM tasks').fetchone()[0] == 2
        assert SECRET in db.execute('SELECT document FROM tasks LIMIT 1').fetchone()[0]
    with closing(TaskJournal(tmp_path)):
        pass
    assert_no_private_bytes(tmp_path)


def test_cleanup_failure_is_pending_and_retried_before_execution(tmp_path, monkeypatch):
    path = legacy(tmp_path, [old_task()])
    connect = sqlite3.connect

    class FailVacuum(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            if sql == 'VACUUM':
                raise sqlite3.OperationalError('synthetic cleanup failure')
            return super().execute(sql, parameters)

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, 'connect', lambda *a, **kw: connect(*a, **kw, factory=FailVacuum))
        with pytest.raises(JournalError):
            manager(tmp_path, lambda a, c: pytest.fail('cleanup failure dispatched a tool'))
    with closing(connect(path)) as db:
        assert db.execute('SELECT needs_vacuum FROM privacy_state').fetchone()[0] == 1
    with manager(tmp_path) as core:
        assert core.submit(request('old', value=SECRET)).task_id == 'old'
    assert_no_private_bytes(tmp_path)


def test_process_exit_during_migration_preserves_all_replay_records(tmp_path):
    legacy(tmp_path, [old_task(), old_task('other')])
    code = '''
import os, sys
from pathlib import Path
from app.storage import task_journal as j
original = j._encode
count = 0
def crash(task):
    global count
    count += 1
    if count == 2:
        os._exit(17)
    return original(task)
j._encode = crash
j.TaskJournal(Path(sys.argv[1]))
'''
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    result = subprocess.run([sys.executable, '-c', code, str(tmp_path)], env=env,
                            capture_output=True, timeout=20)
    assert result.returncode == 17
    with manager(tmp_path, lambda a, c: pytest.fail('crash recovery replayed an effect')) as core:
        assert core.submit(request('old', value=SECRET)).task_id == 'old'
        assert core.submit(request('other', value=SECRET)).task_id == 'other'
    assert_no_private_bytes(tmp_path)


def test_historical_model_read_never_grants_fresh_targets(tmp_path, monkeypatch):
    from app.bootstrap import create_core
    monkeypatch.setenv('TASKVEX_HOME', str(tmp_path))
    # Use the same logical session/call IDs across cores, without a provider.
    with create_core() as core:
        tools = ModelTools(core, principal='local-user', session_id='synthetic', allowed_tools=('memory.read',))
        task = tools.submit({'id': 'read', 'name': 'memory.read', 'arguments': {}})
        core.wait(task.task_id, 5)
    with create_core() as core:
        tools = ModelTools(core, principal='local-user', session_id='synthetic', allowed_tools=('memory.read',))
        task = tools.submit({'id': 'read', 'name': 'memory.read', 'arguments': {}})
        result = tools.result(task.task_id)
        assert result['result']['evidence']['content_available'] is False
        assert tools._memory_snapshot is None and tools._memory_decision_id is None
