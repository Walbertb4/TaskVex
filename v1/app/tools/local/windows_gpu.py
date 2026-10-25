"""Manufacturer-independent GPU usage: Windows PDH performance counters.

It is based on the most GPU intensive engine like Task Manager. Your processes are the same
Their use in the engine is summed up; No different engines or cards are collected.
The first sample is the reference, the percentage occurs in the next sample. Temperature/VRAM capacity
This does not come from the meter; unpredictable. No processes or threads are opened outside the DLL.
"""
import ctypes as c
from ctypes import wintypes as w
import math
import os
import re
from weakref import finalize


class _Number(c.Union):
    _fields_ = [('longValue', w.LONG), ('doubleValue', c.c_double), ('largeValue', c.c_longlong)]


class _Value(c.Structure):
    _fields_ = [('status', w.DWORD), ('number', _Number)]


class _Item(c.Structure):
    _fields_ = [('name', w.LPWSTR), ('value', _Value)]


def _load_pdh():
    """Also use English counter path on localized Windows."""
    if os.name != 'nt':
        raise OSError('Windows counters unavailable')
    dll = c.WinDLL('pdh', use_last_error=True)
    for name, args in (
        ('PdhOpenQueryW', [w.LPCWSTR, c.c_size_t, c.POINTER(w.HANDLE)]),
        ('PdhAddEnglishCounterW', [w.HANDLE, w.LPCWSTR, c.c_size_t, c.POINTER(w.HANDLE)]),
        ('PdhCollectQueryData', [w.HANDLE]),
        ('PdhGetFormattedCounterArrayW', [w.HANDLE, w.DWORD, c.POINTER(w.DWORD), c.POINTER(w.DWORD), c.c_void_p]),
        ('PdhCloseQuery', [w.HANDLE]),
    ):
        fn = getattr(dll, name)
        fn.argtypes, fn.restype = args, w.LONG
    return dll


def aggregate_engines(items) -> list[dict]:
    """Separate ID hardware/engine from PDH instance name; The process ID does not come out.

    If two processes are 20% + 30% in the same engine, the engine is 50%. 40% of another engine
    this is not added: card usage remains 50%. Faulty/incomplete samples are non-zero.
    """
    engines = {}
    for name, value in items:
        match = re.fullmatch(r'pid_\d+_(luid_0x[0-9a-f]+_0x[0-9a-f]+_phys_\d+)_eng_(\d+)_engtype_.+', name, re.I)
        if not match or not math.isfinite(value) or value < 0:
            continue
        key = (match[1].lower(), match[2])
        engines[key] = engines.get(key, 0.0) + value
    devices = {}
    for (adapter, _), value in engines.items():
        devices[adapter] = max(devices.get(adapter, 0.0), min(100.0, value))
    return [{'id': adapter, 'utilization_percent': round(value, 1)} for adapter, value in sorted(devices.items())]


class WindowsGpu:
    """PDH query linked to a single Telemetry owner; close leaves all counters.

    The terminator also uses the handle for short-lived core uses outside the window.
    leaves. After the error, the query is closed; The next reading starts with the new reference.
    """
    def __init__(self):
        self._dll = None
        self._query = w.HANDLE()
        self._counter = w.HANDLE()
        self._cleanup = None

    def close(self):
        if self._cleanup is not None:
            self._cleanup()
        self._cleanup = None
        self._dll = None
        self._query, self._counter = w.HANDLE(), w.HANDLE()

    def __call__(self) -> dict:
        report = {'gpu_source': 'windows-pdh', 'gpu_status': 'unavailable', 'gpu_devices': []}
        try:
            if self._dll is None:
                dll = _load_pdh()
                if dll.PdhOpenQueryW(None, 0, c.byref(self._query)) != 0:
                    return report
                self._cleanup = finalize(self, dll.PdhCloseQuery, self._query)
                self._dll = dll
                if dll.PdhAddEnglishCounterW(self._query, r'\GPU Engine(*)\Utilization Percentage', 0, c.byref(self._counter)) != 0:
                    self.close()
                    return report
                if dll.PdhCollectQueryData(self._query) != 0:
                    self.close()
                    return report
                return {**report, 'gpu_status': 'warming_up'}
            dll = self._dll
            if dll.PdhCollectQueryData(self._query) != 0:
                raise OSError('GPU collection unavailable')
            size, count = w.DWORD(), w.DWORD()
            status = dll.PdhGetFormattedCounterArrayW(self._counter, 0x200, c.byref(size), c.byref(count), None)
            # Unlimited memory allocation although the number Size/instance comes from the native API.
            if status & 0xffffffff != 0x800007D2 or not 0 < size.value <= 4194304:
                raise OSError('GPU counters unavailable')
            capacity = size.value
            buffer = c.create_string_buffer(capacity)
            status = dll.PdhGetFormattedCounterArrayW(self._counter, 0x200, c.byref(size), c.byref(count), buffer)
            if status != 0 or count.value * c.sizeof(_Item) > capacity:
                raise OSError('GPU counter array changed')
            items = c.cast(buffer, c.POINTER(_Item))
            devices = aggregate_engines((items[i].name, items[i].value.number.doubleValue)
                for i in range(count.value) if items[i].value.status in (0, 1) and items[i].name)
            return {**report, 'gpu_status': 'ok' if devices else 'unavailable', 'gpu_devices': devices}
        except (OSError, AttributeError):
            self.close()
            return report
