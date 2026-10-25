"""It speaks the completed REST text as PCM with tool-free Gemini TTS.

It is not the new task/worker; It works on the same single chat lock as TextChat.
The text is not the command to be reinterpreted, but the content that TTS will read verbatim.
Audio remains only in limited RAM; error model/not does not replay operation.
"""
from base64 import b64decode
from threading import Event, Lock

from google import genai
from google.genai import types

from app.storage.credentials import load_gemini_key
from app.session.gemini import GeminiUsage, gemini_token_count

SPEECH_MODEL = 'gemini-3.8-flash-lite-tts'


class GeminiSpeech:
    """One HTTP synthesis and up to 60s PCM; Accepting a stop is not a real finish."""

    def __init__(self, *, usage: GeminiUsage | None = None):
        self._usage = usage
        self._stop = Event()
        self._gate = Lock()
        self._finished = self._http_active = False

    def stop(self) -> str | None:
        """Synchronous HTTP cannot be interrupted on the fly; It is not delivered after incoming PCM Stop."""
        with self._gate:
            if self._finished:
                return None
            self._stop.set()
            return 'speech_response' if self._http_active else 'speech_completion'

    def run(self, text: str, sink) -> dict:
        """Make one toolless request; registration/identity/profile/secrets is not included in the results."""
        result = {'ok': False, 'completed': True, 'speech_model': SPEECH_MODEL,
                  'audio_bytes_forwarded': 0, 'audio_error': None}
        try:
            if not isinstance(text, str) or not text.strip() or len(text) > 20000:
                result['audio_error'] = 'speech_text_limit'
                return result
            key = load_gemini_key()
            if not key:
                result['audio_error'] = 'speech_key_unavailable'
                return result
            # Interactions retry count is 0; normal REST model retry/fallback
            # policy is not used here. Don't charge the same answer again.
            retry = types.HttpRetryOptions(attempts=0)
            options = types.HttpOptions(timeout=20000, retry_options=retry)
            with genai.Client(api_key=key, vertexai=False, http_options=options) as client:
                # SDK 2.32 sets 0 to 1 in client installation; If Interactions
                # the number of repetitions reads this. Fix it without installing lazy resource.
                retry.attempts = 0
                with self._gate:
                    if self._stop.is_set():
                        return result
                    self._http_active = True
                try:
                    response = client.interactions.create(model=SPEECH_MODEL,
                        input=[{'type': 'user_input', 'content': [{'type': 'text', 'text': text}]}],
                        response_format={'type': 'audio', 'mime_type': 'audio/l16', 'sample_rate': 24000},
                        generation_config={'speech_config': [{'voice': 'Kore'}]}, store=False, timeout=20)
                    if self._usage is not None:
                        self._usage.add(gemini_token_count(response.usage, interaction=True))
                except Exception:
                    if self._usage is not None:
                        self._usage.add(None)
                    raise
                finally:
                    with self._gate:
                        self._http_active = False
                if self._stop.is_set():
                    return result
                audio = response.output_audio
                if (response.status != 'completed' or audio is None or audio.mime_type != 'audio/l16'
                        or audio.sample_rate != 24000 or audio.channels not in (None, 1)
                        or not isinstance(audio.data, str) or len(audio.data) > 3840000):
                    result['audio_error'] = 'invalid_speech_audio'
                    return result
                pcm = b64decode(audio.data, validate=True)
                if not pcm or len(pcm) % 2 or len(pcm) > 2880000:
                    result['audio_error'] = 'invalid_speech_audio'
                    return result
                for offset in range(0, len(pcm), 48000):
                    if self._stop.is_set():
                        return result
                    chunk = pcm[offset:offset + 48000]
                    if sink(chunk, 'audio/pcm;rate=24000') is not True:
                        result['audio_error'] = 'playback_unavailable'
                        return result
                    result['audio_bytes_forwarded'] += len(chunk)
                    # At most 1 s chunks stream at real-time speed; available
                    # The 20 s Web Audio queue is not overrun by a single large response.
                    if self._stop.wait(len(chunk) / 48000):
                        return result
                result['ok'] = True
        except Exception:
            result['audio_error'] = 'speech_unavailable'  # Raw SDK text may contain secrets.
        finally:
            with self._gate:
                if self._stop.is_set():
                    result.update(ok=False, code='stopped', stopped=True, audio_error='stopped')
                self._finished = True
        return result
