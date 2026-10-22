"""PyWebView'in tek public event(name, data) metodu ve izinli UI bildirimleri.

PyWebView API çağrılarını arka plan thread'lerinde çalıştırır; kısa core beklemesi
GUI ana döngüsünü bloke etmez. Kilit eşzamanlı save/ready olaylarını sıraya koyar.
Metin modeli uzun bekleme sırasında köprü kilidini tutmaz. Notlar ortak core'a gider.
"""

import json
from base64 import b64decode, b64encode
from binascii import Error as Base64Error
from importlib import import_module
from threading import Lock, RLock
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from webview import Window

from app.core.contracts import ContractError, TaskStatus, ToolRequest, copy_json
from app.storage.json_store import StoreError
from app.storage.credentials import CredentialError, GeminiCredentials
from app.tasks.manager import TaskManagerError
from app.bridge.settings import INTERFACE_DEFAULTS, validate_settings
from app.session.gemini import DEFAULT_MODEL
from app.session.text_chat import TextChat
from app.session.live_input import LiveInput
from app.session.catalog import load_live_catalog


class NativeBridge:
    """Yalnız güvenilir yerel UI'a açılır; kimlik payload'dan alınmaz.

    window/core/store alanları ve yardımcılar özel tutulur; PyWebView'e ayrı
    araç yürütme/ham JS eval/dosya yolu API'si açılmaz. Native profil ve ayar
    deposunun konumunu güvenilir host seçer.
    """

    def __init__(self, core, store) -> None:
        self._core, self._store = core, store
        self._credentials = GeminiCredentials(store.path.parent)
        self._window: Window | None = None
        self._ready = False
        self._notes_ready = False
        self._restart_requested = False
        self._lock = RLock()
        self._chat = TextChat(core, audio_sink=self._audio_chunk, transcript_sink=self._transcript)
        self._model = DEFAULT_MODEL
        self._live_models: dict[str, dict] = {}
        self._live_model = ""
        self._catalog_lock = Lock()

    def _push(self, method: str, *args):
        """İzinli metodu JSON argümanlarıyla çağır; ham metni JS koduna ekleme."""
        if method not in {"initApp", "online", "telemetry", "setCatalog", "log", "startupStatus", "audioChunk", "liveTranscript"}:
            raise ValueError("Unsupported UI method")
        if self._window is None:
            raise RuntimeError("Native window is not attached")
        serialized = json.dumps(args, ensure_ascii=True, allow_nan=False)
        return self._window.evaluate_js(f"window.vex[{json.dumps(method)}](...{serialized})")

    def _audio_chunk(self, request_id: str, data: bytes, mime: str) -> bool:
        """Host isteğinin PCM parçasını JSON ile ilet; dosya/log/geçmişe kaydetme."""
        return self._push("audioChunk", {"request_id": request_id, "mime_type": mime,
                                        "data": b64encode(data).decode("ascii")}) is True

    def _transcript(self, request_id: str, role: str, value: str, sequence: int) -> bool:
        """Host kimliğine bağlı metin snapshot'ı; konuşma içeriğini loglama."""
        return self._push('liveTranscript', {'request_id':request_id, 'role':role,
            'text':value, 'sequence':sequence}) is True

    def _load_settings(self):
        """Eksik dosyayı boş snapshot yap; bozuk dosyayı otomatik sıfırlama."""
        data = self._store.read()
        return {} if data is None else validate_settings(data)

    def _set_on_top(self, value: bool) -> None:
        """Windows pencere özelliğini GUI thread'inde değiştir.

        PyWebView 6.2.1'in WinForms on_top setter'ı doğrudan kontrolü değiştirir;
        API thread'inden çağırmak pencereyi kilitleyebilir. Native host'ta Invoke
        ile GUI sahibine teslim ederiz. Test doubles gerçek WinForms içermez.
        """
        window = self._window
        if window is None:
            raise RuntimeError("Native window is not attached")
        native = getattr(window, "native", None)
        if native is None:
            window.on_top = value
            return
        # System bir Python dosyası değil; pythonnet GUI açılırken bu .NET
        # ad alanını yükler. Çalışma anındaki import GUI thread geçişini korur.
        action = import_module("System").Action
        native.Invoke(action(lambda: setattr(window, "on_top", value)))

    def _system_status(self):
        """Salt okunur aracı da policy/TaskManager hattından geçir."""
        task = self._core.submit(ToolRequest(request_id=uuid4().hex, source="desktop",
                                            principal="local-user", tool="system.status"))
        finished = self._core.wait(task.task_id, timeout=5)
        if finished.status != TaskStatus.SUCCEEDED:
            raise RuntimeError("System status could not be confirmed")
        data = finished.result.data
        self._push("telemetry", {"cpu": data["cpu_percent"], "ram": data["memory_percent"],
                   "gpu": None, "cpuT": None, "gpuT": None, "ramTxt": None,
                   "bat": None, "disk": None,
                   "win": " · ".join(str(data[k]) for k in ["os", "os_release", "architecture"] if data[k])})
        return data

    def _initialize(self) -> dict:
        """İlk açılış ve açık Retry aynı yolu kullanır; hata dosyayı değiştirmez."""
        self._ready = False
        self._notes_ready = False
        try:
            self._push("online", False, "MODEL OFFLINE")
            self._push("setCatalog", {"models": [], "voices": []})
            settings = self._load_settings()
            if self._push("initApp", settings) is not True:
                raise RuntimeError("UI rejected the settings snapshot")
            self._set_on_top(settings.get("onTop", False))
            self._live_model = settings.get("conn", {}).get("model", "")
            self._system_status()
            self._ready = True
            self._push("startupStatus", {"ok": True})
            self._push("log", "Native bridge ready. Local settings and system status are available.")
            return {"ok": True, "completed": True}
        except Exception as error:
            return self._startup_error(error)

    def _startup_error(self, error: Exception) -> dict:
        """Kullanıcıya güvenli, eyleme dönük hata göster; ham dosya içeriği yok."""
        self._ready = False
        code = error.code if isinstance(error, StoreError) else "settings_invalid" if isinstance(error, ContractError) else "startup_failed"
        messages = {
            "corrupt_data": "The saved settings file is damaged. The original has not been changed.",
            "settings_invalid": "Some saved settings are invalid. The original has not been changed.",
            "unsupported_version": "These settings require a different app version. Use a compatible version; this file will not be reset.",
            "read_failed": "Settings could not be read. Check file access and permissions, then retry.",
            "write_failed": "Repaired settings could not be saved. Any preserved backup was kept. Check free space and permissions, then retry.",
            "recovery_failed": "The original settings file could not be preserved. It was not reset. Check file access and retry.",
        }
        message = messages.get(code, "Native startup could not be completed. Retry, or close and reopen the app.")
        status = {"ok": False, "code": code, "message": message,
                  "recoverable": code in {"corrupt_data", "settings_invalid"}}
        try:
            self._push("startupStatus", status)
        except Exception:
            # UI'a hiç erişilemiyorsa event yanıtı/log hatayı taşır; bildirim
            # hatası asıl açılış nedenini ikinci bir traceback ile gizlemesin.
            pass
        return {**status, "error": message}

    def _recover_settings(self, data) -> dict:
        """Yalnız açık UI onayıyla, yalnız ayar dosyasını koruyarak onar.

        JSON okunabiliyorsa tek tek geçerli alanları saklarız. Bozuk JSON'un
        içerik tahmini yapılmaz. Yeni sürüm/izin hatası kurtarma yetkisi vermez.
        Yerel UI koleksiyonlarına ve core notes.json'a hiç dokunulmaz.
        """
        if type(data) is not dict or data != {"confirmed": True} or data["confirmed"] is not True:
            return {"ok": False, "error": "Settings repair requires explicit confirmation"}
        candidate = copy_json(INTERFACE_DEFAULTS)
        try:
            original = self._store.read()
            if original is None:
                return self._initialize()
            try:
                validate_settings(original)
            except ContractError:
                for key, value in original.items():
                    try:
                        candidate.update(validate_settings({key: value}))
                    except ContractError:
                        continue
            else:
                return self._initialize()
        except StoreError as error:
            if error.code != "corrupt_data":
                return self._startup_error(error)
        try:
            backup = self._store.recover_corrupt(validate=validate_settings)
            if backup is None:
                return self._initialize()
            self._store.write(candidate)
            if self._store.read() != candidate:
                raise StoreError("write_failed", "Repaired settings could not be verified")
            result = self._initialize()
            if result["ok"]:
                self._push("log", "Settings repaired. Original preserved as " + backup.name)
            return {**result, "backup": backup.name}
        except (StoreError, ContractError) as error:
            # Dosya zaten yedeklendiyse de geri silmeyiz. Kullanıcı Retry ile
            # yeniden açabilir; hata metni asıl yedeğin saklandığını belirtir.
            result = self._startup_error(error)
            result["error"] = "Repair could not be completed. Any preserved original backup was kept; check file access and retry."
            return result

    def _notes_event(self, name: str, data) -> dict:
        """Sürümlü UI komutunu çevir; dosya/model/UI iş mantığı çalıştırma.

        Kimlik/principal UI payload'ından alınmaz. Tek request_id manager'a
        aynen aktarılır; bekleme timeout'u iptal veya yeniden gönderme izni
        değildir. Native not yazımı ancak onaylı ilk aktarım tamamlanınca açılır.
        """
        if not self._ready:
            return {"ok": False, "error": "Native initialization is incomplete"}
        if (type(data) is not dict or set(data) != {"version", "request_id", "arguments"}
                or type(data["version"]) is not int or data["version"] != 1):
            return {"ok": False, "error": "Expected a version 1 note command"}
        if name != "notes_init" and not self._notes_ready:
            return {"ok": False, "error": "Confirm the initial notes transfer first"}
        if self._chat.busy:
            return {"ok": False, "error": "Wait for the text request before changing or refreshing notes"}
        tools = {"notes_init": "notes.initialize", "note_add": "notes.add",
                 "note_done": "notes.update", "note_del": "notes.delete", "notes_replace": "notes.replace"}
        submitted = False
        try:
            request = ToolRequest(request_id=data["request_id"], source="desktop",
                                  principal="local-user", tool=tools[name], arguments=data["arguments"])
            task = self._core.submit(request)
            submitted = True
            finished = self._core.wait(task.task_id, timeout=8)
            result = finished.result
            if finished.status == TaskStatus.SUCCEEDED and result and result.verified:
                if name == "notes_init":
                    self._notes_ready = result.data["migrated"]
                return {"ok": True, "completed": True, "verified": True,
                        "task_id": task.task_id, "data": result.data}
            return {"ok": False, "unknown": finished.status == TaskStatus.UNKNOWN,
                    "error": result.error.message if result and result.error else "Note operation did not complete"}
        except Exception:
            # Kabulden sonraki bekleme/taşıma hatası yan etkiyi yok sayamaz.
            # Kabul öncesi ret ise dosyaya hiç ulaşmamıştır; tekrar kullanıcıya aittir.
            return {"ok": False, "unknown": submitted,
                    "error": "Note operation could not be confirmed" if submitted else "Note command was rejected"}

    def event(self, name: str, data=None) -> dict:
        """UI isteğine kesin sonuç ver; gizli payload/hata ayrıntısını döndürme.

        ui_ready bir kere snapshot yükler; tekrar bildirim notları/snapshot'ı
        tekrar uygulamaz. save yalnız ayarları kaydeder ve geri okur. Desteksiz
        olay tamamlanmış gibi gösterilmez. Hata, UI emit tarafından görünür olur.
        """
        if name == "query_catalog":
            # Anahtar yazımıyla katalog başlangıcı aynı kısa kilidi paylaşır;
            # eski hesaptan gelen liste yeni anahtarın listesi diye uygulanmaz.
            with self._lock:
                if data is not None or not self._ready:
                    return {"ok": False, "error": "Live catalog requires a ready desktop app and no payload"}
                if not self._catalog_lock.acquire(blocking=False):
                    return {"ok": False, "error": "Live catalog is already loading"}
            try:
                result = load_live_catalog()
                with self._lock:
                    self._live_models = {item["id"]: item for item in result.get("models", [])} if result["ok"] else {}
                    if self._live_model not in self._live_models:
                        self._live_model = next(iter(self._live_models), "")
                    return {**result, "currentModel": self._live_model}
            finally:
                self._catalog_lock.release()
        if name == "stop_task":
            if (not isinstance(data, dict) or set(data) != {"request_id"}
                    or not isinstance(data["request_id"], str) or not 1 <= len(data["request_id"]) <= 128):
                return {"ok": False, "error": "Stop requires the active request_id"}
            return self._chat.stop(data["request_id"])
        if name == 'live_audio_feed':
            # Bu kısa taşıma uzun model kilidini beklemez. Ham PCM yalnız
            # eşleşen aktif turda kabul edilir; geçmiş/farklı isteğe taşınmaz.
            if (type(data) is not dict or not isinstance(data.get('request_id'), str)
                    or not 1 <= len(data['request_id']) <= 128):
                return {'ok': False, 'error': 'Invalid microphone stream target'}
            if set(data) == {'request_id'}:
                return self._chat.audio_input(data['request_id'])
            if (set(data) != {'request_id', 'sequence', 'data'} or type(data['sequence']) is not int
                    or data['sequence'] < 0 or data['data'] is not None and
                    (not isinstance(data['data'], str) or len(data['data']) != 4268)):
                self._chat.stop(data['request_id'])
                return {'ok': False, 'error': 'Invalid microphone stream packet'}
            try:
                chunk = b64decode(data['data'], validate=True) if data['data'] is not None else None
            except (Base64Error, ValueError):
                self._chat.stop(data['request_id'])
                return {'ok': False, 'error': 'Invalid microphone stream encoding'}
            return self._chat.audio_input(data['request_id'], data['sequence'], chunk)
        if name in {"text", "live_text", "live_audio", "live_audio_start"}:
            # Ağ beklerken ayarlar, pencere ve diğer kısa API istekleri aynı
            # RLock arkasında beklememeli. TextChat kendi tek-tur kilidini tutar.
            with self._lock:
                if not self._ready:
                    return {"ok": False, "error": "Native startup is incomplete. Retry startup or reopen the app."}
                model = self._model
                notes_ready = self._notes_ready
                live_model = self._live_model
                if name != 'text' and live_model not in self._live_models:
                    return {"ok": False, "error": "Load Live models in Settings, then select a conversational Live model."}
            request_id = None
            if name == 'live_audio_start':
                if (type(data) is not dict or set(data) != {'request_id'}
                        or not isinstance(data['request_id'], str) or not 1 <= len(data['request_id']) <= 128):
                    return {'ok': False, 'error': 'Invalid microphone stream request'}
                return self._chat.run_live('', live_model, notes_ready=notes_ready,
                                           request_id=data['request_id'], audio_input=LiveInput())
            if name == "live_audio":
                if (type(data) is not dict or set(data) != {"request_id", "mime_type", "data"}
                        or not isinstance(data["request_id"], str) or not 1 <= len(data["request_id"]) <= 128
                        or data["mime_type"] != "audio/pcm;rate=16000"
                        or not isinstance(data["data"], str) or len(data["data"]) > 640000):
                    return {"ok": False, "error": "Invalid microphone request envelope"}
                try:
                    audio = b64decode(data["data"], validate=True)
                except (Base64Error, ValueError):
                    return {"ok": False, "error": "Invalid microphone encoding"}
                return self._chat.run_live("", live_model, notes_ready=notes_ready,
                                           request_id=data["request_id"], audio_input=audio)
            if isinstance(data, dict):
                if (set(data) != {"request_id", "text"} or not isinstance(data["request_id"], str)
                        or not 1 <= len(data["request_id"]) <= 128):
                    return {"ok": False, "error": "Invalid chat request envelope"}
                request_id, data = data["request_id"], data["text"]
            if name == "live_text":
                return self._chat.run_live(data, live_model, notes_ready=notes_ready, request_id=request_id)
            return self._chat.run(data, model, notes_ready=notes_ready, request_id=request_id)
        with self._lock:
            try:
                if name in {"notes_init", "note_add", "note_done", "note_del", "notes_replace"}:
                    return self._notes_event(name, data)
                if name == "ui_ready":
                    if data != {"version": "1.0"}:
                        raise ContractError("Unsupported UI handshake")
                    if not self._ready:
                        return self._initialize()
                    return {"ok": True, "completed": True}
                if name == "retry_startup":
                    if self._chat.busy:
                        return {"ok": False, "error": "Wait for the text request before restarting initialization"}
                    if data is not None:
                        return {"ok": False, "error": "Startup retry accepts no payload"}
                    return self._initialize()
                if name == "recover_settings":
                    if self._chat.busy:
                        return {"ok": False, "error": "Wait for the text request before repairing settings"}
                    return self._recover_settings(data)
                if name == "model":
                    if not self._ready or not isinstance(data, str) or data not in self._live_models:
                        return {"ok": False, "error": "Load the API Live catalog and select a returned model"}
                    if self._chat.busy:
                        return {"ok": False, "error": "Wait for the current text request before changing model"}
                    if data != self._live_model and not self._chat.reset_live():
                        return {"ok": False, "error": "Previous Live session could not be closed"}
                    self._live_model = data
                    return {"ok": True, "completed": True, "model": data, "live_connected": False}
                if name == "query_apikey":
                    if data is not None:
                        raise ContractError("API key status accepts no payload")
                    return {"ok": True, "completed": True, "configured": self._credentials.read() is not None}
                if name == "apikey":
                    if not self._ready:
                        return {"ok": False, "error": "Native initialization is incomplete"}
                    if not isinstance(data, str):
                        raise ContractError("Expected an API key string")
                    if self._catalog_lock.locked():
                        return {"ok": False, "error": "Wait for the Live catalog before changing the key"}
                    if not self._chat.reset_live():
                        return {"ok": False, "error": "Wait for the active request before changing the key"}
                    self._credentials.write(data)
                    self._live_models = {}
                    return {"ok": True, "completed": True, "saved": True, "configured": True}
                if name == "disconnect":
                    if data is not None or not self._chat.reset_live():
                        return {"ok": False, "error": "Wait for the active request before disconnecting"}
                    self._push("online", False, "MODEL OFFLINE")
                    return {"ok": True, "completed": True, "disconnected": True}
                if name == "save":
                    if not self._ready:
                        return {"ok": False, "error": "Native initialization is incomplete"}
                    if type(data) is not dict:
                        raise ContractError("Expected settings object")
                    candidate = {**self._load_settings(), **validate_settings(data, from_ui=True)}
                    self._store.write(candidate)
                    if self._store.read() != candidate:
                        return {"ok": False, "error": "Settings save could not be verified"}
                    if "onTop" in candidate:
                        self._set_on_top(candidate["onTop"])
                    return {"ok": True, "completed": True, "saved": True}
                if name == "ontop":
                    if type(data) is not bool or not self._ready:
                        return {"ok": False, "error": "Expected a boolean and a ready native window"}
                    self._set_on_top(data)
                    return {"ok": True, "completed": True, "onTop": data}
                if name == "reset":
                    if data is not None or not self._ready:
                        return {"ok": False, "error": "Interface reset requires a ready window and no payload"}
                    candidate = {**self._load_settings(), **copy_json(INTERFACE_DEFAULTS)}
                    self._store.write(candidate)
                    if self._store.read() != candidate:
                        return {"ok": False, "error": "Interface reset could not be verified"}
                    self._set_on_top(False)
                    return {"ok": True, "completed": True, "saved": True, "snapshot": candidate}
                if name == "system_status":
                    if data is not None:
                        raise ContractError("System status accepts no payload")
                    return {"ok": True, "completed": True, "data": self._system_status()}
                if name in {"fullscreen", "shutdown", "restart"}:
                    if data is not None:
                        raise ContractError("Window controls accept no payload")
                    if self._window is None:
                        raise RuntimeError("Native window is not attached")
                    if name == "fullscreen":
                        self._window.toggle_fullscreen()
                        return {"ok": True, "completed": True}
                    if not self._chat.close():
                        return {"ok": False, "error": "Wait for the text request before closing the app"}
                    # Çalışan kaynakları sahipsiz bırakmadan kapat. Pencere
                    # yok edilince main() finally/with çıkışı da kapanışı tamamlar.
                    if not self._core.close():
                        return {"ok": False, "error": "A task is still stopping; window was not closed"}
                    # Yeni süreç main() tarafından GUI ve with bloğu kapandıktan
                    # sonra açılır; browser'dan executable/argüman kabul edilmez.
                    self._restart_requested = name == "restart"
                    try:
                        self._window.destroy()
                    except Exception:
                        # Kapanamayan pencere daha sonra X ile kapatılırsa eski,
                        # başarısız restart isteği beklenmedik süreç açmamalı.
                        self._restart_requested = False
                        raise
                    return {"ok": True, "completed": True}
                return {"ok": False, "error": "not_implemented: this native operation is not available yet"}
            except CredentialError:
                return {"ok": False, "error": "API key could not be read or verified in Windows credentials"}
            except (ContractError, StoreError):
                return {"ok": False, "error": "Settings are invalid or could not be read/saved; original data was not reset"}
            except (TimeoutError, TaskManagerError):
                return {"ok": False, "error": "Core operation could not be confirmed"}
            except Exception:
                return {"ok": False, "error": "Native operation failed; completion could not be confirmed"}
