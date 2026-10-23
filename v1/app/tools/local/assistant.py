"""Asistanın sohbet kontrollerini ortak araç hattından isteyen yerel araç.

Bu araç uykuya geçirmez, mikrofon açmaz veya Live bağlantısını kapatmaz.
Yalnız doğrulanmış bir geçiş isteği üretir. Gerçek uygulama, başarılı yanıt
ve ses bitişinden sonra mevcut UI/host yaşam döngüsü sahibindedir.
"""
from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult


SLEEP_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"mode": {"type": "string", "enum": ["once", "persistent", "off"],
        "description": "once: sleep until woken; persistent: return to sleep after each addressed interaction for this chat; off: disable that return preference, not the idle timer."}},
    "required": ["mode"],
}


def request_sleep_mode(arguments: dict, context: ToolContext) -> ToolResult:
    """Kipi doğrula ve istek üret; başarılı sonuç gerçek uyku kanıtı değildir.

    TaskManager başarısı bu yan etkisiz isteğin kabulüdür. applied=false alanı,
    modelin henüz uyunduğunu iddia etmemesi için özellikle sonuçta bulunur.
    Registry şema kontrolüne ek olarak doğrudan çağrıda da hatalı kip reddedilir.
    """
    if set(arguments) != {"mode"} or arguments["mode"] not in ("once", "persistent", "off"):
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
            error=ToolError(code="invalid_arguments", message="Expected a supported sleep mode"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
        data={"mode": arguments["mode"], "apply_after": "reply_playback", "applied": False},
        evidence={"validated_request": True})
