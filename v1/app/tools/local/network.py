"""Local network meters: Passive Windows field adapter that Telemetry calls.

Reads 64-bit byte counters of physical interfaces with GetIfTable2. Package,
IP/MAC, SSID or profile name is not output; There is no speed test. local gateway
The Wi-Fi quality adapter, which does not require ping and location, is called from the same instance.
The difference between the two examples is the traffic speed, not the maximum speed of the connection.
"""
import ctypes as c
from ctypes import wintypes as w
import os

from app.tools.local.network_quality import read_gateway, ping_gateway, wifi_signal


class _Guid(c.Structure):
    _fields_ = [('a', w.DWORD), ('b', w.WORD), ('d', w.WORD), ('tail', w.BYTE * 8)]


class _Row(c.Structure):
    """SDK layout of MIB_IF_ROW2; Alignment is maintained by ctypes."""
    _fields_ = [('luid', c.c_ulonglong), ('index', w.ULONG), ('guid', _Guid),
        ('alias', w.WCHAR * 257), ('description', w.WCHAR * 257),
        ('address_length', w.ULONG), ('address', w.BYTE * 32), ('permanent_address', w.BYTE * 32)] + [
        (name, w.ULONG) for name in ('mtu', 'type', 'tunnel', 'media', 'physical_media', 'access', 'direction')
    ] + [('flags', w.BYTE), ('oper_status', w.ULONG), ('admin_status', w.ULONG),
        ('media_state', w.ULONG), ('network_guid', _Guid), ('connection_type', w.ULONG)] + [
        (name, c.c_ulonglong) for name in ('tx_link', 'rx_link', 'rx_bytes', 'rx_unicast',
        'rx_nonunicast', 'rx_discards', 'rx_errors', 'rx_unknown', 'rx_unicast_bytes',
        'rx_multicast_bytes', 'rx_broadcast_bytes', 'tx_bytes', 'tx_unicast', 'tx_nonunicast',
        'tx_discards', 'tx_errors', 'tx_unicast_bytes', 'tx_multicast_bytes', 'tx_broadcast_bytes', 'queue')]


class _Table(c.Structure):
    _fields_ = [('count', w.ULONG), ('rows', _Row * 1)]


def _load_iphelper():
    if os.name != 'nt':
        raise OSError('Windows network counters unavailable')
    dll = c.WinDLL('iphlpapi', use_last_error=True)
    dll.GetIfTable2.argtypes, dll.GetIfTable2.restype = [c.POINTER(c.c_void_p)], w.ULONG
    dll.FreeMibTable.argtypes, dll.FreeMibTable.restype = [c.c_void_p], None
    return dll


def read_interfaces() -> list[dict]:
    """Read the table and leave it at finally; Exporting personal interface areas.

    Virtual/tunnel/loopback or filter interfaces, VPN and physical
    It is out of scope to avoid being counted twice in the layer. If resource fails []
    Instead of returning an error is given: unknown resource is not 'no connection'.
    """
    dll = _load_iphelper()
    table = c.c_void_p()
    if dll.GetIfTable2(c.byref(table)) != 0:
        raise OSError('Network table unavailable')
    try:
        if not table.value:
            raise OSError('Network table unavailable')
        count = c.cast(table, c.POINTER(_Table)).contents.count
        if count > 4096:
            raise OSError('Network table exceeds limit')
        rows = c.cast(table.value + _Table.rows.offset, c.POINTER(_Row))
        result = []
        for i in range(count):
            row = rows[i]
            if not row.flags & 1 or row.flags & 0x82 or row.type in (24, 131):
                continue
            result.append({'id': str(row.luid), 'up': None if row.oper_status == 4 else row.oper_status == 1 and row.media_state != 2,
                'kind': 'wifi' if row.type == 71 else 'ethernet' if row.type == 6 else 'other',
                'rx_bytes': row.rx_bytes, 'tx_bytes': row.tx_bytes,
                'index': row.index, 'guid': bytes(row.guid)})
        return result
    finally:
        dll.FreeMibTable(table)


class Network:
    """The previous example is used only under Telemetry lock; There is no additional tick."""
    def __init__(self, reader=None):
        self._reader = reader or read_interfaces
        self._previous = None
        self._quality_key = None
        self._quality_at = -float("inf")
        self._quality = {}

    def _sample_quality(self, now, active):
        """Limited quality query every ten seconds; Changing kart/rota deletes the old result."""
        if not active:
            self._quality_key = None
            return {
                "network_ping_ms": None, "network_ping_status": "unavailable" if active is None else "no_link",
                "network_wifi_signal": None, "network_wifi_status": "unavailable" if active is None else "not_connected",
                "network_quality_sampled_at": now}
        route_ok = True
        try:
            gateway = read_gateway(active)
        except (OSError, AttributeError):
            gateway, route_ok = None, False
        key = (tuple(sorted(row["id"] for row in active)), route_ok, gateway)
        if key != self._quality_key or now-self._quality_at >= 10:
            self._quality_key, self._quality_at = key, now
            self._quality = {**wifi_signal(active), **(ping_gateway(gateway) if gateway is not None else {
                "network_ping_ms": None, "network_ping_status": "no_gateway" if route_ok else "unavailable"}),
                "network_quality_sampled_at": now}
        return self._quality

    def sample(self, now: float) -> dict:
        """Divide byte difference by seconds; Speed ​​matching on reset/lost/changed device."""
        data = {'network_source': 'windows-iphelper', 'network_link': None, 'network_kind': None,
            'network_wifi_connected': None, 'network_receive_bps': None, 'network_send_bps': None}
        try:
            rows = self._reader()
        except (OSError, AttributeError):
            self._previous = None
            data.update(self._sample_quality(now, None))
            return data
        active = [row for row in rows if row['up']]
        data['network_link'] = True if active else None if any(row['up'] is None for row in rows) else False
        wifi = [row for row in rows if row['kind'] == 'wifi']
        data['network_wifi_connected'] = True if any(row['up'] for row in wifi) else None if any(row['up'] is None for row in wifi) else False
        kinds = {row['kind'] for row in active}
        data['network_kind'] = next(iter(kinds)) if len(kinds) == 1 else 'multiple' if kinds else None
        current = {row['id']: (row['rx_bytes'], row['tx_bytes']) for row in active}
        if self._previous is not None and current:
            before, old = self._previous
            elapsed = now - before
            # Subtracting old and new card counters from each other in a changing device cluster.
            if elapsed > 0 and current.keys() == old.keys():
                delta = [(current[key][i] - old[key][i]) for key in current for i in (0, 1)]
                if all(value >= 0 for value in delta):
                    data['network_receive_bps'] = sum(delta[::2]) / elapsed
                    data['network_send_bps'] = sum(delta[1::2]) / elapsed
        self._previous = (now, current)
        data.update(self._sample_quality(now, active if data['network_link'] is not None else None))
        return data
