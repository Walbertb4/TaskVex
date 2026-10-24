"""Gemini metin turu: sağlayıcı çağrılarını TaskVex'in ortak araç hattına bağla.

SDK yalnız modelle konuşur; araçları kendisi yürütmez. Bir run çağrısı bir
kullanıcı isteğidir. Araç sonucunu geri gönderirken modelin Content nesnesi
aynen korunur; düşünme imzası gibi sağlayıcı bağlamı yeniden üretilmez.
UI/Live bağlantısı burada yoktur. Core ve ModelTools'un sahibi güvenilir host'tur.
"""

from random import uniform
from time import perf_counter
from threading import Event, Lock
from uuid import uuid4

import httpx
from google import genai
from google.genai import errors, types

from app.core.contracts import ContractError, TaskStatus
from app.session.model_tools import ModelTools, NoteTargetError
from app.session.model_instruction import model_instruction
from app.storage.credentials import load_gemini_key


DEFAULT_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"
MAX_REQUESTS = 5
MAX_TOOL_CALLS = 8
TOOL_WAIT_SECONDS = 5


def gemini_token_count(metadata, *, interaction: bool = False) -> int | None:
    """SDK metadata'sını güvenli tam sayıya çevir; eksik veri sıfır değildir.

    GenerateContent/Live total_token_count, Interactions TTS total_tokens kullanır.
    Bunlar toplam alanlarıdır; alt kalemleri yeniden ekleyip çift saymayız.
    """
    value = getattr(metadata, 'total_tokens' if interaction else 'total_token_count', None)
    return value if type(value) is int and 0 <= value <= 9007199254740991 else None


class GeminiUsage:
    """Tek uygulama oturumunun Gemini kullanım sahibi; yalnız RAM, sır/metin tutmaz.

    REST'te her gerçek HTTP yanıtı (araç turları dahil) bir kez eklenir. Live'da
    aynı üretimdeki ara usage bildirimleri ayrı istek değildir: son snapshot
    araç çağrısı veya tur bitiş sınırında bir kez eklenir. Stop/model/transport değişimi
    bu nesneyi yenilemez. Eksik/başarısız isteğin maliyetini tahmin etmeyiz;
    bilinen toplam korunur ve eksik ölçüm işareti oturum boyunca kalır.
    """
    def __init__(self) -> None:
        self._lock = Lock()
        self._total = 0
        self._seen = False
        self._partial = False
        self._live_pending: int | None = None
        self._live_seen = False

    def observe_live(self, metadata) -> None:
        """Aynı Live üretiminin son snapshot'ını tut; güncellemeleri toplama."""
        self._live_pending = gemini_token_count(metadata)
        self._live_seen = True

    def live_boundary(self) -> None:
        """Araç çağrısı/final yanıt bir üretimi kapatır; sonraki üretim ayrı sayılır."""
        self.add(self._live_pending)
        self._live_pending = None

    def finish_live(self, result: dict) -> None:
        """Tur özeti çıkar; aynı yanıtı UI'da tekrar göstermek yeniden toplamaz."""
        self.live_boundary()
        snapshot = self.report({})
        if self._live_seen:
            result['usage_tokens'] = snapshot['usage_tokens']
        result['usage_partial'] = snapshot['usage_partial']

    def add(self, count: int | None, *, partial: bool = False) -> None:
        """Ayrı sağlayıcı isteğini ekle; negatif/bool/taşma toplamı bozamaz."""
        with self._lock:
            self._partial = self._partial or partial
            if type(count) is not int or count < 0 or self._total + count > 9007199254740991:
                self._partial = True
            else:
                self._total += count
                self._seen = True

    def report(self, result: dict) -> dict:
        """UI'a aynı toplamı verir; sonucu okumak kullanım eklemez."""
        with self._lock:
            return {**result, 'usage_tokens':self._total if self._seen else None,
                'usage_scope':'session', 'usage_partial':self._partial}


class _Stopped(Exception):
    """Yalnız adaptör içi akış kesmesi; sağlayıcı hatası veya başarı değildir."""


def _failure(code: str, message: str, results: list[dict]) -> dict:
    """Hata halinde önceki araç sonuçlarını koru; ham SDK hatası/sır taşıma."""
    return {"ok": False, "code": code, "error": message, "text": "", "tool_results": results}


def _api_failure(error: errors.APIError, results: list[dict]) -> dict:
    """Teşhis kodlarını koru; serbest hata metni, URL ve metadata'yı taşıma.

    SDK exception metni anahtar veya kişisel veri içerebilir. Yalnız HTTP kodu
    ve açık listedeki standart durum/nedenler sonuç JSON'una girebilir.
    """
    code = {400: "invalid_request", 401: "authentication_failed", 402: "billing_required",
            403: "permission_denied", 404: "model_unavailable",
            429: "quota_exceeded"}.get(error.code, "provider_error")
    report = _failure(code, "Gemini request failed; tools were not retried", results)
    report["http_status"] = error.code
    if isinstance(error.status, str) and error.status in {
        "INVALID_ARGUMENT", "UNAUTHENTICATED", "PERMISSION_DENIED", "NOT_FOUND",
        "RESOURCE_EXHAUSTED", "FAILED_PRECONDITION", "INTERNAL", "UNAVAILABLE",
        "DEADLINE_EXCEEDED", "UNIMPLEMENTED", "UNKNOWN",
    }:
        report["provider_status"] = error.status
    body = error.details.get("error", error.details) if isinstance(error.details, dict) else {}
    details = body.get("details", []) if isinstance(body, dict) else []
    if isinstance(details, list):
        for item in details:
            reason = item.get("reason") if isinstance(item, dict) else None
            if isinstance(reason, str) and reason in {
                "API_KEY_INVALID", "API_KEY_EXPIRED", "API_KEY_SERVICE_BLOCKED",
                "API_KEY_HTTP_REFERRER_BLOCKED", "API_KEY_IP_ADDRESS_BLOCKED",
                "ACCESS_TOKEN_EXPIRED", "ACCESS_TOKEN_TYPE_UNSUPPORTED",
                "CREDENTIALS_MISSING", "SERVICE_DISABLED", "BILLING_DISABLED",
            }:
                report["provider_reason"] = reason
                break
    return report


class GeminiText:
    """Bir SDK istemcisini kullan; ağ isteği yalnız açık run çağrısında başlar.

    api_key verilmezse süreç ortamı, yoksa profilin Windows kimlik deposu okunur.
    Anahtar bu adaptörce kaydedilmez ve sonuçlara eklenmez. model ve tools host tarafından seçilir.
    Bu istemciyi with ile kullan veya close çağır; core'u ayrıca host kapatır.
    """

    def __init__(self, tools: ModelTools, *, model: str = DEFAULT_MODEL,
                 api_key: str | None = None, profile: dict | None = None, usage: GeminiUsage | None = None) -> None:
        key = load_gemini_key() if api_key is None else api_key
        if not isinstance(key, str) or not key.strip():
            raise ContractError("GEMINI_API_KEY is missing")
        if not isinstance(model, str) or not model.strip():
            raise ContractError("Expected a model name")
        self._usage = usage
        self._tools, self._model = tools, model
        self._stop = Event()
        self._gate = Lock()
        self._active_task: str | None = None
        self._http_active = self._finished = self._stop_unconfirmed = False
        declarations = [types.FunctionDeclaration(
            name=item["name"], description=item["description"],
            parameters_json_schema=item["parameters"],
        ) for item in tools.declarations()]
        self._config = types.GenerateContentConfig(
            candidate_count=1, max_output_tokens=4096,
            tools=[types.Tool(function_declarations=declarations)] if declarations else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            system_instruction=model_instruction(profile, tools_enabled=bool(declarations)),
        )
        # SDK retry'ı kapalıdır; aşağıdaki sınırlı politika hangi modelin kaç
        # kez çağrıldığını kontrol eder. HTTP timeout milisaniye cinsindedir.
        self._client = genai.Client(api_key=key, vertexai=False, http_options=types.HttpOptions(
            timeout=30_000, retry_options=types.HttpRetryOptions(attempts=1),
        ))

    def close(self) -> None:
        """Bu adaptörün sahip olduğu HTTP istemcisini kapat; core'a dokunma."""
        self._client.close()

    def stop(self) -> str | None:
        """İptali kaydet; bitişi bekleme. Dönen metin neyin beklendiğini belirtir.

        Kapı kilidi yeni araç/HTTP denemesinin kabulünü Stop ile sıralar. Devam
        eden senkron HTTP zorla kapatılmaz; sonuç gelene kadar sahibi bekler.
        """
        with self._gate:
            if self._finished:
                return None
            if not self._stop.is_set():
                self._stop.set()
                if self._active_task:
                    try:
                        self._tools.cancel(self._active_task)
                    except Exception:
                        self._stop_unconfirmed = True
            return "http_response" if self._http_active else "tool_result" if self._active_task else "turn_completion"

    def _check_stop(self) -> None:
        """İptal edilmiş tur yeni HTTP/araç işlemi başlatmamalı."""
        if self._stop.is_set():
            raise _Stopped

    def _wait_retry(self, seconds: float) -> None:
        """Geri çekilme beklemesi iptal sinyaliyle hemen uyanır."""
        self._stop.wait(seconds)

    def _stopped(self, results: list[dict]) -> dict:
        """Kabul edilmiş görevleri gözle; iptali dosya yazısının geri alınması sayma."""
        unknown = self._stop_unconfirmed
        for outcome in results:
            try:
                current = self._tools.result(outcome["task_id"])
                current["id"] = outcome["id"]
                outcome.update(current)
            except Exception:
                unknown = True
            unknown |= not TaskStatus(outcome["status"]).terminal or outcome["status"] == "unknown"
        return {**_failure("stopped", "REST response stopped. Completed actions were not undone." if not unknown else
                "REST stopped but a tool is unresolved. Reopen and check notes before retrying.", results),
                "stopped": not unknown, "unknown": unknown}

    def __enter__(self):
        """with bloğunda ağ kaynaklarının sahibini açık tut."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Başarılı turda da istisnada da SDK bağlantılarını bırak."""
        self.close()

    def run(self, text: str) -> dict:
        """Tek metin isteğini sınırlı model/araç turlarıyla işle.

        Araç başlamadan önce geçici ağ/sunucu hataları sınırlı tekrar edilir.
        Araç sonucu alındıktan sonra retry/fallback yapılmaz; sonuç korunur.
        Önceki run'ı hatadan sonra yeniden çağırmak işlem tekrarına yol açabilir;
        host önce tool_results içindeki bilinen/pending sonuçları incelemelidir.
        Bekleme timeout'u çalışan aracı öldürmez veya başarısız yapmaz.
        """
        attempts: list[str] = []
        details: list[dict] = []
        started = perf_counter()
        with self._gate:
            self._finished = False
            self._active_task = None
        try:
            report = self._run(text, attempts, details)
            with self._gate:
                # Son yanıt ile Stop yarışırsa bu kilit bitiş sınırını belirler.
                if self._stop.is_set():
                    report = self._stopped(report["tool_results"])
                self._finished = True
        finally:
            with self._gate:
                self._finished = True
        # Host/UI gerçek kullanılan modeli görebilsin; seçili ana modeli
        # alternatif modelmiş gibi kalıcı değiştirmiyoruz. Sır taşınmaz.
        report.update(model=attempts[-1] if attempts else self._model, model_attempts=attempts,
                      model_attempt_details=details, elapsed_ms=round((perf_counter() - started) * 1000))
        return report

    def _generate(self, contents: list[types.Content], results: list[dict],
                  attempts: list[str], details: list[dict]) -> types.GenerateContentResponse:
        """Yalnız araç öncesi isteği tekrar et; model imzalarını modeller arası taşıma.

        Ana modelde iki deneme, ardından alternatifte tek deneme vardır.
        Açıkça farklı model seçen host için o modelde iki deneme yapılır.
        Her run ana modelden başlar; fallback seçildiyse o turun devamı orada kalır.
        429 kota/limit ayrımı yapılmadığından burada tekrar edilmez.
        """
        models = [attempts[-1]] if results else [self._model, self._model]
        if not results and self._model == DEFAULT_MODEL:
            models.append(FALLBACK_MODEL)
        for index, model in enumerate(models):
            if index:
                self._wait_retry(2 ** (index - 1) + uniform(0, 0.25))
            with self._gate:
                self._check_stop()
                self._http_active = True
            attempts.append(model)
            started = perf_counter()
            detail: dict[str, str | int] = {"model": model, "outcome": "failed"}
            details.append(detail)
            try:
                response = self._client.models.generate_content(
                    model=model, contents=contents, config=self._config,
                )
                if self._usage is not None:
                    self._usage.add(gemini_token_count(response.usage_metadata))
                detail["outcome"] = "response"
                return response
            except (errors.APIError, httpx.TransportError, OSError) as error:
                if self._usage is not None:
                    self._usage.add(None)  # Sağlayıcı maliyet kanıtı vermedi; retry sıfır maliyet demek değildir.
                # Yalnız sınırlı teşhis alanları: payload, anahtar, yanıt metni
                # ve ham exception kaydedilmez. Süre gerçek HTTP denemesine aittir;
                # retry beklemesi ve araç süresi yalnız toplam elapsed_ms'dedir.
                if isinstance(error, errors.APIError):
                    detail.update(outcome="http_error", http_status=error.code)
                else:
                    detail["outcome"] = "timeout" if isinstance(error, httpx.TimeoutException) else "network_error"
                self._check_stop()
                transient = not isinstance(error, errors.APIError) or error.code in {408, 500, 502, 503, 504}
                if not transient or index == len(models) - 1:
                    raise
            finally:
                detail["elapsed_ms"] = round((perf_counter() - started) * 1000)
                with self._gate:
                    self._http_active = False
        raise AssertionError("Model attempt list must not be empty")

    def _run(self, text: str, attempts: list[str], details: list[dict]) -> dict:
        """Araç turunun tek yürütme yolu; retry yalnız _generate sınırındadır."""
        results: list[dict] = []
        if not isinstance(text, str) or not text.strip():
            return _failure("invalid_text", "Expected non-empty text", results)
        self._tools.begin_turn(text)
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=text)])]
        turn_id = uuid4().hex
        for round_index in range(MAX_REQUESTS):
            try:
                reply = self._generate(contents, results, attempts, details)
                self._check_stop()
            except _Stopped:
                return self._stopped(results)
            except errors.APIError as error:
                return _api_failure(error, results)
            except httpx.TimeoutException:
                return _failure("network_timeout", "Gemini request timed out; tools were not retried", results)
            except (httpx.HTTPError, OSError):
                return _failure("network_error", "Gemini connection failed; tools were not retried", results)
            except ValueError:
                return _failure("provider_protocol", "Gemini request or response was invalid", results)

            candidates = reply.candidates or []
            if len(candidates) != 1 or candidates[0].finish_reason != types.FinishReason.STOP:
                return _failure("incomplete_response", "Gemini returned no complete response", results)
            content = candidates[0].content
            if content is None or not content.parts:
                return _failure("empty_response", "Gemini returned no usable content", results)
            calls = [(index, part.function_call) for index, part in enumerate(content.parts)
                     if part.function_call is not None]
            if not calls:
                answer = "".join(part.text for part in content.parts if part.text and not part.thought)
                if not answer.strip():
                    return _failure("empty_response", "Gemini returned no answer", results)
                # Araç döngüsünün toplamını uydurma: yalnız son generation bildirimi.
                count = gemini_token_count(reply.usage_metadata)
                usage = {'usage_tokens':count} if count is not None else {}
                return {"ok": True, "text": answer, "tool_results": results, **usage}
            if round_index == MAX_REQUESTS - 1 or len(results) + len(calls) > MAX_TOOL_CALLS:
                return _failure("turn_limit", "Model/tool turn limit reached", results)

            responses = []
            for index, call in calls:
                if call.id is not None and not call.id.strip():
                    return _failure("invalid_tool_call", "Model tool call id is empty", results)
                # Bazı model biçimleri id vermez. O parça için kimlik bir kez
                # host tarafından belirlenir; sağlayıcının Content'i değiştirilmez.
                # Sağlayıcı id'sini kullanıcı turuna bağla: yeni run eski çağrı
                # sanılmasın; aynı run içindeki replay hâlâ aynı göreve gitsin.
                call_id = f"{turn_id}:{call.id}" if call.id is not None else f"local:{turn_id}:{round_index}:{index}"
                try:
                    with self._gate:
                        self._check_stop()
                        task = self._tools.submit({"id": call_id, "name": call.name,
                                                   "arguments": call.args if call.args is not None else {}})
                        self._active_task = task.task_id
                        # Beklemeden önce kaydet: Stop geldiğinde kabul edilmiş
                        # görevin kimliği ve olası yan etkisi kaybolmamalı.
                        outcome = {"id": call.id if call.id is not None else call_id, "name": call.name,
                            "task_id": task.task_id, "status": task.status.value,
                            "result": task.result.to_dict() if task.result else None}
                        results.append(outcome)
                except _Stopped:
                    return self._stopped(results)
                except NoteTargetError as error:
                    return _failure(error.code, str(error), results)
                except ContractError as error:
                    return _failure(getattr(error, "code", "invalid_tool_call"),
                                    "Model tool call was rejected", results)
                outcome.update(self._tools.result(task.task_id, timeout=TOOL_WAIT_SECONDS))
                if call.id is not None:
                    outcome["id"] = call.id  # Gemini'ye sağlayıcının özgün kimliği geri döner.
                if self._stop.is_set():
                    return self._stopped(results)
                status = TaskStatus(outcome["status"])
                if not status.terminal:
                    return _failure("task_pending", "Tool is still active; do not repeat the request", results)
                if status in (TaskStatus.UNKNOWN, TaskStatus.CANCELLED):
                    return _failure(f"tool_{status.value}", "Tool did not confirm completion; turn stopped", results)
                responses.append(types.Part(function_response=types.FunctionResponse(
                    id=call.id, name=call.name, response=outcome,
                )))
            # Content'i metne çevirip yeniden kurmak düşünme imzasını düşürür.
            contents.extend([content, types.Content(role="user", parts=responses)])
        return _failure("turn_limit", "Model/tool turn limit reached", results)
