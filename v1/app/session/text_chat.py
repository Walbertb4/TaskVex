"""Native text request owner: runs one Gemini turn at a time.

REST call in API thread; The persistent Live network operates on a single I/O event loop.
The model is not the tool executor: it only uses the ModelTools catalog the host chooses.
uses. REST messages are independent; Live can preserve context in an open session.
"""

from threading import Lock
from collections.abc import Callable
from uuid import uuid4
from hashlib import sha256

from app.core.contracts import ContractError
from app.session.gemini import DEFAULT_MODEL, FALLBACK_MODEL, GeminiText, GeminiUsage
from app.session.model_tools import ModelTools, assistant_control_request
from app.storage.credentials import CredentialError
from app.session.live_session import PersistentLive
from app.session.live_input import LiveInput
from app.session.speech import GeminiSpeech
from app.session.conversation_memory import ConversationMemory
from app.session.model_instruction import personal_memory


# REST and Live share the same authorization catalog; Reporting turns are again tool-free.
BASE_MODEL_TOOLS = ("apps.catalog", "system.status", "media.status", "media.control", "weather.current", "weather.locations", "assistant.request_sleep_mode",
                    "assistant.request_shutdown", "clocks.create", "clocks.control", "clocks.list")
MEMORY_MODEL_TOOLS = ("memory.read", "memory.patch")
NOTE_MODEL_TOOLS = ("notes.add", "notes.list", "notes.select", "notes.update",
                   "notes.delete", "notes.delete_many", "notes.complete_many")


class TextChat:
    """Borrow Core; Close the client at the end of each round, do not put secrets into the results."""

    def __init__(self, core, *, audio_sink: Callable[[str, bytes, str], bool] | None = None,
                 transcript_sink: Callable[[str, str, str, int], bool] | None = None) -> None:
        self._core = core
        self._usage = GeminiUsage()
        self._lock = Lock()
        self._closed = False
        self._live = PersistentLive()
        self._rest_guard = Lock()
        self._rest: tuple[str, GeminiText | GeminiSpeech] | None = None
        self._speech_reply: tuple[str, str] | None = None
        self._audio_sink = audio_sink
        self._transcript_sink = transcript_sink
        self._memory = ConversationMemory()
        self._personal_memory_scope: bytes | None = None

    def _prepare_personal_memory(self, profile: dict | None) -> bool:
        """In the new round, does not bring back the information from the old Live/RAM.

        It is under model lock. The obvious response is not interrupted; change next round
        Drops the old socket and temporary chat context. It does not touch disk notes.
        """
        scope = sha256(personal_memory(profile).encode('utf-8')).digest()
        if self._personal_memory_scope is not None and scope != self._personal_memory_scope:
            if not self._live.close():
                return False
            self._memory.clear()
        self._personal_memory_scope = scope
        return True

    @property
    def busy(self) -> bool:
        """UI/host monitors the situation before starting another round or close."""
        return self._lock.locked()

    def close(self) -> bool:
        """Killing the active round; If empty, close new requests permanently.

        False means the close is not yet safe. network request or
        We do not act as if we have canceled the tool transaction that has already occurred.
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
        """Drop Transport; just clear RAM on new conversation/key replacement.

        Rejection while busy does not delete any recordings. Stop/Disconnect/model replacement is the same
        continues the conversation; The history is transferred to the new socket only as information.
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
        """Busy unlock waiting; signal the matching REST or Live round."""
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
                 audio_input: bytes | LiveInput | None = None, profile: dict | None = None, notification: bool = False,
                 voice: str | None = None) -> dict:
        """A message to the same Live session; busy/shutdown lock common with REST."""
        if audio_input is not None:
            # Don't trust UI: 15 seconds, mono/16 kHz/16-bit; PCM is not written on the report.
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
            if not self._prepare_personal_memory(profile):
                return {'ok': False, 'unknown': True, 'code': 'memory_reset_failed',
                        'error': 'Previous memory context could not be closed. Reopen before continuing.'}
            allowed = BASE_MODEL_TOOLS
            if profile and profile.get("pMemory") is True:
                allowed += MEMORY_MODEL_TOOLS
                if profile.get("pLearn") is True:
                    allowed += ("memory.propose", "memory.decide")
            if notification:
                allowed = ()  # Host notification speaks; cannot run tools on behalf of the user.
            elif notes_ready:
                allowed += NOTE_MODEL_TOOLS
            tools = ModelTools(self._core, principal="local-user", session_id=uuid4().hex, allowed_tools=allowed)
            # The sound depends only on this host request; provider/UI new target
            # cannot choose the identity. The old CLI attempt without a header remains silent.
            output = self._audio_sink
            sink = (lambda data, mime: output(request_id, data, mime)) if output and request_id else None
            text_output = self._transcript_sink
            text_sink = (lambda role, value, sequence: text_output(request_id, role, value, sequence)) if text_output and request_id else None
            report = self._live.ask(text, model, tools, request_id=request_id, audio_sink=sink, profile=profile,
                                    voice=voice,
                                    context=self._memory.snapshot(),
                                    **({'transcript_sink': text_sink} if text_sink else {}),
                                    **({"audio_input": audio_input} if audio_input is not None else {}))
            self._memory.remember(report.get('input_text', '') if audio_input is not None else text, report)
            self._usage.add(report.get('usage_tokens'), partial=report.get('usage_partial', False))
            return self._usage.report({**report, "request_id": request_id})
        except Exception:
            return {"ok": False, "unknown": True, "code": "live_session_error",
                    "error": "Live session could not be confirmed. Reopen and check notes before retrying."}
        finally:
            self._lock.release()

    def audio_input(self, request_id: str, sequence=None, data=None) -> dict:
        """Make limited submissions to your Live queue without waiting for a long chat unlock."""
        return self._live.input(request_id, sequence, data)

    def read_reply(self, request_id: str) -> dict:
        """Just read the last successful REST response once; UI cannot select text.

        The same lock and Stop ID are used. Audio error, already completed
        It does not invalidate the result text/tool. If Bot/CLI does not call this method, it is silent.
        """
        if not self._lock.acquire(blocking=False):
            return {'ok': False, 'completed': True, 'audio_error': 'speech_busy'}
        try:
            with self._rest_guard:
                pending = self._speech_reply
                if self._closed or not pending or pending[0] != request_id or not self._audio_sink:
                    return {'ok': False, 'completed': True, 'request_id': request_id, 'audio_error': 'speech_not_pending'}
                self._speech_reply = None
                speech = GeminiSpeech(usage=self._usage)
                self._rest = (request_id, speech)
            output = self._audio_sink
            result = speech.run(pending[1], lambda data, mime: output(request_id, data, mime))
            return self._usage.report({**result, 'request_id': request_id})
        finally:
            with self._rest_guard:
                self._rest = None
            self._lock.release()

    def run(self, text: object, model: str, *, notes_ready: bool = True, request_id: str | None = None,
            profile: dict | None = None) -> dict:
        """Receive a single message from the ready host; return end result or open rejection.

        The CRUD tools for Catalog/system and notes whose transfer has been approved are opened.
        The Language/personal instruction comes from the host's register snapshot; It does not give tool permission.
        Application opening and import cannot be opened in this language.
        Unexpected error may occur after the tool; In such a result unknown
        The mark prevents automatic resubmission permission.
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
            if not self._prepare_personal_memory(profile):
                return {'ok': False, 'unknown': True, 'code': 'memory_reset_failed',
                        'error': 'Previous memory context could not be closed. Reopen before continuing.'}
            # Normal chat will not be closed just because the note is waiting for transfer. same situation
            # It also narrows the scope of tools in the backend; We don't rely on UI lock alone.
            allowed = BASE_MODEL_TOOLS
            if profile and profile.get("pMemory") is True:
                allowed += MEMORY_MODEL_TOOLS
                if profile.get("pLearn") is True:
                    allowed += ("memory.propose", "memory.decide")
            if notes_ready:
                allowed += NOTE_MODEL_TOOLS
            tools = ModelTools(self._core, principal="local-user", session_id=uuid4().hex,
                               allowed_tools=allowed)
            try:
                client = GeminiText(tools, model=model, profile=profile, usage=self._usage)
            except CredentialError:
                return {"ok": False, "error": "Gemini key is missing or unavailable. Save it in Settings."}
            except ContractError:
                return {"ok": False, "code": "model_config_invalid",
                        "error": "Gemini key or model profile is missing or invalid. Save it in Settings."}
            with client:
                # The pattern lock is held throughout HTTP; Just this short to stop
                # reference lock is used. Each round gets separate client/signal.
                with self._rest_guard:
                    self._rest = (request_id or uuid4().hex, client)
                result = client.run(text)
                result.update(assistant_control_request(result))
                if result.get('ok') and request_id and self._audio_sink:
                    with self._rest_guard:
                        self._speech_reply = (request_id, result['text'])
            return self._usage.report({**result, "completed": True, "request_id": request_id})
        except Exception:
            return {"ok": False, "unknown": True,
                    "error": "Text result could not be confirmed. Do not resend; reopen and check notes."}
        finally:
            with self._rest_guard:
                self._rest = None
            self._lock.release()
