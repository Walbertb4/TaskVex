"""Tests structured annotation selection with real core and synthetic SDK transport.

The model is not claimed to understand natural language; provider open kind/cardinality
produces. True recording/date, single match, fresh snapshot and replay protection
passes through the production line. No user files or paid APIs are used.
"""
import pytest

from app.bootstrap import create_core
from app.session.model_tools import NoteTargetError
from app.session.text_chat import TextChat
from test_note_timestamps import confirmed
from test_local_tools import request
from test_model_note_mutations import execute, gateway, current_snapshot, seed
from test_gemini import transport
from test_live_probe import socket
from test_live_tools import notes


def records(core, *, second_text='Another note', second_time: str | None = "2024-01-01T00:00:00.000Z"):
    """The newest note is first; store location cannot replace date selection."""
    items = [{"id":"new-real-id","text":'hello world',"done":False,"created_at":"2025-02-01T00:00:00.000Z"},
             {"id":"old-real-id","text":second_text,"done":False,"created_at":second_time}]
    confirmed(core, request('notes.replace','seed-selection',{'notes':items}))
    return items


def selection(tools, selector, call_id='select'):
    task = tools.submit({'id':call_id,'name':'notes.select','arguments':selector})
    return tools.result(task.task_id, timeout=2)


@pytest.mark.parametrize('mode',['rest','live'])
@pytest.mark.parametrize('selector',[
    {'kind':'contains','text':'HELL','cardinality':'one'},
    {'kind':'latest','count':1,'cardinality':'one'},
    {'kind':'text','text':'hello world','cardinality':'one'},
    {'kind':'ids','ids':['new-real-id'],'cardinality':'one'},
])
@pytest.mark.parametrize('change',[None, {'done':True}, {'text':'Edited safely'}])
def test_structured_selectors_use_real_ids_for_all_single_mutations(mode,selector,change,transport,socket,taskvex_home):
    with create_core() as core:
        items=records(core);chat=TextChat(core)
        try:
            name='notes.delete' if change is None else 'notes.update'
            report=execute(chat,mode,'A natural request in any supported wording',[
                ('notes.select',selector,'select'),(name,{'id':items[0]['id'],**(change or {})},'mutate')],transport,socket)
            assert report['ok'] and report['tool_results'][-1]['result']['verified']
            assert notes(taskvex_home)==([items[1]] if change is None else [{**items[0],**change},items[1]])
        finally:assert chat.close()


@pytest.mark.parametrize('mode',['rest','live'])
@pytest.mark.parametrize('reason',['multiple','wrong_id','missing_date','tied_date','empty_match','missing_id','too_many_requested'])
def test_ambiguous_or_invalid_selection_preserves_every_record(mode,reason,transport,socket,taskvex_home):
    with create_core() as core:
        items=records(core,second_text='Hello again' if reason=='multiple' else 'Another note',
            second_time=None if reason=='missing_date' else '2025-02-01T00:00:00.000Z' if reason=='tied_date' else '2024-01-01T00:00:00.000Z')
        selector=({'kind':'latest','count':3 if reason=='too_many_requested' else 1,'cardinality':'one'}
            if reason in {'missing_date','tied_date','too_many_requested'} else
            {'kind':'ids','ids':['not-in-store'],'cardinality':'one'} if reason=='missing_id' else
            {'kind':'contains','text':'absent' if reason=='empty_match' else 'hell','cardinality':'one'})
        before=(taskvex_home/'notes.json').read_bytes();chat=TextChat(core)
        try:
            target=items[1]['id'] if reason=='wrong_id' else items[0]['id']
            report=execute(chat,mode,'Ambiguous request', [('notes.select',selector,'select'),
                ('notes.delete',{'id':target},'delete')],transport,socket)
            assert not report['ok'] and report['code']=='note_target_required'
            assert (taskvex_home/'notes.json').read_bytes()==before
        finally:assert chat.close()


def test_ambiguous_one_cannot_be_silently_widened_to_many_or_guessed_id():
    with create_core() as core:
        items=records(core,second_text='Hello again');tools=gateway(core)
        tools.begin_turn('Delete one ambiguous note')
        first=selection(tools,{'kind':'contains','text':'hell','cardinality':'one'})
        assert first['result']['data']['selection_ready'] is False
        for selector in ({'kind':'all','cardinality':'many'}, {'kind':'ids','ids':[items[0]['id']],'cardinality':'one'}):
            selection(tools,selector,selector['kind'])
            with pytest.raises(NoteTargetError):
                tools.submit({'id':'mutation-'+selector['kind'],'name':'notes.delete',
                    'arguments':{'id':items[0]['id'],'expected_snapshot':current_snapshot()}})
        # New user description opens new round; The only target changes with the real ID.
        tools.begin_turn('The user now explicitly chose old-real-id')
        selected=selection(tools,{'kind':'ids','ids':[items[1]['id']],'cardinality':'one'},'clarified')
        task=tools.submit({'id':'clarified-delete','name':'notes.delete','arguments':{
            'id':items[1]['id'],'expected_snapshot':selected['result']['data']['snapshot']}})
        assert tools.result(task.task_id,timeout=2)['result']['verified']


def test_snapshot_change_rejects_mutation_and_blocks_automatic_reselection(taskvex_home):
    with create_core() as core:
        items=records(core);tools=gateway(core);tools.begin_turn('Delete selected note')
        selected=selection(tools,{'kind':'latest','count':1,'cardinality':'one'})
        snapshot=selected['result']['data']['snapshot'];seed(core,'New UI note')
        before=(taskvex_home/'notes.json').read_bytes()
        task=tools.submit({'id':'stale-delete','name':'notes.delete','arguments':{'id':items[0]['id'],'expected_snapshot':snapshot}})
        result=tools.result(task.task_id,timeout=2)
        assert result['status']=='failed' and result['result']['error']['code']=='notes_changed'
        assert (taskvex_home/'notes.json').read_bytes()==before
        selection(tools,{'kind':'ids','ids':[items[0]['id']],'cardinality':'one'},'reselect')
        with pytest.raises(NoteTargetError):
            tools.submit({'id':'retry','name':'notes.delete','arguments':{'id':items[0]['id'],'expected_snapshot':current_snapshot()}})


def test_old_selection_replay_cannot_authorize_a_new_turn():
    with create_core() as core:
        records(core);tools=gateway(core);tools.begin_turn('First request')
        call={'id':'same-selection','name':'notes.select','arguments':{'kind':'latest','count':1,'cardinality':'one'}}
        task=tools.submit(call);selected=tools.result(task.task_id,timeout=2)['result']['data']
        tools.begin_turn('Second request');assert tools.submit(call).task_id==task.task_id
        tools.result(task.task_id)
        with pytest.raises(NoteTargetError):
            tools.submit({'id':'new-delete','name':'notes.delete','arguments':{'id':'new-real-id','expected_snapshot':selected['snapshot']}})
