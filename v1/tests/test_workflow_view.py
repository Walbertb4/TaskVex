"""Native logical progress/Stop uses actual owned jobs, never provider or user data."""
import json
from threading import Event

import pytest

from app.bridge.webview_bridge import NativeBridge
from app.storage.json_store import JsonStore
from app.tasks.manager import TaskManager
from test_task_manager import allow, done, registry_with
from test_workflows import finish, step


def bridge_for(core, home):
    bridge = NativeBridge(core, JsonStore(home / 'settings.json'))
    bridge._ready = True
    return bridge


def test_progress_is_read_only_private_and_filters_actual_host_ownership(tmp_path):
    calls = []
    with TaskManager(registry_with(lambda a, c: (calls.append(a), done(c))[1]), authorize=allow) as core:
        bridge = bridge_for(core, tmp_path)
        assert bridge.event('query_workflows')['data'] == []
        for identifier, principal, source in [('visible', 'local-user', 'desktop'),
                                               ('foreign', 'someone-else', 'desktop'),
                                               ('other-channel', 'local-user', 'telegram')]:
            core.submit_workflow(identifier, (step('first', text='Private contents'),),
                                 principal=principal, source=source, start_paused=True)
        view = bridge.event('query_workflows')['data']
        assert [q['workflow_id'] for q in view] == ['visible']
        assert 'Private contents' not in json.dumps(view) and 'arguments' not in json.dumps(view)
        view[0]['steps'].clear()
        assert len(bridge.event('query_workflows')['data'][0]['steps']) == 1
        assert not calls
        for identifier in ('foreign', 'other-channel'):
            response = bridge.event('cancel_workflow', {'workflow_id': identifier, 'revision': 0})
            assert response['accepted'] is False
            assert core.get_workflow(identifier)['stop_requested'] is False


@pytest.mark.parametrize('payload', [None, {}, {'workflow_id': 'job'},
    {'workflow_id': 'job', 'revision': True}, {'workflow_id': 'job', 'revision': None},
    {'workflow_id': 'job', 'revision': -1}, {'workflow_id': 'job', 'revision': '0'},
    {'workflow_id': '', 'revision': 0}, {'workflow_id': [], 'revision': 0},
    {'workflow_id': 'job', 'revision': 0, 'principal': 'someone-else'}])
def test_native_stop_rejects_forged_or_incomplete_payload(tmp_path, payload):
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as core:
        core.submit_workflow('job', (step('one'),), start_paused=True)
        response = bridge_for(core, tmp_path).event('cancel_workflow', payload)
        assert response['ok'] is False and response['accepted'] is False
        assert not core.get_workflow('job')['stop_requested']


def test_stale_revision_cannot_stop_corrected_or_new_task(tmp_path):
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as core:
        core.submit_workflow('old', (), sealed=False)
        bridge = bridge_for(core, tmp_path)
        before = bridge.event('query_workflows')['data'][0]
        core.update_workflow('old', (step('new-intent'),), expected_revision=before['revision'])
        core.submit_workflow('next', (), sealed=False)
        response = bridge.event('cancel_workflow', {'workflow_id': 'old', 'revision': before['revision']})
        assert response['code'] == 'workflow_changed' and response['accepted'] is False
        assert not core.get_workflow('old')['stop_requested'] and not core.get_workflow('next')['stop_requested']


def test_stop_acceptance_not_completion_preserves_late_real_effect_and_next_job(tmp_path):
    entered, release = Event(), Event()
    calls = []
    def handler(arguments, context):
        calls.append(arguments['name'])
        if arguments['name'] == 'effect':
            entered.set()
            assert release.wait(10)
        return done(context)
    with TaskManager(registry_with(handler), authorize=allow) as core:
        core.submit_workflow('old', (step('one', name='effect'), step('two', name='must-not-run')))
        assert entered.wait(5)
        try:
            core.submit_workflow('new', (step('one', name='new'),))
            bridge = bridge_for(core, tmp_path)
            old = core.get_workflow('old')
            response = bridge.event('cancel_workflow', {'workflow_id': 'old', 'revision': old['revision']})
            assert response['accepted'] is True
            assert response['data']['stop_requested'] and not response['data']['completed']
            assert not core.get_workflow('new')['stop_requested']
        finally:
            release.set()
        actual = finish(core, 'old')
        assert actual['steps'][0]['status'] == 'succeeded' and actual['steps'][1]['status'] == 'cancelled'
        assert finish(core, 'new')['status'] == 'succeeded'
        # Duplicate old Stop cannot cancel new work or rewrite a completed effect.
        assert bridge.event('cancel_workflow', {'workflow_id': 'old', 'revision': old['revision']})['ok']
        assert calls == ['effect', 'new']


def test_not_ready_and_invalid_queries_never_issue_work(tmp_path):
    with TaskManager(registry_with(lambda a, c: done(c)), authorize=allow) as core:
        bridge = bridge_for(core, tmp_path)
        bridge._ready = False
        assert bridge.event('query_workflows') == {'ok': True, 'ready': False, 'data': []}
        assert bridge.event('cancel_workflow', {'workflow_id': 'job', 'revision': 0})['accepted'] is False
        bridge._ready = True
        assert not bridge.event('query_workflows', {})['ok']
