"""Try to ensure that the candidate removed from the conversation does not have a profile without user approval.

Real registry/policy/TaskManager, temporary profile and synthetic REST/Live are used.
This test does not prove that the language model correctly interprets the social context; user
It verifies that the decision cannot be bypassed by the model and the integrity of the record.
"""
import json
from uuid import uuid4

import pytest

from app.bootstrap import create_core
from app.core.contracts import ContractError, ToolRequest
from app.session.gemini import DEFAULT_MODEL
from app.session.model_instruction import model_instruction
from app.session.model_tools import ModelTools
from app.session.text_chat import TextChat
from app.storage.json_store import JsonStore
from app.tools.local.personal_memory import memory_snapshot
from test_gemini import transport, reply, call
from test_live_probe import frame, socket
from test_live_tools import call as live_call
from test_native_bridge import bridge, ready


def stored(store: JsonStore) -> dict:
    value = store.read()
    assert value is not None
    return value


def setup(store: JsonStore, *, learning=True):
    store.write({'prof':{'pMemory':True,'pLearn':learning,'pMem':'User-approved original'}})


def suggest(core, store, *, name='Candidate', quote='My name is Ada', turn='My name is Ada'):
    """The text is not interpreted in natural language; The provider's structured recommendation is simulated."""
    tools = ModelTools(core, principal='local-user', session_id=uuid4().hex,
                       allowed_tools=('memory.read','memory.patch','memory.propose'))
    tools.begin_turn(turn)
    read = tools.submit({'id':'read','name':'memory.read','arguments':{}})
    snapshot = tools.result(read.task_id, timeout=3)['result']['data']['snapshot']
    task = tools.submit({'id':'propose','name':'memory.propose','arguments':{
        'text':name,'source_quote':quote,'expected_snapshot':snapshot}})
    result = tools.result(task.task_id, timeout=3)
    return result


def decide(core, proposal, approve=True, request_id=None):
    task = core.submit(ToolRequest(request_id=request_id or uuid4().hex,
        source='desktop',principal='local-user',tool='memory.decide',
        arguments={'id':proposal['id'],'approve':approve}))
    return core.wait(task.task_id, timeout=3)


@pytest.mark.parametrize('approve',[False,True])
def test_proposal_is_not_profile_until_actual_user_decision(bridge, approve):
    assert ready(bridge)['ok']
    setup(bridge._store)
    before = bridge._store.path.read_bytes()
    result = suggest(bridge._core, bridge._store)
    proposal = result['result']['data']['proposal']
    assert result['result']['verified'] and not result['result']['evidence']['persisted']
    assert bridge._store.path.read_bytes() == before
    command = {'request_id':'native-decision','arguments':{'id':proposal['id'],'approve':approve}}
    accepted = bridge.event('memory_decision',command)
    assert accepted['verified'] and accepted['completed']
    assert bridge.event('memory_decision',command) == accepted
    assert stored(bridge._store)['prof']['pMem'] == ('User-approved original\nCandidate' if approve else 'User-approved original')


@pytest.mark.parametrize('change',[{'pMem':'New manual text'},{'pLearn':False},{'pMemory':False}])
def test_changed_memory_or_consent_invalidates_approval(bridge, change):
    setup(bridge._store)
    proposal = suggest(bridge._core, bridge._store)['result']['data']['proposal']
    data = stored(bridge._store)
    data['prof'].update(change)
    bridge._store.write(data)
    result = decide(bridge._core,proposal)
    assert result.status.value == 'failed'
    assert stored(bridge._store) == data


def test_new_proposal_and_dismissed_proposal_cannot_use_old_approval(bridge):
    setup(bridge._store)
    old = suggest(bridge._core,bridge._store)['result']['data']['proposal']
    current = suggest(bridge._core,bridge._store,name='New candidate')['result']['data']['proposal']
    assert decide(bridge._core,old).status.value == 'failed'
    assert decide(bridge._core,current,False).result.verified
    assert decide(bridge._core,current,True).status.value == 'failed'
    assert stored(bridge._store)['prof']['pMem'] == 'User-approved original'


def test_quote_must_be_from_this_turn_and_model_cannot_approve(bridge):
    setup(bridge._store)
    rejected=suggest(bridge._core,bridge._store,quote='My name is Ada',turn='')
    assert rejected['result']['error']['code']=='source_unavailable'
    with pytest.raises(ContractError):
        ModelTools(bridge._core,principal='local-user',session_id='not-allowed',allowed_tools=('memory.decide',)).submit(
            {'id':'no-read','name':'memory.decide','arguments':{'id':'a'*32,'approve':True}})
    tools = ModelTools(bridge._core,principal='local-user',session_id='voice',allowed_tools=('memory.propose',))
    tools.begin_turn('')
    tools.observe_input('My name is Ada')
    assert tools._user_text == 'My name is Ada'
    tools.begin_turn('Other message')
    assert tools._user_text == 'Other message'


def test_learning_off_rejects_proposal_and_never_changes_profile(bridge):
    setup(bridge._store,learning=False)
    before = bridge._store.path.read_bytes()
    result = suggest(bridge._core,bridge._store)
    assert result['result']['error']['code'] == 'learning_disabled'
    assert bridge._store.path.read_bytes() == before


def test_restart_does_not_turn_pending_proposal_into_saved_fact(taskvex_home):
    store = JsonStore(taskvex_home/'settings.json')
    setup(store)
    with create_core(settings_store=store) as core:
        proposal = suggest(core,store)['result']['data']['proposal']
    with create_core(settings_store=store) as core:
        assert decide(core,proposal).status.value == 'failed'
    assert stored(store)['prof']['pMem'] == 'User-approved original'


def test_rest_self_report_suggests_without_save_then_native_approval(bridge,transport):
    assert ready(bridge)['ok']
    setup(bridge._store)
    profile = stored(bridge._store)['prof']
    transport.responses=[reply([call('memory.read',{},'read')]),
        reply([call('memory.propose',{'text':'Name: Ada',
            'expected_snapshot':memory_snapshot(profile)},'propose')]),reply([{'text':'Suggestion ready'}])]
    report = bridge._chat.run('My name is Ada',DEFAULT_MODEL,profile=profile)
    assert report['ok']
    assert stored(bridge._store)['prof']['pMem']=='User-approved original'
    proposal = report['tool_results'][1]['result']['data']['proposal']
    assert bridge.event('memory_decision',{'request_id':'approve-rest','arguments':{'id':proposal['id'],'approve':True}})['verified']
    assert stored(bridge._store)['prof']['pMem'].endswith('Name: Ada')
    assert 'memory.decide' in json.dumps(transport.requests[0]['tools'])


@pytest.mark.parametrize('source_available,model_quote',[(True,None),(True,'I am called Ada'),(False,'Invented statement')])
def test_live_voice_quote_reaches_proposal_without_extra_provider_request(socket,taskvex_home,source_available,model_quote):
    store=JsonStore(taskvex_home/'settings.json')
    setup(store)
    profile=stored(store)['prof']
    args={'text':'Name: Ada','expected_snapshot':memory_snapshot(profile)}
    if model_quote is not None:
        args['source_quote']=model_quote  # The old provider quote cannot replace the actual source.
    socket.frames=[{'setupComplete':{}}, {'serverContent':{'inputTranscription':{
        'text':'My name is Ada' if source_available else '', 'finished':True}}},
        live_call('memory.read',{},'read'),live_call('memory.propose',args,'propose'),frame('Review the suggestion',complete=True)]
    with create_core(settings_store=store) as core:
        chat=TextChat(core)
        try:
            report=chat.run_live('','future-live',profile=profile,audio_input=b'\0\0'*1600)
            if source_available:
                assert report['ok'],report
                proposal=report['tool_results'][1]['result']['data']['proposal']
                assert proposal['text']=='Name: Ada' and proposal['source_quote']=='My name is Ada'
            else:
                assert not report['ok'] and report['code']=='voice_transcript_required'
                assert not report['tool_results']  # No tool can be operated without ASR.
            assert stored(store)['prof']['pMem']=='User-approved original'
            assert len([item for item in socket.sent if 'setup' in item])==1
        finally:
            assert chat.close()


def test_suggestion_instruction_is_opt_in_and_distinguishes_third_parties():
    assert 'Memory suggestions enabled' not in model_instruction({'pMemory':True})
    assert 'Memory suggestions enabled' not in model_instruction({'pLearn':True})
    instruction=model_instruction({'pMemory':True,'pLearn':True})
    assert 'third parties' in instruction and 'quotations' in instruction and 'ask naturally' in instruction.lower() and 'later explicit' in instruction.lower()


def test_learning_mode_model_cannot_append_around_approval(bridge):
    setup(bridge._store)
    tools=ModelTools(bridge._core,principal='local-user',session_id='approval-boundary',
        allowed_tools=('memory.read','memory.patch','memory.propose'))
    tools.begin_turn('My name is Ada')
    task=tools.submit({'id':'read','name':'memory.read','arguments':{}})
    snapshot=tools.result(task.task_id,timeout=3)['result']['data']['snapshot']
    schema=next(item for item in tools.declarations() if item['name']=='memory.patch')
    assert 'append' not in schema['parameters']['properties']['action']['enum']
    with pytest.raises(ContractError):
        tools.submit({'id':'bypass','name':'memory.patch','arguments':{'action':'append','text':'Name: Ada','expected_snapshot':snapshot}})
    assert stored(bridge._store)['prof']['pMem']=='User-approved original'


def test_proposal_source_proof_is_host_owned_and_replay_stays_stable(bridge):
    setup(bridge._store)
    tools=ModelTools(bridge._core,principal='local-user',session_id='source-proof',allowed_tools=('memory.read','memory.propose'))
    tools.begin_turn('My name is Ada')
    read=tools.submit({'id':'read','name':'memory.read','arguments':{}})
    snapshot=tools.result(read.task_id,timeout=3)['result']['data']['snapshot']
    args={'text':'Name: Ada','source_quote':'My name is Ada','expected_snapshot':snapshot}
    schema=next(item for item in tools.declarations() if item['name']=='memory.propose')
    assert not {'source_verified','source_quote'} & schema['parameters']['properties'].keys()
    with pytest.raises(ContractError):
        tools.submit({'id':'forged','name':'memory.propose','arguments':{**args,'source_verified':True}})
    call={'id':'proposal','name':'memory.propose','arguments':args}
    task=tools.submit(call)
    result=tools.result(task.task_id,timeout=3)
    tools.begin_turn('Unrelated text')
    assert tools.submit(call).task_id==task.task_id
    assert tools.result(task.task_id,timeout=3)==result


def test_model_paraphrase_does_not_reject_valid_current_turn_suggestion(bridge):
    """Even though the provider paraphrases the source sentence, the real source is from the host."""
    setup(bridge._store)
    current='I study engineering.'
    result=suggest(bridge._core,bridge._store, name='Education: engineering',
                   quote='I am an engineering student.',turn=current)
    assert result['status']=='succeeded'
    assert result['result']['data']['proposal']['source_quote']==current
    assert stored(bridge._store)['prof']['pMem']=='User-approved original'


def test_host_source_is_not_limited_to_a_short_model_quote(bridge):
    setup(bridge._store)
    text='x'*2500+' I study engineering.'
    result=suggest(bridge._core,bridge._store,name='Education: engineering',turn=text)
    assert result['status']=='succeeded'
    assert result['result']['data']['proposal']['source_quote']==text


@pytest.mark.parametrize('confirm',[None,True,False])
def test_saved_review_preference_controls_learning_and_defaults_to_ask(bridge,confirm):
    setup(bridge._store)
    data=stored(bridge._store)
    if confirm is not None:
        data['prof']['pMemoryConfirm']=confirm
        bridge._store.write(data)
    result=suggest(bridge._core,bridge._store,name='Preference: blue')
    assert result['result']['verified']
    if confirm is False:
        assert result['result']['data']['proposal'] is None
        assert result['result']['data']['saved_automatically'] is True
        assert result['result']['evidence']['persisted'] and result['result']['evidence']['read_back']
        assert stored(bridge._store)['prof']['pMem']=='User-approved original\nPreference: blue'
        assert bridge._memory_reply({'tool_results':[result]})['memory_profile']['pMem'].endswith('blue')
    else:
        assert result['result']['data']['proposal']
        assert stored(bridge._store)==data


def test_changed_review_choice_invalidates_old_read_before_any_auto_save(bridge):
    setup(bridge._store)
    tools=ModelTools(bridge._core,principal='local-user',session_id='review-scope',allowed_tools=('memory.read','memory.propose'))
    tools.begin_turn('My name is Ada')
    task=tools.submit({'id':'read','name':'memory.read','arguments':{}})
    snapshot=tools.result(task.task_id,timeout=3)['result']['data']['snapshot']
    data=stored(bridge._store)
    data['prof']['pMemoryConfirm']=False
    bridge._store.write(data)
    task=tools.submit({'id':'suggest','name':'memory.propose','arguments':{'text':'Name: Ada','expected_snapshot':snapshot}})
    result=tools.result(task.task_id,timeout=3)
    assert result['result']['error']['code']=='memory_changed'
    assert stored(bridge._store)==data


def test_auto_save_replay_keeps_one_fact_and_old_source(bridge):
    setup(bridge._store)
    data=stored(bridge._store);data['prof']['pMemoryConfirm']=False;bridge._store.write(data)
    tools=ModelTools(bridge._core,principal='local-user',session_id='auto-replay',allowed_tools=('memory.read','memory.propose'))
    tools.begin_turn('My name is Ada')
    task=tools.submit({'id':'read','name':'memory.read','arguments':{}})
    snapshot=tools.result(task.task_id,timeout=3)['result']['data']['snapshot']
    call={'id':'save','name':'memory.propose','arguments':{'text':'Name: Ada','expected_snapshot':snapshot}}
    task=tools.submit(call);result=tools.result(task.task_id,timeout=3)
    before=bridge._store.path.read_bytes()
    tools.begin_turn('Other message')
    assert tools.submit(call).task_id==task.task_id
    assert tools.result(task.task_id,timeout=3)==result
    assert bridge._store.path.read_bytes()==before
    assert stored(bridge._store)['prof']['pMem'].count('Name: Ada')==1


def test_auto_save_failure_never_claims_persisted_success(bridge,monkeypatch):
    from app.storage.json_store import StoreError
    setup(bridge._store)
    data=stored(bridge._store);data['prof']['pMemoryConfirm']=False;bridge._store.write(data)
    def fail_write(candidate):
        raise StoreError('write_failed','Synthetic write failure')
    monkeypatch.setattr(bridge._store,'write',fail_write)
    result=suggest(bridge._core,bridge._store)
    assert result['status']=='failed' and not result['result']['verified']
    assert stored(bridge._store)==data


@pytest.mark.parametrize('approve', [True, False])
@pytest.mark.parametrize('live', [True, False])
def test_later_spoken_or_text_answer_uses_shared_decision(socket, transport, taskvex_home, approve, live):
    """On the actual SDK/core line, ASR and REST resolve the same pending ID."""
    store = JsonStore(taskvex_home/'settings.json')
    setup(store)
    with create_core(settings_store=store) as core:
        proposal = suggest(core, store, name='Name: Ada')['result']['data']['proposal']
        chat = TextChat(core)
        args = {'id':proposal['id'], 'approve':approve}
        try:
            if live:
                socket.frames = [{'setupComplete':{}}, {'serverContent':{'inputTranscription':{
                    'text':'Yes, save that fact' if approve else 'No, do not save that', 'finished':True}}},
                    live_call('memory.read',{},'decision-read'), live_call('memory.decide',args,'decision'),
                    frame('Saved' if approve else 'Dismissed',complete=True)]
                report = chat.run_live('', 'future-live', profile=stored(store)['prof'], audio_input=b'\0\0'*1600)
            else:
                transport.responses = [reply([call('memory.read',{},'decision-read')]),
                    reply([call('memory.decide',args,'decision')]),reply([{'text':'Saved' if approve else 'Dismissed'}])]
                report = chat.run('Yes, save that fact' if approve else 'No, do not save that', DEFAULT_MODEL,
                    profile=stored(store)['prof'])
            assert report['ok'], report
            outcome = report['tool_results'][-1]['result']
            assert outcome['verified'] and outcome['data']['decided_id'] == proposal['id']
            assert stored(store)['prof']['pMem'] == ('User-approved original\nName: Ada' if approve else 'User-approved original')
            assert outcome['evidence']['persisted'] is approve
        finally:
            assert chat.close()


def test_model_cannot_self_approve_even_after_reread_but_later_answer_can(bridge):
    setup(bridge._store)
    tools = ModelTools(bridge._core, principal='local-user',session_id='review-turns',
        allowed_tools=('memory.read','memory.propose','memory.decide'))
    tools.begin_turn('My name is Ada')
    read = tools.submit({'id':'initial-read','name':'memory.read','arguments':{}})
    snapshot = tools.result(read.task_id, timeout=3)['result']['data']['snapshot']
    task = tools.submit({'id':'suggestion','name':'memory.propose','arguments':{
        'text':'Name: Ada','expected_snapshot':snapshot}})
    proposal = tools.result(task.task_id,timeout=3)['result']['data']['proposal']
    read = tools.submit({'id':'reread','name':'memory.read','arguments':{}})
    tools.result(read.task_id,timeout=3)
    decision = {'id':'decision','name':'memory.decide','arguments':{'id':proposal['id'],'approve':True}}
    with pytest.raises(ContractError):
        tools.submit(decision)
    tools.begin_turn('Yes, save that')
    with pytest.raises(ContractError):
        tools.submit(decision)  # ID information of the previous turn is not sufficient.
    read = tools.submit({'id':'new-read','name':'memory.read','arguments':{}})
    tools.result(read.task_id,timeout=3)
    task = tools.submit(decision)
    assert tools.result(task.task_id,timeout=3)['result']['verified']
    tools.begin_turn('Other message')
    assert tools.submit(decision).task_id == task.task_id
    assert stored(bridge._store)['prof']['pMem'].count('Name: Ada') == 1
    assert decide(bridge._core, proposal).status.value == 'failed'  # Late UI confirmation will not write twice.


def test_fresh_read_cannot_authorize_replaced_or_expired_pending_id(bridge):
    setup(bridge._store)
    old = suggest(bridge._core,bridge._store)['result']['data']['proposal']
    tools = ModelTools(bridge._core,principal='local-user',session_id='stale-decision',allowed_tools=('memory.read','memory.decide'))
    tools.begin_turn('Save that')
    read = tools.submit({'id':'read','name':'memory.read','arguments':{}})
    tools.result(read.task_id,timeout=3)
    current = suggest(bridge._core,bridge._store,name='New candidate')['result']['data']['proposal']
    task = tools.submit({'id':'decision','name':'memory.decide','arguments':{'id':old['id'],'approve':True}})
    assert tools.result(task.task_id,timeout=3)['result']['error']['code'] == 'proposal_expired'
    assert stored(bridge._store)['prof']['pMem'] == 'User-approved original'
    assert decide(bridge._core,current,False).result.verified


def test_decision_requires_actual_input_and_read_drops_changed_candidate(bridge):
    setup(bridge._store)
    proposal = suggest(bridge._core,bridge._store)['result']['data']['proposal']
    tools = ModelTools(bridge._core,principal='local-user',session_id='empty-decision',allowed_tools=('memory.read','memory.decide'))
    tools.begin_turn('')
    read = tools.submit({'id':'read','name':'memory.read','arguments':{}})
    tools.result(read.task_id,timeout=3)
    with pytest.raises(ContractError):
        tools.submit({'id':'decision','name':'memory.decide','arguments':{'id':proposal['id'],'approve':True}})
    data = stored(bridge._store)
    data['prof']['pMem'] = 'Manual change'
    bridge._store.write(data)
    read = tools.submit({'id':'changed-read','name':'memory.read','arguments':{}})
    assert tools.result(read.task_id,timeout=3)['result']['data']['proposal'] is None
    assert decide(bridge._core,proposal).status.value == 'failed'
