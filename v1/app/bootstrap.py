"""İlk core'u somut bileşenlerle kur; native pencere/model başlatma.

create_core yalnız açıkça tanımlı güvenilir yerel araçları kaydeder. Plugin taraması, dinamik
import veya ayrı bir dispatcher yoktur. Dönen TaskManager'ın yaşam döngüsü
çağırana aittir: with bloğu veya close kullanılmalıdır.
"""

from app.config import get_data_home
from app.core.contracts import ToolSpec
from app.policy.engine import PolicyEngine
from app.session.tool_registry import ToolRegistry
from app.storage.json_store import JsonStore
from app.tasks.manager import TaskManager
from app.tools.local.notes import ADD_SCHEMA, DELETE_SCHEMA, INITIALIZE_SCHEMA, REPLACE_SCHEMA, UPDATE_SCHEMA, NotesTools
from app.tools.local.telemetry import system_status
from app.tools.local.apps import STATUS_SCHEMA, app_catalog, app_open, app_status


def create_core(*, principal: str = "local-user") -> TaskManager:
    """Tek yerel kullanıcı için registry + policy + worker'ı birleştir.

    Veriler get_data_home()/notes.json'a gider. Kurulum dosya oluşturmaz; ilk
    başarılı not mutasyonu veya onaylı aktarım yazacaktır. principal güvenilir host tarafından seçilir;
    bu parametreyi modelin/kullanıcının gönderdiği payload'dan alma. Kaynak
    yalnız desktop'tır. Worker tüm kayıt ve izin kurulumu bittikten sonra açılır.
    """
    notes = NotesTools(JsonStore(get_data_home() / "notes.json"))
    registry = ToolRegistry()
    registry.register(ToolSpec(
        name="apps.open", description="İzinli Not Defteri'ni bir kez aç ve süreç/pencere kanıtıyla doğrula",
        input_schema=STATUS_SCHEMA, handler=app_open,
        required_capabilities=("apps.read", "apps.launch"), exclusive_resources=("apps.notepad",),
    ))
    registry.register(ToolSpec(
        name="apps.status", description="İzinli uygulamanın Windows süreç/pencere durumunu gözle",
        input_schema=STATUS_SCHEMA, handler=app_status,
        required_capabilities=("apps.read",),
    ))
    registry.register(ToolSpec(
        name="apps.catalog", description="Desteklenen uygulamaları listele; kurulum/çalışma durumu sorgusu değildir",
        input_schema={"type": "object", "additionalProperties": False}, handler=app_catalog,
        required_capabilities=("apps.read",),
    ))
    registry.register(ToolSpec(
        name="notes.replace", description="Açık yedek yüklemesinde not listesini değiştir",
        input_schema=REPLACE_SCHEMA, handler=notes.replace,
        required_capabilities=("notes.write",), exclusive_resources=("notes",),
    ))
    registry.register(ToolSpec(
        name="notes.initialize", description="UI not aktarımını oku veya açık onaydan sonra bir kez uygula",
        input_schema=INITIALIZE_SCHEMA, handler=notes.initialize,
        required_capabilities=("notes.write",), exclusive_resources=("notes",),
    ))
    registry.register(ToolSpec(
        name="notes.add", description="Kalıcı bir yerel not ekle",
        input_schema=ADD_SCHEMA, handler=notes.add,
        required_capabilities=("notes.write",), exclusive_resources=("notes",),
    ))
    registry.register(ToolSpec(
        name="notes.update", description="Sabit kimlikle bir yerel notu güncelle",
        input_schema=UPDATE_SCHEMA, handler=notes.update,
        required_capabilities=("notes.write",), exclusive_resources=("notes",),
    ))
    registry.register(ToolSpec(
        name="notes.delete", description="Sabit kimlikle bir yerel notu sil",
        input_schema=DELETE_SCHEMA, handler=notes.delete,
        required_capabilities=("notes.write",), exclusive_resources=("notes",),
    ))
    registry.register(ToolSpec(
        name="notes.list", description="Yerel notları listele",
        input_schema={"type": "object", "additionalProperties": False}, handler=notes.list,
        required_capabilities=("notes.read",), exclusive_resources=("notes",),
    ))
    registry.register(ToolSpec(
        name="system.status", description="Salt okunur sistem bilgilerini sorgula",
        input_schema={"type": "object", "additionalProperties": False}, handler=system_status,
        required_capabilities=("system.read",),
    ))
    policy = PolicyEngine(principal=principal,
                          capabilities=frozenset({"notes.read", "notes.write", "system.read", "apps.read", "apps.launch"}))
    return TaskManager(registry, authorize=policy.authorize)
