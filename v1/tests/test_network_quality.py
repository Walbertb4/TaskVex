"""Try the quality adapter with fake Windows DLLs; No network packets are sent.

ICMP destination/duration, physical default route selection only, locationless Wi-Fi opcode,
The failed/incomplete/zero measurement and all handle/buffer closures are verified.
"""
import ctypes as c
from ctypes import wintypes as w
import pytest
from app.tools.local import network_quality as quality
from app.tools.local import network


class IpHelper:
    def __init__(self):
        self.rows = [quality._Route(destination=0, mask=0, gateway=0x0100000a, index=1, type=4, metric=10)]
        self.failure = ''
        self.status = 0
        self.rtt = 0
        self.closed = []
        self.target = None

    def GetIpForwardTable(self, buffer, size, ordered):
        assert ordered is False
        if not buffer:
            c.cast(size, c.POINTER(w.ULONG))[0] = 2000000 if self.failure == 'oversize' else 4096
            return 122
        if self.failure == 'resize': return 122
        c.cast(buffer, c.POINTER(w.DWORD))[0] = 10000 if self.failure == 'bounds' else len(self.rows)
        entries = c.cast(c.addressof(buffer)+4, c.POINTER(quality._Route))
        for i, row in enumerate(self.rows): entries[i] = row
        return 0

    def IcmpCreateFile(self):
        return c.c_void_p(-1).value if self.failure == 'open' else 123

    def IcmpSendEcho(self, handle, target, payload, length, options, reply, size, timeout):
        self.target = target
        assert handle == 123 and length == 7 and options is None
        assert bytes(payload)[:7] == b'TaskVex' and timeout == 250 and size == 256
        if self.failure == 'send': raise OSError('private error')
        if self.failure == 'timeout': return 0
        header = c.cast(reply, c.POINTER(quality._EchoHeader)).contents
        header.address = target+1 if self.failure == 'peer' else target
        header.status, header.rtt = self.status, self.rtt
        return 1

    def IcmpCloseHandle(self, handle): self.closed.append(handle)


def test_route_picks_lowest_metric_physical_default_and_keeps_address_private(monkeypatch):
    dll = IpHelper()
    dll.rows += [quality._Route(gateway=0x0200000a, index=2, type=4, metric=1),
        quality._Route(gateway=0x0300000a, index=1, type=4, metric=5),
        quality._Route(destination=1, gateway=0x0400000a, index=1, type=4, metric=0),
        quality._Route(gateway=0x0100007f, index=1, type=4, metric=0)]
    monkeypatch.setattr(quality, '_load_iphelper', lambda: dll)
    assert quality.read_gateway([{'index':1}]) == 0x0300000a
    assert quality.read_gateway([]) is None
    assert quality.read_gateway([{'index':3}]) is None


@pytest.mark.parametrize('failure', ['oversize', 'resize', 'bounds'])
def test_bad_route_buffer_never_pings(monkeypatch, failure):
    dll = IpHelper()
    dll.failure = failure
    monkeypatch.setattr(quality, '_load_iphelper', lambda: dll)
    with pytest.raises(OSError): quality.read_gateway([{'index':1}])
    assert dll.target is None


@pytest.mark.parametrize('failure,status,expected', [
    ('',0,'ok'), ('open',0,'unavailable'), ('send',0,'unavailable'),
    ('timeout',0,'timeout'), ('',11010,'timeout'), ('',11003,'unreachable'), ('peer',0,'unavailable')])
def test_ping_zero_error_timeout_and_always_close(monkeypatch, failure, status, expected):
    dll = IpHelper()
    dll.failure, dll.status = failure, status
    monkeypatch.setattr(quality, '_load_iphelper', lambda: dll)
    monkeypatch.setattr(quality.c, 'get_last_error', lambda:11010)
    result = quality.ping_gateway(0x0100000a)
    assert result['network_ping_status'] == expected
    assert result['network_ping_ms'] == (0 if expected == 'ok' else None)
    assert dll.closed == ([] if failure == 'open' else [123])
    assert 'private' not in str(result)


class Wlan:
    def __init__(self):
        self.headers = [quality._WifiHeader(quality=0), quality._WifiHeader(quality=80)]
        self.status = 0
        self.failure = ''
        self.calls = 0
        self.freed, self.closed = [], []

    def WlanOpenHandle(self, requested, reserved, version, handle):
        assert requested == 2 and reserved is None
        if self.failure == 'open': return 5
        c.cast(handle,c.POINTER(w.HANDLE))[0] = 321
        return 0

    def WlanQueryInterface(self, handle, guid, opcode, reserved, size, data, kind):
        assert opcode == 19 and reserved is None and kind is None
        header = self.headers[min(self.calls,1)]
        self.calls += 1
        if self.failure == 'raise': raise OSError('private WLAN detail')
        c.cast(size,c.POINTER(w.DWORD))[0] = 4 if self.failure == 'short' else c.sizeof(header)
        c.cast(data,c.POINTER(c.c_void_p))[0] = None if self.failure == 'null' else c.addressof(header)
        return self.status

    def WlanFreeMemory(self, data): self.freed.append(data.value)
    def WlanCloseHandle(self, handle, reserved): self.closed.append(handle.value)


def test_wifi_zero_and_weakest_connected_card_use_only_location_free_query(monkeypatch):
    dll = Wlan()
    monkeypatch.setattr(quality, '_load_wlan', lambda: dll)
    rows = [{'kind':'wifi','guid':bytes(16)}]*2
    result = quality.wifi_signal(rows)
    assert result == {'network_wifi_signal':0,'network_wifi_status':'ok'}
    assert len(dll.freed) == 2 and dll.closed == [321] and dll.calls == 2


@pytest.mark.parametrize('failure,status,expected', [
    ('open',0,'unavailable'), ('raise',0,'unavailable'), ('short',0,'unavailable'),
    ('null',0,'unavailable'), ('',5,'access_denied'), ('',87,'unsupported'), ('',50,'unsupported')])
def test_wifi_failures_have_no_location_fallback_and_close_resources(monkeypatch,failure,status,expected):
    dll = Wlan()
    dll.failure, dll.status = failure, status
    monkeypatch.setattr(quality, '_load_wlan', lambda:dll)
    result = quality.wifi_signal([{'kind':'wifi','guid':bytes(16)}])
    assert result['network_wifi_signal'] is None and result['network_wifi_status'] == expected
    assert dll.closed == ([] if failure == 'open' else [321])
    assert len(dll.freed) == (0 if failure in ('open','raise','null') else 1)
    assert dll.calls <= 1 and 'private' not in str(result)


def test_wifi_bad_quality_or_identity_is_not_fake_signal(monkeypatch):
    dll = Wlan()
    dll.headers[0].quality = 101
    monkeypatch.setattr(quality, '_load_wlan', lambda:dll)
    assert quality.wifi_signal([{'kind':'wifi','guid':bytes(16)}])['network_wifi_signal'] is None
    assert quality.wifi_signal([{'kind':'wifi'}])['network_wifi_signal'] is None
    assert quality.wifi_signal([{'kind':'ethernet'}])['network_wifi_status'] == 'not_connected'
    assert quality.wifi_signal([{'kind':'wifi','guid':bytes(16)}]*17)['network_wifi_signal'] is None


def test_quality_cache_route_change_failure_and_disconnect_do_not_retain_success(monkeypatch):
    rows = [{'id':'a','up':True,'kind':'wifi','rx_bytes':0,'tx_bytes':0}]
    gateway = [1]
    calls = []
    monkeypatch.setattr(network, 'read_gateway', lambda _:gateway[0])
    def ping(target):
        calls.append(target)
        return {'network_ping_ms':0 if target == 1 else None,'network_ping_status':'ok' if target == 1 else 'timeout'}
    monkeypatch.setattr(network, 'ping_gateway', ping)
    monkeypatch.setattr(network, 'wifi_signal', lambda _:{'network_wifi_signal':75,'network_wifi_status':'ok'})
    meter = network.Network(lambda:rows)
    assert meter.sample(0)['network_ping_ms'] == 0
    cached = meter.sample(3)
    assert cached['network_quality_sampled_at'] == 0 and calls == [1]
    meter.sample(10)
    assert calls == [1,1]
    gateway[0] = 2
    changed = meter.sample(12)
    assert changed['network_ping_ms'] is None and changed['network_ping_status'] == 'timeout'
    assert calls == [1,1,2]
    rows.clear()
    stopped = meter.sample(14)
    assert stopped['network_ping_ms'] is None and stopped['network_wifi_signal'] is None
    assert stopped['network_ping_status'] == 'no_link' and calls == [1,1,2]


def test_unavailable_dlls_are_controlled(monkeypatch):
    def unavailable(): raise OSError('private detail')
    monkeypatch.setattr(quality, '_load_iphelper', unavailable)
    monkeypatch.setattr(quality, '_load_wlan', unavailable)
    assert quality.ping_gateway(1)['network_ping_status'] == 'unavailable'
    assert quality.wifi_signal([{'kind':'wifi','guid':bytes(16)}])['network_wifi_signal'] is None
