"""Single RAM status for multiple timer/stopwatch owned and registered tools.

Model and native UI mutations are from the same registry/policy/TaskManager line
passes. The host view query reads only the snapshot of this object; every screen
It does not open quests for tiki. Monotonic clock maintains time even if the Windows time setting changes.
Second worker/scheduler and no disc recording; The recordings end when the application is closed.
"""
from math import isfinite
from threading import RLock
from time import monotonic
from uuid import uuid4

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult

CREATE_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {'kind': {'type': 'string', 'enum': ['timer', 'stopwatch']},
        'label': {'type': 'string', 'minLength': 1, 'maxLength': 80, 'pattern': r'\S'},
        'duration_seconds': {'type': 'number', 'exclusiveMinimum': 0, 'maximum': 31536000},
        'start': {'type': 'boolean'}},
    'required': ['kind', 'start'],

}
# Two open schemes with the same allowed fields: relying on the 'not' key in the provider.
CREATE_SCHEMA['anyOf'] = [
    {'type': 'object', 'additionalProperties': False,
     'properties': {**CREATE_SCHEMA['properties'], 'kind': {'enum': ['timer']}},
     'required': ['kind', 'start', 'duration_seconds']},
    {'type': 'object', 'additionalProperties': False,
     'properties': {k: ({'enum': ['stopwatch']} if k == 'kind' else v)
                    for k, v in CREATE_SCHEMA['properties'].items() if k != 'duration_seconds'},
     'required': ['kind', 'start']},
]
CONTROL_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {'id': {'type': 'string', 'pattern': r'\S'},
        'action': {'type': 'string', 'enum': ['start', 'pause', 'reset']},
        'duration_seconds': CREATE_SCHEMA['properties']['duration_seconds']},
    'required': ['id', 'action'],
}
DELETE_SCHEMA = {'type':'object','additionalProperties':False, 'properties':{'id':{'type':'string','minLength':1,'pattern':r'\S'}}, 'required':['id']}
LIST_SCHEMA = {'type': 'object', 'additionalProperties': False}


class Clocks:
    """The same sample is injected into Bootstrap and native bridge.

    The lock does not compete with the worker mutation with the host's view-only reading.
    Each object holds UUID, type, tag, duration, accumulated time, and start instant.
    The standalone computed view, not the internal clock reference, is sent to the UI.
    """

    def __init__(self):
        self._items: dict[str, dict] = {}
        self._lock = RLock()
        self._revision = 0

    def snapshot(self) -> dict:
        """Sample current times at once; Finish the minibus timer once.

        Sample prevents a late-arriving old UI read from overwhelming the newer state.
        Timeout is a natural clock transition; model command or side effect replay
        It is not. The sound of the alarm is unique per the current UI owner, id/generation.
        """
        with self._lock:
            now = monotonic()
            items = []
            for item in self._items.values():
                elapsed = item['accumulated'] + (now - item['started'] if item['state'] == 'running' else 0)
                if item['kind'] == 'timer' and elapsed >= item['duration_seconds']:
                    elapsed = item['duration_seconds']
                    if item['state'] == 'running':
                        item.update(state='finished', accumulated=elapsed, started=None)
                        self._revision += 1
                items.append({k: v for k, v in item.items() if k not in {'started', 'accumulated'}} | {
                    'elapsed_seconds': elapsed,
                    'remaining_seconds': max(0, item['duration_seconds'] - elapsed) if item['kind'] == 'timer' else None})
            return {'clocks': items, 'revision': self._revision, 'sampled_at': now}

    @staticmethod
    def _error(context: ToolContext, code: str, message: str) -> ToolResult:
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
            error=ToolError(code=code, message=message))

    def create(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Create new independent record; the same label won't crush the old record.

        start=True starts immediately; False leaves ready. Positive for Timer,
        finite and mandatory for a maximum period of one year; stopwatch does not take time.
        Apart from the registry, format and cancellation are also checked in a direct call.
        """
        kind, start = arguments.get('kind'), arguments.get('start')
        duration = arguments.get('duration_seconds')
        label = arguments.get('label')
        if (not {'kind', 'start'} <= set(arguments) <= {'kind', 'start', 'duration_seconds', 'label'}
                or kind not in ('timer', 'stopwatch') or type(start) is not bool
                or 'label' in arguments and (not isinstance(label, str) or not label.strip() or len(label) > 80)
                or kind == 'timer' and (not isinstance(duration, (int, float)) or isinstance(duration, bool) or not isfinite(duration) or not 0 < duration <= 31536000)
                or kind == 'stopwatch' and 'duration_seconds' in arguments):
            return self._error(context, 'invalid_arguments', 'Expected kind, start and a valid timer duration or stopwatch')
        with self._lock:
            if context.cancel_event.is_set():
                return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
            clock_id = uuid4().hex
            count = sum(i['kind'] == kind for i in self._items.values()) + 1
            self._items[clock_id] = {'id': clock_id, 'kind': kind, 'label': label or f'{kind.title()} {count}',
                'duration_seconds': duration if kind == 'timer' else None,
                'state': 'running' if start else 'ready', 'generation': 1 if start else 0,
                'accumulated': 0.0, 'started': monotonic() if start else None}
            self._revision += 1
            return self._result(clock_id, context)

    def control(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Pause, pause or reset real ID start/resume.

        start does not reset the running record; pause+start continues where it left off.
        If the expired timer is restarted, a new generation occurs. Reset timer
        maintains the set time; optional duration_seconds only on timer reset
        Changes the time setting of the current Set button. Stopwatch returns to zero. Late Stop completed
        does not undo the change. A target is not selected by name or by guessing the order.
        """
        if (not {'id', 'action'} <= set(arguments) <= {'id', 'action', 'duration_seconds'} or not isinstance(arguments.get('id'), str)
                or arguments.get('action') not in ('start', 'pause', 'reset')):
            return self._error(context, 'invalid_arguments', 'Expected actual clock ID and supported action')
        with self._lock:
            if context.cancel_event.is_set():
                return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
            self.snapshot()
            item = self._items.get(arguments['id'])
            if item is None:
                return self._error(context, 'not_found', 'Clock not found; list actual IDs, do not guess')
            action, now = arguments['action'], monotonic()
            if 'duration_seconds' in arguments:
                duration = arguments['duration_seconds']
                if (action != 'reset' or item['kind'] != 'timer' or not isinstance(duration, (int, float))
                        or isinstance(duration, bool) or not isfinite(duration) or not 0 < duration <= 31536000):
                    return self._error(context, 'invalid_arguments', 'Duration can only configure a timer reset')
                item['duration_seconds'] = duration
            if action == 'reset':
                item.update(state='ready', accumulated=0.0, started=None)
            elif action == 'start' and item['state'] != 'running':
                if item['state'] in ('ready', 'finished'):
                    item['accumulated'] = 0.0
                    item['generation'] += 1
                item.update(state='running', started=now)
            elif action == 'pause' and item['state'] == 'running':
                elapsed = item['accumulated'] + now - item['started']
                done = item['kind'] == 'timer' and elapsed >= item['duration_seconds']
                item.update(state='finished' if done else 'paused',
                    accumulated=item['duration_seconds'] if done else elapsed, started=None)
            self._revision += 1
            return self._result(item['id'], context)

    def delete(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Just delete the real ID target of the UI; verify the result from the same RAM owner.

        TaskManager replay protection and clocks lock are used. from aborted mutation
        is checked first; The finished deletion is not considered undone by late Stop.
        """
        clock_id = arguments.get('id')
        if set(arguments) != {'id'} or not isinstance(clock_id, str) or not clock_id.strip():
            return self._error(context, 'invalid_arguments', 'Expected actual clock ID')
        with self._lock:
            if context.cancel_event.is_set():
                return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
            if clock_id not in self._items:
                return self._error(context, 'not_found', 'Clock not found')
            del self._items[clock_id]
            self._revision += 1
            snapshot = self.snapshot()
            return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                data={**snapshot, 'deleted_id':clock_id}, evidence={'in_memory':True, 'read_back':True})

    def _result(self, clock_id: str, context: ToolContext) -> ToolResult:
        """Read the change back from the sole owner; The JSON copy cannot be modified externally."""
        snapshot = self.snapshot()
        clock = next(c for c in snapshot['clocks'] if c['id'] == clock_id)
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
            data={**snapshot, 'clock': clock}, evidence={'in_memory': True, 'read_back': True})

    def list(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Read-only tool registered for the model; The host view uses the same snapshot."""
        if arguments:
            return self._error(context, 'invalid_arguments', 'Clock list accepts no arguments')
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
            data=self.snapshot(), evidence={'in_memory': True})
