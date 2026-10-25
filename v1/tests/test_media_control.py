"""Exercise media mutations through synthetic Windows sessions and real execution owners.

No real player is controlled. SDK transport, cancellation, journal replay and bridge
checks use temporary profiles; native acceptance is not physical-player acceptance.
"""
import asyncio
from threading import Event
from types import SimpleNamespace

import pytest

from app.bootstrap import create_core
from app.bridge.webview_bridge import NativeBridge
from app.core.contracts import ContractError, ToolContext, ToolRequest, ToolSpec
from app.policy.engine import PolicyEngine
from app.session.model_tools import ModelTools
from app.session.text_chat import TextChat
from app.session.gemini import DEFAULT_MODEL
from app.storage.json_store import JsonStore
from app.tools.local import media
from app.tools.local.media import _read_windows as native_reader
from test_gemini import transport, reply, call as rest_call
from test_live_probe import socket, frame
from test_live_tools import call as live_call


class Player:
    """A mutable GSMTC session; only its native method changes playback state."""
    def __init__(self):
        self.title = 'First track'
        self.state = 5
        self.calls = []
        self.accept = True
        self.change = True
        self.after = lambda: None
        self.controls = SimpleNamespace(**{'is_'+k+'_enabled':True for k in media.ACTIONS})

    async def try_get_media_properties_async(self):
        return SimpleNamespace(title=self.title,artist='Synthetic artist')

    def get_playback_info(self):
        return SimpleNamespace(playback_status=self.state,controls=self.controls)

    async def action(self, action):
        self.calls.append(action)
        if self.accept and self.change:
            if action in ('play','pause'): self.state = 4 if action == 'play' else 5
            else: self.title = action+' track'
        self.after()
        return self.accept

    async def try_play_async(self): return await self.action('play')
    async def try_pause_async(self): return await self.action('pause')
    async def try_skip_next_async(self): return await self.action('next')
    async def try_skip_previous_async(self): return await self.action('previous')


@pytest.fixture
def player(monkeypatch):
    current = SimpleNamespace(session=Player())
    async def manager(): return SimpleNamespace(get_current_session=lambda:current.session)
    monkeypatch.setattr(media,'_request_manager',manager)
    monkeypatch.setattr(media,'_read_windows',native_reader)
    return current


def context(action='play'):
    return ToolContext(task_id='synthetic',cancel_event=Event(),request=ToolRequest(
        request_id='request',source='desktop',principal='local-user',tool='media.control',arguments={'action':action}))


def command(meter, action='play', ctx=None):
    return meter.control({'action':action,'target_id':meter.snapshot()['target_id']},ctx or context(action))


@pytest.mark.parametrize('action',media.ACTIONS)
def test_each_native_action_requires_observed_result(player,action):
    native = player.session
    if action == 'pause': native.state = 4
    meter = media.Media()
    before = meter.snapshot()
    result = command(meter,action)
    assert result.verified and result.status.value == 'succeeded'
    assert result.evidence['accepted'] and result.evidence['read_back']
    assert native.calls == [action]
    assert result.data['target_id'] != before['target_id']
    assert '_session' not in result.data and 'source_app' not in result.data


@pytest.mark.parametrize('action',media.ACTIONS)
def test_manager_local_identity_is_reused_across_polls_and_core_thread(player,monkeypatch,action):
    """Each activation exposes different wrappers for the same underlying player."""
    from concurrent.futures import ThreadPoolExecutor
    activations = []
    async def manager():
        views = {}
        def current():
            if player.session is None:return None
            if player.session not in views:
                view = Player()
                view.__dict__ = player.session.__dict__
                views[player.session] = view
            return views[player.session]
        result = SimpleNamespace(get_current_session=current)
        activations.append(result)
        return result
    monkeypatch.setattr(media,'_request_manager',manager)
    if action=='pause':player.session.state = 4
    now = [0]
    meter = media.Media(clock=lambda:now[0])
    with ThreadPoolExecutor(max_workers=1) as thread:
        first = thread.submit(meter.snapshot).result(2)
        now[0] = 3
        fresh = thread.submit(meter.snapshot).result(2)
        assert fresh['target_id'] == first['target_id'] and len(activations)==1
        assert '_manager' not in fresh and '_session' not in fresh
        with create_core(media=meter) as core:
            task = core.submit(ToolRequest(request_id='manager-bound-control',source='desktop',
                principal='local-user',tool='media.control',arguments={'action':action,'target_id':fresh['target_id']}))
            result = core.wait(task.task_id,2).result
            assert result is not None and result.verified
            assert player.session.calls == [action] and len(activations)==1
        now[0] = 6
        assert thread.submit(meter.snapshot).result(2)['target_id'] == result.data['target_id']
        assert len(activations)==1


def test_missing_session_retains_manager_but_transport_loss_invalidates_it(player,monkeypatch):
    activations = []
    async def manager():
        item = SimpleNamespace(get_current_session=lambda:player.session)
        activations.append(item)
        return item
    monkeypatch.setattr(media,'_request_manager',manager)
    now = [0]
    meter = media.Media(clock=lambda:now[0])
    first = meter.snapshot()
    native = player.session
    player.session = None
    now[0] = 3
    assert meter.snapshot()['status']=='no_session' and len(activations)==1
    player.session = native
    now[0] = 6
    assert meter.snapshot()['target_id'] != first['target_id'] and len(activations)==1
    def unavailable():raise OSError('Synthetic disconnected manager')
    activations[0].get_current_session = unavailable
    now[0] = 9
    assert meter.snapshot()['status']=='unavailable'
    now[0] = 12
    assert meter.snapshot()['status']=='available' and len(activations)==2
    assert not native.calls


def test_identity_cache_and_pre_dispatch_stale_guards(player):
    meter = media.Media()
    first = meter.snapshot()
    assert meter.snapshot() == first
    player.session.title = 'Changed without polling'
    result = command(meter)
    assert result.error is not None and result.error.code == 'media_target_changed' and not player.session.calls
    assert result.data['target_id'] != first['target_id']
    assert meter.control({'action':'play','target_id':first['target_id']},context()).status.value == 'failed'
    old = player.session
    player.session = Player()
    changed = command(meter)
    assert changed.error is not None and changed.error.code == 'media_target_changed'
    assert not old.calls and not player.session.calls


def test_cancel_before_dispatch_and_late_cancel_preserves_real_success(player):
    meter = media.Media()
    ctx = context()
    ctx.cancel_event.set()
    assert command(meter,ctx=ctx).status.value == 'cancelled'
    assert not player.session.calls
    ctx.cancel_event.clear()
    player.session.after = ctx.cancel_event.set
    assert command(meter,ctx=ctx).verified
    assert player.session.calls == ['play']


@pytest.mark.parametrize('reason',['unsupported','rejected','already'])
def test_supported_flags_rejection_and_idempotent_desired_state(player,reason):
    native = player.session
    if reason == 'unsupported': native.controls.is_play_enabled = False
    if reason == 'rejected': native.accept = False
    if reason == 'already': native.state = 4
    result = command(media.Media())
    assert result.verified == (reason == 'already')
    assert native.calls == (['play'] if reason == 'rejected' else [])


@pytest.mark.parametrize('reason',['accepted_only','session_changed','exception','timeout'])
def test_post_dispatch_uncertainty_latches_without_retry(player,reason):
    native = player.session
    ctx = context('next')
    native.change = False
    def after():
        if reason == 'exception': raise RuntimeError('private transport error')
        if reason == 'timeout': raise TimeoutError()
        if reason == 'session_changed': player.session = Player()
        ctx.cancel_event.set()
    native.after = after
    meter = media.Media()
    target = meter.snapshot()['target_id']
    result = command(meter,'next',ctx)
    assert result.status.value == 'unknown' and not result.verified
    assert result.data['control_unknown'] is True
    assert 'private' not in str(result.to_dict())
    ctx.cancel_event.clear()
    assert meter.control({'action':'next','target_id':target},ctx).status.value == 'unknown'
    assert native.calls == ['next']


def test_failure_before_dispatch_is_known(player,monkeypatch):
    meter = media.Media()
    meter.snapshot()
    async def unavailable(manager): raise OSError('private session failure')
    monkeypatch.setattr(media,'_current',unavailable)
    result = command(meter)
    assert result.status.value == 'failed' and not result.data['control_unknown']
    assert not player.session.calls


def test_model_fresh_read_gate_replay_and_policy(player):
    meter = media.Media()
    with create_core(media=meter) as core:
        tools = ModelTools(core,principal='local-user',session_id='media-control',
                           allowed_tools=('media.status','media.control'))
        tools.begin_turn('Play')
        action = {'id':'mutate','name':'media.control','arguments':{'action':'play','target_id':meter.snapshot()['target_id']}}
        with pytest.raises(ContractError,match='Read media.status'): tools.submit(action)
        read = {'id':'read','name':'media.status','arguments':{}}
        task = tools.submit(read)
        data = tools.result(task.task_id,timeout=2)['result']['data']
        action['arguments']['target_id'] = data['target_id']
        changed = tools.submit(action)
        assert tools.result(changed.task_id,timeout=2)['result']['verified']
        tools.begin_turn('Play again')
        assert tools.submit(action).task_id == changed.task_id
        tools.result(task.task_id,timeout=2)  # Old read result cannot authorize a new mutation.
        with pytest.raises(ContractError): tools.submit({**action,'id':'new-mutate'})
        assert player.session.calls == ['play']
    request = ToolRequest(request_id='r',source='desktop',principal='local-user',tool='media.control')
    spec = ToolSpec(name='media.control',description='Control',input_schema=media.CONTROL_SCHEMA,
                    handler=meter.control,required_capabilities=('media.control',))
    assert not PolicyEngine(principal='local-user',capabilities=frozenset({'media.read'})).authorize(request,spec)


@pytest.mark.parametrize('mode',['rest','live'])
def test_both_model_transports_use_same_media_owner(player,mode,transport,socket):
    meter = media.Media()
    target = meter.snapshot()['target_id']
    args = {'action':'play','target_id':target}
    with create_core(media=meter) as core:
        chat = TextChat(core)
        try:
            if mode == 'rest':
                transport.responses = [reply([rest_call('media.status',{},'read')]),
                    reply([rest_call('media.control',args,'play')]),reply([{'text':'Verified'}])]
                report = chat.run('Play current media',DEFAULT_MODEL,notes_ready=False)
            else:
                socket.frames = [{'setupComplete':{}},live_call('media.status',{},'read'),
                    live_call('media.control',args,'play'),frame('Verified',complete=True)]
                report = chat.run_live('Play current media','future-live',notes_ready=False)
            assert report['ok'],report
            assert report['tool_results'][-1]['result']['evidence']['read_back']
            assert player.session.calls == ['play']
        finally:
            assert chat.close()


def test_bridge_poll_shared_commands_validation_and_persistent_replay(player,taskvex_home):
    meter = media.Media()
    payload = {'version':1,'request_id':'native-media-play','arguments':{'action':'play',
                'target_id':meter.snapshot()['target_id']}}
    with create_core(media=meter) as core:
        bridge = NativeBridge(core,JsonStore(taskvex_home/'settings.json'),media=meter)
        try:
            assert not bridge.event('media_command',payload)['ok']
            bridge._ready = True
            count = len(core._entries)
            assert bridge.event('query_media')['ok'] and len(core._entries) == count
            invalid = bridge.event('media_command',{**payload,'version':True})
            assert invalid['completed'] and not invalid['ok'] and invalid['request_id'] == payload['request_id']
            result = bridge.event('media_command',payload)
            assert result['ok'] and result['completed'] and result['verified']
            assert bridge.event('media_command',payload) == result
        finally: assert bridge._chat.close()
    with create_core(media=media.Media()) as core:
        task = core.submit(ToolRequest(request_id=payload['request_id'],source='desktop',principal='local-user',
                                      tool='media.control',arguments=payload['arguments']))
        result = core.wait(task.task_id,2).result
        assert result is not None and result.verified
    assert player.session.calls == ['play']


def test_unknown_media_result_survives_restart_and_blocks_new_controls(player,taskvex_home):
    native = player.session
    native.change = False
    meter = media.Media()
    def uncertain(*args): return {'status':'unknown','code':'media_result_unknown'}
    meter._controller = uncertain
    with create_core(media=meter) as core:
        bridge = NativeBridge(core,JsonStore(taskvex_home/'settings.json'),media=meter)
        try:
            bridge._ready = True
            payload = {'version':1,'request_id':'unknown-media','arguments':{'action':'next','target_id':meter.snapshot()['target_id']}}
            result = bridge.event('media_command',payload)
            assert result['unknown'] and core.uncertain
            assert bridge.event('query_media')['data']['control_unknown']
        finally: assert bridge._chat.close()
    with create_core(media=media.Media()) as core:
        bridge = NativeBridge(core,JsonStore(taskvex_home/'settings.json'),media=media.Media())
        try:
            bridge._ready = True
            assert core.uncertain and bridge.event('query_media')['data']['control_unknown']
            assert bridge.event('media_command',{**payload,'request_id':'new'})['unknown']
        finally: assert bridge._chat.close()
    assert not native.calls
