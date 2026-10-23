"""Aynı veri klasöründe yalnız bir native TaskVex sürecine izin verir.

Kilit dosyasının varlığı değil, açık dosya üzerindeki işletim sistemi kilidi
yetkilidir. Çökmede OS kilidi bırakır; eski PID silme veya zaman aşımı yoktur.
Dosya silinmez: silip yeniden yaratmak iki ayrı dosyanın kilitlenmesine yol açar.
"""
import os
from pathlib import Path
from typing import BinaryIO, Self


class AlreadyRunningError(RuntimeError):
    """Bu veri kökü başka bir süreç tarafından kullanılıyor; başlangıç durmalı."""


class SingleInstance:
    """Veri yazıcılarından önce girilir; core ve pencere kapanana kadar tutulur."""

    def __init__(self, home: Path) -> None:
        self._path = home.resolve() / 'instance.lock'
        self._file: BinaryIO | None = None

    def __enter__(self) -> Self:
        """İlk byte'ı beklemeden kilitle; gerçek I/O hatasını kilit çakışması sayma."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        handle = self._path.open('a+b')
        try:
            if self._path.stat().st_size == 0:
                handle.write(b'\0')
                handle.flush()
            handle.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            handle.close()
            # EACCES/EAGAIN/EDEADLK kilit çakışmasıdır; disk/dizin hataları
            # genel başlangıç hatası olarak kalır, çalışan uygulama uydurulmaz.
            import errno
            if error.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                raise AlreadyRunningError('TaskVex already uses this data directory') from None
            raise
        self._file = handle
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Handle kapanışı normal çıkışta/exception'da OS kilidini bırakır."""
        if self._file is not None:
            self._file.close()
            self._file = None
