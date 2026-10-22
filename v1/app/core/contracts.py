"""TaskVex bileşenlerinin birbiriyle konuşurken kullanacağı ortak veri biçimleri.

Sözleşme, örneğin bir araç isteğinde hangi alanların bulunacağını ve hangi
sonuçların geçerli olduğunu belirler. UI, model adaptörü ve ileride TaskManager
aynı biçimleri kullanacak; her bileşen kendi sonuç formatını icat etmeyecek.

Bu dosya araç çalıştırmaz, izin vermez ve diske yazmaz. Yalnız verilen verinin
temel biçimini ve alanlar arasındaki tutarlılığı kontrol eder. Araç parametreleri
için şema doğrulaması registry'de, görev yürütme TaskManager'dadır.
"""

from __future__ import annotations

# Tip açıklamaları sözleşmeyi okuyana ve editöre yardımcı olur; tek başına
# çalışma zamanında doğrulama yapmaz. Bu yüzden aşağıda açık kontroller de var.

import math
import re
from dataclasses import dataclass, field
from enum import StrEnum
from threading import Event
from typing import Any, Callable, cast


class ContractError(ValueError):
    """Geçersiz sözleşme verisini sıradan bir araç/servis hatasından ayırır.

    Örneğin boş request_id bu hatayı üretir. Ağ kopması veya disk dolması ise
    geçerli bir isteğin yürütülmesi sırasında oluşabilecek başka tür sorunlardır.
    """


def _text(value: Any, name: str) -> None:
    """Bir alanın boş olmayan metin olduğunu kontrol et; geçersizse hata ver.

    name, hata mesajında alanı belirtir. Fonksiyon değeri kırpıp değiştirmez;
    strip() yalnız tamamen boşluklardan oluşan girdiyi fark etmek için kullanılır.
    """
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")


def _tool_name(value: Any) -> None:
    """notes.add gibi alan ve işlem içeren araç adlarını kabul et.

    Nokta ad alanlarını ayırır: notes.add ve notes.list aynı alanın iki işlemi.
    fullmatch bütün metnin kurala uymasını ister; kısmen uygun bir ad yeterli değil.
    Bu ad kontrolü izin kontrolü değildir; geçerli ad araç çalıştırma yetkisi vermez.
    """
    if not isinstance(value, str) or len(value) > 128 or not re.fullmatch(
        r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+", value
    ):
        raise ContractError("tool name must be namespaced, for example notes.add")


def _json_copy(value: Any, active: set[int] | None = None) -> Any:
    """JSON'a uygun veriyi doğrula ve iç içe listeleri/sözlükleri kopyala.

    Böylece çağıran kendi sözlüğünü sonradan değiştirse bile oluşturulan kayıt
    değişmez. Tanınmayan nesneleri metne çevirmeyiz; yanlış veri sessizce düzelmiş
    gibi görünmek yerine ContractError üretir.

    active, şu anda içinden geçtiğimiz kapsayıcı nesnelerin kimliklerini tutar.
    Tüm görülmüş nesnelerin listesi değildir: aynı liste iki farklı alanda
    paylaşılabilir; yalnız kendisine geri dönen veri yapısı yasaktır.
    """
    # type(...) ile tam türü kontrol ediyoruz. Özel sınıfların bu sınıflardan
    # türemiş olması onları otomatik olarak desteklenen JSON verisi yapmaz.
    # None, False ve 0 geçerli ve farklı değerlerdir; hepsi ayrı ayrı korunur.
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    # NaN ve sonsuzluk yukarıdaki koşulu geçemez. Liste/sözlük de değillerse
    # burada reddedilirler; fonksiyonun devamında yalnız kapsayıcılar kalır.
    if type(value) not in (dict, list):
        raise ContractError("expected JSON values with finite numbers")
    active = set() if active is None else active
    # Örneğin items.append(items) kendi içine dönen bir liste oluşturur.
    # Bunu fark etmezsek recursive çağrı, yani fonksiyonun kendisini çağırması,
    # aynı verinin içinde ilerleyemeden devam eder.
    if id(value) in active:
        raise ContractError("cyclic JSON data is not allowed")
    active.add(id(value))
    try:
        if isinstance(value, list):
            # List comprehension: listedeki her öğeyi aynı doğrulama/kopyalama
            # işleminden geçir ve yeni bir liste oluştur. Alt listeler de kopyalanır.
            return [_json_copy(item, active) for item in value]
        # Önceki kontroller nedeniyle burada sözlük kaldığını biliyoruz. cast
        # bunu Pylance'a bildirir; veriyi dönüştürmez ve ek doğrulama yapmaz.
        mapping = cast(dict[str, Any], value)
        # JSON nesnesinde anahtarlar metin olmalı. Örneğin 1 anahtarını "1"
        # yaparak anlamını sessizce değiştirmek yerine yanlış türü reddederiz.
        if any(type(key) is not str for key in mapping):
            raise ContractError("JSON object keys must be strings")
        return {key: _json_copy(item, active) for key, item in mapping.items()}
    finally:
        # Başarılı dönüşte de hatada da bu nesne mevcut ziyaret yolundan çıkar.
        # Böylece sonraki bağımsız dalda aynı nesneyi görmek döngü sanılmaz.
        active.remove(id(value))


def copy_json(value: Any) -> Any:
    """Diğer modüllere de aynı JSON doğrulama/kopyalama kuralını sun.

    Kayıt katmanı da sözleşmeler gibi tuple, döngü, metin olmayan anahtar ve
    sonsuz sayıları reddetsin. Özel active parametresi dışarı açılmaz.
    """
    return _json_copy(value)


def _object(value: Any) -> dict[str, Any]:
    """Kökte özellikle bir JSON nesnesi, yani Python dict gerektiğinde kullan.

    _json_copy tek başına liste veya null da kabul eder. arguments gibi nesne
    olması gereken alanlarda bu daha dar kontrolü kullanırız.
    """
    if type(value) is not dict:
        raise ContractError("expected a JSON object")
    return _json_copy(value)


class TaskStatus(StrEnum):
    """Görev durumlarının yazımını sabitleyen metin tabanlı enum.

    Enum, izinli değerlerin isimlendirilmiş listesidir. SUCCEEDED yerine farklı
    yerlerde "done", "success" yazılmasını önler. .value taşıma için metni verir.
    """
    # Bu ilk dört durumda görev henüz kesin bir sonuç bildirmemiştir.
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    CANCEL_REQUESTED = "cancel_requested"
    # Terminal, bu yürütme kaydının sonuçlandığı anlamına gelir. UNKNOWN'da ise
    # dış dünyadaki sonucun bilinmediğini bildiririz; otomatik tekrar yapılmaz.
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

    @property
    def terminal(self) -> bool:
        """Durum bir sonuç durumuysa True döndür; hiçbir görevi çalıştırma."""
        return self in (
            TaskStatus.SUCCEEDED, TaskStatus.FAILED,
            TaskStatus.CANCELLED, TaskStatus.UNKNOWN,
        )


# dataclass alanlardan constructor/eşitlik gibi standart metotları üretir.
# kw_only=True çağrılarda request_id=... gibi alan adlarını zorunlu kılar.
# frozen=True alanın sonradan atanmasını engeller; iç sözlükleri derin dondurmaz.
# Dolayısıyla sözlük/listeleri yerinde değiştirmeden, yeni kayıt üreterek kullanırız.
@dataclass(frozen=True, kw_only=True)
class ToolRequest:
    """Bir araçtan ne istendiğini taşır; isteği henüz yürütmez.

    request_id giriş isteğinin kimliği, source geldiği kanal, principal isteğin
    sahibi, tool çağrılacak araç, arguments da o aracın parametreleridir.
    Kimlikler burada yalnız biçim olarak kontrol edilir. Kullanıcıyı gerçekten
    doğrulamak giriş adaptörünün ve policy'nin sorumluluğudur.
    """
    request_id: str
    source: str
    principal: str
    tool: str
    # default_factory her istek için ayrı sözlük üretir; istekler ortak bir
    # varsayılan sözlüğü yanlışlıkla paylaşmaz.
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """dataclass constructor'ı alanları atadıktan hemen sonra doğrula."""
        for name in ("request_id", "source", "principal"):
            _text(getattr(self, name), name)
        _tool_name(self.tool)
        # frozen kayıt kurulurken doğrulanmış kopyayı yerleştiriyoruz. Bu özel
        # atama, normal kullanımda kaydı değiştirmek için açılmış bir yol değildir.
        object.__setattr__(self, "arguments", _object(self.arguments))

    def to_dict(self) -> dict[str, Any]:
        """Taşımaya uygun sözlük kopyası ver; JSON metni üretmek başka adımdır."""
        return {
            "request_id": self.request_id, "source": self.source,
            "principal": self.principal, "tool": self.tool,
            "arguments": _object(self.arguments),
        }


@dataclass(frozen=True, kw_only=True)
class ToolError:
    """Makinenin işleyebileceği hata kodu ve okunabilir neden.

    code örneğin not_found olabilir; message nedeni, details ek veriyi taşır.
    Bu alanlara API anahtarı/token konmamalı; bu sınıf gizli bilgi maskelemez.
    """
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Kod/nedeni kontrol et ve ek veriyi çağırandan bağımsız kopyala."""
        _text(self.code, "error code")
        _text(self.message, "error message")
        object.__setattr__(self, "details", _object(self.details))

    def to_dict(self) -> dict[str, Any]:
        """Hata nesnesini JSON uyumlu, bağımsız bir sözlüğe çevir."""
        return {"code": self.code, "message": self.message, "details": _object(self.details)}


@dataclass(frozen=True, kw_only=True)
class ToolResult:
    """Bir aracın terminal sonucunu taşır; kabul veya bekleme bildirimi değildir.

    data araç çıktısıdır; evidence gözlenen kayıt/pencere gibi kanıt bilgisidir.
    verified, yalnız başarılı tamamlanmanın doğrulandığını belirtir. True yazmak
    tek başına kanıt yaratmaz; gerçek gözlemi yapmak handler'ın sorumluluğudur.
    """
    task_id: str
    status: TaskStatus
    verified: bool = False
    data: Any = None
    error: ToolError | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Yanlış durum/başarı/hata birleşimlerini kayıt oluşmadan reddet."""
        _text(self.task_id, "task_id")
        if not isinstance(self.status, TaskStatus) or not self.status.terminal:
            raise ContractError("tool result requires a terminal TaskStatus")
        if type(self.verified) is not bool:
            # Python'da bool, int'in alt türüdür. Bu yüzden yalnız bool kabul
            # ediyoruz; 1 değerinin True yerine kullanılmasına izin vermiyoruz.
            raise ContractError("verified must be boolean")
        if self.error is not None and not isinstance(self.error, ToolError):
            raise ContractError("error must be ToolError or None")
        if self.status == TaskStatus.SUCCEEDED:
            # "İstek kabul edildi" cevabının tamamlandıya yuvarlanmasını önler.
            if not self.verified or self.error is not None:
                raise ContractError("success requires verified=True and no error")
        elif self.verified:
            raise ContractError("verified describes successful completion only")
        if self.status in (TaskStatus.FAILED, TaskStatus.UNKNOWN) and self.error is None:
            # FAILED'da hata nedeni, UNKNOWN'da neden doğrulanamadığı gerekir.
            raise ContractError("failed/unknown results require an error or uncertainty reason")
        object.__setattr__(self, "data", _json_copy(self.data))
        object.__setattr__(self, "evidence", _object(self.evidence))

    def to_dict(self) -> dict[str, Any]:
        """Enum/hata nesnesini sade veriye indir; iç verileri yeniden kopyala."""
        return {
            "task_id": self.task_id, "status": self.status.value,
            "verified": self.verified, "data": _json_copy(self.data),
            "error": self.error.to_dict() if self.error else None,
            "evidence": _object(self.evidence),
        }


@dataclass(frozen=True, kw_only=True)
class Task:
    """Bir görevin o andaki tutarlı görüntüsü; TaskManager'ın kendisi değildir.

    task_id yürütmenin kimliği, request giriş isteğidir; iki kimlik farklı olabilir.
    Bu sınıf kuyruk veya izin verilen durum geçişlerini yönetmez. TaskManager,
    yeni durum için yeni kayıt üretirken aşağıdaki tutarlılık koşulları korunur.
    """
    task_id: str
    request: ToolRequest
    status: TaskStatus = TaskStatus.QUEUED
    result: ToolResult | None = None

    def __post_init__(self) -> None:
        """Sonuç varsa bu göreve ve durumuna ait olduğundan emin ol."""
        _text(self.task_id, "task_id")
        if not isinstance(self.request, ToolRequest) or not isinstance(self.status, TaskStatus):
            raise ContractError("task requires ToolRequest and TaskStatus")
        if self.status.terminal:
            # Başka görevin sonucu veya başarısız görevde başarılı sonuç gibi
            # karışıklıklar kullanıcıya yanlış durum gösterilmesine yol açabilir.
            if not isinstance(self.result, ToolResult):
                raise ContractError("terminal task requires a result")
            if self.result.task_id != self.task_id or self.result.status != self.status:
                raise ContractError("task and result identity/status must match")
        elif self.result is not None:
            raise ContractError("unfinished task cannot have a terminal result")

    def to_dict(self) -> dict[str, Any]:
        """Görevi, isteği ve varsa sonucu ortak taşıma biçimine dönüştür."""
        return {
            "task_id": self.task_id, "request": self.request.to_dict(),
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
        }


@dataclass(frozen=True, kw_only=True)
class ToolContext:
    """Yürütücünün handler'a verdiği çalışma bağlamı; dışarı gönderilecek veri değil.

    cancel_event.set() iptal talebini işaretler; thread'i otomatik durdurmaz.
    Handler uygun aralarda sinyali kontrol ederek güvenle durmalıdır. deadline
    varsa time.monotonic() saatine ait son süredir; Unix tarih/saat değeri değildir.
    """
    task_id: str
    request: ToolRequest
    # Her bağlam ayrı Event alır; bir görevin iptali diğerine yayılmaz.
    # repr/compare kapalı: bu çalışma sinyali görünüm/eşitlik verisi değildir.
    cancel_event: Event = field(default_factory=Event, repr=False, compare=False)
    deadline: float | None = None

    def __post_init__(self) -> None:
        """Bağlam türlerini kontrol et; süreyi bekletme veya iptal çalıştırma."""
        _text(self.task_id, "task_id")
        if not isinstance(self.request, ToolRequest) or not isinstance(self.cancel_event, Event):
            raise ContractError("context requires ToolRequest and cancellation Event")
        if self.deadline is not None and (
            type(self.deadline) not in (int, float) or not math.isfinite(self.deadline)
            or self.deadline < 0
        ):
            raise ContractError("deadline must be a finite non-negative monotonic timestamp")


@dataclass(frozen=True, kw_only=True)
class ToolSpec:
    """Registry'ye kaydolacak aracın tarifi; bu nesneyi kurmak aracı çağırmaz.

    input_schema parametre biçimini tarif eden JSON Schema nesnesidir. handler,
    (arguments, context) alıp ToolResult döndürecek fonksiyon olarak tanımlanır.
    required_capabilities gerekli yetkiler, exclusive_resources eşzamanlı kullanımda
    korunacak kaynaklardır. Bunları bildirmek yetki veya kaynak kilidi sağlamaz;
    uygulamayı policy ve TaskManager yapacak.
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any], ToolContext], ToolResult]
    required_capabilities: tuple[str, ...] = ()
    exclusive_resources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Bildirim biçimini kontrol et; tam parametre şema denetimini registry yapar."""
        _tool_name(self.name)
        _text(self.description, "description")
        schema = _object(self.input_schema)
        # Yalnız kök nesne şartını denetliyoruz. Örneğin required alanının veya
        # gelen arguments'ın şemaya uyumlu olduğunu bu kontrol tek başına söylemez.
        if schema.get("type") != "object":
            raise ContractError("input_schema must declare type=object")
        if not callable(self.handler):
            # callable fonksiyon gibi çağrılabilir olduğunu belirtir; imzasını
            # veya gerçekten ToolResult döndüreceğini burada kanıtlamaz.
            raise ContractError("handler must be callable")
        for name in ("required_capabilities", "exclusive_resources"):
            # Bildirim listeleri tuple olmalı: yanlışlıkla ekleme/silme yerine
            # yeni bildirim oluşturulur. Boş ve yinelenen değerler kabul edilmez.
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise ContractError(f"{name} must be a tuple")
            for value in values:
                _text(value, name)
            if len(values) != len(set(values)):
                raise ContractError(f"{name} contains duplicates")
        object.__setattr__(self, "input_schema", schema)
