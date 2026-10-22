"""Model çağrı sınırını gerçek registry/policy/worker ile doğrula.

Canlı model ve ağ yoktur; sağlayıcının ayrıştırdığı çağrı doğrudan verilir.
Not testleri yalnız conftest'in geçici TASKVEX_HOME dizinine yazar. Bekleme,
iptal ve belirsizlik testlerinde Event kapıları rastgele sleep'in yerini alır.
"""

from threading import Event

import pytest

from app.bootstrap import create_core
from app.core.contracts import ContractError, TaskStatus, ToolResult, ToolSpec
from app.session.model_tools import ModelTools
from app.session.tool_registry import ToolRegistry
from app.tasks.manager import TaskManager, TaskManagerError


def session(core, session_id="session-1", principal="local-user"):
    """Host tarafından seçilen kimlikler ve yalnız iki araçla bir oturum kur."""
    return ModelTools(core, principal=principal, session_id=session_id,
                      allowed_tools=("notes.add", "notes.list"))


def note_call(**changes):
    """Sağlayıcıdan beklenen sade çağrı; kimlik/yetki alanları içermez."""
    return {"id": "call-1", "name": "notes.add", "arguments": {"text": "Test note"}, **changes}


def test_real_note_roundtrip_and_reconnect_replay():
    """Yeni adaptör aynı core/oturumla bağlansa da not ikinci kez eklenmesin."""
    with create_core() as core:
        tools = session(core)
        task = tools.submit(note_call())
        response = tools.result(task.task_id, timeout=2)
        assert response["id"] == "call-1" and response["name"] == "notes.add"
        assert response["status"] == "succeeded" and response["result"]["verified"]
        assert response["result"]["data"]["note"]["text"] == "Test note"
        assert "principal" not in response and "arguments" not in response

        reconnect = session(core)
        assert reconnect.submit(note_call()).task_id == task.task_id
        read = reconnect.submit({"id": "read", "name": "notes.list", "arguments": {}})
        assert len(reconnect.result(read.task_id, timeout=2)["result"]["data"]["notes"]) == 1
        with pytest.raises(TaskManagerError, match="different content"):
            reconnect.submit(note_call(arguments={"text": "Changed"}))


def test_session_id_scopes_provider_call_ids():
    with create_core() as core:
        first = session(core, "a").submit(note_call())
        second = session(core, "b").submit(note_call())
        assert first.task_id != second.task_id
        assert core.wait(second.task_id, 2).status == TaskStatus.SUCCEEDED


@pytest.mark.parametrize("call", [
    None, [], {}, {"id": "x", "name": "notes.list"},
    note_call(id=None), note_call(id=" "), note_call(name=[]),
    note_call(name="apps.open"), note_call(name="shell.run"),
    note_call(principal="admin"), note_call(source="desktop"),
    note_call(arguments=None), note_call(arguments={"text": 7}),
    note_call(arguments={"text": "ok", "path": "SECRET"}),
    note_call(arguments={"text": float("nan")}),
])
def test_invalid_call_does_not_write(call, taskvex_home):
    with create_core() as core:
        with pytest.raises(ContractError) as error:
            session(core).submit(call)
        assert "SECRET" not in str(error.value)
    assert not (taskvex_home / "notes.json").exists()


def test_host_identity_does_not_bypass_policy(taskvex_home):
    with create_core() as core:
        tools = session(core, principal="other-user")
        task = tools.submit(note_call())
        result = tools.result(task.task_id, timeout=2)
        assert result["status"] == "failed"
        assert result["result"]["error"]["code"] == "permission_denied"
    assert not (taskvex_home / "notes.json").exists()


def test_catalog_has_only_exposed_data_and_returns_independent_schemas():
    with create_core() as core:
        tools = session(core)
        catalog = tools.declarations()
        assert {item["name"] for item in catalog} == {"notes.add", "notes.list"}
        assert all(set(item) == {"name", "description", "parameters"} for item in catalog)
        next(item for item in catalog if item["name"] == "notes.add")["parameters"].clear()
        assert next(item for item in tools.declarations() if item["name"] == "notes.add")["parameters"]
        with pytest.raises(ContractError):
            ModelTools(core, principal="local-user", session_id="a", allowed_tools=("unknown.tool",))
        with pytest.raises(ContractError):
            session(core, session_id="")


def test_other_session_cannot_read_or_cancel_a_task():
    with create_core() as core:
        task = session(core).submit(note_call())
        other = session(core, "other")
        with pytest.raises(ContractError):
            other.result(task.task_id)
        with pytest.raises(ContractError):
            other.cancel(task.task_id)
        assert core.wait(task.task_id, 2).status == TaskStatus.SUCCEEDED


@pytest.mark.parametrize("status", [TaskStatus.CANCELLED, TaskStatus.UNKNOWN])
def test_pending_cancellation_and_unknown_keep_actual_state(status):
    """Zaman aşımı başarı/başarısızlık uydurmasın; iptal kabulü bitiş sayılmasın."""
    started, release = Event(), Event()
    registry = ToolRegistry()

    def handler(arguments, context):
        started.set()
        assert release.wait(3)
        return ToolResult(task_id=context.task_id, status=status)

    registry.register(ToolSpec(name="test.run", description="Controlled boundary",
                              input_schema={"type": "object"}, handler=handler))
    with TaskManager(registry, authorize=lambda request, tool: True) as core:
        tools = ModelTools(core, principal="test", session_id="test", allowed_tools=("test.run",))
        call = {"id": "one", "name": "test.run", "arguments": {}}
        task = tools.submit(call)
        try:
            assert started.wait(2)
            pending = tools.result(task.task_id)
            assert pending["status"] == "running" and pending["result"] is None
            if status == TaskStatus.CANCELLED:
                assert tools.cancel(task.task_id).status == TaskStatus.CANCEL_REQUESTED
                assert tools.result(task.task_id)["status"] == "cancel_requested"
        finally:
            release.set()
        response = tools.result(task.task_id, timeout=2)
        assert response["status"] == status.value
        assert response["result"]["verified"] is False
        assert tools.submit(call).task_id == task.task_id
        if status == TaskStatus.UNKNOWN:
            with pytest.raises(TaskManagerError, match="unknown outcome"):
                tools.submit({**call, "id": "two"})
