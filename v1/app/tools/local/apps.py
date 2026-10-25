"""Authorized catalog of the first application plugin; Read-only start of Phase 4.

The catalog tells you which applications TaskVex chooses to support. on computer
does not prove that the application is installed/running; apps.status Windows adapter
Makes read-only observations using apps.open verifies opening with the same observation. With tool parameter
No file path, shell commands or additional application records are taken.
"""

from types import MappingProxyType
import time

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult


# ID is the permanent machine name; The display name can be translated. Mapping is read-only
# and its values are text, so the caller can modify the host by replacing a result list.
# cannot expand the allowed app catalog. The first scope is just Notepad.
APP_CATALOG = MappingProxyType({"notepad": "Notepad"})
STATUS_SCHEMA = {
    "type": "object", "properties": {"app_id": {"type": "string", "enum": list(APP_CATALOG)}},
    "required": ["app_id"], "additionalProperties": False,
}
OPEN_WAIT_SECONDS = 5.0  # Host limit; user/model cannot enlarge it.


def app_catalog(arguments: dict, context: ToolContext) -> ToolResult:
    """Answer parameterless catalog query with common result and cancellation agreement.

    verified=True verifies that only the built-in catalog has been read; installation or
    It is not evidence of an open window. An independent list is created with each call.
    This tool does not write files, scan applications, or launch applications.
    """
    if arguments:
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                          error=ToolError(code="invalid_arguments",
                                          message="Application catalog accepts no arguments"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    return ToolResult(
        task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
        data={"apps": [{"id": app_id, "name": name} for app_id, name in APP_CATALOG.items()]},
        evidence={"source": "builtin_allowlist"},
    )


def app_status(arguments: dict, context: ToolContext) -> ToolResult:
    """Observe the process/window status of the permitted target; Don't call success an observation error.

    A valid implicit observation is also SUCCEEDED; this means the app is open
    It does not mean that the query is completed. Partial observation includes FAILED/data;
    The null field should not be displayed as zero/off. Native libraries only
    the call is loaded instantly, core startup does not create Windows UI dependency.
    """
    if (set(arguments) != {"app_id"} or not isinstance(arguments["app_id"], str)
            or arguments["app_id"] not in APP_CATALOG):
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                          error=ToolError(code="invalid_arguments", message="Expected a supported app_id"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    from app.tools.local.windows_apps import observe_notepad
    try:
        data = observe_notepad(context.cancel_event)
    except InterruptedError:
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    except (NotImplementedError, OSError) as error:
        code = "platform_unsupported" if isinstance(error, NotImplementedError) else "observation_unavailable"
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                          error=ToolError(code=code, message="Application state could not be observed"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    complete = data["complete"]
    return ToolResult(task_id=context.task_id,
                      status=TaskStatus.SUCCEEDED if complete else TaskStatus.FAILED,
                      verified=complete, data=data,
                      error=None if complete else ToolError(code="observation_incomplete",
                                                           message="Application observation was incomplete"),
                      evidence={"source": "win32_process_identity+EnumWindows"})


def app_open(arguments: dict, context: ToolContext) -> ToolResult:
    """Provide permissioned Notepad window; Distinguish between acceptance and completion.

    If there is already a verified window, no new launch will be made. There is a process but
    If there is no window, the current opening is expected; The second process is not desired. no process
    If it is confirmed by full observation that it is not, only the host's system launcher is a
    is called once. A WS_VISIBLE window proves visibility; readiness for focus/interaction
    It is not a guarantee. Cancellation before initiation produces no side effects. initialization
    cancellation/error/timeout does not undo the record after being requested: it returns UNKNOWN and
    There is no automatic repeat. External Notepad cannot be forcibly closed.
    """
    before = app_status(arguments, context)
    if before.status != TaskStatus.SUCCEEDED:
        return before

    def success(observation, requested):
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                          data={**observation, "launch_requested": requested,
                                "already_open": not requested},
                          evidence={"source": "win32_process_identity+EnumWindows",
                                    "window_observed": True, "launch_requested": requested})

    def stopped(requested, code, message):
        return ToolResult(task_id=context.task_id,
                          status=TaskStatus.UNKNOWN if requested else TaskStatus.FAILED,
                          error=ToolError(code=code, message=message),
                          data={"app_id": arguments["app_id"], "launch_requested": requested})

    if before.data["visible_window"]:
        return success(before.data, False)
    requested = False
    if not before.data["running"]:
        from app.tools.local.windows_apps import notepad_launcher, start_notepad
        try:
            executable = notepad_launcher()
        except (OSError, NotImplementedError):
            return stopped(False, "launcher_unavailable", "Notepad system launcher is unavailable")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        # Put the flag before the call: side effect though initialization return is lost
        # may have been made. In case of error, the second start call is not made.
        requested = True
        try:
            start_notepad(executable)
        except Exception:
            return stopped(True, "launch_unconfirmed", "Notepad launch could not be confirmed")

    deadline = time.monotonic() + OPEN_WAIT_SECONDS
    while True:
        if context.cancel_event.is_set():
            if requested:
                return stopped(True, "launch_unconfirmed", "Launch was requested before cancellation; check application state")
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        observed = app_status(arguments, context)
        if observed.status == TaskStatus.SUCCEEDED and observed.data["visible_window"]:
            return success(observed.data, requested)
        if observed.status == TaskStatus.CANCELLED:
            if requested:
                return stopped(True, "launch_unconfirmed", "Launch was requested before cancellation; check application state")
            return observed
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return stopped(requested, "window_unconfirmed" if requested else "window_not_observed",
                           "A Notepad window could not be confirmed; no automatic retry was made")
        context.cancel_event.wait(min(0.1, remaining))
