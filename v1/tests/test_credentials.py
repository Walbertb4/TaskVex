"""Verify identity store by spoofing Win32 boundary; actual record writing.

Blob and C pointer placement are real. Windows error, memory release, profile
isolation and corrupt record situations are checked. Real Windows/UI acceptance separate
native smoke scenario; here the user's identity store is not changed.
"""

import ctypes as c
import os

import pytest

from app.storage import credentials as native

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows credential ABI tests")


class MemoryCredentials:
    """Just keep records of the test; Emulate Win32's pointer ownership."""
    def __init__(self):
        self.entries, self.freed = {}, 0
        self.fail_read = self.fail_write = False

    def CredWriteW(self, pointer, flags):
        value = c.cast(pointer, c.POINTER(native._Credential)).contents
        assert flags == 0 and value.type == 1 and value.persist == 2
        if self.fail_write:
            return False
        self.entries[value.target] = c.string_at(value.blob, value.size)
        return True

    def CredReadW(self, target, kind, flags, output):
        assert kind == 1 and flags == 0
        if self.fail_read or target not in self.entries:
            c.set_last_error(5 if self.fail_read else 1168)
            return False
        value = self.entries[target]
        self.buffer = c.create_string_buffer(value)
        self.credential = native._Credential(size=len(value), blob=c.cast(self.buffer, c.POINTER(c.c_ubyte)))
        c.cast(output, c.POINTER(c.POINTER(native._Credential)))[0] = c.pointer(self.credential)
        return True

    def CredFree(self, pointer):
        self.freed += 1


@pytest.fixture
def memory(monkeypatch):
    backend = MemoryCredentials()
    monkeypatch.setattr(native, "_library", lambda: backend)
    return backend


def test_write_read_verify_and_profile_isolation(memory, tmp_path):
    first = native.GeminiCredentials(tmp_path / "one")
    second = native.GeminiCredentials(tmp_path / "two")
    assert first.read() is None
    first.write("TEST-KEY")
    assert first.read() == "TEST-KEY" and second.read() is None
    assert memory.freed == 2
    first.write("REPLACEMENT")
    assert first.read() == "REPLACEMENT" and len(memory.entries) == 1


@pytest.mark.parametrize("key", [None, 3, "", " ", "leading ", "a\nb", "a\0b", "x" * 2049, "ü"])
def test_invalid_key_never_reaches_windows(memory, tmp_path, key):
    with pytest.raises(native.CredentialError):
        native.GeminiCredentials(tmp_path).write(key)
    assert memory.entries == {}


def test_write_failure_preserves_old_key(memory, tmp_path):
    store = native.GeminiCredentials(tmp_path)
    store.write("OLD")
    memory.fail_write = True
    with pytest.raises(native.CredentialError):
        store.write("NEW")
    assert store.read() == "OLD"


@pytest.mark.parametrize("blob", [b"", b"x" * 2049, b"\xff", b"with space"])
def test_corrupt_key_is_rejected_and_native_memory_freed(memory, tmp_path, blob):
    store = native.GeminiCredentials(tmp_path)
    memory.entries[store._target] = blob
    with pytest.raises(native.CredentialError):
        store.read()
    assert memory.freed == 1


def test_read_error_is_not_missing_key(memory, tmp_path):
    memory.fail_read = True
    with pytest.raises(native.CredentialError):
        native.GeminiCredentials(tmp_path).read()


def test_unverified_write_is_reported(memory, tmp_path, monkeypatch):
    store = native.GeminiCredentials(tmp_path)
    monkeypatch.setattr(store, "read", lambda: "OLD")
    with pytest.raises(native.CredentialError, match="verified"):
        store.write("NEW")


def test_environment_key_precedence_and_stored_key_fallback(memory, monkeypatch):
    from app.config import get_data_home
    store = native.GeminiCredentials(get_data_home())
    store.write("STORED")
    monkeypatch.setenv("GEMINI_API_KEY", "ENVIRONMENT")
    assert native.load_gemini_key() == "ENVIRONMENT"
    monkeypatch.delenv("GEMINI_API_KEY")
    if os.name == "nt":
        assert native.load_gemini_key() == "STORED"


def test_windows_credential_structure_size():
    assert c.sizeof(native._Credential) == (80 if c.sizeof(c.c_void_p) == 8 else 52)
