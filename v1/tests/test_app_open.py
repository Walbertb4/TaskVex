"""Try the apps.open result in core, without starting the actual application.

Observation/Windows startup limit is emulated; registry, policy and management
it is real. There should be no additional side effects of double submissions, cancellations and ambiguity.
Actual Windows adoption is kept in separate report; This file does not open a user window.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from app.bootstrap import create_core
from app.core.contracts import TaskStatus, ToolContext, ToolRequest, ToolSpec
from app.policy.engine import PolicyEngine
from app.session.tool_registry import RegistryError
from app.tasks.manager import TaskManagerError
from app.tools.local import apps, windows_apps


def request(request_id="open", **changes):
    """Generate identities based on trusted desktop login; Try adding parameters."""
    return ToolRequest(**{"request_id": request_id, "source": "desktop", "principal": "local-user",
                          "tool": "apps.open", "arguments": {"app_id": "notepad"}, **changes})


def snapshot(running=False, visible=False, complete=True):
    """Produce a controlled observation that preserves the form of the proof Window/identity."""
    return {"app_id": "notepad", "running": running, "visible_window": visible,
            "processes": [{"pid": 123, "identity": "test", "created": "1"}] if running else [],
            "windows": [{"pid": 123, "hwnd": 456, "minimized": False}] if visible else [],
            "complete": complete, "observed_at": "test"}


@pytest.fixture
def boundary(monkeypatch):
    """Just change the OS limit; call counts capture the second launch."""
    calls = {"launch": [], "resolve": [], "observe": [], "responses": [snapshot()]}
    def observe(cancel):
        responses = calls["responses"]
        value = responses.pop(0) if len(responses) > 1 else responses[0]
        calls["observe"].append(True)
        if isinstance(value, Exception):
            raise value
        return deepcopy(value)
    def resolve():
        calls["resolve"].append(True)
        return r"C:\Windows\System32\notepad.exe"
    monkeypatch.setattr(windows_apps, "observe_notepad", observe)
    monkeypatch.setattr(windows_apps, "notepad_launcher", resolve)
    monkeypatch.setattr(windows_apps, "start_notepad", calls["launch"].append)
    monkeypatch.setattr(apps, "OPEN_WAIT_SECONDS", 0)
    return calls


def run(core, req):
    """Expect the actual terminal result, not the Accepted status."""
    return core.wait(core.submit(req).task_id, 3)


@pytest.mark.parametrize("existing", [True, False])
def test_open_requires_verified_window_and_reports_whether_launch_was_needed(boundary, existing):
    boundary["responses"] = ([snapshot(True, True)] if existing else [snapshot(), snapshot(True, True)])
    with create_core() as core:
        result = run(core, request()).result
    assert result.status == TaskStatus.SUCCEEDED and result.verified
    assert result.data["already_open"] is existing
    assert result.data["launch_requested"] is not existing
    assert result.evidence["window_observed"] is True
    assert len(boundary["launch"]) == (0 if existing else 1)


def test_running_without_window_is_waited_without_second_launch(boundary, monkeypatch):
    boundary["responses"] = [snapshot(True), snapshot(True), snapshot(True, True)]
    monkeypatch.setattr(apps, "OPEN_WAIT_SECONDS", 0.2)
    with create_core() as core:
        assert run(core, request()).status == TaskStatus.SUCCEEDED
    assert boundary["launch"] == [] and boundary["resolve"] == []


@pytest.mark.parametrize("post", [snapshot(True), snapshot(), snapshot(None, None, False), OSError("private")])
def test_unconfirmed_launch_is_unknown_and_cannot_be_replayed(boundary, post):
    boundary["responses"] = [snapshot(), post]
    req = request()
    with create_core() as core:
        result = run(core, req)
        assert result.status == TaskStatus.UNKNOWN
        assert result.result.data["launch_requested"] is True
        assert core.submit(req).task_id == result.task_id
        with pytest.raises(TaskManagerError) as caught:
            core.submit(request("new-open"))
        assert caught.value.code == "uncertain_state"
    assert len(boundary["launch"]) == 1
    assert "private" not in str(result.result.to_dict())


def test_existing_process_timeout_is_failed_not_unknown(boundary):
    boundary["responses"] = [snapshot(True)]
    with create_core() as core:
        result = run(core, request()).result
        assert result.status == TaskStatus.FAILED and result.error.code == "window_not_observed"
        assert run(core, request("catalog", tool="apps.catalog", arguments={})).status == TaskStatus.SUCCEEDED
    assert boundary["launch"] == []


@pytest.mark.parametrize("initial", [snapshot(None, None, False), OSError("private"), NotImplementedError()])
def test_bad_initial_observation_never_launches(boundary, initial):
    boundary["responses"] = [initial]
    with create_core() as core:
        assert run(core, request()).status == TaskStatus.FAILED
    assert boundary["launch"] == []


def test_launcher_resolution_failure_happens_before_side_effect(boundary, monkeypatch):
    def fail():
        raise OSError("private path")
    monkeypatch.setattr(windows_apps, "notepad_launcher", fail)
    with create_core() as core:
        result = run(core, request()).result
        assert result.status == TaskStatus.FAILED and result.error.code == "launcher_unavailable"
    assert not boundary["launch"] and "private" not in str(result.to_dict())


def test_launch_call_exception_is_not_permission_to_resend(boundary, monkeypatch):
    def launch(path):
        boundary["launch"].append(path)
        raise OSError("after possible native acceptance")
    monkeypatch.setattr(windows_apps, "start_notepad", launch)
    with create_core() as core:
        assert run(core, request()).status == TaskStatus.UNKNOWN
    assert len(boundary["launch"]) == 1


@pytest.mark.parametrize("when", ["before", "resolve", "after-launch", "waiting-existing"])
def test_open_cancellation_respects_whether_launch_was_requested(boundary, monkeypatch, when):
    context = ToolContext(task_id="cancel", request=request())
    if when == "before":
        context.cancel_event.set()
    elif when == "resolve":
        def resolve():
            context.cancel_event.set()
            return r"C:\Windows\System32\notepad.exe"
        monkeypatch.setattr(windows_apps, "notepad_launcher", resolve)
    elif when == "after-launch":
        def launch(path):
            boundary["launch"].append(path)
            context.cancel_event.set()
        monkeypatch.setattr(windows_apps, "start_notepad", launch)
    else:
        reads = []
        def observe(cancel):
            reads.append(True)
            if len(reads) > 1:
                cancel.set()
            return snapshot(True)
        monkeypatch.setattr(windows_apps, "observe_notepad", observe)
    result = apps.app_open(context.request.arguments, context)
    assert result.status == (TaskStatus.UNKNOWN if when == "after-launch" else TaskStatus.CANCELLED)
    assert len(boundary["launch"]) == (1 if when == "after-launch" else 0)


def test_concurrent_same_request_launches_only_once(boundary):
    boundary["responses"] = [snapshot(), snapshot(True, True)]
    req = request()
    with create_core() as core:
        with ThreadPoolExecutor(max_workers=4) as pool:
            tasks = list(pool.map(lambda unused: core.submit(req), range(12)))
        assert len({task.task_id for task in tasks}) == 1
        assert core.wait(tasks[0].task_id, 3).status == TaskStatus.SUCCEEDED
        assert core.submit(req).task_id == tasks[0].task_id
    assert len(boundary["launch"]) == 1


@pytest.mark.parametrize("arguments", [{}, {"app_id": "cmd"}, {"app_id": []},
                                      {"app_id": "notepad", "arguments": "/anything"}])
def test_bad_open_arguments_never_reach_native_calls(boundary, arguments):
    with create_core() as core:
        with pytest.raises(RegistryError):
            core.submit(request(arguments=arguments))
    assert not boundary["launch"] and not boundary["observe"]


@pytest.mark.parametrize("identity", [{"source": "telegram"}, {"principal": "other-user"}])
def test_open_policy_denial_prevents_native_calls(boundary, identity):
    with create_core() as core:
        assert run(core, request(**identity)).result.error.code == "permission_denied"
    assert not boundary["launch"] and not boundary["observe"]


@pytest.mark.parametrize("grants", [set(), {"apps.read"}, {"apps.launch"}, {"apps.read", "apps.launch"}])
def test_open_needs_both_observation_and_launch_permission(grants):
    tool = ToolSpec(name="apps.open", description="Open test", input_schema=apps.STATUS_SCHEMA,
                    handler=apps.app_open, required_capabilities=("apps.read", "apps.launch"))
    assert PolicyEngine(principal="local-user", capabilities=grants).authorize(request(), tool) is (len(grants) == 2)
