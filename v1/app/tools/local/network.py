"""Yerel ağ sayaçları: Telemetry'nin çağırdığı pasif Windows alan adaptörü.

GetIfTable2 ile fiziksel arabirimlerin 64 bit byte sayaçlarını okur. Paket,
IP/MAC, SSID, profil adı veya uzak sunucu sorgulanmaz; ping/hız testi yapılmaz.
İki örnek arasındaki fark trafik hızıdır, bağlantının azami hızı değildir.
"""
import ctypes as c
from ctypes import wintypes as w
import os


class _Guid(c.Structure):
    _fields_ = [('a', w.DWORD), ('b', w.WORD), ('d', w.WORD), ('tail', w.BYTE * 8)]


class _Row(c.Structure):
    """MIB_IF_ROW2'nin SDK yerleşimi; hizalama ctypes tarafından korunur."""
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
    """Tabloyu oku ve finally'de bırak; kişisel arabirim alanlarını dışarı verme.

    Sanal/tünel/loopback veya filtre arabirimleri, aynı paketin VPN ve fiziksel
    katmanda iki defa sayılmaması için kapsam dışıdır. Kaynak başarısızsa []
    dönmek yerine hata verilir: bilinmeyen kaynak 'bağlantı yok' değildir.
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
                'rx_bytes': row.rx_bytes, 'tx_bytes': row.tx_bytes})
        return result
    finally:
        dll.FreeMibTable(table)


class Network:
    """Önceki örnek yalnız Telemetry kilidi altında kullanılır; ek tick yoktur."""
    def __init__(self, reader=None):
        self._reader = reader or read_interfaces
        self._previous = None

    def sample(self, now: float) -> dict:
        """Byte farkını saniyeye böl; reset/kayıp/değişen cihazda hız uydurma."""
        data = {'network_source': 'windows-iphelper', 'network_link': None, 'network_kind': None,
            'network_wifi_connected': None, 'network_receive_bps': None, 'network_send_bps': None}
        try:
            rows = self._reader()
        except (OSError, AttributeError):
            self._previous = None
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
            # Değişen cihaz kümesinde eski ve yeni kart sayaçlarını birbirinden çıkarma.
            if elapsed > 0 and current.keys() == old.keys():
                delta = [(current[key][i] - old[key][i]) for key in current for i in (0, 1)]
                if all(value >= 0 for value in delta):
                    data['network_receive_bps'] = sum(delta[::2]) / elapsed
                    data['network_send_bps'] = sum(delta[1::2]) / elapsed
        self._previous = (now, current)
        return data
