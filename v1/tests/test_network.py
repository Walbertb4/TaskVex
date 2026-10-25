"""Try passive network examples with a fake Windows table; internet is not used.

64-bit counters, initial/zero/reset/device replacement and memory release are verified.
It is checked separately that the model and native UI read the same Telemetry instance.
"""
import ctypes as c
from ctypes import wintypes as w
import pytest
from app.tools.local import network
from app.tools.local.telemetry import Telemetry
from test_gemini import transport, reply, call


def row(identity='a', *, up=True, kind='wifi', rx=100, tx=50):
    return {'id': identity, 'up': up, 'kind': kind, 'rx_bytes': rx, 'tx_bytes': tx}


def test_interval_zero_64_bit_counters_and_no_private_names():
    rows = [row(rx=2**40, tx=2**41)]
    meter = network.Network(lambda: rows)
    first = meter.sample(0)
    assert first['network_link'] is True and first['network_kind'] == 'wifi'
    assert first['network_wifi_connected'] is True and first['network_receive_bps'] is None
    zero = meter.sample(2)
    assert zero['network_receive_bps'] == 0 and zero['network_send_bps'] == 0
    rows[:] = [row(rx=2**40+1000, tx=2**41+200)]
    sample = meter.sample(4)
    assert sample['network_receive_bps'] == 500 and sample['network_send_bps'] == 100
    assert not any(key in sample for key in ('ssid', 'ip', 'mac', 'alias'))


@pytest.mark.parametrize('changed', [row('b'), row(rx=0), row(tx=0), row(up=False)])
def test_counter_reset_disconnection_or_adapter_change_is_not_speed(changed):
    rows = [row()]
    meter = network.Network(lambda: rows)
    meter.sample(0)
    rows[:] = [changed]
    sample = meter.sample(2)
    assert sample['network_receive_bps'] is None and sample['network_send_bps'] is None
    assert sample['network_link'] is changed['up']
    # The next constant example is true zero if the connection is still open.
    assert meter.sample(4)['network_receive_bps'] == (0 if changed['up'] else None)


def test_multiple_hardware_links_sum_traffic_and_missing_source_resets_baseline():
    rows = [row(), row('b', kind='ethernet')]
    def read():
        if rows is None: raise OSError('private OS failure')
        return rows
    meter = network.Network(read)
    assert meter.sample(0)['network_kind'] == 'multiple'
    rows = [row(rx=300, tx=70), row('b', kind='ethernet', rx=500, tx=90)]
    sample = meter.sample(2)
    assert sample['network_receive_bps'] == 300 and sample['network_send_bps'] == 30
    rows = None
    lost = meter.sample(4)
    assert lost['network_link'] is None and 'private' not in str(lost)
    rows = [row()]
    assert meter.sample(6)['network_receive_bps'] is None


def test_no_hardware_and_nonpositive_interval_do_not_invent_rates():
    meter = network.Network(lambda: [])
    data = meter.sample(0)
    assert data['network_link'] is False and data['network_wifi_connected'] is False
    assert data['network_receive_bps'] is None
    meter = network.Network(lambda: [row()])
    meter.sample(5)
    assert meter.sample(5)['network_receive_bps'] is None


class Table(c.Structure):
    _fields_ = [('count', w.ULONG), ('rows', network._Row * 6)]


class IpHelper:
    def __init__(self):
        self.table = Table()
        self.table.count = 6
        self.failed = False
        self.freed = []
        for i, entry in enumerate(self.table.rows):
            entry.luid, entry.type, entry.flags = i+1, 71, 1
            entry.oper_status, entry.media_state = 1, 1
            entry.rx_bytes, entry.tx_bytes = 2**40, 2**41
            entry.alias = 'Private adapter name'
        self.table.rows[1].flags = 0       # VPN/virtual interface.
        self.table.rows[2].flags = 3       # Hardware + filtre.
        self.table.rows[3].flags = 129     # Hardware + endpoint.
        self.table.rows[4].type = 24       # Loopback.
        self.table.rows[5].oper_status = 2

    def GetIfTable2(self, pointer):
        if self.failed: return 5
        c.cast(pointer, c.POINTER(c.c_void_p))[0] = c.addressof(self.table)
        return 0

    def FreeMibTable(self, pointer):
        self.freed.append(pointer.value)


def test_windows_table_abi_filters_and_memory_release(monkeypatch):
    assert c.sizeof(network._Row) == 1352 and network._Table.rows.offset == 8
    dll = IpHelper()
    monkeypatch.setattr(network, '_load_iphelper', lambda: dll)
    result = network.read_interfaces()
    assert len(result) == 2 and result[0]['rx_bytes'] == 2**40
    assert result[0]['up'] is True and result[1]['up'] is False
    assert 'Private' not in str(result) and dll.freed == [c.addressof(dll.table)]


@pytest.mark.parametrize('failure', ['api', 'bounds'])
def test_failed_table_and_invalid_count_free_owned_memory(monkeypatch, failure):
    dll = IpHelper()
    dll.failed = failure == 'api'
    if failure == 'bounds': dll.table.count = 4097
    monkeypatch.setattr(network, '_load_iphelper', lambda: dll)
    with pytest.raises(OSError): network.read_interfaces()
    assert len(dll.freed) == (0 if failure == 'api' else 1)


def test_network_model_reads_same_shared_snapshot(transport):
    from app.bootstrap import create_core
    from app.session.gemini import GeminiText
    from app.session.model_tools import ModelTools
    from app.bridge.webview_bridge import NativeBridge
    from app.storage.json_store import JsonStore
    from app.config import get_data_home
    now = [0]
    monitor = Telemetry(reader=lambda: {'memory_total':100,'memory_used':0}, clock=lambda:now[0], network_reader=lambda:[row()])
    monitor.snapshot()
    now[0] = 3
    transport.responses = [reply([call('system.status', {}, 'network-read')]), reply([{'text':'Read'}])]
    with create_core(telemetry=monitor) as core:
        bridge = NativeBridge(core, JsonStore(get_data_home()/'settings.json'), telemetry=monitor)
        bridge._ready = True
        before = len(core._entries)
        view = bridge.event('query_system')['data']
        assert len(core._entries) == before
        assert view['network_receive_bps'] == 0 and view['memory_percent'] == 0
        tools = ModelTools(core, principal='local-user', session_id='network', allowed_tools=('system.status',))
        with GeminiText(tools) as model:
            report = model.run('Read network traffic')
        assert report['tool_results'][0]['result']['data'] == view
        assert bridge._chat.close()


def test_unknown_operational_state_is_not_reported_as_disconnected(monkeypatch):
    dll = IpHelper()
    dll.table.rows[0].oper_status = 4
    monkeypatch.setattr(network, '_load_iphelper', lambda: dll)
    data = network.Network().sample(0)
    assert data['network_link'] is None and data['network_wifi_connected'] is None
    assert data['network_receive_bps'] is None
