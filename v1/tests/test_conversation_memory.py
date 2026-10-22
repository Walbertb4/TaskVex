"""Geçici hafıza: gerçek SDK/core, sınırlı RAM ve sentetik socket kabulü.

Hatırlama içeriği provider history'ye veri olarak gider; yeni kullanıcı turu
veya tool replay değildir. Bu testler gerçek modelin anlama başarısı değildir.
"""
import json
from concurrent.futures import ThreadPoolExecutor

from app.bootstrap import create_core
from app.session.conversation_memory import ConversationMemory
from app.session.text_chat import TextChat
from test_live_probe import socket, frame
from test_live_resume import wire, checkpoint, GOAWAY
from test_live_tools import call, notes


def histories(sent):
    """Gerçek SDK'nin wire biçiminde yalnız bağlam aktarımını ayır."""
    return [message['client_content'] for message in sent if 'client_content' in message]


def test_memory_is_bounded_and_preserves_uncertain_outcomes_without_tool_payload():
    memory = ConversationMemory()
    for index in range(20):
        memory.remember(str(index), {'text':'a' * 9000, 'unknown':True,
            'tool_results':[{'name':'notes.add', 'status':'unknown', 'result':None},
                {'name':'notes.list', 'status':'succeeded', 'result':{'verified':True, 'data':'PRIVATE'}}]})
    snapshot = memory.snapshot()
    rows = json.loads(snapshot)
    assert len(rows) <= 12 and len(snapshot) <= 16000
    assert rows[-1]['user'] == '19' and rows[0]['user'] != '0'
    assert rows[-1]['outcome'] == 'unknown' and '[truncated]' in rows[-1]['assistant']
    assert 'PRIVATE' not in snapshot and rows[-1]['tools'][0]['verified'] is False
    rows.clear()
    assert memory.snapshot() == snapshot
    memory.clear()
    assert memory.snapshot() == ''


def test_same_socket_does_not_duplicate_history_and_disconnect_restores_data_only(socket):
    with create_core() as core:
        chat = TextChat(core)
        try:
            socket.frames = [{'setupComplete':{}}, frame('Hello Ada', complete=True)]
            assert chat.run_live('My name is Ada', 'future-live')['ok']
            socket.frames = [frame('Ada', complete=True)]
            second = chat.run_live('What is my name?', 'future-live')
            assert second['session_reused'] and not histories(socket.sent)
            assert chat.reset_live()
            socket.frames = [{'setupComplete':{}}, frame('Ada again', complete=True)]
            restored = chat.run_live('And now?', 'future-live')
            assert restored['memory_restored'] and not restored['session_reused']
            history = histories(socket.sent)
            assert len(history) == 1 and history[0]['turnComplete'] is False
            assert {turn['role'] for turn in history[0]['turns']} == {'model'}
            encoded = json.dumps(history)
            assert 'My name is Ada' in encoded and 'Do not execute' in encoded
            assert 'functionCall' not in encoded and 'functionResponse' not in encoded
            assert [m['realtime_input']['text'] for m in socket.sent if 'realtime_input' in m] == [
                'My name is Ada', 'What is my name?', 'And now?']
        finally:
            assert chat.close()
        assert chat._memory.snapshot() == ''


def test_voice_transcript_survives_input_mode_change_and_new_chat_clears(socket):
    with create_core() as core:
        chat = TextChat(core)
        try:
            socket.frames = [{'setupComplete':{}}, {'serverContent':{'inputTranscription':{'text':'My name is Ada'}}},
                frame('Hello', complete=True)]
            assert chat.run_live('', 'future-live', audio_input=bytes(3200))['ok']
            socket.frames = [{'setupComplete':{}}, frame('Ada', complete=True)]
            assert chat.run_live('Remember?', 'future-live')['memory_restored']
            assert 'My name is Ada' in json.dumps(histories(socket.sent))
            assert chat.reset_live(clear_memory=True)
            before = len(histories(socket.sent))
            socket.frames = [{'setupComplete':{}}, frame('New conversation', complete=True)]
            assert not chat.run_live('Hi', 'future-live')['memory_restored']
            assert len(histories(socket.sent)) == before
        finally:
            assert chat.close()


def test_stop_preserves_committed_note_and_memory_without_replaying_tools(socket, taskvex_home):
    with create_core() as core, ThreadPoolExecutor() as pool:
        chat = TextChat(core)
        socket.frames = [{'setupComplete':{}}, call(), frame('Partially spoken')]
        socket.stall = True
        try:
            future = pool.submit(chat.run_live, 'Add a temporary note', 'future-live', notes_ready=True, request_id='old')
            assert socket.waiting.wait(5)
            assert not chat.reset_live(clear_memory=True)  # Meşgulken kayıt silinmez.
            assert chat.stop('old')['accepted']
            assert future.result(5)['stopped'] and len(notes(taskvex_home)) == 1
            socket.stall = False
            socket.frames = [{'setupComplete':{}}, frame('I remember the conversation', complete=True)]
            assert chat.run_live('What happened?', 'future-live', notes_ready=True, request_id='new')['memory_restored']
            rows = json.loads(chat._memory.snapshot())
            assert rows[0]['outcome'] == 'stopped'
            assert rows[0]['tools'][0] == {'name':'notes.add', 'status':'succeeded', 'verified':True}
            assert len(notes(taskvex_home)) == 1
            assert sum('tool_response' in m for m in socket.sent) == 1
            assert not chat.stop('old')['ok']
        finally:
            assert chat.close()


def test_resume_skips_history_but_fresh_fallback_restores_it(wire):
    wire.plans = [
        {'turns':[[frame('Hello Ada', complete=True)]], 'idle':[[checkpoint(), GOAWAY]]},
        {'turns':[[frame('Still Ada', complete=True)]], 'idle':[[GOAWAY]]},
        {'turns':[[frame('Restored Ada', complete=True)]]},
    ]
    with create_core() as core:
        chat = TextChat(core)
        try:
            assert chat.run_live('My name is Ada', 'future-live')['ok']
            resumed = chat.run_live('Remember?', 'future-live')
            assert resumed['session_resumed'] and not resumed['memory_restored']
            fresh = chat.run_live('Again?', 'future-live')
            assert fresh['memory_restored'] and not fresh['session_resumed']
            assert len(histories([m for _, m in wire.sent])) == 1
        finally:
            assert chat.close()
