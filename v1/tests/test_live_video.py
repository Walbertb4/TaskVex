"""Synthetic camera transport checks; no real camera, account or paid request.

Exercise the real Live SDK wire format, request ownership and cleanup boundaries.
"""
import asyncio
from base64 import b64encode, urlsafe_b64decode
from threading import Event

import pytest

from app.core.contracts import ContractError
from app.session.live_input import LiveInput
from app.session.live_probe import probe_live_text
from app.session.live_session import PersistentLive
from app.session.live_video import LiveVideo, validate_frame
from test_live_probe import socket, frame
from test_native_bridge import bridge

# JPEG transport framing only; the synthetic provider never decodes this payload.
JPEG = b'\xff\xd8synthetic-image\xff\xd9'


@pytest.mark.parametrize('invalid', [b'', b'not jpeg', b'\xff\xd8missing-end', b'\xff\xd8'+bytes(262144)+b'\xff\xd9', 'jpeg'], ids=['empty','wrong-format','truncated','oversized','wrong-type'])
def test_camera_bounds(invalid):
    with pytest.raises(ContractError):
        validate_frame(invalid)


def test_camera_latest_only_sequence_close_and_expiry(monkeypatch):
    clock = [0.]
    monkeypatch.setattr('app.session.live_video.monotonic', lambda: clock[0])
    video = LiveVideo(JPEG)
    assert video.feed(0, JPEG+b'\xff\xd9')
    assert video.feed(1, JPEG)
    assert video._frame == (0., JPEG)
    sent = []
    class Session:
        async def send_realtime_input(self, **kwargs):
            sent.append(kwargs)
    clock[0] = 3
    asyncio.run(video.start(Session()))
    assert not sent  # A setup delay cannot send stale queued pixels.
    assert video.feed(2, JPEG)
    asyncio.run(video._send_latest(Session()))
    assert len(sent) == 1 and sent[0]['video'].mime_type == 'image/jpeg'
    assert not video.feed(2, JPEG) and video.failed
    video.close()
    assert video._frame is None and not video.feed(3, JPEG)


def test_camera_initial_precedes_text_and_is_not_in_report(socket):
    socket.frames = [{'setupComplete': {}}, frame('A synthetic object', complete=True)]
    video = LiveVideo(JPEG)
    report = asyncio.run(probe_live_text('Describe this', 'future-live', video_input=video))
    assert report['ok'] and report['video_frames_sent'] == 1 and video.closed
    packets = [p['realtime_input'] for p in socket.sent[1:]]
    assert urlsafe_b64decode(packets[0]['video']['data']) == JPEG
    assert packets[1] == {'text': 'Describe this'}
    assert 'synthetic-image' not in str(report) and not report['tool_results']


def test_video_and_microphone_share_socket_and_independent_end(socket):
    async def scenario():
        video, audio = LiveVideo(JPEG), LiveInput()
        socket.frames = [{'setupComplete': {}}, frame('Hello', complete=True)]
        report = await probe_live_text('', 'future-live', video_input=video, audio_input=audio)
        assert report['ok'] and video.closed and audio.closed
    asyncio.run(scenario())
    assert socket.opened == 1
    assert socket.sent[1]['realtime_input'] == {'activityStart': {}}
    assert 'video' in socket.sent[2]['realtime_input']
    assert sum('activityStart' in p.get('realtime_input', {}) for p in socket.sent) == 1


def test_request_id_and_stop_reject_old_camera_packets():
    owner = PersistentLive()
    owner._video = video = LiveVideo(JPEG)
    event = Event()
    owner._pending = ('new', event)
    assert not owner.video_input('old', 0, JPEG)['ok']
    assert owner.video_input('new', 0, JPEG)['ok']
    assert owner.video_input('new', 1, None)['ok'] and video.closed
    assert not event.is_set()  # Camera Off must not Stop the model response.
    owner._video = LiveVideo(JPEG)
    event.set()
    assert not owner.video_input('new', 0, JPEG)['ok']


def test_bridge_camera_uses_existing_live_owner_and_rejects_other_paths(bridge, monkeypatch):
    bridge.event('ui_ready', {'version': '1.0'})
    bridge._live_models = {'future-live': {}}
    bridge._live_model = 'future-live'
    calls = []
    def run(text, model, **kwargs):
        calls.append((text, model, kwargs['video_input']))
        return {'ok': True, 'completed': True}
    monkeypatch.setattr(bridge._chat, 'run_live', run)
    payload = {'request_id': 'camera', 'text': 'Describe this', 'video': b64encode(JPEG).decode()}
    assert bridge.event('live_text', payload)['ok']
    assert calls[0][:2] == ('Describe this', 'future-live')
    assert isinstance(calls[0][2], LiveVideo)
    assert not bridge.event('text', payload)['ok']
    assert not bridge.event('live_text', {**payload, 'video': 'bad encoding!'})['ok']
    assert len(calls) == 1
    bridge._sleeping = True
    assert not bridge.event('live_video_feed', {'request_id': 'camera'})['ok']


def test_video_sender_failure_ends_turn_without_retry(socket):
    class FailedVideo(LiveVideo):
        async def send(self, session):
            raise ContractError('Synthetic video failure')
    socket.frames = [{'setupComplete': {}}]
    socket.stall = True
    report = asyncio.run(probe_live_text('Describe', 'future-live', video_input=FailedVideo(JPEG)))
    assert report['code'] == 'live_contract_error' and report['completed']
    assert report['elapsed_ms'] < 3000 and socket.opened == 1 and socket.closed


def test_camera_cadence_keeps_only_latest_and_discards_closed_pixels():
    from time import monotonic
    sent = []
    class Session:
        async def send_realtime_input(self, **kwargs):
            sent.append((monotonic(), kwargs['video'].data))
    async def scenario():
        video = LiveVideo(JPEG)
        await video.start(Session())
        task = asyncio.create_task(video.send(Session()))
        assert video.feed(0, JPEG+b'\xff\xd9') and video.feed(1, JPEG)
        await asyncio.sleep(.05)
        assert len(sent) == 1
        async with asyncio.timeout(2):
            while len(sent) < 2:
                await asyncio.sleep(.01)
        video.close()
        await video._send_latest(Session())
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())
    assert len(sent) == 2 and sent[1][0] - sent[0][0] >= .95 and sent[1][1] == JPEG


def test_actual_stop_closes_camera_and_preserves_next_request(socket):
    from concurrent.futures import ThreadPoolExecutor
    owner = PersistentLive()
    video = LiveVideo(JPEG)
    socket.frames = [{'setupComplete': {}}]
    socket.stall = True
    try:
        with ThreadPoolExecutor() as pool:
            running = pool.submit(owner.ask, 'Describe', 'future-live', request_id='old', video_input=video)
            assert socket.waiting.wait(3)
            assert owner.stop('old') and video.closed
            assert not owner.video_input('old', 0, JPEG)['ok']
            report = running.result(3)
            assert report['stopped'] and not report.get('unknown')
        socket.frames = [{'setupComplete': {}}, frame('Fresh', complete=True)]
        report = owner.ask('New request', 'future-live', request_id='new')
        assert report['ok'] and not owner.video_input('old', 0, JPEG)['ok']
        assert 'video_frames_sent' not in report
    finally:
        assert owner.close()
