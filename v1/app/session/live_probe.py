"""Live metin/araç turu: transkripti, core sonuçlarını ve gerçek süreleri döndür.

Mikrofon burada açılmaz; UI'ın sınırlı PCM klibi veya akışı aynı oturuma gider.
Ses alıcısı varsa PCM parçaları sınırlı UI oynatıcısına
aktarılır, yoksa atılır. Kaynak verilirse aynı socket korunur; bağımsız probe kendi kaynağını
kapatır. İzinli araçları ModelTools üzerinden yürütür; otomatik retry yapmaz.
"""

import asyncio
from collections.abc import Callable
from threading import Event
from time import perf_counter

from google.genai import errors, types

from app.session.live_session import LiveConnection
from app.session.live_input import LiveInput
from app.session.wake_word import is_wake_only
from app.core.contracts import ContractError, TaskStatus
from app.session.model_tools import ModelTools, NoteTargetError, assistant_control_request
from app.storage.credentials import CredentialError, load_gemini_key

# Parçaları gelmeye devam eden uzun yanıt eski 25 s toplam sürede kesilmesin.
# Olay sessizliği ve toplam tur sınırı ayrıdır; hiçbiri tekrar gönderim yapmaz.
LIVE_TURN_SECONDS = 120
LIVE_IDLE_SECONDS = 25


async def _next_message(messages, sender):
    """Gönderici hata verirse gelen yanıtı/deadline'ı beklemeden aynı turu bitir."""
    receiving = asyncio.create_task(anext(messages))
    try:
        if sender is not None:
            await asyncio.wait((receiving, sender), return_when=asyncio.FIRST_COMPLETED)
            if sender.done():
                sender.result()
        return await receiving
    finally:
        receiving.cancel()
        await asyncio.gather(receiving, return_exceptions=True)


async def probe_live_text(text: str, model: str, *, connection: LiveConnection | None = None,
                          tools: ModelTools | None = None, stop_event: Event | None = None,
                          audio_sink: Callable[[bytes, str], bool] | None = None,
                          transcript_sink: Callable[[str, str, int], bool] | None = None,
                          audio_input: bytes | LiveInput | None = None, profile: dict | None = None,
                          context: str = '', voice: str | None = None) -> dict:
    """25 s olay sessizliği / 120 s toplam tur; süre aşımı tekrar izni değildir.

    first_event_ms ilk içerik/ses parçasını, first_text_ms ilk transkript/metni
    ölçer. elapsed_ms bağlantı ve kapanış dahil toplamdır. Ses üretilmesi sağlayıcı
    kotası tüketebilir; oynatılmaması ücretsiz olduğu anlamına gelmez.
    """
    owned = connection is None
    connection = connection or LiveConnection()
    started = perf_counter()
    report: dict = {"ok": False, "completed": True, "text": "", "tool_results": [],
              "model": model, "model_attempts": [model], "mode": "live_latency_test",
              "first_event_ms": None, "first_text_ms": None, "audio_bytes_discarded": 0,
              "audio_bytes_forwarded": 0, "audio_error": None}
    # Bu sayılar ses/metin içeriği kaydetmeden 25 s beklemenin yerini ayırır.
    report.update(received_events=0, last_received_ms=None, input_final_ms=None)
    transcript: list[str] = []
    plain: list[str] = []
    text_length = 0
    bound_tools = None
    sender = None
    streaming = isinstance(audio_input, LiveInput)
    sequence = 0

    async def publish(role: str, value: str):
        """Birikimli metni kimlikli alıcıya ilet; ekran hatası araç sonucunu bozmaz."""
        nonlocal sequence
        sequence += 1
        if transcript_sink:
            try:
                if await asyncio.to_thread(transcript_sink, role, value, sequence) is not True:
                    report['transcript_error'] = 'transcript_delivery_failed'
            except Exception:
                report['transcript_error'] = 'transcript_delivery_failed'
    try:
        if audio_input is not None and not streaming and (type(audio_input) is not bytes or not 3200 <= len(audio_input) <= 480000 or len(audio_input) % 2):
            raise ContractError("Invalid microphone PCM")
        if stop_event and stop_event.is_set():
            raise asyncio.CancelledError
        key = load_gemini_key()
        if not key:
            report.update(code="missing_api_key", error="Save a Gemini key before the Live test.")
            return report
        async with asyncio.timeout(LIVE_TURN_SECONDS):
            async with connection.open(model, key, tools, audio_input='stream' if streaming else audio_input is not None,
                                       profile=profile, context=context, voice=voice) as session:
                report['memory_restored'] = connection.context_restored
                report["session_reused"] = connection.reused
                report["session_resumed"] = connection.resumed
                report["logical_session_id"] = connection.logical_id
                report["context_reset_reason"] = connection.reset_reason
                if not owned:
                    report["mode"] = "live_session"
                bound_tools = connection.tools
                previous_tasks = frozenset(connection.calls.values())
                if bound_tools:
                    bound_tools.begin_turn(text)
                report["tools_enabled"] = bound_tools is not None
                report["connect_ms"] = round((perf_counter() - started) * 1000)
                if isinstance(audio_input, LiveInput):
                    # Gönderme ve alma aynı socket/event loop sahibindedir.
                    # Alınan her olaydan önce gönderici hatası da denetlenir;
                    # sessizce ses kaybedip araç çalıştırmaya devam etmek yoktur.
                    sender = asyncio.create_task(audio_input.send(session))
                elif audio_input is None:
                    await session.send_realtime_input(text=text)
                else:
                    # Tek, açıkça bitirilmiş konuşma: sessizlikten niyet tahmin
                    # edilmez. Aynı socket/Stop hattında en çok 15 saniye gönder.
                    await session.send_realtime_input(activity_start=types.ActivityStart())
                    for offset in range(0, len(audio_input), 3200):
                        if stop_event and stop_event.is_set():
                            raise asyncio.CancelledError
                        await session.send_realtime_input(audio=types.Blob(
                            data=audio_input[offset:offset + 3200], mime_type="audio/pcm;rate=16000"))
                    await session.send_realtime_input(activity_end=types.ActivityEnd())
                messages = 0
                incoming = session.receive().__aiter__()
                while True:
                    try:
                        idle = asyncio.timeout(LIVE_IDLE_SECONDS)
                        try:
                            async with idle:
                                message = await _next_message(incoming, sender)
                        except TimeoutError:
                            if not idle.expired():
                                raise
                            report.update(code='live_idle_timeout', timeout_seconds=LIVE_IDLE_SECONDS,
                                error='Live event wait timed out. This message was not retried; check existing tool results.')
                            report['wait_phase'] = ('after_input_final' if report['input_final_ms'] is not None
                                else 'before_input_final' if streaming else 'provider_reply')
                            return report
                    except StopAsyncIteration:
                        break
                    messages += 1
                    report['received_events'] = messages
                    report['last_received_ms'] = round((perf_counter() - started) * 1000)
                    if message.go_away is not None:
                        # GoAway bir ön bildirimdir; devam eden mesajı tekrar
                        # gönderme. Süre/deadline içinde gerçek bitişi bekle.
                        connection.draining = True
                        report["goaway_received"] = True
                    if messages > 2000:
                        report.update(code="live_protocol", error="Live event limit reached.")
                        return report
                    if message.tool_call_cancellation and bound_tools:
                        for call_id in message.tool_call_cancellation.ids or []:
                            if call_id in connection.calls:
                                bound_tools.cancel(connection.calls[call_id])
                        report.update(code="tool_cancelled", error="Server cancelled tool calls. Existing completed actions were not undone.")
                        return report
                    content = message.server_content
                    if content and content.input_transcription and content.input_transcription.finished is True:
                        report['input_final_ms'] = round((perf_counter() - started) * 1000)
                    if audio_input is not None and content and content.input_transcription and content.input_transcription.text:
                        report["input_text"] = report.get("input_text", "") + content.input_transcription.text
                        if len(report["input_text"]) > 20000:
                            raise ContractError("Microphone transcript limit exceeded")
                        await publish('u', report['input_text'])
                        if bound_tools:
                            bound_tools.observe_input(report['input_text'])
                    # Yalnız ayarlı hitap bir görev değildir. İlk kesin konuşma
                    # bitişinde/araç teklifinde kapat; modelden selam/araç bekleme.
                    # KWS ile aynı hitap tanımı; görev cümlesi veya niyeti yorumlanmaz.
                    wake_only = (audio_input is not None and not report['tool_results'] and
                        is_wake_only(report.get('input_text', ''), (profile or {}).get('pWake', 'Vex')))
                    if wake_only and (message.tool_call or content and (content.turn_complete or
                            content.input_transcription and content.input_transcription.finished)):
                        await connection.reset('wake_only')
                        transcript.clear(); plain.clear()
                        report.update(ok=True, wake_only=True)
                        return report
                    if isinstance(audio_input, LiveInput) and (message.tool_call or content and
                            (content.input_transcription and content.input_transcription.finished is True or
                             content.output_transcription and content.output_transcription.text or content.turn_complete or
                             any(not part.thought and (part.text or part.inline_data and part.inline_data.data)
                                 for part in ((content.model_turn.parts or []) if content.model_turn else [])))):
                        # Bitmiş kullanıcı transkripti eski PCM kabulünü hemen kapatır;
                        # yanıt/araç devam edebilir. Düşünce parçası bitiş değildir. Yeni barge-in ayrı kaynakta kalır.
                        audio_input.close()
                        if sender:
                            sender.cancel()
                            await asyncio.gather(sender, return_exceptions=True)
                            sender = None
                        # Final transkriptte yerel kaynak kapanırsa açık etkinliği
                        # de kapat. Otomatik VAD kapalıyken audio_stream_end değil,
                        # activity_end aynı socket sahibinden gönderilmelidir.
                        if audio_input.end_sent_at is None:
                            if stop_event and stop_event.is_set():
                                raise asyncio.CancelledError
                            await session.send_realtime_input(activity_end=types.ActivityEnd())
                            audio_input.end_sent_at = perf_counter()
                    if message.tool_call:
                        calls = message.tool_call.function_calls or []
                        if not bound_tools or not calls or len(report["tool_results"]) + len(calls) > 8:
                            report.update(code="live_protocol", error="Unexpected tool call or tool limit reached.")
                            return report
                        for call in calls:
                            if stop_event and stop_event.is_set():
                                raise asyncio.CancelledError
                            if not isinstance(call.id, str) or not call.id.strip():
                                report.update(code="invalid_tool_call", error="Live tool call requires a non-empty id.")
                                return report
                            try:
                                # Transkript gelmeden modelin ses komutunu doğru
                                # anladığı varsayılarak hiçbir araç çalıştırılmaz.
                                if audio_input is not None and not report.get("input_text", "").strip():
                                    report.update(code="voice_transcript_required", error="No speech transcript was confirmed; no tool was started.")
                                    return report
                                task = bound_tools.submit({"id": call.id, "name": call.name,
                                    "arguments": call.args if call.args is not None else {}})
                            except NoteTargetError as error:
                                report.update(code=error.code, error=str(error))
                                return report
                            except ContractError as error:
                                report.update(code=getattr(error, "code", "invalid_tool_call"), error="Live tool call was rejected.")
                                return report
                            connection.calls[call.id] = task.task_id
                            # Kabul edilen görevi beklemeden önce rapora koy:
                            # timeout olursa gerçekleşmiş olabilecek işlem kaybolmaz.
                            outcome = bound_tools.result(task.task_id)
                            report["tool_results"].append(outcome)
                            final = await asyncio.to_thread(bound_tools.result, task.task_id, timeout=5)
                            outcome.clear()
                            outcome.update(final)
                            status = TaskStatus(outcome["status"])
                            if not status.terminal:
                                report.update(code="task_pending", unknown=True, error="Tool is still active. Do not resend; reopen and check notes.")
                                return report
                            if status in {TaskStatus.UNKNOWN, TaskStatus.CANCELLED}:
                                report.update(code="tool_" + status.value, unknown=status == TaskStatus.UNKNOWN,
                                    error="Tool did not confirm completion; Live turn stopped.")
                                return report
                            await session.send_tool_response(function_responses=[types.FunctionResponse(
                                id=call.id, name=call.name, response=outcome)])
                    content = message.server_content
                    if not content:
                        continue
                    pieces = []
                    if content.output_transcription and content.output_transcription.text:
                        pieces.append(content.output_transcription.text)
                        transcript.append(content.output_transcription.text)
                    for part in (content.model_turn.parts or []) if content.model_turn else []:
                        if part.text and not part.thought:
                            pieces.append(part.text)
                            plain.append(part.text)
                    if pieces:
                        text_length += sum(len(piece) for piece in pieces)
                        if report["first_text_ms"] is None:
                            report["first_text_ms"] = round((perf_counter() - started) * 1000)
                        if report["first_event_ms"] is None:
                            report["first_event_ms"] = report["first_text_ms"]
                    if text_length > 32000:
                        report.update(code="live_response_limit", error="Live test response exceeded the text limit.")
                        return report
                    if pieces:
                        report['text'] = ''.join(transcript or plain)
                        await publish('j', report['text'])
                    if content.interrupted:
                        report.update(code='live_interrupted', error='Live response was interrupted; check existing tool results before retrying.')
                        return report
                    for part in (content.model_turn.parts or []) if content.model_turn else []:
                        if part.inline_data and part.inline_data.data:
                            data, mime = part.inline_data.data, part.inline_data.mime_type
                            if audio_sink and not report["audio_error"]:
                                # Parça ve tur boyutu sınırlı; taşıma onayı
                                # fiziksel hoparlörden ses geldiğinin kanıtı değildir.
                                if mime != "audio/pcm;rate=24000" or len(data) % 2 or len(data) > 131072:
                                    report["audio_error"] = "invalid_pcm"
                                elif report["audio_bytes_forwarded"] + len(data) > 2880000:
                                    report["audio_error"] = "audio_limit"
                                else:
                                    try:
                                        if stop_event and stop_event.is_set():
                                            raise asyncio.CancelledError
                                        if await asyncio.to_thread(audio_sink, data, mime) is True:
                                            report["audio_bytes_forwarded"] += len(data)
                                        else:
                                            report["audio_error"] = "playback_unavailable"
                                    except Exception:
                                        report["audio_error"] = "playback_unavailable"
                            if not audio_sink or report["audio_error"]:
                                report["audio_bytes_discarded"] += len(data)
                            if report["first_event_ms"] is None:
                                report["first_event_ms"] = round((perf_counter() - started) * 1000)
                    # Extended thinking'de turn_complete tek başına bitiş
                    # değildir; sağlayıcı IDLE bildirdiyse tamamlanmıştır.
                    status = content.interaction_status
                    finished = status == types.InteractionStatus.IDLE if status and status != types.InteractionStatus.INTERACTION_STATUS_UNSPECIFIED else bool(content.turn_complete)
                    if report["tool_results"] and "extended-thinking" in model:
                        finished = status == types.InteractionStatus.IDLE
                    if finished and not message.tool_call:
                        answer = "".join(transcript or plain)
                        if answer.strip():
                            report.update(ok=True, text=answer)
                            # Gerçek model yanıtı tamamlandı. UI aynı ses kuyruğunu
                            # boşalttıktan sonra host uyku geçişini isteyebilir;
                            # transkripti erken kesip yerel onay uydurmayız.
                            report.update(assistant_control_request(report, previous_tasks))
                            return report
                        break
                report.update(code="live_incomplete", error="Live returned no complete text transcript.")
    except asyncio.CancelledError:
        # Ağ coroutine'ini kesmek çalışan Python aracını öldürmez. Yalnız bu
        # turun kabul edilmiş görevlerine iptal verip gerçek sonuçlarını oku.
        # Daha önce doğrulanmış dosya yazıları başarılı olarak korunur.
        unresolved = False
        try:
            if bound_tools:
                for outcome in report["tool_results"]:
                    bound_tools.cancel(outcome["task_id"])
                for outcome in report["tool_results"]:
                    final = await asyncio.to_thread(bound_tools.result, outcome["task_id"], timeout=5)
                    outcome.clear()
                    outcome.update(final)
        except Exception:
            # Core sonucu okunamazsa önceki kanıtı sakla; iptal olmuş varsayma.
            unresolved = True
        unresolved |= any(not TaskStatus(item["status"]).terminal or item["status"] == "unknown"
                          for item in report["tool_results"])
        report.update(code="stopped", stopped=not unresolved, unknown=unresolved,
            error="Live response stopped. Completed actions were not undone." if not unresolved else
                  "Model stopped but a tool is unresolved. Reopen and check notes before retrying.")
    except TimeoutError:
        report.update(code="live_timeout", timeout_seconds=LIVE_TURN_SECONDS,
            error="Live turn time limit reached. This message was not retried; check existing tool results.")
    except CredentialError:
        report.update(code="missing_api_key", error="Gemini key is missing or unavailable. Save it in Settings.")
    except ContractError:
        report.update(code="live_contract_error", error="Live data failed validation; check existing tool results before retrying.")
    except errors.APIError as error:
        report.update(code="live_api_error", error="Live API rejected the turn; completed tool results were preserved.")
        if 100 <= error.code <= 599:
            report["http_status"] = error.code
        elif error.code in {1000, 1001, 1006, 1008, 1011, 1012, 1013}:
            report["websocket_code"] = error.code
    except Exception as error:
        # WebSocket kapanışının serbest reason/metni anahtar içerebilir; yalnız
        # sayısal standart kodu göster. Ham exception asla UI'a taşınmaz.
        code = getattr(getattr(error, "rcvd", None), "code", None)
        if type(code) is int and code in {1000, 1001, 1006, 1008, 1011, 1012, 1013}:
            report["websocket_code"] = code
        report.update(code="live_connection_error", error="Live connection failed. Check the selected conversational model and API access.")
        if connection.draining:
            report.update(code="live_go_away", error="Live disconnected before the turn completed; this message was not retried.")
    finally:
        # Başarısız/kesilen turun alınmış metni de kalır; başarıya çevrilmez.
        report['text'] = ''.join(transcript or plain)[:32000]
        if isinstance(audio_input, LiveInput):
            report['input_boundary'] = 'manual_activity'
            audio_input.close()
        if sender:
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)
        if isinstance(audio_input, LiveInput):
            report['input_sent_packets'] = audio_input.sent_packets
            report['input_first_sent_ms'] = (round((audio_input.first_sent_at - started) * 1000)
                if audio_input.first_sent_at is not None else None)
            report['input_end_sent_ms'] = (round((audio_input.end_sent_at - started) * 1000)
                if audio_input.end_sent_at is not None else None)
        if any(item["status"] in {"queued", "running", "cancel_requested", "unknown"} for item in report["tool_results"]):
            report["unknown"] = True
        if owned or not report["ok"]:
            await connection.reset("stopped" if report.get("code") == "stopped" else "previous_turn_failed")
        report["elapsed_ms"] = round((perf_counter() - started) * 1000)
    return report
