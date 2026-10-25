"""Select and verify only allowed preferences from Generic UI save.

Not/skill/routine and credential ownership do not belong to this module. log file
also goes through the same scheme; Just because it's valid JSON doesn't mean it's a valid setting.
"""

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from app.core.contracts import ContractError, copy_json


_TEXT = {"type": "string", "maxLength": 16_000}
_COLOR = {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"}
_WIDGETS = ["time", "system", "timer", "weather", "calendar", "remind", "notes", "media", "net", "log"]
_FIELDS = {
    'weatherLocation':{'type':['object','null'],'properties':{
        'label':{'type':'string','minLength':1,'maxLength':240},
        'latitude':{'type':'number','minimum':-90,'maximum':90},
        'longitude':{'type':'number','minimum':-180,'maximum':180},'source':{'enum':['manual','auto']}},
        'required':['label','latitude','longitude','source'],'additionalProperties':False},
    "theme": _COLOR,
    "colors": {"type": "object", "properties": {k: _COLOR for k in
               ["idle", "sleeping", "listening", "thinking", "speaking", "executing", "activating"]}, "additionalProperties": False},
    "prof": {"type": "object", "properties": {
        **{k: _TEXT for k in ["pLang", "pBr", "pIns", "pMem", "pSc", "pSys", "pGreet"]},
        "pWake": {"type":"string", "minLength":1, "maxLength":64, "pattern":"^[A-Za-z]+(?: [A-Za-z]+){0,2}$"},
        "pTab": {"type": "boolean"}, "pApp": {"type": "boolean"},
        "pMemory": {"type": "boolean"}, "pLearn": {"type":"boolean"}, "pMemoryConfirm": {"type":"boolean"}}, "additionalProperties": False},
    "devs": {"type": "object", "properties": {k: {"type": ["string", "integer", "null"]}
             for k in ["dIn", "dOut", "dCam"]}, "additionalProperties": False},
    "conn": {"type": "object", "properties": {k: _TEXT for k in ["model", "voice"]}, "additionalProperties": False},
    "sfx": {"type": "boolean"}, "onTop": {"type": "boolean"},
    "vol": {"type": "number", "minimum": 0, "maximum": 1},
    "replyVolume": {"type": "number", "minimum": 0, "maximum": 1},
    "sleepDelay": {"type": "integer", "minimum": 0, "maximum": 300},
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

# Reset covers appearance/behavior preferences only; profile, device/connection and
# collections are not available here. The default is preserved by making a copy with each use.
INTERFACE_DEFAULTS = {"theme": "#a78bfa", "colors": {}, "sfx": True, "vol": 0.8, "replyVolume": 1,
                      "wake": 50, "sleepDelay": 10, "noise": 420, "onTop": False, "cmp": "auto",
                      "tab": "theme", "layout": None}


def validate_settings(data: dict, *, from_ui: bool = False) -> dict:
    """Project UI payload; Reject the unknown area in the disk record.

    UI store carries collections; We do not write these. within a permitted area
    If the unknown field (e.g. conn.apikey) is not kept silent, the entire record is rejected.
    The return is independent copy; The error does not put user data in its message.
    """
    if type(data) is not dict:
        raise ContractError("Expected settings object")
    # Location consent is owned by the explicit weather selection flow, never a generic save/import.
    candidate = copy_json({k: v for k, v in data.items() if k in _FIELDS and k!='weatherLocation'} if from_ui else data)
    try:
        _VALIDATOR.validate(candidate)
    except ValidationError:
        raise ContractError("Settings do not match the supported fields and ranges") from None
    layout = candidate.get("layout") or []
    if len({item["id"] for item in layout}) != len(layout):
        raise ContractError("Settings layout has duplicate widget ids")
    return candidate
