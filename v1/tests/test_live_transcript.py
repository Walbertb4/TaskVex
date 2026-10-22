"""Anlık Live transkriptini gerçek SDK/sentetik socket ile sınar; dış API yok.

Tur tamamlanmadan metnin iletilmesi, Stop'ta korunması ve doğru host kimliği
ana sözleşmedir. Bildirim hatası araç sonucunu veya retry politikasını değiştirmez.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.session.live_probe import probe_live_text
from app.session.live_session import PersistentLive
from app.session.text_chat import TextChat
from app.bootstrap import create_core
from test_live_probe import socket, frame
from test_native_bridge import bridge


def test_transcript_arrives_before_completion_and_survives_stop(socket):
    socket.frames = [{'setupComplete':{}}, frame('First '), frame('words')]
    socket.stall = True
    packets = []
    owner = PersistentLive()
    with ThreadPoolExecutor() as pool:
        pending = pool.submit(owner.ask, 'Hello', 'future-live', request_id='first',
                              transcript_sink=lambda *args: packets.append(args) or True)
        assert socket.waiting.wait(3) and not pending.done()
        assert packets == [('j','First ',1), ('j','First words',2)]
        assert owner.stop('first')
        report = pending.result(5)
    assert report['stopped'] and report['text'] == 'First words'
    assert owner.close()


def test_input_and_output_snapshots_are_scoped_by_host(socket):
    socket.frames = [{'setupComplete':{}}, {'serverContent':{'inputTranscription':{'text':'Mer'}}},
        {'serverContent':{'inputTranscription':{'text':'haba'}}}, frame('Hello'), frame(' world',complete=True)]
    delivered = []
    with create_core() as core:
        chat = TextChat(core, transcript_sink=lambda *args: delivered.append(args) or True)
        report = chat.run_live('', 'future-live', request_id='voice-id', audio_input=bytes(3200))
        assert report['ok'] and report['input_text'] == 'Merhaba'
        assert delivered == [('voice-id','u','Mer',1), ('voice-id','u','Merhaba',2),
                             ('voice-id','j','Hello',3), ('voice-id','j','Hello world',4)]
        assert chat.close()


def test_transcript_delivery_error_keeps_final_text_without_retry(socket):
    socket.frames = [{'setupComplete':{}}, frame('Fallback',complete=True)]
    def broken(*args):
        raise RuntimeError('Synthetic UI failure')
    report = asyncio.run(probe_live_text('Hello','future-live',transcript_sink=broken))
    assert report['ok'] and report['text'] == 'Fallback' and socket.opened == 1
    assert report['transcript_error'] == 'transcript_delivery_failed'


def test_interrupted_event_keeps_its_last_text(socket):
    socket.frames = [{'setupComplete':{}}, {'serverContent':{'interrupted':True,
        'outputTranscription':{'text':'Partial'}}}]
    report = asyncio.run(probe_live_text('Hello','future-live'))
    assert report['code'] == 'live_interrupted' and report['text'] == 'Partial'


def test_bridge_serializes_transcript_as_data(bridge):
    assert bridge._transcript('id', 'j', '<img onerror=x>', 1)
    assert bridge._window.calls[-1] == ('liveTranscript', [{'request_id':'id','role':'j','text':'<img onerror=x>','sequence':1}])
