"""Local tool that requests the assistant's chat controls from the shared tool line.

These tools do not sleep, do not close windows, do not manage microphone or Live.
It only produces a verified migration request. Real application, successful response
and after the audio end the current UI/host life cycle is in the owner.
"""
from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult


SLEEP_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"mode": {"type": "string", "enum": ["once", "persistent", "off"],
        "description": "once: sleep until woken; persistent: return to sleep after each addressed interaction for this chat; off: disable that return preference, not the idle timer."}},
    "required": ["mode"],
}


def request_sleep_mode(arguments: dict, context: ToolContext) -> ToolResult:
    """Validate the mode and generate the request; A successful result is not proof of actual sleep.

    TaskManager success is the acceptance of this side-effectless request. applied=false field,
    It is specifically included in the result so that the model does not yet claim to be fit.
    In addition to the registry schema check, the direct call also rejects the incorrect mode.
    """
    if set(arguments) != {"mode"} or arguments["mode"] not in ("once", "persistent", "off"):
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
            error=ToolError(code="invalid_arguments", message="Expected a supported sleep mode"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
        data={"mode": arguments["mode"], "apply_after": "reply_playback", "applied": False},
        evidence={"validated_request": True})


SHUTDOWN_SCHEMA = {"type": "object", "additionalProperties": False}


def request_shutdown(arguments: dict, context: ToolContext) -> ToolResult:
    """Just accept the request to close TaskVex; worker does not close the window.

    The main application enters the Shutdown host path after the current response/ring cycle.
    uses. There is no operating system shutdown, restart or free command.
    This result is not the actual window closing, but the validated pending request.
    """
    if arguments:
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
            error=ToolError(code="invalid_arguments", message="TaskVex shutdown accepts no arguments"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
        data={"action": "shutdown", "scope": "taskvex", "apply_after": "reply_playback", "applied": False},
        evidence={"validated_request": True})
