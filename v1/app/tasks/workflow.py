"""Logical task contracts/metadata; TaskManager remains the only executor/owner.

Plans are trusted host input, not a new model tool, script language or persistent
scheduler. Full plan arguments stay in RAM; only normal per-step receipts persist.
"""

from collections import deque
from dataclasses import dataclass, field
from hashlib import sha256
import json
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
            'sealed': self.sealed, 'requires_review': safety_locked or self.status in {'unknown', 'review_required'},
            'wait_reason': self.wait_reason, 'no_progress_count': self.no_progress_count,
            'steps': [{'step_id': s.step_id, 'tool': s.tool, 'status': self.states[s.step_id],
                       'task_id': self.task_ids.get(s.step_id), 'error_code': self.codes.get(s.step_id),
                       'blocked_by': list(self.blocked_by.get(s.step_id, ()))} for s in self.steps]}
