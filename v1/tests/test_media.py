"""Try pure media owner with synthetic session; Don't touch the real player.

UI/model uses the same example, poll does not log. Source absence/timeout,
session exchange and COM lifecycle are verified with the mock service.
"""
import asyncio
from threading import Event
from types import SimpleNamespace
import pytest
from app.tools.local import media
from app.tools.local.media import _read_windows as native_reader
from app.core.contracts import ToolContext, ToolRequest
from test_gemini import transport, reply, call


def test_shared_cache_is_copy_and_failure_clears_old_metadata():
    now = [0]
    records = iter([{'status':'available','title':'First','artist':'Artist','state':'playing'},
        {'status':'timeout'}, {'status':'no_session'}])
    meter = media.Media(reader=lambda:next(records),clock=lambda:now[0])
    first = meter.snapshot()
    first['title'] = 'Corrupted'
    assert meter.snapshot()['title'] == 'First'
    now[0] = 2
    failed = meter.snapshot()
    assert failed['title'] is None and failed['state'] is None and failed['status'] == 'timeout'
    now[0] = 4
    assert meter.snapshot()['status'] == 'no_session'


@pytest.mark.parametrize('raw', [None, {}, {'status':'wrong'}, {'status':'available','title':123,'artist':{},'state':'weird'}])
def test_invalid_fields_never_become_metadata(raw):
    data = media.Media(reader=lambda:raw).snapshot()
    assert data['title'] is None and data['artist'] is None and data['state'] is None


def test_strings_are_bounded_and_os_failures_are_private():
    data = media.Media(reader=lambda:{'status':'available','title':'x'*10000,'artist':'a'*10000}).snapshot()
    assert len(data['title']) == 512 and len(data['artist']) == 512
    def failed(): raise OSError('private Windows service error')
    data = media.Media(reader=failed).snapshot()
    assert data['status'] == 'unavailable' and 'private' not in str(data)


class Session:
    def __init__(self):
        self.properties: SimpleNamespace | None = SimpleNamespace(title='Synthetic track',artist='Synthetic artist')
        self.status = 5
    async def try_get_media_properties_async(self): return self.properties
    def get_playback_info(self): return SimpleNamespace(playback_status=self.status)


@pytest.mark.parametrize('state', ['paused','playing','no_session','changed','missing-properties'])
def test_native_current_session_read_and_change_guard(monkeypatch,state):
    session = Session()
    if state == 'playing':session.status = 4
    if state == 'missing-properties':session.properties = None
    calls = []
    def current():
        calls.append(True)
        return None if state == 'no_session' else Session() if state == 'changed' and len(calls)>1 else session
    async def manager():return SimpleNamespace(get_current_session=current)
    monkeypatch.setattr(media,'_request_manager',manager)
    data = asyncio.run(media._read_async())
    if state in ('playing','paused'):assert data['state'] == state and data['title'] == 'Synthetic track'
    else:assert data['status'] == {'no_session':'no_session','changed':'session_changed','missing-properties':'unavailable'}[state]


@pytest.mark.parametrize('failure', ['none','timeout','os','init'])
def test_com_initialization_balanced_and_timeout_is_not_no_session(monkeypatch,failure):
    import winrt.runtime as runtime
    calls = []
    def init(kind):
        calls.append('init')
        if failure == 'init': raise OSError('incompatible apartment')
    monkeypatch.setattr(runtime,'init_apartment',init)
    monkeypatch.setattr(runtime,'uninit_apartment',lambda:calls.append('uninit'))
    async def read(manager=None):
        if failure == 'timeout':raise TimeoutError()
        if failure == 'os':raise OSError('private provider failure')
        return {'status':'no_session'}
    monkeypatch.setattr(media,'_read_async',read)
    data = native_reader()
    assert calls == (['init'] if failure == 'init' else ['init','uninit'])
    assert data['status'] == {'none':'no_session','timeout':'timeout','os':'unavailable','init':'unavailable'}[failure]


def test_ui_and_model_share_same_owner_policy_and_no_poll_tasks(transport,taskvex_home):
    from app.bootstrap import create_core
    from app.bridge.webview_bridge import NativeBridge
    from app.storage.json_store import JsonStore
    from app.session.gemini import GeminiText
    from app.session.model_tools import ModelTools
    from app.session.text_chat import BASE_MODEL_TOOLS
    assert 'media.status' in BASE_MODEL_TOOLS
    meter = media.Media(reader=lambda:{'status':'available','title':'Synthetic','state':'paused'},clock=lambda:10)
    transport.responses = [reply([call('media.status',{},'current-media')]),reply([{'text':'Read'}])]
    with create_core(media=meter) as core:
        bridge = NativeBridge(core,JsonStore(taskvex_home/'settings.json'),media=meter)
        assert not bridge.event('query_media')['ok']
        bridge._ready = True
        assert not bridge.event('query_media',{})['ok']
        before = len(core._entries)
        view = bridge.event('query_media')['data']
        assert len(core._entries) == before
        tools = ModelTools(core,principal='local-user',session_id='media',allowed_tools=('media.status',))
        with GeminiText(tools) as model: report = model.run('What is playing?')
        assert report['ok'] and report['tool_results'][0]['result']['verified']
        assert report['tool_results'][0]['result']['data'] == view
        assert bridge._chat.close()


def test_cancelled_tool_does_not_read_media_and_unavailable_is_failed():
    request = ToolRequest(request_id='r',source='desktop',principal='local-user',tool='media.status')
    context = ToolContext(task_id='t',request=request,cancel_event=Event())
    context.cancel_event.set()
    def forbidden():raise AssertionError('cancelled reader ran')
    assert media.Media(reader=forbidden).status({},context).status.value == 'cancelled'
    context.cancel_event.clear()
    result = media.Media(reader=lambda:{'status':'unsupported'}).status({},context)
    assert result.status.value == 'failed' and not result.verified and result.data['title'] is None


def test_media_read_capability_is_explicit():
    from app.policy.engine import PolicyEngine
    from app.core.contracts import ToolSpec
    request = ToolRequest(request_id='r',source='desktop',principal='local-user',tool='media.status')
    spec = ToolSpec(name='media.status',description='Read',input_schema={'type':'object'},
        handler=media.Media().status,required_capabilities=('media.read',))
    assert not PolicyEngine(principal='local-user',capabilities=frozenset({'system.read'})).authorize(request,spec)
    assert PolicyEngine(principal='local-user',capabilities=frozenset({'media.read'})).authorize(request,spec)
