"""Task-bound permission/target cleanup under the existing worker; synthetic adapters."""

from threading import Event

import pytest

from app.automation.targets import TargetError, TargetReferences
from app.core.contracts import TaskStatus, ToolError, ToolRequest, ToolResult
from app.policy.engine import PolicyEngine
from app.policy.task_scope import AccessRequirement, TaskScopes
from app.session.tool_registry import ToolRegistry
from app.tasks.manager import TaskManager, TaskManagerError
from app.tasks.workflow import WorkflowStep
from test_policy import spec
from test_targets import snapshot
from test_task_manager import done
from test_workflows import finish


VALUE = snapshot()
RESOURCE = ('window', VALUE.resource_id, 'read')


def build(handler=None, *, home=None):
    scopes = TaskScopes()
    targets = TargetReferences(scopes)
    registry = ToolRegistry()
    registry.register(spec('system.status', ('system.read',), handler or (lambda a, c: done(c))))
    policy = PolicyEngine(principal='local-user', capabilities=frozenset({'system.read'}),
        scopes=scopes, resolve_access=lambda r: AccessRequirement(resources=frozenset({RESOURCE})))
    core = TaskManager(registry, authorize=policy.authorize, journal_home=home,
                       task_scopes=scopes, target_references=targets)
    return core, scopes, targets


def grant(scopes, targets, task_id='job'):
    scope_id = scopes.begin(task_id=task_id, principal='local-user', resources=[RESOURCE])
    ref = targets.issue(scope_id, 'local-user', VALUE, lambda cancel: VALUE)
    scopes.grant_input(scope_id)
    return scope_id, ref


def operation(step_id='one'):
    return WorkflowStep(step_id=step_id, tool='system.status')


def request(scope_id):
    return ToolRequest(request_id='approval', tool='system.status', source='desktop',
                       principal='local-user', authorization_id=scope_id)


@pytest.mark.parametrize('status', [TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.UNKNOWN])
def test_completion_releases_grants_input_approvals_and_cached_targets(status):
    def handler(arguments, context):
        return done(context) if status == TaskStatus.SUCCEEDED else ToolResult(
            task_id=context.task_id, status=status, error=ToolError(code='synthetic', message='Fixture'))
    core, scopes, targets = build(handler)
    with core:
        scope_id, ref = grant(scopes, targets)
        scopes.approve(request(scope_id))
        core.submit_workflow('job', (operation(),), authorization_id=scope_id)
        result = finish(core, 'job')
        assert result['status'] == status.value
        assert not scopes.active(scope_id, 'local-user') and ref not in targets._references
        assert not scopes.allows(request(scope_id), AccessRequirement(high_impact=True), ask_before_input=True)
        with pytest.raises(ValueError):
            scopes.grant_input(scope_id)
        with pytest.raises(TargetError):
            targets.resolve(ref, request(scope_id), Event())


def test_scope_spans_planning_turns_and_ends_only_when_whole_task_is_sealed():
    core, scopes, targets = build()
    with core:
        scope_id, ref = grant(scopes, targets)
        core.submit_workflow('job', (operation(),), authorization_id=scope_id, sealed=False)
        finish(core, 'job', 'planning')
        assert scopes.active(scope_id, 'local-user', task_id='job')
        core.update_workflow('job', (operation('next'),), expected_revision=0)
        finish(core, 'job', 'planning')
        assert scopes.allows(request(scope_id), AccessRequirement(physical_input=True), ask_before_input=True)
        assert targets.resolve(ref, request(scope_id), Event()) == VALUE
        core.update_workflow('job', (), expected_revision=1, sealed=True)
        finish(core, 'job')
        assert not scopes.active(scope_id, 'local-user') and ref not in targets._references


@pytest.mark.parametrize('stop', ['cancel', 'close'])
def test_stop_revokes_immediately_but_real_late_success_is_preserved(stop):
    entered, release = Event(), Event()
    def handler(arguments, context):
        entered.set()
        assert release.wait(5)
        return done(context)
    core, scopes, targets = build(handler)
    with core:
        scope_id, ref = grant(scopes, targets)
        core.submit_workflow('job', (operation(),), authorization_id=scope_id)
        assert entered.wait(5)
        try:
            if stop == 'cancel':
                result = core.cancel_workflow('job')
                assert not result['completed'] and result['stop_requested']
            else:
                assert not core.close(timeout=0)
            assert not scopes.active(scope_id, 'local-user') and ref not in targets._references
        finally:
            release.set()
        result = finish(core, 'job')
        assert result['steps'][0]['status'] == 'succeeded'


def test_wait_and_independent_job_completion_do_not_revoke_another_task():
    core, scopes, targets = build()
    with core:
        waiting, ref = grant(scopes, targets, 'waiting')
        core.submit_workflow('waiting', (), authorization_id=waiting, sealed=False)
        core.pause_workflow('waiting', expected_revision=0, reason='login')
        other, other_ref = grant(scopes, targets, 'other')
        core.submit_workflow('other', (operation(),), authorization_id=other)
        finish(core, 'other')
        assert scopes.active(waiting, 'local-user') and ref in targets._references
        assert not scopes.active(other, 'local-user') and other_ref not in targets._references
        core.cancel_workflow('other')  # Old Stop cannot affect the waiting task's authority.
        assert scopes.active(waiting, 'local-user')
        core.cancel_workflow('waiting')
        assert not scopes.active(waiting, 'local-user')


def test_scope_replacement_at_checkpoint_invalidates_old_targets_and_approvals():
    core, scopes, targets = build()
    with core:
        old, ref = grant(scopes, targets)
        scopes.approve(request(old))
        core.submit_workflow('job', (), authorization_id=old, sealed=False)
        core.pause_workflow('job', expected_revision=0, reason='user_action')
        scopes.end(old)
        new = scopes.begin(task_id='job', principal='local-user', resources=[RESOURCE])
        result = core.replace_workflow_scope('job', expected_revision=1, authorization_id=new)
        assert result['revision'] == 2 and result['status'] == 'waiting_for_user'
        assert ref not in targets._references
        assert not scopes.allows(request(new), AccessRequirement(physical_input=True), ask_before_input=True)
        assert not scopes.allows(request(new), AccessRequirement(high_impact=True), ask_before_input=True)
        with pytest.raises(TaskManagerError):
            core.resume_workflow('job', expected_revision=1, reobserve=lambda: True)
        core.resume_workflow('job', expected_revision=2, reobserve=lambda: True)
        core.update_workflow('job', (operation(),), expected_revision=3, sealed=True)
        assert finish(core, 'job')['status'] == 'succeeded'
        assert not scopes.active(new, 'local-user')


def test_scope_replacement_rejects_active_child_and_foreign_task():
    entered, release = Event(), Event()
    def handler(arguments, context):
        entered.set()
        assert release.wait(5)
        return done(context)
    core, scopes, targets = build(handler)
    with core:
        own, _ = grant(scopes, targets)
        foreign, _ = grant(scopes, targets, 'foreign')
        core.submit_workflow('job', (operation(),), authorization_id=own, sealed=False)
        assert entered.wait(5)
        try:
            with pytest.raises(TaskManagerError) as error:
                core.replace_workflow_scope('job', expected_revision=0, authorization_id=foreign)
            assert error.value.code == 'task_active'
        finally:
            release.set()
        finish(core, 'job', 'planning')
        with pytest.raises(TaskManagerError) as error:
            core.replace_workflow_scope('job', expected_revision=0, authorization_id=foreign)
        assert error.value.code == 'invalid_scope'
        assert scopes.active(foreign, 'local-user')
        scopes.end(foreign)


@pytest.mark.parametrize('owner,principal', [('other-task', 'local-user'), ('job', 'foreign-user')])
def test_admission_rejects_wrong_task_or_principal_without_revoking_foreign_grant(owner, principal):
    core, scopes, targets = build(lambda a, c: pytest.fail('Wrong scope dispatched'))
    with core:
        scope_id = scopes.begin(task_id=owner, principal=principal, resources=[RESOURCE])
        with pytest.raises(TaskManagerError) as error:
            core.submit_workflow('job', (operation(),), authorization_id=scope_id)
        assert error.value.code == 'invalid_scope'
        assert scopes.active(scope_id, principal)
        scopes.end(scope_id)


def test_unknown_cleans_waiting_task_and_actual_unknown_task():
    core, scopes, targets = build(lambda a, c: ToolResult(task_id=c.task_id, status=TaskStatus.UNKNOWN,
        error=ToolError(code='unknown', message='Synthetic uncertainty')))
    with core:
        waiting, waiting_ref = grant(scopes, targets, 'waiting')
        core.submit_workflow('waiting', (), authorization_id=waiting, sealed=False)
        core.pause_workflow('waiting', expected_revision=0, reason='login')
        active, active_ref = grant(scopes, targets, 'active')
        core.submit_workflow('active', (operation(),), authorization_id=active)
        assert finish(core, 'active')['status'] == 'unknown'
        assert finish(core, 'waiting')['requires_review'] and core.uncertain
        assert not scopes.active(waiting, 'local-user') and not scopes.active(active, 'local-user')
        assert waiting_ref not in targets._references and active_ref not in targets._references


def test_composition_requires_same_scope_owner_before_worker_start():
    first, other = TaskScopes(), TaskScopes()
    targets = TargetReferences(first)
    with pytest.raises(TaskManagerError) as error:
        TaskManager(ToolRegistry(), task_scopes=other, target_references=targets)
    assert error.value.code == 'invalid_scope_owner'
    with pytest.raises(TaskManagerError):
        TaskManager(ToolRegistry(), target_references=targets)


def test_cleanup_failure_revokes_scope_and_locks_dispatch_without_rewriting_success(monkeypatch):
    core, scopes, targets = build()
    with core:
        scope_id, ref = grant(scopes, targets)
        def fail(scope):
            raise RuntimeError('Synthetic cleanup fault')
        monkeypatch.setattr(targets, 'release_scope', fail)
        core.submit_workflow('job', (operation(),), authorization_id=scope_id)
        result = finish(core, 'job')
        assert result['steps'][0]['status'] == 'succeeded' and result['requires_review']
        assert not scopes.active(scope_id, 'local-user') and core.uncertain and core.scope_cleanup_failed
        with pytest.raises(TargetError):
            targets.resolve(ref, request(scope_id), Event())
        with pytest.raises(TaskManagerError) as error:
            core.acknowledge_unknown(['not-a-reviewable-effect'])
        assert error.value.code == 'scope_cleanup_failed' and core.uncertain


def test_recovery_requires_fresh_task_scope_and_cleans_it_after_remaining_work(tmp_path):
    core, scopes, targets = build(home=tmp_path)
    with core:
        old, old_ref = grant(scopes, targets)
        core.submit_workflow('job', (operation(),), authorization_id=old, sealed=False)
        finish(core, 'job', 'planning')
    assert not scopes.active(old, 'local-user') and old_ref not in targets._references
    core, scopes, targets = build(home=tmp_path)
    with core:
        record, = core.recoverable_workflows()
        def forbidden_observation(metadata):
            pytest.fail('A stale scope must be rejected before resource observation')
        with pytest.raises(TaskManagerError) as error:
            core.recover_workflow('job', expected_revision=record['revision'], authorization_id=old,
                                  replan=forbidden_observation)
        assert error.value.code == 'invalid_scope'
        new, ref = grant(scopes, targets)
        core.recover_workflow('job', expected_revision=record['revision'], authorization_id=new,
                              replan=lambda r: (operation('remaining'),))
        assert finish(core, 'job')['status'] == 'succeeded'
        assert not scopes.active(new, 'local-user') and ref not in targets._references


def test_historical_review_stub_cannot_revoke_another_tasks_scope(tmp_path):
    core, scopes, targets = build(home=tmp_path)
    with core:
        past, _ = grant(scopes, targets, 'past')
        core.submit_workflow('past', (operation(),), authorization_id=past)
        finish(core, 'past')
    core, scopes, targets = build(home=tmp_path)
    with core:
        other, ref = grant(scopes, targets, 'other')
        result = core.submit_workflow('past', (), authorization_id=other)
        assert result['status'] == 'review_required'
        core.cancel_workflow('past')
        assert scopes.active(other, 'local-user') and ref in targets._references
        scopes.end(other)


def test_stop_invalidates_an_inflight_target_reader_without_locking_cleanup():
    entered, release = Event(), Event()
    ref = ''
    def handler(arguments, context):
        try:
            targets.resolve(ref, context.request, context.cancel_event)
            pytest.fail('Stopped target reader completed as valid')
        except TargetError as error:
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED,
                              error=ToolError(code=error.code, message='Synthetic cancelled observation'))
    def reader(cancel):
        entered.set()
        assert release.wait(5)
        return VALUE
    core, scopes, targets = build(handler)
    with core:
        scope_id, _ = grant(scopes, targets)
        ref = targets.issue(scope_id, 'local-user', VALUE, reader)
        core.submit_workflow('job', (operation(),), authorization_id=scope_id)
        assert entered.wait(5)
        try:
            core.cancel_workflow('job')
            assert ref not in targets._references and not scopes.active(scope_id, 'local-user')
        finally:
            release.set()
        assert finish(core, 'job')['status'] == 'cancelled'


def test_scope_only_composition_can_end_a_local_task_without_target_store():
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='local', principal='local-user')
    with TaskManager(ToolRegistry(), task_scopes=scopes) as core:
        core.submit_workflow('local', (), authorization_id=scope_id, sealed=False)
        assert scopes.active(scope_id, 'local-user')
        core.cancel_workflow('local')
        assert not scopes.active(scope_id, 'local-user')


@pytest.mark.parametrize('operation_name', ['resume', 'observe'])
@pytest.mark.parametrize('when', ['before', 'during'])
def test_revoked_scope_blocks_observation_and_continuation_without_changing_plan(operation_name, when):
    core, scopes, targets = build()
    with core:
        scope_id, _ = grant(scopes, targets)
        core.submit_workflow('job', (), authorization_id=scope_id, sealed=False)
        if operation_name == 'resume':
            core.pause_workflow('job', expected_revision=0, reason='login')
        before = core.get_workflow('job')
        observed = []
        def callback():
            observed.append(1)
            scopes.end(scope_id)
            return {'fresh': 'fixture'}
        if when == 'before':
            scopes.end(scope_id)
        with pytest.raises(TaskManagerError) as error:
            if operation_name == 'resume':
                core.resume_workflow('job', expected_revision=before['revision'], reobserve=lambda: bool(callback()))
            else:
                core.observe_workflow('job', expected_revision=before['revision'], observe=callback)
        assert error.value.code == 'invalid_scope'
        assert observed == ([] if when == 'before' else [1])
        assert core.get_workflow('job') == before
