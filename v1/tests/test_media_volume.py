"""Player-volume checks: synthetic Core Audio, real shared tools, no user audio writes."""
from contextlib import contextmanager
from threading import Event

import pytest

from app.tools.local import media, media_volume as volume
from app.bootstrap import create_core
from app.session.text_chat import TextChat
from app.session.gemini import DEFAULT_MODEL
from test_media_control import player
from test_gemini import transport, reply, call as rest_call
from test_live_probe import socket, frame
from test_live_tools import call as live_call


@pytest.fixture
def audio(monkeypatch):
    state = {'level':.65,'muted':False,'writes':[],'sessions':[], 'open':0,'closed':0,'error':None}
    state['sessions'] = [{'target':('endpoint','instance',123),'pointer':'simple-audio-volume'}]
    @contextmanager
    def sessions(source):
        assert source=='SyntheticPlayer.exe'
        state['open'] += 1
        try:yield state['sessions']
        finally:state['closed'] += 1
    def call(pointer,index,types=(),*args):
        assert pointer=='simple-audio-volume'
        if index==3:
            state['writes'].append(args[0])
            if state['error']=='write':raise OSError('Synthetic failed write')
            if state['error']!='no_change':state['level'] = args[0]
            if state['error']=='disappeared':state['sessions'] = []
        elif index==4:
            if state['error']=='readback' and state['writes']:raise OSError('Synthetic lost readback')
            args[0]._obj.value = state['level']
        elif index==6:args[0]._obj.value = state['muted']
        else:raise AssertionError('Unexpected interface: endpoint/master/mute must never be written')
        return 0
    monkeypatch.setattr(volume,'_sessions',sessions)
    monkeypatch.setattr(volume,'_call',call)
    return state


@pytest.mark.parametrize('source,name,app,match',[
    ('Browser','browser.exe',None,True),('browser.exe','BROWSER.EXE',None,True),
    ('Package!Player','host.exe','Package!Player',True),('Browser','other.exe',None,False),
    ('Browser','mybrowser.exe',None,False),('Browser',None,None,False)])
def test_exact_application_identity_only(source,name,app,match):
    assert volume._matches(source,name,app)==match


def test_active_session_selection_preserves_real_ambiguity():
    first,second,old = {'active':True,'id':1},{'active':True,'id':2},{'active':False,'id':3}
    assert volume._active_sessions([old,first])==[first]
    assert volume._active_sessions([old,first,second])==[first,second]
    assert volume._active_sessions([old])==[old]


def test_failed_native_activation_balances_com_cleanup(monkeypatch):
    import winrt.runtime as runtime
    calls = []
    monkeypatch.setattr(runtime,'init_apartment',lambda kind:calls.append('init'))
    monkeypatch.setattr(runtime,'uninit_apartment',lambda:calls.append('uninit'))
    assert volume.read('SyntheticPlayer.exe')=={'status':'unavailable'}
    assert calls==['init','uninit']


def test_read_privacy_zero_and_ambiguity(audio):
    sample = volume.read('SyntheticPlayer.exe')
    assert sample['percent']==65 and sample['muted'] is False
    audio['level'] = 0
    assert volume.read('SyntheticPlayer.exe')['percent']==0
    audio['sessions'] *= 2
    assert volume.read('SyntheticPlayer.exe')=={'status':'ambiguous'}
    audio['sessions'] = []
    assert volume.read('SyntheticPlayer.exe')=={'status':'unavailable'}
    assert volume.read(None)=={'status':'unavailable'}
    assert audio['open']==audio['closed'] and not audio['writes']


@pytest.mark.parametrize('percent',[0,35,100])
def test_absolute_application_write_and_readback_preserves_mute(audio,percent):
    audio['muted'] = True
    observed = volume.read('SyntheticPlayer.exe')
    result = volume.set_volume('SyntheticPlayer.exe',observed['_target'],percent,Event(),lambda:True)
    assert result['status']=='succeeded' and result['evidence']['read_back']
    assert result['evidence']['scope']=='application'
    assert audio['writes']==[percent/100] and audio['muted']
    assert audio['open']==audio['closed']


@pytest.mark.parametrize('reason',['stale','cancelled','changed','ambiguous','already'])
def test_pre_dispatch_checks_never_write(audio,reason):
    observed = volume.read('SyntheticPlayer.exe')
    cancel = Event()
    if reason=='cancelled':cancel.set()
    if reason=='stale':audio['sessions'][0]['target'] = ('endpoint','new-instance',123)
    if reason=='ambiguous':audio['sessions'] *= 2
    result = volume.set_volume('SyntheticPlayer.exe',observed['_target'],65 if reason=='already' else 30,
        cancel,lambda:reason!='changed')
    assert result['status']==('cancelled' if reason=='cancelled' else 'succeeded' if reason=='already' else 'failed')
    assert not audio['writes'] and audio['open']==audio['closed']


@pytest.mark.parametrize('reason',['write','readback','no_change','disappeared'])
def test_post_dispatch_failure_is_unknown_without_retry(audio,reason):
    observed = volume.read('SyntheticPlayer.exe')
    audio['error'] = reason
    result = volume.set_volume('SyntheticPlayer.exe',observed['_target'],30,Event(),lambda:True)
    assert result['status']=='unknown' and audio['writes']==[.3]
    assert audio['open']==audio['closed']


def test_stop_during_target_check_prevents_volume_dispatch(audio):
    target = volume.read('SyntheticPlayer.exe')['_target']
    cancel = Event()
    def still_current():cancel.set();return True
    result = volume.set_volume('SyntheticPlayer.exe',target,30,cancel,still_current)
    assert result['status']=='cancelled' and not audio['writes']


def test_verified_volume_change_survives_late_stop(audio,monkeypatch):
    target = volume.read('SyntheticPlayer.exe')['_target']
    cancel = Event()
    original = volume._call
    def call(pointer,index,types=(),*args):
        result = original(pointer,index,types,*args)
        if index==3:cancel.set()
        return result
    monkeypatch.setattr(volume,'_call',call)
    result = volume.set_volume('SyntheticPlayer.exe',target,30,cancel,lambda:True)
    assert result['status']=='succeeded' and audio['writes']==[.3]


def test_metadata_loss_after_verified_volume_write_is_not_known_failure(player,audio,monkeypatch):
    player.session.source_app_user_model_id = 'SyntheticPlayer.exe'
    meter = media.Media()
    target = meter.snapshot()['target_id']
    original = media._current
    async def current(manager):
        if audio['writes']:raise OSError('Synthetic lost GSMTC metadata after volume write')
        return await original(manager)
    monkeypatch.setattr(media,'_current',current)
    from test_media_control import context
    result = meter.control({'action':'set_volume','target_id':target,'percent':30},context())
    assert result.status.value=='unknown' and result.data['control_unknown']
    assert audio['writes']==[.3]


@pytest.mark.parametrize('bad',[None,True,-1,101,float('nan'),'30'])
def test_volume_arguments_are_validated_before_any_write(player,audio,bad):
    player.session.source_app_user_model_id = 'SyntheticPlayer.exe'
    meter = media.Media()
    from test_media_control import context
    result = meter.control({'action':'set_volume','target_id':meter.snapshot()['target_id'],'percent':bad},context())
    assert result.status.value=='failed' and not audio['writes']


@pytest.mark.parametrize('mode',['rest','live'])
def test_both_model_paths_and_replay_share_player_volume(mode,player,audio,transport,socket):
    player.session.source_app_user_model_id = 'SyntheticPlayer.exe'
    meter = media.Media()
    snapshot = meter.snapshot()
    assert snapshot['volume']=={'status':'available','scope':'application','percent':65,'muted':False}
    assert '_target' not in str(snapshot)
    args = {'action':'set_volume','target_id':snapshot['target_id'],'percent':25}
    with create_core(media=meter) as core:
        chat = TextChat(core)
        try:
            if mode=='rest':
                transport.responses = [reply([rest_call('media.status',{},'read')]),
                    reply([rest_call('media.control',args,'set')]),reply([rest_call('media.control',args,'set')]),
                    reply([{'text':'Verified application volume'}])]
                report = chat.run('Set player volume to 25%',DEFAULT_MODEL,notes_ready=False)
            else:
                socket.frames = [{'setupComplete':{}},live_call('media.status',{},'read'),
                    live_call('media.control',args,'set'),live_call('media.control',args,'set'),
                    frame('Verified application volume',complete=True)]
                report = chat.run_live('Set player volume to 25%','future-live',notes_ready=False)
            assert report['ok'],report
            final = report['tool_results'][-1]['result']
            assert final['verified'] and final['data']['volume']['percent']==25
            assert final['evidence']['scope']=='application' and audio['writes']==[.25]
        finally:assert chat.close()


def test_audio_target_change_rotates_media_token(player,audio):
    player.session.source_app_user_model_id = 'SyntheticPlayer.exe'
    now = [0]
    meter = media.Media(clock=lambda:now[0])
    before = meter.snapshot()
    audio['level'] = .4
    now[0] = 3
    assert meter.snapshot()['target_id']==before['target_id']
    audio['sessions'][0]['target'] = ('new-device','new-session',123)
    now[0] = 6
    assert meter.snapshot()['target_id']!=before['target_id']


def test_unknown_volume_uses_existing_persistent_core_lock(player,audio):
    player.session.source_app_user_model_id = 'SyntheticPlayer.exe'
    meter = media.Media()
    target = meter.snapshot()['target_id']
    audio['error'] = 'readback'
    from app.core.contracts import ToolRequest
    with create_core(media=meter) as core:
        task = core.submit(ToolRequest(request_id='volume-unknown',source='desktop',principal='local-user',
            tool='media.control',arguments={'action':'set_volume','target_id':target,'percent':20}))
        result = core.wait(task.task_id,2).result
        assert result is not None and result.status.value=='unknown' and core.uncertain
    with create_core(media=media.Media()) as core:assert core.uncertain
    assert audio['writes']==[.2]
