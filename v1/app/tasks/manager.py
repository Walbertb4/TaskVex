"""TaskVex's single worker task and replay manager.

submit accepts the request; A single worker operates the handlers sequentially. get/wait
gives a copy of the status, cancel requests cancellation, close stops accepting new jobs.
Since there is a single worker, two handlers do not use a common resource at the same time, such as a desktop.

When a persistent profile is given, the disk log is recorded before execution. parallel
It is not a resource planner or policy engine. Execution if no authorization callback
is rejected. Thread does not force cancellation; The handler must manage its own sub-resources.
"""

from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field, replace
from inspect import iscoroutine, iscoroutinefunction
import math
from pathlib import Path
from threading import Condition, Event, Thread, current_thread
from time import monotonic
from typing import Callable, NoReturn
from uuid import uuid4

from app.core.contracts import (
    ContractError, Task, TaskStatus, ToolContext, ToolError,
    ToolRequest, ToolResult, ToolSpec, request_fingerprint,
)
from app.session.tool_registry import RegistryError, ToolRegistry
from app.policy.task_scope import AccessRequirement, TaskScopes
from app.automation.targets import TargetReferences
from app.storage.task_journal import JournalError, TaskJournal
from app.tasks.workflow import _Workflow, WorkflowStep, TERMINAL, STEP_TERMINAL, copy_steps, definition_key, validate_steps


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
    deadline: float | None = None
    attempts: int = 0


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
                 capacity: int = 256, journal_home: Path | None = None,
                 task_scopes: TaskScopes | None = None,
                 target_references: TargetReferences | None = None,
                 access_requirement: Callable[[ToolRequest], AccessRequirement | None] | None = None,
                 input_preference: Callable[[], bool] | None = None) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TaskManagerError("invalid_registry", "Expected ToolRegistry")
        if authorize is not None and not callable(authorize):
            raise TaskManagerError("invalid_authorizer", "Expected authorization callback")
        if type(capacity) is not int or capacity < 1:
            raise TaskManagerError("invalid_capacity", "Capacity must be a positive integer")
        if ((task_scopes is not None and not isinstance(task_scopes, TaskScopes))
                or (target_references is not None and (task_scopes is None
                    or not isinstance(target_references, TargetReferences)
                    or not target_references.uses_scopes(task_scopes)))):
            raise TaskManagerError('invalid_scope_owner', 'Expected matching task scope and target owners')
        self._task_scopes, self._target_references = task_scopes, target_references
        if (access_requirement is not None and (task_scopes is None or not callable(access_requirement))
                or input_preference is not None and (task_scopes is None or not callable(input_preference))):
            raise TaskManagerError('invalid_scope_owner', 'Permission callbacks require a scope owner')
        self._access_requirement, self._input_preference = access_requirement, input_preference
        self._scope_cleanup_failed = False
        self._registry = registry
        self._authorize = authorize
        self._capacity = capacity
        self._entries: dict[str, _Entry] = {}
        self._requests: dict[tuple[str, str], str] = {}
        self._queue: deque[str] = deque()
        # Logical intake order shares this owner/worker; it is not another executor.
        self._workflows: dict[str, _Workflow] = {}
        self._workflow_order: deque[str] = deque()
        self._active_workflow: str | None = None
        self._workflow_tasks: dict[str, tuple[str, str]] = {}
        # Condition locks both records and prevents the worker from using the processor in an empty queue.
        # It allows him to sleep without getting busy. This lock is not held while the Handler is running.
        self._condition = Condition()
        self._closing = False
        self._journal = TaskJournal(journal_home) if journal_home is not None else None
        self._acknowledged_unknowns: set[str] = set()
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

    @property
    def scope_cleanup_failed(self) -> bool:
        """Distinguish a resource cleanup fault from an uncertain tool outcome."""
        with self._condition:
            return self._scope_cleanup_failed

    @property
    def task_scopes(self) -> TaskScopes | None:
        """Trusted host composition only; never serialized to UI/model payloads."""
        return self._task_scopes

    def unresolved_tasks(self) -> list[dict]:
        """Expose IDs/tool names for local review, without private arguments/results."""
        with self._condition:
            if self._journal_failed:
                self._journal_error()
            try:
                tasks = self._journal.unresolved() if self._journal else [entry.task for entry in self._entries.values()
                    if entry.task.status == TaskStatus.UNKNOWN and entry.task.task_id not in self._acknowledged_unknowns]
            except JournalError:
                self._journal_error()
            return [{'task_id': task.task_id, 'tool': task.request.tool} for task in tasks]

    def acknowledge_unknown(self, task_ids: list[str]) -> None:
        """Local recovery retains UNKNOWN and dedup records; no handler is rerun.

        No worker may be active. Failed storage or an unseen new unknown still
        blocks work. Acknowledgement does not infer whether the old action happened.
        """
        if (type(task_ids) is not list or not 1 <= len(task_ids) <= 256
                or any(type(item) is not str or not item.strip() or len(item) > 128 for item in task_ids)
                or len(set(task_ids)) != len(task_ids)):
            raise TaskManagerError('invalid_recovery', 'Select valid task IDs for review')
        with self._condition:
            if self._scope_cleanup_failed:
                raise TaskManagerError('scope_cleanup_failed', 'Restart after task resource cleanup failure')
            if self._closing or self._journal_failed:
                raise TaskManagerError('recovery_unavailable', 'Task history must be available before review')
            if any(not entry.task.status.terminal for entry in self._entries.values()):
                raise TaskManagerError('task_active', 'Wait for active tasks before review')
            for task_id in task_ids:
                if self._entry(task_id).task.status != TaskStatus.UNKNOWN:
                    raise TaskManagerError('invalid_recovery', 'Only unknown results can be acknowledged')
            try:
                if self._journal:
                    self._journal.acknowledge(task_ids)
                else:
                    self._acknowledged_unknowns.update(task_ids)
                self._uncertain = bool(self.unresolved_tasks())
            except JournalError:
                self._journal_error()

    def describe_tools(self) -> list[dict]:
        """Notify model adapter only; grant handler and authorization object.

        Schemas are independent copies of the registry. This catalog is not a permission;
        The adapter selects the visible subset, again checking the current policy on execution.
        """
        return [{"name": tool.name, "description": tool.description,
                 "parameters": tool.input_schema} for tool in self._registry.list_tools()]

    def submit_workflow(self, workflow_id: str, steps: tuple[WorkflowStep, ...], *,
                        principal: str = 'local-user', source: str = 'desktop',
                        authorization_id: str | None = None, sealed: bool = True,
                        start_paused: bool = False) -> dict:
        """Accept a host plan without holding a conversation turn or running handlers.

        This is not model exposure: the later host binding must enforce ModelTools
        visibility/domain gates. Actual steps still use registry/policy/this worker.
        """
        job = _Workflow(workflow_id, validate_steps(steps), principal, source, authorization_id, sealed)
        if type(start_paused) is not bool:
            raise TaskManagerError('invalid_workflow', 'Expected a boolean initial pause')
        job.creation_key = definition_key([job.creation_key, start_paused])
        if start_paused:
            job.wait_reason = 'user_action'
        for step in job.steps:
            self._registry.validate_request(job.request(step))
        with self._condition:
            if self._closing:
                raise TaskManagerError('closed', 'TaskManager is closing')
            existing = self._workflows.get(workflow_id)
            if existing is not None:
                if existing.creation_key != job.creation_key:
                    raise TaskManagerError('workflow_conflict', 'Workflow ID has different content')
                return existing.snapshot(safety_locked=self._uncertain)
            if self._uncertain:
                raise TaskManagerError('uncertain_state', 'An earlier operation has unknown outcome')
            for key, old in list(self._workflows.items()):
                if len(self._workflows) < self._capacity:
                    break
                if old.status in TERMINAL:
                    del self._workflows[key]
            if len(self._workflows) >= self._capacity:
                raise TaskManagerError('capacity_exceeded', 'Active logical task capacity reached')
            history = any(p == principal and rid.startswith(job.prefix) for p, rid in self._requests)
            if self._journal is not None:
                try:
                    history |= self._journal.has_requests(principal, job.prefix)
                    history |= self._journal.workflow(principal, workflow_id) is not None
                except JournalError:
                    self._journal_error()
            # Lost plan/context is not proof that a previous step can be repeated,
            # nor permission to continue its dependents from a historical success.
            if history:
                job.status = 'review_required'
                job.recovery_stub = True
            else:
                self._check_workflow_scope(job)
                self._workflow_order.append(workflow_id)
            self._workflows[workflow_id] = job
            self._save_workflows()
            self._advance_workflows()
            self._condition.notify_all()
            return job.snapshot(safety_locked=self._uncertain)

    def get_workflow(self, workflow_id: str) -> dict:
        """Read progress only; never schedule new operations as a query side effect."""
        with self._condition:
            return self._workflow(workflow_id).snapshot(safety_locked=self._uncertain)

    def workflows(self, *, principal: str, source: str) -> list[dict]:
        """Bounded current-process progress only; no payloads, grants or restart dispatch."""
        if any(type(value) is not str or not value.strip() for value in (principal, source)):
            raise TaskManagerError('invalid_owner', 'Expected task principal and source')
        with self._condition:
            return [job.snapshot(safety_locked=self._uncertain) for job in self._workflows.values()
                    if job.principal == principal and job.source == source]

    def _workflow(self, workflow_id: str) -> _Workflow:
        if not isinstance(workflow_id, str) or workflow_id not in self._workflows:
            raise TaskManagerError('unknown_workflow', 'Logical task ID is not known')
        return self._workflows[workflow_id]

    def update_workflow(self, workflow_id: str, steps: tuple[WorkflowStep, ...], *,
                        expected_revision: int, sealed: bool | None = None,
                        remove: tuple[str, ...] = ()) -> dict:
        """CAS upsert/remove of unsent steps; no resending private completed bodies."""
        patches = copy_steps(steps)
        if type(expected_revision) is not int or expected_revision < 0 or (sealed is not None and type(sealed) is not bool):
            raise TaskManagerError('invalid_revision', 'Expected workflow revision and optional sealed flag')
        if (not isinstance(remove, (tuple, list)) or any(not isinstance(v, str) for v in remove)
                or len(set(remove)) != len(remove) or set(remove) & {s.step_id for s in patches}):
            raise ContractError('Expected distinct removal IDs without conflicting upserts')
        with self._condition:
            job = self._workflow(workflow_id)
            if job.revision != expected_revision:
                raise TaskManagerError('workflow_changed', 'Read the current logical task revision')
            if self._closing or self._uncertain or job.stop_requested or job.status in TERMINAL | {'review_required'}:
                raise TaskManagerError('workflow_closed', 'Logical task cannot accept this correction')
            if job.wait_reason is not None and job.permission is None and job.permission_result is None:
                raise TaskManagerError('workflow_waiting', 'Reobserve and continue before changing this plan')
            self._check_workflow_scope(job)
            incoming = {s.step_id: s for s in patches}
            previous = {s.step_id: s for s in job.steps}
            if set(remove) - previous.keys():
                raise TaskManagerError('unknown_step', 'Removal names an unknown logical step')
            for old in job.steps:
                if old.step_id in job.task_ids and (old.step_id in remove
                        or (old.step_id in incoming and definition_key(old.definition()) !=
                            definition_key(incoming[old.step_id].definition()))):
                    raise TaskManagerError('step_locked', 'Submitted or concluded steps cannot be changed')
            merged = [incoming.get(s.step_id, s) for s in job.steps if s.step_id not in remove]
            merged.extend(s for s in patches if s.step_id not in previous)
            owned = validate_steps(merged)
            for step in owned:
                self._registry.validate_request(job.request(step))
            job.steps = owned
            job.states = {s.step_id: job.states[s.step_id] if s.step_id in job.task_ids else 'pending' for s in owned}
            job.codes = {key: value for key, value in job.codes.items() if key in job.task_ids}
            job.blocked_by.clear()
            if sealed is not None:
                job.sealed = sealed
            job.revision += 1
            self._invalidate_permission(job)
            self._save_workflows()
            self._advance_workflows()
            self._condition.notify_all()
            return job.snapshot(safety_locked=self._uncertain)

    def _check_workflow_revision(self, workflow_id: str, expected_revision: int) -> _Workflow:
        """Check a host decision under the Condition, including after unlocked reads."""
        if type(expected_revision) is not int or expected_revision < 0:
            raise TaskManagerError('invalid_revision', 'Expected a non-negative workflow revision')
        job = self._workflow(workflow_id)
        if job.revision != expected_revision:
            raise TaskManagerError('workflow_changed', 'Read the current logical task revision')
        if self._closing or self._uncertain or job.stop_requested or job.status in TERMINAL | {'review_required'}:
            raise TaskManagerError('workflow_closed', 'Logical task cannot accept this decision')
        return job

    def _check_workflow_scope(self, job: _Workflow, *, authorization_id: str | None = None) -> None:
        scope_id = authorization_id if authorization_id is not None else job.authorization_id
        if self._task_scopes is not None and scope_id is not None:
            if (job.source != 'desktop' or not self._task_scopes.active(
                    scope_id, job.principal, task_id=job.workflow_id)):
                raise TaskManagerError('invalid_scope', 'Scope must belong to this logical task and principal')

    def _release_workflow_scope(self, job: _Workflow) -> None:
        """Revoke before cancelling effects; never turn a late real result into rollback."""
        if self._task_scopes is None or job.recovery_stub or job.scope_released or job.authorization_id is None:
            return
        try:
            try:
                self._task_scopes.end(job.authorization_id)
            finally:
                if self._target_references is not None:
                    self._target_references.release_scope(job.authorization_id)
            job.scope_released = True
        except Exception:
            # Keep cleaning other jobs, but no further dispatch/review can clear this fault.
            self._scope_cleanup_failed = self._uncertain = True

    def _invalidate_permission(self, job: _Workflow) -> None:
        if job.permission is not None:
            job.permission_result = {'id': job.permission['id'], 'task_id': job.workflow_id, 'outcome': 'invalidated'}
            job.permission = None

    def permission_view(self) -> dict:
        """RAM-only review data; no authority IDs, callbacks or persistent request bodies."""
        with self._condition:
            pending, decisions = [], []
            for job in self._workflows.values():
                prompt = job.permission
                if prompt is not None:
                    pending.append({'id': prompt['id'], 'task_id': job.workflow_id, 'kind': prompt['kind'],
                        'step_id': prompt['step_id'], 'tool': prompt['request'].tool,
                        'arguments': deepcopy(prompt['request'].arguments),
                        'resources': sorted(prompt['requirement'].resources)})
                if job.permission_result is not None:
                    decisions.append({**job.permission_result, 'task_completed': job.status in TERMINAL})
            return {'pending': pending, 'decisions': decisions}

    def _permission_requirement(self, request: ToolRequest) -> AccessRequirement:
        try:
            requirement = self._access_requirement(_copy_request(request)) if self._access_requirement else None
        except Exception:
            requirement = None
        if not isinstance(requirement, AccessRequirement):
            raise TaskManagerError('permission_unavailable', 'Trusted operation requirements are unavailable')
        return requirement

    def request_workflow_permission(self, workflow_id: str, step_id: str, *, expected_revision: int) -> dict:
        """Host asks for one unmet concrete permission before accepting any effect."""
        with self._condition:
            job = self._check_workflow_revision(workflow_id, expected_revision)
            self._check_workflow_scope(job)
            if self._task_scopes is None or job.authorization_id is None or job.active_step is not None or job.status != 'waiting_for_user':
                raise TaskManagerError('permission_unavailable', 'Pause a scoped task before requesting consent')
            step = next((s for s in job.steps if s.step_id == step_id), None)
            if step is None or job.states[step_id] != 'pending':
                raise TaskManagerError('step_locked', 'Consent requires an unsent step')
            request = self._registry.validate_request(job.request(step))
            requirement = self._permission_requirement(request)
            ask = self._input_preference() if self._input_preference else True
            if type(ask) is not bool:
                raise TaskManagerError('permission_unavailable', 'Physical input preference is invalid')
            grants = self._task_scopes.resources(request)
            kind = ('scope' if not requirement.resources <= grants else
                    'input' if requirement.physical_input and ask and not self._task_scopes.allows(
                        request, AccessRequirement(physical_input=True), ask_before_input=True) else
                    'operation' if requirement.high_impact and not self._task_scopes.allows(
                        request, AccessRequirement(high_impact=True), ask_before_input=True) else None)
            if kind is None:
                self._invalidate_permission(job)
                return {'required': False, 'task_id': workflow_id}
            previous = job.permission
            if previous is None or request_fingerprint(previous['request']) != request_fingerprint(request) or previous['requirement'] != requirement or previous['kind'] != kind:
                self._invalidate_permission(job)
                job.permission = {'id': uuid4().hex, 'kind': kind, 'revision': job.revision,
                    'step_id': step_id, 'request': request, 'requirement': requirement}
            assert job.permission is not None
            return {'required': True, 'id': job.permission['id'], 'task_id': workflow_id}

    def decide_workflow_permission(self, decision_id: str, approve: bool) -> dict:
        """Consume a concrete UI nonce; acceptance does not run or complete the task."""
        if type(decision_id) is not str or not decision_id.strip() or type(approve) is not bool:
            raise TaskManagerError('invalid_permission', 'Expected a decision ID and boolean approval')
        with self._condition:
            job = next((j for j in self._workflows.values() if j.permission and j.permission['id'] == decision_id), None)
            if job is None:
                previous = next((j.permission_result for j in self._workflows.values()
                    if j.permission_result and j.permission_result['id'] == decision_id), None)
                if previous is not None and previous['outcome'] == ('approved' if approve else 'denied'):
                    return {**previous, 'accepted': True,
                            'task_completed': self._workflows[previous['task_id']].status in TERMINAL}
                raise TaskManagerError('stale_permission', 'Permission request is no longer current')
            prompt = job.permission
            assert prompt is not None
            self._check_workflow_revision(job.workflow_id, prompt['revision'])
            self._check_workflow_scope(job)
            step = next(s for s in job.steps if s.step_id == prompt['step_id'])
            current = job.request(step)
            try:
                live_requirement = self._permission_requirement(current)
            except TaskManagerError:
                self._invalidate_permission(job)
                raise
            if (job.active_step is not None or job.status != 'waiting_for_user'
                    or request_fingerprint(current) != request_fingerprint(prompt['request'])
                    or live_requirement != prompt['requirement']):
                self._invalidate_permission(job)
                raise TaskManagerError('stale_permission', 'Operation changed; request fresh consent')
            if approve:
                assert self._task_scopes is not None
                scope_id = job.authorization_id
                assert scope_id is not None
                if prompt['kind'] == 'scope':
                    resources = self._task_scopes.resources(current) | prompt['requirement'].resources
                    self._task_scopes.end(scope_id)
                    fresh = self._task_scopes.begin(task_id=job.workflow_id, principal=job.principal, resources=resources)
                    self.replace_workflow_scope(job.workflow_id, expected_revision=job.revision, authorization_id=fresh)
                elif prompt['kind'] == 'input':
                    self._task_scopes.grant_input(scope_id)
                else:
                    self._task_scopes.approve(current)
            job.permission = None
            job.permission_result = {'id': decision_id, 'task_id': job.workflow_id,
                                     'outcome': 'approved' if approve else 'denied'}
            return {**job.permission_result, 'accepted': True, 'task_completed': False}

    def replace_workflow_scope(self, workflow_id: str, *, expected_revision: int,
                               authorization_id: str) -> dict:
        """Bind a fresh host-approved scope only at a safe checkpoint, never grant it.

        The host pauses/reobserves and revokes the old scope before issuing the new
        one for this same task. Pending UI/model data cannot call begin/approve here.
        """
        with self._condition:
            job = self._check_workflow_revision(workflow_id, expected_revision)
            if self._task_scopes is None or type(authorization_id) is not str or not authorization_id.strip():
                raise TaskManagerError('invalid_scope', 'Expected a fresh host-issued task scope')
            if job.active_step is not None:
                raise TaskManagerError('task_active', 'Pause and wait for accepted work before scope replacement')
            if authorization_id == job.authorization_id:
                raise TaskManagerError('invalid_scope', 'Scope replacement requires a fresh identity')
            self._check_workflow_scope(job, authorization_id=authorization_id)
            self._release_workflow_scope(job)
            if self._scope_cleanup_failed:
                self._task_scopes.end(authorization_id)
                raise TaskManagerError('scope_cleanup_failed', 'Restart after resource cleanup failure')
            job.authorization_id = authorization_id
            self._invalidate_permission(job)
            job.scope_released = False
            job.revision += 1
            self._save_workflows()
            return job.snapshot(safety_locked=self._uncertain)

    def recoverable_workflows(self, *, principal: str = 'local-user', after: str = '', limit: int = 256) -> list[dict]:
        """Page private restart metadata without loading plans, grants or scheduling."""
        if (type(principal) is not str or not principal.strip() or type(after) is not str
                or type(limit) is not int or not 1 <= limit <= 256):
            raise TaskManagerError('invalid_recovery', 'Expected principal, cursor and bounded page size')
        with self._condition:
            if self._journal is None or self._journal_failed:
                raise TaskManagerError('recovery_unavailable', 'Persistent task history is required')
            try:
                return self._journal.recoverable_workflows(principal, after, limit)
            except JournalError:
                self._journal_error()

    def _recovery_record(self, workflow_id: str, principal: str, expected_revision: int, *, dismiss: bool = False) -> dict:
        if (type(expected_revision) is not int or expected_revision < 0
                or type(workflow_id) is not str or not workflow_id.strip()
                or type(principal) is not str or not principal.strip()):
            raise TaskManagerError('invalid_recovery', 'Expected workflow identity and revision')
        if self._closing or (self._uncertain and not dismiss) or self._journal_failed or self._journal is None:
            raise TaskManagerError('recovery_unavailable', 'Resolve safety locks before continuing')
        try:
            record = self._journal.workflow(principal, workflow_id)
        except JournalError:
            self._journal_error()
        if record is None or record['status'] != 'recovery_required' or (record['stop_requested'] and not dismiss):
            raise TaskManagerError('not_recoverable', 'Logical task is not awaiting restart recovery')
        if record['revision'] != expected_revision:
            raise TaskManagerError('workflow_changed', 'Read the current recovery revision')
        current = self._workflows.get(workflow_id)
        if current is not None and not current.recovery_stub:
            raise TaskManagerError('workflow_active', 'Logical task already belongs to this process')
        return record

    def recover_workflow(self, workflow_id: str, *, expected_revision: int,
                         replan: Callable[[dict], tuple[WorkflowStep, ...]], principal: str = 'local-user',
                         authorization_id: str | None = None, sealed: bool = True) -> dict:
        """Explicit trusted-host Continue: reobserve/replan outside locks, never restore payloads.

        The host must obtain missing intent/parameters and current permission itself.
        Past steps are metadata only; every new operation needs a fresh step ID.
        """
        if not callable(replan):
            raise TaskManagerError('invalid_observer', 'Expected a trusted fresh-state replanner')
        with self._condition:
            record = self._recovery_record(workflow_id, principal, expected_revision)
            if self._task_scopes is not None and authorization_id is not None:
                if record['source'] != 'desktop' or not self._task_scopes.active(
                        authorization_id, principal, task_id=workflow_id):
                    raise TaskManagerError('invalid_scope', 'Recovery requires a current scope for this task')
        try:
            steps = validate_steps(replan(deepcopy(record)))
        except Exception:
            raise TaskManagerError('reobservation_required', 'Fresh remaining work could not be planned') from None
        job = _Workflow(workflow_id, steps, principal, record['source'], authorization_id, sealed)
        job.history = record['history'] + record['steps']
        if {s.step_id for s in steps} & {s['step_id'] for s in job.history}:
            raise TaskManagerError('step_locked', 'Historical step IDs cannot be dispatched again')
        for step in steps:
            self._registry.validate_request(job.request(step))
        job.revision = expected_revision + 1
        job.creation_key = record['creation_key']
        with self._condition:
            if self._recovery_record(workflow_id, principal, expected_revision) != record:
                raise TaskManagerError('workflow_changed', 'Recovery state changed during reobservation')
            self._check_workflow_scope(job)
            for key, old in list(self._workflows.items()):
                if len(self._workflows) < self._capacity or workflow_id in self._workflows:
                    break
                if old.status in TERMINAL:
                    del self._workflows[key]
            if len(self._workflows) >= self._capacity and workflow_id not in self._workflows:
                raise TaskManagerError('capacity_exceeded', 'Active logical task capacity reached')
            try:
                assert self._journal is not None
                self._journal.save_workflow(job.record(), expected_revision=expected_revision)
            except JournalError:
                self._journal_error()
            job.saved_key = definition_key(job.record())
            self._workflows[workflow_id] = job
            self._workflow_order.append(workflow_id)
            self._advance_workflows()
            self._condition.notify_all()
            return job.snapshot(safety_locked=self._uncertain)

    def cancel_recovery(self, workflow_id: str, *, expected_revision: int,
                        principal: str = 'local-user') -> dict:
        """Explicitly dismiss a restart task without rewriting any effect receipt."""
        with self._condition:
            record = self._recovery_record(workflow_id, principal, expected_revision, dismiss=True)
            record.update(status='cancelled', stop_requested=True, revision=expected_revision + 1)
            try:
                assert self._journal is not None
                self._journal.save_workflow(record, expected_revision=expected_revision)
            except JournalError:
                self._journal_error()
            return record

    def pause_workflow(self, workflow_id: str, *, expected_revision: int, reason: str) -> dict:
        """Host-requested intervention; finish any accepted operation before yielding."""
        if reason not in ('login', 'captcha', 'two_factor', 'elevation', 'user_action'):
            raise TaskManagerError('invalid_wait', 'Expected a supported intervention reason')
        with self._condition:
            job = self._check_workflow_revision(workflow_id, expected_revision)
            if job.wait_reason is not None:
                raise TaskManagerError('workflow_waiting', 'Logical task already awaits intervention')
            job.wait_reason = reason
            job.revision += 1
            job.status = 'wait_requested'
            if job.active_step is None:
                self._yield_workflow(job)
            self._advance_workflows()
            self._condition.notify_all()
            return job.snapshot(safety_locked=self._uncertain)

    def _yield_workflow(self, job: _Workflow) -> None:
        """A safe intervention checkpoint releases intake without occupying a worker."""
        if job.sealed and all(state in STEP_TERMINAL for state in job.states.values()):
            self._complete_workflow(job)
            return
        job.status = 'waiting_for_user'
        if job.workflow_id in self._workflow_order:
            self._workflow_order.remove(job.workflow_id)
        if self._active_workflow == job.workflow_id:
            self._active_workflow = None

    def resume_workflow(self, workflow_id: str, *, expected_revision: int,
                        reobserve: Callable[[], bool]) -> dict:
        """Explicit host Continue; fresh target/permission validation runs outside locks.

        The callback is trusted host code, never a model/UI boolean. It must check
        current resources and authorization; normal policy still checks each step.
        """
        if not callable(reobserve):
            raise TaskManagerError('invalid_observer', 'Expected a trusted reobservation callback')
        with self._condition:
            job = self._check_workflow_revision(workflow_id, expected_revision)
            if job.status != 'waiting_for_user':
                raise TaskManagerError('not_waiting', 'Wait for the current operation to finish')
            if job.permission is not None:
                raise TaskManagerError('permission_pending', 'Resolve the pending UI decision before continuing')
            if job.permission_result is not None and job.permission_result['outcome'] == 'denied':
                raise TaskManagerError('permission_denied', 'The user denied this task permission')
            self._check_workflow_scope(job)
            observed_job = job
        try:
            observed = reobserve() is True
        except Exception:
            observed = False
        with self._condition:
            job = self._check_workflow_revision(workflow_id, expected_revision)
            if job is not observed_job:
                raise TaskManagerError('workflow_changed', 'Logical task changed during reobservation')
            if job.status != 'waiting_for_user' or not observed:
                raise TaskManagerError('reobservation_required', 'Fresh state and authorization were not confirmed')
            self._check_workflow_scope(job)
            job.wait_reason = None
            job.observation_key = None
            job.no_progress_count = 0
            job.revision += 1
            job.status = 'queued'
            self._save_workflows()
            self._workflow_order.append(workflow_id)
            self._advance_workflows()
            self._condition.notify_all()
            return job.snapshot(safety_locked=self._uncertain)

    def observe_workflow(self, workflow_id: str, *, expected_revision: int,
                         observe: Callable[[], dict]) -> dict:
        """Evaluate a planning checkpoint using trusted fresh state, not model prose.

        Retain only a RAM digest. Polling progress or editing a plan never counts
        as evidence; a verified completed operation resets the counter separately.
        """
        if not callable(observe):
            raise TaskManagerError('invalid_observer', 'Expected a trusted observation callback')
        with self._condition:
            job = self._check_workflow_revision(workflow_id, expected_revision)
            if job.status != 'planning' or job.wait_reason is not None:
                raise TaskManagerError('not_planning', 'Observe an idle planning checkpoint')
            self._check_workflow_scope(job)
            observed_job = job
        try:
            state = observe()
            if type(state) is not dict or not state:
                raise ValueError('Missing observation')
            key = definition_key(state)
        except Exception:
            raise TaskManagerError('observation_unavailable', 'Fresh state could not be observed') from None
        with self._condition:
            job = self._check_workflow_revision(workflow_id, expected_revision)
            if job is not observed_job:
                raise TaskManagerError('workflow_changed', 'Logical task changed during observation')
            if job.status != 'planning' or job.wait_reason is not None:
                raise TaskManagerError('not_planning', 'Planning checkpoint changed during observation')
            self._check_workflow_scope(job)
            job.no_progress_count = job.no_progress_count + 1 if key == job.observation_key else 0
            job.observation_key = key
            job.revision += 1
            if job.no_progress_count >= 3:
                job.wait_reason = 'no_progress'
                self._advance_workflows()
            self._save_workflows()
            self._condition.notify_all()
            return job.snapshot(safety_locked=self._uncertain)

    def cancel_workflow(self, workflow_id: str, *, expected_revision: int | None = None,
                        principal: str | None = None, source: str | None = None) -> dict:
        """Accept Stop for this logical ID, not whichever conversation is newest."""
        with self._condition:
            job = self._workflow(workflow_id)
            if ((principal is not None and job.principal != principal)
                    or (source is not None and job.source != source)):
                raise TaskManagerError('unknown_workflow', 'Logical task does not belong to this host')
            if expected_revision is not None:
                if type(expected_revision) is not int or expected_revision < 0:
                    raise TaskManagerError('invalid_revision', 'Expected a nonnegative task revision')
                if job.revision != expected_revision:
                    raise TaskManagerError('workflow_changed', 'Read the current task revision before Stop')
            if job.status not in TERMINAL:
                if job.recovery_stub and self._journal is not None:
                    try:
                        record = self._journal.workflow(job.principal, workflow_id)
                    except JournalError:
                        self._journal_error()
                    if record is not None and record['status'] == 'recovery_required':
                        self.cancel_recovery(workflow_id, principal=job.principal, expected_revision=record['revision'])
                self._stop_workflow(job, 'workflow_stopped')
                self._advance_workflows()
                self._condition.notify_all()
            return job.snapshot(safety_locked=self._uncertain)

    def _record_workflow_task(self, task: Task) -> None:
        """Mirror real worker state into progress; no extra execution/result authority."""
        owner = self._workflow_tasks.get(task.task_id)
        if owner is None:
            return
        workflow_id, step_id = owner
        job = self._workflows[workflow_id]
        job.states[step_id] = task.status.value
        if task.result is not None and task.result.error is not None:
            job.codes[step_id] = task.result.error.code
        if task.status.terminal:
            job.active_step = None
            del self._workflow_tasks[task.task_id]
            if task.status == TaskStatus.SUCCEEDED:
                job.no_progress_count = 0
                job.observation_key = None

    def _complete_workflow(self, job: _Workflow) -> None:
        """Aggregate metadata without erasing successful effects or private receipts."""
        self._invalidate_permission(job)
        states = set(job.states.values())
        if 'unknown' in states:
            job.status = 'unknown'
        elif any(s['status'] == 'unknown' for s in job.history):
            job.status = 'unknown'
        elif job.status == 'review_required' or (job.stop_requested and (not job.sealed or states - {'succeeded'})):
            job.status = 'cancelled'
        elif states - {'succeeded'}:
            job.status = 'failed'
        else:
            job.status = 'succeeded'
        self._release_workflow_scope(job)
        # Terminal progress needs IDs/tool names, not a second RAM payload history.
        job.steps = tuple(replace(s, arguments={}) for s in job.steps)
        job.wait_reason = None
        job.observation_key = None
        if job.workflow_id in self._workflow_order:
            self._workflow_order.remove(job.workflow_id)
        if self._active_workflow == job.workflow_id:
            self._active_workflow = None

    def _stop_workflow(self, job: _Workflow, reason: str) -> None:
        job.stop_requested = True
        self._invalidate_permission(job)
        self._release_workflow_scope(job)
        for step in job.steps:
            if job.states[step.step_id] == 'pending':
                job.states[step.step_id] = 'cancelled'
                job.codes[step.step_id] = reason
        if job.active_step is not None:
            self.cancel(job.task_ids[job.active_step])
        if job.active_step is None:
            self._complete_workflow(job)
        else:
            job.status = 'cancel_requested'

    def _advance_workflows(self) -> None:
        try:
            self._advance_workflow_queue()
        finally:
            self._save_workflows()

    def _save_workflows(self) -> None:
        """Checkpoint only changed metadata before the lock can release queued work."""
        if self._journal is None or self._journal_failed:
            return
        try:
            for job in self._workflows.values():
                if job.recovery_stub or job.suspended_on_close:
                    continue
                record = job.record()
                key = definition_key(record)
                if key != job.saved_key:
                    self._journal.save_workflow(record)
                    job.saved_key = key
        except JournalError:
            self._journal_error()

    def _advance_workflow_queue(self) -> None:
        """Admit one ready step to the existing queue; never call/wait on a handler."""
        if self._closing or self._uncertain:
            for job in list(self._workflows.values()):
                if job.status not in TERMINAL:
                    self._stop_workflow(job, 'manager_closing' if self._closing else 'uncertain_state')
            return
        while True:
            if self._active_workflow is None:
                while self._workflow_order:
                    candidate = self._workflow_order.popleft()
                    if candidate in self._workflows and self._workflows[candidate].status not in TERMINAL | {'waiting_for_user'}:
                        self._active_workflow = candidate
                        break
            if self._active_workflow is None:
                return
            job = self._workflows[self._active_workflow]
            if job.active_step is not None:
                return
            if job.stop_requested:
                self._complete_workflow(job)
                continue
            if job.wait_reason is not None:
                self._yield_workflow(job)
                continue
            # Propagate definite prerequisite failures; independent branches survive.
            changed = True
            while changed:
                changed = False
                for step in job.steps:
                    bad = tuple(d for d in step.depends_on if job.states[d] in STEP_TERMINAL - {'succeeded'})
                    if job.states[step.step_id] == 'pending' and bad:
                        job.states[step.step_id] = 'blocked'
                        job.blocked_by[step.step_id] = bad
                        job.codes[step.step_id] = 'dependency_failed'
                        changed = True
            ready = next((s for s in job.steps if job.states[s.step_id] == 'pending'
                          and all(job.states[d] == 'succeeded' for d in s.depends_on)), None)
            if ready is None:
                if not job.sealed:
                    job.status = 'planning'
                    return  # No spin: waiting for a host plan update holds no worker.
                self._complete_workflow(job)
                continue
            try:
                task = self.submit(job.request(ready))
            except (TaskManagerError, RegistryError) as error:
                if error.code == 'capacity_exceeded' and any(not e.task.status.terminal for e in self._entries.values()):
                    return  # Existing queued/running tools will wake this owner on completion.
                job.states[ready.step_id] = 'failed'
                job.codes[ready.step_id] = error.code
                if self._uncertain or self._closing:
                    self._advance_workflows()
                    return
                continue
            job.task_ids[ready.step_id] = task.task_id
            job.states[ready.step_id] = task.status.value
            job.active_step = ready.step_id
            job.status = 'running'
            self._workflow_tasks[task.task_id] = (job.workflow_id, ready.step_id)
            if task.status.terminal:
                self._record_workflow_task(task)
                job.status = 'review_required'
                self._active_workflow = None
                continue
            return

    def submit(self, request: ToolRequest) -> Task:
        """Queue the current request or grant the current task for the same identity/content.

        Repeat key (principal, request_id). Fingerprint channel, tool and all
        Also includes parameters. Different users may use the same request_id;
        If the same user uses the same ID for different request, he will get an error.
        """
        owned = self._registry.validate_request(request)
        fingerprint = request_fingerprint(owned)
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
                    record = self._journal.find(*key)
                except JournalError:
                    self._journal_error()
                if record is not None:
                    archived, original_fingerprint = record
                    if original_fingerprint != fingerprint:
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
                    # Disk receipts are read-only; their redacted request is never dispatched.
                    return _Entry(task=archived, fingerprint='')
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

    def operation_progress(self, task_id: str) -> dict:
        """Host telemetry; elapsed deadline is not cancellation or actual completion."""
        with self._condition:
            entry = self._entry(task_id)
            available = task_id in self._entries
            metadata = entry.task.result.evidence.get('operation_policy') if entry.task.result is not None else None
            exceeded = (bool(metadata.get('deadline_exceeded')) if entry.deadline is not None and isinstance(metadata, dict)
                        else False) if entry.task.result is not None else (
                        entry.deadline is not None and monotonic() >= entry.deadline)
            return {'task_id': task_id, 'status': entry.task.status.value,
                    'completed': entry.task.status.terminal, 'telemetry_available': available,
                    'attempts': entry.attempts if available else None,
                    'deadline_exceeded': exceeded if available else None,
                    'cancel_requested': entry.cancel_event.is_set() if available else None}

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
                self._record_workflow_task(entry.task)
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
            if self._journal is not None and not self._journal_failed:
                try:
                    for job in self._workflows.values():
                        if job.status not in TERMINAL and not job.stop_requested and not job.recovery_stub and not job.suspended_on_close:
                            record = job.record()
                            record.update(status='recovery_required', revision=job.revision + 1)
                            self._journal.save_workflow(record)
                            job.suspended_on_close = True
                except JournalError:
                    self._journal_failed = self._uncertain = True
            self._cancel_pending("Manager is closing")
            for entry in self._entries.values():
                if not entry.task.status.terminal:
                    entry.cancel_event.set()
                    entry.task = replace(entry.task, status=TaskStatus.CANCEL_REQUESTED)
                    self._record_workflow_task(entry.task)
            self._advance_workflows()
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
        self._record_workflow_task(entry.task)

    def _cancel_pending(self, reason: str) -> None:
        """Cancel jobs that have not yet run under lock and empty the queue."""
        while self._queue:
            entry = self._entries[self._queue.popleft()]
            if not entry.task.status.terminal:
                entry.cancel_event.set()
                self._finish(entry, self._result(entry, TaskStatus.CANCELLED, "cancelled", reason))

    def _execute(self, entry: _Entry) -> ToolResult:
        """At most one safe read retry, inside the same worker/request/deadline."""
        started_at = monotonic()
        try:
            policy = self._registry.get(entry.task.request.tool)
        except RegistryError as error:
            return self._result(entry, TaskStatus.FAILED, error.code, 'Tool is unavailable')
        except BaseException:
            return self._result(entry, TaskStatus.FAILED, 'preflight_error', 'Tool policy could not be verified')
        with self._condition:
            entry.deadline = started_at + policy.timeout_seconds if policy.timeout_seconds is not None else None
        result = self._execute_once(entry)
        blocked = None
        if (entry.attempts == 1 and policy.read_only and result.status == TaskStatus.FAILED and result.error is not None
                and result.error.code in policy.transient_errors):
            with self._condition:
                blocked = ('cancelled' if entry.cancel_event.is_set() or self._closing else
                           'uncertain_state' if self._uncertain or self._journal_failed else
                           'operation_deadline' if entry.deadline is not None and monotonic() >= entry.deadline else None)
            if blocked is None:
                previous_attempts = entry.attempts
                retried = self._execute_once(entry)
                if entry.attempts > previous_attempts:
                    result = retried
                else:
                    # No new handler ran: keep the actual failed read, not a fake second result.
                    blocked = retried.error.code if retried.error is not None else 'preflight_failed'
        if policy.timeout_seconds is not None:
            result = replace(result, evidence={**result.evidence, 'operation_policy': {
                'attempts': entry.attempts, 'retry_blocked': blocked,
                'deadline_exceeded': entry.deadline is not None and monotonic() >= entry.deadline}})
        return result

    def _execute_once(self, entry: _Entry) -> ToolResult:
        """One authorized handler delivery; unconfirmed delivery outcomes stay UNKNOWN."""
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
                if self._closing or self._uncertain or self._journal_failed:
                    return self._result(entry, TaskStatus.FAILED, 'uncertain_state', 'Execution is not currently safe')
                if entry.deadline is not None and monotonic() >= entry.deadline:
                    return self._result(entry, TaskStatus.FAILED, 'operation_deadline', 'Operation deadline elapsed before dispatch')
                # There is no delivery to the tool until the transaction is completed. Crash from this recording
                # If it happens later, the restart result is counted as UNKNOWN.
                self._persist(entry.task)
                if entry.deadline is not None and monotonic() >= entry.deadline:
                    return self._result(entry, TaskStatus.FAILED, 'operation_deadline', 'Operation deadline elapsed before dispatch')
                # After this point, it is deemed to be delivered to the handler. later
                # Incoming cancellation is seen with Event; It has not started yet, no guarantee is given.
                started = True
                entry.attempts += 1
            context = ToolContext(task_id=entry.task.task_id, request=_copy_request(request),
                                  cancel_event=entry.cancel_event, deadline=entry.deadline)
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
                self._record_workflow_task(entry.task)
                self._condition.notify_all()
            result = self._execute(entry)
            with self._condition:
                self._finish(entry, result)
                if result.status == TaskStatus.UNKNOWN or self._uncertain:
                    # Uncertain external processing may be ongoing. Because Worker is back
                    # We do not start the next handler considering the common resource is safe.
                    self._uncertain = True
                    self._cancel_pending("Earlier operation has unknown outcome")
                try:
                    self._advance_workflows()
                except TaskManagerError:
                    # Failed recovery metadata locks admission; keep the worker alive for cleanup.
                    self._cancel_pending('Task history unavailable')
                self._condition.notify_all()
