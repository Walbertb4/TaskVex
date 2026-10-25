"""Common data formats that TaskVex components will use when talking to each other.

The contract specifies, for example, which fields will be included in a tool request and which
determines that the results are valid. UI, model adapter and TaskManager in the future
will use the same formats; not every component will invent its own result format.

This file does not run tools, does not allow permissions, and does not write to disk. Only given data
Checks the base format and consistency between fields. Tool parameters
For schema validation is in the registry, task execution is in the TaskManager.
"""

from __future__ import annotations

# Type descriptions assist the contract reader and editor; alone
# Does not validate at runtime. That's why there are also explicit controls below.

import math
import re
from dataclasses import dataclass, field
from enum import StrEnum
from threading import Event
from typing import Any, Callable, cast


class ContractError(ValueError):
    """It distinguishes invalid contract data from a regular tool/service error.

    For example, empty request_id produces this error. If there is a network break or disk full
    are other types of problems that can occur during the execution of a valid request.
    """


def _text(value: Any, name: str) -> None:
    """Check that a field is non-empty text; If invalid, throw an error.

    name specifies the field in the error message. The function does not trim or change the value;
    strip() is only used to detect input that consists entirely of spaces.
    """
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")


def _tool_name(value: Any) -> None:
    """Accept tool names that contain fields and actions, such as notes.add.

    The point separates namespaces: notes.add and notes.list are two operations of the same field.
    fullmatch requires all text to comply with the rule; A partially suitable name is not enough.
    This name check is not a permission check; Valid name does not authorize tool operation.
    """
    if not isinstance(value, str) or len(value) > 128 or not re.fullmatch(
        r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+", value
    ):
        raise ContractError("tool name must be namespaced, for example notes.add")


def _json_copy(value: Any, active: set[int] | None = None) -> Any:
    """Validate JSON-compliant data and copy nested lists/dictionaries.

    Thus, even if the caller changes his dictionary later, the created record remains valid.
    does not change. We do not convert unrecognizable objects into text; incorrect data corrected silently
    Instead of appearing like this, it produces ContractError.

    active holds the IDs of the container objects we are currently passing through.
    It is not a list of all seen objects: the same list in two different areas
    can be shared; A data structure returning only to itself is prohibited.
    """
    # We check the exact type with type(...). Special classes from these classes
    # Derivation does not automatically make them supported JSON data.
    # None, False, and 0 are valid and distinct values; All are protected separately.
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    # NaN and infinity cannot pass the above condition. If they are not at List/dictionary
    # here they are rejected; Only containers remain in the rest of the function.
    if type(value) not in (dict, list):
        raise ContractError("expected JSON values with finite numbers")
    active = set() if active is None else active
    # For example, items.append(items) creates a self-revolving list.
    # If we do not notice this, the recursive call, that is, the function calling itself,
    # It continues without progressing through the same data.
    if id(value) in active:
        raise ContractError("cyclic JSON data is not allowed")
    active.add(id(value))
    try:
        if isinstance(value, list):
            # List comprehension: interpret each item in the list as the same validation/copying
            # process and create a new list. Sublists are also copied.
            return [_json_copy(item, active) for item in value]
        # We know that there is a dictionary left here due to previous checks. casting
        # reports this to Pylance; it does not transform the data and does not perform additional validation.
        mapping = cast(dict[str, Any], value)
        # In a JSON object, keys must be text. For example, change the key 1 to "1"
        # By doing so, we reject the wrong type rather than silently changing its meaning.
        if any(type(key) is not str for key in mapping):
            raise ContractError("JSON object keys must be strings")
        return {key: _json_copy(item, active) for key, item in mapping.items()}
    finally:
        # This object moves out of the current visit path on both a successful return and an error.
        # Thus, seeing the same object in the next independent branch is not considered a loop.
        active.remove(id(value))


def copy_json(value: Any) -> Any:
    """Serve the same JSON validation/copy rule to other modules.

    The record layer also contains tuples, loops, non-text keys, and
    reject infinite numbers. The special active parameter is not exposed.
    """
    return _json_copy(value)


def _object(value: Any) -> dict[str, Any]:
    """Use it specifically when you need a JSON object, i.e. Python dict, at the root.

    _json_copy also accepts list alone or null. object like arguments
    We use this narrower control in areas where it should be.
    """
    if type(value) is not dict:
        raise ContractError("expected a JSON object")
    return _json_copy(value)


class TaskStatus(StrEnum):
    """Text-based enum that fixes the spelling of task states.

    An enum is a named list of allowed values. different instead of SUCCEEDED
    It prevents "done" and "success" from being written in places. .value returns the text for moving.
    """
    # In these first four cases the task has not yet reported a definitive result.
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    CANCEL_REQUESTED = "cancel_requested"
    # Terminal means this execution record has concluded. In UNKNOWN
    # we declare that the outcome in the outside world is unknown; There is no automatic repeat.
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

    @property
    def terminal(self) -> bool:
        """Return True if the condition is a result condition; do not run any tasks."""
        return self in (
            TaskStatus.SUCCEEDED, TaskStatus.FAILED,
            TaskStatus.CANCELLED, TaskStatus.UNKNOWN,
        )


# Generates standard methods such as constructor/equality from dataclass fields.
# kw_only=True requires field names such as request_id=... in calls.
# frozen=True prevents the field from being assigned later; It does not deep freeze internal dictionaries.
# Therefore, we use dictionary/lists by producing a new record without changing it on site.
@dataclass(frozen=True, kw_only=True)
class ToolRequest:
    """It conveys what is required of a tool; does not execute the request yet.

    request_id is the ID of the login request, source is the channel it came from, principal is the ID of the request.
    owner, tool are the tool to be called, and arguments are the parameters of that tool.
    Identities are checked here only in form. the user really
    It is the responsibility of the input adapter and policy to verify.
    """
    request_id: str
    source: str
    principal: str
    tool: str
    # default_factory produces a separate dictionary for each request; desires are a common
    # It does not accidentally share the default dictionary.
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the dataclass constructor immediately after assigning the fields."""
        for name in ("request_id", "source", "principal"):
            _text(getattr(self, name), name)
        _tool_name(self.tool)
        # We place the verified copy when setting up the frozen record. this is special
        # Assignment is not a way to change the record in normal use.
        object.__setattr__(self, "arguments", _object(self.arguments))

    def to_dict(self) -> dict[str, Any]:
        """Provide a copy of the dictionary suitable for carrying; Generating JSON text is another step."""
        return {
            "request_id": self.request_id, "source": self.source,
            "principal": self.principal, "tool": self.tool,
            "arguments": _object(self.arguments),
        }


@dataclass(frozen=True, kw_only=True)
class ToolError:
    """Error code and readable cause that the machine can handle.

    code can be not_found for example; message reason details carries additional data.
    API key/token should not be placed in these fields; This class does not mask confidential information.
    """
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Check Kod/reason and copy additional data caller-independently."""
        _text(self.code, "error code")
        _text(self.message, "error message")
        object.__setattr__(self, "details", _object(self.details))

    def to_dict(self) -> dict[str, Any]:
        """Translate the error object into a JSON-compatible, self-contained dictionary."""
        return {"code": self.code, "message": self.message, "details": _object(self.details)}


@dataclass(frozen=True, kw_only=True)
class ToolResult:
    """It carries the terminal outcome of a tool; It is not a notification of acceptance or expectation.

    data is the tool output; evidence observed record/window such as evidence information.
    verified indicates that only successful completion has been verified. write true
    does not create evidence by itself; It is the handler's responsibility to make the actual observation.
    """
    task_id: str
    status: TaskStatus
    verified: bool = False
    data: Any = None
    error: ToolError | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Reject incorrect status/success/error combinations before registration occurs."""
        _text(self.task_id, "task_id")
        if not isinstance(self.status, TaskStatus) or not self.status.terminal:
            raise ContractError("tool result requires a terminal TaskStatus")
        if type(self.verified) is not bool:
            # In Python, bool is a subtype of int. So only bool is accepted
            # we do; We do not allow the value 1 to be used instead of True.
            raise ContractError("verified must be boolean")
        if self.error is not None and not isinstance(self.error, ToolError):
            raise ContractError("error must be ToolError or None")
        if self.status == TaskStatus.SUCCEEDED:
            # Prevents the "request accepted" response from being rounded to completed.
            if not self.verified or self.error is not None:
                raise ContractError("success requires verified=True and no error")
        elif self.verified:
            raise ContractError("verified describes successful completion only")
        if self.status in (TaskStatus.FAILED, TaskStatus.UNKNOWN) and self.error is None:
            # In FAILED the error reason should be, in UNKNOWN the reason should be why it cannot be verified.
            raise ContractError("failed/unknown results require an error or uncertainty reason")
        object.__setattr__(self, "data", _json_copy(self.data))
        object.__setattr__(self, "evidence", _object(self.evidence))

    def to_dict(self) -> dict[str, Any]:
        """Reduce object Enum/error to plain data; recopy internal data."""
        return {
            "task_id": self.task_id, "status": self.status.value,
            "verified": self.verified, "data": _json_copy(self.data),
            "error": self.error.to_dict() if self.error else None,
            "evidence": _object(self.evidence),
        }


@dataclass(frozen=True, kw_only=True)
class Task:
    """The current coherent view of a task; It is not the TaskManager itself.

    task_id is the ID of the execution, request is the input request; The two identities may be different.
    This class does not manage queues or allowed state transitions. TaskManager,
    The following consistency conditions are maintained when generating a new record for the new state.
    """
    task_id: str
    request: ToolRequest
    status: TaskStatus = TaskStatus.QUEUED
    result: ToolResult | None = None

    def __post_init__(self) -> None:
        """If there is a consequence, make sure it pertains to this task and situation."""
        _text(self.task_id, "task_id")
        if not isinstance(self.request, ToolRequest) or not isinstance(self.status, TaskStatus):
            raise ContractError("task requires ToolRequest and TaskStatus")
        if self.status.terminal:
            # Such as the result of another task or a successful result on a failed task.
            # Confusions may result in incorrect status being displayed to the user.
            if not isinstance(self.result, ToolResult):
                raise ContractError("terminal task requires a result")
            if self.result.task_id != self.task_id or self.result.status != self.status:
                raise ContractError("task and result identity/status must match")
        elif self.result is not None:
            raise ContractError("unfinished task cannot have a terminal result")

    def to_dict(self) -> dict[str, Any]:
        """Convert the task, request, and result, if any, into common transport format."""
        return {
            "task_id": self.task_id, "request": self.request.to_dict(),
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
        }


@dataclass(frozen=True, kw_only=True)
class ToolContext:
    """The work context given by the handler to the handler; It is not data to be sent out.

    cancel_event.set() marks the cancellation request; It does not stop the thread automatically.
    The handler must stop safely by checking the signal at appropriate intervals. deadline
    The last time of the time.monotonic() clock, if any; It is not a Unix date/time value.
    """
    task_id: str
    request: ToolRequest
    # Each context receives a separate Event; Cancellation of one task does not propagate to another.
    # repr/compare is off: this operating signal is not view/equality data.
    cancel_event: Event = field(default_factory=Event, repr=False, compare=False)
    deadline: float | None = None

    def __post_init__(self) -> None:
        """Check context types; suspend or cancel operation."""
        _text(self.task_id, "task_id")
        if not isinstance(self.request, ToolRequest) or not isinstance(self.cancel_event, Event):
            raise ContractError("context requires ToolRequest and cancellation Event")
        if self.deadline is not None and (
            type(self.deadline) not in (int, float) or not math.isfinite(self.deadline)
            or self.deadline < 0
        ):
            raise ContractError("deadline must be a finite non-negative monotonic timestamp")


@dataclass(frozen=True, kw_only=True)
class ToolSpec:
    """Description of the tool to be registered in the Registry; Installing this object does not call the tool.

    input_schema is a JSON Schema object that describes the parameter format. handler,
    It is defined as a function that will take (arguments, context) and return ToolResult.
    required_capabilities required powers, exclusive_resources in concurrent use
    are resources to be protected. Declaring these does not grant authority or resource lock;
    policy and TaskManager will do the implementation.
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any], ToolContext], ToolResult]
    required_capabilities: tuple[str, ...] = ()
    exclusive_resources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Check notification format; Performs full parameter schema checking in the registry."""
        _tool_name(self.name)
        _text(self.description, "description")
        schema = _object(self.input_schema)
        # We only check the root object condition. For example, the required field or
        # This check alone does not say that the incoming arguments are compatible with the schema.
        if schema.get("type") != "object":
            raise ContractError("input_schema must declare type=object")
        if not callable(self.handler):
            # callable indicates that it can be called, such as a function; his signature
            # or does not prove here that it will actually return ToolResult.
            raise ContractError("handler must be callable")
        for name in ("required_capabilities", "exclusive_resources"):
            # Notification lists must be tuples: mistakenly substituted insertion/deletion
            # A new notification is created. Empty and duplicate values ​​are not accepted.
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise ContractError(f"{name} must be a tuple")
            for value in values:
                _text(value, name)
            if len(values) != len(set(values)):
                raise ContractError(f"{name} contains duplicates")
        object.__setattr__(self, "input_schema", schema)
