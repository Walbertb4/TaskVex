"""Host-owned, RAM-only task grants used by the shared policy before dispatch.

This module grants no OS access and executes nothing. Trusted adapters resolve
actual resource references and user decisions; model/tool output cannot issue grants.
"""

from dataclasses import dataclass, field
from threading import Lock
from uuid import uuid4

from app.core.contracts import ContractError, ToolRequest, request_fingerprint


def _resources(values) -> frozenset[tuple[str, str, str]]:
    """Exact (kind, opaque reference, action) matches; no path/prefix/wildcard grants."""
    if not isinstance(values, (set, frozenset, tuple, list)):
        raise ContractError('Expected explicit resource grants')
    for item in values:
        if (type(item) is not tuple or len(item) != 3
                or any(not isinstance(part, str) for part in item)
                or item[0] not in {'app', 'file', 'folder', 'window', 'browser', 'person'}
                or not isinstance(item[1], str) or not item[1].strip() or item[1] == '*'
                or item[2] not in {'read', 'write', 'control', 'capture', 'message', 'call'}):
            raise ContractError('Expected a resource kind, exact reference and action')
    return frozenset(values)


@dataclass(frozen=True, kw_only=True)
class AccessRequirement:
    """Trusted policy resolver output, never supplied by a model or plugin schema."""

    resources: frozenset[tuple[str, str, str]] = frozenset()
    high_impact: bool = False
    physical_input: bool = False

    def __post_init__(self) -> None:
        if type(self.high_impact) is not bool or type(self.physical_input) is not bool:
            raise ContractError('Access flags must be boolean')
        object.__setattr__(self, 'resources', _resources(self.resources))


@dataclass
class _Scope:
    """Private task state; approval digests never retain request content."""

    task_id: str
    principal: str
    resources: frozenset[tuple[str, str, str]]
    input_approved: bool = False
    approvals: set[str] = field(default_factory=set)


class TaskScopes:
    """One host-owned permission store; ending a task removes all its grants.

    Revocation blocks later policy checks, not an authorization already in flight.
    Lifecycle integration must also cancel active work through TaskManager.
    Nothing here survives restart or restores authority from the task journal.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._active: dict[str, _Scope] = {}

    def begin(self, *, task_id: str, principal: str, resources=()) -> str:
        """Issue an opaque scope after the trusted host establishes task authority."""
        if any(not isinstance(v, str) or not v.strip() for v in (task_id, principal)):
            raise ContractError('Expected task and principal IDs')
        grants = _resources(resources)
        with self._lock:
            if any(scope.task_id == task_id for scope in self._active.values()):
                raise ContractError('Task already has an active authorization scope')
            scope_id = uuid4().hex
            self._active[scope_id] = _Scope(task_id=task_id, principal=principal, resources=grants)
            return scope_id

    def _owner(self, request: ToolRequest) -> _Scope | None:
        if request.authorization_id is None or request.source != 'desktop':
            return None
        scope = self._active.get(request.authorization_id)
        return scope if scope is not None and scope.principal == request.principal else None

    def active(self, authorization_id: str, principal: str, *, task_id: str | None = None) -> bool:
        """Read scope liveness/ownership without creating or expanding any grant."""
        if not isinstance(authorization_id, str) or not isinstance(principal, str):
            return False
        with self._lock:
            scope = self._active.get(authorization_id)
            return (scope is not None and scope.principal == principal
                    and (task_id is None or scope.task_id == task_id))

    def approve(self, request: ToolRequest) -> None:
        """Record a real user decision for exactly this request, arguments and scope."""
        with self._lock:
            scope = self._owner(request)
            if scope is None:
                raise ContractError('No active task scope for approval')
            scope.approvals.add(request_fingerprint(request))

    def grant_input(self, authorization_id: str) -> None:
        """Record physical-input handover for this task only; not high-impact consent."""
        with self._lock:
            scope = self._active.get(authorization_id)
            if scope is None:
                raise ContractError('No active task scope for input handover')
            scope.input_approved = True

    def resources(self, request: ToolRequest) -> frozenset[tuple[str, str, str]]:
        """Trusted host view of exact grants, never a grant operation."""
        with self._lock:
            scope = self._owner(request)
            if scope is None:
                raise ContractError('No active task scope')
            return scope.resources

    def end(self, authorization_id: str) -> bool:
        """Revoke references, input handover and operation approvals together."""
        with self._lock:
            return self._active.pop(authorization_id, None) is not None

    def allows(self, request: ToolRequest, requirement: AccessRequirement, *, ask_before_input: bool) -> bool:
        """Check the current task at dispatch; approvals cannot expand resource scope."""
        with self._lock:
            scope = self._owner(request)
            return bool(scope is not None
                and requirement.resources <= scope.resources
                and (not requirement.high_impact or request_fingerprint(request) in scope.approvals)
                and (not requirement.physical_input or not ask_before_input or scope.input_approved))
