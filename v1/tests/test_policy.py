"""Policy kararlarını ve gerçek TaskManager izin noktasını yan etkisiz doğrular.

Buradaki notes/system handler'ları yalnız test fonksiyonlarıdır. Not dosyası,
donanım, UI veya hesap kullanılmaz; reddedilen iş handler'a hiç ulaşmamalıdır.
"""

from dataclasses import FrozenInstanceError, replace

import pytest

from app.core.contracts import ContractError, TaskStatus, ToolRequest, ToolResult, ToolSpec
from app.policy.engine import PolicyEngine
from app.session.tool_registry import ToolRegistry
from app.tasks.manager import TaskManager


def spec(name="notes.list", capabilities=("notes.read",), handler=lambda a, c: None):
    """Sadece izin testine gereken geçerli araç bildirimini oluştur."""
    return ToolSpec(name=name, description="Policy test aracı",
                    input_schema={"type": "object"}, handler=handler,
                    required_capabilities=capabilities)


def request(tool="notes.list", **changes):
    """Güvenilir masaüstü isteğini kopyalayarak olumsuz sınır durumlarını kur."""
    return replace(ToolRequest(request_id="p1", source="desktop", principal="local-user",
                               tool=tool), **changes)


@pytest.mark.parametrize("name,capability", [
    ("assistant.request_sleep_mode", "assistant.control"),
    ("notes.add", "notes.write"), ("notes.list", "notes.read"),
    ("notes.select", "notes.read"), ("notes.delete_many", "notes.write"),
    ("notes.update", "notes.write"), ("notes.delete", "notes.write"),
    ("notes.initialize", "notes.write"), ("notes.replace", "notes.write"),
    ("apps.catalog", "apps.read"),
    ("apps.status", "apps.read"),
    ("system.status", "system.read"),
])
def test_known_tools_require_explicit_grant(name, capability):
    tool, req = spec(name, (capability,)), request(name)
    assert PolicyEngine(principal="local-user").authorize(req, tool) is False
    policy = PolicyEngine(principal="local-user", capabilities=frozenset({capability}))
    assert policy.authorize(req, tool) is True


@pytest.mark.parametrize("changes", [
    {"principal": "other-user"}, {"principal": "LOCAL-USER"},
    {"source": "telegram"}, {"source": "discord"}, {"source": "model"},
    {"source": "Desktop"}, {"tool": "notes.add"},
])
def test_identity_source_and_tool_mismatch_denied(changes):
    policy = PolicyEngine(principal="local-user", capabilities=frozenset({"notes.read"}))
    assert policy.authorize(request(**changes), spec()) is False


@pytest.mark.parametrize("name,capabilities", [
    ("files.delete", ()), ("apps.open", ("notes.read",)),
    ("notes.list", ()), ("notes.list", ("notes.write",)),
    ("notes.list", ("notes.read", "files.delete")),
])
def test_plugin_cannot_approve_itself_or_change_required_capabilities(name, capabilities):
    policy = PolicyEngine(principal="local-user",
                          capabilities=frozenset({"notes.read", "notes.write", "system.read"}))
    assert policy.authorize(request(name), spec(name, capabilities)) is False


def test_write_permission_does_not_grant_read_permission():
    policy = PolicyEngine(principal="local-user", capabilities=frozenset({"notes.write"}))
    assert policy.authorize(request(), spec()) is False


@pytest.mark.parametrize("capabilities", [None, "notes.read", [None], ["*"], ["files.delete"]])
def test_invalid_grants_fail_at_configuration(capabilities):
    with pytest.raises(ContractError):
        PolicyEngine(principal="local-user", capabilities=capabilities)


@pytest.mark.parametrize("principal", [None, 0, "", "  "])
def test_invalid_principal_fails_at_configuration(principal):
    with pytest.raises(ContractError):
        PolicyEngine(principal=principal)


def test_configuration_cannot_be_changed_through_original_set():
    grants = {"notes.read"}
    policy = PolicyEngine(principal="local-user", capabilities=grants)
    grants.add("notes.write")
    assert policy.capabilities == frozenset({"notes.read"})
    with pytest.raises(FrozenInstanceError):
        policy.principal = "other-user"


@pytest.mark.parametrize("req,tool", [(None, spec()), (request(), None)])
def test_invalid_callback_objects_are_denied(req, tool):
    assert PolicyEngine(principal="local-user").authorize(req, tool) is False


def test_task_manager_enforces_policy_before_handler_and_preserves_replays():
    """İzinli iş bir kez çalışır; reddedilen işten sonra kuyruk devam eder."""
    calls = []

    def handler(arguments, context):
        calls.append(context.request.request_id)
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED,
                          verified=True, evidence={"test_handler_finished": True})

    registry = ToolRegistry()
    registry.register(spec(handler=handler))
    registry.register(spec("notes.add", ("notes.write",), handler))
    policy = PolicyEngine(principal="local-user", capabilities=frozenset({"notes.read"}))
    with TaskManager(registry, authorize=policy.authorize) as manager:
        denied = manager.submit(request("notes.add", request_id="denied"))
        denied = manager.wait(denied.task_id, 2)
        assert denied.status == TaskStatus.FAILED
        assert denied.result.error.code == "permission_denied"
        permitted = manager.submit(request())
        assert manager.wait(permitted.task_id, 2).status == TaskStatus.SUCCEEDED
        assert manager.submit(request()).task_id == permitted.task_id
        foreign = manager.submit(request(request_id="foreign", principal="other-user"))
        assert manager.wait(foreign.task_id, 2).result.error.code == "permission_denied"
    assert calls == ["p1"]
