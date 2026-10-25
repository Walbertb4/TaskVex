"""Try explicit user memory requests with real core and synthetic SDK.

No data is used outside of temporary settings.json. Language comprehension quality of the model
not, verifies co-execution, register, target, cancellation/replay and UI conflict limit.
"""
import json

import pytest

from app.bootstrap import create_core
from app.core.contracts import ContractError, ToolRequest, ToolContext
from app.session.gemini import DEFAULT_MODEL
from app.session.model_tools import ModelTools
from app.session.text_chat import TextChat
from app.storage.json_store import JsonStore, StoreError
from app.tools.local.personal_memory import PersonalMemory, memory_base, memory_snapshot
from test_gemini import transport, reply, call
from test_live_probe import frame
from test_live_resume import wire
from test_live_tools import call as live_call
from test_native_bridge import bridge, ready


def read_saved(store: JsonStore) -> dict:
    """If there is no document known to be written in the test, generate an open assertion error."""
    data = store.read()
    assert data is not None
    return data


def setup_store(home, text="School: Alpha"):
    """Only install known documents that are explicitly enabled in the temporary profile."""
    store = JsonStore(home / 'settings.json')
    store.write({'theme': '#a78bfa', 'prof': {'pMemory': True, 'pMem': text, 'pLang': 'en'}})
    return store


def model_tools(core):
    return ModelTools(core, principal='local-user', session_id='memory-test',
                      allowed_tools=('memory.read', 'memory.patch'))


def invoke(tools, name, arguments=None, call_id='read'):
    task = tools.submit({'id': call_id, 'name': name, 'arguments': arguments or {}})
    return tools.result(task.task_id, timeout=3)


@pytest.mark.parametrize('action,text,replacement,expected', [
    ('append', 'Job: Developer', None, 'School: Alpha\nJob: Developer'),
    ('replace', 'Alpha', 'Beta', 'School: Beta'),
    ('forget', 'School: Alpha', None, ''), ('clear', None, None, ''),
])
def test_verified_mutation_and_replay_preserve_other_preferences(taskvex_home, action, text, replacement, expected):
    store = setup_store(taskvex_home)
    with create_core(settings_store=store) as core:
        tools = model_tools(core)
        snapshot = invoke(tools, 'memory.read')['result']['data']['snapshot']
        args = {'action': action, 'expected_snapshot': snapshot}
        if text is not None:
            args['text'] = text
        if replacement is not None:
            args['replacement'] = replacement
        result = invoke(tools, 'memory.patch', args, 'write')
        assert result['status'] == 'succeeded' and result['result']['verified']
        before = store.path.read_bytes()
        tools.begin_turn('Replay')
        assert invoke(tools, 'memory.patch', args, 'write') == result
        assert store.path.read_bytes() == before
    saved = read_saved(store)
    assert saved['prof']['pMem'] == expected and saved['prof']['pMemory'] is True
    assert saved['theme'] == '#a78bfa' and saved['prof']['pLang'] == 'en'


def test_fresh_read_and_unchanged_disk_required(taskvex_home):
    store = setup_store(taskvex_home)
    with create_core(settings_store=store) as core:
        tools = model_tools(core)
        args = {'action': 'clear', 'expected_snapshot': memory_snapshot(read_saved(store)['prof'])}
        with pytest.raises(ContractError):
            invoke(tools, 'memory.patch', args, 'without-read')
        invoke(tools, 'memory.read')
        tools.begin_turn('New turn')
        with pytest.raises(ContractError):
            invoke(tools, 'memory.patch', args, 'old-turn')
        invoke(tools, 'memory.read', call_id='fresh-read')
        candidate = read_saved(store)
        candidate['prof']['pMem'] = 'New UI memory'
        store.write(candidate)
        result = invoke(tools, 'memory.patch', args, 'stale')
        assert result['result']['error']['code'] == 'memory_changed'
        assert read_saved(store) == candidate


@pytest.mark.parametrize('text', ['missing', 'Alpha'])
def test_ambiguous_or_missing_target_preserves_document(taskvex_home, text):
    store = setup_store(taskvex_home, 'Alpha\nAlpha')
    with create_core(settings_store=store) as core:
        tools = model_tools(core)
        snapshot = invoke(tools, 'memory.read')['result']['data']['snapshot']
        before = store.path.read_bytes()
        result = invoke(tools, 'memory.patch', {'action': 'forget', 'text': text, 'expected_snapshot': snapshot}, 'write')
        assert result['result']['error']['code'] == 'memory_target_required'
        assert store.path.read_bytes() == before


def test_disabled_memory_is_not_disclosed_or_enabled(taskvex_home):
    store = setup_store(taskvex_home)
    data = read_saved(store)
    data['prof']['pMemory'] = False
    store.write(data)
    with create_core(settings_store=store) as core:
        result = invoke(model_tools(core), 'memory.read')
        assert result['result']['error']['code'] == 'memory_disabled'
        assert 'Alpha' not in json.dumps(result)
    assert read_saved(store) == data


def test_rest_memory_read_then_patch_uses_real_settings(transport, taskvex_home):
    store = setup_store(taskvex_home)
    snapshot = memory_snapshot(read_saved(store)['prof'])
    transport.responses = [reply([call('memory.read', {}, 'read')]),
        reply([call('memory.patch', {'action': 'replace', 'text': 'Alpha', 'replacement': 'Beta', 'expected_snapshot': snapshot}, 'patch')]),
        reply([{'text': 'Corrected'}])]
    with create_core(settings_store=store) as core:
        chat = TextChat(core)
        try:
            result = chat.run('Correct my school to Beta', DEFAULT_MODEL, profile=read_saved(store)['prof'])
            assert result['ok'] and len(result['tool_results']) == 2
            assert all(item['result']['verified'] for item in result['tool_results'])
        finally:
            assert chat.close()
    assert read_saved(store)['prof']['pMem'] == 'School: Beta'


def test_live_patch_next_turn_forget_resets_old_context(wire, taskvex_home):
    store = setup_store(taskvex_home)
    snapshot = memory_snapshot(read_saved(store)['prof'])
    wire.plans = [{'turns': [[live_call('memory.read', {}, 'read'),
        live_call('memory.patch', {'action': 'clear', 'expected_snapshot': snapshot}, 'clear'), frame('Forgotten', complete=True)]]},
        {'turns': [[frame('Hello', complete=True)]]}]
    with create_core(settings_store=store) as core:
        chat = TextChat(core)
        try:
            result = chat.run_live('Forget everything about me', 'future-live', profile=read_saved(store)['prof'])
            assert result['ok'] and len(result['tool_results']) == 2
            assert read_saved(store)['prof']['pMem'] == ''
            assert chat.run_live('Hello', 'future-live', profile=read_saved(store)['prof'])['ok']
            assert wire.opened == 2
            assert not [m for _, m in wire.sent if 'client_content' in m]
        finally:
            assert chat.close()


def test_ui_stale_profile_cannot_overwrite_model_memory(bridge):
    assert ready(bridge)['ok']
    original = {'pMemory': True, 'pMem': 'School: Alpha'}
    assert bridge.event('save', {'prof': original})['saved']
    tools = model_tools(bridge._core)
    snapshot = invoke(tools, 'memory.read')['result']['data']['snapshot']
    result = invoke(tools, 'memory.patch', {'action': 'append', 'text': 'Job: Developer', 'expected_snapshot': snapshot}, 'patch')
    assert result['result']['verified']
    assert bridge._memory_reply({'tool_results': [result]})['memory_profile']['pMem'].endswith('Developer')
    before = bridge._store.path.read_bytes()
    rejected = bridge.event('save', {'prof': original, 'memoryBase': memory_base(original)})
    assert rejected['code'] == 'memory_changed'
    assert bridge._store.path.read_bytes() == before
    current = read_saved(bridge._store)['prof']
    assert bridge.event('save', {'prof': {**current, 'pMem': 'Manual correction'}, 'memoryBase': memory_base(current)})['saved']


def test_write_failure_does_not_report_success(taskvex_home, monkeypatch):
    store = setup_store(taskvex_home)
    with create_core(settings_store=store) as core:
        tools = model_tools(core)
        snapshot = invoke(tools, 'memory.read')['result']['data']['snapshot']
        def fail(data):
            raise StoreError('write_failed', 'Synthetic error')
        monkeypatch.setattr(store, 'write', fail)
        result = invoke(tools, 'memory.patch', {'action': 'clear', 'expected_snapshot': snapshot}, 'write')
        assert result['status'] == 'failed' and not result['result']['verified']
        assert read_saved(store)['prof']['pMem'] == 'School: Alpha'


def test_cancel_before_write_and_late_cancel_preserve_real_outcome(taskvex_home, monkeypatch):
    store = setup_store(taskvex_home)
    memory = PersonalMemory(store)
    arguments = {'action': 'clear', 'expected_snapshot': memory_snapshot(read_saved(store)['prof'])}
    request = ToolRequest(request_id='cancel-memory', source='desktop', principal='local-user', tool='memory.patch', arguments=arguments)
    context = ToolContext(task_id='memory-task', request=request)
    context.cancel_event.set()
    assert memory.patch(arguments, context).status.value == 'cancelled'
    assert read_saved(store)['prof']['pMem'] == 'School: Alpha'
    context.cancel_event.clear()
    original = store.write
    def late_cancel(data):
        original(data)
        context.cancel_event.set()
    monkeypatch.setattr(store, 'write', late_cancel)
    result = memory.patch(arguments, context)
    assert result.status.value == 'succeeded' and result.verified
    assert read_saved(store)['prof']['pMem'] == ''


def test_readback_failure_is_unknown(taskvex_home, monkeypatch):
    store = setup_store(taskvex_home)
    memory = PersonalMemory(store)
    arguments = {'action':'clear', 'expected_snapshot':memory_snapshot(read_saved(store)['prof'])}
    context = ToolContext(task_id='memory-task', request=ToolRequest(request_id='memory-readback', source='desktop', principal='local-user', tool='memory.patch', arguments=arguments))
    original = store.write
    def write_without_verifiable_read(data):
        original(data)
        def fail():
            raise StoreError('read_failed', 'Synthetic readback failure')
        monkeypatch.setattr(store, 'read', fail)
    monkeypatch.setattr(store, 'write', write_without_verifiable_read)
    result = memory.patch(arguments, context)
    assert result.status.value == 'unknown' and not result.verified


def test_ui_and_model_share_transaction_without_losing_theme(bridge):
    assert ready(bridge)['ok']
    assert bridge.event('save', {'prof':{'pMemory':True, 'pMem':'School: Alpha'}})['saved']
    tools = model_tools(bridge._core)
    snapshot = invoke(tools, 'memory.read')['result']['data']['snapshot']
    with bridge._store.lock:
        task = tools.submit({'id':'concurrent-patch', 'name':'memory.patch', 'arguments':{
            'action':'append', 'text':'Job: Developer', 'expected_snapshot':snapshot}})
        assert bridge.event('save', {'theme':'#112233'})['saved']
    result = tools.result(task.task_id, timeout=3)
    assert result['result']['verified']
    data = read_saved(bridge._store)
    assert data['theme'] == '#112233' and data['prof']['pMem'].endswith('Developer')
