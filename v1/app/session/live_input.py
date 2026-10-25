"""Moves microphone tracks from API thread to single Live owner with limited RAM.

This queue does not operate tools. Sequence number replay/missing rejects the part;
In case of overflow or device error, the turn is canceled and the process is not continued with the lost sound.
"""
import asyncio
from queue import Empty, Full, Queue
from threading import Lock
from time import perf_counter

from google.genai import types

from app.core.contracts import ContractError


class LiveInput:
    """PCM for a total of 15 seconds, waiting for a maximum of 2 seconds; no audio is written to disk."""

    def __init__(self):
        self._queue: Queue[bytes | None] = Queue(maxsize=20)
        self._lock = Lock()
        self.ready = False
        self.closed = False
        self.failed = False
        self._sequence = self._bytes = 0
        # The accepted queue and the audio actually sent to the socket are separate.
        # Content is not retained; counter/time. for delay diagnosis of this round only
        self.sent_packets = 0
        self.first_sent_at: float | None = None
        self.end_sent_at: float | None = None

    def feed(self, sequence: int, data: bytes | None) -> bool:
        """Just take the next 100 ms PCM; None is the open speech ending."""
        with self._lock:
            if not self.ready or self.closed:
                return False
            if (type(sequence) is not int or sequence != self._sequence
                    or data is not None and (type(data) is not bytes or len(data) != 3200)
                    or self._bytes + len(data or b'') > 480000):
                self.failed = self.closed = True
                return False
            try:
                self._queue.put_nowait(data)
            except Full:
                self.failed = self.closed = True
                return False
            self._sequence += 1
            self._bytes += len(data or b'')
            if data is None:
                self.closed = True
            return True

    async def send(self, session):
        """Export limit of single local conversation to SDK with open start/end.

        Ready cannot be opened until the startup is sent. Last packet from sequential queue
        then generates activity_end; With the automatic VAD/EOS there are no two separate finishers.
        """
        await session.send_realtime_input(activity_start=types.ActivityStart())
        self.ready = True
        while True:
            if self.failed:
                raise ContractError('Microphone stream failed')
            try:
                chunk = await asyncio.to_thread(self._queue.get, True, .2)
            except Empty:
                continue
            if chunk is None:
                await session.send_realtime_input(activity_end=types.ActivityEnd())
                self.end_sent_at = perf_counter()
                return
            await session.send_realtime_input(audio=types.Blob(data=chunk, mime_type='audio/pcm;rate=16000'))
            self.sent_packets += 1
            if self.first_sent_at is None:
                self.first_sent_at = perf_counter()

    def close(self):
        """Reject late packets and drop pending PCM; Don't touch another round's tail."""
        with self._lock:
            self.closed = True
            self.ready = False
            while True:
                try:
                    self._queue.get_nowait()
                except Empty:
                    break
