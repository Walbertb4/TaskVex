"""Model araç çağrılarını mevcut core'a taşıyan küçük oturum adaptörü.

Bu modül model çalıştırmaz, ağ bağlantısı veya yeni worker açmaz. Sağlayıcının
çağrısı id/name/arguments biçimine çevrildikten sonra buraya gelir. Parametre
şemasının sahibi registry, iznin sahibi policy, yürütmenin sahibi TaskManager'dır.
Gemini SDK nesneleri bu sınırdan içeri girmez.
"""

from hashlib import sha256
import json
import re

from app.core.contracts import ContractError, Task, ToolRequest
from app.tasks.manager import TaskManager


NOTE_TARGET_INSTRUCTION = (
    "Before notes.update/delete, call notes.list in this user turn and use its actual record IDs. "
    "A quoted literal contains filter (e.g. içinde 'merh' geçen not, or note containing 'merh') "
    "may select exactly one matching note. Never use fuzzy matching or select one of multiple matches. "
    "For 'son notu'/'latest note', use the unique greatest created_at, never list position; "
    "if any note lacks a creation time or the latest time is tied, ask for an explicit ID. "
    "Do not combine latest and contains filters. Never guess a target: ask for exact text or ID when unclear. "
    "For ambiguous matches, show the actual candidate IDs and ask for an explicit record ID. "
    "Do not infer an ID from list position. "
)


def _fold_text(value: str) -> str:
    """Yazım ayrıntılarını eşleştir; içerik/ID'yi depoda değiştirme.

    Türkçe büyük İ'nin casefold çıktısındaki birleşen nokta kaldırılır;
    tipografik tırnaklar aynı literal sorgunun parçası olarak okunur.
    """
    value = value.translate(str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"}))
    return " ".join(value.casefold().replace("\u0307", "").split())


class NoteTargetError(ContractError):
    """Yazı yapılmadan hedef açıklaması iste; ham model/veri hatasını UI'a taşıma."""

    code = "note_target_required"

    def __init__(self):
        super().__init__("Hangi notu değiştireyim? Notları listeleyip mevcut tam metni veya kayıt ID’sini belirt. "
                         "Tek eşleşen tırnaklı bir içerik filtresi de kullanabilirsin. Birden fazla adayda veya son notun "
                         "zamanı doğrulanamıyorsa ID gerekli. Bu hedefe işlem yapılmadı; önceki doğrulanmış işlemler korunur.")


class ModelTools:
    """Tek mantıksal model oturumunu güvenilir kullanıcı ve araç listesine bağla.

    core, principal, session_id ve allowed_tools güvenilir host tarafından seçilir;
    model payload'ından alınmaz. Yeniden bağlantı aynı session_id'yi korumalıdır.
    Bu nesne core'un sahibi değildir; oluşturmaz veya kapatmaz.
    """

    def __init__(self, core: TaskManager, *, principal: str, session_id: str,
                 allowed_tools: tuple[str, ...]) -> None:
        if any(not isinstance(value, str) or not value.strip()
               for value in (principal, session_id)):
            raise ContractError("Expected a principal and model session id")
        if not isinstance(allowed_tools, tuple) or any(
            not isinstance(name, str) for name in allowed_tools
        ):
            raise ContractError("Expected a tuple of allowed tool names")
        declarations = core.describe_tools()
        self._allowed = frozenset(allowed_tools)
        if not self._allowed <= {item["name"] for item in declarations}:
            raise ContractError("Model tool is not registered")
        self._core, self._principal, self._session_id = core, principal, session_id
        self._calls: dict[str, str] = {}
        self._user_text = ""
        self._notes: list[dict] | None = None
        self._fresh_reads: set[str] = set()

    def begin_turn(self, text: str) -> None:
        """Host'un güncel mesajını bağla; eski Live listesini yeni seçim sayma.

        Çağrı kimlikleri korunur; yalnız hedef seçme kanıtı sıfırlanır. Böylece
        resume/replay önceki yazıyı tekrar etmez, yeni komut ise yeni liste ister.
        """
        self._user_text = _fold_text(text)
        self._notes = None
        self._fresh_reads.clear()

    def _check_note_target(self, arguments: object) -> None:
        """Modelin tahmin ettiği ID'yi kullanıcı seçimi yerine kabul etme.

        Açık ID, tırnaklı literal içerik filtresi, en yeni oluşturulma zamanı
        veya tek tam metin seçilir. Serbest tarif, bulanık benzerlik ve çoklu
        hedef çözülmez. CRUD/dosya/izin doğrulaması mevcut core'da kalır.
        """
        if not isinstance(arguments, dict) or self._notes is None:
            raise NoteTargetError
        target = next((note for note in self._notes if note["id"] == arguments.get("id")), None)
        if target is None:
            raise NoteTargetError

        def mentioned(value: str) -> bool:
            normalized = _fold_text(value)
            return re.search(r"(?<!\w)" + re.escape(normalized) + r"(?!\w)", self._user_text) is not None

        explicit_ids = [note["id"] for note in self._notes if mentioned(note["id"])]
        if explicit_ids == [target["id"]]:
            return
        if explicit_ids:
            raise NoteTargetError

        # Literal sorgu yalnız kullanıcının kendi tırnaklarından çıkarılır;
        # modelin önerdiği kısmi metin, kullanıcı seçimi yerine geçemez.
        queries = []
        quoted = list(re.finditer(r"([\"'])(.*?)\1", self._user_text))
        for match in quoted:
            before, after = self._user_text[:match.start()], self._user_text[match.end():]
            if re.match(r"\s+(?:geçmeyen|içermeyen|bulunmayan|olmayan)\b", after):
                raise NoteTargetError
            prefix_tr = re.search(r"\b(?:içinde|içerisinde)\s*$", before)
            prefix_en = re.search(r"\b(?:containing|contains)\s*$", before)
            suffix_tr = re.match(r"\s+(?:geçen|içeren|bulunan)\s+not\w*\b", after)
            if prefix_tr or prefix_en or suffix_tr:
                if (prefix_tr and not re.match(r"\s+(?:geçen|olan|bulunan)\b", after)
                        or prefix_en and re.search(r"\bnot\s+(?:containing|contains)\s*$", before)):
                    raise NoteTargetError
                queries.append(match.group(2).strip())
        outside_quotes = re.sub(r"([\"'])(.*?)\1", " ", self._user_text)
        latest = re.findall(r"\b(?:(?:en\s+)?son(?:\s+(?:eklediğim|eklenen|oluşturulan))?\s+"
                            r"not(?:u|un|um|umu|umun)?|(?:last|latest|newest)(?:\s+(?:added|created))?\s+note)\b", outside_quotes)
        filter_words = re.search(r"\b(?:içinde|içerisinde|geçen|içeren|containing|contains|contain|without)\b", outside_quotes)
        if queries:
            if len(queries) != 1 or not queries[0] or latest:
                raise NoteTargetError
            matches = [note["id"] for note in self._notes if queries[0] in _fold_text(note["text"])]
        elif latest:
            if len(latest) != 1 or filter_words or any(not note.get("created_at") for note in self._notes):
                raise NoteTargetError
            # Core listeyi doğrulamıştır: canonical UTC ISO metinler tarih
            # sırasıyla karşılaştırılabilir. Liste konumu ve ID sıralanmaz.
            newest = max(note["created_at"] for note in self._notes)
            matches = [note["id"] for note in self._notes if note["created_at"] == newest]
        elif filter_words:
            raise NoteTargetError  # Tırnaksız/olumsuz/bozuk filtreyi tam metin sanma.
        else:
            matches = [note["id"] for note in self._notes if mentioned(note["text"])]
        if matches != [target["id"]]:
            raise NoteTargetError

    def declarations(self) -> list[dict]:
        """Host'un izin verdiği araç şemalarını bağımsız JSON verisi olarak ver."""
        return [item for item in self._core.describe_tools() if item["name"] in self._allowed]

    def submit(self, call: object) -> Task:
        """id/name/arguments çağrısını sıraya al; kabulü başarı sayma.

        Eksik/fazla alan, geçersiz JSON, görünmeyen araç veya hatalı parametre
        reddedilir. Aynı oturum/çağrı kimliği aynı manager request_id'sini üretir;
        içerik değişmişse manager çakışma verir, yan etkiyi tekrarlamaz.
        """
        if not isinstance(call, dict) or set(call) != {"id", "name", "arguments"}:
            raise ContractError("Expected only id, name and arguments")
        call_id, name = call["id"], call["name"]
        if not isinstance(call_id, str) or not call_id.strip():
            raise ContractError("Expected a model call id")
        if not isinstance(name, str) or name not in self._allowed:
            raise ContractError("Tool is not exposed to this model session")
        # Replay seçim kontrolünden önce tanınır: silinmiş notun eski başarılı
        # çağrısı yeniden listede bulunmayabilir. İçerik çakışmasını manager denetler.
        replay = call_id in self._calls.values()
        if not replay and name in {"notes.update", "notes.delete"}:
            self._check_note_target(call["arguments"])
        # Çiftin JSON kodlaması ('ab','c') ile ('a','bc') karışmasını önler.
        # Ayrı model oturumlarında aynı sağlayıcı çağrı kimliği çakışmamalıdır.
        key = sha256(json.dumps([self._session_id, call_id], ensure_ascii=True).encode()).hexdigest()
        task = self._core.submit(ToolRequest(
            request_id=f"model:{key}", source="desktop", principal=self._principal,
            tool=name, arguments=call["arguments"],
        ))
        self._calls[task.task_id] = call_id
        if not replay:
            if name == "notes.list":
                self._notes = None
                self._fresh_reads.clear()
                self._fresh_reads.add(task.task_id)
            elif name.startswith("notes."):
                self._notes = None
                self._fresh_reads.clear()
        return task

    def _call_id(self, task_id: str) -> str:
        """Başka bir oturumun/UI'ın görevini okuma veya iptal etme."""
        if not isinstance(task_id, str) or task_id not in self._calls:
            raise ContractError("Task does not belong to this model session")
        return self._calls[task_id]

    def result(self, task_id: str, *, timeout: float = 0) -> dict:
        """Çağrı kimliğiyle birlikte gerçek görev durumunu ve sonucunu döndür.

        Bekleme süresinin dolması işlemin başarısız/iptal olduğu anlamına gelmez;
        güncel queued/running/cancel_requested ve result=None korunur. Sağlayıcı
        yalnız terminal durumda function response göndermelidir. Sonucu yeniden
        okumak yeni görev göndermez. Burada ham istek/kullanıcı kimliği paylaşılmaz.
        """
        call_id = self._call_id(task_id)
        try:
            task = self._core.wait(task_id, timeout)
        except TimeoutError:
            task = self._core.get(task_id)
        if task_id in self._fresh_reads and task.status.terminal:
            self._fresh_reads.discard(task_id)
            if task.result is not None and task.result.verified and task.status.value == "succeeded":
                self._notes = task.result.to_dict()["data"]["notes"]
        return {"id": call_id, "name": task.request.tool, "task_id": task.task_id,
                "status": task.status.value,
                "result": task.result.to_dict() if task.result is not None else None}

    def cancel(self, task_id: str) -> Task:
        """Yalnız bu oturumun görevini iptal et; çalışan işte tamamlanmayı bekle."""
        self._call_id(task_id)
        return self._core.cancel(task_id)
