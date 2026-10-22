"""Salt okunur ilk sistem aracı; sürekli telemetri servisi veya UI adaptörü değil.

Standart Python'daki platform/os bilgilerini kullanır. CPU kullanım yüzdesi ve
RAM doluluğu burada ölçülmez; sıfır veya rastgele değer yerine None döner.
"""

import os
import platform

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult


def system_status(arguments: dict, context: ToolContext) -> ToolResult:
    """İşletim sistemi ve mantıksal CPU sayısını anlık sorgula; yan etki üretme.

    Parametre almaz, dosya yazmaz, cihaz açmaz. CPU sayısı sistem tarafından
    bulunamazsa None kalır; kullanılamayan ölçüm gerçek sıfırla karıştırılmaz.
    Host adı, kullanıcı adı ve sırlar bu çıktıya dahil edilmez.
    """
    if arguments:
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                          error=ToolError(code="invalid_arguments", message="System status accepts no arguments"))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
    try:
        data = {"os": platform.system() or None, "os_release": platform.release() or None,
                "architecture": platform.machine() or None, "logical_cpu_count": os.cpu_count(),
                "cpu_percent": None, "memory_percent": None}
    except OSError:
        return ToolResult(task_id=context.task_id, status=TaskStatus.FAILED,
                          error=ToolError(code="system_unavailable", message="System information is unavailable"))
    return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                      data=data, evidence={"source": "python.platform+os"})
