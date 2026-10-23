"""Uyku isteğinin ortak araç/izin hattını ve tur sınırlarını doğrular.

Sağlayıcı seçimi sentetiktir; gerçek modelin bütün dilleri anladığını kanıtlamaz.
Registry, policy, TaskManager ve SDK taşıması gerçek koddan geçer; gerçek
kullanıcı kaydı, mikrofon veya ücretli API kullanılmaz.
"""
import pytest
from concurrent.futures import ThreadPoolExecutor

from app.bootstrap import create_core
from app.core.contracts import ContractError
from app.session.model_tools import ModelTools, sleep_request
from app.session.text_chat import TextChat
from test_gemini import transport, reply, call
from test_live_probe import socket, frame
from test_sleep import sleep_call


@pytest.mark.parametrize('mode', ['once', 'persistent', 'off'])
def test_core_request_is_verified_but_not_applied(mode):
    with create_core() as core:
        tools = ModelTools(core, principal='local-user', session_id='control',
            allowed_tools=('assistant.request_sleep_mode',))
        task = tools.submit({'id': 'control', 'name': 'assistant.request_sleep_mode', 'arguments': {'mode': mode}})
        outcome = tools.result(task.task_id, timeout=2)
        assert outcome['status'] == 'succeeded'
        assert outcome['result']['verified']
        assert outcome['result']['data'] == {'mode': mode, 'apply_after': 'reply_playback', 'applied': False}
        assert tools.submit({'id': 'control', 'name': 'assistant.request_sleep_mode', 'arguments': {'mode': mode}}).task_id == task.task_id
        report = {'ok': True, 'tool_results': [outcome]}
        assert sleep_request(report)['sleep_mode'] == mode
        assert sleep_request(report, frozenset({task.task_id})) == {}
        for guard in ({'ok': False}, {'unknown': True}, {'stopped': True}):
            assert sleep_request({**report, **guard}) == {}


@pytest.mark.parametrize('arguments', [{}, {'mode': 'anything'}, {'mode': None},
    {'mode': 'once', 'permission': True}, {'mode': ['once']}])
def test_schema_rejects_invalid_control(arguments):
    with create_core() as core:
        tools = ModelTools(core, principal='local-user', session_id='invalid', allowed_tools=('assistant.request_sleep_mode',))
        with pytest.raises(ContractError):
            tools.submit({'id': 'bad', 'name': 'assistant.request_sleep_mode', 'arguments': arguments})


@pytest.mark.parametrize('mode', ['once', 'persistent', 'off'])
def test_rest_sleep_uses_same_tool_without_note_transfer(transport, mode):
    transport.responses = [reply([call('assistant.request_sleep_mode', {'mode': mode})]),
        reply([{'text': 'Acknowledged'}])]
    with create_core() as core:
        chat = TextChat(core)
        report = chat.run('A natural request', 'gemini-3.8-flash', notes_ready=False, request_id='rest-control')
        assert report['ok'] and report['completed'] and report['sleep_mode'] == mode
        assert report['tool_results'][0]['result']['data']['applied'] is False
        assert len(transport.requests) == 2
        assert chat.close()


def test_live_replayed_old_control_does_not_schedule_another_transition(socket):
    socket.frames = [{'setupComplete': {}}, sleep_call('persistent', 'replayed-control'), frame('Accepted', complete=True)]
    with create_core() as core:
        chat = TextChat(core)
        first = chat.run_live('Uyku moduna kalıcı olarak gir', 'future-live', notes_ready=False)
        assert first['ok'] and first['sleep_mode'] == 'persistent'
        socket.frames = [sleep_call('persistent', 'replayed-control'), frame('Old call replayed', complete=True)]
        second = chat.run_live('Another request', 'future-live', notes_ready=False)
        assert second['ok'] and not second.get('sleep_requested') and 'sleep_mode' not in second
        assert second['tool_results'][0]['task_id'] == first['tool_results'][0]['task_id']
        assert chat.close()


@pytest.mark.parametrize('ending', [frame('Partial'), {'serverContent': {'interrupted': True}}])
def test_no_completed_reply_means_no_sleep_even_after_tool_acceptance(socket, ending):
    socket.frames = [{'setupComplete': {}}, sleep_call('once'), ending]
    with create_core() as core:
        chat = TextChat(core)
        report = chat.run_live('Please sleep', 'future-live')
        assert not report['ok'] and not report.get('sleep_requested') and 'sleep_mode' not in report
        assert report['tool_results'][0]['result']['verified']
        assert chat.close()


def test_model_acknowledgement_alone_does_not_change_mode(socket):
    socket.frames = [{'setupComplete': {}}, frame('I will sleep now', complete=True)]
    with create_core() as core:
        chat = TextChat(core)
        report = chat.run_live('Uyku moduna kalıcı olarak gir', 'future-live')
        assert report['ok'] and not report.get('sleep_requested') and 'sleep_mode' not in report
        assert chat.close()


def test_stop_after_control_acceptance_discards_pending_change(socket):
    socket.frames = [{'setupComplete': {}}, sleep_call('persistent')]
    socket.stall = True
    with create_core() as core, ThreadPoolExecutor(max_workers=1) as pool:
        chat = TextChat(core)
        try:
            running = pool.submit(chat.run_live, 'Please stay asleep', 'future-live', request_id='stopping-control')
            assert socket.waiting.wait(3)
            assert chat.stop('stopping-control')['accepted']
            report = running.result(3)
            assert report['stopped'] and not report['ok'] and not report.get('sleep_requested')
            assert report['tool_results'][0]['result']['data']['applied'] is False
        finally:
            chat.close()


def test_conflicting_control_requests_do_not_guess(socket):
    socket.frames = [{'setupComplete': {}}, sleep_call('persistent', 'enable'), sleep_call('off', 'disable'), frame('Done', complete=True)]
    with create_core() as core:
        chat = TextChat(core)
        report = chat.run_live('Unclear request', 'future-live')
        assert not report['ok'] and report['code'] == 'conflicting_sleep_requests'
        assert not report.get('sleep_requested') and chat.close()
