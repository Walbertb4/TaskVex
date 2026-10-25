"""Windows adapters for network quality; The cache and instance owner is Network.

The ping target is only the OS's IPv4 default gateway for the active physical card.
Single ICMP request waits 250 ms; an internet/speed test or free target tool
It is not. The Wi-Fi query uses opcode 19, which does not include location-sensitive fields;
It doesn't fall into the old current_connection query. IP/SSID/MAC does not carry over to results.
"""
import ctypes as c
from ctypes import wintypes as w
import os


class _Route(c.Structure):
    _fields_ = [(name, w.DWORD) for name in ('destination', 'mask', 'policy', 'gateway',
        'index', 'type', 'protocol', 'age', 'as_number', 'metric', 'metric2', 'metric3', 'metric4', 'metric5')]


class _EchoHeader(c.Structure):
    """Common initial fields of 32/64 bit response; native pointer fields are not read."""
    _fields_ = [('address', w.DWORD), ('status', w.DWORD), ('rtt', w.DWORD)]


class _WifiHeader(c.Structure):
    """Fixed header of WLAN_REALTIME_CONNECTION_QUALITY; The link string is not read."""
    _fields_ = [('phy', w.ULONG), ('quality', w.ULONG), ('rx_rate', w.ULONG),
        ('tx_rate', w.ULONG), ('mlo', w.BOOL), ('link_count', w.ULONG)]


def _load_iphelper():
    if os.name != 'nt': raise OSError('Windows network quality unavailable')
    dll = c.WinDLL('iphlpapi', use_last_error=True)
    for name, args, result in (
        ('GetIpForwardTable', [c.c_void_p, c.POINTER(w.ULONG), w.BOOL], w.DWORD),
        ('IcmpCreateFile', [], w.HANDLE),
        ('IcmpCloseHandle', [w.HANDLE], w.BOOL),
        ('IcmpSendEcho', [w.HANDLE, w.DWORD, c.c_void_p, w.WORD, c.c_void_p, c.c_void_p, w.DWORD, w.DWORD], w.DWORD),
    ):
        fn = getattr(dll, name)
        fn.argtypes, fn.restype = args, result
    return dll


def read_gateway(active: list[dict]) -> int | None:
    """Lowest metric physical IPv4 default route; The raw address is only in RAM."""
    indices = {row.get('index') for row in active if row.get('index') is not None}
    if not indices: return None
    dll = _load_iphelper()
    size = w.ULONG()
    if dll.GetIpForwardTable(None, c.byref(size), False) != 122 or not 4 <= size.value <= 1048576:
        raise OSError('Route table unavailable')
    capacity = size.value
    buffer = c.create_string_buffer(capacity)
    if dll.GetIpForwardTable(buffer, c.byref(size), False) != 0:
        raise OSError('Route table changed')
    count = c.cast(buffer, c.POINTER(w.DWORD))[0]
    if 4 + count * c.sizeof(_Route) > capacity:
        raise OSError('Route table exceeds buffer')
    rows = c.cast(c.addressof(buffer) + 4, c.POINTER(_Route))
    choices = []
    for i in range(count):
        row = rows[i]
        first_octet = row.gateway & 255
        if row.destination == 0 and row.mask == 0 and row.index in indices and row.type == 4 and 0 < first_octet < 224 and first_octet != 127:
            choices.append((row.metric, row.index, row.gateway))
    return min(choices)[2] if choices else None


def ping_gateway(gateway: int) -> dict:
    """Single fixed payload to local target; timeout is not the absolute absence of access."""
    report = {'network_ping_ms': None, 'network_ping_status': 'unavailable'}
    handle = None
    dll = None
    try:
        dll = _load_iphelper()
        handle = dll.IcmpCreateFile()
        if handle in (None, 0, c.c_void_p(-1).value): return report
        payload = c.create_string_buffer(b'TaskVex')
        reply = c.create_string_buffer(256)
        count = dll.IcmpSendEcho(handle, gateway, payload, 7, None, reply, len(reply), 250)
        if not count:
            return {**report, 'network_ping_status': 'timeout' if c.get_last_error() == 11010 else 'unavailable'}
        header = c.cast(reply, c.POINTER(_EchoHeader)).contents
        if header.status == 11010: return {**report, 'network_ping_status': 'timeout'}
        if header.status != 0: return {**report, 'network_ping_status': 'unreachable'}
        if header.address != gateway: return report
        return {'network_ping_ms': header.rtt, 'network_ping_status': 'ok'}
    except (OSError, AttributeError):
        return report
    finally:
        if dll is not None and handle not in (None, 0, c.c_void_p(-1).value): dll.IcmpCloseHandle(handle)


def _load_wlan():
    if os.name != 'nt': raise OSError('Windows Wi-Fi quality unavailable')
    dll = c.WinDLL('wlanapi', use_last_error=True)
    for name, args, result in (
        ('WlanOpenHandle', [w.DWORD, c.c_void_p, c.POINTER(w.DWORD), c.POINTER(w.HANDLE)], w.DWORD),
        ('WlanCloseHandle', [w.HANDLE, c.c_void_p], w.DWORD),
        ('WlanFreeMemory', [c.c_void_p], None),
        ('WlanQueryInterface', [w.HANDLE, c.c_void_p, w.DWORD, c.c_void_p, c.POINTER(w.DWORD), c.POINTER(c.c_void_p), c.c_void_p], w.DWORD),
    ):
        fn = getattr(dll, name)
        fn.argtypes, fn.restype = args, result
    return dll


def wifi_signal(active: list[dict]) -> dict:
    """Lowest signal percentage of connected Wi-Fi cards; Location permission is not requested.

    Hiding the missing query in multiple cards and presenting the remaining card as the whole system.
    Each response memory and client handle is released at each exit.
    """
    report = {'network_wifi_signal': None, 'network_wifi_status': 'unavailable'}
    cards = [row for row in active if row['kind'] == 'wifi']
    if not cards: return {**report, 'network_wifi_status': 'not_connected'}
    if len(cards) > 16 or any(not isinstance(row.get('guid'), bytes) or len(row['guid']) != 16 for row in cards): return report
    handle = w.HANDLE()
    opened = False
    dll = None
    try:
        dll = _load_wlan()
        version = w.DWORD()
        if dll.WlanOpenHandle(2, None, c.byref(version), c.byref(handle)) != 0: return report
        opened = True
        values = []
        for row in cards:
            guid = c.create_string_buffer(row['guid'])
            size, data = w.DWORD(), c.c_void_p()
            try:
                status = dll.WlanQueryInterface(handle, guid, 19, None, c.byref(size), c.byref(data), None)
                if status != 0:
                    return {**report, 'network_wifi_status': 'access_denied' if status == 5 else 'unsupported' if status in (50, 87, 120) else 'unavailable'}
                if not data.value or not c.sizeof(_WifiHeader) <= size.value <= 65536: return report
                quality = c.cast(data, c.POINTER(_WifiHeader)).contents.quality
                if quality > 100: return report
                values.append(quality)
            finally:
                if data.value: dll.WlanFreeMemory(data)
        return {'network_wifi_signal': min(values), 'network_wifi_status': 'ok'}
    except (OSError, AttributeError):
        return report
    finally:
        if opened and dll is not None: dll.WlanCloseHandle(handle, None)
