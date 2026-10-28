"""Logical task contracts/metadata; TaskManager remains the only executor/owner.

Plans are trusted host input, not a new model tool, script language or persistent
scheduler. Full plan arguments stay in RAM; only normal per-step receipts persist.
"""

from collections import deque
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Any

from app.core.contracts import ContractError, ToolRequest


TERMINAL = frozenset({'succeeded', 'failed', 'cancelled', 'unknown'})
STEP_TERMINAL = TERMINAL | {'blocked'}


@dataclass(frozen=True, kw_only=True)
class WorkflowStep:
    """One registered tool operation and prerequisite step IDs, never expressions."""

    step_id: str
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise ContractError('Expected a logical step ID')
        if (not isinstance(self.depends_on, (tuple, list))
                or any(not isinstance(v, str) or not v.strip() for v in self.depends_on)
                or len(set(self.depends_on)) != len(self.depends_on)):
            raise ContractError('Expected unique prerequisite step IDs')
        # Reuse the existing JSON/tool-name contract without submitting any work.
        validated = ToolRequest(request_id='validate-step', source='desktop', principal='host',
                                tool=self.tool, arguments=self.arguments)
        object.__setattr__(self, 'arguments', validated.arguments)
        object.__setattr__(self, 'depends_on', tuple(sorted(self.depends_on)))

    def definition(self) -> dict:
        return {'step_id': self.step_id, 'tool': self.tool, 'arguments': self.arguments,
                'depends_on': list(self.depends_on)}


def copy_steps(steps) -> tuple[WorkflowStep, ...]:
    """Detach plan/patch data before it can become the owner's mutable state."""
    if not isinstance(steps, (tuple, list)) or any(not isinstance(s, WorkflowStep) for s in steps):
        raise ContractError('Expected logical workflow steps')
    owned = tuple(WorkflowStep(**s.definition()) for s in steps)
    if len({s.step_id for s in owned}) != len(owned):
        raise ContractError('Duplicate workflow step IDs')
    return owned


def validate_steps(steps) -> tuple[WorkflowStep, ...]:
    """Validate the complete DAG, including dependencies outside a sparse patch."""
    owned = copy_steps(steps)
    by_id = {s.step_id: s for s in owned}
    if any(set(s.depends_on) - by_id.keys() for s in owned):
        raise ContractError('Duplicate or missing workflow step IDs')
    remaining = {s.step_id: len(s.depends_on) for s in owned}
    followers: dict[str, list[str]] = {key: [] for key in by_id}
    for step in owned:
        for dependency in step.depends_on:
            followers[dependency].append(step.step_id)
    ready = deque(key for key, count in remaining.items() if count == 0)
    visited = 0
    while ready:
        visited += 1
        for child in followers[ready.popleft()]:
            remaining[child] -= 1
            if remaining[child] == 0:
                ready.append(child)
    if visited != len(owned):
        raise ContractError('Workflow dependencies must not contain a cycle')
    return owned


def definition_key(value) -> str:
    """Stable comparison for revisions, distinguishing JSON booleans/numbers."""
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@dataclass
class _Workflow:
    """Private bookkeeping, mutated only under TaskManager's existing Condition."""

    workflow_id: str
    steps: tuple[WorkflowStep, ...]
    principal: str
    source: str
    authorization_id: str | None
    sealed: bool
    revision: int = 0
    status: str = 'queued'
    stop_requested: bool = False
    active_step: str | None = None
    states: dict[str, str] = field(default_factory=dict)
    task_ids: dict[str, str] = field(default_factory=dict)
    codes: dict[str, str] = field(default_factory=dict)
    blocked_by: dict[str, tuple[str, ...]] = field(default_factory=dict)
    creation_key: str = ''
    wait_reason: str | None = None
    no_progress_count: int = 0
    observation_key: str | None = None
    history: list[dict] = field(default_factory=list)
    saved_key: str | None = None
    recovery_stub: bool = False
    suspended_on_close: bool = False
    scope_released: bool = False
    permission: dict | None = None
    permission_result: dict | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.workflow_id, str) or not self.workflow_id.strip() or type(self.sealed) is not bool:
            raise ContractError('Expected workflow ID and sealed flag')
        self.states = {s.step_id: 'pending' for s in self.steps}
        self.creation_key = definition_key([self.principal, self.source, self.authorization_id,
                                           self.sealed, [s.definition() for s in self.steps]])
        # Validate host identity even for an empty incremental plan.
        ToolRequest(request_id='validate-plan', source=self.source, principal=self.principal,
                    tool='workflow.validation', authorization_id=self.authorization_id)

    @property
    def prefix(self) -> str:
        return 'workflow:' + sha256(self.workflow_id.encode()).hexdigest() + ':'

    def request(self, step: WorkflowStep) -> ToolRequest:
        """Stable IDs survive polls/revisions; sent steps cannot be edited/restarted."""
        return ToolRequest(request_id=self.prefix + sha256(step.step_id.encode()).hexdigest(),
            source=self.source, principal=self.principal, tool=step.tool,
            arguments=step.arguments, authorization_id=self.authorization_id)

    def snapshot(self, *, safety_locked: bool) -> dict:
        """Return progress metadata only, never a second copy of private plan bodies."""
        return {'workflow_id': self.workflow_id, 'revision': self.revision, 'status': self.status,
            'completed': self.status in TERMINAL, 'stop_requested': self.stop_requested,
            'sealed': self.sealed, 'requires_review': safety_locked or self.status in {'unknown', 'review_required'}
                or any(s['status'] == 'unknown' for s in self.history),
            'wait_reason': self.wait_reason, 'no_progress_count': self.no_progress_count,
            'historical_steps': [dict(s) for s in self.history],
            'steps': [{'step_id': s.step_id, 'tool': s.tool, 'status': self.states[s.step_id],
                       'task_id': self.task_ids.get(s.step_id), 'error_code': self.codes.get(s.step_id),
                       'blocked_by': list(self.blocked_by.get(s.step_id, ()))} for s in self.steps]}

    def record(self) -> dict:
        """Content-free recovery metadata; no arguments, errors, grants or targets."""
        return {'workflow_id': self.workflow_id, 'principal': self.principal, 'source': self.source,
                'revision': self.revision, 'status': self.status, 'sealed': self.sealed,
                'stop_requested': self.stop_requested, 'creation_key': self.creation_key,
                'history': [dict(s) for s in self.history],
                'steps': [{'step_id': s.step_id, 'tool': s.tool, 'status': self.states[s.step_id],
                           'task_id': self.task_ids.get(s.step_id)} for s in self.steps]}


def validate_record(value: dict) -> dict:
    """Reject extra/private fields and malformed stored identities before recovery."""
    fields = {'workflow_id', 'principal', 'source', 'revision', 'status', 'sealed',
              'stop_requested', 'creation_key', 'history', 'steps'}
    if type(value) is not dict or value.keys() != fields:
        raise ValueError('Invalid workflow record')
    ToolRequest(request_id=value['workflow_id'], principal=value['principal'],
                source=value['source'], tool='workflow.validation')
    if (type(value['revision']) is not int or value['revision'] < 0
            or type(value['sealed']) is not bool or type(value['stop_requested']) is not bool
            or type(value['creation_key']) is not str
            or re.fullmatch(r'[0-9a-f]{64}', value['creation_key']) is None
            or value['status'] not in TERMINAL | {'queued', 'running', 'planning', 'wait_requested',
                'waiting_for_user', 'cancel_requested', 'review_required', 'recovery_required'}):
        raise ValueError('Invalid workflow state')
    ids = set()
    for name in ('steps', 'history'):
        if type(value[name]) is not list:
            raise ValueError('Invalid workflow steps')
        for step in value[name]:
            if type(step) is not dict or step.keys() != {'step_id', 'tool', 'status', 'task_id'}:
                raise ValueError('Invalid workflow step')
            ToolRequest(request_id=step['step_id'], principal=value['principal'],
                        source=value['source'], tool=step['tool'])
            if (step['step_id'] in ids or step['status'] not in STEP_TERMINAL |
                    {'pending', 'queued', 'running', 'cancel_requested'}
                    or (step['task_id'] is not None and
                        (type(step['task_id']) is not str or not step['task_id'].strip()))):
                raise ValueError('Invalid workflow step state')
            ids.add(step['step_id'])
    return json.loads(json.dumps(value, allow_nan=False))
