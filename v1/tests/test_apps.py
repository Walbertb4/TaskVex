"""Uygulama kataloğunu gerçek registry/policy/worker hattında doğrula.

Bu ilk adım uygulama başlatmaz. Testler geçici TASKVEX_HOME kullanır; katalog
okunurken not/ayar dosyası veya başka yan etki oluşmaması beklenir.
"""

import pytest

from app.bootstrap import create_core
from app.config import get_data_home
from app.core.contracts import TaskStatus, ToolContext, ToolRequest
from app.session.tool_registry import RegistryError
from app.tools.local.apps import APP_CATALOG, app_catalog, app_status


def request(**changes):
    """Güvenilir masaüstü girişinin oluşturacağı parametresiz isteği kur."""
    return ToolRequest(**{"request_id": "catalog", "source": "desktop",
                          "principal": "local-user", "tool": "apps.catalog", **changes})


def test_catalog_uses_core_and_does_not_claim_installed_or_running():
    with create_core() as core:
        task = core.submit(request())
        finished = core.wait(task.task_id, timeout=3)
        assert finished.status == TaskStatus.SUCCEEDED
        assert finished.result.verified
        assert finished.result.data == {"apps": [{"id": "notepad", "name": "Notepad"}]}
        assert finished.result.evidence == {"source": "builtin_allowlist"}
    assert not get_data_home().exists()


@pytest.mark.parametrize("identity", [{"source": "telegram"}, {"principal": "other-user"}])
def test_catalog_requires_trusted_local_identity(identity):
    with create_core() as core:
        finished = core.wait(core.submit(request(**identity)).task_id, timeout=3)
        assert finished.status == TaskStatus.FAILED
        assert finished.result.error.code == "permission_denied"
    assert not get_data_home().exists()


@pytest.mark.parametrize("arguments", [{"app_id": "notepad"}, {"path": "cmd.exe"},
                                      {"command": "anything"}])
def test_catalog_rejects_parameters_before_handler(arguments, monkeypatch):
    def forbidden(*args):
        raise AssertionError("Invalid request reached application handler")

    monkeypatch.setattr("app.bootstrap.app_catalog", forbidden)
    with create_core() as core:
        with pytest.raises(RegistryError) as caught:
            core.submit(request(arguments=arguments))
    assert caught.value.code == "invalid_arguments"
    assert not get_data_home().exists()


def test_catalog_is_immutable_and_results_are_independent():
    with pytest.raises(TypeError):
        APP_CATALOG["shell"] = "Unapproved"
    context = ToolContext(task_id="direct", request=request())
    first = app_catalog({}, context)
    first.data["apps"][0]["name"] = "Changed by caller"
    assert app_catalog({}, context).data["apps"][0]["name"] == "Notepad"


def test_catalog_honors_cancellation_and_direct_argument_validation():
    context = ToolContext(task_id="cancelled", request=request())
    assert app_catalog({"path": "anything"}, context).error.code == "invalid_arguments"
    context.cancel_event.set()
    assert app_catalog({}, context).status == TaskStatus.CANCELLED


@pytest.mark.parametrize("complete,running", [(True, True), (True, False), (False, None)])
def test_status_uses_common_core_and_partial_read_does_not_halt_worker(monkeypatch, complete, running):
    from app.tools.local import windows_apps
    data = {"app_id": "notepad", "complete": complete, "running": running,
            "visible_window": running, "processes": [], "windows": [], "observed_at": "test"}
    monkeypatch.setattr(windows_apps, "observe_notepad", lambda cancel: data)
    with create_core() as core:
        task = core.submit(request(tool="apps.status", arguments={"app_id": "notepad"}))
        result = core.wait(task.task_id, 3).result
        assert result.status == (TaskStatus.SUCCEEDED if complete else TaskStatus.FAILED)
        assert result.verified is complete and result.data == data
        if not complete:
            assert result.error.code == "observation_incomplete"
        assert core.wait(core.submit(request(request_id="after-read")).task_id, 3).status == TaskStatus.SUCCEEDED
    assert not get_data_home().exists()


@pytest.mark.parametrize("arguments", [{}, {"app_id": "cmd"}, {"app_id": []},
                                      {"app_id": "notepad", "path": "other.exe"}])
def test_status_invalid_target_never_reaches_observer(monkeypatch, arguments):
    def forbidden(cancel):
        raise AssertionError("Invalid target reached observer")
    monkeypatch.setattr("app.tools.local.windows_apps.observe_notepad", forbidden)
    assert app_status(arguments, ToolContext(task_id="invalid", request=request())).error.code == "invalid_arguments"
    with create_core() as core:
        with pytest.raises(RegistryError):
            core.submit(request(tool="apps.status", arguments=arguments))


@pytest.mark.parametrize("error,code", [(OSError("private path"), "observation_unavailable"),
                                      (NotImplementedError("private path"), "platform_unsupported")])
def test_status_unavailable_is_not_closed_or_private_error_leak(monkeypatch, error, code):
    def unavailable(cancel):
        raise error
    monkeypatch.setattr("app.tools.local.windows_apps.observe_notepad", unavailable)
    result = app_status({"app_id": "notepad"}, ToolContext(task_id="unavailable", request=request()))
    assert result.status == TaskStatus.FAILED and result.error.code == code
    assert result.data is None and "private" not in str(result.to_dict())


@pytest.mark.parametrize("when", ["before", "during", "after"])
def test_status_honors_cancellation(monkeypatch, when):
    context = ToolContext(task_id="cancel", request=request())
    def observe(cancel):
        if when == "before":
            raise AssertionError("Pre-cancelled observation should not run")
        if when == "during":
            raise InterruptedError()
        cancel.set()
        return {"complete": True}
    monkeypatch.setattr("app.tools.local.windows_apps.observe_notepad", observe)
    if when == "before":
        context.cancel_event.set()
    assert app_status({"app_id": "notepad"}, context).status == TaskStatus.CANCELLED


@pytest.mark.parametrize("identity", [{"source": "telegram"}, {"principal": "other-user"}])
def test_status_denied_identity_does_not_inspect_machine(monkeypatch, identity):
    def forbidden(cancel):
        raise AssertionError("Denied request reached Windows")
    monkeypatch.setattr("app.tools.local.windows_apps.observe_notepad", forbidden)
    with create_core() as core:
        task = core.submit(request(tool="apps.status", arguments={"app_id": "notepad"}, **identity))
        assert core.wait(task.task_id, 3).result.error.code == "permission_denied"
