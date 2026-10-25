"""Windows' sole read-only owner of the current media session.

The UI and model read the same two-second sample. GSMTC, application to Windows
is the media information it reports; window/tab content or microphone is not read.
Oynat/pause/skip is not available in this slice. WinRT objects related during reading
Stays at COM apartment; Only JSON fields are output to UI/model.
"""
import asyncio
from copy import deepcopy
import os
from threading import Lock
from time import monotonic

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult


async def _request_manager():
    """Ability to replace Windows API activation with synthetic transport in tests."""
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
    return await GlobalSystemMediaTransportControlsSessionManager.request_async()


async def _read_async() -> dict:
    """If Windows switched to another session while waiting for metadata, discard the old header."""
    manager = await _request_manager()
    session = manager.get_current_session()
    if session is None:
        return {'status': 'no_session'}
    properties = await session.try_get_media_properties_async()
    playback = session.get_playback_info()
    if properties is None or playback is None:
        return {'status':'unavailable'}
    # WinRT equality is native object ID, not Python wrapper ID.
    if manager.get_current_session() != session:
        return {'status': 'session_changed'}
    state = {0:'closed', 1:'opened', 2:'changing', 3:'stopped', 4:'playing', 5:'paused'}.get(int(playback.playback_status))
    return {'status':'available', 'title':properties.title, 'artist':properties.artist, 'state':state}


def _read_windows() -> dict:
    """Wait no more than two seconds in the temporary asyncio loop; worker/thread tripping.

    COM apartment is the WinRT context of the calling thread. A different apartment
    If it is established, we do not change it. Successful init is offset by its own uninit.
    """
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
        return asyncio.run(asyncio.wait_for(_read_async(), timeout=2))
    except TimeoutError:
        return {'status':'timeout'}
    except ImportError:
        return {'status':'unsupported'}
    except (OSError, RuntimeError):
        return {'status':'unavailable'}
    finally:
        uninit_apartment()


class Media:
    """Single cache/lock; timeout or resource loss does not preserve the old fragment."""
    def __init__(self, *, reader=None, clock=None):
        self._reader = reader or _read_windows
        self._clock = clock or monotonic
        self._lock = Lock()
        self._sample = None

    def snapshot(self) -> dict:
        """The new sample collapses into a JSON contract; independent copy is output."""
        with self._lock:
            now = self._clock()
            if self._sample is not None and now-self._sample['sampled_at'] < 2:
                return deepcopy(self._sample)
            data = {'source':'windows-gsmtc', 'sampled_at':now, 'status':'unavailable',
                'title':None, 'artist':None, 'state':None}
            try:
                raw = self._reader()
            except (OSError, RuntimeError, TimeoutError):
                raw = {}
            if isinstance(raw, dict) and raw.get('status') in (
                'available', 'no_session', 'session_changed', 'timeout', 'unsupported', 'unavailable'):
                data['status'] = raw['status']
                if raw['status'] == 'available':
                    for key in ('title','artist'):
                        if isinstance(raw.get(key), str):
                            data[key] = raw[key][:512]
                    if raw.get('state') in ('closed','opened','changing','stopped','playing','paused'):
                        data['state'] = raw['state']
            self._sample = data
            return deepcopy(data)

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
