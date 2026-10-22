"""Windows'ta Not Defteri gözlemi ve yalnız güvenilir sistem başlatıcısı.

ctypes standart kütüphanesi Win32 işlevlerini çağırır. Bütün yerel kaynaklar
finally ile kapatılır. Yalnız geçerli oturumdaki notepad.exe adayları incelenir;
başlık ve belge içeriği okunmaz. Paket ailesi/sistem yolu ile kimlik doğrulanır.
Gözlem bir anlık görüntüdür; sonraki GUI eylemine kalıcı hedef garantisi vermez.
Başlatma yardımcıları sabit Not Defteri hedefini kullanır; odaklama/kapatma yoktur.
"""

import ctypes as c
from ctypes import wintypes as w
from datetime import datetime, timezone
import ntpath
import os


class _ProcessEntry(c.Structure):
    """PROCESSENTRY32W bellek düzeni; pointer boyutu 32/64 bit Python'a uyar."""
    _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("pid", w.DWORD),
                ("heap", c.c_size_t), ("module", w.DWORD), ("threads", w.DWORD),
                ("parent", w.DWORD), ("priority", w.LONG), ("flags", w.DWORD),
                ("name", w.WCHAR * 260)]


def _libraries():
    """Win32 ABI imzalarını açık tanımla; HANDLE'ın 64 bitte kırpılmasını önle."""
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
    """PATH/cwd/ortam değişkeni yerine Windows'un sistem dizinini kullan.

    Bu yol host tarafından seçilir; araç parametresiyle dosya/komut alınmaz.
    Eksik başlatıcıda alternatif executable veya kurulum denemesi yapılmaz.
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
    """Host'un çözdüğü EXE'yi Windows'a bir kez ilet; dönüşü başarı kanıtı sayma.

    os.startfile Windows ShellExecute yolunu kullanır; cmd/PowerShell komutu
    veya kullanıcı argümanı çalıştırılmaz. Harici uygulama TaskVex'ten uzun
    yaşayabilir; burada süreç öldürme/çıkış kodu bekleme yapılmaz. Gerçek sonuç
    apps.open tarafından OS kimliği ve pencere gözlemiyle ayrıca doğrulanır.
    """
    os.startfile(executable, operation="open", cwd=ntpath.dirname(executable))


def _check_cancel(cancel):
    """C callback'i dışında kooperatif iptali Python istisnasına çevir."""
    if cancel.is_set():
        raise InterruptedError("Observation cancelled")


def _candidates(kernel, cancel):
    """Süreç snapshot'ından yalnız Not Defteri adaylarını seç; başka içerik taşıma."""
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
        if c.get_last_error() != 18:  # ERROR_NO_MORE_FILES: normal liste sonu.
            raise OSError("Process enumeration incomplete")
        return candidates
    finally:
        kernel.CloseHandle(snapshot)


def _identity(kernel, pid, windows_directory):
    """Süreç adı adaydır; gerçek image yolu/paket ailesi karar verir.

    Dönüş kimlik türü ve oluşum zamanıdır. PID yeniden kullanılmışsa ikinci
    okumada oluşum zamanı değişir; eski pencere eşlemesi sonuçtan çıkarılır.
    Kullanıcı/modelden executable yolu veya paket adı alınmaz.
    """
    # SYNCHRONIZE yalnız 0 ms yaşam kontrolü içindir; süreç durdurulmaz/bekletilmez.
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
        if kernel.WaitForSingleObject(handle, 0) != 258:  # WAIT_TIMEOUT: hâlâ canlı.
            raise OSError("Process exited or liveness unavailable")
        created, exited, cpu, user = (w.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle, c.byref(created), c.byref(exited), c.byref(cpu), c.byref(user)):
            raise OSError("Process time unavailable")
        return {"pid": pid, "identity": identity,
                "created": str((created.dwHighDateTime << 32) | created.dwLowDateTime)}
    finally:
        kernel.CloseHandle(handle)


def _windows(user, pids, cancel):
    """Geçerli desktop'un üst seviye WS_VISIBLE pencerelerini PID'ye bağla.

    WS_VISIBLE, önde/etkileşime hazır demek değildir; küçültülmüş pencere de
    bu bayrağı taşır. Başlık okumayız. C callback içinden istisna kaçırmayız.
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
    """Anlık gözlemi döndür; eksik incelemeyi kesin 'kapalı' sonucuna çevirme.

    Başka oturumlar dışlanır. Tek adayın erişim/kimlik doğrulaması başarısızsa
    complete=False olur. Kanıtlanan pozitif bulgu korunabilir; negatif bulgu
    eksik taramada null'dır. Görev katmanı bu kısmi sonucu FAILED olarak sunar,
    salt okunur gözlem yüzünden manager'ı UNKNOWN ile durdurmaz.
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
    # Gözlem sırasında kapanma/PID yeniden kullanımı eski HWND'yi doğrulanmış
    # saydırmasın. Aynı pid + oluşum zamanı + kimlik hâlâ eşleşmeli.
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
