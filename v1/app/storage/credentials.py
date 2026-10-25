"""Store the Gemini key in Windows Credential Manager.

TASKVEX_HOME profiles use separate registration; temporary test profile real key
cannot read or crush. CredRead/Write APIs with ctypes standard library
is called; There is no return to the JSON/plaintext spare tank. In the same Windows account
It does not provide a sandbox against running trusted processes.
"""

import ctypes as c
from ctypes import wintypes as w
from hashlib import sha256
import os
from pathlib import Path


class CredentialError(RuntimeError):
    """Report operating system error with fixed message without key."""


class _Credential(c.Structure):
    """Win32 CREDENTIALW layout; pointers respect 32/64 bit Python."""
    _fields_ = [("flags", w.DWORD), ("type", w.DWORD), ("target", w.LPWSTR),
                ("comment", w.LPWSTR), ("written", w.FILETIME), ("size", w.DWORD),
                ("blob", c.POINTER(c.c_ubyte)), ("persist", w.DWORD),
                ("attribute_count", w.DWORD), ("attributes", c.c_void_p),
                ("alias", w.LPWSTR), ("username", w.LPWSTR)]


def _library():
    """Set Windows API signatures on; Do not make system calls during import."""
    if os.name != "nt":
        raise CredentialError("Windows credential storage is unavailable")
    library = c.WinDLL("advapi32", use_last_error=True)
    signatures = [
        (library.CredReadW, [w.LPCWSTR, w.DWORD, w.DWORD, c.POINTER(c.POINTER(_Credential))], w.BOOL),
        (library.CredWriteW, [c.POINTER(_Credential), w.DWORD], w.BOOL),
        (library.CredFree, [c.c_void_p], None),
    ]
    for function, arguments, result in signatures:
        function.argtypes, function.restype = arguments, result
    return library


def _validate(key: str) -> bytes:
    """Reject input that is empty, overly long, or does not comply with the HTTP header."""
    if not isinstance(key, str) or not 1 <= len(key) <= 2048 or any(
        not 33 <= ord(char) <= 126 for char in key
    ):
        raise CredentialError("Expected a non-empty API key without whitespace")
    return key.encode("ascii")


class GeminiCredentials:
    """Gemini record for the single data profile chosen by the trusted host.

    The profile path is not taken from the UI/model payload. The record name contains the summary of the path;
    The path itself does not appear in the identity store. Only the person who has the authority to return the key
    It is on the Python host; Only configured status is sent to the UI.
    """

    def __init__(self, home: Path) -> None:
        profile = str(home.resolve()).casefold()
        self._target = "TaskVex/Gemini/" + sha256(profile.encode("utf-8")).hexdigest()

    def read(self) -> str | None:
        """Read record and release memory with CredFree; hiding the error except for not being found."""
        library = _library()
        pointer = c.POINTER(_Credential)()
        if not library.CredReadW(self._target, 1, 0, c.byref(pointer)):
            if c.get_last_error() == 1168:  # ERROR_NOT_FOUND
                return None
            raise CredentialError("API key could not be read from Windows credentials")
        try:
            if not pointer or not 1 <= pointer.contents.size <= 2048 or not pointer.contents.blob:
                raise CredentialError("Stored API key is invalid")
            try:
                key = c.string_at(pointer.contents.blob, pointer.contents.size).decode("ascii")
            except UnicodeDecodeError:
                raise CredentialError("Stored API key is invalid") from None
            _validate(key)
            return key
        finally:
            library.CredFree(pointer)

    def write(self, key: str) -> None:
        """Just write the record of this profile and verify it by reading it back; make a network request.

        Local buffer is cleared; Python strings are definitely deleted from memory
        not claimed. If post-write validation fails, the record may have been applied.
        """
        data = _validate(key)
        buffer = c.create_string_buffer(data)
        credential = _Credential(type=1, target=self._target, size=len(data),
                                 blob=c.cast(buffer, c.POINTER(c.c_ubyte)), persist=2,
                                 username="TaskVex")  # CRED_PERSIST_LOCAL_MACHINE: same as user/machine
        try:
            if not _library().CredWriteW(c.byref(credential), 0):
                raise CredentialError("API key could not be stored in Windows credentials")
        finally:
            c.memset(c.addressof(buffer), 0, c.sizeof(buffer))
        if self.read() != key:
            raise CredentialError("API key storage could not be verified")


def load_gemini_key() -> str | None:
    """The open process switch takes precedence; Otherwise, read the current profile in Windows."""
    key = os.environ.get("GEMINI_API_KEY")
    if key is not None:
        _validate(key)
        return key
    if os.name != "nt":
        return None
    from app.config import get_data_home
    return GeminiCredentials(get_data_home()).read()
