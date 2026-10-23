"""Sınırlı mikrofon akışını gerçek SDK ve sentetik socket ile doğrula.

Gerçek hesap, mikrofon veya kullanıcı notu kullanılmaz. VAD setup'ı, parça
sırası, Stop ve transkript güvenliği üretim kodundan geçer.
"""
import asyncio
from base64 import urlsafe_b64decode
from concurrent.futures import ThreadPoolExecutor
from time import monotonic, sleep
import pytest

from app.bootstrap import create_core
from app.session.live_input import LiveInput
from app.session.live_probe import probe_live_text
from app.session.text_chat import TextChat
from app.core.contracts import ContractError
from test_live_probe import socket, frame
from test_live_tools import call, notes
from test_native_bridge import bridge


def test_stream_queue_validates_order_size_and_backpressure():
    stream = LiveInput()
    assert not stream.feed(0, bytes(3200))
    stream.ready = True
    assert stream.feed(0, bytes(3200))
    assert not stream.feed(0, bytes(3200)) and stream.failed
    stream.close()
    assert not stream.ready and not stream.feed(1, bytes(3200))
    for wrong in [b'', bytes(3199), 'audio', None]:
        stream = LiveInput()
        stream.ready = True
        if wrong is None:
            assert stream.feed(0, None) and stream.closed
        else:
            assert not stream.feed(0, wrong) and stream.failed
    stream = LiveInput()
    stream.ready = True
    assert all(stream.feed(i, bytes(3200)) for i in range(20))
    assert not stream.feed(20, bytes(3200)) and stream.failed
    stream = LiveInput()
    stream.ready = True
    for i in range(150):
        assert stream.feed(i, bytes(3200))
        stream._queue.get_nowait()
    assert not stream.feed(150, bytes(3200)) and stream.failed


def test_stream_sends_before_finish_with_automatic_vad(socket):
    async def scenario():
        stream = LiveInput()
        socket.frames = [{'setupComplete':{}}, {'serverContent':{'inputTranscription':{'text':'Merhaba'}}}, frame('Hello', complete=True)]
        task = asyncio.create_task(probe_live_text('', 'future-live', audio_input=stream))
        while not stream.ready:
            await asyncio.sleep(.001)
        assert stream.feed(0, b'\xff' * 3200)
        report = await task
        assert report['ok'] and report['input_text'] == 'Merhaba'
        assert stream.closed and not stream.ready
        return report
    asyncio.run(scenario())
    vad = socket.sent[0]['setup']['realtimeInputConfig']['automatic_activity_detection']
    assert vad['disabled'] is False and vad['silence_duration_ms'] == 700
    packets = [p['realtime_input'] for p in socket.sent[1:]]
    assert packets and 'audio' in packets[0]
    assert urlsafe_b64decode(packets[0]['audio']['data']) == b'\xff' * 3200
    assert not any('activityStart' in p or 'activityEnd' in p for p in packets)


@pytest.mark.parametrize('transcribed', [False, True])
def test_stream_tools_require_transcript(socket, taskvex_home, transcribed):
    with create_core() as core:
        chat = TextChat(core)
        stream = LiveInput()
        socket.frames = [{'setupComplete':{}},
            *([{'serverContent':{'inputTranscription':{'text':'Add a note'}}}] if transcribed else []),
            call(), frame('Done', complete=True)]
        with ThreadPoolExecutor() as pool:
            pending = pool.submit(chat.run_live, '', 'future-live', request_id='stream', notes_ready=True, audio_input=stream)
            deadline = monotonic() + 3
            while not stream.ready and monotonic() < deadline:
                sleep(.001)
            assert stream.feed(0, bytes(3200))
            report = pending.result(5)
        assert report['ok'] == transcribed and len(notes(taskvex_home)) == int(transcribed)
        if not transcribed:
            assert report['code'] == 'voice_transcript_required'
        assert chat.close()


def test_stream_sender_failure_does_not_wait_for_provider_or_start_tools(socket):
    class FailedInput(LiveInput):
        async def send(self, session):
            raise ContractError('Synthetic sender failure')
    socket.frames = [{'setupComplete':{}}]
    report = asyncio.run(probe_live_text('', 'future-live', audio_input=FailedInput()))
    assert report['code'] == 'live_contract_error' and not report['tool_results']
    assert report['elapsed_ms'] < 3000 and socket.closed


def test_explicit_stream_end_uses_audio_stream_end():
    sent = []
    class Session:
        async def send_realtime_input(self, **kwargs):
            sent.append(kwargs)
    async def scenario():
        stream = LiveInput()
        task = asyncio.create_task(stream.send(Session()))
        while not stream.ready:
            await asyncio.sleep(0)
        assert stream.feed(0, bytes(3200)) and stream.feed(1, None)
        await asyncio.wait_for(task, 2)
        stream.close()
    asyncio.run(scenario())
    assert sent[0]['audio'].mime_type == 'audio/pcm;rate=16000'
    assert sent[1] == {'audio_stream_end':True}


def test_stream_stop_is_scoped_and_closes_ingress(socket):
    socket.frames = [{'setupComplete':{}}]
    socket.stall = True
    with create_core() as core:
        chat = TextChat(core)
        stream = LiveInput()
        with ThreadPoolExecutor() as pool:
            pending = pool.submit(chat.run_live, '', 'future-live', request_id='stream', audio_input=stream)
            deadline = monotonic() + 3
            while not stream.ready and monotonic() < deadline:
                sleep(.001)
            assert chat.audio_input('old', 0, bytes(3200))['ok'] is False
            assert not chat.stop('old')['ok']
            assert chat.audio_input('stream', 0, bytes(3200))['ok']
            assert socket.waiting.wait(3)
            assert chat.stop('stream')['accepted']
            assert pending.result(5)['stopped']
        assert stream.closed and not stream.ready and not chat.audio_input('stream', 1, bytes(3200))['ok']
        assert chat.close()


def test_native_stream_envelope_rejects_before_dispatch(bridge, monkeypatch):
    received = []
    monkeypatch.setattr(bridge._chat, 'audio_input', lambda *args: received.append(args) or {'ok':True})
    assert bridge.event('live_audio_feed', {'request_id':'mic'})['ok']
    from base64 import b64encode
    packet = {'request_id':'mic', 'sequence':0, 'data':b64encode(bytes(3200)).decode()}
    assert bridge.event('live_audio_feed', packet)['ok']
    assert received[-1] == ('mic', 0, bytes(3200))
    for changes in [{'sequence':True}, {'data':'x'}, {'data':'%'*4268}, {'extra':True}, {'request_id':None}]:
        assert not bridge.event('live_audio_feed', {**packet, **changes})['ok']
    assert len(received) == 2


def test_thought_only_does_not_close_active_microphone(socket, monkeypatch):
    """İşitilmeyen model düşüncesi devam eden kullanıcı girişini kesmemeli."""
    from app.session import live_probe
    original = live_probe._next_message
    checks = []
    stream = LiveInput()

    async def next_message(messages, sender):
        if checks:
            assert not stream.closed
        message = await original(messages, sender)
        if message.server_content and message.server_content.model_turn:
            checks.append(True)
        return message

    monkeypatch.setattr(live_probe, '_next_message', next_message)
    socket.frames = [{'setupComplete': {}},
        {'serverContent': {'modelTurn': {'parts': [{'text': 'Internal', 'thought': True}]}}},
        frame('Merhaba', complete=True)]

    async def scenario():
        task = asyncio.create_task(probe_live_text('', 'future-live', audio_input=stream))
        while not stream.ready:
            await asyncio.sleep(.001)
        assert stream.feed(0, bytes(3200))
        result = await task
        assert result['ok'] and result['text'] == 'Merhaba' and stream.closed
    asyncio.run(scenario())
    assert checks
