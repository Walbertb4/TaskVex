"""Gemini model listesini API'den oku; yalnız bildirilen Live yeteneğini göster.

Model adından tahmin veya sabit model listesi yoktur. Listeleme üretim isteği
değildir ve Live WebSocket erişiminin/konuşmanın çalıştığını kanıtlamaz.
"""

import re

from google import genai
from google.genai import types

from app.storage.credentials import load_gemini_key


def load_live_catalog() -> dict:
    """En çok beş sayfa oku; tam başarı yoksa kısmi/eski listeyi başarı sayma.

    SDK supported_actions alanı REST supportedGenerationMethods karşılığıdır.
    bidiGenerateContent bildirmeyen kayıt, adı live içerse bile gösterilmez.
    Her sayfa 10 saniye ile sınırlıdır; istemci bütün çıkışlarda kapatılır.
    Anahtar, ham sağlayıcı hatası veya hesap bilgisi sonuçlara konmaz.
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
