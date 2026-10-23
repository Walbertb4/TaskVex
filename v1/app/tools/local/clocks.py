"""Çoklu timer/stopwatch için tek RAM durum sahibi ve kayıtlı araçlar.

Model ve native UI mutasyonları aynı registry/policy/TaskManager hattından
geçer. Host görünüm sorgusu yalnız bu nesnenin snapshot'ını okur; her ekran
tiki için görev açmaz. Monoton saat, Windows saat ayarı değişse de süreyi korur.
İkinci worker/scheduler ve disk kaydı yoktur; uygulama kapanınca kayıtlar biter.
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
# Aynı izinli alanlarla iki açık şema: sağlayıcıda 'not' anahtarına dayanma.
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
    """Bootstrap ve native bridge'e aynı örnek enjekte edilir.

    Kilit, worker mutasyonunu host'un salt görünüm okumasıyla yarıştırmaz.
    Her nesne UUID, tür, etiket, süre, birikmiş zaman ve başlangıç anını tutar.
    UI'ya dahili saat referansı değil, bağımsız hesaplanmış görünüm gönderilir.
    """

    def __init__(self):
        self._items: dict[str, dict] = {}
        self._lock = RLock()
        self._revision = 0

    def snapshot(self) -> dict:
        """Güncel süreleri tek anda örnekle; dolmuş timer'ı bir kez finished yap.

        Sample, geç gelen eski UI okumasının daha yeni durumu ezmesini önler.
        Zaman aşımı doğal bir saat geçişidir; model komutu veya yan etki replay'i
        değildir. Alarmın sesi mevcut UI sahibinde, id/generation başına tektir.
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
        """Yeni bağımsız kayıt oluştur; aynı etiket eski kaydı ezmez.

        start=True hemen başlatır; False hazır bırakır. Timer için pozitif,
        sonlu ve en çok bir yıl süre zorunludur; stopwatch süre almaz.
        Registry dışında doğrudan çağrıda da biçim ve iptal kontrol edilir.
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
        """Gerçek ID'yi başlat/devam ettir, duraklat veya sıfırla.

        start çalışan kaydı sıfırlamaz; pause+start kaldığı yerden devamdır.
        Biten timer yeniden başlatılırsa yeni generation olur. Reset timer'ın
        ayarlı süresini korur; optional duration_seconds yalnız timer resetinde
        mevcut Set düğmesinin süre ayarını değiştirir. Stopwatch sıfıra döner. Geç Stop tamamlanmış
        değişikliği geri almaz. İsimle veya sıra tahminiyle hedef seçilmez.
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
        """Yalnız UI’ın gerçek ID hedefini sil; sonucu aynı RAM sahibinden doğrula.

        TaskManager tekrar koruması ve clocks kilidi kullanılır. İptal mutasyondan
        önce kontrol edilir; bitmiş silme geç Stop ile geri alınmış sayılmaz.
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
        """Değişikliği tek sahibinden geri oku; JSON kopyası dışarıda değiştirilemez."""
        snapshot = self.snapshot()
        clock = next(c for c in snapshot['clocks'] if c['id'] == clock_id)
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
            data={**snapshot, 'clock': clock}, evidence={'in_memory': True, 'read_back': True})

    def list(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Model için kayıtlı salt okunur araç; host görünümü aynı snapshot'ı kullanır."""
        if arguments:
            return self._error(context, 'invalid_arguments', 'Clock list accepts no arguments')
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
            data=self.snapshot(), evidence={'in_memory': True})
