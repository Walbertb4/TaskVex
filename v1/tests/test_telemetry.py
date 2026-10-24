"""Tek telemetri sahibini sahte donanımla ve gerçek core hattıyla dene.

Hiçbir pencere başlığı, kullanıcı dosyası veya ücretli API kullanılmaz. UI
snapshot sorgusunun günlük/worker üretmediği ve modelin aynı örneği gördüğü
kontrol edilir; bu test bütün GPU/sensörler için donanım kabulü değildir.
"""
from threading import Event
import pytest
from app.bootstrap import create_core
from app.bridge.webview_bridge import NativeBridge
from app.core.contracts import ToolContext, ToolRequest
from app.storage.json_store import JsonStore
from app.tools.local.telemetry import Telemetry, system_status


def source(times=(20,60,40)):
    return {'times':times,'memory_used':0,'memory_total':100,'disk_used':0,'disk_total':200,
        'disk_volume':'C:','active_process':'synthetic.exe','battery_present':True,
        'battery_percent':0,'ac_connected':False}


def test_shared_sample_cpu_delta_zero_cache_and_copy():
    now=[0];calls=[]
    def reader():
        calls.append(True)
        return source((20,60,40) if len(calls)==1 else (40,120,80))
    monitor=Telemetry(reader=reader,clock=lambda:now[0])
    first=monitor.snapshot()
    assert first['cpu_percent'] is None and first['memory_percent']==0
    first['active_process']='corrupted'
    assert monitor.snapshot()['active_process']=='synthetic.exe' and len(calls)==1
    now[0]=2
    second=monitor.snapshot()
    assert second['cpu_percent']==80 and second['battery_percent']==0 and second['disk_used']==0
    assert second['gpu_percent'] is None and 'gpu_percent' in second['unavailable']


@pytest.mark.parametrize('second',[(0,0,0),(0,60,40),(999,61,40)])
def test_reset_or_invalid_cpu_counters_never_fake_usage(second):
    now=[0];values=iter([source(),source(second)])
    monitor=Telemetry(reader=lambda:next(values),clock=lambda:now[0])
    monitor.snapshot();now[0]=3
    assert monitor.snapshot()['cpu_percent'] is None


def test_failed_source_clears_old_metrics_and_resets_cpu_reference():
    now=[0];calls=[0]
    def reader():
        calls[0]+=1
        if calls[0]==2:raise OSError('private failure')
        return source()
    monitor=Telemetry(reader=reader,clock=lambda:now[0])
    assert monitor.snapshot()['memory_percent']==0
    now[0]=3
    lost=monitor.snapshot()
    assert lost['memory_percent'] is None and lost['active_process'] is None and 'private' not in str(lost)
    now[0]=6
    assert monitor.snapshot()['cpu_percent'] is None


def test_processor_group_scope_not_reported_as_all_cpu(monkeypatch):
    monkeypatch.setattr('app.tools.local.telemetry.os.cpu_count',lambda:128)
    now=[0];values=iter([source(),source((40,120,80))])
    monitor=Telemetry(reader=lambda:next(values),clock=lambda:now[0])
    monitor.snapshot();now[0]=3
    assert monitor.snapshot()['cpu_percent'] is None


def test_ui_read_and_model_tool_share_owner_without_poll_tasks(taskvex_home):
    monitor=Telemetry(reader=source,clock=lambda:10)
    store=JsonStore(taskvex_home/'settings.json')
    with create_core(settings_store=store,telemetry=monitor) as core:
        bridge=NativeBridge(core,store,telemetry=monitor)
        assert not bridge.event('query_system')['ok']
        bridge._ready=True
        assert not bridge.event('query_system',{})['ok']
        # Böyle bir UI sorgusu core.submit'e uğramaz; worker/journal poll ile büyümez.
        initial=len(core._entries)
        view=bridge.event('query_system')
        for _ in range(5):
            view=bridge.event('query_system')
            assert view['ok'] and view['data']['memory_percent']==0
        assert len(core._entries)==initial
        request=ToolRequest(request_id='model-system',source='desktop',principal='local-user',tool='system.status')
        result=core.wait(core.submit(request).task_id,3)
        assert result.result is not None
        assert result.result.verified and result.result.to_dict()['data']==view['data']
        assert bridge._chat.close()


def test_cancelled_measurement_does_not_read_hardware():
    def forbidden():raise AssertionError('cancelled reader ran')
    context=ToolContext(task_id='cancel',request=ToolRequest(request_id='r',source='desktop',principal='local-user',tool='system.status'),cancel_event=Event())
    context.cancel_event.set()
    assert system_status({},context,monitor=Telemetry(reader=forbidden)).status.value=='cancelled'
