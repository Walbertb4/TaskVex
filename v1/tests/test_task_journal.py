"""Tests the persistent task log with temporary profiles and real child processes.

The counter file is just a testing side effect; Note model/network/user is not used.
Crash points are selected by Event or file flag; There is no random timing.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import os
import sqlite3
import subprocess
import sys
from threading import Event

import pytest

from app.core.contracts import Task, TaskStatus, ToolError, ToolRequest
from app.storage.instance_lock import AlreadyRunningError
from app.storage.task_journal import JournalError, TaskJournal
from app.tasks.manager import TaskManager, TaskManagerError
from test_task_manager import allow, done, registry_with, request


def manager(home, handler=None, capacity=4):
    """Install administrator with real disk logger, fake handler and small RAM limit."""
    return TaskManager(registry_with(handler or (lambda a, c: done(c))),
                       authorize=allow, capacity=capacity, journal_home=home)


@pytest.mark.parametrize('capacity', [4, 256])
def test_more_than_256_jobs_replay_and_restart_keep_ids_and_bounded_ram(tmp_path, capacity):
    calls = []
    with manager(tmp_path, lambda a, c: (calls.append(c.task_id), done(c))[1], capacity=capacity) as core:
        first = core.submit(request(value=0))
        original = core.wait(first.task_id, 5)
        for number in range(1, 300):
            task = core.submit(request(f'r{number+1}', value=number))
            assert core.wait(task.task_id, 5).status == TaskStatus.SUCCEEDED
            assert len(core._entries) <= capacity and len(core._requests) <= capacity
        assert first.task_id not in core._entries
        assert core.submit(request(value=0)) == original
        assert core.get(first.task_id) == original
        assert core.wait(first.task_id, 0) == original
        assert core.cancel(first.task_id) == original
        with pytest.raises(TaskManagerError, match='different content'):
            core.submit(request(value=999))
        assert len(calls) == 300
    with manager(tmp_path, lambda a, c: pytest.fail('replayed old effect')) as core:
        assert core.submit(request(value=0)) == original
        assert core.get(first.task_id) == original
        with pytest.raises(TaskManagerError) as error:
            core.submit(request(value=1))
        assert error.value.code == 'request_conflict'
        assert not core._entries


def test_active_capacity_cancel_and_late_success(tmp_path):
    entered, release = Event(), Event()
    calls = []

    def handler(a, c):
        calls.append(c.task_id)
        entered.set()
        assert release.wait(5)
        return done(c)

    with manager(tmp_path, handler, capacity=2) as core:
        first = core.submit(request())
        assert entered.wait(5)
        second = core.submit(request('second'))
        with pytest.raises(TaskManagerError) as error:
            core.submit(request('third'))
        assert error.value.code == 'capacity_exceeded'
        assert core.submit(request()).task_id == first.task_id
        assert core.cancel(second.task_id).status == TaskStatus.CANCELLED
        third = core.submit(request('third'))
        assert core.cancel(first.task_id).status == TaskStatus.CANCEL_REQUESTED
        release.set()
        assert core.wait(first.task_id, 5).status == TaskStatus.SUCCEEDED
        assert core.wait(third.task_id, 5).status == TaskStatus.SUCCEEDED
        assert len(calls) == 2
    with manager(tmp_path) as core:
        assert core.submit(request('second')).status == TaskStatus.CANCELLED
        assert core.submit(request()).status == TaskStatus.SUCCEEDED


def test_concurrent_archived_replays_do_not_reexecute(tmp_path):
    calls = []
    with manager(tmp_path, lambda a, c: (calls.append(1), done(c))[1], capacity=1) as core:
        first = core.submit(request())
        core.wait(first.task_id, 5)
        core.wait(core.submit(request('evict')).task_id, 5)
        with ThreadPoolExecutor(max_workers=8) as pool:
            replays = list(pool.map(lambda _: core.submit(request()), range(24)))
        assert {t.task_id for t in replays} == {first.task_id}
        assert calls == [1, 1]
        assert len(core._entries) == 1


@pytest.mark.parametrize('point', ['accept', 'start', 'finish'])
def test_write_failure_never_starts_later_effects_or_erases_known_result(tmp_path, monkeypatch, point):
    calls = []
    with manager(tmp_path, lambda a, c: (calls.append(1), done(c))[1]) as core:
        journal = core._journal
        assert journal is not None
        original = journal.save

        def save(task):
            if ((point == 'accept' and task.status == TaskStatus.QUEUED)
                    or (point == 'start' and task.status == TaskStatus.RUNNING)
                    or (point == 'finish' and task.status.terminal)):
                raise JournalError('injected failure')
            original(task)

        monkeypatch.setattr(journal, 'save', save)
        if point == 'accept':
            with pytest.raises(TaskManagerError) as error:
                core.submit(request())
            assert error.value.code == 'journal_unavailable'
        else:
            outcome = core.wait(core.submit(request()).task_id, 5)
            assert outcome.status == (TaskStatus.SUCCEEDED if point == 'finish' else TaskStatus.FAILED)
        with pytest.raises(TaskManagerError):
            core.submit(request('later'))
        assert calls == ([1] if point == 'finish' else [])
    with manager(tmp_path) as core:
        if point == 'finish':
            assert core.submit(request()).status == TaskStatus.UNKNOWN
            with pytest.raises(TaskManagerError) as error:
                core.submit(request('later'))
            assert error.value.code == 'uncertain_state'


def test_unknown_remains_locked_after_restart(tmp_path):
    with manager(tmp_path, lambda a, c: None) as core:
        first = core.submit(request())
        assert core.wait(first.task_id, 5).status == TaskStatus.UNKNOWN
    with manager(tmp_path) as core:
        assert core.submit(request()).status == TaskStatus.UNKNOWN
        with pytest.raises(TaskManagerError) as error:
            core.submit(request('new'))
        assert error.value.code == 'uncertain_state'


def test_queued_recovery_cancelled_and_started_unknown_without_execution(tmp_path):
    journal = TaskJournal(tmp_path)
    journal.save(Task(task_id='queued', request=request()))
    journal.save(Task(task_id='started', request=request('running'), status=TaskStatus.RUNNING))
    journal.close()
    with manager(tmp_path, lambda a, c: pytest.fail('recovered task executed')) as core:
        assert core.submit(request()).status == TaskStatus.CANCELLED
        assert core.submit(request('running')).status == TaskStatus.UNKNOWN


@pytest.mark.parametrize('damage', ['bytes', 'version', 'record'])
def test_corrupt_history_fails_closed_and_is_preserved(tmp_path, damage):
    with manager(tmp_path) as core:
        core.wait(core.submit(request()).task_id, 5)
    path = tmp_path / 'tasks.sqlite3'
    if damage == 'bytes':
        path.write_bytes(b'broken database')
    else:
        with closing(sqlite3.connect(path)) as db, db:
            db.execute('PRAGMA user_version=2' if damage == 'version'
                       else "UPDATE tasks SET document='{}'")
    before = path.read_bytes()
    with pytest.raises(JournalError):
        manager(tmp_path)
    assert path.read_bytes() == before


def test_second_journal_owner_rejected_and_normal_close_releases(tmp_path):
    with manager(tmp_path):
        with pytest.raises(AlreadyRunningError):
            manager(tmp_path)
    with manager(tmp_path):
        pass


def test_missing_journal_during_session_is_not_recreated(tmp_path):
    calls = []
    with manager(tmp_path, lambda a, c: (calls.append(1), done(c))[1]) as core:
        journal = core._journal
        assert journal is not None
        journal.path.unlink()
        with pytest.raises(TaskManagerError) as error:
            core.submit(request())
        assert error.value.code == 'journal_unavailable'
        assert not journal.path.exists() and calls == []


def test_persisted_results_remain_history_not_restored_ram_resources(tmp_path, monkeypatch):
    """Real bootstrap does not call the same handler again; counter RAM is not resurrected."""
    from app.bootstrap import create_core
    monkeypatch.setenv('TASKVEX_HOME', str(tmp_path))
    req = ToolRequest(request_id='create-clock', source='desktop', principal='local-user',
                      tool='clocks.create', arguments={'kind': 'stopwatch', 'start': False})
    with create_core() as core:
        first = core.wait(core.submit(req).task_id, 5)
        assert first.status == TaskStatus.SUCCEEDED
    with create_core() as core:
        assert core.submit(req) == first
        listed = core.wait(core.submit(ToolRequest(request_id='fresh-list', source='desktop',
                              principal='local-user', tool='clocks.list')).task_id, 5)
        assert listed.result is not None
        assert listed.result.data['clocks'] == []


CHILD = '''
from pathlib import Path
import sys
from app.tasks.manager import TaskManager
from test_task_manager import registry_with, request, allow, done
home, mode = Path(sys.argv[1]), sys.argv[2]
def effect(a, c):
    with (home / 'effects').open('a') as f:
        f.write('once\\n'); f.flush()
    if mode == 'crash':
        print('started', flush=True)
        from threading import Event
        Event().wait()
    return done(c)
with TaskManager(registry_with(effect), authorize=allow, journal_home=home) as core:
    task = core.submit(request())
    print(core.wait(task.task_id, 10).status.value, flush=True)
'''


@pytest.mark.parametrize('crash', [False, True])
def test_real_process_restart_and_killed_handler_never_repeat_effect(tmp_path, crash):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(Path(__file__).resolve().parents[1]),
                                                     str(Path(__file__).resolve().parent)]))
    command = [sys.executable, '-c', CHILD, str(tmp_path)]
    if crash:
        child = subprocess.Popen(command + ['crash'], env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
        assert child.stdout is not None and child.stderr is not None
        try:
            # Instead of communicate timeout, limit stdout wait to separate future.
            with ThreadPoolExecutor(max_workers=1) as pool:
                line = pool.submit(child.stdout.readline)
                try:
                    assert line.result(timeout=15).strip() == 'started'
                finally:
                    child.kill()
                    child.wait(timeout=10)
        finally:
            child.stdout.close()
            child.stderr.close()
    else:
        first = subprocess.run(command + ['complete'], env=env, capture_output=True, text=True, timeout=20)
        assert first.returncode == 0, first.stderr
        assert first.stdout.strip() == 'succeeded'
    replay = subprocess.run(command + ['replay'], env=env, capture_output=True, text=True, timeout=20)
    assert replay.returncode == 0, replay.stderr
    assert replay.stdout.strip() == ('unknown' if crash else 'succeeded')
    assert (tmp_path / 'effects').read_text().splitlines() == ['once']
