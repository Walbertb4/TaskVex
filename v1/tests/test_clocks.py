"""Sayaçların tek sahibi, gerçek araç hattı ve sentetik REST/Live kabulü.

Gerçek kullanıcı verisi/API/uyku kullanılmaz. Monoton saat denetimli ilerler;
UI snapshot poll'ü görev açmamalı, Stop tamamlanmış saati geri almamalıdır.
"""
from threading import Event
from uuid import uuid4

import pytest

from app.bootstrap import create_core
from app.config import get_data_home
from app.bridge.webview_bridge import NativeBridge
from app.core.contracts import ContractError, ToolContext, TaskStatus
from app.session.model_tools import ModelTools
from app.session.text_chat import TextChat
from app.storage.json_store import JsonStore
from app.tools.local import clocks as module
from test_local_tools import request, run
from test_native_bridge import FakeWindow, ready
from test_gemini import transport, reply, call
from test_live_probe import socket, frame
from test_live_tools import call as live_call


@pytest.fixture
def clock_time(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(module, 'monotonic', lambda: now[0])
    return now


def mutate(core, tool, args):
    result = run(core, request(tool, uuid4().hex, args)).result
    assert result is not None and result.verified
    return result.to_dict()['data']


def test_multiple_clocks_pause_resume_reset_and_wall_clock_independence(clock_time):
    clocks = module.Clocks()
    with create_core(clocks=clocks) as core:
        first = mutate(core, 'clocks.create', {'kind':'timer','start':True,'duration_seconds':10,'label':'Tea'})['clock']
        second = mutate(core, 'clocks.create', {'kind':'timer','start':True,'duration_seconds':20,'label':'Tea'})['clock']
        watch = mutate(core, 'clocks.create', {'kind':'stopwatch','start':True})['clock']
        assert len({first['id'],second['id'],watch['id']}) == 3
        clock_time[0] += 2.25
        paused = mutate(core,'clocks.control',{'id':first['id'],'action':'pause'})['clock']
        assert paused['remaining_seconds']==7.75 and paused['state']=='paused'
        clock_time[0] += 3
        assert clocks.snapshot()['clocks'][0]['remaining_seconds']==7.75
        assert clocks.snapshot()['clocks'][2]['elapsed_seconds']==5.25
        mutate(core,'clocks.control',{'id':first['id'],'action':'start'})
        clock_time[0] += 1
        # Tekrar Start, çalışan süreyi sıfırlamaz.
        started = mutate(core,'clocks.control',{'id':first['id'],'action':'start'})['clock']
        assert started['remaining_seconds']==6.75
        reset = mutate(core,'clocks.control',{'id':first['id'],'action':'reset'})['clock']
        assert reset['remaining_seconds']==10 and reset['state']=='ready'
        sw = mutate(core,'clocks.control',{'id':watch['id'],'action':'reset'})['clock']
        assert sw['elapsed_seconds']==0 and sw['state']=='ready'
        assert clocks.snapshot()['clocks'][1]['state']=='running'


def test_finished_timer_reset_restart_and_snapshot_are_independent(clock_time):
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        clock=mutate(core,'clocks.create',{'kind':'timer','start':True,'duration_seconds':1})['clock']
        clock_time[0]+=2
        snapshot=clocks.snapshot()
        assert snapshot['clocks'][0]['state']=='finished' and snapshot['clocks'][0]['remaining_seconds']==0
        revision=snapshot['revision'];snapshot['clocks'][0]['label']='tampered'
        assert clocks.snapshot()['clocks'][0]['label']!='tampered' and clocks.snapshot()['revision']==revision
        restarted=mutate(core,'clocks.control',{'id':clock['id'],'action':'start'})['clock']
        assert restarted['generation']==clock['generation']+1 and restarted['remaining_seconds']==1


@pytest.mark.parametrize('args',[
    {'kind':'timer','start':True}, {'kind':'timer','start':True,'duration_seconds':0},
    {'kind':'timer','start':True,'duration_seconds':-1}, {'kind':'timer','start':True,'duration_seconds':True},
    {'kind':'stopwatch','start':True,'duration_seconds':10}, {'kind':'stopwatch','start':'yes'},
    {'kind':'timer','start':True,'duration_seconds':31536001}, {'kind':'stopwatch','start':True,'label':' '}])
def test_invalid_creation_never_changes_collection(args):
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        with pytest.raises(ContractError):core.submit(request('clocks.create',arguments=args))
        assert clocks.snapshot()['clocks']==[]


def test_replay_is_same_clock_and_fresh_target_is_required_each_turn():
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        tools=ModelTools(core,principal='local-user',session_id='clocks',allowed_tools=('clocks.create','clocks.control','clocks.list'))
        tools.begin_turn('Create')
        call={'id':'new','name':'clocks.create','arguments':{'kind':'stopwatch','start':True}}
        task=tools.submit(call);outcome=tools.result(task.task_id,timeout=2);clock_id=outcome['result']['data']['clock']['id']
        assert tools.submit(call).task_id==task.task_id and len(clocks.snapshot()['clocks'])==1
        tools.begin_turn('Pause')
        control={'id':'pause','name':'clocks.control','arguments':{'id':clock_id,'action':'pause'}}
        with pytest.raises(ContractError):tools.submit(control)
        task=tools.submit({'id':'read','name':'clocks.list','arguments':{}});tools.result(task.task_id,timeout=2)
        tools.result(tools.submit(control).task_id,timeout=2)
        assert clocks.snapshot()['clocks'][0]['state']=='paused'
        tools.begin_turn('New turn');tools.result(task.task_id)
        with pytest.raises(ContractError):tools.submit({**control,'id':'new-pause'})


@pytest.mark.parametrize('cancel_before',[True,False])
def test_stop_before_create_and_late_stop_preserve_real_result(monkeypatch,cancel_before):
    clocks=module.Clocks();stopped=Event()
    if cancel_before:stopped.set()
    original=clocks._result
    def late_result(clock_id,context):
        stopped.set();return original(clock_id,context)
    monkeypatch.setattr(clocks,'_result',late_result)
    args={'kind':'stopwatch','start':True}
    result=clocks.create(args,ToolContext(task_id='clock-stop',request=request('clocks.create',arguments=args),cancel_event=stopped))
    assert result.status==(TaskStatus.CANCELLED if cancel_before else TaskStatus.SUCCEEDED)
    assert len(clocks.snapshot()['clocks'])==(0 if cancel_before else 1)


def test_native_ui_commands_and_poll_use_same_owner_without_poll_tasks(tmp_path,monkeypatch):
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        api=NativeBridge(core,JsonStore(tmp_path/'settings.json'),clocks=clocks)
        monkeypatch.setattr(api,'_window',FakeWindow());assert ready(api)['ok']
        result=api.event('clock_command',{'version':1,'request_id':'ui-create','tool':'clocks.create',
            'arguments':{'kind':'stopwatch','start':True}})
        assert result['verified'] and len(clocks.snapshot()['clocks'])==1
        assert api.event('clock_command',{'version':1,'request_id':'ui-create','tool':'clocks.create',
            'arguments':{'kind':'stopwatch','start':True}})['data']['clock']['id']==result['data']['clock']['id']
        monkeypatch.setattr(core,'submit',lambda *a: pytest.fail('View polling must not create tasks'))
        for _ in range(600):assert api.event('query_clocks')['verified']
        assert not api.event('query_clocks',{})['ok']


@pytest.mark.parametrize('mode',['rest','live'])
def test_model_creation_and_fresh_list_control(mode,transport,socket):
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        chat=TextChat(core)
        try:
            args={'kind':'stopwatch','start':True,'label':'Model watch'}
            if mode=='rest':transport.responses=[reply([call('clocks.create',args)]),reply([{'text':'Started'}])]
            else:socket.frames=[{'setupComplete':{}},live_call('clocks.create',args),frame('Started',complete=True)]
            first=chat.run('Start watch','gemini-3.8-flash') if mode=='rest' else chat.run_live('Start watch','future-live')
            assert first['ok'];clock_id=first['tool_results'][0]['result']['data']['clock']['id']
            args={'id':clock_id,'action':'pause'}
            if mode=='rest':transport.responses=[reply([call('clocks.list',{},'read')]),reply([call('clocks.control',args,'pause')]),reply([{'text':'Paused'}])]
            else:socket.frames=[live_call('clocks.list',{},'read'),live_call('clocks.control',args,'pause'),frame('Paused',complete=True)]
            second=chat.run('Pause watch','gemini-3.8-flash') if mode=='rest' else chat.run_live('Pause watch','future-live')
            assert second['ok'] and clocks.snapshot()['clocks'][0]['state']=='paused'
        finally:assert chat.close()


def test_unknown_ui_command_blocks_new_mutations_and_model_but_allows_view(tmp_path,monkeypatch):
    """Bekleme sonucu kaybolursa işlem tekrar edilmez; görünüm okumak kilidi aşmaz."""
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        api=NativeBridge(core,JsonStore(tmp_path/'settings.json'),clocks=clocks)
        monkeypatch.setattr(api,'_window',FakeWindow());assert ready(api)['ok']
        with monkeypatch.context() as patch:
            def timeout(*args,**kwargs):raise TimeoutError('Synthetic unknown wait')
            patch.setattr(core,'wait',timeout)
            result=api.event('clock_command',{'version':1,'request_id':'unknown-clock','tool':'clocks.create',
                'arguments':{'kind':'stopwatch','start':True}})
        assert result['unknown'] and not result['ok']
        assert api.event('query_clocks')['verified']
        assert not api.event('clock_command',{'version':1,'request_id':'new-clock','tool':'clocks.create',
            'arguments':{'kind':'stopwatch','start':True}})['ok']
        assert api.event('text',{'request_id':'new-model','text':'Hello'})['unknown']


def test_unknown_id_changes_no_clock(clock_time):
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        mutate(core,'clocks.create',{'kind':'stopwatch','start':True})
        before=clocks.snapshot()
        outcome=run(core,request('clocks.control',arguments={'id':'missing','action':'reset'}))
        assert outcome.status==TaskStatus.FAILED and clocks.snapshot()==before


def test_pause_crossing_timer_deadline_finishes_instead_of_sticking_paused(clock_time,monkeypatch):
    """Okuma ile pause arasındaki çok küçük deadline yarışı doğru sonuçlanır."""
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        clock=mutate(core,'clocks.create',{'kind':'timer','start':True,'duration_seconds':1})['clock']
        ticks=iter([100.999,101.0001,101.0002])
        monkeypatch.setattr(module,'monotonic',lambda:next(ticks))
        result=mutate(core,'clocks.control',{'id':clock['id'],'action':'pause'})['clock']
        assert result['state']=='finished' and result['elapsed_seconds']==1 and result['remaining_seconds']==0


def test_timer_set_preserves_id_and_other_clocks_while_stopwatch_rejects_duration():
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        timer=mutate(core,'clocks.create',{'kind':'timer','start':True,'duration_seconds':60})['clock']
        watch=mutate(core,'clocks.create',{'kind':'stopwatch','start':False})['clock']
        result=mutate(core,'clocks.control',{'id':timer['id'],'action':'reset','duration_seconds':120})['clock']
        assert result['id']==timer['id'] and result['remaining_seconds']==120 and result['state']=='ready'
        assert len(clocks.snapshot()['clocks'])==2
        for args in ({'id':watch['id'],'action':'reset','duration_seconds':10},
                     {'id':timer['id'],'action':'start','duration_seconds':10}):
            result=run(core,request('clocks.control',uuid4().hex,args))
            assert result.status==TaskStatus.FAILED
        assert clocks.snapshot()['clocks'][1]==watch


def test_timer_notification_verifies_actual_generation_and_never_retries(clock_time, monkeypatch):
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        api=NativeBridge(core, JsonStore(get_data_home()/'settings.json'), clocks=clocks)
        monkeypatch.setattr(api,'_window',FakeWindow())
        assert ready(api)['ok']
        api._live_model='synthetic-live';api._live_models={'synthetic-live':{}}
        created=mutate(core,'clocks.create',{'kind':'timer','start':True,'duration_seconds':1,'label':'Tea'})['clock']
        payload={'request_id':'notification-1','id':created['id'],'generation':created['generation']}
        calls=[]
        def notify(text, model, **options):
            calls.append((text,options))
            return {'ok':True,'completed':True,'text':'Your timer has finished.'}
        monkeypatch.setattr(api._chat,'run_live',notify)
        assert not api.event('clock_finished',payload)['ok'] and not calls
        clock_time[0]+=2
        assert api.event('clock_finished',payload)['ok']
        assert calls[0][1]['notification'] is True and 'Tea' in calls[0][0]
        assert not api.event('clock_finished',payload)['ok'] and len(calls)==1
        mutate(core,'clocks.control',{'id':created['id'],'action':'start'})
        assert not api.event('clock_finished',payload)['ok']
        clock_time[0]+=2
        next_payload={**payload,'request_id':'notification-2','generation':created['generation']+1}
        api._sleeping=True
        assert not api.event('clock_finished',next_payload)['ok']
        api._sleeping=False
        monkeypatch.setattr(api._chat,'run_live',lambda *a,**k:{'ok':False,'completed':True,'stopped':True})
        assert api.event('clock_finished',next_payload)['stopped']
        assert not api.event('clock_finished',next_payload)['ok']


def test_host_notification_uses_profile_and_exposes_no_mutation_tools(monkeypatch):
    with create_core() as core:
        chat=TextChat(core)
        def ask(text, model, tools, **kwargs):
            assert tools.declarations() == []
            assert kwargs['profile']=={'pLang':'en','pIns':'Call me Captain.'}
            with pytest.raises(ContractError):
                tools.submit({'id':'unexpected','name':'notes.delete','arguments':{'id':'anything'}})
            return {'ok':True,'completed':True,'text':'Timer finished, Captain.','tool_results':[]}
        monkeypatch.setattr(chat._live,'ask',ask)
        result=chat.run_live('Host timer event','synthetic-live',profile={'pLang':'en','pIns':'Call me Captain.'}, notification=True)
        assert result['ok'] and not chat.busy
        assert chat.close()


@pytest.mark.parametrize('kind',['timer','stopwatch'])
def test_ui_delete_removes_only_actual_target_with_replay_protection(clock_time, monkeypatch, kind):
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        api=NativeBridge(core, JsonStore(get_data_home()/'settings.json'), clocks=clocks)
        monkeypatch.setattr(api,'_window',FakeWindow());assert ready(api)['ok']
        args={'kind':kind,'start':True,**({'duration_seconds':10} if kind=='timer' else {})}
        first=mutate(core,'clocks.create',args)['clock'];second=mutate(core,'clocks.create',args)['clock']
        payload={'version':1,'request_id':'ui-delete','tool':'clocks.delete','arguments':{'id':first['id']}}
        result=api.event('clock_command',payload)
        assert result['ok'] and result['verified'] and result['data']['deleted_id']==first['id']
        assert [c['id'] for c in clocks.snapshot()['clocks']]==[second['id']]
        assert api.event('clock_command',payload)==result
        assert len(clocks.snapshot()['clocks'])==1
        assert not api.event('clock_command',{**payload,'request_id':'missing','arguments':{'id':first['id']}})['ok']


def test_cancelled_clock_delete_does_not_mutate(clock_time):
    clocks=module.Clocks()
    with create_core(clocks=clocks) as core:
        target=mutate(core,'clocks.create',{'kind':'stopwatch','start':True})['clock']
        stop=Event();stop.set()
        args={'id':target['id']}
        result=clocks.delete(args,ToolContext(task_id='cancel-delete',request=request('clocks.delete',arguments=args),cancel_event=stop))
        assert result.status==TaskStatus.CANCELLED and clocks.snapshot()['clocks'][0]['id']==target['id']


@pytest.mark.parametrize('mode',['rest','live'])
def test_model_catalog_does_not_expose_ui_clock_delete(transport,socket,mode):
    with create_core() as core:
        chat=TextChat(core)
        def ask(*args,**kwargs):
            tools=args[2] if mode=='live' else None
            if tools is not None:
                assert 'clocks.delete' not in {d['name'] for d in tools.declarations()}
                with pytest.raises(ContractError):tools.submit({'id':'delete','name':'clocks.delete','arguments':{'id':'any'}})
            return {'ok':True,'completed':True,'text':'Hello','tool_results':[]}
        if mode=='live':
            from unittest.mock import patch
            with patch.object(chat._live,'ask',ask):assert chat.run_live('Hello','synthetic')['ok']
        else:
            transport.responses=[reply([{'text':'Hello'}])]
            assert chat.run('Hello','gemini-3.8-flash')['ok']
            assert 'clocks.delete' not in {d['name'] for d in transport.requests[0]['tools'][0]['functionDeclarations']}
        assert chat.close()
