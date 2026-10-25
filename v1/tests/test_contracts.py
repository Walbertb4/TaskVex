import json
from dataclasses import FrozenInstanceError

import pytest

from app.core.contracts import (
    ContractError, Task, TaskStatus, ToolContext, ToolError,
    ToolRequest, ToolResult, ToolSpec,
)


def request(**changes):
    return ToolRequest(**{
        "request_id": "request-1", "source": "desktop", "principal": "local-user",
        "tool": "notes.add", "arguments": {"text": "Hello"}, **changes,
    })


def result(status=TaskStatus.SUCCEEDED, **changes):
    return ToolResult(**{
        "task_id": "task-1", "status": status,
        "verified": status == TaskStatus.SUCCEEDED,
        "error": ToolError(code="uncertain", message="No final receipt")
        if status in (TaskStatus.FAILED, TaskStatus.UNKNOWN) else None,
        **changes,
    })


def test_request_keeps_json_values_and_detaches_caller_and_serialized_data():
    arguments = {"items": [0, False, None, {"text": 'Turkish'}]}
    item = request(arguments=arguments)
    arguments["items"].clear()
    wire = item.to_dict()
    wire["arguments"]["items"].clear()
    assert item.arguments == {"items": [0, False, None, {"text": 'Turkish'}]}
    assert json.loads(json.dumps(item.to_dict(), allow_nan=False)) == item.to_dict()
    with pytest.raises(FrozenInstanceError):
        item.request_id = "changed"


@pytest.mark.parametrize("field,value", [
    ("request_id", " "), ("source", None), ("principal", 17),
    ("tool", "notes"), ("tool", "notes;exec"), ("tool", "notes..add"),
    ("arguments", []), ("arguments", {"x": float("nan")}),
    ("arguments", {"x": float("inf")}), ("arguments", {1: "coerced key"}),
    ("arguments", {"x": object()}), ("arguments", {"x": (1, 2)}),
])
def test_invalid_requests_cannot_enter_core(field, value):
    with pytest.raises(ContractError):
        request(**{field: value})


def test_circular_json_rejected_but_shared_non_circular_values_work():
    cycle = []
    cycle.append(cycle)
    with pytest.raises(ContractError):
        request(arguments={"x": cycle})
    shared = [1]
    assert request(arguments={"a": shared, "b": shared}).arguments == {"a": [1], "b": [1]}


@pytest.mark.parametrize("changes", [
    {"verified": False}, {"verified": 1},
    {"error": ToolError(code="failed", message="Conflict")},
    {"status": TaskStatus.RUNNING}, {"status": TaskStatus.CANCEL_REQUESTED},
    {"status": "succeeded"}, {"data": {"value": float("inf")}},
    {"evidence": []},
])
def test_accepted_or_invalid_response_cannot_become_success(changes):
    with pytest.raises(ContractError):
        result(**changes)


@pytest.mark.parametrize("status", [TaskStatus.FAILED, TaskStatus.UNKNOWN])
def test_failure_and_uncertainty_require_reason_and_cannot_claim_verified(status):
    with pytest.raises(ContractError):
        result(status, error=None)
    with pytest.raises(ContractError):
        result(status, verified=True)


@pytest.mark.parametrize("status", [
    TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.UNKNOWN,
])
def test_terminal_task_and_result_have_same_identity_status_and_wire_values(status):
    outcome = result(status, data={"count": 0}, evidence={"receipt": "local-write"})
    task = Task(task_id="task-1", request=request(), status=status, result=outcome)
    wire = json.loads(json.dumps(task.to_dict(), allow_nan=False))
    assert wire["status"] == status.value == wire["result"]["status"]
    assert wire["result"]["data"]["count"] == 0
    with pytest.raises(ContractError):
        Task(task_id="other-task", request=request(), status=status, result=outcome)
    with pytest.raises(ContractError):
        Task(task_id="task-1", request=request(), status=status)


def test_cancel_request_is_unfinished_and_different_from_cancelled():
    task = Task(task_id="task-1", request=request(), status=TaskStatus.CANCEL_REQUESTED)
    assert not task.status.terminal
    assert task.to_dict()["result"] is None
    with pytest.raises(ContractError):
        Task(task_id="task-1", request=request(), result=result())
    with pytest.raises(ContractError):
        Task(task_id="task-1", request=request(), status=TaskStatus.FAILED, result=result())


def test_context_cancellation_is_per_task_and_not_an_automatic_final_result():
    first = ToolContext(task_id="task-1", request=request(), deadline=10.5)
    second = ToolContext(task_id="task-2", request=request())
    first.cancel_event.set()
    assert first.cancel_event.is_set()
    assert not second.cancel_event.is_set()


@pytest.mark.parametrize("deadline", [float("nan"), float("inf"), -1, True, "10"])
def test_invalid_deadlines_rejected(deadline):
    with pytest.raises(ContractError):
        ToolContext(task_id="task-1", request=request(), deadline=deadline)


def test_tool_registration_does_not_execute_handler_and_detaches_schema():
    def handler(arguments, context):
        raise AssertionError("A contract must not execute a tool")

    schema = {"type": "object", "properties": {"text": {"type": "string"}}}
    spec = ToolSpec(name="notes.add", description="Add a note", input_schema=schema,
                    handler=handler, required_capabilities=("notes.write",),
                    exclusive_resources=("notes-store",))
    schema["properties"].clear()
    assert spec.input_schema["properties"] == {"text": {"type": "string"}}
    assert spec.handler is handler


@pytest.mark.parametrize("changes", [
    {"name": "bad name"}, {"description": ""}, {"handler": None},
    {"input_schema": {"type": "array"}}, {"input_schema": []},
    {"required_capabilities": ["notes.write"]},
    {"required_capabilities": ("notes.write", "notes.write")},
    {"exclusive_resources": ("",)},
])
def test_invalid_tool_declarations_rejected(changes):
    with pytest.raises(ContractError):
        ToolSpec(**{
            "name": "notes.add", "description": "Add note",
            "input_schema": {"type": "object"}, "handler": lambda args, ctx: None,
            **changes,
        })


def test_error_wire_data_is_structured_and_detached():
    error = ToolError(code="not_found", message="Missing note", details={"id": "n1"})
    wire = error.to_dict()
    wire["details"]["id"] = "changed"
    assert error.details["id"] == "n1"
    with pytest.raises(ContractError):
        ToolError(code="", message="Missing note")
