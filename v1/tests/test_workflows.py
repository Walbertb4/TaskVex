"""Logical DAGs use the existing worker/receipts; all tools/providers are synthetic."""

from dataclasses import replace
import json
from threading import Event

import pytest

from app.core.contracts import ContractError, TaskStatus, ToolError, ToolResult
from app.session.tool_registry import RegistryError
from app.session.tool_registry import ToolRegistry
from app.policy.engine import PolicyEngine
from app.policy.task_scope import AccessRequirement, TaskScopes
from app.tasks.manager import TaskManager, TaskManagerError
from app.tasks.workflow import WorkflowStep
from test_task_manager import allow, done, registry_with
from test_policy import spec


def step(step_id, *, dependencies=(), **arguments):
    return WorkflowStep(step_id=step_id, tool='test.run', arguments=arguments, depends_on=dependencies)


def finish(core, workflow_id, status=None):
    """External test wait only; the production workflow API never waits on handlers."""
    with core._condition:
        assert core._condition.wait_for(lambda: (
            core.get_workflow(workflow_id)['status'] == status if status else
            core.get_workflow(workflow_id)['completed']), timeout=10)
    return core.get_workflow(workflow_id)


def test_failure_blocks_dependents_but_completes_independent_branches():
    calls = []
    def handler(arguments, context):
        calls.append(arguments['name'])
        if arguments.get('fail'):
            return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                              error=ToolError(code='synthetic_failure', message='Definite pre-effect failure'))
        return done(context)
    steps = (step('open', name='open', fail=True), step('play', dependencies=('open',), name='play'),
             step('independent', name='independent'), step('nested', dependencies=('play',), name='nested'))
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('job', steps)
        result = finish(core, 'job')
        assert result['status'] == 'failed' and not core.uncertain
        by_id = {s['step_id']: s for s in result['steps']}
        assert by_id['play']['status'] == by_id['nested']['status'] == 'blocked'
        assert by_id['play']['task_id'] is None and by_id['play']['blocked_by'] == ['open']
        assert by_id['independent']['status'] == 'succeeded'
    assert calls == ['open', 'independent']


def test_new_application_jobs_queue_and_old_stop_does_not_cancel_new_job():
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(arguments['name'])
        if arguments['name'] == 'first':
            entered.set()
            assert release.wait(5)
        return done(context)
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('first-job', (step('one', name='first'), step('two', name='not-run')))
        assert entered.wait(5)
        try:
            queued = core.submit_workflow('next-job', (step('one', name='next'),))
            assert queued['status'] == 'queued' and queued['steps'][0]['task_id'] is None
            stopping = core.cancel_workflow('first-job')
            assert stopping['stop_requested'] and not stopping['completed']
            assert stopping['steps'][1]['status'] == 'cancelled'
        finally:
            release.set()
        stopped = finish(core, 'first-job')
        assert stopped['status'] == 'cancelled'
        assert stopped['steps'][0]['status'] == 'succeeded'  # Late real success remains real.
        finish(core, 'next-job')
        core.cancel_workflow('first-job')
        assert core.get_workflow('next-job')['status'] == 'succeeded'
    assert calls == ['first', 'next']


def test_stop_of_last_running_step_cannot_erase_its_verified_success():
    entered, release = Event(), Event()
    def handler(arguments, context):
        entered.set()
        assert release.wait(5)
        return done(context)
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('job', (step('only'),))
        assert entered.wait(5)
        try:
            assert core.cancel_workflow('job')['status'] == 'cancel_requested'
        finally:
            release.set()
        assert finish(core, 'job')['status'] == 'succeeded'


def test_incremental_plan_correction_is_cas_and_never_rewrites_a_submitted_step():
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(arguments['value'])
        if arguments['value'] == 'first':
            entered.set()
            assert release.wait(5)
        return done(context)
    original = (step('first', value='first'), step('later', dependencies=('first',), value='old'))
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('job', original)
        assert entered.wait(5)
        try:
            with pytest.raises(TaskManagerError) as error:
                core.update_workflow('job', (step('first', value='rewritten'), original[1]), expected_revision=0)
            assert error.value.code == 'step_locked'
            changed = (original[0], step('later', dependencies=('first',), value='corrected'))
            assert core.update_workflow('job', changed, expected_revision=0)['revision'] == 1
            with pytest.raises(TaskManagerError) as error:
                core.update_workflow('job', original, expected_revision=0)
            assert error.value.code == 'workflow_changed'
            # A delayed creation replay cannot overwrite the correction.
            assert core.submit_workflow('job', original)['revision'] == 1
        finally:
            release.set()
        assert finish(core, 'job')['status'] == 'succeeded'
    assert calls == ['first', 'corrected']


def test_open_plan_waits_without_worker_busy_loop_and_accepts_actual_new_steps():
    calls = []
    with TaskManager(registry_with(lambda a, c: (calls.append(a['value']), done(c))[1]), authorize=allow) as core:
        first = step('observe', value='actual-observation')
        core.submit_workflow('job', (first,), sealed=False)
        progress = finish(core, 'job', 'planning')
        assert not progress['completed'] and not core._queue and core._worker.is_alive()
        for _ in range(20):
            core.get_workflow('job')
        assert calls == ['actual-observation']
        core.update_workflow('job', (first, step('use-result', dependencies=('observe',), value='fresh-ID')),
                             expected_revision=0, sealed=True)
        assert finish(core, 'job')['status'] == 'succeeded'
    assert calls == ['actual-observation', 'fresh-ID']


def test_sparse_patch_can_add_and_remove_unsent_steps_without_resending_completed_bodies():
    calls = []
    with TaskManager(registry_with(lambda a, c: (calls.append(a['value']), done(c))[1]), authorize=allow) as core:
        core.submit_workflow('job', (step('observed', value='PRIVATE_COMPLETED_BODY'),), sealed=False)
        finish(core, 'job', 'planning')
        core.update_workflow('job', (step('added', dependencies=('observed',), value='actual-ID'),),
                             expected_revision=0)
        finish(core, 'job', 'planning')
        # A sparse patch contains no prior private body; the owner retains its definition.
        result = core.update_workflow('job', (), expected_revision=1, sealed=True)
        assert result['status'] == 'succeeded' and 'PRIVATE_COMPLETED_BODY' not in json.dumps(result)
    assert calls == ['PRIVATE_COMPLETED_BODY', 'actual-ID']


def test_pending_removal_and_caller_mutation_do_not_rewrite_accepted_data():
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(arguments['value'])
        if arguments['value'] == 'first':
            entered.set()
            assert release.wait(5)
        return done(context)
    first, pending, removed = step('first', value='first'), step('pending', value='original'), step('removed', value='never')
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('job', (first, pending, removed))
        assert entered.wait(5)
        try:
            pending.arguments['value'] = 'caller-mutated'
            with pytest.raises(TaskManagerError):
                core.update_workflow('job', (), expected_revision=0, remove=('first',))
            updated = core.update_workflow('job', (), expected_revision=0, remove=('removed',))
            assert updated['revision'] == 1
        finally:
            release.set()
        finish(core, 'job')
    assert calls == ['first', 'original']


@pytest.mark.parametrize('steps', [
    (step('a', dependencies=('missing',)),),
    (step('a', dependencies=('b',)), step('b', dependencies=('a',))),
    (step('a'), step('a')),
])
def test_bad_graph_is_rejected_before_any_effect(steps):
    calls = []
    with TaskManager(registry_with(lambda a, c: calls.append(1)), authorize=allow) as core:
        with pytest.raises(ContractError):
            core.submit_workflow('bad', steps)
        assert not core._workflows and not calls


def test_unknown_tool_in_later_step_rejects_entire_plan_before_first_effect():
    with TaskManager(registry_with(lambda a, c: pytest.fail('invalid plan ran')), authorize=allow) as core:
        with pytest.raises(RegistryError):
            core.submit_workflow('bad', (step('good'), WorkflowStep(step_id='bad', tool='unknown.execute')))


@pytest.mark.parametrize('metadata', [{'principal': 'other-user'}, {'source': 'telegram'}])
def test_host_identity_still_passes_existing_policy_for_each_step(metadata):
    calls = []
    registry = ToolRegistry()
    registry.register(spec('system.status', ('system.read',), lambda a, c: (calls.append(1), done(c))[1]))
    policy = PolicyEngine(principal='local-user', capabilities=frozenset({'system.read'}))
    with TaskManager(registry, authorize=policy.authorize) as core:
        core.submit_workflow('denied', (WorkflowStep(step_id='read', tool='system.status'),), **metadata)
        result = finish(core, 'denied')
        assert result['status'] == 'failed' and result['steps'][0]['error_code'] == 'permission_denied'
    assert not calls


def test_scoped_permission_is_rechecked_between_workflow_steps():
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='job', principal='local-user', resources=[('window', 'chosen', 'read')])
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return done(context)
    registry = ToolRegistry()
    registry.register(spec('system.status', ('system.read',), handler))
    policy = PolicyEngine(principal='local-user', capabilities=frozenset({'system.read'}), scopes=scopes,
                         resolve_access=lambda r: AccessRequirement(resources=frozenset({('window', 'chosen', 'read')})))
    steps = (WorkflowStep(step_id='first', tool='system.status'),
             WorkflowStep(step_id='second', tool='system.status', depends_on=('first',)))
    with TaskManager(registry, authorize=policy.authorize) as core:
        core.submit_workflow('job', steps, authorization_id=scope_id)
        assert entered.wait(5)
        try:
            scopes.end(scope_id)
        finally:
            release.set()
        result = finish(core, 'job')
        assert result['steps'][0]['status'] == 'succeeded'
        assert result['steps'][1]['error_code'] == 'permission_denied'
    assert calls == [1]


def test_unknown_step_locks_other_jobs_and_never_replays_itself():
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(context.task_id)
        entered.set()
        assert release.wait(5)
        return ToolResult(task_id=context.task_id, status=TaskStatus.UNKNOWN,
                          error=ToolError(code='synthetic_unknown', message='Effect unclear'))
    with TaskManager(registry_with(handler), authorize=allow) as core:
        original = (step('unknown'), step('dependent', dependencies=('unknown',)), step('independent'))
        core.submit_workflow('job', original)
        assert entered.wait(5)
        try:
            core.submit_workflow('queued', (step('never'),))
        finally:
            release.set()
        assert finish(core, 'job')['status'] == 'unknown' and core.uncertain
        assert finish(core, 'queued')['status'] == 'cancelled'
        assert core.submit_workflow('job', original)['requires_review']
        assert len(calls) == 1
        with pytest.raises(TaskManagerError):
            core.submit_workflow('new', (step('no'),))


def test_history_prefix_gates_whole_plan_after_restart_even_if_new_step_is_first(tmp_path):
    calls = []
    def handler(arguments, context):
        calls.append(1)
        return done(context)
    with TaskManager(registry_with(handler), authorize=allow, journal_home=tmp_path) as core:
        core.submit_workflow('durable-job', (step('completed'),))
        finish(core, 'durable-job')
    with TaskManager(registry_with(handler), authorize=allow, journal_home=tmp_path) as core:
        result = core.submit_workflow('durable-job', (step('new-effect'), step('completed')))
        assert result['status'] == 'review_required' and not result['completed']
        assert all(s['task_id'] is None for s in result['steps']) and calls == [1]


def test_cancelling_empty_history_review_cannot_claim_goal_success(tmp_path):
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow, journal_home=tmp_path) as core:
        core.submit_workflow('past', (step('done'),))
        finish(core, 'past')
    with TaskManager(registry_with(lambda a, c: pytest.fail('history replay')), authorize=allow, journal_home=tmp_path) as core:
        assert core.submit_workflow('past', ())['status'] == 'review_required'
        assert core.cancel_workflow('past')['status'] == 'cancelled'


def test_history_probe_failure_blocks_admission_and_new_effects(tmp_path, monkeypatch):
    from app.storage.task_journal import JournalError
    with TaskManager(registry_with(lambda a, c: pytest.fail('unsafe dispatch')), authorize=allow, journal_home=tmp_path) as core:
        def fail(*args):
            raise JournalError('synthetic lookup failure')
        monkeypatch.setattr(core._journal, 'has_requests', fail)
        with pytest.raises(TaskManagerError) as error:
            core.submit_workflow('unsafe', (step('never'),))
        assert error.value.code == 'journal_unavailable' and core.uncertain
        assert not core._workflows and not core._queue


def test_logical_capacity_is_not_lifetime_limit_and_plan_bodies_are_not_history(tmp_path):
    calls = []
    with TaskManager(registry_with(lambda a, c: (calls.append(1), done(c))[1]), authorize=allow,
                     capacity=1, journal_home=tmp_path) as core:
        for number in range(260):
            core.submit_workflow(f'job-{number}', (step('only', value='PRIVATE_PLAN_CONTENT'),))
            progress = finish(core, f'job-{number}')
            assert 'PRIVATE_PLAN_CONTENT' not in json.dumps(progress)
            assert core._workflows[f'job-{number}'].steps[0].arguments == {}
            assert len(core._workflows) <= 1 and len(core._entries) <= 1
        assert core.submit_workflow('job-0', (step('only', value='PRIVATE_PLAN_CONTENT'),))['status'] == 'review_required'
    assert len(calls) == 260
    assert b'PRIVATE_PLAN_CONTENT' not in (tmp_path / 'tasks.sqlite3').read_bytes()


def test_close_does_not_claim_running_work_finished_and_prevents_next_step():
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return done(context)
    core = TaskManager(registry_with(handler), authorize=allow)
    try:
        core.submit_workflow('job', (step('running'), step('later')))
        assert entered.wait(5)
        assert not core.close(timeout=0)
        assert core.get_workflow('job')['status'] == 'cancel_requested'
    finally:
        release.set()
        assert core.close(timeout=5)
    result = core.get_workflow('job')
    assert result['status'] == 'cancelled' and result['steps'][0]['status'] == 'succeeded'
    assert calls == [1]


def test_workflow_does_not_hold_text_chat_lock_for_an_immediate_question(taskvex_home, monkeypatch):
    from app.bootstrap import create_core
    from app.session.gemini import DEFAULT_MODEL
    from app.session.text_chat import TextChat
    entered, release = Event(), Event()
    def handler(arguments, context, **kwargs):
        entered.set()
        assert release.wait(5)
        return done(context)
    class FakeText:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def run(self, text):
            return {'ok': True, 'text': 'Synthetic immediate answer', 'tool_results': []}
    monkeypatch.setattr('app.bootstrap.system_status', handler)
    monkeypatch.setattr('app.session.text_chat.GeminiText', FakeText)
    with create_core() as core:
        chat = TextChat(core)
        core.submit_workflow('background', (WorkflowStep(step_id='read', tool='system.status'),))
        assert entered.wait(5)
        try:
            assert not chat.busy
            reply = chat.run('A question without tools', DEFAULT_MODEL, notes_ready=False)
            assert reply['ok'] and reply['text'] == 'Synthetic immediate answer'
            assert not core.get_workflow('background')['completed']
        finally:
            release.set()
            chat.close()
        finish(core, 'background')
