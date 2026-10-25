"""Notepad observation and only reliable system launcher in Windows.

The ctypes standard library calls Win32 functions. All local resources
It is closed with finally. Only notepad.exe candidates from the current session are examined;
The title and document content are not read. The packet is authenticated via family/system.
Observation is a snapshot; does not guarantee a persistent target to the next GUI action.
Launch aids use the fixed Notepad target; There is no focus/shutdown.
"""

import ctypes as c
from ctypes import wintypes as w
from datetime import datetime, timezone
import ntpath
import os


class _ProcessEntry(c.Structure):
    """PROCESSENTRY32W memory layout; pointer size fits 32/64 bit Python."""
    _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("pid", w.DWORD),
                ("heap", c.c_size_t), ("module", w.DWORD), ("threads", w.DWORD),
                ("parent", w.DWORD), ("priority", w.LONG), ("flags", w.DWORD),
                ("name", w.WCHAR * 260)]


def _libraries():
    """Explicitly define Win32 ABI signatures; Prevent HANDLE from being truncated in 64 bit."""
    if os.name != "nt":
        raise NotImplementedError("Windows observation is unavailable")
    kernel = c.WinDLL("kernel32", use_last_error=True)
    user = c.WinDLL("user32", use_last_error=True)
    signatures = [
        (kernel.CreateToolhelp32Snapshot, [w.DWORD, w.DWORD], w.HANDLE),
        (kernel.Process32FirstW, [w.HANDLE, c.POINTER(_ProcessEntry)], w.BOOL),
        (kernel.Process32NextW, [w.HANDLE, c.POINTER(_ProcessEntry)], w.BOOL),
        (kernel.CloseHandle, [w.HANDLE], w.BOOL),
        (kernel.OpenProcess, [w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
        (kernel.WaitForSingleObject, [w.HANDLE, w.DWORD], w.DWORD),
        (kernel.GetCurrentProcessId, [], w.DWORD),
        (kernel.ProcessIdToSessionId, [w.DWORD, c.POINTER(w.DWORD)], w.BOOL),
        (kernel.QueryFullProcessImageNameW, [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)], w.BOOL),
        (kernel.GetWindowsDirectoryW, [w.LPWSTR, w.UINT], w.UINT),
        (kernel.GetSystemDirectoryW, [w.LPWSTR, w.UINT], w.UINT),
        (kernel.GetPackageFamilyName, [w.HANDLE, c.POINTER(w.UINT), w.LPWSTR], w.LONG),
        (kernel.GetProcessTimes, [w.HANDLE, *[c.POINTER(w.FILETIME)] * 4], w.BOOL),
        (user.IsWindowVisible, [w.HWND], w.BOOL),
        (user.IsIconic, [w.HWND], w.BOOL),
        (user.GetWindowThreadProcessId, [w.HWND, c.POINTER(w.DWORD)], w.DWORD),
    ]
    for function, arguments, result in signatures:
        function.argtypes, function.restype = arguments, result
    return kernel, user


def notepad_launcher():
    """Use Windows' system directory instead of variable PATH/cwd/environment.

    This path is chosen by the host; file/command is not received with the tool parameter.
    No alternative executable or installation is attempted in the missing launcher.
    """
    kernel, unused = _libraries()
    directory = c.create_unicode_buffer(32768)
    length = kernel.GetSystemDirectoryW(directory, len(directory))
    if not 0 < length < len(directory):
        raise OSError("System launcher location unavailable")
    executable = ntpath.join(directory.value, "notepad.exe")
    if not os.path.isfile(executable):
        raise OSError("Notepad launcher unavailable")
    return executable


def start_notepad(executable):
    """Pass the host-decoded EXE to Windows once; Don't consider the return as evidence of success.

    os.startfile uses the Windows ShellExecute path; cmd/PowerShell command
    or the user argument is not executed. External app longer than TaskVex
    can live; Here, the process code kill/exit is not waited for. real result
    It is further verified by apps.open with OS ID and window observation.
    """
    os.startfile(executable, operation="open", cwd=ntpath.dirname(executable))


def _check_cancel(cancel):
    """Convert cooperative cancellation outside C callback to Python exception."""
    if cancel.is_set():
        raise InterruptedError("Observation cancelled")


def _candidates(kernel, cancel):
    """Select only Notebook candidates from the process snapshot; moving other content."""
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)  # TH32CS_SNAPPROCESS
    if snapshot == c.c_void_p(-1).value or snapshot is None:
        raise OSError("Process snapshot unavailable")
    try:
        entry = _ProcessEntry()
        entry.dwSize = c.sizeof(entry)
        more = kernel.Process32FirstW(snapshot, c.byref(entry))
        candidates = []
        while more:
            _check_cancel(cancel)
            if entry.name.casefold() == "notepad.exe":
                candidates.append(entry.pid)
            more = kernel.Process32NextW(snapshot, c.byref(entry))
        if c.get_last_error() != 18:  # ERROR_NO_MORE_FILES: normal list end.
            raise OSError("Process enumeration incomplete")
        return candidates
    finally:
        kernel.CloseHandle(snapshot)


def _identity(kernel, pid, windows_directory):
    """The process name is a candidate; real image path/packet family decides.

    The return is the identity type and formation time. Second if PID is reused
    The formation time changes in reading; The old window mapping is removed from the result.
    Executable path or package name from user/model is not retrieved.
    """
    # SYNCHRONIZE is for 0 ms life control only; process is not stopped/does not wait.
    handle = kernel.OpenProcess(0x1000 | 0x100000, False, pid)
    if not handle:
        raise OSError("Process identity unavailable")
    try:
        image = c.create_unicode_buffer(32768)
        length = w.DWORD(len(image))
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, c.byref(length)):
            raise OSError("Process image unavailable")
        path = ntpath.normcase(ntpath.normpath(image.value))
        family = c.create_unicode_buffer(256)
        family_length = w.UINT(len(family))
        package_result = kernel.GetPackageFamilyName(handle, c.byref(family_length), family)
        if package_result not in (0, 15700):  # APPMODEL_ERROR_NO_PACKAGE
            raise OSError("Package identity unavailable")
        classic = {ntpath.normcase(ntpath.join(windows_directory, part, "notepad.exe"))
                   for part in ("", "System32", "SysWOW64")}
        if (package_result == 0 and family.value == "Microsoft.WindowsNotepad_8wekyb3d8bbwe"
                and ntpath.basename(path) == "notepad.exe"):
            identity = "microsoft_notepad_package"
        elif package_result == 15700 and path in classic:
            identity = "windows_system_notepad"
        else:
            return None
        if kernel.WaitForSingleObject(handle, 0) != 258:  # WAIT_TIMEOUT: still alive.
            raise OSError("Process exited or liveness unavailable")
        created, exited, cpu, user = (w.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle, c.byref(created), c.byref(exited), c.byref(cpu), c.byref(user)):
            raise OSError("Process time unavailable")
        return {"pid": pid, "identity": identity,
                "created": str((created.dwHighDateTime << 32) | created.dwLowDateTime)}
    finally:
        kernel.CloseHandle(handle)


def _windows(user, pids, cancel):
    """Bind the current desktop's top-level WS_VISIBLE windows to the PID.

    WS_VISIBLE, front/interaction It does not mean ready; in minimized window
    carries this flag. We don't read headlines. We don't miss exceptions from C callbacks.
    """
    callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    user.EnumWindows.argtypes, user.EnumWindows.restype = [callback_type, w.LPARAM], w.BOOL
    windows, errors = [], []

    def visit(hwnd, unused):
        try:
            if cancel.is_set():
                return False
            pid = w.DWORD()
            if user.GetWindowThreadProcessId(hwnd, c.byref(pid)) and pid.value in pids:
                if user.IsWindowVisible(hwnd):
                    windows.append({"hwnd": int(hwnd), "pid": pid.value,
                                    "minimized": bool(user.IsIconic(hwnd))})
            return True
        except Exception:
            errors.append(True)
            return False

    succeeded = user.EnumWindows(callback_type(visit), 0)
    _check_cancel(cancel)
    if not succeeded or errors:
        raise OSError("Window enumeration incomplete")
    return windows


def observe_notepad(cancel):
    """Return instant observation; converting incomplete review to definitive 'closed' result.

    Other sessions are excluded. If verification of single candidate access/identity fails
    complete=False. The proven positive finding can be maintained; negative finding
    It is null in incomplete scan. The task layer presents this partial result as FAILED,
    It does not stop the manager with UNKNOWN because of the read-only observation.
    """
    _check_cancel(cancel)
    kernel, user = _libraries()
    directory = c.create_unicode_buffer(32768)
    size = kernel.GetWindowsDirectoryW(directory, len(directory))
    session = w.DWORD()
    if not 0 < size < len(directory) or not kernel.ProcessIdToSessionId(kernel.GetCurrentProcessId(), c.byref(session)):
        raise OSError("Windows observation context unavailable")
    processes, complete = [], True
    for pid in _candidates(kernel, cancel):
        _check_cancel(cancel)
        try:
            target_session = w.DWORD()
            if not kernel.ProcessIdToSessionId(pid, c.byref(target_session)):
                raise OSError("Process session unavailable")
            if target_session.value != session.value:
                continue
            process = _identity(kernel, pid, directory.value)
            if process is not None:
                processes.append(process)
        except OSError:
            complete = False
    try:
        windows = _windows(user, {p["pid"] for p in processes}, cancel)
    except OSError:
        windows, complete = [], False
    # During observation shutdown/PID reuse confirmed old HWND
    # Don't let it count. Same pid + creation time + id should still match.
    stable = []
    for process in processes:
        _check_cancel(cancel)
        try:
            if _identity(kernel, process["pid"], directory.value) == process:
                stable.append(process)
            else:
                complete = False
        except OSError:
            complete = False
    stable_pids = {p["pid"] for p in stable}
    windows = [window for window in windows if window["pid"] in stable_pids]
    _check_cancel(cancel)
    return {"app_id": "notepad", "running": True if stable else False if complete else None,
            "visible_window": True if windows else False if complete else None,
            "processes": stable, "windows": windows, "complete": complete,
            "observed_at": datetime.now(timezone.utc).isoformat()}
