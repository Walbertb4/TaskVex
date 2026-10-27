"""Host-scoped policy checks through the real registry/worker, no OS or provider."""

from dataclasses import replace
from hashlib import sha256
import json
from threading import Event

import pytest

from app.core.contracts import ContractError, TaskStatus, ToolRequest, request_fingerprint
from app.policy.engine import PolicyEngine
from app.policy.task_scope import AccessRequirement, TaskScopes
from app.session.model_tools import ModelTools
from app.session.tool_registry import ToolRegistry
from app.tasks.manager import TaskManager
from test_policy import spec
from test_task_manager import done


REF = ('file', 'selected-file-ref', 'read')


def req(scope_id=None, *, request_id='operation', target=REF[1], **kwargs):
    return ToolRequest(request_id=request_id, source='desktop', principal='local-user',
                       tool='notes.list', arguments={'target': target}, authorization_id=scope_id, **kwargs)


def policy(scopes, *, high_impact=False, physical_input=False, ask_before_input=True):
    def resolve(request):
        if request.tool == 'system.status':
            return None
        return AccessRequirement(resources=frozenset({('file', request.arguments['target'], 'read')}),
                                 high_impact=high_impact, physical_input=physical_input)
    return PolicyEngine(principal='local-user', capabilities=frozenset({'notes.read', 'system.read'}),
                        scopes=scopes, resolve_access=resolve, ask_before_input=ask_before_input)


@pytest.mark.parametrize('kind', ['app', 'file', 'folder', 'window', 'browser', 'person'])
def test_resources_are_exact_and_do_not_expand_by_prefix(kind):
    scopes = TaskScopes()
    resource = (kind, 'chosen', 'capture' if kind == 'window' else 'read')
    scope_id = scopes.begin(task_id='logical-task', principal='local-user', resources=[resource])
    request = req(scope_id)
    assert scopes.allows(request, AccessRequirement(resources=frozenset({resource})), ask_before_input=True)
    for other in [(kind, 'chosen-child', resource[2]), (kind, 'chosen', 'write')]:
        assert not scopes.allows(request, AccessRequirement(resources=frozenset({other})), ask_before_input=True)
    assert scopes.end(scope_id)
    assert not scopes.allows(request, AccessRequirement(), ask_before_input=False)
    with pytest.raises(ContractError):
        scopes.grant_input(scope_id)
    with pytest.raises(ContractError):
        scopes.approve(request)


@pytest.mark.parametrize('resources', ['*', [('file', '*', 'read')], [('file', 'id', '*')],
                                     [(['file'], 'id', 'read')], [('file', 'id')]])
def test_malformed_or_wildcard_grants_fail_at_host_boundary(resources):
    with pytest.raises(ContractError):
        TaskScopes().begin(task_id='task', principal='local-user', resources=resources)


def test_foreign_principal_source_and_unissued_scope_are_denied():
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='task', principal='local-user', resources=[REF])
    engine, tool = policy(scopes), spec()
    for request in [req(), req('invented'), replace(req(scope_id), principal='other'),
                    replace(req(scope_id), source='telegram')]:
        assert not engine.authorize(request, tool)
    assert engine.authorize(req(scope_id), tool)
    assert not PolicyEngine(principal='local-user', capabilities=frozenset({'notes.read'})).authorize(req(scope_id), tool)
    with pytest.raises(ContractError):
        scopes.begin(task_id='task', principal='other')


def test_input_handover_and_high_impact_approval_are_independent():
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='task', principal='local-user', resources=[REF])
    request, tool = req(scope_id), spec()
    engine = policy(scopes, high_impact=True, physical_input=True)
    assert not engine.authorize(request, tool)
    scopes.grant_input(scope_id)
    assert not engine.authorize(request, tool)
    scopes.approve(request)
    assert engine.authorize(request, tool)
    assert not engine.authorize(replace(request, request_id='different-operation'), tool)
    assert not engine.authorize(replace(request, arguments={'target': 'other'}), tool)
    other_id = scopes.begin(task_id='another-task', principal='local-user', resources=[REF])
    assert not engine.authorize(replace(request, authorization_id=other_id), tool)
    # Even a real input preference does not disable high-impact or resource checks.
    no_question = policy(scopes, high_impact=True, physical_input=True, ask_before_input=False)
    assert not no_question.authorize(req(other_id), tool)
    scopes.approve(req(other_id))
    assert no_question.authorize(req(other_id), tool)


def test_approval_never_expands_resources_and_resolver_failure_is_closed():
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='task', principal='local-user')
    scopes.approve(req(scope_id))
    assert not policy(scopes, high_impact=True).authorize(req(scope_id), spec())
    def broken(request):
        raise ValueError('synthetic resolver failure')
    engine = PolicyEngine(principal='local-user', capabilities=frozenset({'notes.read'}),
                          scopes=scopes, resolve_access=broken)
    assert not engine.authorize(req(scope_id), spec())


def test_queued_task_checks_revocation_before_handler_dispatch():
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='task', principal='local-user', resources=[REF])
    entered, release = Event(), Event()
    calls = []
    def blocker(arguments, context):
        entered.set()
        assert release.wait(5)
        return done(context)
    registry = ToolRegistry()
    registry.register(spec('system.status', ('system.read',), blocker))
    registry.register(spec(handler=lambda a, c: (calls.append(c.task_id), done(c))[1]))
    with TaskManager(registry, authorize=policy(scopes).authorize) as core:
        first = core.submit(ToolRequest(request_id='block', source='desktop', principal='local-user', tool='system.status'))
        assert entered.wait(5)
        try:
            queued = core.submit(req(scope_id))
            scopes.end(scope_id)
        finally:
            release.set()
        core.wait(first.task_id, 5)
        result = core.wait(queued.task_id, 5)
        assert result.status == TaskStatus.FAILED and not calls
        assert result.result is not None and result.result.error is not None
        assert result.result.error.code == 'permission_denied'


def test_model_cannot_supply_its_own_authorization_but_host_scope_reaches_worker():
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='task', principal='local-user', resources=[REF])
    registry = ToolRegistry()
    registry.register(spec(handler=lambda a, c: done(c, {'host_scope': c.request.authorization_id})))
    with TaskManager(registry, authorize=policy(scopes).authorize) as core:
        tools = ModelTools(core, principal='local-user', session_id='session',
                           allowed_tools=('notes.list',), authorization_id=scope_id)
        call = {'id': 'call', 'name': 'notes.list', 'arguments': {'target': REF[1]}}
        with pytest.raises(ContractError):
            tools.submit({**call, 'authorization_id': scope_id})
        task = tools.submit(call)
        result = tools.result(task.task_id, timeout=5)
        assert result['status'] == 'succeeded' and result['result']['data']['host_scope'] == scope_id
        denied = tools.submit({**call, 'id': 'other', 'arguments': {'target': 'not-granted'}})
        assert tools.result(denied.task_id, timeout=5)['status'] == 'failed'


def test_receipts_do_not_restore_authority_after_restart(tmp_path):
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='task', principal='local-user', resources=[REF])
    calls = []
    registry = ToolRegistry()
    registry.register(spec(handler=lambda a, c: (calls.append(c.task_id), done(c))[1]))
    with TaskManager(registry, authorize=policy(scopes).authorize, journal_home=tmp_path) as core:
        original = core.wait(core.submit(req(scope_id)).task_id, 5)
    with TaskManager(registry, authorize=policy(TaskScopes()).authorize, journal_home=tmp_path) as core:
        history = core.submit(req(scope_id))
        assert history.task_id == original.task_id
        assert history.result is not None
        assert history.result.evidence['content_available'] is False
        denied = core.wait(core.submit(req(scope_id, request_id='new-effect')).task_id, 5)
        assert denied.status == TaskStatus.FAILED
    assert len(calls) == 1


def test_unscoped_request_keeps_previous_serialization_and_digest():
    request = req()
    original = {'request_id': request.request_id, 'source': request.source, 'principal': request.principal,
                'tool': request.tool, 'arguments': request.arguments}
    canonical = json.dumps(original, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    assert request.to_dict() == original
    assert request_fingerprint(request) == 'sha256-v1:' + sha256(canonical.encode()).hexdigest()
    assert request_fingerprint(req('scope-a')) != request_fingerprint(req('scope-b'))
