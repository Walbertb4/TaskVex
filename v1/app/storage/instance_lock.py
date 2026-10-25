"""Allows only one native TaskVex process in the same data folder.

The operating system lock on the open file, not the existence of the lock file
is authorized. Releases OS lock on crash; There is no old PID deletion or timeout.
The file is not deleted: deleting and recreating it results in two separate files being locked.
"""
import os
from pathlib import Path
from typing import BinaryIO, Self


class AlreadyRunningError(RuntimeError):
    """This data root is used by another process; The beginning must stop."""


class SingleInstance:
    """Data is entered before the printers; core and is held until the window closes."""

    def __init__(self, home: Path) -> None:
        self._path = home.resolve() / 'instance.lock'
        self._file: BinaryIO | None = None

    def __enter__(self) -> Self:
        """Lock without waiting for the first byte; Don't count the actual I/O error as a lock conflict."""
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
            # EACCES/EAGAIN/EDEADLK is lock conflict; disk/directory errors
            # It remains a general startup error, the running application is not adapted.
            import errno
            if error.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                raise AlreadyRunningError('TaskVex already uses this data directory') from None
            raise
        self._file = handle
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Handle closing normally releases OS lock at winter/exception."""
        if self._file is not None:
            self._file.close()
            self._file = None
