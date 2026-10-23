"""İlk yerel araçlar için açık izin listesi; varsayılan karar rettir.

Registry parametre biçimini, bu modül ise işlemi kimin isteyebileceğini denetler.
TaskManager, handler'ı çağırmadan hemen önce authorize metodunu kullanır.
Modelin gönderdiği bir alan veya pluginin yetki bildirimi izin yaratmaz.

principal/source değerleri güvenilir giriş adaptöründen gelmelidir; burada bir
metnin eşleşmesi gerçek kullanıcı kimlik doğrulaması veya Python sandbox'ı değildir.
"""

from dataclasses import dataclass
from types import MappingProxyType

from app.core.contracts import ContractError, ToolRequest, ToolSpec


# Araç -> gereken yetki eşlemesini core belirler. Plugin kendi bildiriminden
# yetki türetemez; boş veya farklı required_capabilities bildirimi de reddedilir.
_TOOL_CAPABILITIES = MappingProxyType({
    "assistant.request_sleep_mode": frozenset({"assistant.control"}),
    "assistant.request_shutdown": frozenset({"assistant.control"}),
    "apps.catalog": frozenset({"apps.read"}),
    "apps.status": frozenset({"apps.read"}),
    "apps.open": frozenset({"apps.read", "apps.launch"}),
    "notes.add": frozenset({"notes.write"}),
    "notes.update": frozenset({"notes.write"}),
    "notes.delete": frozenset({"notes.write"}),
    "notes.initialize": frozenset({"notes.write"}),
    "notes.replace": frozenset({"notes.write"}),
    "notes.list": frozenset({"notes.read"}),
    "notes.select": frozenset({"notes.read"}),
    "notes.delete_many": frozenset({"notes.write"}),
    "notes.complete_many": frozenset({"notes.write"}),
    "clocks.create": frozenset({"clocks.write"}),
    "clocks.control": frozenset({"clocks.write"}),
    "clocks.list": frozenset({"clocks.read"}),
    "system.status": frozenset({"system.read"}),
})
_KNOWN_CAPABILITIES = frozenset().union(*_TOOL_CAPABILITIES.values())


@dataclass(frozen=True, kw_only=True)
class PolicyEngine:
    """Tek yerel kullanıcıya uygulama başlangıcında verilen izinleri tutar.

    principal güvenilir host'un tanımladığı kullanıcıdır. capabilities açıkça
    verilmezse boş kalır ve bütün işlemler reddedilir. Örneğin notes.read yalnız
    not listelemeye izin verir; notes.write kendiliğinden okuma yetkisi vermez.
    İzinler başlangıçta kopyalanır, dışarıdaki set sonradan yetkiyi değiştiremez.

    Bu aşamada onay bekletme veya uzaktan kanal yetkilendirmesi yoktur. Riskli
    araçlar ve desktop dışındaki kaynaklar, uygulama eklenene kadar reddedilir.
    """

    principal: str
    capabilities: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Hatalı host yapılandırmasını sessiz izin yerine başlangıç hatası yap."""
        if not isinstance(self.principal, str) or not self.principal.strip():
            raise ContractError("Policy principal must be a non-empty string")
        # Metin iterable olsa da yetki listesi değildir. Yalnız açık set/tuple/list
        # kabul edilir; her eleman kontrol edilmeden frozenset üretmeyiz.
        if not isinstance(self.capabilities, (set, frozenset, tuple, list)) or any(
            not isinstance(item, str) or item not in _KNOWN_CAPABILITIES
            for item in self.capabilities
        ):
            raise ContractError("Policy capabilities must contain known capability names")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))

    def authorize(self, request: ToolRequest, tool: ToolSpec) -> bool:
        """TaskManager callback'i: yalnız bütün koşullar sağlanırsa True döndür.

        İstek/araç eşleşmesi, masaüstü kaynağı, kullanıcı ve core'un beklediği
        yetki bildirimi birlikte kontrol edilir. Parametre doğrulaması registry'de
        kalır; bu fonksiyon handler çalıştırmaz, onay üretmez ve veri kaydetmez.
        """
        if not isinstance(request, ToolRequest) or not isinstance(tool, ToolSpec):
            return False
        if (request.source != "desktop" or request.principal != self.principal
                or request.tool != tool.name):
            return False
        required = _TOOL_CAPABILITIES.get(tool.name)
        return (required is not None
                and frozenset(tool.required_capabilities) == required
                and required <= self.capabilities)
