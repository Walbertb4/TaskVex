"""Human waits and trusted progress checkpoints; no provider or real user data."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from app.core.contracts import TaskStatus, ToolError, ToolResult
from app.tasks.manager import TaskManager, TaskManagerError
from test_task_manager import allow, done, registry_with
from test_workflows import finish, step


def test_intervention_yields_after_actual_effect_and_independent_jobs_continue():
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(arguments['name'])
        if arguments['name'] == 'first':
            entered.set()
            assert release.wait(5)
        return done(context)
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('job', (step('one', name='first'), step('two', name='second')))
        assert entered.wait(5)
        try:
            core.submit_workflow('independent', (step('one', name='independent'),))
            pending = core.pause_workflow('job', expected_revision=0, reason='login')
            assert pending['status'] == 'wait_requested' and not pending['completed']
            with pytest.raises(TaskManagerError, match='Wait for the current operation'):
                core.resume_workflow('job', expected_revision=1, reobserve=lambda: True)
        finally:
            release.set()
        waiting = finish(core, 'job', 'waiting_for_user')
        finish(core, 'independent')
        assert waiting['wait_reason'] == 'login'
        assert waiting['steps'][0]['status'] == 'succeeded'
        assert waiting['steps'][1]['task_id'] is None
        for _ in range(5):
            assert core.get_workflow('job') == waiting  # No expiry or scheduling from polls.
        with pytest.raises(TaskManagerError, match='Reobserve'):
            core.update_workflow('job', (step('two', name='changed'),), expected_revision=1)
        core.resume_workflow('job', expected_revision=1, reobserve=lambda: True)
        assert finish(core, 'job')['status'] == 'succeeded'
    assert calls == ['first', 'independent', 'second']


def test_queued_intervention_waits_immediately_without_stopping_other_work():
    entered, release = Event(), Event()
    def handler(arguments, context):
        entered.set()
        assert release.wait(5)
        return done(context)
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('active', (step('one'),))
        assert entered.wait(5)
        try:
            core.submit_workflow('queued', (step('one'),))
            result = core.pause_workflow('queued', expected_revision=0, reason='captcha')
            assert result['status'] == 'waiting_for_user'
            assert result['steps'][0]['task_id'] is None
            assert core.get_workflow('active')['status'] == 'running'
            assert core.cancel_workflow('queued')['status'] == 'cancelled'
        finally:
            release.set()
        finish(core, 'active')


@pytest.mark.parametrize('observer', [lambda: False, lambda: 1, lambda: (_ for _ in ()).throw(RuntimeError('private'))])
def test_failed_reobservation_preserves_wait_and_never_dispatches(observer):
    calls = []
    with TaskManager(registry_with(lambda a, c: calls.append(a)), authorize=allow) as core:
        core.submit_workflow('job', (), sealed=False)
        core.pause_workflow('job', expected_revision=0, reason='two_factor')
        before = core.get_workflow('job')
        with pytest.raises(TaskManagerError) as error:
            core.resume_workflow('job', expected_revision=1, reobserve=observer)
        assert error.value.code == 'reobservation_required'
        assert core.get_workflow('job') == before and calls == []


def test_stop_during_reobservation_is_responsive_and_late_continue_cannot_revive_job():
    entered, release = Event(), Event()
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as core:
        core.submit_workflow('job', (), sealed=False)
        core.pause_workflow('job', expected_revision=0, reason='elevation')
        def observe():
            entered.set()
            assert release.wait(5)
            return True
        with ThreadPoolExecutor() as pool:
            pending = pool.submit(core.resume_workflow, 'job', expected_revision=1, reobserve=observe)
            assert entered.wait(5)
            try:
                assert core.cancel_workflow('job')['status'] == 'cancelled'
                core.submit_workflow('new', (step('one'),))
                assert finish(core, 'new')['status'] == 'succeeded'
            finally:
                release.set()
            with pytest.raises(TaskManagerError) as error:
                pending.result(5)
            assert error.value.code == 'workflow_closed'
        assert core.get_workflow('job')['status'] == 'cancelled'


def test_no_progress_uses_trusted_observations_not_polling_or_plan_revisions():
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as core:
        core.submit_workflow('job', (), sealed=False)
        state = {'window': 'fixture', 'generation': 1}
        def observe():
            return state
        result = core.observe_workflow('job', expected_revision=0, observe=observe)
        assert result['no_progress_count'] == 0
        result = core.observe_workflow('job', expected_revision=1, observe=observe)
        assert result['no_progress_count'] == 1
        result = core.update_workflow('job', (), expected_revision=2)
        assert result['no_progress_count'] == 1
        for _ in range(5):
            assert core.get_workflow('job') == result
        result = core.observe_workflow('job', expected_revision=3, observe=observe)
        assert result['no_progress_count'] == 2
        result = core.observe_workflow('job', expected_revision=4, observe=observe)
        assert result['status'] == 'waiting_for_user' and result['wait_reason'] == 'no_progress'
        assert result['no_progress_count'] == 3 and not result['completed']
        core.submit_workflow('other', (step('one'),))
        finish(core, 'other')
        core.resume_workflow('job', expected_revision=5, reobserve=lambda: True)
        assert core.get_workflow('job')['status'] == 'planning'
        assert core.get_workflow('job')['no_progress_count'] == 0


def test_new_evidence_and_actual_success_reset_counter_without_retaining_private_state(tmp_path):
    marker = 'PRIVATE-OBSERVATION-FIXTURE'
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow, journal_home=tmp_path) as core:
        core.submit_workflow('job', (), sealed=False)
        for revision in range(3):
            core.observe_workflow('job', expected_revision=revision, observe=lambda: {'state': marker})
        assert core.get_workflow('job')['no_progress_count'] == 2
        core.observe_workflow('job', expected_revision=3, observe=lambda: {'state': 'changed'})
        assert core.get_workflow('job')['no_progress_count'] == 0
        core.observe_workflow('job', expected_revision=4, observe=lambda: {'state': 'changed'})
        core.update_workflow('job', (step('one'),), expected_revision=5)
        finish(core, 'job', 'planning')
        assert core.get_workflow('job')['no_progress_count'] == 0
        assert core._workflows['job'].observation_key is None
        assert marker not in str(core.get_workflow('job'))
    assert marker.encode() not in (tmp_path / 'tasks.sqlite3').read_bytes()


@pytest.mark.parametrize('observer', [lambda: {}, lambda: [], lambda: {'v': float('nan')}, lambda: (_ for _ in ()).throw(RuntimeError('private'))])
def test_invalid_observation_fails_closed_without_advancing_revision(observer):
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as core:
        core.submit_workflow('job', (), sealed=False)
        before = core.get_workflow('job')
        with pytest.raises(TaskManagerError) as error:
            core.observe_workflow('job', expected_revision=0, observe=observer)
        assert error.value.code == 'observation_unavailable'
        assert core.get_workflow('job') == before


def test_concurrent_observations_use_revision_cas_and_callback_holds_no_lock():
    entered, release = Event(), Event()
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as core:
        core.submit_workflow('job', (), sealed=False)
        def observe():
            entered.set()
            assert release.wait(5)
            return {'state': 'old'}
        with ThreadPoolExecutor() as pool:
            pending = pool.submit(core.observe_workflow, 'job', expected_revision=0, observe=observe)
            assert entered.wait(5)
            try:
                core.observe_workflow('job', expected_revision=0, observe=lambda: {'state': 'current'})
            finally:
                release.set()
            with pytest.raises(TaskManagerError) as error:
                pending.result(5)
            assert error.value.code == 'workflow_changed'
        assert core.get_workflow('job')['revision'] == 1


@pytest.mark.parametrize('outcome', ['succeeded', 'unknown'])
def test_wait_cannot_hide_last_completion_or_bypass_unknown(outcome):
    entered, release = Event(), Event()
    def handler(arguments, context):
        entered.set()
        assert release.wait(5)
        return done(context) if outcome == 'succeeded' else ToolResult(
            task_id=context.task_id, status=TaskStatus.UNKNOWN,
            error=ToolError(code='unclear', message='Synthetic uncertainty'))
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('job', (step('one'),))
        assert entered.wait(5)
        try:
            core.pause_workflow('job', expected_revision=0, reason='user_action')
        finally:
            release.set()
        result = finish(core, 'job')
        assert result['status'] == outcome
        assert result['wait_reason'] is None
        with pytest.raises(TaskManagerError):
            core.resume_workflow('job', expected_revision=1, reobserve=lambda: True)


def test_close_cancels_waiting_metadata_and_observers_are_not_called_after_stop():
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as core:
        core.submit_workflow('job', (), sealed=False)
        with pytest.raises(TaskManagerError):
            core.pause_workflow('job', expected_revision=True, reason='login')
        with pytest.raises(TaskManagerError):
            core.pause_workflow('job', expected_revision=0, reason='private reason')
        core.pause_workflow('job', expected_revision=0, reason='login')
        assert core.close()
        assert core.get_workflow('job')['status'] == 'cancelled'
        def unexpected():
            pytest.fail('Observer must not run for a stopped task')
        with pytest.raises(TaskManagerError):
            core.resume_workflow('job', expected_revision=1, reobserve=unexpected)


@pytest.mark.parametrize('operation', ['resume', 'observe'])
def test_callback_cannot_apply_to_recreated_same_id_after_cache_eviction(operation):
    entered, release = Event(), Event()
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow, capacity=1) as core:
        def prepare():
            core.submit_workflow('job', (), sealed=False)
            if operation == 'resume':
                core.pause_workflow('job', expected_revision=0, reason='login')
        prepare()
        def callback():
            entered.set()
            assert release.wait(5)
            return {'state': 'stale'}
        with ThreadPoolExecutor() as pool:
            if operation == 'resume':
                pending = pool.submit(core.resume_workflow, 'job', expected_revision=1,
                                      reobserve=lambda: bool(callback()))
            else:
                pending = pool.submit(core.observe_workflow, 'job', expected_revision=0, observe=callback)
            assert entered.wait(5)
            try:
                core.cancel_workflow('job')
                core.submit_workflow('evict', ())
                core.cancel_workflow('evict')
                prepare()
                before = core.get_workflow('job')
            finally:
                release.set()
            with pytest.raises(TaskManagerError) as error:
                pending.result(5)
            assert error.value.code == 'workflow_changed'
        assert core.get_workflow('job') == before


def test_continue_does_not_restore_revoked_authorization():
    entered, release = Event(), Event()
    permitted, calls = [True], []
    def handler(arguments, context):
        calls.append(context.task_id)
        entered.set()
        assert release.wait(5)
        return done(context)
    with TaskManager(registry_with(handler), authorize=lambda r, s: permitted[0]) as core:
        core.submit_workflow('job', (step('first'), step('second', dependencies=('first',))))
        assert entered.wait(5)
        try:
            core.pause_workflow('job', expected_revision=0, reason='login')
        finally:
            release.set()
        finish(core, 'job', 'waiting_for_user')
        permitted[0] = False
        core.resume_workflow('job', expected_revision=1, reobserve=lambda: True)
        result = finish(core, 'job')
        assert result['steps'][0]['status'] == 'succeeded'
        assert result['steps'][1]['error_code'] == 'permission_denied'
        assert len(calls) == 1


def test_unknown_from_independent_work_cancels_wait_and_blocks_continue():
    with TaskManager(registry_with(lambda a, c: ToolResult(
            task_id=c.task_id, status=TaskStatus.UNKNOWN,
            error=ToolError(code='unclear', message='Synthetic uncertainty'))), authorize=allow) as core:
        core.submit_workflow('waiting', (), sealed=False)
        core.pause_workflow('waiting', expected_revision=0, reason='login')
        core.submit_workflow('other', (step('one'),))
        finish(core, 'other')
        assert finish(core, 'waiting')['status'] == 'cancelled'
        assert core.get_workflow('waiting')['requires_review']
        with pytest.raises(TaskManagerError):
            core.resume_workflow('waiting', expected_revision=1, reobserve=lambda: True)
