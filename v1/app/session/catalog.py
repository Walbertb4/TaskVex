"""Read Gemini model list from API; Show only declared Live ability.

There is no guesswork or fixed model list from the model name. Listing production request
is not and does not prove that Live WebSocket access/talk works.
"""

import re

from google import genai
from google.genai import types

from app.storage.credentials import load_gemini_key

# Google Live voice document (2026-10-24): this list was not discovered from the API.
# https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice
# Only documented ready-made Live sounds; Adding exclusive/TTS-only sounds.
LIVE_VOICES = tuple('Zephyr Puck Charon Kore Fenrir Leda Orus Aoede Callirrhoe '
    'Autonoe Enceladus Iapetus Umbriel Algieba Despina Erinome Algenib Rasalgethi '
    'Laomedeia Achernar Alnilam Schedar Gacrux Pulcherrima Achird Zubenelgenubi '
    'Vindemiatrix Sadachbia Sadaltager Sulafat'.split())


def live_voice_catalog() -> list[dict]:
    """Generate UI options from the same permission list; It is not proof of account access."""
    return [{'id': voice, 'name': voice, 'live': True} for voice in LIVE_VOICES]


def selected_live_voice(value: object) -> str:
    """move legacy preference to Puck; sending unknown name to provider."""
    return value if isinstance(value, str) and value in LIVE_VOICES else 'Puck'


def load_live_catalog() -> dict:
    """Read no more than five pages; If there is no complete success, do not count the partial/old list as success.

    The SDK supported_actions field is the REST equivalent of supportedGenerationMethods.
    A record that does not declare bidiGenerateContent will not be shown, even if its name contains live.
    Each page is limited to 10 seconds; The client is closed at all exits.
    No key, raw provider error, or account information is put into the results.
    """
    try:
        key = load_gemini_key()
        if not key:
            return {"ok": False, "error": "Save a Gemini API key or set GEMINI_API_KEY, then load Live models."}
        models = {}
        with genai.Client(api_key=key, vertexai=False, http_options=types.HttpOptions(
                timeout=10_000, retry_options=types.HttpRetryOptions(attempts=1))) as client:
            pager = client.models.list(config=types.ListModelsConfig(page_size=100))
            for page_index in range(5):
                for item in pager.page:
                    if "bidiGenerateContent" not in (item.supported_actions or []):
                        continue
                    if not item.name or not re.fullmatch(r"models/[A-Za-z0-9][A-Za-z0-9._-]{0,180}", item.name):
                        continue
                    name = item.name.removeprefix("models/")
                    models[name] = {"id": name, "name": (item.display_name or name)[:256], "live": True}
                if not pager.config.get("page_token"):
                    break
                if page_index == 4:
                    return {"ok": False, "error": "Live catalog exceeds the page limit; no partial list was applied."}
                pager.next_page()
        return {"ok": True, "completed": True, "models": sorted(models.values(), key=lambda item: item["id"])}
    except Exception:
        return {"ok": False, "error": "Live model catalog could not be loaded. Check key, network and API access."}
