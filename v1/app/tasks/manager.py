"""TaskVex'in tek worker ile çalışan, bellek içi görev yöneticisi.

submit isteği kabul eder; tek worker handler'ları sırayla çalıştırır. get/wait
durum kopyası verir, cancel iptal ister, close yeni iş kabulünü durdurur.
Tek worker olduğu için iki handler aynı anda desktop gibi ortak kaynağı kullanmaz.

Bu sürüm kalıcı görev günlüğü, paralel kaynak planlayıcısı veya policy motoru
değildir. Yetki kararı için dar bir callback noktası vardır; verilmezse yürütme
reddedilir. Thread iptali zorlamaz; handler kendi alt kaynaklarını yönetmelidir.
"""

from collections import deque
from dataclasses import dataclass, field, replace
from inspect import iscoroutine, iscoroutinefunction
import json
import math
from threading import Condition, Event, Thread, current_thread
from typing import Callable
from uuid import uuid4

from app.core.contracts import (
    ContractError, Task, TaskStatus, ToolContext, ToolError,
    ToolRequest, ToolResult, ToolSpec,
)
from app.session.tool_registry import RegistryError, ToolRegistry


class TaskManagerError(ContractError):
    """Kimlik çakışması, kapasite veya yaşam döngüsü hatasını koduyla bildirir."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class _Entry:
    """Dışarı verilmeyen görev kaydı; iptal Event'i manager/handler arasında ortaktır."""

    task: Task
    fingerprint: str
    cancel_event: Event = field(default_factory=Event)


def _copy_request(request: ToolRequest) -> ToolRequest:
    """İç sözlüğü paylaşmadan, ortak sözleşmeyi yeniden doğrulayarak kopyala."""
    return ToolRequest(**request.to_dict())


def _copy_result(result: ToolResult) -> ToolResult:
    """Handler'ın tuttuğu result/data/error nesnelerini manager kaydından ayır."""
    return replace(result, error=replace(result.error) if result.error is not None else None)


def _snapshot(task: Task) -> Task:
    """Dışarıdaki kod durum kopyasını değiştirerek iç kaydı değiştiremesin."""
    return replace(task, request=_copy_request(task.request),
                   result=_copy_result(task.result) if task.result is not None else None)


def _timeout(value: float | None) -> None:
    """Bekleme sınırını kontrol et; None sınırsız, sıfır anlık kontrol demektir."""
    if value is not None and (
        type(value) not in (int, float) or value < 0 or not math.isfinite(value)
    ):
        raise TaskManagerError("invalid_timeout", "Timeout must be finite and non-negative")


class TaskManager:
    """Kısa ömürlü bir uygulama oturumunun görevlerini ve tekrar anahtarlarını tutar.

    authorize(request, tool) yalnız açık True döndürürse handler'a geçilir.
    Kimlik doğrulaması giriş adaptörünün, izin kuralları policy modülünün
    sorumluluğudur. Callback yokluğu tüm yürütmeleri reddeder.

    capacity, terminal görevler dahil tutulan kayıt sayısını sınırlar. Eski
    kayıtları sessizce silmeyiz: silersek aynı isteği ikinci kez çalıştırabiliriz.
    Bu sınır dolunca yeni kimlikler reddedilir; eski istekler hâlâ sorgulanabilir.
    """

    def __init__(self, registry: ToolRegistry, *,
                 authorize: Callable[[ToolRequest, ToolSpec], bool] | None = None,
                 capacity: int = 256) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TaskManagerError("invalid_registry", "Expected ToolRegistry")
        if authorize is not None and not callable(authorize):
            raise TaskManagerError("invalid_authorizer", "Expected authorization callback")
        if type(capacity) is not int or capacity < 1:
            raise TaskManagerError("invalid_capacity", "Capacity must be a positive integer")
        self._registry = registry
        self._authorize = authorize
        self._capacity = capacity
        self._entries: dict[str, _Entry] = {}
        self._requests: dict[tuple[str, str], str] = {}
        self._queue: deque[str] = deque()
        # Condition hem kayıtları kilitler hem boş kuyrukta worker'ın işlemciyi
        # meşgul etmeden uyumasını sağlar. Handler çalışırken bu kilit tutulmaz.
        self._condition = Condition()
        self._closing = False
        self._uncertain = False
        self._worker = Thread(target=self._run, name="taskvex-worker", daemon=False)
        self._worker.start()

    def describe_tools(self) -> list[dict]:
        """Model adaptörüne yalnız bildirim ver; handler ve yetki nesnesi verme.

        Şemalar registry'nin bağımsız kopyalarıdır. Bu katalog bir izin değildir;
        adaptör görünür alt kümeyi seçer, yürütmede mevcut policy yine denetler.
        """
        return [{"name": tool.name, "description": tool.description,
                 "parameters": tool.input_schema} for tool in self._registry.list_tools()]

    def submit(self, request: ToolRequest) -> Task:
        """Geçerli isteği sıraya al veya aynı kimlik/içerik için mevcut görevi ver.

        Tekrar anahtarı (principal, request_id). Parmak izi kanal, araç ve tüm
        parametreleri de içerir. Farklı kullanıcılar aynı request_id kullanabilir;
        aynı kullanıcı aynı kimliği farklı istek için kullanırsa hata alır.
        """
        owned = self._registry.validate_request(request)
        fingerprint = json.dumps(owned.to_dict(), sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False, allow_nan=False)
        key = (owned.principal, owned.request_id)
        with self._condition:
            if self._closing:
                raise TaskManagerError("closed", "TaskManager is closing")
            existing_id = self._requests.get(key)
            if existing_id is not None:
                entry = self._entries[existing_id]
                if entry.fingerprint != fingerprint:
                    raise TaskManagerError("request_conflict", "Request id has different content")
                return _snapshot(entry.task)
            if self._uncertain:
                raise TaskManagerError("uncertain_state", "An earlier operation has unknown outcome")
            if len(self._entries) >= self._capacity:
                raise TaskManagerError("capacity_exceeded", "Task record capacity reached")
            task = Task(task_id=uuid4().hex, request=owned)
            self._entries[task.task_id] = _Entry(task=task, fingerprint=fingerprint)
            self._requests[key] = task.task_id
            self._queue.append(task.task_id)
            self._condition.notify_all()
            return _snapshot(task)

    def _entry(self, task_id: str) -> _Entry:
        """Kilit altındaki iç yardımcı; bulunmayan görevi kontrollü hata yap."""
        if not isinstance(task_id, str) or task_id not in self._entries:
            raise TaskManagerError("unknown_task", "Task id is not known")
        return self._entries[task_id]

    def get(self, task_id: str) -> Task:
        """Görevin o andaki bağımsız kopyasını ver; bekleme veya çalıştırma yapma."""
        with self._condition:
            return _snapshot(self._entry(task_id).task)

    def wait(self, task_id: str, timeout: float | None = None) -> Task:
        """Terminal sonucu bekle; bekleme süresi dolarsa TimeoutError üret.

        Bu süre yalnız çağıranın beklemesini sınırlar. Görevi iptal etmez, unknown
        yapmaz ve çalışan thread'i öldürmez. Böylece bekleme timeout'u başarı veya
        uygulanmadı kanıtı sanılmaz. Worker kendi kuyruğunu bekleyemez.
        """
        _timeout(timeout)
        with self._condition:
            entry = self._entry(task_id)
            if current_thread() is self._worker and not entry.task.status.terminal:
                raise TaskManagerError("worker_wait", "Worker cannot wait for its own queue")
            if not self._condition.wait_for(lambda: entry.task.status.terminal, timeout):
                raise TimeoutError("Task is still unfinished")
            return _snapshot(entry.task)

    def cancel(self, task_id: str) -> Task:
        """Kuyruktaki işi bitir; çalışan işe yalnız işbirlikçi iptal sinyali gönder.

        Çalışan handler başarılı sonucu doğrulamış dönerse geç iptal bu başarıyı
        silmez. Handler durduğunu kendisi CANCELLED sonucu ile bildirmelidir.
        """
        with self._condition:
            entry = self._entry(task_id)
            if not entry.task.status.terminal:
                entry.cancel_event.set()
                if entry.task.status == TaskStatus.QUEUED:
                    self._finish(entry, self._result(entry, TaskStatus.CANCELLED, "cancelled",
                                                    "Cancelled before execution"))
                else:
                    entry.task = replace(entry.task, status=TaskStatus.CANCEL_REQUESTED)
                self._condition.notify_all()
            return _snapshot(entry.task)

    def close(self, timeout: float | None = 5.0) -> bool:
        """Yeni kabulü durdur, bekleyenleri iptal et ve worker'ın bitmesini bekle.

        True worker gerçekten kapandı demektir. False hâlâ çalışan handler var
        demektir; uygulama bunu güvenli kapanış tamamlandı diye göstermemeli.
        Thread daemon değildir: normal çıkışta sessizce terk edilmez.
        """
        _timeout(timeout)
        if current_thread() is self._worker:
            raise TaskManagerError("worker_wait", "Worker cannot close itself synchronously")
        with self._condition:
            self._closing = True
            self._cancel_pending("Manager is closing")
            for entry in self._entries.values():
                if not entry.task.status.terminal:
                    entry.cancel_event.set()
                    entry.task = replace(entry.task, status=TaskStatus.CANCEL_REQUESTED)
            self._condition.notify_all()
        self._worker.join(timeout)
        return not self._worker.is_alive()

    def __enter__(self):
        """with bloğunda kullanımı sağlar; çıkışta worker kapatılacaktır."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """with çıkışında takılı kalan worker'ı sessizce gizleme."""
        if not self.close():
            raise TaskManagerError("shutdown_timeout", "Worker is still running")

    @staticmethod
    def _result(entry: _Entry, status: TaskStatus, code: str, message: str) -> ToolResult:
        """Manager'ın ürettiği başarısız/iptal/belirsiz sonucu ortak tipe çevir."""
        return ToolResult(task_id=entry.task.task_id, status=status,
                          error=ToolError(code=code, message=message))

    def _finish(self, entry: _Entry, result: ToolResult) -> None:
        """Kilit altında terminal durumu ve sonucu birlikte yerleştir."""
        entry.task = replace(entry.task, status=result.status, result=result)

    def _cancel_pending(self, reason: str) -> None:
        """Kilit altında henüz çalıştırılmamış işleri iptal et ve kuyruğu boşalt."""
        while self._queue:
            entry = self._entries[self._queue.popleft()]
            if not entry.task.status.terminal:
                entry.cancel_event.set()
                self._finish(entry, self._result(entry, TaskStatus.CANCELLED, "cancelled", reason))

    def _execute(self, entry: _Entry) -> ToolResult:
        """Worker'ın tek handler çağrısı; kullanıcı verisini exception mesajından sızdırma."""
        started = False
        try:
            request = self._registry.validate_request(entry.task.request)
            spec = self._registry.get(request.tool)
            if iscoroutinefunction(spec.handler):
                return self._result(entry, TaskStatus.FAILED, "unsupported_handler", "Expected a synchronous handler")
            # Callback bağımsız kopyalar alır; yanlışlıkla parametreleri değiştirip
            # daha önce doğrulanan veri yerine başka veri çalıştırmasın.
            if self._authorize is None or self._authorize(_copy_request(request), replace(spec)) is not True:
                return self._result(entry, TaskStatus.FAILED, "permission_denied", "Execution not authorized")
            with self._condition:
                if entry.cancel_event.is_set():
                    return self._result(entry, TaskStatus.CANCELLED, "cancelled", "Cancelled before execution")
                # Bu noktadan sonra handler'a teslim edilmiş sayılır. Daha sonra
                # gelen iptal Event ile görülür; henüz başlamadı garantisi verilmez.
                started = True
            context = ToolContext(task_id=entry.task.task_id, request=_copy_request(request),
                                  cancel_event=entry.cancel_event)
            raw = spec.handler(request.arguments, context)
            if not isinstance(raw, ToolResult):
                # Sync fonksiyon yanlışlıkla coroutine döndürdüyse başlatmadan
                # kapat; await edilmeyen coroutine uyarısını da sahipsiz bırakma.
                if iscoroutine(raw):
                    raw.close()
                return self._result(entry, TaskStatus.UNKNOWN, "invalid_result", "Handler returned no valid result")
            result = _copy_result(raw)
            if result.task_id != entry.task.task_id:
                return self._result(entry, TaskStatus.UNKNOWN, "invalid_result", "Handler result has wrong task id")
            return result
        except RegistryError as error:
            # Handler çalıştıktan sonra atılan RegistryError da yan etkinin hiç
            # yapılmadığını kanıtlamaz; yalnız preflight hatasında FAILED denebilir.
            return self._result(entry, TaskStatus.UNKNOWN if started else TaskStatus.FAILED,
                                "handler_error" if started else error.code, "Tool validation or execution failed")
        except BaseException:
            # SystemExit gibi worker'ı öldürebilecek plugin hataları da bütün
            # kuyruğu sahipsiz bırakmasın. Ana thread'in sinyalleri burada tutulmaz.
            return self._result(entry, TaskStatus.UNKNOWN if started else TaskStatus.FAILED,
                                "handler_error" if started else "preflight_error", "Tool execution could not be confirmed")

    def _run(self) -> None:
        """Tek worker döngüsü: sırayı al, kilit dışında çalıştır, sonucu yayınla."""
        while True:
            with self._condition:
                self._condition.wait_for(lambda: bool(self._queue) or self._closing)
                if not self._queue:
                    return
                entry = self._entries[self._queue.popleft()]
                if entry.task.status.terminal:
                    continue
                entry.task = replace(entry.task, status=TaskStatus.RUNNING)
                self._condition.notify_all()
            result = self._execute(entry)
            with self._condition:
                self._finish(entry, result)
                if result.status == TaskStatus.UNKNOWN:
                    # Belirsiz dış işlem sürüyor olabilir. Worker geri döndü diye
                    # ortak kaynağı güvenli sanıp sonraki handler'ı başlatmıyoruz.
                    self._uncertain = True
                    self._cancel_pending("Earlier operation has unknown outcome")
                self._condition.notify_all()
