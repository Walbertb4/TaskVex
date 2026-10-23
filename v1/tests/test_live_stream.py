"""Sınırlı mikrofon akışını gerçek SDK ve sentetik socket ile doğrula.

Gerçek hesap, mikrofon veya kullanıcı notu kullanılmaz. VAD setup'ı, parça
sırası, Stop ve transkript güvenliği üretim kodundan geçer.
"""
import asyncio
from base64 import urlsafe_b64decode
from concurrent.futures import ThreadPoolExecutor
from time import monotonic, sleep
import pytest
from google.genai import types

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


def test_stream_sends_with_explicit_activity_boundary(socket):
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
    assert vad['disabled'] is True and 'silence_duration_ms' not in vad
    packets = [p['realtime_input'] for p in socket.sent[1:]]
    assert packets[0] == {'activityStart':{}}
    assert urlsafe_b64decode(packets[1]['audio']['data']) == b'\xff' * 3200
    assert not any('audioStreamEnd' in p for p in packets)


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


def test_explicit_stream_end_uses_ordered_activity_end():
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
        assert stream.sent_packets == 1
        assert stream.first_sent_at is not None and stream.end_sent_at is not None
        assert stream.first_sent_at <= stream.end_sent_at
        stream.close()
    asyncio.run(scenario())
    assert isinstance(sent[0]['activity_start'], types.ActivityStart)
    assert sent[1]['audio'].mime_type == 'audio/pcm;rate=16000'
    assert 'activity_end' in sent[2] and len(sent) == 3


@pytest.mark.parametrize('sent,final', [(False, False), (True, False), (True, True)])
def test_idle_timeout_identifies_input_progress_without_audio_content(socket, monkeypatch, sent, final):
    """25 s sınırını küçültmeden aynı dalı kısa sentetik beklemeyle dene.

    Hiç PCM gitmemesi, PCM gidip transkript gelmemesi ve kesin transkript
    sonrası sessizlik ayrı kanıttır; sağlayıcı arızası olduğu varsayılmaz.
    """
    from app.session import live_probe
    monkeypatch.setattr(live_probe, 'LIVE_IDLE_SECONDS', .08)
    socket.frames = [{'setupComplete': {}}]
    if final:
        socket.frames.append({'serverContent': {'inputTranscription': {'text': 'Test', 'finished': True}}})
    socket.stall = True

    async def scenario():
        stream = LiveInput()
        task = asyncio.create_task(probe_live_text('', 'future-live', audio_input=stream))
        while not stream.ready and not task.done():
            await asyncio.sleep(.001)
        if sent:
            assert stream.feed(0, bytes(3200))
        report = await task
        assert report['code'] == 'live_idle_timeout'
        assert report['input_sent_packets'] == int(sent)
        assert (report['input_first_sent_ms'] is not None) == sent
        assert (report['input_end_sent_ms'] is not None) == final
        assert report['received_events'] == int(final)
        assert (report['input_final_ms'] is not None) == final
        assert report['wait_phase'] == ('after_input_final' if final else 'before_input_final')
        assert socket.opened == 1 and socket.closed and stream.closed
        assert 'test-key' not in str(report)
    asyncio.run(scenario())


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


@pytest.mark.parametrize('final_text', ['Notlarimi listele', None])
def test_final_transcript_closes_old_ingress_before_model_thinks(socket, final_text):
    """Sonraki PCM eski tura gitmez; yanıtı iptal etmek için Stop kullanılmaz."""
    async def scenario():
        stream = LiveInput()
        transcription = {'finished': True}
        if final_text:
            transcription['text'] = final_text
        socket.frames = [{'setupComplete': {}}, {'serverContent': {'inputTranscription': transcription}}]
        socket.stall = True
        task = asyncio.create_task(probe_live_text('', 'future-live', audio_input=stream))
        while not stream.ready:
            await asyncio.sleep(.001)
        assert stream.feed(0, bytes(3200))
        assert await asyncio.to_thread(socket.waiting.wait, 2)
        assert stream.closed and not stream.feed(1, b'\x01\x00' * 1600)
        assert not task.done()  # Model yanıtı beklenir; giriş sonu Stop değildir.
        socket.frames.append(frame('Confirmed', complete=True))
        # Fixture boş recv'de kasıtlı beklediğinden sonuç yerine kontrollü temizle.
        task.cancel()
        await task
    asyncio.run(scenario())


@pytest.mark.parametrize('text', ['Vex', 'Vex.', 'Computer'])
def test_wake_only_turn_finishes_without_tool_or_model_answer(socket, text):
    socket.frames = [{'setupComplete': {}},
        {'serverContent': {'inputTranscription': {'text': text, 'finished': True}}}]
    result = asyncio.run(probe_live_text('', 'future-live', audio_input=bytes(3200),
        profile={'pWake': 'Computer' if text == 'Computer' else 'Vex'}))
    assert result['ok'] and result['completed'] and result['wake_only']
    assert not result['tool_results'] and result['text'] == ''
    assert socket.closed



def test_final_transcript_keeps_the_real_reply_alive(socket, monkeypatch):
    """Girişin kapanışı gerçek model yanıtını iptal etmez."""
    from app.session import live_probe
    original = live_probe._next_message
    stream = LiveInput()
    reads = 0

    async def checked(messages, sender):
        nonlocal reads
        reads += 1
        if reads == 2:
            assert stream.closed and not stream.feed(1, bytes(3200))
        return await original(messages, sender)

    monkeypatch.setattr(live_probe, '_next_message', checked)
    socket.frames = [{'setupComplete': {}},
        {'serverContent': {'inputTranscription': {'text': 'Merhaba', 'finished': True}}},
        frame('Reply survived', complete=True)]

    async def scenario():
        task = asyncio.create_task(probe_live_text('', 'future-live', audio_input=stream))
        while not stream.ready:
            await asyncio.sleep(.001)
        assert stream.feed(0, bytes(3200))
        result = await task
        assert result['ok'] and result['text'] == 'Reply survived'
    asyncio.run(scenario())


def test_final_transcript_flushes_audio_before_waiting_for_reply(socket, monkeypatch):
    """Sunucu EOS gelmeden yanıtlamazsa giriş kapatıp beklemek 25 s kilit yaratır."""
    from google.genai.live import AsyncSession
    from app.session import live_probe
    original = AsyncSession.send_realtime_input
    monkeypatch.setattr(live_probe, 'LIVE_IDLE_SECONDS', .08)
    async def send(session, **kwargs):
        await original(session, **kwargs)
        if 'activity_end' in kwargs:
            socket.frames.append(frame('Reply after flush', complete=True))
    monkeypatch.setattr(AsyncSession, 'send_realtime_input', send)
    socket.frames = [{'setupComplete': {}}, {'serverContent': {
        'inputTranscription': {'text': 'Merhaba', 'finished': True}}}]
    socket.stall = True
    async def scenario():
        stream = LiveInput()
        task = asyncio.create_task(probe_live_text('', 'future-live', audio_input=stream))
        while not stream.ready and not task.done():
            await asyncio.sleep(.001)
        assert stream.feed(0, bytes(3200))
        report = await task
        assert report['ok'] and report['text'] == 'Reply after flush'
        assert report['input_end_sent_ms'] is not None
        assert not stream.feed(1, bytes(3200))
    asyncio.run(scenario())


def test_fourteen_packets_and_two_interim_transcripts_end_without_final_flag(socket, monkeypatch):
    """Kullanıcının 14 PCM/2 olay gözlemi: ara transkript final sayılmadan bitir.

    Sentetik sunucu cevabı yalnız açık activity_end sonrasında verir. Gerçek
    sağlayıcı arızasının yeniden üretimi değil, yeni protokol kabulüdür.
    """
    from google.genai.live import AsyncSession
    from app.session import live_probe
    original_send, original_next = AsyncSession.send_realtime_input, live_probe._next_message
    async def scenario():
        ended = asyncio.Event()
        sent_packets = reads = 0
        async def send(session, **kwargs):
            nonlocal sent_packets
            await original_send(session, **kwargs)
            if 'audio' in kwargs:
                sent_packets += 1
            if 'activity_end' in kwargs:
                assert sent_packets == 14
                socket.frames.append(frame('Explicit turn answered', complete=True))
                ended.set()
        async def receive(messages, sender):
            nonlocal reads
            reads += 1
            if reads == 3:
                await ended.wait()
            return await original_next(messages, sender)
        monkeypatch.setattr(AsyncSession, 'send_realtime_input', send)
        monkeypatch.setattr(live_probe, '_next_message', receive)
        socket.frames = [{'setupComplete': {}},
            {'serverContent': {'inputTranscription': {'text':'Mer'}}},
            {'serverContent': {'inputTranscription': {'text':'haba'}}}]
        stream = LiveInput()
        task = asyncio.create_task(probe_live_text('', 'future-live', audio_input=stream))
        while not stream.ready:
            await asyncio.sleep(.001)
        for sequence in range(14):
            assert stream.feed(sequence, bytes(3200))
        assert stream.feed(14, None)
        report = await asyncio.wait_for(task, 2)
        assert report['ok'] and report['input_text'] == 'Merhaba'
        assert report['input_boundary'] == 'manual_activity' and report['input_sent_packets'] == 14
        assert report['input_end_sent_ms'] is not None and socket.opened == 1
    asyncio.run(scenario())
