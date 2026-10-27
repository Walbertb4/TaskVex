"""Open permission list for first local tools; The default decision is rejection.

The Registry controls the parameter format, and this module controls who can request the operation.
TaskManager uses the authorize method just before calling the handler.
The authorization statement of a field or plugin sent by the model does not create permission.

principal/source values must come from the reliable input adapter; here is a
matching text is not real user authentication or Python sandboxing.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable

from app.core.contracts import ContractError, ToolRequest, ToolSpec
from app.policy.task_scope import AccessRequirement, TaskScopes


# Tool -> core determines the required authorization mapping. Plugin from its own declaration
# cannot derive authority; An empty or different required_capabilities declaration is also rejected.
_TOOL_CAPABILITIES = MappingProxyType({
    'weather.current':frozenset({'weather.read'}),
    'weather.locations':frozenset({'weather.read'}),
    "assistant.request_sleep_mode": frozenset({"assistant.control"}),
    "assistant.request_shutdown": frozenset({"assistant.control"}),
    "apps.catalog": frozenset({"apps.read"}),
    "apps.status": frozenset({"apps.read"}),
    "apps.open": frozenset({"apps.read", "apps.launch"}),
    "memory.propose": frozenset({"memory.write"}),
    "memory.decide": frozenset({"memory.write"}),
    "memory.read": frozenset({"memory.read"}),
    "memory.patch": frozenset({"memory.write"}),
    "notes.add": frozenset({"notes.write"}),
    "notes.update": frozenset({"notes.write"}),
    "notes.delete": frozenset({"notes.write"}),
    "notes.initialize": frozenset({"notes.write"}),
    "notes.replace": frozenset({"notes.write"}),
    "notes.list": frozenset({"notes.read"}),
    "notes.select": frozenset({"notes.read"}),
    "notes.delete_many": frozenset({"notes.write"}),
    "notes.complete_many": frozenset({"notes.write"}),
    "clocks.create": frozenset({"clocks.write"}),
    "clocks.delete": frozenset({"clocks.write"}),
    "clocks.control": frozenset({"clocks.write"}),
    "clocks.list": frozenset({"clocks.read"}),
    "system.status": frozenset({"system.read"}),
    "media.status": frozenset({"media.read"}),
    "media.control": frozenset({"media.control"}),
})
_KNOWN_CAPABILITIES = frozenset().union(*_TOOL_CAPABILITIES.values())


@dataclass(frozen=True, kw_only=True)
class PolicyEngine:
    """It keeps the permissions granted to a single local user at application startup.

    principal is the user defined by the trusted host. capabilities clearly
    If it is not given, it remains empty and all transactions are rejected. For example notes.read alone
    allows note listing; notes.write does not automatically grant reading permissions.
    Permissions are copied at startup, the outside set cannot change the permission later.

    Optional host-owned task scopes add resource/risk checks. They do not suspend
    handlers for approval or authenticate external channels. UI binding is separate.
    """

    principal: str
    capabilities: frozenset[str] = frozenset()
    scopes: TaskScopes | None = None
    resolve_access: Callable[[ToolRequest], AccessRequirement | None] | None = None
    ask_before_input: bool = True

    def __post_init__(self) -> None:
        """Make incorrect host configuration a startup error instead of silent permission."""
        if not isinstance(self.principal, str) or not self.principal.strip():
            raise ContractError("Policy principal must be a non-empty string")
        # Although the text is iterable, the authorization list is not. Open only set/tuple/list
        # is accepted; We do not produce frozen sets without checking every element.
        if not isinstance(self.capabilities, (set, frozenset, tuple, list)) or any(
            not isinstance(item, str) or item not in _KNOWN_CAPABILITIES
            for item in self.capabilities
        ):
            raise ContractError("Policy capabilities must contain known capability names")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        if ((self.scopes is None) != (self.resolve_access is None)
                or (self.scopes is not None and not isinstance(self.scopes, TaskScopes))
                or (self.resolve_access is not None and not callable(self.resolve_access))
                or type(self.ask_before_input) is not bool):
            raise ContractError('Expected paired task scope store/resolver and boolean input preference')

    def authorize(self, request: ToolRequest, tool: ToolSpec) -> bool:
        """TaskManager callback: return True only if all conditions are met.

        Request/tool mapping, desktop resource, user and core expect
        authorization notification is checked together. Parameter validation in registry
        remains; This function does not run a handler, does not generate a confirmation, and does not save data.
        """
        if not isinstance(request, ToolRequest) or not isinstance(tool, ToolSpec):
            return False
        if (request.source != "desktop" or request.principal != self.principal
                or request.tool != tool.name):
            return False
        required = _TOOL_CAPABILITIES.get(tool.name)
        if (required is None or frozenset(tool.required_capabilities) != required
                or not required <= self.capabilities):
            return False
        if self.resolve_access is None or self.scopes is None:
            return request.authorization_id is None
        try:
            requirement = self.resolve_access(ToolRequest(**request.to_dict()))
        except Exception:
            return False
        if requirement is None:
            return request.authorization_id is None
        return isinstance(requirement, AccessRequirement) and self.scopes.allows(
            request, requirement, ask_before_input=self.ask_before_input)
