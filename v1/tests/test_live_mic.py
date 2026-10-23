"""Mikrofon PCM'ini gerçek SDK/sentetik socket ile dene; cihaz ve API açılmaz.

Geçici notlar aynı core hattından yürür. Transkript yoksa araç başlamamalı,
ses/metin kapsam değişimi eski checkpoint'i kullanmamalıdır.
"""
import asyncio
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.bootstrap import create_core
from app.session.live_probe import probe_live_text
from app.session.text_chat import TextChat
from test_live_probe import socket, frame
from test_live_tools import call, notes
from test_native_bridge import bridge


def test_mic_pcm_uses_explicit_activity_and_input_transcript(socket):
    socket.frames = [{"setupComplete": {}}, {"serverContent": {"inputTranscription": {"text": "Merhaba"}}},
                     frame("Hello", complete=True)]
    report = asyncio.run(probe_live_text('', 'future-live', audio_input=b'\x00\x00' * 3200))
    assert report['ok'] and report['input_text'] == 'Merhaba'
    setup = socket.sent[0]['setup']
    assert setup['realtimeInputConfig']['automatic_activity_detection']['disabled']
    assert 'inputAudioTranscription' in setup
    packets = [item['realtime_input'] for item in socket.sent[1:]]
    assert 'activityStart' in packets[0] and 'activityEnd' in packets[-1]
    assert len(packets) == 4 and all('audio' in packet for packet in packets[1:-1])
    assert all(packet['audio']['mime_type'] == 'audio/pcm;rate=16000' for packet in packets[1:-1])
    assert 'data' not in report and 'test-key' not in str(report)


@pytest.mark.parametrize('data', [b'', b'\x00' * 3199, b'\x00' * 480002], ids=['empty', 'odd', 'large'])
def test_invalid_mic_never_opens_provider(socket, data):
    report = asyncio.run(probe_live_text('', 'future-live', audio_input=data))
    assert not report['ok'] and socket.opened == 0


@pytest.mark.parametrize('transcribed', [False, True])
def test_voice_tools_require_transcript_and_share_core(socket, taskvex_home, transcribed):
    socket.frames = [{"setupComplete": {}}, *([{'serverContent': {'inputTranscription': {'text':'Add a note'}}}] if transcribed else []),
                     call(), frame('Done', complete=True)]
    with create_core() as core:
        chat = TextChat(core)
        try:
            report = chat.run_live('', 'future-live', notes_ready=True, request_id='mic', audio_input=b'\x00\x00' * 1600)
            assert report['ok'] == transcribed
            assert len(notes(taskvex_home)) == int(transcribed)
            if not transcribed:
                assert report['code'] == 'voice_transcript_required' and not report['tool_results']
        finally:
            assert chat.close()


def test_text_to_audio_resets_setup_instead_of_using_text_checkpoint(socket):
    with create_core() as core:
        chat = TextChat(core)
        try:
            socket.frames = [{'setupComplete':{}}, frame('First', complete=True)]
            first = chat.run_live('Hi', 'future-live', request_id='text')
            socket.frames = [{'setupComplete':{}}, frame('Second', complete=True)]
            second = chat.run_live('', 'future-live', request_id='mic', audio_input=b'\x00\x00' * 1600)
            assert first['ok'] and second['ok'] and socket.opened == 2
            assert second['context_reset_reason'] == 'scope_changed' and not second['session_resumed']
            assert first['logical_session_id'] != second['logical_session_id']
        finally:
            assert chat.close()


def test_native_mic_envelope_is_validated_before_chat(bridge, monkeypatch):
    bridge._ready = True
    bridge._live_model = 'future-live'
    bridge._live_models = {'future-live':{}}
    received = []
    monkeypatch.setattr(bridge._chat, 'run_live', lambda text, model, **kw: received.append((text, kw)) or {'ok':True})
    packet = {'request_id':'mic', 'mime_type':'audio/pcm;rate=16000', 'data':b64encode(b'\x00\x00' * 1600).decode()}
    assert bridge.event('live_audio', packet)['ok']
    assert received[0][0] == '' and received[0][1]['audio_input'] == b'\x00\x00' * 1600
    for changes in [{'data':'%%%x'}, {'mime_type':'audio/webm'}, {'request_id':None}, {'data':'a'*640004}]:
        assert not bridge.event('live_audio', {**packet, **changes})['ok']
    assert len(received) == 1


def test_voice_update_and_delete_use_transcribed_target_and_real_id(socket, taskvex_home):
    from app.tools.local.notes import notes_snapshot
    with create_core() as core:
        chat = TextChat(core)
        try:
            socket.frames = [{'setupComplete':{}}, call(), frame('Added', complete=True)]
            assert chat.run_live('Add a note', 'future-live', notes_ready=True, request_id='seed')['ok']
            note_id = notes(taskvex_home)[0]['id']
            for verb, name, args, command in [
                ('edit', 'notes.update', {'id':note_id, 'text':'Voice edited note', 'done':True},
                 'Change Live synthetic note to Voice edited note and mark done'),
                ('delete', 'notes.delete', {'id':note_id}, 'Delete Voice edited note')]:
                socket.frames = [*([{'setupComplete':{}}] if verb == 'edit' else []),
                    {'serverContent':{'inputTranscription':{'text':command}}},
                    call('notes.select', {'kind':'ids','ids':[note_id],'cardinality':'one'}, 'select-' + verb),
                    call(name, {**args, 'expected_snapshot':notes_snapshot(notes(taskvex_home))}, 'mutate-' + verb), frame('Done', complete=True)]
                report = chat.run_live('', 'future-live', notes_ready=True, request_id=verb, audio_input=b'\x00\x00'*1600)
                assert report['ok'] and report['tool_results'][-1]['result']['verified']
                if verb == 'edit':
                    assert notes(taskvex_home)[0]['text'] == 'Voice edited note' and notes(taskvex_home)[0]['done']
                else:
                    assert notes(taskvex_home) == []
        finally:
            assert chat.close()


@pytest.mark.parametrize('committed', [False, True])
def test_voice_stop_keeps_actual_tool_result_and_does_not_replay(socket, taskvex_home, committed):
    socket.stall = True
    socket.frames = [{'setupComplete':{}}, {'serverContent':{'inputTranscription':{'text':'Add a note'}}},
                     *([call()] if committed else [])]
    with create_core() as core, ThreadPoolExecutor(max_workers=1) as pool:
        chat = TextChat(core)
        try:
            running = pool.submit(chat.run_live, '', 'future-live', notes_ready=True, request_id='mic-stop', audio_input=b'\x00\x00'*1600)
            assert socket.waiting.wait(3)
            assert not chat.stop('old')['ok'] and chat.stop('mic-stop')['ok']
            report = running.result(5)
            assert report['stopped'] and socket.opened == 1 and len(notes(taskvex_home)) == int(committed)
        finally:
            assert chat.close()
