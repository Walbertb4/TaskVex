"""Concrete UI nonce decisions over existing scopes/policy; temporary/synthetic only."""
from dataclasses import replace
import json

import pytest

from app.bootstrap import create_core
from app.bridge.webview_bridge import NativeBridge
from app.core.contracts import TaskStatus
from app.policy.engine import PolicyEngine
from app.policy.task_scope import AccessRequirement, TaskScopes
from app.session.tool_registry import ToolRegistry
from app.storage.json_store import JsonStore
from app.storage.settings import validate_settings
from app.tasks.manager import TaskManager, TaskManagerError
from app.tasks.workflow import WorkflowStep
from test_policy import spec
from test_task_manager import done
from test_workflows import finish


REF = ('window', 'fixture-window', 'control')


def build(home, *, requirement=None, resources=(), ask=True):
    current = [requirement or AccessRequirement(resources=frozenset({REF}), physical_input=True, high_impact=True)]
    preference, calls = [ask], []
    scopes = TaskScopes()
    registry = ToolRegistry()
    registry.register(spec('system.status', ('system.read',), lambda a, c: (calls.append(a), done(c))[1]))
    resolve = lambda r: current[0]
    policy = PolicyEngine(principal='local-user', capabilities=frozenset({'system.read'}),
                          scopes=scopes, resolve_access=resolve)
    core = TaskManager(registry, task_scopes=scopes, access_requirement=resolve,
        input_preference=lambda: preference[0], journal_home=home / 'tasks',
        authorize=lambda r, s: replace(policy, ask_before_input=preference[0]).authorize(r, s))
    scope_id = scopes.begin(task_id='job', principal='local-user', resources=resources)
    core.submit_workflow('job', (WorkflowStep(step_id='one', tool='system.status', arguments={'text': 'Fixture content'}),),
                         authorization_id=scope_id, start_paused=True)
    store = JsonStore(home / 'settings.json')
    bridge = NativeBridge(core, store)
    bridge._ready = True
    return core, scopes, bridge, current, preference, calls


def prompt(core):
    revision = core.get_workflow('job')['revision']
    result = core.request_workflow_permission('job', 'one', expected_revision=revision)
    return result


def decide(bridge, identifier, approve=True):
    return bridge.event('task_permission_decision', {'id': identifier, 'approve': approve})


def test_scope_input_and_operation_are_separate_real_decisions_not_effect_completion(tmp_path):
    core, scopes, bridge, _, _, calls = build(tmp_path)
    with core:
        old_scope = core._workflows['job'].authorization_id
        assert old_scope is not None
        for kind in ('scope', 'input', 'operation'):
            pending = prompt(core)
            view = bridge.event('query_task_permissions')['data']
            assert view['pending'][0]['kind'] == kind
            assert old_scope not in json.dumps(view) and 'authorization_id' not in json.dumps(view)
            result = decide(bridge, pending['id'])
            assert result['accepted'] and result['outcome'] == 'approved' and not result['task_completed']
            assert decide(bridge, pending['id']) == result
            assert calls == [] and core.get_workflow('job')['status'] == 'waiting_for_user'
        assert not scopes.active(old_scope, 'local-user')
        assert prompt(core)['required'] is False
        # Only a trusted host fresh check, not the UI decision payload, starts work.
        core.resume_workflow('job', expected_revision=core.get_workflow('job')['revision'], reobserve=lambda: True)
        assert finish(core, 'job')['status'] == 'succeeded' and calls == [{'text': 'Fixture content'}]
    assert b'Fixture content' not in (tmp_path / 'tasks/tasks.sqlite3').read_bytes()


def test_reject_grants_nothing_and_cannot_be_replayed_as_approval(tmp_path):
    core, scopes, bridge, _, _, calls = build(tmp_path)
    with core:
        nonce = prompt(core)['id']
        result = decide(bridge, nonce, False)
        assert result['outcome'] == 'denied' and calls == []
        assert decide(bridge, nonce, True)['ok'] is False
        assert core.get_workflow('job')['status'] == 'waiting_for_user'
        assert prompt(core)['id'] != nonce


@pytest.mark.parametrize('change', ['stop', 'arguments', 'scope'])
def test_old_ui_decision_cannot_authorize_changed_or_stopped_work(tmp_path, change):
    core, scopes, bridge, _, _, calls = build(tmp_path, resources=[REF], ask=False)
    with core:
        nonce = prompt(core)['id']
        revision = core.get_workflow('job')['revision']
        if change == 'stop':
            core.cancel_workflow('job')
        elif change == 'arguments':
            core.update_workflow('job', (WorkflowStep(step_id='one', tool='system.status', arguments={'text': 'Changed'}),),
                                 expected_revision=revision)
        else:
            old = core._workflows['job'].authorization_id
            assert old is not None
            scopes.end(old)
            fresh = scopes.begin(task_id='job', principal='local-user', resources=[REF])
            core.replace_workflow_scope('job', expected_revision=revision, authorization_id=fresh)
        assert decide(bridge, nonce)['ok'] is False and calls == []
        assert core.permission_view()['decisions'][0]['outcome'] == 'invalidated'


def test_changed_trusted_requirement_invalidates_nonce_without_grant(tmp_path):
    core, _, bridge, current, _, calls = build(tmp_path, resources=[REF], ask=False)
    with core:
        nonce = prompt(core)['id']
        current[0] = AccessRequirement(resources=frozenset({('window', 'different', 'control')}), high_impact=True)
        assert decide(bridge, nonce)['code'] == 'stale_permission'
        assert core.permission_view()['pending'] == [] and calls == []


def test_pending_decision_blocks_resume_and_payload_cannot_supply_grants(tmp_path):
    core, _, bridge, _, _, calls = build(tmp_path)
    with core:
        nonce = prompt(core)['id']
        for data in ({'id': nonce, 'approve': True, 'resources': [['window', '*', 'control']]},
                     {'id': nonce, 'approve': 1}, {'id': 'unseen', 'approve': True}):
            assert bridge.event('task_permission_decision', data)['ok'] is False
        with pytest.raises(TaskManagerError) as error:
            core.resume_workflow('job', expected_revision=0, reobserve=lambda: True)
        assert error.value.code == 'permission_pending' and calls == []


def test_input_preference_does_not_bypass_resource_or_high_impact_consent(tmp_path):
    core, _, bridge, _, preference, calls = build(tmp_path, ask=False)
    with core:
        pending = prompt(core)
        assert core.permission_view()['pending'][0]['kind'] == 'scope'
        decide(bridge, pending['id'])
        pending = prompt(core)
        assert core.permission_view()['pending'][0]['kind'] == 'operation'
        decide(bridge, pending['id'])
        assert prompt(core)['required'] is False and calls == []
        preference[0] = True
        assert prompt(core)['required'] is True
        assert core.permission_view()['pending'][0]['kind'] == 'input'


def test_input_preference_persists_and_is_read_by_actual_bootstrap_policy(taskvex_home, monkeypatch):
    store = JsonStore(taskvex_home / 'settings.json')
    calls = []
    monkeypatch.setattr('app.bootstrap.system_status', lambda a, c, **kw: (calls.append(1), done(c))[1])
    resolve = lambda r: AccessRequirement(physical_input=True)
    with create_core(settings_store=store, resolve_access=resolve) as core:
        api = NativeBridge(core, store)
        api._ready = True
        assert api.event('save', {'askBeforeInput': False})['ok']
        scopes = core.task_scopes
        assert scopes is not None
        sid = scopes.begin(task_id='job', principal='local-user')
        core.submit_workflow('job', (WorkflowStep(step_id='read', tool='system.status'),), authorization_id=sid)
        assert finish(core, 'job')['status'] == 'succeeded'
    with create_core(settings_store=store, resolve_access=resolve) as core:
        saved = store.read()
        assert saved is not None and saved['askBeforeInput'] is False
        scopes = core.task_scopes
        assert scopes is not None
        sid = scopes.begin(task_id='second', principal='local-user')
        store.write({**saved, 'askBeforeInput': True})
        core.submit_workflow('second', (WorkflowStep(step_id='read', tool='system.status'),), authorization_id=sid)
        assert finish(core, 'second')['steps'][0]['error_code'] == 'permission_denied'
    assert calls == [1]


@pytest.mark.parametrize('value', ['false', 0, None])
def test_input_preference_rejects_non_boolean_settings(value):
    with pytest.raises(ValueError):
        validate_settings({'askBeforeInput': value})


def test_prompt_requires_safe_host_pause_and_explicit_trusted_resolver(tmp_path):
    core, _, _, _, _, _ = build(tmp_path)
    with core:
        core._access_requirement = None
        with pytest.raises(TaskManagerError) as error:
            prompt(core)
        assert error.value.code == 'permission_unavailable'
        assert core.permission_view()['pending'] == []


def test_denied_input_cannot_be_bypassed_by_later_preference_change(tmp_path):
    core, _, bridge, _, preference, calls = build(tmp_path, resources=[REF],
        requirement=AccessRequirement(resources=frozenset({REF}), physical_input=True))
    with core:
        nonce = prompt(core)['id']
        decide(bridge, nonce, False)
        preference[0] = False
        with pytest.raises(TaskManagerError) as error:
            core.resume_workflow('job', expected_revision=0, reobserve=lambda: True)
        assert error.value.code == 'permission_denied' and calls == []
