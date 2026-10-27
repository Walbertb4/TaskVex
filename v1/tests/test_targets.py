"""Shared target freshness/geometry checks; synthetic adapters, never desktop input."""

from dataclasses import replace
from threading import Event
from time import monotonic

import pytest

from app.automation.targets import FrameGeometry, TargetError, TargetReferences, TargetSnapshot, can_fallback
from app.core.contracts import ContractError, TaskStatus, ToolError, ToolRequest, ToolResult
from app.policy.engine import PolicyEngine
from app.policy.task_scope import TaskScopes
from app.session.model_tools import ModelTools
from app.session.tool_registry import ToolRegistry
from app.tasks.manager import TaskManager
from test_policy import spec


def snapshot(**kwargs):
    return TargetSnapshot(**{'application_id': 'synthetic-app', 'instance_id': 'pid-42-created-100',
        'window_id': 'hwnd-17-lifetime-3', 'generation': 'content-1', 'foreground': True, **kwargs})


def request(scope_id, *, request_id='read'):
    return ToolRequest(request_id=request_id, source='desktop', principal='local-user',
                       tool='notes.list', authorization_id=scope_id)


def setup(value=None, *, capacity=256):
    value = value or snapshot()
    current = [value]
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='logical-task', principal='local-user',
                            resources=[('browser' if value.tab_id else 'window', value.resource_id, 'read')])
    targets = TargetReferences(scopes, capacity=capacity)
    ref_id = targets.issue(scope_id, 'local-user', value, lambda cancel: current[0])
    return scopes, targets, scope_id, ref_id, current


@pytest.mark.parametrize('field,value', [('application_id', 'other-app'), ('instance_id', 'pid-42-created-200'),
    ('window_id', 'hwnd-17-lifetime-4'), ('generation', 'content-2'), ('foreground', False),
    ('element_id', 'different-runtime-element')])
def test_identity_version_and_focus_change_make_old_reference_stale(field, value):
    _, targets, scope_id, ref_id, current = setup()
    assert targets.resolve(ref_id, request(scope_id), Event()) == current[0]
    current[0] = replace(current[0], **{field: value})
    with pytest.raises(TargetError) as error:
        targets.resolve(ref_id, request(scope_id), Event())
    assert error.value.code == 'target_stale'
    assert not can_fallback(error.value, dispatched=False)


@pytest.mark.parametrize('change', [{'tab_id': 'tab-2'}, {'document_id': 'document-2'}])
def test_navigation_and_tab_switch_invalidate_dom_targets(change):
    _, targets, scope_id, ref_id, current = setup(snapshot(tab_id='tab-1', document_id='document-1'))
    current[0] = replace(current[0], **change)
    with pytest.raises(TargetError, match='target_stale'):
        targets.resolve(ref_id, request(scope_id), Event())


def test_new_document_observation_discards_old_element_refs_before_reader_runs():
    original = snapshot(tab_id='tab-1', document_id='document-1', element_id='old-button')
    _, targets, scope_id, old_ref, _ = setup(original)
    newer = replace(original, document_id='document-2', element_id='other-button')
    targets.issue(scope_id, 'local-user', newer, lambda c: newer)
    with pytest.raises(TargetError, match='target_stale'):
        targets.resolve(old_ref, request(scope_id), Event())


def geometry(**kwargs):
    return FrameGeometry(**{'frame_id': 'frame-1', 'screen_x': -1920, 'screen_y': 0,
        'captured_at': monotonic(), 'coordinate_space': 'physical_desktop',
        'screen_width': 1920, 'screen_height': 1080, 'frame_width': 640,
        'frame_height': 360, 'dpi': 144, **kwargs})


def test_frame_points_use_physical_bounds_without_double_dpi_scaling():
    _, targets, scope_id, ref_id, _ = setup(snapshot(geometry=geometry()))
    assert targets.resolve_point(ref_id, request(scope_id), Event(), 0, 0, max_frame_age=10) == (-1920, 0)
    assert targets.resolve_point(ref_id, request(scope_id), Event(), 320, 180, max_frame_age=10) == (-960, 540)
    assert targets.resolve_point(ref_id, request(scope_id), Event(), 639, 359, max_frame_age=10) == (-3, 1077)
    for x, y in [(-1, 0), (640, 0), (0, 360), (0.5, 0), (True, 0)]:
        with pytest.raises(ContractError):
            targets.resolve_point(ref_id, request(scope_id), Event(), x, y, max_frame_age=10)


@pytest.mark.parametrize('change', [{'dpi': 192}, {'screen_x': 0}, {'screen_width': 1280},
                                  {'frame_width': 1280}, {'frame_id': 'frame-2'}])
def test_changed_capture_geometry_or_frame_prevents_old_coordinate_use(change):
    _, targets, scope_id, ref_id, current = setup(snapshot(geometry=geometry()))
    old_geometry = current[0].geometry
    assert isinstance(old_geometry, FrameGeometry)
    current[0] = replace(current[0], geometry=replace(old_geometry, **change))
    with pytest.raises(TargetError, match='target_stale'):
        targets.resolve_point(ref_id, request(scope_id), Event(), 10, 10, max_frame_age=10)


@pytest.mark.parametrize('changes', [{'instance_id': ''}, {'generation': None}, {'foreground': 1},
                                   {'tab_id': 'tab-without-document'}, {'geometry': 'not-geometry'}])
def test_missing_identity_or_unproven_metadata_is_not_accepted(changes):
    with pytest.raises(ContractError):
        snapshot(**changes)


@pytest.mark.parametrize('changes', [{'dpi': True}, {'screen_width': 0}, {'frame_width': -1},
    {'coordinate_space': 'logical_pixels'}, {'captured_at': float('nan')}])
def test_invalid_or_logical_geometry_is_not_relabelled_as_physical(changes):
    with pytest.raises(ContractError):
        geometry(**changes)


@pytest.mark.parametrize('captured_at', [90.0, 101.0])
def test_expired_or_future_frame_time_is_stale_with_explicit_host_budget(monkeypatch, captured_at):
    monkeypatch.setattr('app.automation.targets.monotonic', lambda: 100.0)
    _, targets, scope_id, ref_id, _ = setup(snapshot(geometry=geometry(captured_at=captured_at)))
    with pytest.raises(TargetError, match='target_stale'):
        targets.resolve_point(ref_id, request(scope_id), Event(), 0, 0, max_frame_age=1)


@pytest.mark.parametrize('value,code', [(snapshot(foreground=None), 'target_unsupported'),
    (snapshot(foreground=False), 'target_stale'), (snapshot(), 'target_unsupported')])
def test_no_invented_focus_or_geometry_for_physical_input(value, code):
    _, targets, scope_id, ref_id, _ = setup(value)
    with pytest.raises(TargetError, match=code):
        targets.resolve_point(ref_id, request(scope_id), Event(), 0, 0, max_frame_age=10)


@pytest.mark.parametrize('code', ['target_no_match', 'target_unsupported', 'target_permission_denied',
                                 'target_stale', 'target_unavailable'])
def test_resolution_statuses_are_preserved_and_fallback_requires_known_pre_dispatch(code):
    scopes = TaskScopes()
    scope_id = scopes.begin(task_id='task', principal='local-user')
    targets = TargetReferences(scopes)
    def reader(cancel):
        raise TargetError(code)
    ref_id = targets.issue(scope_id, 'local-user', snapshot(), reader)
    with pytest.raises(TargetError) as error:
        targets.resolve(ref_id, request(scope_id), Event())
    assert error.value.code == code
    assert can_fallback(error.value, dispatched=False) == (code in {'target_no_match', 'target_unsupported'})
    assert not can_fallback(error.value, dispatched=True)
    assert not can_fallback(error.value, dispatched=None)


@pytest.mark.parametrize('result', [None, {'window_id': 'guessed'}])
def test_incomplete_observation_is_unavailable_not_a_definite_no_match(result):
    scopes, targets, scope_id, _, _ = setup()
    ref_id = targets.issue(scope_id, 'local-user', snapshot(), lambda cancel: result)
    with pytest.raises(TargetError, match='target_unavailable') as error:
        targets.resolve(ref_id, request(scope_id), Event())
    assert not can_fallback(error.value, dispatched=False)


def test_reader_errors_do_not_leak_content_or_allow_fallback():
    _, targets, scope_id, _, _ = setup()
    def reader(cancel):
        raise OSError('synthetic private path/message')
    ref_id = targets.issue(scope_id, 'local-user', snapshot(), reader)
    with pytest.raises(TargetError, match='target_unavailable') as error:
        targets.resolve(ref_id, request(scope_id), Event())
    assert 'private' not in str(error.value)


def test_cancellation_scope_end_and_reference_replacement_during_read_are_rechecked():
    for mode in ('cancel', 'end', 'replace'):
        scopes, targets, scope_id, _, _ = setup()
        cancel = Event()
        def reader(event):
            if mode == 'cancel':
                event.set()
            elif mode == 'end':
                scopes.end(scope_id)
            else:
                targets.issue(scope_id, 'local-user', snapshot(), lambda c: snapshot())
            return snapshot()
        ref_id = targets.issue(scope_id, 'local-user', snapshot(), reader)
        expected = {'cancel': 'target_cancelled', 'end': 'target_permission_denied', 'replace': 'target_stale'}[mode]
        with pytest.raises(TargetError, match=expected):
            targets.resolve(ref_id, request(scope_id), cancel)


def test_scope_and_principal_cannot_borrow_references():
    scopes, targets, scope_id, ref_id, _ = setup()
    other = scopes.begin(task_id='other-task', principal='local-user')
    for req in [request(other), replace(request(scope_id), principal='other-user'),
                replace(request(scope_id), source='telegram')]:
        with pytest.raises(TargetError, match='target_permission_denied'):
            targets.resolve(ref_id, req, Event())
    scopes.end(scope_id)
    with pytest.raises(TargetError, match='target_permission_denied'):
        targets.access(ref_id, request(scope_id), action='read')


def test_capacity_is_live_observations_not_lifetime_and_never_evicts_active_targets():
    scopes, targets, scope_id, ref_id, _ = setup(capacity=1)
    with pytest.raises(TargetError, match='target_capacity'):
        targets.issue(scope_id, 'local-user', snapshot(window_id='different-window'), lambda c: snapshot())
    assert targets.resolve(ref_id, request(scope_id), Event()) == snapshot()
    for _ in range(300):
        targets.release(ref_id, request(scope_id))
        ref_id = targets.issue(scope_id, 'local-user', snapshot(), lambda c: snapshot())
    scopes.end(scope_id)
    other = scopes.begin(task_id='new-task', principal='local-user')
    targets.issue(other, 'local-user', snapshot(), lambda c: snapshot())
    assert len(targets._references) == 1
    scopes.end(other)
    targets.release_scope(other)
    assert not targets._references


def test_target_issue_does_not_grant_control_and_revalidation_precedes_effect():
    scopes, targets, scope_id, ref_id, current = setup()
    effects = []
    def handler(arguments, context):
        try:
            value = targets.resolve(arguments['target_id'], context.request, context.cancel_event)
        except TargetError as error:
            return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                              error=ToolError(code=error.code, message='Synthetic target not ready'))
        effects.append(value.generation)
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                          data={'generation': value.generation})
    registry = ToolRegistry()
    registry.register(spec(handler=handler))
    policy = PolicyEngine(principal='local-user', capabilities=frozenset({'notes.read'}), scopes=scopes,
        resolve_access=lambda req: targets.access(req.arguments['target_id'], req, action='read'))
    with TaskManager(registry, authorize=policy.authorize) as core:
        tools = ModelTools(core, principal='local-user', session_id='synthetic-session',
                           allowed_tools=('notes.list',), authorization_id=scope_id)
        call = {'id': 'read', 'name': 'notes.list', 'arguments': {'target_id': ref_id}}
        task = tools.submit(call)
        assert tools.result(task.task_id, timeout=3)['status'] == 'succeeded'
        current[0] = replace(current[0], generation='changed-by-user')
        failed = tools.submit({**call, 'id': 'after-change'})
        result = tools.result(failed.task_id, timeout=3)
        assert result['result']['error']['code'] == 'target_stale'
        assert effects == ['content-1'] and not core.uncertain
    control = targets.access(ref_id, request(scope_id), action='control')
    assert not scopes.allows(request(scope_id), control, ask_before_input=False)
