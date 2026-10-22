"""Native metin isteğinin sahibi: aynı anda tek Gemini turu çalıştırır.

REST çağrısı API thread'inde; kalıcı Live ağı tek I/O event loop'unda çalışır.
Model, araç yürütücüsü değildir: yalnız host'un seçtiği ModelTools kataloğunu
kullanır. REST mesajları bağımsızdır; Live açık oturumda bağlamı koruyabilir.
"""

from threading import Lock
from collections.abc import Callable
from uuid import uuid4

from app.core.contracts import ContractError
from app.session.gemini import DEFAULT_MODEL, FALLBACK_MODEL, GeminiText
from app.session.model_tools import ModelTools
from app.storage.credentials import CredentialError
from app.session.live_session import PersistentLive
from app.session.live_input import LiveInput
from app.session.speech import GeminiSpeech
from app.session.conversation_memory import ConversationMemory
from app.session.sleep_intent import wants_sleep


class TextChat:
    """Core'u ödünç al; istemciyi her tur sonunda kapat, sırları sonuçlara koyma."""

    def __init__(self, core, *, audio_sink: Callable[[str, bytes, str], bool] | None = None,
                 transcript_sink: Callable[[str, str, str, int], bool] | None = None) -> None:
        self._core = core
        self._lock = Lock()
        self._closed = False
        self._live = PersistentLive()
        self._rest_guard = Lock()
        self._rest: tuple[str, GeminiText | GeminiSpeech] | None = None
        self._speech_reply: tuple[str, str] | None = None
        self._audio_sink = audio_sink
        self._transcript_sink = transcript_sink
        self._memory = ConversationMemory()

    @property
    def busy(self) -> bool:
        """UI/host başka bir tur veya kapanış başlatmadan önce durumu gözler."""
        return self._lock.locked()

    def close(self) -> bool:
        """Aktif turu öldürme; boşsa yeni istekleri kalıcı kapat.

        False kapanışın henüz güvenli olmadığı anlamına gelir. Ağ isteğini veya
        gerçekleşmiş araç işlemini iptal etmiş gibi davranmayız.
        """
        if not self._lock.acquire(blocking=False):
            return False
        try:
            self._speech_reply = None
            if not self._live.close():
                return False
            self._closed = True
            self._memory.clear()
            return True
        finally:
            self._lock.release()

    def reset_live(self, *, clear_memory: bool = False) -> bool:
        """Transport'u bırak; yalnız yeni sohbet/anahtar değişiminde RAM'i temizle.

        Meşgulken ret hiçbir kaydı silmez. Stop/Disconnect/model değişimi aynı
        sohbeti sürdürür; geçmiş yeni socket'e yalnız bilgi olarak aktarılır.
        """
        if not self._lock.acquire(blocking=False):
            return False
        try:
            self._speech_reply = None
            closed = self._live.close()
            if closed and clear_memory:
                self._memory.clear()
            return closed
        finally:
            self._lock.release()

    def stop(self, request_id: str) -> dict:
        """Meşgul kilidini bekleme; eşleşen REST veya Live turuna sinyal ver."""
        with self._rest_guard:
            if self._rest and self._rest[0] == request_id:
                waiting = self._rest[1].stop()
                if waiting is not None:
                    return {'ok': True, 'completed': False, 'request_id': request_id,
                            'accepted': True, 'waiting_for': waiting}
            if self._speech_reply and self._speech_reply[0] == request_id:
                self._speech_reply = None
                return {'ok': True, 'completed': False, 'accepted': True, 'request_id': request_id,
                        'waiting_for': 'speech_completion'}
        accepted = self._live.stop(request_id)
        return {"ok": accepted, "completed": False, "request_id": request_id,
                **({"accepted": True} if accepted else {"error": "No matching active request"})}

    def run_live(self, text: object, model: str, *, notes_ready: bool = False, request_id: str | None = None,
                 audio_input: bytes | LiveInput | None = None, profile: dict | None = None) -> dict:
        """Aynı Live oturumuna bir mesaj; REST ile ortak meşgul/kapanış kilidi."""
        if audio_input is not None:
            # UI'ya güvenme: 15 saniye, mono/16 kHz/16-bit; PCM rapora yazılmaz.
            if (not isinstance(audio_input, LiveInput) and
                    (type(audio_input) is not bytes or not 3200 <= len(audio_input) <= 480000 or len(audio_input) % 2)) or text != "":
                return {"ok": False, "error": "Expected 0.1–15 seconds of mono 16 kHz PCM"}
            text = ""
        elif not isinstance(text, str) or not text.strip() or len(text) > 20000:
            return {"ok": False, "error": "Enter a message between 1 and 20000 characters"}
        if not self._lock.acquire(blocking=False):
            return {"ok": False, "error": "A model request is already running"}
        try:
            with self._rest_guard:
                self._speech_reply = None
            if self._closed:
                return {"ok": False, "error": "Text session is closed; reopen the app"}
            if audio_input is None and wants_sleep(text):
                if not self._live.close():
                    return {'ok':False, 'unknown':True, 'error':'Live closure could not be confirmed'}
                return {'ok':True, 'completed':True, 'text':'Sleep mode requested.', 'sleep_requested':True,
                        'model':'local', 'model_attempts':[], 'tool_results':[], 'mode':'local_sleep', 'request_id':request_id}
            allowed = ("apps.catalog", "system.status")
            if notes_ready:
                allowed += ("notes.add", "notes.list", "notes.update", "notes.delete")
            tools = ModelTools(self._core, principal="local-user", session_id=uuid4().hex, allowed_tools=allowed)
            # Ses yalnız bu host isteğine bağlıdır; sağlayıcı/UI yeni hedef
            # kimliği seçemez. Başlıksız eski CLI denemesi sessiz kalır.
            output = self._audio_sink
            sink = (lambda data, mime: output(request_id, data, mime)) if output and request_id else None
            text_output = self._transcript_sink
            text_sink = (lambda role, value, sequence: text_output(request_id, role, value, sequence)) if text_output and request_id else None
            report = self._live.ask(text, model, tools, request_id=request_id, audio_sink=sink, profile=profile,
                                    context=self._memory.snapshot(),
                                    **({'transcript_sink': text_sink} if text_sink else {}),
                                    **({"audio_input": audio_input} if audio_input is not None else {}))
            self._memory.remember(report.get('input_text', '') if audio_input is not None else text, report)
            return {**report, "request_id": request_id}
        except Exception:
            return {"ok": False, "unknown": True, "code": "live_session_error",
                    "error": "Live session could not be confirmed. Reopen and check notes before retrying."}
        finally:
            self._lock.release()

    def audio_input(self, request_id: str, sequence=None, data=None) -> dict:
        """Uzun sohbet kilidini beklemeden kendi Live kuyruğuna sınırlı teslim yap."""
        return self._live.input(request_id, sequence, data)

    def read_reply(self, request_id: str) -> dict:
        """Yalnız son başarılı REST cevabını bir kez oku; UI metin seçemez.

        Aynı kilit ve Stop kimliği kullanılır. Ses hatası, daha önce tamamlanmış
        metin/araç sonucunu geçersiz yapmaz. Bot/CLI bu metodu çağırmazsa sessizdir.
        """
        if not self._lock.acquire(blocking=False):
            return {'ok': False, 'completed': True, 'audio_error': 'speech_busy'}
        try:
            with self._rest_guard:
                pending = self._speech_reply
                if self._closed or not pending or pending[0] != request_id or not self._audio_sink:
                    return {'ok': False, 'completed': True, 'request_id': request_id, 'audio_error': 'speech_not_pending'}
                self._speech_reply = None
                speech = GeminiSpeech()
                self._rest = (request_id, speech)
            output = self._audio_sink
            result = speech.run(pending[1], lambda data, mime: output(request_id, data, mime))
            return {**result, 'request_id': request_id}
        finally:
            with self._rest_guard:
                self._rest = None
            self._lock.release()

    def run(self, text: object, model: str, *, notes_ready: bool = True, request_id: str | None = None,
            profile: dict | None = None) -> dict:
        """Hazır host'tan tek mesaj al; bitiş sonucu veya açık ret döndür.

        Katalog/sistem ve aktarımı onaylanan notların CRUD araçları açılır.
        Dil/kişisel talimat host'un kayıt snapshot'ından gelir; araç izni vermez.
        Uygulama açma ve import bu dilimde açılmaz.
        Beklenmeyen hata araç sonrası oluşabilir; böyle bir sonuçta unknown
        işareti otomatik yeniden gönderme izni verilmesini engeller.
        """
        if not isinstance(text, str) or not text.strip() or len(text) > 20_000:
            return {"ok": False, "error": "Enter a message between 1 and 20000 characters"}
        if model not in {DEFAULT_MODEL, FALLBACK_MODEL}:
            return {"ok": False, "error": "Select a supported text model"}
        if not self._lock.acquire(blocking=False):
            return {"ok": False, "error": "A text request is already running"}
        try:
            with self._rest_guard:
                self._speech_reply = None
            if self._closed:
                return {"ok": False, "error": "Text session is closed; reopen the app"}
            # Not aktarımı bekliyor diye normal sohbet kapatılmaz. Aynı durum
            # backend'de araç kapsamını da daraltır; yalnız UI kilidine güvenmeyiz.
            allowed = ("apps.catalog", "system.status")
            if notes_ready:
                allowed += ("notes.add", "notes.list", "notes.update", "notes.delete")
            tools = ModelTools(self._core, principal="local-user", session_id=uuid4().hex,
                               allowed_tools=allowed)
            try:
                client = GeminiText(tools, model=model, profile=profile)
            except CredentialError:
                return {"ok": False, "error": "Gemini key is missing or unavailable. Save it in Settings."}
            except ContractError:
                return {"ok": False, "code": "model_config_invalid",
                        "error": "Gemini key or model profile is missing or invalid. Save it in Settings."}
            with client:
                # Model kilidi HTTP boyunca tutulur; Stop için yalnız bu kısa
                # referans kilidi kullanılır. Her tur ayrı istemci/sinyal alır.
                with self._rest_guard:
                    self._rest = (request_id or uuid4().hex, client)
                result = client.run(text)
                if result.get('ok') and request_id and self._audio_sink:
                    with self._rest_guard:
                        self._speech_reply = (request_id, result['text'])
            return {**result, "completed": True, "request_id": request_id}
        except Exception:
            return {"ok": False, "unknown": True,
                    "error": "Text result could not be confirmed. Do not resend; reopen and check notes."}
        finally:
            with self._rest_guard:
                self._rest = None
            self._lock.release()
