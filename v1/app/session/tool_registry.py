"""TaskVex araçlarının tek kayıt ve parametre doğrulama noktası.

Registry bir rehber gibi çalışır: hangi araç var, nasıl parametre bekliyor ve
handler'ı hangisi? Burada handler çağrılmaz. Kuyruk ve seri yürütme TaskManager'da;
gerçek izin kuralları sonraki policy aşamasında bu yürütme hattına bağlanacak.

Araçlar bootstrap sırasında açıkça kaydedilecek; klasör tarayıp Python dosyası
import etmiyoruz. Yerleşik araç ile plugin aracı için ayrı kayıt sistemi yok.
"""

from dataclasses import replace
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from app.core.contracts import ContractError, ToolRequest, ToolSpec


class RegistryError(ContractError):
    """Kayıt/parametre hatasını makinenin okuyabileceği bir kodla belirtir.

    code örneğin duplicate_tool veya invalid_arguments olabilir. Hata metnine
    gelen parametre değerlerini koymayız; onlar gizli veya kişisel veri içerebilir.
    İleride yürütücü bu hatayı ToolError biçimine çevirebilir.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _check_inline_schema(node: Any) -> None:
    """Başlangıç sürümünün açık şema sınırını belge içinde denetle.

    Draft 2020-12 kullanıyoruz; başka draft bildirimi yanlış kurallarla
    yorumlanmasın. Bu sürüm referanslı şemaları desteklemez: $ref ve benzerleri
    belgenin hiçbir bölümünde bulunamaz. Böylece şema doğrulaması dış kaynak
    indirmez veya çözülemeyen referansı ilk kullanıcı çağrısına bırakmaz.

    Bu küçük profil kontrolü JSON Schema motoru değildir; required, enum,
    minLength, iç içe nesne/dizi gibi asıl kuralları jsonschema denetler.
    """
    if isinstance(node, list):
        for item in node:
            _check_inline_schema(item)
    elif isinstance(node, dict):
        if any(key in node for key in ("$ref", "$dynamicRef", "$recursiveRef")):
            raise RegistryError("invalid_schema", "Schema references are not supported")
        if "$schema" in node and node["$schema"] != Draft202012Validator.META_SCHEMA["$id"]:
            raise RegistryError("invalid_schema", "Only JSON Schema Draft 2020-12 is supported")
        for item in node.values():
            _check_inline_schema(item)


class ToolRegistry:
    """Araçları adlarıyla saklar; sessiz üzerine yazmaya izin vermez.

    Kayıtlar başlangıçta oluşturulur; çalışma sırasında hot reload veya paralel
    kayıt değişikliği bu sürümün sözleşmesi değildir. Dışarı verilen ToolSpec
    kopyalarının şeması değiştirilse bile içerideki kaydı değiştirmemeli.
    """

    def __init__(self) -> None:
        # Validator, önceden kontrol edilmiş şemayı tekrar kullanır; her istekte
        # aynı araç şemasının yapısını yeniden incelemek gerekmez.
        self._tools: dict[str, tuple[ToolSpec, Draft202012Validator]] = {}

    def register(self, tool: ToolSpec) -> None:
        """Geçerli ToolSpec'i kaydet; hata halinde registry'yi değiştirme.

        Aynı ad ikinci kez gelirse aynı fonksiyon bile olsa duplicate_tool verilir.
        Şema ve bildirim kontrolü tamamlanmadan sözlüğe ekleme yapılmaz.
        """
        if not isinstance(tool, ToolSpec):
            raise RegistryError("invalid_tool", "Expected ToolSpec")
        if tool.name in self._tools:
            raise RegistryError("duplicate_tool", f"Tool already registered: {tool.name}")

        # frozen dataclass içindeki sözlük derin immutable değildir. replace,
        # ToolSpec constructor'ını yeniden çalıştırır ve şemayı tekrar kopyalar.
        # Böylece kaydeden kişinin tuttuğu nesne registry'nin iç kaydı olmaz.
        owned = replace(tool)
        _check_inline_schema(owned.input_schema)
        try:
            Draft202012Validator.check_schema(owned.input_schema)
        except SchemaError:
            # Kütüphanenin ayrıntılı hatası şema/default örneklerini içerebilir.
            # Genel hata verip hata zincirinde de bu veriyi dışarı taşımıyoruz.
            raise RegistryError("invalid_schema", "Invalid JSON Schema declaration") from None
        validator = Draft202012Validator(owned.input_schema)
        self._tools[owned.name] = (owned, validator)

    def get(self, name: str) -> ToolSpec:
        """Adıyla araç bul ve bağımsız bildirim kopyası döndür.

        Bilinmeyen ad fallback veya varsayılan araç seçmez; unknown_tool hatası
        üretir. Dönen handler hâlâ çağrılabilir Python fonksiyonudur; bir sandbox
        veya yetki kontrolü değildir. Ürün yürütme yolu TaskManager'dan geçecek.
        """
        if not isinstance(name, str) or name not in self._tools:
            raise RegistryError("unknown_tool", "Tool is not registered")
        return replace(self._tools[name][0])

    def list_tools(self) -> list[ToolSpec]:
        """Araçları ada göre sabit sırada, bağımsız bildirim kopyalarıyla listele.

        Sonuç tüm kayıtları içerir; kullanıcının çağırma yetkisi olduğu anlamına
        gelmez. Model/UI için görünür katalog filtreleme daha sonra eklenecek.
        """
        return [self.get(name) for name in sorted(self._tools)]

    def validate_request(self, request: ToolRequest) -> ToolRequest:
        """Aracı bul, isteği yeniden kopyala/doğrula ve geçerli kopyayı döndür.

        Dönüş parametreleri normalize etmez: metin sayı yapılmaz, null atılmaz,
        şemadaki default alanlar otomatik eklenmez. Hatalı değer reddedilir.
        Bu kontrol hiçbir handler çalıştırmaz ve policy izni vermez.
        """
        if not isinstance(request, ToolRequest):
            raise RegistryError("invalid_request", "Expected ToolRequest")
        try:
            # İstek oluşturulduktan sonra arguments sözlüğü değiştirilmiş olabilir.
            # to_dict ve constructor geçerli JSON sınırını tekrar kontrol eder.
            owned = ToolRequest(**request.to_dict())
        except ContractError:
            raise RegistryError("invalid_request", "Request violates the core contract") from None
        if owned.tool not in self._tools:
            raise RegistryError("unknown_tool", "Tool is not registered")
        validator = self._tools[owned.tool][1]
        try:
            validator.validate(owned.arguments)
        except ValidationError as error:
            # Örneğin 'minLength' denetimin adını bildirir, kullanıcının asıl
            # metnini veya şifre gibi parametre değerlerini hata içine koymaz.
            raise RegistryError(
                "invalid_arguments", f"Arguments violate schema rule: {error.validator}"
            ) from None
        return owned
