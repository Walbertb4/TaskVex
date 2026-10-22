"""İlk uygulama plugininin izinli kataloğu; Aşama 4'ün salt okunur başlangıcı.

Katalog, TaskVex'in desteklemeyi seçtiği uygulamaları söyler. Bilgisayarda
uygulamanın kurulu/çalışıyor olduğunu kanıtlamaz; apps.status Windows adaptörünü
kullanarak salt okunur gözlem yapar. apps.open aynı gözlemle açılışı doğrular. Araç parametresiyle
dosya yolu, shell komutu ya da ek uygulama kaydı alınmaz.
"""

from types import MappingProxyType
import time

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult


# Kimlik kalıcı makine adıdır; görünen ad çevrilebilir. Eşleme salt okunurdur
# ve değerleri metindir, böylece çağıran bir sonuç listesini değiştirerek host'un
# izinli uygulama kataloğunu genişletemez. İlk kapsam yalnız Not Defteri'dir.
APP_CATALOG = MappingProxyType({"notepad": "Notepad"})
STATUS_SCHEMA = {
    "type": "object", "properties": {"app_id": {"type": "string", "enum": list(APP_CATALOG)}},
    "required": ["app_id"], "additionalProperties": False,
}
OPEN_WAIT_SECONDS = 5.0  # Host sınırı; kullanıcı/model bunu büyütemez.


def app_catalog(arguments: dict, context: ToolContext) -> ToolResult:
    """Parametresiz katalog sorgusunu ortak sonuç ve iptal sözleşmesiyle yanıtla.

    verified=True yalnız yerleşik kataloğun okunduğunu doğrular; kurulum veya
    açık pencere kanıtı değildir. Her çağrıda bağımsız bir liste oluşturulur.
    Bu araç dosya yazmaz, uygulama taramaz ve uygulama başlatmaz.
    """
    if arguments:
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                          error=ToolError(code="invalid_arguments",
                                          message="Application catalog accepts no arguments"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    return ToolResult(
        task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
        data={"apps": [{"id": app_id, "name": name} for app_id, name in APP_CATALOG.items()]},
        evidence={"source": "builtin_allowlist"},
    )


def app_status(arguments: dict, context: ToolContext) -> ToolResult:
    """İzinli hedefin süreç/pencere durumunu gözle; gözlem hatasında başarı deme.

    Geçerli bir kapalı gözlem de SUCCEEDED'dır; bu, uygulamanın açık olduğu
    değil sorgunun tamamlandığı anlamındadır. Kısmi gözlem FAILED/data içerir;
    null alanı sıfır/kapalı diye gösterilmemelidir. Native kütüphaneler yalnız
    çağrı anında yüklenir, core başlangıcı Windows UI bağımlılığı yaratmaz.
    """
    if (set(arguments) != {"app_id"} or not isinstance(arguments["app_id"], str)
            or arguments["app_id"] not in APP_CATALOG):
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                          error=ToolError(code="invalid_arguments", message="Expected a supported app_id"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    from app.tools.local.windows_apps import observe_notepad
    try:
        data = observe_notepad(context.cancel_event)
    except InterruptedError:
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    except (NotImplementedError, OSError) as error:
        code = "platform_unsupported" if isinstance(error, NotImplementedError) else "observation_unavailable"
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                          error=ToolError(code=code, message="Application state could not be observed"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    complete = data["complete"]
    return ToolResult(task_id=context.task_id,
                      status=TaskStatus.SUCCEEDED if complete else TaskStatus.FAILED,
                      verified=complete, data=data,
                      error=None if complete else ToolError(code="observation_incomplete",
                                                           message="Application observation was incomplete"),
                      evidence={"source": "win32_process_identity+EnumWindows"})


def app_open(arguments: dict, context: ToolContext) -> ToolResult:
    """İzinli Not Defteri penceresini sağla; kabul ile tamamlanmayı ayır.

    Zaten doğrulanmış pencere varsa yeni başlatma yapılmaz. Süreç var ama
    pencere yoksa mevcut açılış beklenir; ikinci süreç istenmez. Hiç süreç
    olmadığı tam gözlemle doğrulanırsa yalnız host'un sistem başlatıcısı bir
    kez çağrılır. Başarı WS_VISIBLE pencere kanıtıdır; odak/etkileşime hazır
    garantisi değildir. Başlatmadan önceki iptal yan etki üretmez. Başlatma
    istendikten sonra iptal/hata/timeout kaydı geri almaz: UNKNOWN döner ve
    otomatik tekrar yapılmaz. Harici Not Defteri zorla kapatılmaz.
    """
    before = app_status(arguments, context)
    if before.status != TaskStatus.SUCCEEDED:
        return before

    def success(observation, requested):
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                          data={**observation, "launch_requested": requested,
                                "already_open": not requested},
                          evidence={"source": "win32_process_identity+EnumWindows",
                                    "window_observed": True, "launch_requested": requested})

    def stopped(requested, code, message):
        return ToolResult(task_id=context.task_id,
                          status=TaskStatus.UNKNOWN if requested else TaskStatus.FAILED,
                          error=ToolError(code=code, message=message),
                          data={"app_id": arguments["app_id"], "launch_requested": requested})

    if before.data["visible_window"]:
        return success(before.data, False)
    requested = False
    if not before.data["running"]:
        from app.tools.local.windows_apps import notepad_launcher, start_notepad
        try:
            executable = notepad_launcher()
        except (OSError, NotImplementedError):
            return stopped(False, "launcher_unavailable", "Notepad system launcher is unavailable")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        # Bayrağı çağrıdan önce koy: başlatma dönüşü kaybolsa da yan etki
        # yapılmış olabilir. Hata halinde ikinci start çağrısı yapılmaz.
        requested = True
        try:
            start_notepad(executable)
        except Exception:
            return stopped(True, "launch_unconfirmed", "Notepad launch could not be confirmed")

    deadline = time.monotonic() + OPEN_WAIT_SECONDS
    while True:
        if context.cancel_event.is_set():
            if requested:
                return stopped(True, "launch_unconfirmed", "Launch was requested before cancellation; check application state")
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        observed = app_status(arguments, context)
        if observed.status == TaskStatus.SUCCEEDED and observed.data["visible_window"]:
            return success(observed.data, requested)
        if observed.status == TaskStatus.CANCELLED:
            if requested:
                return stopped(True, "launch_unconfirmed", "Launch was requested before cancellation; check application state")
            return observed
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return stopped(requested, "window_unconfirmed" if requested else "window_not_observed",
                           "A Notepad window could not be confirmed; no automatic retry was made")
        context.cancel_event.wait(min(0.1, remaining))
