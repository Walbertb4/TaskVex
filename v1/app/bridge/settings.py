"""Generic UI save içinden yalnız izinli tercihleri seç ve doğrula.

Not/skill/rutin ve credential sahipliği bu modüle ait değildir. Kayıt dosyası
da aynı şemadan geçer; geçerli JSON olması geçerli ayar olduğu anlamına gelmez.
"""

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from app.core.contracts import ContractError, copy_json


_TEXT = {"type": "string", "maxLength": 16_000}
_COLOR = {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"}
_WIDGETS = ["time", "system", "timer", "weather", "calendar", "remind", "notes", "media", "net", "log"]
_FIELDS = {
    "theme": _COLOR,
    "colors": {"type": "object", "properties": {k: _COLOR for k in
               ["idle", "sleeping", "listening", "thinking", "speaking", "executing", "activating"]}, "additionalProperties": False},
    "prof": {"type": "object", "properties": {
        **{k: _TEXT for k in ["pLang", "pBr", "pIns", "pMem", "pSc", "pSys", "pGreet"]},
        "pWake": {"type":"string", "minLength":1, "maxLength":64, "pattern":"^[A-Za-z]+(?: [A-Za-z]+){0,2}$"},
        "pTab": {"type": "boolean"}, "pApp": {"type": "boolean"}}, "additionalProperties": False},
    "devs": {"type": "object", "properties": {k: {"type": ["string", "integer", "null"]}
             for k in ["dIn", "dOut", "dCam"]}, "additionalProperties": False},
    "conn": {"type": "object", "properties": {k: _TEXT for k in ["model", "voice"]}, "additionalProperties": False},
    "sfx": {"type": "boolean"}, "onTop": {"type": "boolean"},
    "vol": {"type": "number", "minimum": 0, "maximum": 1},
    "wake": {"type": "number", "minimum": 0, "maximum": 100},
    "noise": {"type": "number", "minimum": 0, "maximum": 1000},
    "cmp": {"enum": ["auto", "on", "off"]},
    "tab": {"enum": ["theme", "audio", "connection", "interface", "system"]},
    "layout": {"type": ["array", "null"], "maxItems": 10, "items": {
        "type": "object", "properties": {"id": {"enum": _WIDGETS}, "c": {"enum": ["L", "R"]},
        "on": {"enum": [0, 1]}, "sz": {"type": "integer", "minimum": 0, "maximum": 2}},
        "required": ["id", "c", "on", "sz"], "additionalProperties": False}},
}
_VALIDATOR = Draft202012Validator({"type": "object", "properties": _FIELDS, "additionalProperties": False})

# Reset yalnız görünüm/davranış tercihlerini kapsar; profil, cihaz/bağlantı ve
# koleksiyonlar burada yoktur. Her kullanımda kopya alınarak varsayılan korunur.
INTERFACE_DEFAULTS = {"theme": "#a78bfa", "colors": {}, "sfx": True, "vol": 0.8,
                      "wake": 50, "noise": 420, "onTop": False, "cmp": "auto",
                      "tab": "theme", "layout": None}


def validate_settings(data: dict, *, from_ui: bool = False) -> dict:
    """UI payload'ını projekte et; disk kaydındaki bilinmeyen alanı ise reddet.

    UI store koleksiyonlar taşır; bunları yazmayız. İzinli bir alanın içindeki
    bilinmeyen alan (ör. conn.apikey) ise sessiz saklanmaz, bütün kayıt reddedilir.
    Dönüş bağımsız kopyadır; hata kullanıcı verisini mesajına koymaz.
    """
    if type(data) is not dict:
        raise ContractError("Expected settings object")
    candidate = copy_json({k: v for k, v in data.items() if k in _FIELDS} if from_ui else data)
    try:
        _VALIDATOR.validate(candidate)
    except ValidationError:
        raise ContractError("Settings do not match the supported fields and ranges") from None
    layout = candidate.get("layout") or []
    if len({item["id"] for item in layout}) != len(layout):
        raise ContractError("Settings layout has duplicate widget ids")
    return candidate
