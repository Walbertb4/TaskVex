"""PCM taşımasını gerçek SDK ile, sentetik socket üzerinden doğrula.

Ses hoparlöre verilmez; sink yalnız gözlemcidir. UI teslimi fiziksel çalma
kanıtı sayılmaz. Hatalı ses çıktısı doğrulanmış araç/metin sonucunu kaybettirmez.
"""

import asyncio
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from app.bootstrap import create_core
from app.session.live_probe import probe_live_text
from app.session.live_session import PersistentLive
from app.session.text_chat import TextChat
from test_live_probe import socket, frame
from test_live_tools import call, notes


def pcm(data=b'\x00\x00' * 24, mime='audio/pcm;rate=24000'):
    """Sesi ve transkripti aynı server event'e koy; bütün parçalar okunmalı."""
    return {"serverContent": {"modelTurn": {"role": "model", "parts": [
        {"inlineData": {"data": b64encode(data).decode(), "mimeType": mime}}]},
        "outputTranscription": {"text": "Synthetic audio transcript"}, "turnComplete": True}}


def audio_frame(text):
    """Eski probe fixture'ının üç baytlık örneğini tam 16-bit PCM yap."""
    message = frame(text, complete=True, audio=True)
    for part in message['serverContent']['modelTurn']['parts']:
        part['inlineData']['data'] = 'AAA='
    return message


def test_audio_parts_and_transcript_are_both_forwarded_without_recording(socket):
    delivered = []
    socket.frames = [{"setupComplete": {}}, audio_frame("Answer")]
    report = asyncio.run(probe_live_text('Hi', 'future-live',
        audio_sink=lambda data, mime: delivered.append((data, mime)) or True))
    assert report['ok'] and report['text'] == 'Answer'
    assert len(delivered) == 2 and report['audio_bytes_forwarded'] == 4
    assert report['audio_bytes_discarded'] == 0 and report['audio_error'] is None
    assert all(mime == 'audio/pcm;rate=24000' for _, mime in delivered)
    assert 'data' not in report  # Rapor/history PCM içermez.


@pytest.mark.parametrize('data,mime', [(b'\x00', 'audio/pcm;rate=24000'),
    (b'\x00\x00', 'audio/mp3'), (b'\x00' * 131074, 'audio/pcm;rate=24000')], ids=['odd', 'mime', 'oversize'])
def test_invalid_pcm_preserves_text_and_never_reaches_ui(socket, data, mime):
    delivered = []
    socket.frames = [{"setupComplete": {}}, pcm(data, mime)]
    report = asyncio.run(probe_live_text('Hi', 'future-live',
        audio_sink=lambda *args: delivered.append(args) or True))
    assert report['ok'] and report['text'] == 'Synthetic audio transcript'
    assert report['audio_error'] == 'invalid_pcm' and not delivered


@pytest.mark.parametrize('reject', [False, True])
def test_rejected_playback_stops_forwarding_but_keeps_verified_note(socket, taskvex_home, reject):
    delivered = []
    def sink(data, mime):
        delivered.append(data)
        if reject:
            raise RuntimeError('SECRET driver detail')
        return False
    socket.frames = [{"setupComplete": {}}, call(), audio_frame('Saved')]
    with create_core() as core:
        chat = TextChat(core, audio_sink=lambda request_id, data, mime: sink(data, mime))
        try:
            report = chat.run_live('Add note', 'future-live', notes_ready=True, request_id='audio-1')
            assert report['ok'] and len(notes(taskvex_home)) == 1
            assert report['tool_results'][0]['result']['verified']
            assert report['audio_error'] == 'playback_unavailable' and len(delivered) == 1
            assert report['audio_bytes_forwarded'] == 0 and report['audio_bytes_discarded'] == 4
            assert 'SECRET' not in str(report)
        finally:
            assert chat.close()


def test_host_scopes_audio_to_user_request_and_next_message(socket):
    delivered = []
    with create_core() as core:
        chat = TextChat(core, audio_sink=lambda request_id, data, mime: delivered.append(request_id) or True)
        try:
            socket.frames = [{"setupComplete": {}}, pcm()]
            assert chat.run_live('One', 'future-live', request_id='first')['ok']
            socket.frames = [pcm()]
            assert chat.run_live('Two', 'future-live', request_id='second')['ok']
            assert delivered == ['first', 'second']
        finally:
            assert chat.close()


def test_stop_during_audio_delivery_has_no_replay_or_new_audio_request(socket):
    entered, release = Event(), Event()
    def sink(data, mime):
        entered.set()
        assert release.wait(5)
        return True
    socket.frames = [{"setupComplete": {}}, pcm()]
    host = PersistentLive()
    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            running = pool.submit(host.ask, 'One', 'future-live', request_id='audio-1', audio_sink=sink)
            assert entered.wait(3)
            assert host.stop('audio-1') and not host.stop('old')
            release.set()
            report = running.result(5)
            assert report['stopped'] and not report['ok'] and socket.closed
            assert socket.opened == 1
        finally:
            release.set()
            assert host.close()


def test_audio_turn_limit_bounds_total_forwarded_pcm(socket):
    delivered = []
    chunk = pcm(b'\x00\x00' * 65536)
    chunk['serverContent']['turnComplete'] = False
    socket.frames = [{"setupComplete": {}}, *[chunk] * 23, frame('Done', complete=True)]
    report = asyncio.run(probe_live_text('Hi', 'future-live',
        audio_sink=lambda data, mime: delivered.append(len(data)) or True))
    assert report['ok'] and report['audio_error'] == 'audio_limit'
    assert sum(delivered) <= 2880000 and len(delivered) == 21
