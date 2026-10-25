"""Try checking the identity, resource closure and race limits of Win32 monitoring.

Mock APIs are used only in testing; real Notepad does not open/close.
The actual machine observation is in the separate acceptance report. ctypes callback Windows ABI
These low-level tests are skipped outside of Windows because they require
"""

import ctypes as c
import os
from threading import Event
from types import SimpleNamespace

import pytest

from app.tools.local import windows_apps as native


pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows ABI tests")


class Kernel:
    """Check identity API responses; Watch each handle taken close."""
    def __init__(self):
        self.closed = []
        self.image = r"C:\Program Files\WindowsApps\Notepad\Notepad.exe"
        self.family = "Microsoft.WindowsNotepad_8wekyb3d8bbwe"
        self.package_code = 0
        self.fail = ""

    def OpenProcess(self, access, inherit, pid):
        assert access == 0x101000 and inherit is False
        return 0 if self.fail == "open" else pid

    def CloseHandle(self, handle):
        self.closed.append(handle)
        return True

    def WaitForSingleObject(self, handle, timeout):
        assert timeout == 0
        return 0 if self.fail == "exited" else 258

    def QueryFullProcessImageNameW(self, handle, flags, image, length):
        image.value = self.image
        return self.fail != "image"

    def GetPackageFamilyName(self, handle, length, family):
        family.value = self.family
        return self.package_code

    def GetProcessTimes(self, handle, created, exited, cpu, user):
        created._obj.dwHighDateTime = 1
        created._obj.dwLowDateTime = 42
        return self.fail != "time"

    def GetWindowsDirectoryW(self, value, length):
        value.value = r"C:\Windows"
        return len(value.value)

    def GetSystemDirectoryW(self, value, length):
        value.value = r"C:\Windows\System32"
        return len(value.value)

    def GetCurrentProcessId(self):
        return 999

    def ProcessIdToSessionId(self, pid, session):
        session._obj.value = 2 if pid == 20 else 1
        return True


def user_api(*, visible=True, fail=False):
    """Offer the only pair of HWND/PIDs with no header information; C callback is actually called."""
    def enumerate_windows(callback, unused):
        return bool(callback(101, 0)) and not fail
    def owner(hwnd, pid):
        pid._obj.value = 10
        return 1
    return SimpleNamespace(EnumWindows=enumerate_windows, GetWindowThreadProcessId=owner,
                           IsWindowVisible=lambda hwnd: visible, IsIconic=lambda hwnd: False)


@pytest.mark.parametrize("identity", ["package", "classic", "untrusted", "wrong-package", "wrong-exe"])
def test_identity_requires_os_package_or_exact_system_path_and_closes_handle(identity):
    kernel = Kernel()
    if identity == "classic":
        kernel.image, kernel.package_code = r"C:\Windows\System32\notepad.exe", 15700
    elif identity == "untrusted":
        kernel.image, kernel.package_code = r"C:\Users\someone\notepad.exe", 15700
    elif identity == "wrong-package":
        kernel.family = "Other.Notepad_other"
    elif identity == "wrong-exe":
        kernel.image = r"C:\Package\something.exe"
    result = native._identity(kernel, 10, r"C:\Windows")
    assert kernel.closed == [10]
    if identity in {"package", "classic"}:
        assert result["pid"] == 10 and result["created"] == str((1 << 32) | 42)
    else:
        assert result is None


@pytest.mark.parametrize("failure", ["open", "image", "time", "package", "exited"])
def test_identity_errors_do_not_leak_open_handles(failure):
    kernel = Kernel()
    kernel.fail = failure
    if failure == "package":
        kernel.package_code = 5
    with pytest.raises(OSError):
        native._identity(kernel, 10, r"C:\Windows")
    assert kernel.closed == ([] if failure == "open" else [10])


@pytest.mark.parametrize("mode", ["running", "closed", "hidden", "denied", "reuse", "enum-error", "other-session"])
def test_observation_distinguishes_absence_unavailable_and_pid_reuse(monkeypatch, mode):
    kernel = Kernel()
    user = user_api(visible=mode != "hidden", fail=mode == "enum-error")
    monkeypatch.setattr(native, "_libraries", lambda: (kernel, user))
    monkeypatch.setattr(native, "_candidates", lambda kernel, cancel: [] if mode == "closed" else [20] if mode == "other-session" else [10])
    real_identity = native._identity
    calls = []
    def identity(kernel, pid, directory):
        calls.append(pid)
        if mode == "denied":
            raise OSError("Access denied")
        value = real_identity(kernel, pid, directory)
        if mode == "reuse" and len(calls) == 2:
            value["created"] = "different-process"
        return value
    monkeypatch.setattr(native, "_identity", identity)
    result = native.observe_notepad(Event())
    complete = mode in {"running", "closed", "hidden", "other-session"}
    assert result["complete"] is complete
    assert result["running"] is (True if mode in {"running", "hidden", "enum-error"} else False if complete else None)
    assert result["visible_window"] is (True if mode == "running" else False if complete else None)
    assert bool(result["windows"]) is (mode == "running")
    assert "title" not in str(result) and "C:\\" not in str(result)
    if mode == "other-session":
        assert calls == []


def test_snapshot_filters_name_and_closes_on_error_and_cancellation(monkeypatch):
    for stop in ("normal", "error", "cancel"):
        kernel = Kernel()
        cancel = Event()
        def first(snapshot, entry):
            entry._obj.name, entry._obj.pid = "NOTEPAD.EXE", 10
            if stop == "cancel":
                cancel.set()
            return True
        kernel.CreateToolhelp32Snapshot = lambda flags, pid: 55
        kernel.Process32FirstW = first
        kernel.Process32NextW = lambda snapshot, entry: False
        monkeypatch.setattr(c, "get_last_error", lambda: 18 if stop == "normal" else 5)
        if stop == "normal":
            assert native._candidates(kernel, cancel) == [10]
        else:
            with pytest.raises(InterruptedError if stop == "cancel" else OSError):
                native._candidates(kernel, cancel)
        assert kernel.closed == [55]


def test_window_callback_cancellation_and_exception_are_reported():
    cancel = Event()
    cancel.set()
    with pytest.raises(InterruptedError):
        native._windows(user_api(), {10}, cancel)
    user = user_api()
    def broken(hwnd):
        raise OSError("Could not inspect window")
    user.IsWindowVisible = broken
    with pytest.raises(OSError):
        native._windows(user, {10}, Event())


@pytest.mark.parametrize("mode", ["valid", "missing", "bad-directory"])
def test_launcher_uses_only_windows_system_directory(monkeypatch, mode):
    kernel, checked = Kernel(), []
    if mode == "bad-directory":
        kernel.GetSystemDirectoryW = lambda value, length: 0
    def exists(path):
        checked.append(path)
        return mode != "missing"
    monkeypatch.setattr(native, "_libraries", lambda: (kernel, None))
    monkeypatch.setattr(native, "os", SimpleNamespace(path=SimpleNamespace(isfile=exists)))
    if mode == "valid":
        assert native.notepad_launcher() == r"C:\Windows\System32\notepad.exe"
    else:
        with pytest.raises(OSError):
            native.notepad_launcher()
    assert checked == ([] if mode == "bad-directory" else [r"C:\Windows\System32\notepad.exe"])


def test_native_launch_has_no_user_command_arguments(monkeypatch):
    calls = []
    monkeypatch.setattr(native, "os", SimpleNamespace(startfile=lambda *args, **kw: calls.append((args, kw))))
    native.start_notepad(r"C:\Windows\System32\notepad.exe")
    assert calls == [((r"C:\Windows\System32\notepad.exe",),
                      {"operation": "open", "cwd": r"C:\Windows\System32"})]
