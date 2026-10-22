"""Mikrofon parçalarını API thread'inden tek Live sahibine sınırlı RAM ile taşır.

Bu kuyruk araç çalıştırmaz. Sıra numarası tekrar/eksik parçayı reddeder;
taşma veya cihaz hatasında tur iptal edilir, kayıp sesle işleme devam edilmez.
"""
import asyncio
from queue import Empty, Full, Queue
from threading import Lock

from google.genai import types

from app.core.contracts import ContractError


class LiveInput:
    """En çok 2 saniye bekleyen, toplam 15 saniye PCM; hiçbir ses diske yazılmaz."""

    def __init__(self):
        self._queue: Queue[bytes | None] = Queue(maxsize=20)
        self._lock = Lock()
        self.ready = False
        self.closed = False
        self.failed = False
        self._sequence = self._bytes = 0

    def feed(self, sequence: int, data: bytes | None) -> bool:
        """Yalnız sıradaki 100 ms PCM'i al; None açık konuşma bitişidir."""
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
        """SDK socket'ine yalnız sahibi yazar; sessizlik VAD için de iletilir."""
        self.ready = True
        while True:
            if self.failed:
                raise ContractError('Microphone stream failed')
            try:
                chunk = await asyncio.to_thread(self._queue.get, True, .2)
            except Empty:
                continue
            if chunk is None:
                await session.send_realtime_input(audio_stream_end=True)
                return
            await session.send_realtime_input(audio=types.Blob(data=chunk, mime_type='audio/pcm;rate=16000'))

    def close(self):
        """Geç paketleri reddet ve bekleyen PCM'i bırak; başka turun kuyruğuna dokunma."""
        with self._lock:
            self.closed = True
            self.ready = False
            while True:
                try:
                    self._queue.get_nowait()
                except Empty:
                    break
