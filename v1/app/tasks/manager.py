"""TaskVex's single worker task and replay manager.

submit accepts the request; A single worker operates the handlers sequentially. get/wait
gives a copy of the status, cancel requests cancellation, close stops accepting new jobs.
Since there is a single worker, two handlers do not use a common resource at the same time, such as a desktop.

When a persistent profile is given, the disk log is recorded before execution. parallel
It is not a resource planner or policy engine. Execution if no authorization callback
is rejected. Thread does not force cancellation; The handler must manage its own sub-resources.
"""

from collections import deque
from dataclasses import dataclass, field, replace
from inspect import iscoroutine, iscoroutinefunction
import json
import math
from pathlib import Path
from threading import Condition, Event, Thread, current_thread
from typing import Callable, NoReturn
from uuid import uuid4

from app.core.contracts import (
    ContractError, Task, TaskStatus, ToolContext, ToolError,
    ToolRequest, ToolResult, ToolSpec,
)
from app.session.tool_registry import RegistryError, ToolRegistry
from app.storage.task_journal import JournalError, TaskJournal


class TaskManagerError(ContractError):
    """Reports an identity conflict, capacity, or lifecycle error with its code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class _Entry:
    """Task record not exported; Cancel Event is common between manager/handler."""

    task: Task
    fingerprint: str
    cancel_event: Event = field(default_factory=Event)


def _copy_request(request: ToolRequest) -> ToolRequest:
    """Copy the public contract by revalidating it without sharing the internal dictionary."""
    return ToolRequest(**request.to_dict())


def _copy_result(result: ToolResult) -> ToolResult:
    """Separate the result/data/error objects held by the handler from the manager register."""
    return replace(result, error=replace(result.error) if result.error is not None else None)


def _snapshot(task: Task) -> Task:
    """The external code cannot change the internal record by changing the state copy."""
    return replace(task, request=_copy_request(task.request),
                   result=_copy_result(task.result) if task.result is not None else None)


def _fingerprint(request: ToolRequest) -> str:
    """Request representation that detects content change, regardless of field order."""
    return json.dumps(request.to_dict(), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _timeout(value: float | None) -> None:
    """Check waiting limit; None means unlimited, zero instant control."""
    if value is not None and (
        type(value) not in (int, float) or value < 0 or not math.isfinite(value)
    ):
        raise TaskManagerError("invalid_timeout", "Timeout must be finite and non-negative")


class TaskManager:
    """It holds the tasks and replay keys for an ephemeral application session.

    If authorize(request, tool) only returns True, the handler is passed.
    Authentication login adapter, permission rules policy module
    It is the responsibility. Absence of callback rejects all executions.

    If persistent journal_home is given, capacity RAM/active is the task limit; terminal
    records are queried from disk. Legacy safe total in logless volume usage
    limit is preserved: replay information that has not been moved to disk cannot be silently deleted.
    """

    def __init__(self, registry: ToolRegistry, *,
                 authorize: Callable[[ToolRequest, ToolSpec], bool] | None = None,
                 capacity: int = 256, journal_home: Path | None = None) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TaskManagerError("invalid_registry", "Expected ToolRegistry")
        if authorize is not None and not callable(authorize):
            raise TaskManagerError("invalid_authorizer", "Expected authorization callback")
        if type(capacity) is not int or capacity < 1:
            raise TaskManagerError("invalid_capacity", "Capacity must be a positive integer")
        self._registry = registry
        self._authorize = authorize
        self._capacity = capacity
        self._entries: dict[str, _Entry] = {}
        self._requests: dict[tuple[str, str], str] = {}
        self._queue: deque[str] = deque()
        # Condition locks both records and prevents the worker from using the processor in an empty queue.
        # It allows him to sleep without getting busy. This lock is not held while the Handler is running.
        self._condition = Condition()
        self._closing = False
        self._journal = TaskJournal(journal_home) if journal_home is not None else None
        self._journal_failed = False
        self._uncertain = self._journal.uncertain if self._journal else False
        self._worker = Thread(target=self._run, name="taskvex-worker", daemon=False)
        try:
            self._worker.start()
        except BaseException:
            if self._journal is not None:
                self._journal.close()
            raise

    @property
    def uncertain(self) -> bool:
        """Expose the existing journal/worker safety latch without granting reset authority."""
        with self._condition:
            return self._uncertain

    def describe_tools(self) -> list[dict]:
        """Notify model adapter only; grant handler and authorization object.

        Schemas are independent copies of the registry. This catalog is not a permission;
        The adapter selects the visible subset, again checking the current policy on execution.
        """
        return [{"name": tool.name, "description": tool.description,
                 "parameters": tool.input_schema} for tool in self._registry.list_tools()]

    def submit(self, request: ToolRequest) -> Task:
        """Queue the current request or grant the current task for the same identity/content.

        Repeat key (principal, request_id). Fingerprint channel, tool and all
        Also includes parameters. Different users may use the same request_id;
        If the same user uses the same ID for different request, he will get an error.
        """
        owned = self._registry.validate_request(request)
        fingerprint = _fingerprint(owned)
        key = (owned.principal, owned.request_id)
        with self._condition:
            if self._closing:
                raise TaskManagerError("closed", "TaskManager is closing")
            existing_id = self._requests.get(key)
            if existing_id is not None:
                entry = self._entries[existing_id]
                if entry.fingerprint != fingerprint:
                    raise TaskManagerError("request_conflict", "Request id has different content")
                return _snapshot(entry.task)
            if self._journal is not None:
                try:
                    archived = self._journal.find(*key)
                except JournalError:
                    self._journal_error()
                if archived is not None:
                    if _fingerprint(archived.request) != fingerprint:
                        raise TaskManagerError("request_conflict", "Request id has different content")
                    return _snapshot(archived)
            if self._uncertain:
                raise TaskManagerError("uncertain_state", "An earlier operation has unknown outcome")
            # Only the terminal record with a permanent copy can be removed from RAM. disc
            # Since its history is not deleted, the old request_id still gives the same result.
            if self._journal is not None:
                for task_id, entry in list(self._entries.items()):
                    if len(self._entries) < self._capacity:
                        break
                    if entry.task.status.terminal:
                        del self._entries[task_id]
                        del self._requests[(entry.task.request.principal, entry.task.request.request_id)]
            if len(self._entries) >= self._capacity:
                raise TaskManagerError("capacity_exceeded", "Active task capacity reached")
            task = Task(task_id=uuid4().hex, request=owned)
            self._persist(task)
            self._entries[task.task_id] = _Entry(task=task, fingerprint=fingerprint)
            self._requests[key] = task.task_id
            self._queue.append(task.task_id)
            self._condition.notify_all()
            return _snapshot(task)

    def _entry(self, task_id: str) -> _Entry:
        """Internal assistant under lock and key; Make a controlled error on the task that does not exist."""
        if isinstance(task_id, str):
            if task_id in self._entries:
                return self._entries[task_id]
            if self._journal is not None:
                try:
                    archived = self._journal.get(task_id)
                except JournalError:
                    self._journal_error()
                if archived is not None and archived.status.terminal:
                    return _Entry(task=archived, fingerprint=_fingerprint(archived.request))
        raise TaskManagerError("unknown_task", "Task id is not known")

    def _journal_error(self) -> NoReturn:
        """Do not allow any new handlers after repository failure; hide content."""
        self._journal_failed = True
        self._uncertain = True
        raise TaskManagerError('journal_unavailable', 'Task history could not be safely recorded')

    def _persist(self, task: Task) -> None:
        """Commit to disk under lock and key; write error acceptance/success is not counted."""
        if self._journal_failed:
            self._journal_error()
        if self._journal is not None:
            try:
                self._journal.save(task)
            except JournalError:
                self._journal_error()

    def get(self, task_id: str) -> Task:
        """Export the current independent copy of the task; do not standby or start."""
        with self._condition:
            return _snapshot(self._entry(task_id).task)

    def wait(self, task_id: str, timeout: float | None = None) -> Task:
        """Wait for terminal result; If wait time expires, throw TimeoutError.

        This period only limits the caller's waiting time. Does not cancel the task, unknown
        It doesn't and it doesn't kill the running thread. So the wait timeout is success or
        It cannot be considered as evidence that it was not implemented. Worker cannot wait in his own queue.
        """
        _timeout(timeout)
        with self._condition:
            entry = self._entry(task_id)
            if current_thread() is self._worker and not entry.task.status.terminal:
                raise TaskManagerError("worker_wait", "Worker cannot wait for its own queue")
            if not self._condition.wait_for(lambda: entry.task.status.terminal, timeout):
                raise TimeoutError("Task is still unfinished")
            return _snapshot(entry.task)

    def cancel(self, task_id: str) -> Task:
        """Finish the job in the queue; Send lone collaborative cancel signal to the running job.

        If the working handler returns with a successful result, late cancellation
        does not delete. The handler must notify that it has stopped with the CANCELLED result.
        """
        with self._condition:
            entry = self._entry(task_id)
            if not entry.task.status.terminal:
                entry.cancel_event.set()
                if entry.task.status == TaskStatus.QUEUED:
                    self._queue.remove(task_id)
                    self._finish(entry, self._result(entry, TaskStatus.CANCELLED, "cancelled",
                                                    "Cancelled before execution"))
                else:
                    entry.task = replace(entry.task, status=TaskStatus.CANCEL_REQUESTED)
                self._condition.notify_all()
            return _snapshot(entry.task)

    def close(self, timeout: float | None = 5.0) -> bool:
        """Stop the new acceptance, cancel the pending ones, and wait for the worker to finish.

        True worker means it is actually closed. False there is still a working handler
        means; The application should not show this as a safe shutdown completed.
        Thread is not a daemon: it is not silently abandoned on normal exit.
        """
        _timeout(timeout)
        if current_thread() is self._worker:
            raise TaskManagerError("worker_wait", "Worker cannot close itself synchronously")
        with self._condition:
            self._closing = True
            self._cancel_pending("Manager is closing")
            for entry in self._entries.values():
                if not entry.task.status.terminal:
                    entry.cancel_event.set()
                    entry.task = replace(entry.task, status=TaskStatus.CANCEL_REQUESTED)
            self._condition.notify_all()
        self._worker.join(timeout)
        stopped = not self._worker.is_alive()
        with self._condition:
            if stopped and self._journal is not None:
                self._journal.close()
        return stopped

    def __enter__(self):
        """Allows use in the with block; The worker will be closed on exit."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Silently hiding the worker stuck at the with exit."""
        if not self.close():
            raise TaskManagerError("shutdown_timeout", "Worker is still running")

    @staticmethod
    def _result(entry: _Entry, status: TaskStatus, code: str, message: str) -> ToolResult:
        """Convert the result failed/cancelled/uncertain produced by the Manager to the common type."""
        return ToolResult(task_id=entry.task.task_id, status=status,
                          error=ToolError(code=code, message=message))

    def _finish(self, entry: _Entry, result: ToolResult) -> None:
        """Place terminal state and result together under lock and key."""
        entry.task = replace(entry.task, status=result.status, result=result)
        try:
            self._persist(entry.task)
        except TaskManagerError:
            # If the tool is truly finished, do not consider it as having undone its result. Store
            # error locks new jobs; On restart, the old RUNNING becomes unknown.
            pass

    def _cancel_pending(self, reason: str) -> None:
        """Cancel jobs that have not yet run under lock and empty the queue."""
        while self._queue:
            entry = self._entries[self._queue.popleft()]
            if not entry.task.status.terminal:
                entry.cancel_event.set()
                self._finish(entry, self._result(entry, TaskStatus.CANCELLED, "cancelled", reason))

    def _execute(self, entry: _Entry) -> ToolResult:
        """Worker's single handler call; Leaking user data from exception message."""
        started = False
        try:
            request = self._registry.validate_request(entry.task.request)
            spec = self._registry.get(request.tool)
            if iscoroutinefunction(spec.handler):
                return self._result(entry, TaskStatus.FAILED, "unsupported_handler", "Expected a synchronous handler")
            # Callback makes independent copies; accidentally changed parameters
            # Do not run any other data instead of previously verified data.
            if self._authorize is None or self._authorize(_copy_request(request), replace(spec)) is not True:
                return self._result(entry, TaskStatus.FAILED, "permission_denied", "Execution not authorized")
            with self._condition:
                if entry.cancel_event.is_set():
                    return self._result(entry, TaskStatus.CANCELLED, "cancelled", "Cancelled before execution")
                # There is no delivery to the tool until the transaction is completed. Crash from this recording
                # If it happens later, the restart result is counted as UNKNOWN.
                self._persist(entry.task)
                # After this point, it is deemed to be delivered to the handler. later
                # Incoming cancellation is seen with Event; It has not started yet, no guarantee is given.
                started = True
            context = ToolContext(task_id=entry.task.task_id, request=_copy_request(request),
                                  cancel_event=entry.cancel_event)
            raw = spec.handler(request.arguments, context)
            if not isinstance(raw, ToolResult):
                # If the sync function accidentally returned a coroutine, start it without initializing it.
                # close; Don't leave the unawaited coroutine warning unattended.
                if iscoroutine(raw):
                    raw.close()
                return self._result(entry, TaskStatus.UNKNOWN, "invalid_result", "Handler returned no valid result")
            result = _copy_result(raw)
            if result.task_id != entry.task.task_id:
                return self._result(entry, TaskStatus.UNKNOWN, "invalid_result", "Handler result has wrong task id")
            return result
        except RegistryError as error:
            # The RegistryError thrown after the Handler runs also has no side effects.
            # does not prove that it was not done; Only preflight error can say FAILED.
            return self._result(entry, TaskStatus.UNKNOWN if started else TaskStatus.FAILED,
                                "handler_error" if started else error.code, "Tool validation or execution failed")
        except BaseException:
            # Plugin errors that can kill the worker, such as SystemExit, are also
            # Don't leave your tail unattended. The main thread's signals are not kept here.
            return self._result(entry, TaskStatus.UNKNOWN if started else TaskStatus.FAILED,
                                "handler_error" if started else "preflight_error", "Tool execution could not be confirmed")

    def _run(self) -> None:
        """Single worker loop: get queue, run outside lock, publish result."""
        while True:
            with self._condition:
                self._condition.wait_for(lambda: bool(self._queue) or self._closing)
                if not self._queue:
                    return
                entry = self._entries[self._queue.popleft()]
                if entry.task.status.terminal:
                    continue
                entry.task = replace(entry.task, status=TaskStatus.RUNNING)
                self._condition.notify_all()
            result = self._execute(entry)
            with self._condition:
                self._finish(entry, result)
                if result.status == TaskStatus.UNKNOWN or self._uncertain:
                    # Uncertain external processing may be ongoing. Because Worker is back
                    # We do not start the next handler considering the common resource is safe.
                    self._uncertain = True
                    self._cancel_pending("Earlier operation has unknown outcome")
                self._condition.notify_all()
