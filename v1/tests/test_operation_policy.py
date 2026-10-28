"""Explicit operation budgets and one safe read retry; fake clock, no provider."""

from dataclasses import replace
from threading import Event

import pytest

from app.core.contracts import ContractError, Task, TaskStatus, ToolError, ToolResult, ToolSpec
from app.session.tool_registry import ToolRegistry
from app.tasks.manager import TaskManager
from test_task_manager import allow, done, request
from test_workflows import finish, step


READ = {'read_only': True, 'timeout_seconds': 5, 'transient_errors': ('transient',)}


def registry(handler, **policy):
    result = ToolRegistry()
    result.register(ToolSpec(name='test.run', description='Synthetic operation',
                             input_schema={'type': 'object'}, handler=handler, **policy))
    return result


def failure(context, *, code='transient', status=TaskStatus.FAILED):
    return ToolResult(task_id=context.task_id, status=status,
                      error=ToolError(code=code, message='Synthetic failure'))


def outcome(task: Task) -> ToolResult:
    assert task.result is not None
    return task.result


def error_code(task: Task) -> str:
    error = outcome(task).error
    assert error is not None
    return error.code


@pytest.fixture
def clock(monkeypatch):
    now = [100.0]
    monkeypatch.setattr('app.tasks.manager.monotonic', lambda: now[0])
    return now


def test_read_retry_shares_request_deadline_and_rechecks_policy_once(clock, tmp_path):
    contexts, checks = [], []
    def handler(arguments, context):
        contexts.append(context)
        return failure(context) if len(contexts) == 1 else done(context)
    with TaskManager(registry(handler, **READ), authorize=lambda r, s: (checks.append(r), True)[1],
                     journal_home=tmp_path) as core:
        submitted = core.submit(request())
        result = core.wait(submitted.task_id, 5)
        assert result.status == TaskStatus.SUCCEEDED
        assert len(contexts) == len(checks) == 2
        assert contexts[0].task_id == contexts[1].task_id == submitted.task_id
        assert contexts[0].request == contexts[1].request
        assert contexts[0].deadline == contexts[1].deadline == 105
        assert contexts[0].cancel_event is contexts[1].cancel_event
        assert outcome(result).evidence['operation_policy']['attempts'] == 2
        assert core.submit(request()).task_id == submitted.task_id
    with TaskManager(registry(handler, **READ), authorize=allow, journal_home=tmp_path) as core:
        assert core.submit(request()).task_id == submitted.task_id
        assert core.operation_progress(submitted.task_id)['telemetry_available'] is False
        assert core.operation_progress(submitted.task_id)['attempts'] is None
    assert len(contexts) == 2


@pytest.mark.parametrize('policy,code,status', [
    ({'timeout_seconds': 5}, 'transient', TaskStatus.FAILED),
    (READ, 'permanent', TaskStatus.FAILED),
    (READ, 'transient', TaskStatus.UNKNOWN),
])
def test_mutation_permanent_and_unknown_never_retry(clock, policy, code, status):
    calls = []
    def handler(arguments, context):
        calls.append(context.task_id)
        return failure(context, code=code, status=status)
    with TaskManager(registry(handler, **policy), authorize=allow) as core:
        result = core.wait(core.submit(request()).task_id, 5)
        assert result.status == status and len(calls) == 1
        assert core.uncertain == (status == TaskStatus.UNKNOWN)


def test_transient_failure_retries_at_most_once(clock):
    calls = []
    def handler(arguments, context):
        calls.append(1)
        return failure(context)
    with TaskManager(registry(handler, **READ), authorize=allow) as core:
        result = core.wait(core.submit(request()).task_id, 5)
        assert result.status == TaskStatus.FAILED and calls == [1, 1]
        assert outcome(result).evidence['operation_policy']['attempts'] == 2


def test_budget_spent_by_first_read_prevents_retry_and_keeps_real_failure(clock):
    def handler(arguments, context):
        clock[0] = 106
        return failure(context)
    with TaskManager(registry(handler, **READ), authorize=allow) as core:
        result = core.wait(core.submit(request()).task_id, 5)
        assert error_code(result) == 'transient'
        assert outcome(result).evidence['operation_policy'] == {
            'attempts': 1, 'retry_blocked': 'operation_deadline', 'deadline_exceeded': True}


def test_authorization_time_consumes_budget_without_dispatch(clock):
    def authorize(r, s):
        clock[0] = 106
        return True
    with TaskManager(registry(lambda a, c: pytest.fail('Expired operation dispatched'), **READ),
                     authorize=authorize) as core:
        result = core.wait(core.submit(request()).task_id, 5)
        assert result.status == TaskStatus.FAILED and error_code(result) == 'operation_deadline'
        assert outcome(result).evidence['operation_policy']['attempts'] == 0


def test_retry_rechecks_revoked_authority_and_preserves_the_only_actual_read(clock):
    allowed, calls = [True], []
    def handler(arguments, context):
        calls.append(1)
        allowed[0] = False
        return failure(context)
    with TaskManager(registry(handler, **READ), authorize=lambda r, s: allowed[0]) as core:
        result = core.wait(core.submit(request()).task_id, 5)
        assert calls == [1] and error_code(result) == 'transient'
        assert outcome(result).evidence['operation_policy']['retry_blocked'] == 'permission_denied'


def test_preflight_denial_is_not_a_retryable_handler_failure(clock):
    checks = []
    policy = {**READ, 'transient_errors': ('permission_denied',)}
    with TaskManager(registry(lambda a, c: pytest.fail('Denied'), **policy),
                     authorize=lambda r, s: (checks.append(1), False)[1]) as core:
        result = core.wait(core.submit(request()).task_id, 5)
        assert checks == [1] and error_code(result) == 'permission_denied'
        assert outcome(result).evidence['operation_policy']['attempts'] == 0


def test_deadline_does_not_fake_completion_and_late_success_survives_stop(clock):
    entered, release = Event(), Event()
    def handler(arguments, context):
        entered.set()
        assert release.wait(5)
        return done(context)
    with TaskManager(registry(handler, timeout_seconds=5), authorize=allow) as core:
        task = core.submit(request())
        assert entered.wait(5)
        try:
            clock[0] = 106
            progress = core.operation_progress(task.task_id)
            assert progress['deadline_exceeded'] and not progress['completed']
            assert progress['status'] == 'running' and not progress['cancel_requested']
            with pytest.raises(TimeoutError):
                core.wait(task.task_id, 0)
            assert core.cancel(task.task_id).status == TaskStatus.CANCEL_REQUESTED
        finally:
            release.set()
        result = core.wait(task.task_id, 5)
        assert result.status == TaskStatus.SUCCEEDED and outcome(result).verified
        assert outcome(result).evidence['operation_policy']['deadline_exceeded']


@pytest.mark.parametrize('stop', ['cancel', 'close'])
def test_stop_and_close_during_first_read_prevent_retry(clock, stop):
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return failure(context)
    core = TaskManager(registry(handler, **READ), authorize=allow)
    try:
        task = core.submit(request())
        assert entered.wait(5)
        if stop == 'cancel':
            core.cancel(task.task_id)
        else:
            assert not core.close(timeout=0)
    finally:
        release.set()
        assert core.close(timeout=5)
    assert calls == [1] and error_code(core.get(task.task_id)) == 'transient'


def test_terminal_deadline_telemetry_is_frozen_not_recomputed_later(clock):
    with TaskManager(registry(lambda a, c: done(c), timeout_seconds=5), authorize=allow) as core:
        task = core.wait(core.submit(request()).task_id, 5)
        clock[0] = 1000
        assert core.operation_progress(task.task_id)['deadline_exceeded'] is False
        assert outcome(task).evidence['operation_policy']['deadline_exceeded'] is False


def test_legacy_defaults_preserve_evidence_and_do_not_trust_handler_retry_claims(clock):
    calls = []
    def handler(arguments, context):
        calls.append(1)
        assert context.deadline is None
        return replace(failure(context), evidence={'operation_policy': 'not host telemetry'})
    with TaskManager(registry(handler), authorize=allow) as core:
        result = core.wait(core.submit(request()).task_id, 5)
        assert calls == [1] and outcome(result).evidence == {'operation_policy': 'not host telemetry'}
        assert core.operation_progress(result.task_id)['deadline_exceeded'] is False


@pytest.mark.parametrize('policy', [
    {'read_only': 1}, {'timeout_seconds': True}, {'timeout_seconds': 0},
    {'timeout_seconds': -1}, {'timeout_seconds': float('nan')}, {'timeout_seconds': float('inf')},
    {'transient_errors': ('transient',)}, {'read_only': True, 'transient_errors': ('transient',)},
    {**READ, 'transient_errors': ['transient']}, {**READ, 'transient_errors': ('transient', 'transient')},
])
def test_invalid_or_unbounded_retry_policy_rejected_before_registration(policy):
    with pytest.raises(ContractError):
        registry(lambda a, c: done(c), **policy)


def test_transient_read_retry_uses_existing_workflow_worker_and_real_dependency_result(clock):
    counts = {}
    def handler(arguments, context):
        counts[context.request.request_id] = counts.get(context.request.request_id, 0) + 1
        return failure(context) if len(counts) == 1 and counts[context.request.request_id] == 1 else done(context)
    with TaskManager(registry(handler, **READ), authorize=allow) as core:
        core.submit_workflow('job', (step('first'), step('next', dependencies=('first',))))
        result = finish(core, 'job')
        assert result['status'] == 'succeeded' and sorted(counts.values()) == [1, 2]


def test_deadline_rechecked_after_durable_write_before_handler(clock, monkeypatch):
    with TaskManager(registry(lambda a, c: pytest.fail('Expired after journal write'), **READ), authorize=allow) as core:
        persist = core._persist
        def slow_write(task):
            persist(task)
            if task.status == TaskStatus.RUNNING:
                clock[0] = 106
        monkeypatch.setattr(core, '_persist', slow_write)
        result = core.wait(core.submit(request()).task_id, 5)
        assert error_code(result) == 'operation_deadline'
        assert outcome(result).evidence['operation_policy']['attempts'] == 0


def test_cancel_between_retry_gate_and_second_authorization_prevents_dispatch(clock):
    entered, release = Event(), Event()
    checks, calls = [], []
    def authorize(r, s):
        checks.append(1)
        if len(checks) == 2:
            entered.set()
            assert release.wait(5)
        return True
    def handler(arguments, context):
        calls.append(1)
        return failure(context)
    with TaskManager(registry(handler, **READ), authorize=authorize) as core:
        task = core.submit(request())
        assert entered.wait(5)
        try:
            core.cancel(task.task_id)
        finally:
            release.set()
        result = core.wait(task.task_id, 5)
        assert calls == [1] and error_code(result) == 'transient'
        assert outcome(result).evidence['operation_policy']['retry_blocked'] == 'cancelled'


def test_second_attempt_receives_fresh_validated_arguments_and_same_remaining_budget(clock):
    seen = []
    def handler(arguments, context):
        seen.append(dict(arguments))
        if len(seen) == 1:
            arguments['value'] = 'changed by failed handler'
            clock[0] = 104
            return failure(context)
        assert context.deadline == 105
        clock[0] = 106
        return done(context)
    with TaskManager(registry(handler, **READ), authorize=allow) as core:
        result = core.wait(core.submit(request(value='original')).task_id, 5)
        assert seen == [{'value': 'original'}, {'value': 'original'}]
        assert result.status == TaskStatus.SUCCEEDED
        assert outcome(result).evidence['operation_policy']['deadline_exceeded']
