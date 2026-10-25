# Core contracts — Tier 1 / tier 2

October 21, 2026. Implementation: v1/app/core/contracts.py. This module is data contracts only; It does not run registry, TaskManager, policy, registry, UI bridge or model session. No production dependencies added.

## Types

| Type | Fields | Meaning |
|---|---|---|
| ToolRequest | request_id, source, principal, tool, arguments | Single tool request. Task ID and in-session duplication prevention are the responsibility of the TaskManager. |
| ToolSpec | name, description, input_schema, handler, required_capabilities, exclusive_resources | Interior registration of a tool. It does not include UI or model SDK. |
| ToolContext | task_id, request, cancel_event, deadline | Task context from executor to handler. Python Event signal is for collaborative cancellation. |
| ToolError | code, message, details | Structured error or uncertainty justification. Confidential information is not included; log masking is on the next layer. |
| ToolResult | task_id, status, verified, data, error, evidence | Only terminal tool result. Acceptance/pending is not the success result of this type. |
| Task | task_id, request, status, result | A point-in-time record of the task. It is not the object that will implement state transitions. |

request_id the ID of the login request; task_id is the execution ID of the core. It is not assumed that they are the same identity. source/principal cannot be empty, but this format check does not verify identity. The ID will come from the trusted login adapter; The principal written by the model does not give authority.

Tool names carry a lowercase namespace: notes.add, system.status, apps.open. It is the job of the future model adapter to translate the internal tool name into the provider's function-name format.

## States

| TaskStatus | Terminal? | Usage |
|---|---|---|
| queued | No | Next |
| running | No | Working |
| awaiting_approval | No | Waiting for user approval; not yet implemented |
| cancel_requested | No | Cancellation request received; not evidence that the physical process has stopped |
| succeeded | Yes | Handler clearly states that it has confirmed that the transaction has been completed |
| failed | Yes | The cause of the error is known; ToolError mandatory |
| canceled | Yes | Actuator/handler confirmed stop; not confused with acceptance of cancellation request |
| unknown | Yes | The result of this execution could not be verified; ambiguity reason required in ToolError |

verified=True and error=None are mandatory for succeeded. In other cases verified=False; This field only verifies successful completion, not whether an error was observed. Evidence can carry data observed in different situations.

verified=True alone does not prove that a transaction has occurred in the world; The handler must actually observe the evidence. The module prevents incorrect case combinations, it is not a validation engine. There is no way to automatically convert an empty handler return or {ok:true} response to a ToolResult. The TaskManager executor checks the actual return type; UNKNOWN counts the incorrect result.

The result of a terminal Task must be found; the resulting task_id and status must match the task. Unfinished Task terminal cannot carry results. Sequential transition, resource lock and replay rules for run states will be implemented in the TaskManager phase. unknown is not an automatic retry permission.

## JSON and data limit

- arguments/input_schema/details/evidence is JSON object at root. data can be any valid JSON value.
- Object keys text; numbers are finite; tuple, special object and circular structure are rejected. Null, False and true zero are preserved.
- JSON data is copied in constructor and to_dict boundaries; Any change the caller makes to the original list or serialized return does not change the record.
- frozen dataclass prevents field assignment; The interior of dictionary/lists is not made deep immutable. Instead of making in-situ mutations, a new record should be created. Registry/TaskManager will accept and execute its own verification/copy at the limit.
- ToolSpec only checks that the schema is a JSON object and the root type=object. Full JSON Schema validity and compliance of arguments with the tool schema will be verified at the Registry stage; No separate schema engine was written here.
- Provides JSON compatible copy with request, error, result and task to_dict(). The ToolSpec handler and ToolContext Event are not wire payloads; these are not serialized out.
- If there is a deadline, the last time must be in the same time base as time.monotonic(); It's not a Unix timestamp. These types do not check whether the time has expired or not.
- defined as handler signature (arguments, context) -> ToolResult. This step checks for the existence of the callable; It does not call the function and does not consider the signature/return annotation as evidence of execution.

## Example

```python
from app.core.contracts import ToolRequest, ToolResult, Task, TaskStatus

request = ToolRequest(
    request_id="request-1", source="desktop", principal="local-user",
    tool="notes.add", arguments={"text": "Ders note"},
)
queued = Task(task_id="task-1", request=request)

# A handler should only produce success after verifying the actual record:
result = ToolResult(
    task_id="task-1", status=TaskStatus.SUCCEEDED, verified=True,
    data={"note_id": "note-1"}, evidence={"persisted": True},
)
finished = Task(
    task_id="task-1", request=request, status=TaskStatus.SUCCEEDED, result=result,
)
wire = finished.to_dict()
```

The sample does not save a note; It only shows the use of common types. The actual notes tool and output format are now described in [Phase 1 agreement](STAGE1_CORE.md). Existing UI emit payloads have not been silently changed to this internal contract.

## Validation

`.\.venv\Scripts\python.exe -m pytest -q` through v1: 45 tests passed. Tested JSON bounds, loops, zero/null/boolean separation, copy separation from external mutation, task/result identity and state consistency, inter-task separation of abort signal, and bad tool notifications.

Registry, single-worker handler dispatch/status/cancellation, first local permission rules and disk registration layer are now available: [ToolRegistry](TOOL_REGISTRY.md), [TaskManager](TASK_MANAGER.md), [Policy](POLICY.md), [Registry](STORAGE.md). The record layer uses public JSON validation with the public copy_json(value) helper; The fields of data contracts have not changed. Registration testing was performed on temporary files; There is no native or model testing yet. Manager refuses execution by default; Its integration with the policy callback has been tested.

Phase 1 with real notes.add/list and system.status is also completed; **of 215 tests**
current acceptance results are in [STAGE1_CORE.md](STAGE1_CORE.md).
