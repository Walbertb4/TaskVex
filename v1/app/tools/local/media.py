"""Shared Windows media owner: bounded reads and verified session-bound controls.

Public snapshots contain opaque target IDs, never WinRT objects or source app IDs.
Private references pin the Agile WinRT manager and its observed session; native
methods run inside an initialized COM apartment. UI/model use the same core tools.
"""
import asyncio
from copy import deepcopy
import os
from threading import Lock
from time import monotonic
from uuid import uuid4

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult


ACTIONS = ('play', 'pause', 'next', 'previous')
CONTROL_SCHEMA = {'type':'object', 'additionalProperties':False,
    'properties':{'action':{'type':'string','enum':list(ACTIONS)},
                  'target_id':{'type':'string','pattern':r'^[0-9a-f]{32}$'}},
    'required':['action','target_id']}


def _signature(raw):
    """Bind a target to observed metadata/state/capabilities, excluding sample time."""
    return (tuple(raw.get(k)[:512] if isinstance(raw.get(k),str) else None for k in ('title','artist')),
            raw.get('state'), tuple(raw.get('controls',{}).get(k) is True for k in ACTIONS))


async def _request_manager():
    """Ability to replace Windows API activation with synthetic transport in tests."""
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
    return await GlobalSystemMediaTransportControlsSessionManager.request_async()


async def _current(manager) -> dict:
    """Read one current session and reject a session change during metadata await."""
    session = manager.get_current_session()
    if session is None:
        return {'status':'no_session'}
    properties = await session.try_get_media_properties_async()
    playback = session.get_playback_info()
    if properties is None or playback is None:
        return {'status':'unavailable'}
    if manager.get_current_session() != session:
        return {'status':'session_changed'}
    controls = getattr(playback,'controls',None)
    return {'status':'available','title':properties.title,'artist':properties.artist,
        'state':{0:'closed',1:'opened',2:'changing',3:'stopped',4:'playing',5:'paused'}.get(int(playback.playback_status)),
        'controls':{k:getattr(controls,'is_'+k+'_enabled',False) is True for k in ACTIONS},
        '_session':session}


async def _read_async(manager=None) -> dict:
    """Reuse one manager's session identities until a transport failure invalidates it."""
    manager = manager if manager is not None else await _request_manager()
    return {**await _current(manager),'_manager':manager}


async def _control_async(target, action, expected, cancel, attempt) -> dict:
    """Issue at most one native request, then verify its observable result.

    Once dispatch starts, timeout/exception/Stop without confirmed readback is
    unknown, not a safe retry. Readback is allowed after Stop; no new action is.
    """
    # RequestAsync creates manager-local session identities, even for the same app.
    # Reuse the manager that issued this target; never compare across activations.
    manager = expected.get('_manager')
    if manager is None:
        return {'status':'failed','code':'media_target_changed'}
    before = await _current(manager)
    def result(status, code, raw=before, **evidence):
        return {'status':status,'code':code,'raw':{**raw,'_manager':manager},'evidence':evidence}
    if before.get('_session') != target or _signature(before) != _signature(expected):
        return result('failed','media_target_changed')
    if cancel.is_set():
        return result('cancelled','cancelled')
    goal = {'play':'playing','pause':'paused'}.get(action)
    if goal and before['state'] == goal:
        return result('succeeded','already_in_state',read_back=True,already_in_state=True)
    if not before['controls'].get(action):
        return result('failed','media_action_unsupported')
    if manager.get_current_session() != target:
        return result('failed','media_target_changed',{'status':'session_changed'})
    if cancel.is_set():
        return result('cancelled','cancelled')
    method = {'play':'try_play_async','pause':'try_pause_async',
              'next':'try_skip_next_async','previous':'try_skip_previous_async'}[action]
    attempt['sent'] = True  # Even an exception from the call may follow delivery.
    accepted = await getattr(target,method)()
    if accepted is False:
        return result('failed','media_request_rejected',accepted=False)
    if accepted is not True:
        return result('unknown','media_result_unknown')
    deadline = asyncio.get_running_loop().time()+1.2
    while True:
        after = await _current(manager)
        if after.get('_session') != target:
            return result('unknown','media_session_changed_after_dispatch',after,accepted=True)
        # shortcut: metadata cannot prove same-title skips; add timeline evidence if needed.
        verified = (after.get('state') == goal if goal else
                    _signature(after)[0] != _signature(before)[0])
        if verified:
            return result('succeeded','verified',after,accepted=True,read_back=True)
        if cancel.is_set() or asyncio.get_running_loop().time() >= deadline:
            return result('unknown','media_result_unknown',after,accepted=True)
        await asyncio.sleep(.1)


def _native(operation, timeout=2) -> dict:
    """Initialize COM for this call, bound the await, and balance apartment cleanup."""
    if os.name != 'nt':
        return {'status':'unsupported'}
    try:
        from winrt.runtime import ApartmentType, init_apartment, uninit_apartment
        init_apartment(ApartmentType.MULTI_THREADED)
    except ImportError:
        return {'status':'unsupported'}
    except OSError:
        return {'status':'unavailable'}
    try:
        return asyncio.run(asyncio.wait_for(operation(), timeout=timeout))
    except TimeoutError:
        return {'status':'timeout'}
    except ImportError:
        return {'status':'unsupported'}
    except (OSError, RuntimeError):
        return {'status':'unavailable'}
    finally:
        uninit_apartment()



def _read_windows(manager=None) -> dict:
    return _native(lambda:_read_async(manager))


def _control_windows(target, action, expected, cancel) -> dict:
    attempt = {'sent':False}
    raw = _native(lambda:_control_async(target,action,expected,cancel,attempt),timeout=4)
    if raw.get('status') in ('succeeded','failed','unknown','cancelled'):
        return raw
    return {'status':'unknown' if attempt['sent'] else 'failed',
            'code':'media_result_unknown' if attempt['sent'] else 'media_unavailable',
            'raw':raw,'evidence':{'dispatched':attempt['sent']}}


class Media:
    """Single cache/lock; timeout or resource loss does not preserve the old fragment."""
    def __init__(self, *, reader=None, controller=None, clock=None):
        self._reader = reader
        self._controller = controller or _control_windows
        self._clock = clock or monotonic
        self._lock = Lock()
        self._sample = None
        self._session: object | None = None
        self._manager: object | None = None
        self._target_id: str | None = None
        self._uncertain = False

    def snapshot(self) -> dict:
        """The new sample collapses into a JSON contract; independent copy is output."""
        with self._lock:
            now = self._clock()
            if self._sample is not None and now-self._sample['sampled_at'] < 2:
                return deepcopy(self._sample)
            try:
                raw = self._reader() if self._reader is not None else _read_windows(self._manager)
            except (OSError, RuntimeError, TimeoutError):
                raw = {}
            return self._publish(raw)

    def _publish(self, raw) -> dict:
        """Strip private WinRT identity and invalidate stale control target IDs."""
        data = {'source':'windows-gsmtc','sampled_at':self._clock(),'status':'unavailable',
                'title':None,'artist':None,'state':None,'target_id':None,
                'controls':{k:False for k in ACTIONS},'control_unknown':self._uncertain}
        session = None
        self._manager = raw.get('_manager') if isinstance(raw,dict) else None
        if isinstance(raw,dict) and raw.get('status') in (
                'available','no_session','session_changed','timeout','unsupported','unavailable'):
            data['status'] = raw['status']
            if raw['status'] == 'available':
                for key in ('title','artist'):
                    if isinstance(raw.get(key),str):data[key] = raw[key][:512]
                if raw.get('state') in ('closed','opened','changing','stopped','playing','paused'):
                    data['state'] = raw['state']
                session = raw.get('_session')
                if session is not None:
                    data['controls'] = {k:raw.get('controls',{}).get(k) is True for k in ACTIONS}
                    if session != self._session or self._sample is None or _signature(data) != _signature(self._sample):
                        self._target_id = uuid4().hex
                    data['target_id'] = self._target_id
        if session is None:self._target_id = None
        self._session = session
        self._sample = data
        return deepcopy(data)

    def control(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Mutate the exact observed target through the shared task/replay boundary."""
        if (set(arguments) != {'action','target_id'} or arguments.get('action') not in ACTIONS
                or not isinstance(arguments.get('target_id'),str)):
            return ToolResult(task_id=context.task_id,status=TaskStatus.FAILED,
                error=ToolError(code='invalid_arguments',message='Expected an action and current media target ID'))
        with self._lock:
            if context.cancel_event.is_set():
                return ToolResult(task_id=context.task_id,status=TaskStatus.CANCELLED)
            if self._uncertain:
                return ToolResult(task_id=context.task_id,status=TaskStatus.UNKNOWN,
                    error=ToolError(code='media_result_unknown',message='Earlier media result is unknown; do not retry'))
            if self._session is None or self._sample is None or arguments['target_id'] != self._target_id:
                return ToolResult(task_id=context.task_id,status=TaskStatus.FAILED,
                    error=ToolError(code='media_target_changed',message='Read media.status again; the old target is no longer current'))
            outcome: dict
            try:
                expected = {**deepcopy(self._sample),'_manager':self._manager}
                outcome = self._controller(self._session,arguments['action'],expected,context.cancel_event)
            except Exception:
                outcome = {'status':'unknown','code':'media_result_unknown'}
            status = TaskStatus(outcome['status'])
            self._uncertain = status == TaskStatus.UNKNOWN
            data = self._publish(outcome.get('raw',{}))
            return ToolResult(task_id=context.task_id,status=status,verified=status==TaskStatus.SUCCEEDED,
                data=data,evidence={'source':'windows-gsmtc',**outcome.get('evidence',{})},
                error=None if status in (TaskStatus.SUCCEEDED,TaskStatus.CANCELLED) else
                    ToolError(code=outcome['code'],message='Media action was not confirmed; no automatic retry'))

    def status(self, arguments: dict, context: ToolContext) -> ToolResult:
        """The model reads the same sample via the existing registry/policy/TaskManager."""
        if arguments:
            return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                error=ToolError(code='invalid_arguments', message='Media status accepts no arguments'))
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        data = self.snapshot()
        if data['status'] not in ('available','no_session'):
            return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED, data=data,
                error=ToolError(code='media_unavailable', message='Current Windows media session could not be read'))
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
            data=data, evidence={'source':'windows-gsmtc', 'read_only':True})
