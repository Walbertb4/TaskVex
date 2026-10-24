"""Windows GPU adaptörünü sahte PDH ile doğrula; gerçek GPU/API kullanılmaz.

Sayaç ABI'si (Windows DLL veri biçimi), ilk örnek, sıfır, motor toplama,
kaynak kapanışı ve ortak model/UI sahibi denetlenir. Donanım kabulü değildir.
"""
import ctypes as c
from ctypes import wintypes as w
import pytest
from app.tools.local import windows_gpu as gpu
from app.tools.local.telemetry import Telemetry
from test_gemini import transport, reply, call


def instance(pid=1, adapter='a', engine=0):
    return f'pid_{pid}_luid_0x00000000_0x{adapter}_phys_0_eng_{engine}_engtype_3D'


class Pdh:
    """DLL imzalarını taklit eder; buffer gerçek ctypes yerleşimini kullanır."""
    def __init__(self):
        self.closed = []
        self.rows = [(instance(), 0.0, 0)]
        self.failure: str | None = None
        self.collected = 0

    def PdhOpenQueryW(self, source, user, query):
        assert source is None
        c.cast(query, c.POINTER(w.HANDLE))[0] = 123
        return 1 if self.failure == 'open' else 0

    def PdhAddEnglishCounterW(self, query, path, user, counter):
        assert path == r'\GPU Engine(*)\Utilization Percentage'
        c.cast(counter, c.POINTER(w.HANDLE))[0] = 456
        return 1 if self.failure == 'add' else 0

    def PdhCollectQueryData(self, query):
        self.collected += 1
        return 1 if self.failure == 'collect' else 0

    def PdhCloseQuery(self, query):
        self.closed.append(query.value)
        return 0

    def PdhGetFormattedCounterArrayW(self, counter, fmt, size, count, buffer):
        assert fmt == 0x200
        size_ptr, count_ptr = c.cast(size, c.POINTER(w.DWORD)), c.cast(count, c.POINTER(w.DWORD))
        if buffer is None:
            size_ptr[0] = 5000000 if self.failure == 'oversize' else 4096
            return 0x800007D2
        if self.failure == 'resize':
            return 0x800007D2
        count_ptr[0] = 100000 if self.failure == 'bad-count' else len(self.rows)
        self.names = [c.create_unicode_buffer(name) for name, _, _ in self.rows]
        items = c.cast(buffer, c.POINTER(gpu._Item))
        for i, (_, value, status) in enumerate(self.rows):
            items[i].name = c.cast(self.names[i], w.LPWSTR)
            items[i].value.status = status
            items[i].value.number.doubleValue = value
        return 0


def test_processes_sum_per_engine_then_busiest_engine_and_adapter():
    devices = gpu.aggregate_engines([
        (instance(1), 20), (instance(2), 30), (instance(1, engine=1), 40),
        (instance(1, 'b'), 75), (instance(2, 'b', 1), 80),
        (instance(1, 'c'), 0), ('not-an-engine', 90), (instance(1, 'd'), float('nan')),
        (instance(1, 'd'), -1), (instance(2, 'd'), float('inf'))])
    assert [item['utilization_percent'] for item in devices] == [50, 80, 0]
    assert all('pid_' not in item['id'] for item in devices)
    assert gpu.aggregate_engines([(instance(), 90), (instance(2), 20)])[0]['utilization_percent'] == 100


def test_first_sample_zero_invalid_instance_and_handle_cleanup(monkeypatch):
    dll = Pdh()
    monkeypatch.setattr(gpu, '_load_pdh', lambda: dll)
    reader = gpu.WindowsGpu()
    assert reader()['gpu_status'] == 'warming_up'
    assert dll.collected == 1
    dll.rows += [(instance(2), 90, 0xC0000BBA)]
    assert reader()['gpu_devices'][0]['utilization_percent'] == 0
    reader.close()
    reader.close()
    assert dll.closed == [123]


@pytest.mark.parametrize('failure', ['open', 'add', 'collect', 'oversize', 'resize', 'bad-count'])
def test_failed_native_calls_clear_and_close_then_recover(monkeypatch, failure):
    dll = Pdh()
    monkeypatch.setattr(gpu, '_load_pdh', lambda: dll)
    reader = gpu.WindowsGpu()
    if failure not in ('open', 'add', 'collect'):
        reader()
    dll.failure = failure
    report = reader()
    assert report['gpu_status'] == 'unavailable' and report['gpu_devices'] == []
    assert dll.closed == ([] if failure == 'open' else [123])
    dll.failure = None
    assert reader()['gpu_status'] == 'warming_up'
    reader.close()


def test_missing_empty_counters_and_finalizer(monkeypatch):
    import gc
    dll = Pdh()
    dll.rows = []
    monkeypatch.setattr(gpu, '_load_pdh', lambda: dll)
    reader = gpu.WindowsGpu()
    reader()
    assert reader()['gpu_status'] == 'unavailable'
    del reader
    gc.collect()
    assert dll.closed == [123]
    def unavailable(): raise OSError('private OS detail')
    monkeypatch.setattr(gpu, '_load_pdh', unavailable)
    assert 'private' not in str(gpu.WindowsGpu()())


def test_shared_cache_and_gpu_failure_preserve_ram():
    now = [0]
    rows = iter([
        {'gpu_devices': [{'id': 'a', 'utilization_percent': 0}, {'id': 'b', 'utilization_percent': 25}]},
        {'gpu_devices': []}])
    monitor = Telemetry(reader=lambda: {'memory_total': 100, 'memory_used': 0},
        clock=lambda: now[0], gpu_reader=lambda: next(rows))
    assert monitor.snapshot()['gpu_percent'] == 25
    copy = monitor.snapshot()
    copy['gpu_devices'][0]['utilization_percent'] = 100
    assert monitor.snapshot()['gpu_devices'][0]['utilization_percent'] == 0
    now[0] = 3
    lost = monitor.snapshot()
    assert lost['gpu_percent'] is None and lost['memory_percent'] == 0
    assert lost['gpu_temperature'] is None and lost['cpu_temperature'] is None


def test_gpu_model_uses_existing_shared_owner(transport):
    from app.bootstrap import create_core
    from app.session.gemini import GeminiText
    from app.session.model_tools import ModelTools
    monitor = Telemetry(reader=lambda: {}, clock=lambda: 10, gpu_reader=lambda: {
        'gpu_source': 'windows-pdh', 'gpu_status': 'ok',
        'gpu_devices': [{'id': 'synthetic', 'utilization_percent': 12}]})
    transport.responses = [reply([call('system.status', {}, 'gpu-status')]), reply([{'text': 'Read'}])]
    with create_core(telemetry=monitor) as core:
        tools = ModelTools(core, principal='local-user', session_id='synthetic-gpu', allowed_tools=('system.status',))
        with GeminiText(tools) as model:
            report = model.run('Read GPU usage')
        result = report['tool_results'][0]['result']
        assert report['ok'] and result['verified'] and result['data'] == monitor.snapshot()
        assert result['data']['gpu_percent'] == 12
    assert len(transport.requests) == 2
