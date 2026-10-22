"""Küçük JSON nesnelerini eski dosyayı yarım bırakmadan kaydet.

Yeni içerik hedefle aynı dizindeki geçici dosyaya yazılır, flush/fsync ile
tamamlanır ve os.replace ile hedefin yerine geçirilir. Replace öncesi hata
eski dosyayı değiştirmez. Disk/yazma hataları başarı gibi gizlenmez.

Dosya zarfı version + data içerir. Bozuk kayıt otomatik boş veri sayılmaz;
read hata verir, recover_corrupt ancak açıkça çağrılırsa aslı ayrı korunur.
Bu sınıf not şemasını, yetkiyi veya sırların güvenli saklanmasını yönetmez.
"""

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable
from uuid import uuid4

from app.core.contracts import ContractError, copy_json


class StoreError(ValueError):
    """Hata kodunu taşır; mesajlarda kayıt içeriği veya sistem yolu bulunmaz."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Aynı JSON anahtarının önceki değeri sessizce ezmesini engelle."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    """Python decoder'ın kabul ettiği NaN/Infinity standart JSON değildir."""
    raise ValueError("Non-finite JSON number")


class JsonStore:
    """Güvenilir host'un seçtiği tek dosyada version=1 JSON nesnesi saklar.

    path mutlak bir dosya yoludur; araç/model girdisinden doğrudan alınmamalı.
    read eksik dosyada None, geçerli boş kayıtta {} döndürür. Böylece 'henüz
    oluşturulmadı' ile 'kullanıcı veriyi temizledi' birbirine karışmaz.

    shortcut: tek host/yazıcı varsayılır; çok süreç veya paralel read-modify-write
    gerekirse transaction/kilit desteği olan depoya geç. Atomik replace tek
    başına iki yazarın birbirinin değişikliğini ezmesini önlemez.
    """

    def __init__(self, path: Path) -> None:
        """Konumu kontrol et; nesne oluşturmak dosya okumaz veya yaratmaz."""
        if not isinstance(path, Path) or not path.is_absolute() or not path.name:
            raise ContractError("Store path must be an absolute file path")
        self.path = path

    def read(self) -> dict[str, Any] | None:
        """Kaydı doğrulayarak oku; bozuk/asıl dosyayı değiştirmeden hata bildir.

        Desteklenmeyen sürüm farklı hata kodudur: daha yeni uygulamanın verisini
        bozuk sanıp sıfırlamak yerine yükseltme/migration kararı host'a bırakılır.
        """
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except UnicodeError:
            raise StoreError("corrupt_data", "Stored data is not valid UTF-8") from None
        except OSError:
            raise StoreError("read_failed", "Stored data could not be read") from None
        try:
            document = json.loads(text, object_pairs_hook=_unique_object,
                                  parse_constant=_reject_constant)
            if (type(document) is not dict or type(document.get("version")) is not int
                    or document["version"] < 1):
                raise ValueError("Invalid version envelope")
            if document["version"] != 1:
                raise StoreError("unsupported_version", "Stored data version is not supported")
            if set(document) != {"version", "data"} or type(document["data"]) is not dict:
                raise ValueError("Invalid data envelope")
            return copy_json(document["data"])
        except (ValueError, RecursionError) as error:
            if isinstance(error, StoreError):
                raise
            raise StoreError("corrupt_data", "Stored data is invalid; original file preserved") from None

    def write(self, data: dict[str, Any]) -> None:
        """Tam nesneyi atomik değiştir; dönüş yalnız replace başarılıysa gerçekleşir.

        Önce bellekte doğrularız. Sonra var olan kaydı kontrol ederiz: bozuk veya
        yeni sürümlü dosyanın üstüne yanlışlıkla yazmayız. Başarıdan önce geçici
        dosya kapatılır; bu Windows'ta replace için de gereklidir.
        """
        try:
            if type(data) is not dict:
                raise ContractError("Store data must be a JSON object")
            text = json.dumps({"version": 1, "data": copy_json(data)},
                              ensure_ascii=False, allow_nan=False, indent=2) + "\n"
            # UTF-8'e çevrilemeyen yalnız surrogate karakterler de diske dokunmadan
            # reddedilir; json.dumps metin üretmiş olması yeterli değildir.
            content = text.encode("utf-8")
        except (ValueError, TypeError, RecursionError):
            raise StoreError("invalid_data", "Expected a JSON object with finite values") from None
        self.read()
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # NamedTemporaryFile bağlamı dosyayı replace'ten önce kapatır. Aynı
            # dizin kullanmak farklı diskler arasında atomiklik kaybını önler.
            with tempfile.NamedTemporaryFile(mode="wb", dir=self.path.parent,
                                             prefix=f".{self.path.name}.", suffix=".tmp",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except OSError:
            raise StoreError("write_failed", "Stored data could not be saved") from None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    # Temizlik asıl yazma hatasını maskelemesin. Artık .tmp,
                    # normal açılışta hiçbir zaman asıl kayıt sayılmaz.
                    pass

    def recover_corrupt(self, *, validate: Callable[[dict], Any] | None = None) -> Path | None:
        """Yalnız bozuk dosyayı benzersiz .corrupt adına taşı; yeni kayıt yazma.

        Host önce hatayı kullanıcıya bildirmeli ve bu kurtarmayı açıkça seçmeli.
        Dönen yol asıl baytları koruyan dosyadır. Sağlıklı/eksik kayıtta None;
        okuma izni veya sürüm hatasında ret verir. Kurtarma başarısızsa asıl kalır.
        validate verilirse geçerli JSON içindeki uygulama şeması da denetlenir;
        yalnız ContractError bozuk kayıt sayılır, beklenmeyen validator hatası değil.
        """
        try:
            data = self.read()
            if data is None:
                return None
            if validate is None:
                return None
            try:
                validate(data)
            except ContractError:
                pass
            else:
                return None
        except StoreError as error:
            if error.code != "corrupt_data":
                raise
        backup = self.path.with_name(f"{self.path.name}.{uuid4().hex}.corrupt")
        try:
            os.replace(self.path, backup)
        except OSError:
            raise StoreError("recovery_failed", "Corrupt data could not be preserved") from None
        return backup
