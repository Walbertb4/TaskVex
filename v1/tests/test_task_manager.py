"""Verifies queue/cancellation races with real threads, without external side effects.

Event doors keep handlers waiting at certain points. So sleep randomly
Instead of using test, it knows whether the job has actually started or not.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from app.core.contracts import TaskStatus, ToolError, ToolRequest, ToolResult, ToolSpec
from app.session.tool_registry import RegistryError, ToolRegistry
from app.tasks.manager import TaskManager, TaskManagerError


def registry_with(handler):
    """Save test function only; no real application or file tool."""
    registry = ToolRegistry()
    registry.register(ToolSpec(name="test.run", description='trial tool',
                               input_schema={"type": "object"}, handler=handler))
    return registry


def request(request_id="r1", *, principal="test-user", source="test", **arguments):
    """Make it easy to test coverage of the same ID."""
    return ToolRequest(request_id=request_id, source=source, principal=principal,
                       tool="test.run", arguments=arguments)


def done(context, data=None):
    """Convert the handler ending observed by the test into a successful ToolResult."""
    return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED,
                      verified=True, data=data, evidence={"handler_finished": True})


def allow(request, tool):
    """Explicit permission for testing alone; It is not a production policy application."""
    return True


def test_default_denies_execution():
    calls = []
    with TaskManager(registry_with(lambda a, c: calls.append(a))) as manager:
        task = manager.submit(request())
        result = manager.wait(task.task_id, 2)
        assert result.status == TaskStatus.FAILED
        assert result.result.error.code == "permission_denied"
    assert calls == []


def test_success_and_completed_replay_only_execute_once():
    calls = []

    def handler(arguments, context):
        calls.append(arguments)
        return done(context, {"count": 0})

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        queued = manager.submit(request(value=0))
        assert queued.status == TaskStatus.QUEUED
        finished = manager.wait(queued.task_id, 2)
        replay = manager.submit(request(value=0))
        assert finished.status == replay.status == TaskStatus.SUCCEEDED
        assert finished.task_id == replay.task_id
        assert finished.result.data == {"count": 0}
        assert calls == [{"value": 0}]


def test_concurrent_replays_admit_one_task():
    """The control-et/add race of simultaneous submissions should not result in a double-hander."""
    calls = []
    entered, release = Event(), Event()

    def handler(arguments, context):
        calls.append(arguments)
        entered.set()
        assert release.wait(2)
        return done(context)

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        with ThreadPoolExecutor(max_workers=8) as pool:
            tasks = list(pool.map(lambda _: manager.submit(request(value=1)), range(16)))
        assert entered.wait(2)
        assert len({task.task_id for task in tasks}) == 1
        release.set()
        assert manager.wait(tasks[0].task_id, 2).status == TaskStatus.SUCCEEDED
        assert len(calls) == 1


@pytest.mark.parametrize("changed", [request(value=2), request(source="other", value=1)])
def test_same_request_id_with_changed_content_rejected(changed):
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as manager:
        first = manager.submit(request(value=1))
        with pytest.raises(TaskManagerError) as error:
            manager.submit(changed)
        assert error.value.code == "request_conflict"
        assert manager.wait(first.task_id, 2).status == TaskStatus.SUCCEEDED


def test_request_id_is_scoped_by_principal_and_key_order_is_irrelevant():
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as manager:
        first = manager.submit(request(a=1, b=2))
        replay = manager.submit(request(b=2, a=1))
        other = manager.submit(request(principal="another-user", a=1, b=2))
        assert first.task_id == replay.task_id != other.task_id


def test_fifo_and_queued_cancellation_never_run_cancelled_handler():
    order = []
    entered, release = Event(), Event()

    def handler(arguments, context):
        order.append(arguments["value"])
        if arguments["value"] == 1:
            entered.set()
            assert release.wait(2)
        return done(context)

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        first = manager.submit(request("r1", value=1))
        assert entered.wait(2)
        second = manager.submit(request("r2", value=2))
        third = manager.submit(request("r3", value=3))
        assert manager.cancel(second.task_id).status == TaskStatus.CANCELLED
        assert manager.submit(request("r2", value=2)).status == TaskStatus.CANCELLED
        assert order == [1]
        release.set()
        assert manager.wait(third.task_id, 2).status == TaskStatus.SUCCEEDED
        assert manager.wait(first.task_id, 2).status == TaskStatus.SUCCEEDED
        assert order == [1, 3]


def test_running_cancel_stays_requested_until_handler_really_stops():
    entered, finish = Event(), Event()

    def handler(arguments, context):
        entered.set()
        assert finish.wait(2)
        assert context.cancel_event.is_set()
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        task = manager.submit(request())
        assert entered.wait(2)
        assert manager.cancel(task.task_id).status == TaskStatus.CANCEL_REQUESTED
        with pytest.raises(TimeoutError):
            manager.wait(task.task_id, 0)
        assert manager.get(task.task_id).result is None
        finish.set()
        assert manager.wait(task.task_id, 2).status == TaskStatus.CANCELLED


def test_cancel_during_preflight_prevents_handler_call():
    entered, release = Event(), Event()
    calls = []

    def authorize(item, spec):
        entered.set()
        assert release.wait(2)
        return True

    with TaskManager(registry_with(lambda a, c: calls.append(a)), authorize=authorize) as manager:
        task = manager.submit(request())
        assert entered.wait(2)
        manager.cancel(task.task_id)
        release.set()
        assert manager.wait(task.task_id, 2).status == TaskStatus.CANCELLED
        assert calls == []


def test_wait_timeout_does_not_cancel_or_invent_unknown_status():
    entered, release = Event(), Event()

    def handler(arguments, context):
        entered.set()
        assert release.wait(2)
        assert not context.cancel_event.is_set()
        return done(context)

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        task = manager.submit(request())
        assert entered.wait(2)
        with pytest.raises(TimeoutError):
            manager.wait(task.task_id, 0)
        assert manager.get(task.task_id).status == TaskStatus.RUNNING
        release.set()
        assert manager.wait(task.task_id, 2).status == TaskStatus.SUCCEEDED


def test_close_reports_still_running_and_late_cancel_does_not_erase_success():
    entered, release = Event(), Event()
    calls = []

    def handler(arguments, context):
        calls.append(arguments)
        entered.set()
        assert release.wait(2)
        return done(context)

    manager = TaskManager(registry_with(handler), authorize=allow)
    try:
        active = manager.submit(request())
        assert entered.wait(2)
        queued = manager.submit(request("r2"))
        assert manager.close(0) is False
        assert manager.get(active.task_id).status == TaskStatus.CANCEL_REQUESTED
        assert manager.get(queued.task_id).status == TaskStatus.CANCELLED
        with pytest.raises(TaskManagerError) as error:
            manager.submit(request("r3"))
        assert error.value.code == "closed"
        release.set()
        assert manager.close(2) is True
        assert manager.close(0) is True
        assert manager.get(active.task_id).status == TaskStatus.SUCCEEDED
        assert len(calls) == 1
    finally:
        release.set()
        manager.close(2)


@pytest.mark.parametrize("invalid", [None, "Done", {"ok": True}, "wrong-id", "bad-data"])
def test_unknown_result_stops_following_work_and_never_retries(invalid):
    entered, release = Event(), Event()
    calls = []

    def handler(arguments, context):
        calls.append(arguments)
        entered.set()
        assert release.wait(2)
        if invalid == "wrong-id":
            return ToolResult(task_id="other", status=TaskStatus.SUCCEEDED, verified=True)
        if invalid == "bad-data":
            output = done(context, {})
            output.data["bad"] = object()
            return output
        return invalid

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        first = manager.submit(request())
        assert entered.wait(2)
        second = manager.submit(request("r2"))
        release.set()
        outcome = manager.wait(first.task_id, 2)
        assert outcome.status == TaskStatus.UNKNOWN
        assert manager.wait(second.task_id, 2).status == TaskStatus.CANCELLED
        assert manager.submit(request()).task_id == first.task_id
        with pytest.raises(TaskManagerError) as error:
            manager.submit(request("r3"))
        assert error.value.code == "uncertain_state"
        assert len(calls) == 1


@pytest.mark.parametrize("exception", [RuntimeError, SystemExit])
def test_handler_exception_is_unknown_and_does_not_leak_exception_text(exception):
    def handler(arguments, context):
        raise exception("private-token-value")

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        task = manager.submit(request())
        outcome = manager.wait(task.task_id, 2)
        assert outcome.status == TaskStatus.UNKNOWN
        assert "private-token-value" not in str(outcome.to_dict())


def test_confirmed_failure_can_be_followed_by_another_task():
    def handler(arguments, context):
        if arguments.get("fail"):
            return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                              error=ToolError(code="not_applied", message="No effect was applied"))
        return done(context)

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        bad = manager.submit(request(fail=True))
        good = manager.submit(request("r2"))
        assert manager.wait(bad.task_id, 2).status == TaskStatus.FAILED
        assert manager.wait(good.task_id, 2).status == TaskStatus.SUCCEEDED


def test_authorization_error_is_failed_without_handler_and_does_not_stop_queue():
    calls = []

    def authorize(item, spec):
        if item.request_id == "r1":
            raise RuntimeError("secret")
        return True

    def handler(arguments, context):
        calls.append(arguments)
        return done(context)

    with TaskManager(registry_with(handler), authorize=authorize) as manager:
        first = manager.submit(request())
        second = manager.submit(request("r2"))
        outcome = manager.wait(first.task_id, 2)
        assert outcome.status == TaskStatus.FAILED
        assert "secret" not in str(outcome.to_dict())
        assert manager.wait(second.task_id, 2).status == TaskStatus.SUCCEEDED
        assert calls == [{}]


def test_manager_owns_request_and_result_copies_even_with_mutating_callback():
    originals = []

    def authorize(item, spec):
        item.arguments["items"].clear()
        spec.input_schema.clear()
        return True

    def handler(arguments, context):
        assert arguments == {"items": [1]}
        context.request.arguments.clear()
        output = done(context, {"items": [1]})
        originals.append(output)
        return output

    with TaskManager(registry_with(handler), authorize=authorize) as manager:
        initial = request(items=[1])
        task = manager.submit(initial)
        initial.arguments.clear()
        task.request.arguments.clear()
        outcome = manager.wait(task.task_id, 2)
        originals[0].data["items"].clear()
        outcome.result.data.clear()
        current = manager.get(task.task_id)
        assert current.request.arguments == {"items": [1]}
        assert current.result.data == {"items": [1]}


def test_capacity_keeps_replay_records_and_rejects_new_work():
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow, capacity=1) as manager:
        first = manager.submit(request())
        manager.wait(first.task_id, 2)
        assert manager.submit(request()).task_id == first.task_id
        with pytest.raises(TaskManagerError) as error:
            manager.submit(request("r2"))
        assert error.value.code == "capacity_exceeded"


def test_missing_task_and_invalid_request_are_controlled_errors():
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as manager:
        for action in [manager.get, manager.cancel, manager.wait]:
            with pytest.raises(TaskManagerError) as error:
                action("missing")
            assert error.value.code == "unknown_task"
        with pytest.raises(RegistryError):
            manager.submit({})


def test_async_handler_is_not_started_by_synchronous_worker():
    calls = []

    async def handler(arguments, context):
        calls.append(arguments)

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        task = manager.submit(request())
        outcome = manager.wait(task.task_id, 2)
        assert outcome.status == TaskStatus.FAILED
        assert outcome.result.error.code == "unsupported_handler"
        assert calls == []


def test_sync_handler_returning_coroutine_is_closed_without_execution():
    """A false return does not generate an unawaited coroutine warning or hidden second execution."""
    calls = []

    async def inner():
        calls.append("executed")

    with TaskManager(registry_with(lambda a, c: inner()), authorize=allow) as manager:
        task = manager.submit(request())
        assert manager.wait(task.task_id, 2).status == TaskStatus.UNKNOWN
        assert calls == []


def test_invalid_parameters_do_not_consume_capacity_or_enter_handler():
    """Even queue/register space should not be wasted if application validation fails."""
    registry = ToolRegistry()
    registry.register(ToolSpec(name="test.run", description='Number test',
                               input_schema={"type": "object", "properties": {
                                   "value": {"type": "integer"}}, "required": ["value"]},
                               handler=lambda a, c: done(c)))
    with TaskManager(registry, authorize=allow, capacity=1) as manager:
        with pytest.raises(RegistryError):
            manager.submit(request(value=True))
        task = manager.submit(request(value=0))
        assert manager.wait(task.task_id, 2).status == TaskStatus.SUCCEEDED


@pytest.mark.parametrize("decision", [False, 1, "allow", None])
def test_authorization_requires_explicit_true(decision):
    """Truthy should not inadvertently replace a text/number consent decree."""
    calls = []
    with TaskManager(registry_with(lambda a, c: calls.append(a)),
                     authorize=lambda r, s: decision) as manager:
        task = manager.submit(request())
        assert manager.wait(task.task_id, 2).status == TaskStatus.FAILED
        assert calls == []


def test_worker_cannot_deadlock_by_waiting_for_its_own_queue():
    def handler(arguments, context):
        with pytest.raises(TaskManagerError) as error:
            manager.wait(context.task_id)
        assert error.value.code == "worker_wait"
        return done(context)

    with TaskManager(registry_with(handler), authorize=allow) as manager:
        task = manager.submit(request())
        assert manager.wait(task.task_id, 2).status == TaskStatus.SUCCEEDED


@pytest.mark.parametrize("timeout", [-1, float("nan"), float("inf"), True, "1"])
def test_invalid_wait_limits_do_not_change_manager(timeout):
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as manager:
        task = manager.submit(request())
        with pytest.raises(TaskManagerError):
            manager.wait(task.task_id, timeout)
        assert manager.wait(task.task_id, 2).status == TaskStatus.SUCCEEDED
