"""Not ekleme/listeleme/güncelleme/silme; not dosyasının şeması burada.

JSON store dosya bütünlüğünü, registry giriş biçimini, policy ise izni denetler.
Bu modül UI import etmez ve kendi worker'ını başlatmaz. Bütün mutasyonlar tek
TaskManager üzerinden sıralanmalıdır; aynı dosyaya paralel yazar desteklenmez.
Eski UI notları ancak host'un açık aktarım akışıyla initialize'a verilir.
"""

from uuid import uuid4
from datetime import datetime, timezone

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult
from app.storage.json_store import JsonStore, StoreError


MAX_NOTE_LENGTH = 10_000
CREATED_AT_SCHEMA = {"anyOf": [{"type": "null"}, {"type": "string",
    "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"}]}
ADD_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string", "minLength": 1,
                              "maxLength": MAX_NOTE_LENGTH, "pattern": r"\S"}},
    "required": ["text"],
    "additionalProperties": False,
}
UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "pattern": r"\S"},
        "text": ADD_SCHEMA["properties"]["text"],
        "done": {"type": "boolean"},
    },
    "required": ["id"],
    "anyOf": [{"required": ["text"]}, {"required": ["done"]}],
    "additionalProperties": False,
}
DELETE_SCHEMA = {
    "type": "object",
    "properties": {"id": {"type": "string", "pattern": r"\S"}},
    "required": ["id"],
    "additionalProperties": False,
}
INITIALIZE_SCHEMA = {
    "type": "object",
    "properties": {"notes": {"anyOf": [
        {"type": "null"},
        {"type": "array", "items": {
            "type": "object", "properties": {
                "text": ADD_SCHEMA["properties"]["text"], "done": {"type": "boolean"},
                "created_at": CREATED_AT_SCHEMA},
            "required": ["text", "done"], "additionalProperties": False,
        }},
    ]}},
    "required": ["notes"], "additionalProperties": False,
}
REPLACE_SCHEMA = {
    "type": "object", "properties": {"notes": {"type": "array", "items": {
        "type": "object", "properties": {
            "id": {"type": "string", "pattern": r"\S"},
            "text": ADD_SCHEMA["properties"]["text"], "done": {"type": "boolean"},
            "created_at": CREATED_AT_SCHEMA},
        "required": ["id", "text", "done"], "additionalProperties": False,
    }}}, "required": ["notes"], "additionalProperties": False,
}


def _valid_text(value) -> bool:
    """Boş/yalnız boşluk veya aşırı uzun metinleri reddet; asıl metni değiştirme."""
    return isinstance(value, str) and bool(value.strip()) and len(value) <= MAX_NOTE_LENGTH


def _valid_created_at(value) -> bool:
    """UTC tarihini gerçek takvimle doğrula; eski kaydın bilinmeyen tarihi null olabilir.

    Yalnız YYYY-MM-DDTHH:mm:ss.sssZ biçimi kullanılır. Gün/ay taşması ve yerel
    saat belirsizliği kabul edilmez; kayıt okurken geçmişe yapay tarih yazılmaz.
    """
    if value is None:
        return True
    if not isinstance(value, str) or len(value) != 24 or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.isoformat(timespec="milliseconds").replace("+00:00", "Z") == value
    except ValueError:
        return False


def _error(context: ToolContext, code: str, message: str,
           status: TaskStatus = TaskStatus.FAILED) -> ToolResult:
    """İçerik/dosya yolu sızdırmadan beklenen hatayı ortak sonuca dönüştür."""
    return ToolResult(task_id=context.task_id, status=status,
                      error=ToolError(code=code, message=message))


class NotesTools:
    """Host'un verdiği tek JsonStore üzerinde not CRUD işlemlerini yürütür.

    Kalıcı biçim: {notes: [{id, text, done, created_at?}]}.
    created_at yeni kayıtta backend'in UTC saatidir; eski kayıtta eksik/null
    gerçek oluşturulma zamanının bilinmediği anlamına gelir.
    id kayıt oluşturulurken üretilir ve yeniden açılışta değişmez. UI'ın eski
    {t,d} biçimini native adaptör dönüştürür. ui_migrated işareti aktarımın
    tamamlandığını notlarla aynı atomik dosyada tutar; ayrı işaret dosyası yoktur.
    """

    def __init__(self, store: JsonStore) -> None:
        """Dosya yolunu host seçer; araç parametresiyle dosya yolu alınmaz."""
        self._store = store

    def _load_document(self) -> dict:
        """JSON geçerli olsa bile bozuk not kayıtlarını boş sayarak silme.

        Eksik dosya yeni depo demektir. Var olan dosyada notes listesi zorunlu;
        tanınmayan alanları da üstüne yazıp kaybetmemek için açıkça reddederiz.
        """
        data = self._store.read()
        if data is None:
            return {"notes": []}
        if (not {"notes"} <= set(data) <= {"notes", "ui_migrated"}
                or type(data["notes"]) is not list
                or ("ui_migrated" in data and type(data["ui_migrated"]) is not bool)):
            raise StoreError("invalid_notes", "Stored notes have an invalid shape")
        seen = set()
        for note in data["notes"]:
            if (type(note) is not dict or not {"id", "text", "done"} <= set(note) <= {"id", "text", "done", "created_at"}
                    or not isinstance(note["id"], str) or not note["id"].strip()
                    or note["id"] in seen or not _valid_text(note["text"])
                    or type(note["done"]) is not bool or not _valid_created_at(note.get("created_at"))):
                raise StoreError("invalid_notes", "Stored notes have an invalid record")
            seen.add(note["id"])
        return data

    def _load(self) -> list[dict]:
        """CRUD çağıranları için doğrulanmış belgeden yalnız not listesini al."""
        return self._load_document()["notes"]

    def initialize(self, arguments: dict, context: ToolContext) -> ToolResult:
        """notes:null ile oku; açık aktarımda eski notları bir kez ekle.

        Eski core notları korunur; aynı metinli eski UI notları da ayrı UUID
        alır. ui_migrated ve eklenen notlar tek replace ile yazılır. Yazma
        sonrası doğrulama belirsizse otomatik tekrar yoktur. Yeniden açılışta
        işaret varsa gönderilen eski liste yeniden eklenmez. Bu işaret normal
        ekle/güncelle/sil işlemleriyle, son not silinse bile korunur.
        """
        incoming = arguments.get("notes")
        if (set(arguments) != {"notes"} or (incoming is not None and (
                type(incoming) is not list or any(
                    type(item) is not dict or not {"text", "done"} <= set(item) <= {"text", "done", "created_at"}
                    or not _valid_text(item["text"]) or type(item["done"]) is not bool
                    or not _valid_created_at(item.get("created_at"))
                    for item in incoming)))):
            return _error(context, "invalid_arguments", "Expected valid legacy notes or null")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            document = self._load_document()
            if incoming is not None and not document.get("ui_migrated", False):
                updated = [*document["notes"], *[{"id": uuid4().hex, **item} for item in incoming]]
                return self._commit(updated, None, context, migrated=True)
        except StoreError as error:
            return _error(context, error.code, str(error))
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                          data={"notes": document["notes"],
                                "migrated": document.get("ui_migrated", False)},
                          evidence={"store_read": True})

    def replace(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Açık yedek içe aktarımında tam listeyi tek atomik yazmayla değiştir.

        Kimlikler korunur; eski kimliksiz yedeğe kimliği UI adaptörü üretir.
        Yinelenen id ve bozuk kayıtlar hiçbir yazımdan önce reddedilir. Bozuk
        mevcut depo yine ezilmez; reset/onarım yerine geçen bir araç değildir.
        """
        items = arguments.get("notes")
        if (set(arguments) != {"notes"} or type(items) is not list or any(
                type(n) is not dict or not {"id", "text", "done"} <= set(n) <= {"id", "text", "done", "created_at"}
                or not isinstance(n["id"], str) or not n["id"].strip()
                or not _valid_text(n["text"]) or type(n["done"]) is not bool
                or not _valid_created_at(n.get("created_at")) for n in items)
                or len({n["id"] for n in items}) != len(items)):
            return _error(context, "invalid_arguments", "Expected valid notes with unique ids")
        return self._commit(items, None, context, migrated=True)

    def list(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Diskteki güncel listeyi döndür; eksik depoyu okurken dosya oluşturma."""
        if arguments:
            return _error(context, "invalid_arguments", "Notes list accepts no arguments")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED,
                          verified=True, data={"notes": notes}, evidence={"store_read": True})

    def add(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Notu kaydet ve geri okuyarak doğrula; kayıt sonrası belirsizlikte dur.

        Yazmadan önce iptal edilirse dosyaya dokunulmaz. Yazma bittikten sonraki
        geç iptal gerçek kaydı geri almış sayılmaz. Kayıt yapılmışken tekrar
        okuma başarısızsa FAILED değil UNKNOWN döner; otomatik tekrar yapılmaz.
        """
        if set(arguments) != {"text"} or not _valid_text(arguments["text"]):
            return _error(context, "invalid_arguments", "Expected non-blank note text")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
            note = {"id": uuid4().hex, "text": arguments["text"], "done": False,
                    "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")}
            updated = [*notes, note]
        except StoreError as error:
            return _error(context, error.code, str(error))
        return self._commit(updated, note, context)

    def update(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Sabit id ile metni ve/veya tamamlanma durumunu değiştir.

        Eksik alan korunur; done=False notu yeniden açar. Metin eşitliği ya da
        liste sırası hedef seçmez, böylece aynı metinli iki not karışmaz. Hedef
        yoksa yeni not yaratılmaz; not_found döner ve dosyaya dokunulmaz.
        """
        if (not self._valid_target(arguments)
                or not set(arguments) <= {"id", "text", "done"}
                or not ({"text", "done"} & set(arguments))
                or ("text" in arguments and not _valid_text(arguments["text"]))
                or ("done" in arguments and type(arguments["done"]) is not bool)):
            return _error(context, "invalid_arguments", "Expected id and valid text or done")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        original = next((note for note in notes if note["id"] == arguments["id"]), None)
        if original is None:
            return _error(context, "not_found", "Note was not found")
        note = {**original, **arguments}
        updated = [note if item["id"] == note["id"] else item for item in notes]
        return self._commit(updated, note, context)

    def delete(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Yalnız verilen id'yi sil; aynı metinli diğer notları olduğu gibi koru.

        Bulunamayan hedef hata verir. Aynı request_id'nin tekrarını TaskManager
        mevcut oturumda önler; bu handler kendi kendine tekrar deneme yapmaz.
        """
        if not self._valid_target(arguments) or set(arguments) != {"id"}:
            return _error(context, "invalid_arguments", "Expected a note id")
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            notes = self._load()
        except StoreError as error:
            return _error(context, error.code, str(error))
        note = next((item for item in notes if item["id"] == arguments["id"]), None)
        if note is None:
            return _error(context, "not_found", "Note was not found")
        updated = [item for item in notes if item["id"] != note["id"]]
        return self._commit(updated, note, context)

    @staticmethod
    def _valid_target(arguments: dict) -> bool:
        """Registry dışında doğrudan çağrıda da boş/yanlış kimliği reddet."""
        return isinstance(arguments.get("id"), str) and bool(arguments["id"].strip())

    def _commit(self, updated: list[dict], note: dict | None, context: ToolContext,
                *, migrated: bool = False) -> ToolResult:
        """Bütün not mutasyonlarında aynı iptal/yazma/geri okuma sözleşmesini uygula.

        Başarıdaki note, ekleme/güncellemede yeni kayıt; silmede silinen kayıttır.
        note=None toplu aktarım/restore içindir; doğrulanmış tam listeyi döndürür.
        Geri okuma başarısızsa yazılmış veri geri alınmaz ve UNKNOWN döner.
        """
        if context.cancel_event.is_set():
            return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
        try:
            # Aktarım işareti metadata'dır; sıradan CRUD onu düşürürse eski UI
            # önbelleği yeniden açılışta ikinci kez eklenebilir. Aynen koru.
            document = {**self._load_document(), "notes": updated}
            if migrated:
                document["ui_migrated"] = True
            if context.cancel_event.is_set():
                return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
            self._store.write(document)
        except StoreError as error:
            return _error(context, error.code, str(error))
        try:
            if self._load_document() != document:
                raise StoreError("commit_unverified", "Saved notes could not be verified")
        except StoreError:
            return _error(context, "commit_unverified", "Saved notes could not be verified",
                          TaskStatus.UNKNOWN)
        return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED,
                          verified=True,
                          data={"note": note} if note is not None else {"notes": updated, "migrated": True},
                          evidence={"persisted": True, "read_back": True,
                                    **({"note_id": note["id"]} if note is not None else {})})
