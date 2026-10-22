"""Gemini anahtarını Windows Kimlik Bilgileri Yöneticisi'nde sakla.

TASKVEX_HOME profilleri ayrı kayıt kullanır; geçici test profili gerçek anahtarı
okuyamaz veya ezemez. CredRead/Write API'leri ctypes standart kütüphanesiyle
çağrılır; JSON/plaintext yedek deposuna geri dönüş yoktur. Aynı Windows hesabında
çalışan güvenilir süreçlere karşı bir sandbox sağlamaz.
"""

import ctypes as c
from ctypes import wintypes as w
from hashlib import sha256
import os
from pathlib import Path


class CredentialError(RuntimeError):
    """İşletim sistemi hatasını anahtar içermeyen sabit mesajla bildir."""


class _Credential(c.Structure):
    """Win32 CREDENTIALW yerleşimi; pointer'lar 32/64 bit Python'a uyar."""
    _fields_ = [("flags", w.DWORD), ("type", w.DWORD), ("target", w.LPWSTR),
                ("comment", w.LPWSTR), ("written", w.FILETIME), ("size", w.DWORD),
                ("blob", c.POINTER(c.c_ubyte)), ("persist", w.DWORD),
                ("attribute_count", w.DWORD), ("attributes", c.c_void_p),
                ("alias", w.LPWSTR), ("username", w.LPWSTR)]


def _library():
    """Windows API imzalarını açık kur; import sırasında sistem çağrısı yapma."""
    if os.name != "nt":
        raise CredentialError("Windows credential storage is unavailable")
    library = c.WinDLL("advapi32", use_last_error=True)
    signatures = [
        (library.CredReadW, [w.LPCWSTR, w.DWORD, w.DWORD, c.POINTER(c.POINTER(_Credential))], w.BOOL),
        (library.CredWriteW, [c.POINTER(_Credential), w.DWORD], w.BOOL),
        (library.CredFree, [c.c_void_p], None),
    ]
    for function, arguments, result in signatures:
        function.argtypes, function.restype = arguments, result
    return library


def _validate(key: str) -> bytes:
    """Boş, aşırı uzun veya HTTP başlığına uygun olmayan girdiyi reddet."""
    if not isinstance(key, str) or not 1 <= len(key) <= 2048 or any(
        not 33 <= ord(char) <= 126 for char in key
    ):
        raise CredentialError("Expected a non-empty API key without whitespace")
    return key.encode("ascii")


class GeminiCredentials:
    """Güvenilir host'un seçtiği tek veri profiline ait Gemini kaydı.

    Profil yolu UI/model payload'ından alınmaz. Kayıt adı yolun özetini içerir;
    yolun kendisi kimlik deposunda görünmez. Anahtarı geri verme yetkisi yalnız
    Python host'undadır; UI'a yalnız configured durumu gönderilir.
    """

    def __init__(self, home: Path) -> None:
        profile = str(home.resolve()).casefold()
        self._target = "TaskVex/Gemini/" + sha256(profile.encode("utf-8")).hexdigest()

    def read(self) -> str | None:
        """Kaydı oku ve CredFree ile belleği bırak; bulunamama dışında hatayı gizleme."""
        library = _library()
        pointer = c.POINTER(_Credential)()
        if not library.CredReadW(self._target, 1, 0, c.byref(pointer)):
            if c.get_last_error() == 1168:  # ERROR_NOT_FOUND
                return None
            raise CredentialError("API key could not be read from Windows credentials")
        try:
            if not pointer or not 1 <= pointer.contents.size <= 2048 or not pointer.contents.blob:
                raise CredentialError("Stored API key is invalid")
            try:
                key = c.string_at(pointer.contents.blob, pointer.contents.size).decode("ascii")
            except UnicodeDecodeError:
                raise CredentialError("Stored API key is invalid") from None
            _validate(key)
            return key
        finally:
            library.CredFree(pointer)

    def write(self, key: str) -> None:
        """Yalnız bu profilin kaydını yaz ve geri okuyarak doğrula; ağ isteği yapma.

        Yerel buffer temizlenir; Python string'lerinin bellekten kesin silindiği
        iddia edilmez. Yazma sonrası doğrulama başarısızsa kayıt uygulanmış olabilir.
        """
        data = _validate(key)
        buffer = c.create_string_buffer(data)
        credential = _Credential(type=1, target=self._target, size=len(data),
                                 blob=c.cast(buffer, c.POINTER(c.c_ubyte)), persist=2,
                                 username="TaskVex")  # CRED_PERSIST_LOCAL_MACHINE: aynı kullanıcı/makine
        try:
            if not _library().CredWriteW(c.byref(credential), 0):
                raise CredentialError("API key could not be stored in Windows credentials")
        finally:
            c.memset(c.addressof(buffer), 0, c.sizeof(buffer))
        if self.read() != key:
            raise CredentialError("API key storage could not be verified")


def load_gemini_key() -> str | None:
    """Açık süreç anahtarı önceliklidir; yoksa Windows'taki mevcut profili oku."""
    key = os.environ.get("GEMINI_API_KEY")
    if key is not None:
        _validate(key)
        return key
    if os.name != "nt":
        return None
    from app.config import get_data_home
    return GeminiCredentials(get_data_home()).read()
