"""Bounded, request-scoped camera/screen input for the existing Live socket owner.

Only the latest JPEG is retained in RAM. This is media input, not a tool executor;
frames never enter task history, conversation summaries or files.
"""
import asyncio
from threading import Lock
from typing import TypedDict
from time import monotonic

from google.genai import types

from app.core.contracts import ContractError


def validate_frame(data: bytes) -> bytes:
    """Bound transport size and JPEG framing; decoding remains the provider's job."""
    if type(data) is not bytes or not 4 <= len(data) <= 262144 or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
        raise ContractError('Invalid camera JPEG')
    return data


class LiveVideo:
    """One initial frame and a latest-only slot, sent at most once per second."""

    def __init__(self, initial: bytes):
        self._frame: tuple[float, bytes] | None = (monotonic(), validate_frame(initial))
        self._lock = Lock()
        self._sequence = 0
        self.ready = True  # Accept fresh frames during socket setup; no provider send yet.
        self.closed = self.failed = False
        self.sent_frames = 0

    def feed(self, sequence: int, data: bytes | None) -> bool:
        """Reject late/replayed packets; null closes only video, never microphone or reply."""
        with self._lock:
            if self.closed:
                return False
            if type(sequence) is not int or sequence != self._sequence or sequence >= 120:
                self.failed = self.closed = True
                self._frame = None
                return False
            try:
                if data is not None:
                    validate_frame(data)
            except ContractError:
                self.failed = self.closed = True
                self._frame = None
                return False
            self._sequence += 1
            self._frame = (monotonic(), data) if data is not None else None
            self.closed = data is None
            return True

    async def start(self, session):
        """Send the initial image before text/audio begins, using the same socket."""
        await self._send_latest(session)
        self.ready = not self.closed

    async def _send_latest(self, session):
        with self._lock:
            frame, self._frame = self._frame, None
            if self.closed or frame is None or monotonic() - frame[0] > 2:
                return
        await session.send_realtime_input(video=types.Blob(data=frame[1], mime_type='image/jpeg'))
        self.sent_frames += 1

    async def send(self, session):
        """Sample the latest slot; no queue, replay or reconnect worker is introduced."""
        while not self.closed:
            await asyncio.sleep(1)
            await self._send_latest(session)

    def close(self):
        """Discard queued pixels immediately; an already sent image cannot be recalled."""
        with self._lock:
            self.closed = True
            self.ready = False
            self._frame = None


class VideoOptions(TypedDict, total=False):
    """Typed optional keyword shared by bridge and conversation owner."""

    video_input: LiveVideo
