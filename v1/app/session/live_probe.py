"""Live text/tool ​​lap: return transcript, core results and actual times.

The microphone does not turn on here; The UI's limited PCM clip or stream goes into the same session.
PCM tracks to limited UI player if audio receiver is present
transferred or discarded. If the resource is given, the same socket is maintained; independent probe its own source
closes. Executes permissioned tools through ModelTools; It does not automatically retry.
"""

import asyncio
from collections.abc import Callable
from threading import Event
from time import perf_counter

from google.genai import errors, types

from app.session.live_session import LiveConnection
from app.session.live_input import LiveInput
from app.session.gemini import GeminiUsage
from app.session.wake_word import is_wake_only
from app.core.contracts import ContractError, TaskStatus
from app.session.model_tools import ModelTools, NoteTargetError, assistant_control_request
from app.storage.credentials import CredentialError, load_gemini_key

# Don't cut off the old 25 s total time for the long response that continues to come in parts.
# Event silence and total lap limit are separate; none of them resubmit.
LIVE_TURN_SECONDS = 120
LIVE_IDLE_SECONDS = 25


async def _next_message(messages, sender):
    """If the sender gives an error, finish the same round without waiting for the incoming response/deadline."""
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
    """25 s event silence / 120 s total lap; Timeout is not a repeat permit.

    first_event_ms first content/audio, first_text_ms first transcript/text
    measures. elapsed_ms is the total including connection and closure. sound generation provider
    may consume its quota; Just because it's not playable doesn't mean it's free.
    """
    owned = connection is None
    connection = connection or LiveConnection()
    started = perf_counter()
    report: dict = {"ok": False, "completed": True, "text": "", "tool_results": [],
              "model": model, "model_attempts": [model], "mode": "live_latency_test",
              "first_event_ms": None, "first_text_ms": None, "audio_bytes_discarded": 0,
              "audio_bytes_forwarded": 0, "audio_error": None}
    # These numbers voice/text reserve the place to wait 25 s without saving the content.
    report.update(received_events=0, last_received_ms=None, input_final_ms=None)
    transcript: list[str] = []
    plain: list[str] = []
    text_length = 0
    bound_tools = None
    sender = None
    streaming = isinstance(audio_input, LiveInput)
    sequence = 0
    usage = GeminiUsage()

    async def publish(role: str, value: str):
        """Forward accumulated text to identified recipient; Screen error will not distort the tool result."""
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
                    # Sending and receiving are on the same socket/event loop owner.
                    # Sender error is also checked before each received event;
                    # There is no silently losing sound and continuing to start the tool.
                    sender = asyncio.create_task(audio_input.send(session))
                elif audio_input is None:
                    await session.send_realtime_input(text=text)
                else:
                    # A single, clearly finished speech: guessing intent from silence
                    # It is not done. Send up to 15 seconds on the same socket/Stop line.
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
                    # Final provider notice: we do not collect; It is not the sum of quota/session.
                    if message.usage_metadata is not None:
                        usage.observe_live(message.usage_metadata)
                    messages += 1
                    report['received_events'] = messages
                    report['last_received_ms'] = round((perf_counter() - started) * 1000)
                    if message.go_away is not None:
                        # GoAway is a preliminary notification; Repeat ongoing message
                        # sending Wait for the real ending in Duration/deadline.
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
                    # Only adjusted address is not a task. First definitive speech
                    # Close on offer/tool; expect model greetings/tool.
                    # Same address definition as KWS; The duty statement or intent is not interpreted.
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
                        # The finished user transcript immediately closes the old PCM acceptance;
                        # answer/tool can continue. The thought piece is not the ending. The new barge-in remains in the separate resource.
                        audio_input.close()
                        if sender:
                            sender.cancel()
                            await asyncio.gather(sender, return_exceptions=True)
                            sender = None
                        # Open event if local resource is closed in final transcript
                        # close it too. audio_stream_end is not when auto VAD is off,
                        # activity_end must be sent from the same socket owner.
                        if audio_input.end_sent_at is None:
                            if stop_event and stop_event.is_set():
                                raise asyncio.CancelledError
                            await session.send_realtime_input(activity_end=types.ActivityEnd())
                            audio_input.end_sent_at = perf_counter()
                    if message.tool_call:
                        usage.live_boundary()
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
                                # Correct the model's voice command before the transcript arrives.
                                # No tool is operated assuming it understands.
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
                            # Put the accepted task in the report before waiting:
                            # If there is a timeout, any transaction that may have occurred will not be lost.
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
                                # Track and turn size limited; transport confirmation
                                # It is not proof that sound is coming from the physical speaker.
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
                    # turn_complete ending alone in extended thinking
                    # is not; If the provider reported IDLE, it is complete.
                    status = content.interaction_status
                    finished = status == types.InteractionStatus.IDLE if status and status != types.InteractionStatus.INTERACTION_STATUS_UNSPECIFIED else bool(content.turn_complete)
                    if report["tool_results"] and "extended-thinking" in model:
                        finished = status == types.InteractionStatus.IDLE
                    if finished and not message.tool_call:
                        answer = "".join(transcript or plain)
                        if answer.strip():
                            report.update(ok=True, text=answer)
                            # The actual model response is complete. UI same audio queue
                            # After unloading, the host may request a sleep transition;
                            # We do not cut the transcript early and fabricate local approval.
                            report.update(assistant_control_request(report, previous_tasks))
                            return report
                        break
                report.update(code="live_incomplete", error="Live returned no complete text transcript.")
    except asyncio.CancelledError:
        # Hacking the network coroutine does not kill the running Python tool. only this
        # Cancel the accepted missions of the turn and read the real results.
        # Previously verified file writings are successfully preserved.
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
            # If the Core result is unreadable, keep the previous evidence; Don't assume it's cancelled.
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
        # The WebSocket closure may contain the free key reason/text; alone
        # Show numeric standard code. The raw exception is never carried to the UI.
        code = getattr(getattr(error, "rcvd", None), "code", None)
        if type(code) is int and code in {1000, 1001, 1006, 1008, 1011, 1012, 1013}:
            report["websocket_code"] = code
        report.update(code="live_connection_error", error="Live connection failed. Check the selected conversational model and API access.")
        if connection.draining:
            report.update(code="live_go_away", error="Live disconnected before the turn completed; this message was not retried.")
    finally:
        usage.finish_live(report)
        # The retrieved text of the Interrupted turn also remains; does not translate into success.
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
