"""Private logical restart metadata and explicit fresh replanning; synthetic tools only."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Event

import pytest

from app.storage.task_journal import JournalError, TaskJournal
from app.tasks.manager import TaskManager, TaskManagerError
from test_task_manager import allow, done, registry_with
from test_workflows import finish, step


SECRET = 'PRIVATE-RECOVERY-FIXTURE-CONTENT'


def manager(home, handler=None, **kwargs):
    return TaskManager(registry_with(handler or (lambda a, c: done(c))),
                       authorize=allow, journal_home=home, **kwargs)


def suspended(home):
    with manager(home) as core:
        core.submit_workflow('job', (step('completed', text=SECRET),), sealed=False)
        finish(core, 'job', 'planning')
        core.pause_workflow('job', expected_revision=0, reason='login')


def crash(home, mode):
    code = '''
import os, sys
from pathlib import Path
from app.core.contracts import ToolResult, TaskStatus, ToolSpec
from app.session.tool_registry import ToolRegistry
from app.tasks.manager import TaskManager
from app.tasks.workflow import WorkflowStep
registry=ToolRegistry()
mode=sys.argv[2]
def handler(arguments, context):
    if mode == 'running': os._exit(17)
    if mode == 'stop_running':
        core.cancel_workflow('job')
        os._exit(17)
    return ToolResult(task_id=context.task_id,status=TaskStatus.SUCCEEDED,verified=True)
registry.register(ToolSpec(name='test.run',description='Synthetic',input_schema={'type':'object'},handler=handler))
core=TaskManager(registry,authorize=lambda r,s: True,journal_home=Path(sys.argv[1]))
if mode == 'receipt_window':
    original=core._journal.save_workflow
    def save(record, **kwargs):
        if any(s['status']=='succeeded' for s in record['steps']): os._exit(17)
        return original(record, **kwargs)
    core._journal.save_workflow=save
core.submit_workflow('job',(WorkflowStep(step_id='old',tool='test.run',arguments={'text':'PRIVATE-RECOVERY-FIXTURE-CONTENT'}),),sealed=False)
core._worker.join(10)
os._exit(19)
'''
    result = subprocess.run([sys.executable, '-c', code, str(home), mode],
        env=dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1])),
        capture_output=True, timeout=20)
    assert result.returncode == 17, result.stderr.decode(errors='replace')


def test_normal_close_lists_metadata_without_resuming_and_continue_replans_only_remaining(tmp_path):
    suspended(tmp_path)
    calls = []
    with manager(tmp_path, lambda a, c: (calls.append(a), done(c))[1]) as core:
        record, = core.recoverable_workflows()
        assert record['workflow_id'] == 'job' and record['status'] == 'recovery_required'
        assert record['steps'][0]['status'] == 'succeeded' and record['steps'][0]['task_id']
        assert SECRET not in json.dumps(record) and 'authorization_id' not in record
        assert calls == [] and core.recoverable_workflows() == [record]
        def replan(metadata):
            assert metadata == record
            metadata['steps'].clear()  # Callback receives an isolated metadata copy.
            return (step('remaining', text='Fresh scoped work'),)
        core.recover_workflow('job', expected_revision=record['revision'], replan=replan)
        result = finish(core, 'job')
        assert result['status'] == 'succeeded'
        assert result['historical_steps'][0]['task_id'] == record['steps'][0]['task_id']
        assert calls == [{'text': 'Fresh scoped work'}]
        with pytest.raises(TaskManagerError):
            core.recover_workflow('job', expected_revision=record['revision'], replan=replan)
    assert SECRET.encode() not in (tmp_path / 'tasks.sqlite3').read_bytes()
    with manager(tmp_path) as core:
        assert core.recoverable_workflows() == []


@pytest.mark.parametrize('mode,expected', [('receipt_window', 'succeeded'), ('running', 'unknown')])
def test_crash_window_uses_real_receipt_and_never_repeats_old_effect(tmp_path, mode, expected):
    crash(tmp_path, mode)
    calls = []
    with manager(tmp_path, lambda a, c: (calls.append(1), done(c))[1]) as core:
        record, = core.recoverable_workflows()
        assert record['steps'][0]['status'] == expected
        assert calls == []
        if expected == 'unknown':
            with pytest.raises(TaskManagerError):
                core.recover_workflow('job', expected_revision=record['revision'], replan=lambda r: (step('new'),))
            unresolved, = core.unresolved_tasks()
            core.acknowledge_unknown([unresolved['task_id']])
            assert not core.uncertain
        core.recover_workflow('job', expected_revision=record['revision'], replan=lambda r: (step('new'),))
        result = finish(core, 'job')
        assert calls == [1]
        assert result['historical_steps'][0]['status'] == expected
        assert result['steps'][0]['status'] == 'succeeded'
        assert result['status'] == ('unknown' if expected == 'unknown' else 'succeeded')


def test_failed_replanning_and_old_step_ids_cannot_dispatch(tmp_path):
    suspended(tmp_path)
    with manager(tmp_path, lambda a, c: pytest.fail('Old effect replayed')) as core:
        record, = core.recoverable_workflows()
        with pytest.raises(TaskManagerError) as error:
            core.recover_workflow('job', expected_revision=record['revision'], replan=lambda r: (step('completed'),))
        assert error.value.code == 'step_locked'
        def fail(metadata):
            raise RuntimeError(SECRET)
        with pytest.raises(TaskManagerError) as error:
            core.recover_workflow('job', expected_revision=record['revision'], replan=fail)
        assert error.value.code == 'reobservation_required' and SECRET not in str(error.value)
        assert core.recoverable_workflows() == [record]


def test_stop_during_unlocked_replanning_prevents_late_continue(tmp_path):
    suspended(tmp_path)
    entered, release = Event(), Event()
    with manager(tmp_path, lambda a, c: pytest.fail('Late Continue dispatched')) as core:
        record, = core.recoverable_workflows()
        def replan(metadata):
            entered.set()
            assert release.wait(5)
            return (step('new'),)
        with ThreadPoolExecutor() as pool:
            pending = pool.submit(core.recover_workflow, 'job', expected_revision=record['revision'], replan=replan)
            assert entered.wait(5)
            try:
                core.cancel_recovery('job', expected_revision=record['revision'])
                assert core.recoverable_workflows() == []
            finally:
                release.set()
            with pytest.raises(TaskManagerError):
                pending.result(5)
    with manager(tmp_path) as core:
        assert core.recoverable_workflows() == []


def test_no_restored_scope_and_live_worker_policy_still_denies(tmp_path):
    suspended(tmp_path)
    calls = []
    with TaskManager(registry_with(lambda a, c: (calls.append(c), done(c))[1]),
                     authorize=lambda r, s: r.authorization_id == 'fresh-host-scope', journal_home=tmp_path) as core:
        record, = core.recoverable_workflows()
        core.recover_workflow('job', expected_revision=record['revision'], replan=lambda r: (step('new'),))
        result = finish(core, 'job')
        assert result['steps'][0]['error_code'] == 'permission_denied' and calls == []


def test_multiple_restarts_keep_step_identities_and_unknown_history(tmp_path):
    suspended(tmp_path)
    with manager(tmp_path) as core:
        record, = core.recoverable_workflows()
        old_id = record['steps'][0]['task_id']
        core.recover_workflow('job', expected_revision=record['revision'],
                              replan=lambda r: (step('second'),), sealed=False)
        finish(core, 'job', 'planning')
    with manager(tmp_path) as core:
        record, = core.recoverable_workflows()
        assert record['history'][0]['task_id'] == old_id
        assert record['steps'][0]['step_id'] == 'second' and record['steps'][0]['status'] == 'succeeded'
        core.recover_workflow('job', expected_revision=record['revision'], replan=lambda r: ())
        result = finish(core, 'job')
        assert len(result['historical_steps']) == 2 and result['status'] == 'succeeded'


def test_empty_metadata_tombstone_prevents_restart_or_same_process_eviction_reuse(tmp_path):
    with manager(tmp_path, capacity=1) as core:
        core.submit_workflow('empty', ())
        core.submit_workflow('evict', ())
        result = core.submit_workflow('empty', (step('never'),))
        assert result['status'] == 'review_required' and result['steps'][0]['task_id'] is None
    with manager(tmp_path) as core:
        assert core.recoverable_workflows() == []
        assert core.submit_workflow('empty', ())['status'] == 'review_required'


def test_schema2_migration_preserves_receipts_without_fabricating_old_logical_plans(tmp_path):
    from test_task_manager import request
    with manager(tmp_path) as core:
        first = core.submit(request())
        core.wait(first.task_id, 5)
    with closing(sqlite3.connect(tmp_path / 'tasks.sqlite3')) as db, db:
        db.execute('DROP TABLE workflows')
        db.execute('PRAGMA user_version=2')
    with manager(tmp_path, lambda a, c: pytest.fail('Migration executed a receipt')) as core:
        assert core.recoverable_workflows() == []
        assert core.submit(request()).task_id == first.task_id
    with closing(sqlite3.connect(tmp_path / 'tasks.sqlite3')) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 3


@pytest.mark.parametrize('damage', ['extra_content', 'wrong_identity', 'missing_receipt', 'wrong_tool', 'wrong_source'])
def test_corrupt_workflow_metadata_fails_closed_and_releases_profile_lock(tmp_path, damage):
    suspended(tmp_path)
    path = tmp_path / 'tasks.sqlite3'
    with closing(sqlite3.connect(path)) as db, db:
        original, = db.execute('SELECT document FROM workflows').fetchone()
        record = json.loads(original)
        if damage == 'extra_content':
            record['arguments'] = {'text': SECRET}
        elif damage == 'wrong_identity':
            record['workflow_id'] = 'other'
        elif damage == 'wrong_tool':
            record['steps'][0]['tool'] = 'test.other'
        elif damage == 'wrong_source':
            record['source'] = 'other'
        else:
            record['steps'][0]['task_id'] = 'missing'
            db.execute('DELETE FROM tasks')
        db.execute('UPDATE workflows SET document=?', (json.dumps(record, sort_keys=True, ensure_ascii=True),))
    with pytest.raises(JournalError):
        TaskJournal(tmp_path)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('UPDATE workflows SET document=?', (original,))
    if damage != 'missing_receipt':
        with closing(TaskJournal(tmp_path)):
            pass


def test_recovery_pages_are_principal_scoped_and_do_not_load_all_history(tmp_path):
    with manager(tmp_path, capacity=4) as core:
        for name in ('a', 'b', 'c'):
            core.submit_workflow(name, (), sealed=False)
    with manager(tmp_path) as core:
        first, = core.recoverable_workflows(limit=1)
        assert first['workflow_id'] == 'a'
        assert [r['workflow_id'] for r in core.recoverable_workflows(after='a', limit=2)] == ['b', 'c']
        assert core.recoverable_workflows(principal='other') == []
        for limit in (True, 0, 257):
            with pytest.raises(TaskManagerError):
                core.recoverable_workflows(limit=limit)
        with pytest.raises(TaskManagerError):
            core.recoverable_workflows(principal='')
        with pytest.raises(TaskManagerError):
            core.recover_workflow('a', principal='other', expected_revision=first['revision'], replan=lambda r: ())


def test_metadata_write_failure_before_dispatch_locks_new_work(tmp_path, monkeypatch):
    with manager(tmp_path, lambda a, c: pytest.fail('Unrecorded step dispatched')) as core:
        def fail(*args, **kwargs):
            raise JournalError('Synthetic storage failure')
        monkeypatch.setattr(core._journal, 'save_workflow', fail)
        with pytest.raises(TaskManagerError) as error:
            core.submit_workflow('job', (step('one'),))
        assert error.value.code == 'journal_unavailable' and core.uncertain


def test_explicit_stop_before_crash_cannot_be_resumed_and_dismissal_preserves_unknown(tmp_path):
    crash(tmp_path, 'stop_running')
    with manager(tmp_path, lambda a, c: pytest.fail('Stopped effect replayed')) as core:
        record, = core.recoverable_workflows()
        assert record['stop_requested'] and core.uncertain
        with pytest.raises(TaskManagerError):
            core.recover_workflow('job', expected_revision=record['revision'], replan=lambda r: (step('new'),))
        core.cancel_recovery('job', expected_revision=record['revision'])
        assert core.recoverable_workflows() == [] and core.uncertain
        assert len(core.unresolved_tasks()) == 1


def test_failed_metadata_checkpoint_after_real_success_keeps_worker_and_effect_result(tmp_path, monkeypatch):
    calls = []
    with manager(tmp_path, lambda a, c: (calls.append(1), done(c))[1]) as core:
        assert core._journal is not None
        original = core._journal.save_workflow
        def fail(record, **kwargs):
            if any(s['status'] == 'succeeded' for s in record['steps']):
                raise JournalError('Synthetic post-result failure')
            return original(record, **kwargs)
        monkeypatch.setattr(core._journal, 'save_workflow', fail)
        core.submit_workflow('job', (step('one'), step('two')))
        with core._condition:
            assert core._condition.wait_for(lambda: core.uncertain, timeout=5)
        result = core.get_workflow('job')
        assert result['steps'][0]['status'] == 'succeeded'
        assert core._worker.is_alive() and calls == [1]
    with manager(tmp_path, lambda a, c: pytest.fail('Post-result recovery replay')) as core:
        record, = core.recoverable_workflows()
        assert record['steps'][0]['status'] == 'succeeded'
        assert core.recoverable_workflows() == [record]


def test_schema2_migration_failure_is_atomic_and_retryable(tmp_path, monkeypatch):
    with manager(tmp_path):
        pass
    path = tmp_path / 'tasks.sqlite3'
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('DROP TABLE workflows')
        db.execute('PRAGMA user_version=2')
    connect = sqlite3.connect
    class FailIndex(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            if sql.startswith('CREATE INDEX workflows_recovery'):
                raise sqlite3.OperationalError('Synthetic migration failure')
            return super().execute(sql, parameters)
    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, 'connect', lambda *a, **kw: connect(*a, **kw, factory=FailIndex))
        with pytest.raises(JournalError):
            TaskJournal(tmp_path)
    with closing(connect(path)) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 2
        assert db.execute("SELECT name FROM sqlite_master WHERE name='workflows'").fetchone() is None
    with closing(TaskJournal(tmp_path)):
        pass
