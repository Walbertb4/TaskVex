"""Kullanıcı hafızası işlemleri ve onay bekleyen adaylar için tek alan sahibi.

Yeni depo veya doğal dil çözücüsü yoktur. Model yapılandırılmış değişikliği
seçer; taze snapshot ve tekil hedef diskte tekrar doğrulanır. Native host aynı
JsonStore örneğinin kilidini paylaşır; UI kaydıyla yarışıp tercih kaybetmeyiz.
"""
from hashlib import sha256
import json
from uuid import uuid4

from app.storage.settings import validate_settings
from app.core.contracts import ContractError, TaskStatus, ToolContext, ToolError, ToolResult
from app.storage.json_store import JsonStore, StoreError

READ_SCHEMA = {"type": "object", "additionalProperties": False}
_TEXT = {"type": "string", "minLength": 1, "maxLength": 16_000, "pattern": r"\S"}
PATCH_SCHEMA = {"type": "object", "additionalProperties": False,
    "properties": {"action": {"enum": ["append", "replace", "forget", "clear"]},
        "text": _TEXT, "replacement": _TEXT,
        "expected_snapshot": {"type": "string", "pattern": "^[0-9a-f]{64}$"}},
    "required": ["action", "expected_snapshot"]}

PROPOSE_SCHEMA = {"type":"object", "additionalProperties":False,
    "properties":{"source_verified":{"type":"boolean"}, "text":{**_TEXT,"maxLength":1000}, "source_quote":{"type":"string","maxLength":20_000},
                  "expected_snapshot":PATCH_SCHEMA['properties']['expected_snapshot']},
    "required":["text","source_quote","expected_snapshot","source_verified"]}
DECIDE_SCHEMA = {"type":"object", "additionalProperties":False,
    "properties":{"id":{"type":"string","pattern":"^[0-9a-f]{32}$"}, "approve":{"type":"boolean"}},
    "required":["id","approve"]}


def memory_base(profile: dict) -> dict:
    """UI karşılaştırması için yalnız hafıza metni ve açık gönderim tercihi."""
    return {"pMem": profile.get("pMem", ""), "pMemory": profile.get("pMemory", False)}


def memory_snapshot(profile: dict) -> str:
    """Metin ve izin değişimi eski model seçimini birlikte geçersiz kılar."""
    return sha256(json.dumps({**memory_base(profile), "pLearn":profile.get("pLearn", False), "pMemoryConfirm":profile.get("pMemoryConfirm", True)}, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _failure(context: ToolContext, code: str, message: str, *, unknown: bool = False) -> ToolResult:
    return ToolResult(task_id=context.task_id, status=TaskStatus.UNKNOWN if unknown else TaskStatus.FAILED,
                      error=ToolError(code=code, message=message))


class PersonalMemory:
    """Profil belgesinin alan aracı; dosyanın sahibi mevcut ayar deposudur."""

    def __init__(self, store: JsonStore) -> None:
        self._store = store
        # Tek aday RAM'de bekler; yeni öneri eskisini geçersiz kılar. Restart onay sayılmaz.
        self._proposal: dict | None = None

    def read(self, arguments: dict, context: ToolContext) -> ToolResult:
        """İzin kapalıysa yerel metni modele sızdırmadan reddet."""
        if arguments:
            return _failure(context, "invalid_arguments", "Memory read accepts no arguments")
        return self._apply(None, context)

    def patch(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Dar değişikliği uygula; hedef eksik/çokluysa bütün belgeyi koru."""
        action = arguments.get("action")
        fields = {"append": {"text"}, "replace": {"text", "replacement"}, "forget": {"text"}, "clear": set()}
        if (not isinstance(action, str) or action not in fields
                or set(arguments) != {"action", "expected_snapshot"} | fields[action]
                or any(not isinstance(arguments[k], str) or not arguments[k].strip()
                       or len(arguments[k]) > 16_000 for k in fields[action])):
            return _failure(context, "invalid_arguments", "Expected one structured memory change")
        return self._apply(arguments, context)

    def propose(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Kullanıcı tercihine göre aday üret veya aynı append yoluyla doğrulayarak kaydet.

        ModelTools bu turun gerçek girdisini kaynak olarak kendisi bağlar. Burada
        güncel izin/snapshot tekrar doğrulanır; eski onay yeni adayı kaydedemez.
        """
        if arguments.get('source_verified') is not True:
            return _failure(context, 'source_unavailable', 'Source quote is not in the current user input; skip the suggestion and continue the reply')
        with self._store.lock:
            result = self._apply(None, context)
            if not result.verified:
                return result
            profile = (self._store.read() or {}).get('prof', {})
            if profile.get('pLearn') is not True:
                return _failure(context, 'learning_disabled', 'Enable memory suggestions in Personalization first')
            if arguments.get('expected_snapshot') != result.data['snapshot']:
                return _failure(context, 'memory_changed', 'Memory changed; no suggestion was created')
            text = arguments['text']
            if text in result.data['text']:
                return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                                  data={'proposal':None}, evidence={'already_saved':True, 'persisted':False})
            if profile.get('pMemoryConfirm', True) is False:
                # Sormadan kayıt yalnız kullanıcının kalıcı tercihinden gelir;
                # model bir auto_save/onay parametresi gönderemez.
                saved = self._apply({'action':'append', 'text':text,
                    'expected_snapshot':result.data['snapshot']}, context)
                if saved.verified:
                    self._proposal = None
                    return ToolResult(task_id=context.task_id, status=saved.status, verified=True,
                        data={**saved.to_dict()['data'], 'proposal':None, 'saved_automatically':True},
                        evidence=saved.to_dict()['evidence'])
                return saved
            self._proposal = {'id':uuid4().hex, 'text':text, 'source_quote':arguments['source_quote'],
                              'snapshot':result.data['snapshot']}
            return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                              data={'proposal':self._proposal}, evidence={'persisted':False, 'approval_required':True})

    def decide(self, arguments: dict, context: ToolContext) -> ToolResult:
        """Yalnız native kullanıcı düğmesinden onay/ret; modele açılmaz.

        Onaylanan metin UI payload'ından değil bu alan sahibindeki adaydan alınır.
        Aynı append iş mantığı kullanılır. Değişmiş izin/belge ve eski ID ret verir.
        """
        with self._store.lock:
            proposal = self._proposal
            if proposal is None or arguments.get('id') != proposal['id']:
                return _failure(context, 'proposal_expired', 'This suggestion is no longer current')
            if context.cancel_event.is_set():
                return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
            if not arguments['approve']:
                self._proposal = None
                return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                                  data={'dismissed':True}, evidence={'persisted':False})
            result = self._apply({'action':'append', 'text':proposal['text'],
                                  'expected_snapshot':proposal['snapshot']}, context)
            if result.status.terminal:
                self._proposal = None
            return result

    def _apply(self, change: dict | None, context: ToolContext) -> ToolResult:
        """Kontrol/yazma/readback tek kısa kilitte; geç iptal gerçek etkiyi silmez.

        Yazma başladıktan sonraki doğrulama hatası belirsizdir; otomatik tekrar
        yapılmamalıdır. Günlük eski metni tutabilir, unutma geçmiş silme değildir.
        """
        with self._store.lock:
            written = False
            try:
                data = validate_settings(self._store.read() or {})
                profile = data.get("prof", {})
                if profile.get("pMemory") is not True:
                    return _failure(context, "memory_disabled", "Enable personal memory in Personalization first; no local memory was disclosed or changed")
                text = profile.get("pMem", "")
                if context.cancel_event.is_set():
                    return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
                if change is not None:
                    if change.get("expected_snapshot") != memory_snapshot(profile):
                        return _failure(context, "memory_changed", "Memory changed; ask the user before selecting again")
                    action = change["action"]
                    if action in ("replace", "forget") and text.count(change["text"]) != 1:
                        return _failure(context, "memory_target_required", "The exact memory target is missing or ambiguous; ask the user to clarify")
                    if action == "append":
                        updated = text + ("\n" if text else "") + change["text"]
                    elif action == "clear":
                        updated = ""
                    else:
                        updated = text.replace(change["text"], change.get("replacement", ""), 1)
                    candidate = validate_settings({**data, "prof": {**profile, "pMem": updated}})
                    if context.cancel_event.is_set():
                        return ToolResult(task_id=context.task_id, status=TaskStatus.CANCELLED)
                    self._store.write(candidate)
                    written = True
                    if self._store.read() != candidate:
                        return _failure(context, "memory_unverified", "Memory write could not be verified; do not repeat", unknown=True)
                    profile = candidate["prof"]
                return ToolResult(task_id=context.task_id, status=TaskStatus.SUCCEEDED, verified=True,
                    data={"text": profile.get("pMem", ""), "snapshot": memory_snapshot(profile)},
                    evidence={"store_read": True, "persisted": change is not None, "read_back": change is not None})
            except (StoreError, ContractError):
                return _failure(context, "memory_unverified" if written else "memory_unavailable",
                    "Personal memory could not be verified; no automatic retry", unknown=written)
