"""Real Windows/WebView2 acceptance control: python tests/native_smoke.py.

not included in pytest; It requires a real native engine. The main process is a temporary
creates TASKVEX_HOME; open/save, registration-import-export, cancellation and setting-error
and note CRUD/identity runs store/text scenarios in eleven separate processes. Windows are hidden. User
data is not used; At the end of the test, the temporary profile/data directory is cleared.
"""

import argparse
import faulthandler
import json
import os
import socket
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Event
import time
import traceback

# When the script is run directly from tests/ the app package should also be present.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from native_scenarios import (
    check_native_note_ui, check_native_note_crud, check_native_note_batches, check_native_clocks, check_native_shutdown_request, check_local_sleep, check_wake_recovery, check_real_local_wake, check_native_media, check_native_screen
)


def child(home: Path, phase: str, debug: bool = False) -> None:
    """Run main() installation in production with real native engine."""
    os.environ["TASKVEX_HOME"] = str(home)
    faulthandler.dump_traceback_later(30)
    import webview
    # Connecting to server 42001 of open user application. same test
    # Origin must remain constant when the profile is reopened.
    home.mkdir(parents=True, exist_ok=True)
    port_file = home / 'test-http-port'
    if not port_file.exists():
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port_file.write_text(str(listener.getsockname()[1]), encoding='ascii')
    webview.settings['DEFAULT_HTTP_PORT'] = int(port_file.read_text(encoding='ascii'))
    from app.tools.local import telemetry as telemetry_module
    telemetry_module.WindowsGpu=lambda:lambda:{'gpu_source':'windows-pdh','gpu_status':'ok',
        'gpu_devices':[{'id':'synthetic-adapter','utilization_percent':0}]}
    from app.tools.local import network as network_module
    network_module.read_interfaces=lambda:[{'id':'synthetic','up':True,'kind':'wifi','rx_bytes':100,'tx_bytes':50}]
    network_module.read_gateway=lambda _:1
    network_module.ping_gateway=lambda _:{'network_ping_ms':0,'network_ping_status':'ok'}
    network_module.wifi_signal=lambda _:{'network_wifi_signal':75,'network_wifi_status':'ok'}
    from app.tools.local import media as media_module
    media_module._read_windows=lambda manager=None:{'status':'available','title':'Native synthetic track','artist':'Synthetic artist','state':'paused'}
    from app.tools.services import weather as weather_module
    def synthetic_weather(kind,params):
        from datetime import datetime, timezone
        if kind=='locations':return {'results':[{'name':'Native Test City','country':'Test Country','latitude':41.12,'longitude':29.99}]}
        return {'utc_offset_seconds':0,'current_units':{'temperature_2m':'°C','apparent_temperature':'°C',
            'relative_humidity_2m':'%','wind_speed_10m':'km/h'},'current':{'time':datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            'temperature_2m':0,'apparent_temperature':-2,'relative_humidity_2m':0,'wind_speed_10m':0,'weather_code':0}}
    weather_module._request_json=synthetic_weather
    from app.main import main
    from app.storage.json_store import StoreError

    captured, outcome, launches = {}, {}, []
    key_query_started, release_key_query = Event(), Event()
    original_create, original_start = webview.create_window, webview.start
    text_started, release_text = Event(), Event()
    rest_stop_started, release_rest_stop = Event(), Event()
    text_requests = []
    wake_state = {'packets':0, 'detect':False, 'instances':0}
    speech_state = {'requests': [], 'fail': False, 'block': False, 'started': Event(), 'release': Event()}
    text_payloads = []  # It only checks the SDK instruction of the temporary test profile.
    if phase != 'chat':
        # Automatic catalog loading is normal startup; keep real accounts and network out of this test.
        from app.bridge import webview_bridge as catalog_bridge
        catalog_bridge.load_live_catalog = lambda: {'ok':True,'completed':True,'models':[]}
    catalog_ready = Event()
    live_state: dict = {"opened": 0, "closed": False, "sent": [], "waiting": Event(), "stall": False,
                        "resumed": False}
    if phase == "chat":
        # Real SDK/core/native DOM; only HTTP transport is synthetic.
        # The production key is not read and no requests are sent to the external network.
        import httpx
        from app.bridge import webview_bridge as bridge_module
        class SyntheticWake:
            """Only the detection limit is fake; actual PCM/bridge/Live cycle is attempted."""
            def __init__(self, word, sensitivity=50):
                wake_state['instances'] += 1
                self.id = 'native-local-wake-' + str(wake_state['instances'])
                self.sequence = 0
            def feed(self, sequence, pcm):
                assert sequence == self.sequence and len(pcm) == 3200
                self.sequence += 1
                wake_state['packets'] += 1
                return wake_state['detect'] and any(pcm)
        bridge_module.WakeWord = SyntheticWake
        from app.session import gemini
        from contextlib import asynccontextmanager
        from google.genai import live

        def audio_reply(text, samples=2400):
            """Give silent PCM to true Web Audio; Claiming physical voice acceptance."""
            from base64 import b64encode
            return {"serverContent": {"modelTurn": {"role": "model", "parts": [{"inlineData": {
                "data": b64encode(b'\x00\x00' * samples).decode(), "mimeType": "audio/pcm;rate=24000"}}]},
                "outputTranscription": {"text": text}, "turnComplete": True},
                "usageMetadata":{"totalTokenCount":10}}

        def crud_plan(text):
            """Just select the ID in the real repository from the synthetic user command.

            Model imitation is only at the limit of carrying; It does not change the record.
            List/transaction/last response generation goes through ModelTools and TaskManager.
            """
            from app.storage.json_store import JsonStore
            from app.tools.local.notes import notes_snapshot
            if text.startswith('Native BULK '):
                data = JsonStore(home / 'notes.json').read()
                assert data is not None
                saved = data['notes']
                latest = text in ('Native BULK latest', 'Native BULK latest_done')
                selected = sorted(saved, key=lambda n:n.get('created_at') or '', reverse=True)[:2] if latest else saved
                return [('notes.select', {'kind':'latest','count':2,'cardinality':'many'} if latest else
                    {'kind':'all','cardinality':'many'}), ('notes.complete_many' if text.endswith(('_done','_reopen')) else 'notes.delete_many', {
                        'ids':[n['id'] for n in selected], 'expected_snapshot':notes_snapshot(saved),
                        **({'done':not text.endswith('_reopen')} if text.endswith(('_done','_reopen')) else {})})]
            verb, target = text.removeprefix("Native CRUD ").split(": ", 1)
            target = target.split(" | ", 1)[0]
            snapshot = JsonStore(home / "notes.json").read()
            assert snapshot is not None
            saved = snapshot["notes"]
            matches = [note for note in saved if note["text"] == target]
            assert len(matches) == 1
            args = {"id": matches[0]["id"], "expected_snapshot": notes_snapshot(saved)}
            if verb == "done":
                args["done"] = True
            elif verb == "edit":
                args["text"] = target + " edited"
            selector = ({'kind':'contains','text':'synthetic','cardinality':'one'} if verb == 'done'
                else {'kind':'latest','count':1,'cardinality':'one'})
            return [('notes.select', selector), ('notes.delete' if verb == 'delete' else 'notes.update', args)]

        def clock_plan(text):
            """Synthetic provider fixture only; production is not a natural language parser."""
            _, _, mode, action = text.split()
            if action in ('watch', 'timer1', 'timer2'):
                args={'kind':'stopwatch' if action=='watch' else 'timer', 'start':True, 'label':mode+' '+action}
                if action!='watch':args['duration_seconds']=120 if action=='timer1' else 180
                return [('clocks.create',args)]
            target='timer1' if action=='pause_timer1' else 'watch'
            clock=next(c for c in captured['api']._clocks.snapshot()['clocks'] if c['label']==mode+' '+target)
            return [('clocks.list',{}),('clocks.control',{'id':clock['id'],'action':'pause' if action=='pause_timer1' else 'reset'})]

        @asynccontextmanager
        async def live_socket(*args, **kwargs):
            live_state["opened"] += 1
            live_state.update(closed=False, stall=False)
            frames = [{"setupComplete": {}}]
            turns = 0
            remembered_name = None
            class Socket:
                async def send(self, value):
                    nonlocal turns, remembered_name
                    message = json.loads(value)
                    live_state["sent"].append(message)
                    if 'client_content' in message:
                        assert message['client_content']['turnComplete'] is False
                        for turn in message['client_content']['turns']:
                            assert turn['role'] == 'model'
                            for part in turn['parts']:
                                history = json.loads(part['text'].split('Historical JSON:\n', 1)[1])
                                if any(row['user'] == 'Native temporary name is Ada' for row in history):
                                    remembered_name = 'Ada'
                        return
                    if 'setup' in message:
                        self.setup_tools=message['setup'].get('tools',[])
                    if "setup" in message and live_state["opened"] == 2:
                        assert message["setup"]["sessionResumption"]["handle"] == "NATIVE_SYNTHETIC_RESUME_HANDLE"
                        live_state["resumed"] = True
                    if "realtime_input" in message:
                        incoming = message['realtime_input']
                        if incoming.get('audioStreamEnd'):
                            raise AssertionError('Manual VAD must use activityEnd, not audioStreamEnd')
                        if 'activityEnd' in incoming:
                            live_state['input_ended'] = live_state.get('input_ended', 0) + 1
                            if live_state.get('hold_microphone_reply'):
                                # Thinking view for a short period of time
                                # Attach it to the open test barrier, not to luck catch.
                                while live_state.get('hold_status_reply'):
                                    import asyncio
                                    await asyncio.sleep(.001)
                                frames.append(audio_reply('Native microphone Off answer'))
                            elif not getattr(self, 'media_answered', False):
                                frames.append({'serverContent':{'inputTranscription':{'text':'Native microphone hello'}}})
                                frames.append(audio_reply('Native microphone answer'))
                            self.media_answered = True
                            return
                        if 'audio' in incoming:
                            # The SDK's wire format is URL-safe base64;
                            # The standard decoder may corrupt '-'/'_' instances.
                            from base64 import urlsafe_b64decode
                            if live_state.get('hold_microphone_reply'):
                                if any(urlsafe_b64decode(incoming['audio']['data'])):
                                    live_state['voice_seen'] = True
                                    live_state['quiet_packets'] = 0
                                elif live_state.get('voice_seen'):
                                    live_state['quiet_packets'] = live_state.get('quiet_packets', 0) + 1
                                    if live_state['quiet_packets'] == 15:
                                        frames.append(audio_reply('Native status reply', 12000))
                                return
                            if any(urlsafe_b64decode(incoming['audio']['data'])) and not getattr(self, 'media_answered', False):
                                frames.append({'serverContent':{'inputTranscription':{'text':'Native microphone hello'}}})
                                frames.append(audio_reply('Native microphone answer'))
                                self.media_answered = True
                            return
                        if 'activityStart' in incoming:
                            self.media_answered = False
                            return
                        text = message["realtime_input"].get("text", "")
                        # Only the synthetic provider's predetermined tool
                        # selection; There is no sentence pattern or intent parser in production.
                        if text.startswith('Host event: the following timer has actually finished.'):
                            assert not self.setup_tools
                            live_state['timer_announcements']=live_state.get('timer_announcements',0)+1
                            frames.append(audio_reply('Native personalized timer completion'))
                            return
                        if text.startswith('Native CLOCK '):
                            frames.extend({'toolCall':{'functionCalls':[{'id':'clock-'+text+'-'+str(i),'name':name,'args':args}]}}
                                for i,(name,args) in enumerate(clock_plan(text)))
                            frames.append({'serverContent':{'outputTranscription':{'text':text+' confirmed'},'turnComplete':True}})
                            return
                        if text.startswith('Native SHUTDOWN '):
                            live_state['shutdown_calls'] = live_state.get('shutdown_calls', 0) + 1
                            frames.append({'toolCall': {'functionCalls': [{'id': 'shutdown-'+str(live_state['shutdown_calls']),
                                'name': 'assistant.request_shutdown', 'args': {}}]}})
                            return
                        mode = {'Please enter sleep mode.': 'once',
                            'Enter sleep mode permanently': 'persistent',
                            'Disable persistent sleep mode': 'off'}.get(text)
                        if mode:
                            live_state['sleep_requests'] = live_state.get('sleep_requests', 0) + 1
                            frames.append({'toolCall': {'functionCalls': [{'id': 'native-sleep-' + str(live_state['sleep_requests']),
                                'name': 'assistant.request_sleep_mode', 'args': {'mode': mode}}]}})
                            return
                        if text == 'Native server interruption':
                            frames.append({'serverContent':{'outputTranscription':{'text':'Native interrupted reply'}, 'interrupted':True}})
                            return
                        if text == 'Native temporary name is Ada':
                            remembered_name = 'Ada'
                            frames.append(audio_reply('Native temporary name acknowledged'))
                            return
                        if text == 'Native approve memory':
                            frames.append({'toolCall':{'functionCalls':[{'id':'native-review-read','name':'memory.read','args':{}}]}})
                            return
                        if text in ('Native self report Ada','Native self report Beta','Native self report Gamma','Native self report Delta'):
                            from app.tools.local.personal_memory import memory_snapshot
                            from app.storage.json_store import JsonStore
                            profile = (JsonStore(home / 'settings.json').read() or {}).get('prof', {})
                            for name,args,call_id in (
                                ('memory.read',{},'read-'+text),
                                ('memory.propose',{'text':'User name '+text.split()[-1], 'source_quote':'Paraphrased source, not actual user input',
                                    'expected_snapshot':memory_snapshot(profile)},'propose-'+text),
                            ):
                                frames.append({'toolCall':{'functionCalls':[{'id':call_id,'name':name,'args':args}]}})
                            frames.append(audio_reply('Native memory suggestion ready'))
                            return
                        if text == 'Native remember job':
                            from app.tools.local.personal_memory import memory_snapshot
                            from app.storage.json_store import JsonStore
                            profile = (JsonStore(home / 'settings.json').read() or {}).get('prof', {})
                            for name, args, call_id in (
                                ('memory.read', {}, 'native-memory-read'),
                                ('memory.patch', {'action':'append', 'text':'Native saved job',
                                    'expected_snapshot':memory_snapshot(profile)}, 'native-memory-patch'),
                            ):
                                frames.append({'toolCall':{'functionCalls':[{'id':call_id, 'name':name, 'args':args}]}})
                            frames.append(audio_reply('Native job remembered'))
                            return
                        if text == 'Native memory ask':
                            frames.append(audio_reply('Native remembered name: ' + (remembered_name or 'unknown')))
                            return
                        if text == 'Native profile probe':
                            frames.append(audio_reply('Native profile probe Live'))
                            return
                        if text == 'Native microphone rejected note':
                            # The non-existent goal should be rejected; registration/permission line
                            # is the production code. Model error does not turn the microphone Off.
                            frames.append({'toolCall':{'functionCalls':[{'id':'missing-note-call','name':'notes.delete',
                                'args':{'id':'missing-synthetic-note'}}]}})
                            return
                        if text == 'Native barge active':
                            frames.append({'toolCall':{'functionCalls':[{'id':'native-barge-note','name':'notes.add',
                                'args':{'text':'Committed before barge-in'}}]}})
                            return
                        if text == 'Native barge playback':
                            frames.append(audio_reply('Native barge playback reply', 60000))
                            return
                        if text == 'Native barge waiting':
                            reply = audio_reply('Native barge waiting reply', 60000)
                            reply['serverContent']['turnComplete'] = False
                            frames.append(reply)
                            live_state['stall'] = True
                            return
                        if text in {"Native playback only", "Native audio muted", "Native key switch"}:
                            frames.append(audio_reply(text + " reply", 2400 if text == "Native audio muted" else 48000))
                            return
                        if text.startswith(("Native CRUD ", "Native BULK ")):
                            for index, (name, arguments) in enumerate(crud_plan(text)):
                                frames.append({"toolCall": {"functionCalls": [{"id": f"native-crud-{text}-{index}",
                                    "name": name, "args": arguments}]}})
                            frames.append({"serverContent": {"outputTranscription": {
                                "text": text + " confirmed"}, "turnComplete": True}})
                            return
                        if message["realtime_input"].get("text") == "Native Stop":
                            live_state["stall"] = True
                            return
                        turns += 1
                        if turns >= 3:
                            # The third and fourth rounds send the same call ID:
                            # The real core should write a single note, the UI should refresh every result.
                            frames.append({"toolCall": {"functionCalls": [{"id": "live-ui-note",
                                "name": "notes.add", "args": {"text": "Live UI synthetic note"}}]}})
                        else:
                            frames.append(audio_reply("Live synthetic reply" if turns == 1 else "Live reused reply"))
                    elif "tool_response" in message:
                        response = message["tool_response"]["functionResponses"][0]
                        assert response["response"]["result"]["verified"]
                        if response['id'] == 'native-review-read':
                            proposal = response['response']['result']['data']['proposal']
                            assert proposal
                            frames.append({'toolCall':{'functionCalls':[{'id':'native-review-decision','name':'memory.decide',
                                'args':{'id':proposal['id'],'approve':True}}]}})
                            return
                        if response['id'] == 'native-review-decision':
                            assert response['response']['result']['evidence']['read_back']
                            frames.append(audio_reply('The suggested fact was saved.'))
                            return
                        if response['id'].startswith('clock-Native CLOCK '):return
                        if response['name'] == 'assistant.request_shutdown':
                            assert response['response']['result']['data']['applied'] is False
                            frames.append(audio_reply('TaskVex will close.', 12000))
                            return
                        if response['name'] == 'assistant.request_sleep_mode':
                            data = response['response']['result']['data']
                            assert data['applied'] is False
                            frames.append(audio_reply("OK sir, I'm turning off permanent sleep mode." if data['mode'] == 'off'
                                else "OK sir, I'm passing.", 12000))
                            return
                        if response["id"].startswith("native-crud-"):
                            return
                        if response['id'] == 'native-barge-note':
                            reply = audio_reply('Native barge active reply', 60000)
                            reply['serverContent']['turnComplete'] = False
                            frames.append(reply)
                            live_state['stall'] = True
                            return
                        frames.append(audio_reply(f"Live tool saved turn {turns}"))
                        if turns == 4 and live_state["opened"] == 1:
                            # Secure checkpoint and GoAway idle of the completed turn
                            # falls on its tail; The next text does not go to the old socket.
                            frames.extend([{"sessionResumptionUpdate": {"resumable": True,
                                "newHandle": "NATIVE_SYNTHETIC_RESUME_HANDLE"}}, {"goAway": {"timeLeft": "10s"}}])
                async def recv(self, **kwargs):
                    if frames and 'setupComplete' in frames[0] and live_state.get('hold_setup'):
                        import asyncio
                        live_state['setup_waiting'] = True
                        while live_state.get('hold_setup'):
                            await asyncio.sleep(.001)
                    while not frames and not live_state["stall"]:
                        import asyncio
                        await asyncio.sleep(.001)  # Also evoke the response added by the stream sender.
                    if not frames and live_state["stall"]:
                        import asyncio
                        live_state["waiting"].set()
                        await asyncio.sleep(3600)  # Stop should interrupt the actual SDK await.
                    return json.dumps(frames.pop(0)).encode()
            try:
                yield Socket()
            finally:
                live_state["closed"] = True
        setattr(live, "ws_connect", live_socket)
        os.environ["GEMINI_API_KEY"] = "TASKVEX_SYNTHETIC_KEY"
        original_client = gemini.genai.Client
        responses = [
            httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                "role": "model", "parts": [{"text": "Hello before notes confirmation"}]}}]}),
            httpx.Response(503, json={"error": {"code": 503}}),
            httpx.Response(503, json={"error": {"code": 503}}),
            httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                "role": "model", "parts": [{"functionCall": {"id": "native-note", "name": "notes.add",
                "args": {"text": "Chat synthetic note"}}, "thoughtSignature": "c2ln"}]}}]}),
            httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                "role": "model", "parts": [{"text": "Saved <img src=x onerror=alert(1)>"}]}}]}),
            httpx.Response(400, json={"error": {"code": 400, "message": "SECRET"}}),
        ]

        def handle_text(request):
            if request.url.path.endswith('/interactions'):
                from base64 import b64encode
                speech_state['requests'].append(json.loads(request.content))
                if speech_state['block']:
                    speech_state['started'].set()
                    assert speech_state['release'].wait(10)
                if speech_state['fail']:
                    return httpx.Response(503, json={'error':{'message':'SECRET'}})
                return httpx.Response(200, json={'id':'native-tts', 'status':'completed', 'steps':[
                    {'type':'model_output', 'content':[{'type':'audio', 'mime_type':'audio/l16',
                     'sample_rate':24000, 'data':b64encode(bytes(4800)).decode()}]}]})
            if request.method == "GET":
                assert catalog_ready.wait(10), "Synthetic capture was not installed before catalog loading"
                return httpx.Response(200, json={"models": [
                    {"name": "models/text-only", "supportedGenerationMethods": ["generateContent"]},
                    {"name": "models/future-live", "displayName": "Future Live", "supportedGenerationMethods": ["bidiGenerateContent"]},
                ]})
            text_requests.append(str(request.url))
            body = json.loads(request.content)
            text_payloads.append(body)
            prompt = body["contents"][0]["parts"][0].get("text", "")
            if prompt.startswith('Native CLOCK '):
                plan=clock_plan(prompt); index=(len(body['contents'])-1)//2
                parts=([{'functionCall':{'id':'clock-'+str(index),'name':plan[index][0],'args':plan[index][1]}}]
                    if index<len(plan) else [{'text':prompt+' confirmed'}])
                return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':parts}}]})
            if prompt.startswith('Native SHUTDOWN '):
                parts = ([{'functionCall': {'id':'shutdown-rest','name':'assistant.request_shutdown','args':{}}}]
                    if len(body['contents']) == 1 else [{'text':'TaskVex will close.'}])
                return httpx.Response(200, json={'candidates': [{'finishReason':'STOP','content':{'role':'model','parts':parts}}]})
            if prompt == 'Native profile probe':
                return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {
                    'role': 'model', 'parts': [{'text': 'Native profile probe REST'}]}}]})
            if prompt.startswith(("Native CRUD ", "Native BULK ")):
                round_index = (len(body["contents"]) - 1) // 2
                if round_index == 2:
                    parts = [{"text": prompt + " confirmed"}]
                else:
                    # In the next round of HTTP the mutation may have already been made;
                    # We solve the plan only when generating the list and mutation response.
                    name, arguments = crud_plan(prompt)[round_index]
                    parts = [{"functionCall": {"id": f"native-crud-{round_index}", "name": name, "args": arguments}}]
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                    "role": "model", "parts": parts}}]})
            if body["contents"][0]["parts"][0].get("text") == "Native REST Stop":
                rest_stop_started.set()
                assert release_rest_stop.wait(15)
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                    "role": "model", "parts": [{"functionCall": {"id": "must-not-run", "name": "notes.add",
                        "args": {"text": "Must not be saved after REST Stop"}}}]}}]})
            if len(text_requests) == 1:
                body = json.loads(request.content)
                assert {item["name"] for item in body["tools"][0]["functionDeclarations"]} == {"apps.catalog", "system.status", "media.status", "media.control", "weather.current", "weather.locations", "assistant.request_sleep_mode", "assistant.request_shutdown", "clocks.create", "clocks.control", "clocks.list"}
                text_started.set()
                assert release_text.wait(20)
            assert responses, "Unexpected model retry"
            return responses.pop(0)

        def client(**kwargs):
            kwargs["http_options"].client_args = {"transport": httpx.MockTransport(handle_text)}
            return original_client(**kwargs)

        gemini.genai.Client = client
        gemini.GeminiText._wait_retry = lambda self, seconds: None

    def create(*args, **kwargs):
        kwargs["hidden"] = True
        captured["api"] = kwargs["js_api"]
        if phase == 'unknown':
            from app.core.contracts import Task, TaskStatus, ToolRequest, ToolResult, ToolError
            from app.storage.json_store import JsonStore
            api = captured['api']
            api._store.write({'theme': '#a78bfa', 'prof': {'pIns': 'Synthetic preserved profile'}})
            captured['original_settings'] = api._store.path.read_bytes()
            JsonStore(home / 'notes.json').write({'notes': [], 'ui_migrated': True})
            captured['original_notes'] = (home / 'notes.json').read_bytes()
            task = Task(task_id='native-synthetic-unknown', status=TaskStatus.UNKNOWN,
                request=ToolRequest(request_id='native-previous-action', source='desktop', principal='local-user',
                    tool='media.control', arguments={'action':'pause','target_id':'a'*32}),
                result=ToolResult(task_id='native-synthetic-unknown', status=TaskStatus.UNKNOWN,
                    error=ToolError(code='synthetic_unknown', message='Effect unconfirmed')))
            api._core._journal.save(task)
            api._core._uncertain = True
            captured['unknown_task'] = task
        if phase == "credentials":
            original_event = captured["api"].event
            queries = []

            def event(name, data=None):
                result = original_event(name, data)
                if name == "query_apikey" and not queries:
                    queries.append(True)
                    key_query_started.set()
                    assert release_key_query.wait(25)
                return result

            captured["api"].event = event
        captured["window"] = original_create(*args, **kwargs)
        return captured["window"]

    def wait_until(check):
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if check():
                return
            time.sleep(0.1)
        raise TimeoutError("Native acceptance condition was not reached")

    def exercise():
        window, api = captured["window"], captured["api"]

        def js(body):
            completed, result = Event(), {}

            def callback(value):
                result["value"] = value
                completed.set()

            window.evaluate_js("Promise.resolve().then(async()=>{" + body +
                               "}).catch(e=>({test_error:String(e)}))", callback=callback)
            assert completed.wait(15), "JS promise did not complete"
            value = result["value"]
            assert not (isinstance(value, dict) and "test_error" in value), value
            return value

        def export_backup(accept):
            """Emulate file selection; try the real WebView2 download script."""
            from webview.platforms import edgechromium
            original_forms = getattr(edgechromium, "WinForms")
            export_path = home / ("exported-backup.json" if accept else "cancelled-backup.json")
            calls = []

            class SaveDialog:
                def ShowDialog(self, owner):
                    calls.append(True)
                    self.FileName = str(export_path)
                    return original_forms.DialogResult.OK if accept else original_forms.DialogResult.Cancel

            class FormsProxy:
                SaveFileDialog = SaveDialog

                def __getattr__(self, name):
                    return getattr(original_forms, name)

            setattr(edgechromium, "WinForms", FormsProxy())
            try:
                js("document.getElementById('expB').click();return true;")
                wait_until(lambda: len(calls) == 1)
                if accept:
                    wait_until(lambda: export_path.is_file() and export_path.stat().st_size > 0)
                    return json.loads(export_path.read_text('utf-8'))
                assert not export_path.exists()
                return None
            finally:
                setattr(edgechromium, "WinForms", original_forms)

        try:
            if phase == 'unknown':
                task = captured['unknown_task']
                wait_until(lambda: window.evaluate_js("typeof window.vex==='object' && !document.getElementById('acknowledgeTasks').hidden"))
                assert not api._ready and api._core.uncertain
                assert window.evaluate_js("document.getElementById('recoverSettings').hidden")
                assert 'not damaged' in window.evaluate_js("document.getElementById('nativeIssueText').textContent")
                assert 'media.control' in window.evaluate_js("document.getElementById('nativeIssueTasks').textContent")
                retry = js("return await window.pywebview.api.event('retry_startup');")
                assert retry['code'] == 'uncertain_state'
                js("window.confirm=()=>false;document.getElementById('acknowledgeTasks').click();return true;")
                assert api._core.uncertain and not api._ready
                js("window.confirm=()=>true;document.getElementById('acknowledgeTasks').click();return true;")
                wait_until(lambda: api._ready and api._notes_ready)
                wait_until(lambda: window.evaluate_js("document.getElementById('nativeIssue').hidden"))
                wait_until(lambda: js("const t=await import('./js/clocks.js');return t.nativeClocksActive();"))
                assert not api._core.uncertain
                historical = api._core.get(task.task_id)
                assert historical.task_id == task.task_id and historical.status == task.status
                assert historical.request.arguments == {}
                assert historical.result.evidence == {'historical': True, 'content_available': False}
                assert api._core.submit(task.request) == historical
                assert api._store.path.read_bytes() == captured['original_settings']
                assert (home / 'notes.json').read_bytes() == captured['original_notes']
                assert not list(home.glob('settings.json.*.corrupt'))
                outcome.update(ok=True, phase=phase, declined_review_preserved=True, review_completed=True,
                    unknown_result_preserved=True, replay_protection_preserved=True, settings_preserved=True,
                    post_recovery_notes_and_clocks_connected=True)
                return
            if phase in {"corrupt", "schema_invalid", "future"}:
                original = (home / "settings.json").read_bytes()
                existing_backups = set(home.glob("settings.json.*.corrupt"))
                wait_until(lambda: window.evaluate_js(
                    "typeof window.vex==='object' && document.getElementById('nativeIssue')?.hidden===false"))
                assert not api._ready
                assert "Native local note" in js("const s=await import('./js/settings.js');return JSON.stringify(s.store.notes);")
                if phase == "future":
                    assert window.evaluate_js("document.getElementById('recoverSettings').hidden")
                    assert "version" in window.evaluate_js("document.getElementById('nativeIssueText').textContent")
                    assert (home / "settings.json").read_bytes() == original
                    assert set(home.glob("settings.json.*.corrupt")) == existing_backups
                    outcome.update(ok=True, phase=phase, future_version_preserved=True, repair_hidden=True)
                    return
                assert not window.evaluate_js("document.getElementById('recoverSettings').hidden")
                retry = js("return await window.pywebview.api.event('retry_startup');")
                assert retry["ok"] is False and (home / "settings.json").read_bytes() == original
                js("window.confirm=()=>false;document.getElementById('recoverSettings').click();return true;")
                assert (home / "settings.json").read_bytes() == original
                assert set(home.glob("settings.json.*.corrupt")) == existing_backups
                before = js("const s=await import('./js/settings.js');return JSON.stringify([s.store.notes,s.store.skills,s.store.routines,s.store.prof]);")
                js("window.confirm=()=>true;document.getElementById('recoverSettings').click();return true;")
                wait_until(lambda: api._ready)
                wait_until(lambda: window.evaluate_js("document.getElementById('nativeIssue').hidden"))
                wait_until(lambda: api._notes_ready)
                wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
                after = js("const s=await import('./js/settings.js');return JSON.stringify([s.store.notes,s.store.skills,s.store.routines,s.store.prof]);")
                expected = json.loads(before)
                if phase == 'schema_invalid':
                    # The current repaired backend profile does not contain memory. old
                    # The vulnerability of UI profile permission/text should not be inherited from this profile.
                    expected[3]['pMem'] = ''
                    expected[3]['pMemory'] = False
                    expected[3]['pLearn'] = False
                    expected[3]['pMemoryConfirm'] = True
                assert json.loads(after) == expected, (json.loads(after), expected)
                new_backups = set(home.glob("settings.json.*.corrupt")) - existing_backups
                assert len(new_backups) == 1 and new_backups.pop().read_bytes() == original
                assert api._store.read()["vol"] == 0.8
                if phase == "schema_invalid":
                    assert api._store.read()["prof"] == {"pIns": "Native profile 📝"}
                    assert api._store.read()["theme"] == "#4fd8ff"
                outcome.update(ok=True, phase=phase, issue_visible=True, declined_repair_preserved=True,
                               original_backed_up=True, repair_completed=True, local_data_preserved=True)
                return
            wait_until(lambda: api._ready)
            initial = js("return {alias:window.vex===window.jarvis, api:Object.keys(window.pywebview.api),"
                         "online:document.getElementById('netP').textContent,"
                         "system:document.getElementById('win').textContent};")
            assert initial["alias"] and initial["api"] == ["event"], initial
            assert "OFFLINE" in initial["online"], initial
            wait_until(lambda: "%" in window.evaluate_js("document.getElementById('ram').textContent"))
            assert '%' in window.evaluate_js("document.getElementById('ram').textContent")
            outcome['native_local_memory_and_system_sample']=True
            assert window.evaluate_js("document.getElementById('gpu').textContent")=='0%'
            assert window.evaluate_js("document.getElementById('gpuT').textContent")=='—'
            assert window.evaluate_js("document.getElementById('gpuLabel').textContent")=='GPU'
            assert 'Windows GPU usage' in window.evaluate_js("document.getElementById('gpu').title")
            assert window.evaluate_js("document.getElementById('systemStatus')===null")
            assert window.evaluate_js("document.getElementById('cpuT').textContent")=='—'
            outcome['native_windows_gpu_zero_and_static_label']=True
            assert window.evaluate_js("document.getElementById('nLink').textContent")=='Wi-Fi'
            assert window.evaluate_js("document.getElementById('nWifi').textContent")=='75%'
            assert window.evaluate_js("document.getElementById('nPing').textContent")=='0 ms'
            assert 'Local IPv4 gateway' in window.evaluate_js("document.getElementById('nPing').title")
            if phase=='save':
                wait_until(lambda: window.evaluate_js("document.getElementById('nDown').textContent")=='0.00 Mbps')
                assert window.evaluate_js("document.getElementById('nUp').textContent")=='0.00 Mbps'
            outcome['native_local_network_link_and_rates']=True
            outcome['native_gateway_ping_and_wifi_signal']=True
            wait_until(lambda: window.evaluate_js("document.getElementById('mTitle2').textContent")=='Native synthetic track')
            assert 'paused' in window.evaluate_js("document.getElementById('mArt').textContent")
            assert window.evaluate_js("document.getElementById('mPlay').disabled && !document.getElementById('eq').classList.contains('on')")
            outcome['native_read_only_media_view']=True
            if phase == 'save':
                check_native_media(window,api,js,wait_until,outcome)
                js("const p=await import('./js/panels.js');const s=await import('./js/settings.js');p.openM('mSet');s.switchTab('connection');document.getElementById('locIn').value='Native Test City';document.getElementById('locSaveB').click();return true;")
                wait_until(lambda:window.evaluate_js("document.querySelectorAll('#locChoices button').length")>0)
                js("document.querySelector('#locChoices button').click();return true;")
                wait_until(lambda:window.evaluate_js("document.getElementById('wT').textContent")=='0°')
                assert api._store.read()['weatherLocation']['label']=='Native Test City, Test Country'
                assert '0 km/h' in window.evaluate_js("document.getElementById('wM').textContent")
                js("const p=await import('./js/panels.js');p.closeM();return true;")
                outcome['native_weather_selection_persistence_zero_and_dashboard']=True
                camera = js("const {liveVideo}=await import('./js/live_video.js');"
                    "const devices=navigator.mediaDevices,original=devices.getUserMedia.bind(devices);"
                    "const canvas=document.createElement('canvas');canvas.width=320;canvas.height=240;"
                    "canvas.getContext('2d').fillRect(0,0,320,240);const stream=canvas.captureStream(1);"
                    "let requested=null;devices.getUserMedia=async options=>{requested=options;return stream;};"
                    "try{const ready=await liveVideo.start();const image=liveVideo.snapshot();liveVideo.stop();"
                    "return {ready,jpeg:image?.startsWith('/9j/'),bounded:image?.length<=349528,"
                    "videoOnly:requested.audio===false,ended:stream.getTracks().every(t=>t.readyState==='ended'),"
                    "off:document.getElementById('camB').getAttribute('aria-pressed')==='false'};}"
                    "finally{liveVideo.stop();devices.getUserMedia=original;}")
                assert camera == {'ready':True,'jpeg':True,'bounded':True,'videoOnly':True,'ended':True,'off':True}, camera
                outcome['native_synthetic_camera_capture_jpeg_and_cleanup']=True
                permission = js("const devices=navigator.mediaDevices,original=devices.getUserMedia.bind(devices);"
                    "const canvas=document.createElement('canvas');canvas.width=160;canvas.height=120;"
                    "canvas.getContext('2d').fillRect(0,0,160,120);const stream=canvas.captureStream(1);"
                    "let options=null;devices.getUserMedia=async value=>{options=value;return stream;};"
                    "try{const settings=await import('./js/settings.js');const panels=await import('./js/panels.js');"
                    "panels.openM('mSet');settings.switchTab('system');"
                    "document.querySelector('[data-request-permission=\"camera\"]').click();"
                    "await new Promise(resolve=>setTimeout(resolve,50));"
                    "return {allowed:document.getElementById('permission-camera').dataset.state==='granted',"
                    "videoOnly:options.audio===false&&options.video===true,ended:stream.getTracks().every(t=>t.readyState==='ended'),"
                    "off:document.getElementById('camB').getAttribute('aria-pressed')==='false'};}"
                    "finally{devices.getUserMedia=original;stream.getTracks().forEach(t=>t.stop());(await import('./js/panels.js')).closeM();}")
                assert permission == {'allowed':True,'videoOnly':True,'ended':True,'off':True}, permission
                outcome['native_default_camera_permission_without_live_or_capture']=True
                check_native_screen(window, js, outcome)
            if phase=='reopen':
                assert window.evaluate_js("!document.getElementById('scrT').checked && document.querySelector('#scr video')===null")
                outcome['native_screen_does_not_resume_on_restart']=True
                wait_until(lambda:window.evaluate_js("document.getElementById('wT').textContent")=='0°')
                outcome['native_weather_location_restored_without_geolocation']=True
            if phase == "chat":
                # The new autostart should never reach the physical microphone.
                # Each permission call receives a fresh, quiet synth track.
                js("window.defaultMicContext=new AudioContext();window.defaultMicTracks=[];"
                   "window.testMicOff=()=>{const b=document.getElementById('micB');if(b.getAttribute('aria-pressed')==='true')b.click();};"
                   "window.testMicOn=()=>{testMicOff();document.getElementById('micB').click();};"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=defaultMicContext.createMediaStreamDestination();defaultMicTracks.push(...d.stream.getTracks());return d.stream;}});return true;")
                js("const d=document.getElementById('sleepDelay');d.value='0';d.dispatchEvent(new Event('change'));return true;")
                wait_until(lambda: (api._store.read() or {}).get('sleepDelay') == 0)
                wait_until(lambda: window.evaluate_js("document.getElementById('dIn').options.length>0 && document.getElementById('dOut').options.length>0"))
                assert window.evaluate_js("document.getElementById('devB')===null")
                outcome['audio_devices_listed_at_startup_without_scan_button'] = True
                assert js("const input=document.getElementById('sleepDelay');document.getElementById('sleepMore').click();if(input.value!=='1')return false;document.getElementById('sleepLess').click();document.getElementById('sleepLess').click();if(input.value!=='0')return false;input.value='300';document.getElementById('sleepMore').click();if(input.value!=='300')return false;input.value='0';input.dispatchEvent(new Event('change'));return true;")
                outcome['themed_sleep_stepper_bounded_to_0_300']=True
                catalog_ready.set()
                assert window.evaluate_js("document.getElementById('refreshModels')===null")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                silent_requests = len(live_state['sent'])
                time.sleep(.3)
                assert len(live_state['sent']) == silent_requests
                assert not window.evaluate_js("document.getElementById('inp').disabled")
                outcome['automatic_listening_after_catalog_without_click_or_idle_api'] = True
                js("testMicOff();return true;")
                js("document.getElementById('liveLatencyTest').checked=false;return true;")
                wait_until(lambda: "Use backend notes" in window.evaluate_js("document.getElementById('notesConnect').textContent"))
                assert not api._notes_ready
                js("document.getElementById('inp').value='Hello before notes confirmation';"
                   "document.getElementById('send').click();return true;")
                assert text_started.wait(5)
                assert api._chat.busy
                assert window.evaluate_js("document.getElementById('send').disabled && document.getElementById('noteAdd').disabled")
                assert not api.event("text", "Duplicate")["ok"]
                assert not api.event("shutdown")["ok"]
                assert not api._chat.close()
                assert api.event("save", {"vol": 0.5})["ok"]
                release_text.set()
                wait_until(lambda: "Answered by" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert not api._notes_ready and "Hello before notes confirmation" in window.evaluate_js("document.getElementById('msgs').textContent")
                js("window.confirm=()=>true;document.getElementById('notesConnect').click();return true;")
                wait_until(lambda: api._notes_ready)
                js("document.getElementById('inp').value='Add the synthetic note';document.getElementById('send').click();return true;")
                wait_until(lambda: "gemini-3.5-flash-lite" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                state = js("return {notes:document.getElementById('notes').textContent,"
                           "answer:document.getElementById('msgs').textContent,"
                           "safe:!document.querySelector('#msgs img'),input:document.getElementById('inp').value,"
                           "online:document.getElementById('netP').textContent};")
                assert "Chat synthetic note" in state["notes"] and "Saved <img" in state["answer"]
                assert state["safe"] and state["input"] == "" and "gemini-3.5-flash-lite" in state["online"]
                assert len(text_requests) == 5 and "gemini-3.5-flash-lite" in text_requests[-1]
                assert 'playback finished' in window.evaluate_js("document.getElementById('textStatus').textContent")
                from app.core.contracts import ToolRequest
                from uuid import uuid4
                task = api._core.submit(ToolRequest(request_id=uuid4().hex, source="desktop",
                    principal="local-user", tool="notes.list"))
                finished = api._core.wait(task.task_id, timeout=3)
                assert finished.result is not None
                assert sum(n["text"] == "Chat synthetic note" for n in finished.result.data["notes"]) == 1
                document = (home / "notes.json").read_bytes()
                js("document.getElementById('inp').value='Rejected request';document.getElementById('send').click();return true;")
                wait_until(lambda: "HTTP 400" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert "invalid_request" in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert "Model request:" in window.evaluate_js("document.getElementById('log').textContent")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert window.evaluate_js("document.getElementById('inp').value") == "Rejected request"
                assert "FAILED" in window.evaluate_js("document.getElementById('netP').textContent")
                assert "SECRET" not in window.evaluate_js("document.getElementById('log').textContent")
                assert (home / "notes.json").read_bytes() == document
                assert len(speech_state['requests']) == 2
                assert speech_state['requests'][-1]['input'][0]['content'][0]['text'] == 'Saved <img src=x onerror=alert(1)>'
                assert 'tools' not in speech_state['requests'][-1]
                # Audio error preserves text; Mute does not start the new TTS request.
                speech_state['fail'] = True
                js("document.getElementById('inp').value='Native profile probe';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'audio unavailable: speech_unavailable' in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert len(speech_state['requests']) == 3  # It does not become a 503 TTS repeat.
                assert 'Native profile probe REST' in window.evaluate_js("document.getElementById('msgs').textContent")
                speech_state['fail'] = False
                speech_count = len(speech_state['requests'])
                js("document.getElementById('mute').click();document.getElementById('inp').value='Native profile probe';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert len(speech_state['requests']) == speech_count
                assert 'playback muted' in window.evaluate_js("document.getElementById('textStatus').textContent")
                js("document.getElementById('mute').click();return true;")
                # Synthesis HTTP can wait while the text is visible. Stop acceptance,
                # does not open checks until the actual HTTP is finished; registration is irrevocable.
                speech_state['block'] = True
                js("document.getElementById('inp').value='Native profile probe';document.getElementById('send').click();return true;")
                assert speech_state['started'].wait(5)
                assert 'Native profile probe REST' in window.evaluate_js("document.getElementById('msgs').textContent")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: 'Speech stop requested' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("document.getElementById('send').disabled") and api._chat.busy
                speech_state['release'].set()
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                speech_state['block'] = False
                assert (home / 'notes.json').read_bytes() == document
                outcome['rest_speech_text_first_failure_preserved_no_retry_mute_and_stop'] = True
                before_rest_stop = len(text_requests)
                js("document.getElementById('inp').value='Native REST Stop';document.getElementById('send').click();return true;")
                assert rest_stop_started.wait(5)
                assert not window.evaluate_js("document.getElementById('stopTask').disabled")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: "Waiting for the current HTTP request" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert api._chat.busy and window.evaluate_js("document.getElementById('send').disabled && document.getElementById('noteAdd').disabled")
                release_rest_stop.set()
                wait_until(lambda: "Stopped. Completed actions" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert (home / "notes.json").read_bytes() == document
                assert len(text_requests) == before_rest_stop + 1 and not api._chat.busy
                check_native_note_crud(home, window, js, wait_until, outcome, "rest", "Chat synthetic note")
                document = (home / "notes.json").read_bytes()
                assert window.evaluate_js("document.getElementById('mSel').value") == 'future-live'
                wait_until(lambda: "API Live models loaded" in window.evaluate_js("document.getElementById('liveCatalogStatus').textContent"))
                assert window.evaluate_js("Array.from(document.getElementById('mSel').options).map(o=>o.value)") == ['future-live']
                js("const select=document.getElementById('mSel');select.value='future-live';"
                   "select.dispatchEvent(new Event('change'));return true;")
                wait_until(lambda: api._live_model == 'future-live')
                wait_until(lambda: "Live model selected" in window.evaluate_js("document.getElementById('liveCatalogStatus').textContent"))
                assert api._model == 'gemini-3.8-flash'
                rest_requests = len(text_requests)
                js("window.nativeAudioPackets=[];const original=window.vex.audioChunk;"
                   "window.vex.audioChunk=packet=>{const accepted=original(packet);"
                   "window.nativeAudioPackets.push({id:packet.request_id,accepted});return accepted;};return true;")
                js("document.getElementById('liveLatencyTest').checked=true;document.getElementById('inp').value='Live test';"
                   "document.getElementById('send').click();return true;")
                wait_until(lambda: "first text" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert "Live synthetic reply" in window.evaluate_js("document.getElementById('msgs').textContent")
                assert window.evaluate_js("document.getElementById('tokTxt').textContent")== '≥ 10'
                assert 'Session total: 10' in window.evaluate_js("document.getElementById('tokSub').textContent")
                assert "LAST LIVE TEST" in window.evaluate_js("document.getElementById('netP').textContent")
                assert live_state["opened"] == 1 and not live_state["closed"] and len(text_requests) == rest_requests
                js("document.getElementById('inp').value='Second Live message';document.getElementById('send').click();return true;")
                wait_until(lambda: "session reused" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert "Live reused reply" in window.evaluate_js("document.getElementById('msgs').textContent")
                assert window.evaluate_js("document.getElementById('tokTxt').textContent")== '≥ 20'
                outcome['application_session_tokens_accumulate_native_replies']=True
                assert live_state["opened"] == 1 and len(text_requests) == rest_requests
                assert (home / "notes.json").read_bytes() == document
                for turn in [3, 4]:
                    js("document.getElementById('inp').value='Live add note';document.getElementById('send').click();return true;")
                    wait_until(lambda: f"Live tool saved turn {turn}" in window.evaluate_js("document.getElementById('msgs').textContent"))
                    wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                    assert "Live UI synthetic note" in window.evaluate_js("document.getElementById('notes').textContent")
                from app.storage.json_store import JsonStore
                snapshot = JsonStore(home / "notes.json").read()
                assert snapshot is not None
                saved = snapshot["notes"]
                assert sum(note["text"] == "Live UI synthetic note" for note in saved) == 1
                assert live_state["opened"] == 1 and len(text_requests) == rest_requests
                before_stop = (home / "notes.json").read_bytes()
                logical_id = api._chat._live._connection.logical_id
                js("document.getElementById('inp').value='Resume check';document.getElementById('send').click();return true;")
                wait_until(lambda: "session resumed" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state["opened"] == 2 and live_state["resumed"]
                assert api._chat._live._connection.logical_id == logical_id
                assert (home / "notes.json").read_bytes() == before_stop
                assert "NATIVE_SYNTHETIC_RESUME_HANDLE" not in window.evaluate_js("document.body.textContent")
                check_native_note_crud(home, window, js, wait_until, outcome, "live", "Live UI synthetic note")
                before_stop = (home / "notes.json").read_bytes()
                js("document.getElementById('inp').value='Native Stop';document.getElementById('send').click();return true;")
                assert live_state["waiting"].wait(5)
                assert not window.evaluate_js("document.getElementById('stopTask').disabled")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: "Stopped. Completed actions" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state["closed"] and (home / "notes.json").read_bytes() == before_stop
                js("document.getElementById('inp').value='After stop';document.getElementById('send').click();return true;")
                wait_until(lambda: "new session" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state["opened"] == 3 and not live_state["closed"]
                # True mute and Stop only tail sound: model completed
                # Therefore, a new native/model cancellation should not be initiated.
                js("document.getElementById('mute').click();return true;")
                assert js("const a=await import('./js/live_audio.js');return a.liveAudio.muted;") is True
                js("document.getElementById('inp').value='Native audio muted';document.getElementById('send').click();return true;")
                wait_until(lambda: "playback muted" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                js("document.getElementById('mute').click();document.getElementById('inp').value='Native playback only';"
                   "document.getElementById('send').click();return true;")
                wait_until(lambda: "Native playback only reply" in window.evaluate_js("document.getElementById('msgs').textContent"))
                assert not api._chat.busy and window.evaluate_js("document.getElementById('send').disabled")
                last_audio_id = window.evaluate_js("window.nativeAudioPackets.at(-1).id")
                assert window.evaluate_js("window.nativeAudioPackets.length>0 && window.nativeAudioPackets.every(p=>p.accepted)")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: "playback stopped" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert js("return window.vex.audioChunk(" + json.dumps({"request_id": last_audio_id,
                    "mime_type": "audio/pcm;rate=24000", "data": "AAA="}) + ");") is False
                js("document.getElementById('inp').value='Native key switch';document.getElementById('send').click();return true;")
                wait_until(lambda: "Native key switch reply" in window.evaluate_js("document.getElementById('msgs').textContent"))
                assert window.evaluate_js("document.getElementById('send').disabled")
                js("const api=await import('./js/api.js');api.setConnectionStatus('offline','KEY CHANGED');"
                   "window.dispatchEvent(new Event('taskvex-key-saved'));return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert "KEY CHANGED" in window.evaluate_js("document.getElementById('netP').textContent")
                js("const c=await import('./js/connections.js');c.setCatalog({models:[{id:'gemini-3.8-live',name:'Synthetic Live'}],currentModel:'gemini-3.8-live'});return true;")
                # Physical microphone opening: to the real AudioWorklet/PCM path
                # give test oscillator stream only; Real account is not used.
                js("window.testMicContext=new AudioContext();window.testMicOsc=testMicContext.createOscillator();window.testMicDestinations=[];"
                   "testMicOsc.start();await testMicContext.resume();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=testMicContext.createMediaStreamDestination();testMicDestinations.push(d);"
                   "if(testMicDestinations.length===1)testMicOsc.connect(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Native microphone answer' in window.evaluate_js("document.getElementById('msgs').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Native microphone hello' in window.evaluate_js("document.getElementById('msgs').textContent")
                wait_until(lambda: window.evaluate_js("testMicDestinations.length>=2"))
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("testMicDestinations[0].stream.getTracks().every(t=>t.readyState==='ended')")
                # A third party other than the initial speech source and response listener
                # the microphone should not be turned on; At the end of the response, the same track remains live.
                assert window.evaluate_js("testMicDestinations.length===2 && testMicDestinations[1].stream.getTracks().every(t=>t.readyState==='live')")
                outcome['reply_end_preserved_waiting_microphone_without_reopen'] = True
                js("testMicOsc.connect(testMicDestinations.at(-1));return true;")
                wait_until(lambda: window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length===3"))
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                js("testMicOff();testMicOsc.stop();await testMicContext.close();return true;")
                assert window.evaluate_js("testMicDestinations.every(d=>d.stream.getTracks().every(t=>t.readyState==='ended'))")
                outcome['two_voice_turns_automatic_rearm_without_second_click'] = True
                outcome['microphone_stream_worklet_pcm_transcript_and_cleanup'] = True
                # User On preference is independent of Stop/model rejection.
                # In silence, new conversation is expected without another API request.
                js("window.persistentMicContext=new AudioContext();window.persistentMicOsc=persistentMicContext.createOscillator();"
                   "window.persistentMicDestinations=[];persistentMicOsc.start();await persistentMicContext.resume();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=persistentMicContext.createMediaStreamDestination();persistentMicDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                unchanged_notes = (home / 'notes.json').read_bytes()
                js("document.getElementById('inp').value='Native microphone rejected note';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                assert window.evaluate_js("document.getElementById('micB').textContent.includes('Microphone On')")
                assert (home / 'notes.json').read_bytes() == unchanged_notes
                sent_after_error = len(live_state['sent'])
                time.sleep(.3)
                assert len(live_state['sent']) == sent_after_error  # The old command/retry is missing.
                js("document.getElementById('inp').value='Native barge waiting';document.getElementById('send').click();return true;")
                wait_until(lambda: api._chat.busy and js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                js("window.stopMicStates=[];window.stopMicObserver=new MutationObserver(()=>stopMicStates.push(document.getElementById('micB').classList.contains('on')));"
                   "stopMicObserver.observe(document.getElementById('micB'),{attributes:true,attributeFilter:['class']});return true;")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not api._chat.busy and not window.evaluate_js("document.getElementById('send').disabled"))
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                assert window.evaluate_js("document.getElementById('micB').getAttribute('aria-pressed')==='true' && window.vex.state==='idle'")
                assert js("stopMicObserver.disconnect();return !stopMicStates.includes(false);")
                assert window.evaluate_js("document.getElementById('netP').classList.contains('idle') && !document.getElementById('netP').classList.contains('off')")
                assert 'LIVE READY' in window.evaluate_js("document.getElementById('netP').textContent")
                assert js("document.getElementById('netP').click();return document.getElementById('netP').classList.contains('idle');")
                outcome['stop_microphone_light_stable_and_connection_neutral'] = True
                js("document.getElementById('inp').value='Native server interruption';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert window.evaluate_js("document.getElementById('netP').classList.contains('idle') && !document.getElementById('netP').classList.contains('off')")
                assert 'Native interrupted reply' in window.evaluate_js("document.getElementById('msgs').textContent")
                outcome['confirmed_server_interruption_neutral_not_transport_failure'] = True
                previous_voice_answers = window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length")
                js("persistentMicOsc.connect(persistentMicDestinations.at(-1));return true;")
                wait_until(lambda: window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length") > previous_voice_answers)
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                # The Off decision is not removed by a subsequent Stop or model-ready event.
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                js("document.getElementById('inp').value='Native barge waiting';document.getElementById('send').click();return true;")
                wait_until(lambda: api._chat.busy and js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                js("testMicOff();return true;")
                time.sleep(.1)
                assert api._chat.busy and window.evaluate_js("document.getElementById('send').disabled")
                assert js("return document.querySelector('#msgs .m.j[data-request-id]:last-child').dataset.state;") == 'live'
                outcome['microphone_off_preserves_active_output_until_explicit_stop'] = True
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                js("window.dispatchEvent(new CustomEvent('taskvex-live-model-ready',{detail:{ready:true}}));return true;")
                assert js("const m=await import('./js/live_mic.js');return !m.liveMic.active && document.getElementById('micB').textContent.includes('Microphone Off');")
                js("persistentMicOsc.stop();await persistentMicContext.close();return true;")
                outcome['microphone_on_survives_rejected_note_and_stop_without_replay'] = True
                outcome['manual_microphone_off_survives_stop_and_model_ready'] = True
                # Quiet standby/talk/answer distinction with true AudioWorklet.
                # Hybrid EOS can now have early response; open server response
                # Thinking of holding on to the barrier and eyeing the locks deterministically.
                live_state['hold_microphone_reply'] = True
                live_state['hold_status_reply'] = True
                js("window.statusContext=new AudioContext();window.statusOsc=statusContext.createOscillator();window.statusDestinations=[];"
                   "statusOsc.start();await statusContext.resume();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=statusContext.createMediaStreamDestination();statusDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js('window.vex.state') == 'idle'
                js("statusOsc.connect(statusDestinations.at(-1));return true;")
                wait_until(lambda: api._chat.busy and window.evaluate_js('window.vex.state') == 'listening')
                js("statusOsc.disconnect();return true;")
                wait_until(lambda: window.evaluate_js('window.vex.state') == 'thinking')
                assert api._chat.busy and window.evaluate_js("document.getElementById('send').disabled")
                live_state['hold_status_reply'] = False
                wait_until(lambda: window.evaluate_js('window.vex.state') == 'speaking')
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js('window.vex.state') == 'idle'
                js("testMicOff();statusOsc.stop();await statusContext.close();return true;")
                live_state['hold_microphone_reply'] = False
                outcome['idle_waiting_listening_speech_thinking_and_speaking'] = True
                # Mic Off only sends EOS; active pattern round does not count as a Stop.
                live_state['hold_microphone_reply'] = True
                ended_before = live_state.get('input_ended', 0)
                live_state['voice_seen'] = False
                js("window.offContext=new AudioContext();window.offOsc=offContext.createOscillator();offOsc.start();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=offContext.createMediaStreamDestination();offOsc.connect(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: api._chat.busy and live_state.get('voice_seen'))
                js("testMicOff();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state.get('input_ended', 0) == ended_before + 1
                assert 'Native microphone Off answer' in window.evaluate_js("document.getElementById('msgs').textContent")
                assert 'Stopped' not in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert window.evaluate_js("document.getElementById('micB').getAttribute('aria-pressed')==='false'")
                js("offOsc.stop();await offContext.close();return true;")
                live_state['hold_microphone_reply'] = False
                outcome['microphone_off_ends_input_without_stopping_answer'] = True
                # Before Setup is finished, Off uses the same input end path.
                assert api._chat.reset_live()
                live_state.update(hold_setup=True, setup_waiting=False, hold_microphone_reply=True)
                ended_before = live_state.get('input_ended', 0)
                js("window.earlyContext=new AudioContext();window.earlyOsc=earlyContext.createOscillator();earlyOsc.start();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=earlyContext.createMediaStreamDestination();earlyOsc.connect(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: live_state.get('setup_waiting'))
                js("testMicOff();return true;")
                live_state['hold_setup'] = False
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state.get('input_ended', 0) == ended_before + 1
                assert 'Stopped' not in window.evaluate_js("document.getElementById('textStatus').textContent")
                js("earlyOsc.stop();await earlyContext.close();return true;")
                live_state['hold_microphone_reply'] = False
                outcome['microphone_off_before_setup_ends_input_without_stop'] = True
                # The same actual WebView microphone cuts out the old response; new turn
                # It is opened only after the host finalizes the old tool result.
                for prompt in ['Native barge active', 'Native barge playback']:
                    previous_answers = window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length")
                    js("window.bargeContext=new AudioContext();window.bargeOsc=bargeContext.createOscillator();window.bargeDestinations=[];"
                       "bargeOsc.start();await bargeContext.resume();"
                       "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                       "const d=bargeContext.createMediaStreamDestination();bargeDestinations.push(d);return d.stream;}});"
                       "testMicOn();return true;")
                    wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                    js("document.getElementById('inp').value=" + json.dumps(prompt) + ";document.getElementById('send').click();return true;")
                    wait_until(lambda: window.evaluate_js("document.getElementById('send').disabled && document.getElementById('micB').classList.contains('on')"))
                    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                    old_reply_id = window.evaluate_js("document.querySelector('#msgs .m.j[data-request-id]:last-child')?.dataset.requestId")
                    assert old_reply_id
                    if prompt.endswith('active'):
                        assert api._chat.busy
                        assert 'Native barge active reply' in window.evaluate_js("document.getElementById('msgs').textContent")
                        assert js("return document.querySelector('[data-request-id=' + JSON.stringify(" + json.dumps(old_reply_id) + ") + '].j').dataset.state;") == 'live'
                        outcome['live_transcript_visible_before_turn_completion'] = True
                    # A short 100 ms pulse should not interrupt the old response or initiate a new one.
                    # should not initiate conversation; Then the real term candidate is tried.
                    js("bargeOsc.connect(bargeDestinations.at(-1));await new Promise(r=>setTimeout(r,100));"
                       "bargeOsc.disconnect();await new Promise(r=>setTimeout(r,200));return true;")
                    assert window.evaluate_js("document.getElementById('send').disabled")
                    assert window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length") == previous_answers
                    assert js("return document.querySelector('[data-request-id=' + JSON.stringify(" + json.dumps(old_reply_id) + ") + '].j').dataset.state;") != 'interrupted'
                    js("bargeOsc.connect(bargeDestinations.at(-1));return true;")
                    wait_until(lambda: window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length") > previous_answers)
                    wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                    assert not api._chat.busy
                    assert js("const nodes=Array.from(document.querySelectorAll('#msgs .m.j')).filter(n=>n.dataset.requestId===" + json.dumps(old_reply_id) + ");return nodes.length===1 && nodes[0].dataset.state==='interrupted' && nodes[0].textContent.includes('reply');")
                    if prompt.endswith('active'):
                        from app.storage.json_store import JsonStore
                        assert sum(n['text']=='Committed before barge-in' for n in (JsonStore(home/'notes.json').read() or {})['notes']) == 1
                    js("testMicOff();bargeOsc.stop();await bargeContext.close();return true;")
                    assert window.evaluate_js("bargeDestinations.every(d=>d.stream.getTracks().every(t=>t.readyState==='ended'))")
                outcome['barge_in_active_preserved_commit_and_playback_handoff'] = True
                outcome['short_noise_did_not_interrupt_active_or_playback_reply'] = True
                outcome['live_transcript_interrupted_text_preserved_without_duplicate'] = True
                assert 'Failed to send live_audio_start: Live response stopped' not in window.evaluate_js("document.getElementById('log').textContent")
                outcome['normal_stop_not_logged_as_transport_failure'] = True
                js("window.bargeContext=new AudioContext();window.bargeOsc=bargeContext.createOscillator();window.bargeDestinations=[];"
                   "bargeOsc.start();await bargeContext.resume();window.newBargeTurns=0;window.bargeOriginalEvent=window.pywebview.api.event;"
                   "window.pywebview.api.event=(name,data)=>{if(name==='live_audio_start')window.newBargeTurns++;"
                   "if(name==='stop_task')return new Promise(resolve=>{window.releaseBargeStop=()=>bargeOriginalEvent(name,data).then(resolve);});"
                   "return bargeOriginalEvent(name,data);};"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=bargeContext.createMediaStreamDestination();bargeDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                js("document.getElementById('inp').value='Native barge waiting';document.getElementById('send').click();return true;")
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return document.getElementById('send').disabled && m.liveMic.waitingForSpeech;"))
                js("bargeOsc.connect(bargeDestinations.at(-1));return true;")
                wait_until(lambda: window.evaluate_js("typeof window.releaseBargeStop==='function'"))
                assert api._chat.busy and window.evaluate_js('window.newBargeTurns') == 0
                js("document.getElementById('disc').click();releaseBargeStop();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert window.evaluate_js('window.newBargeTurns') == 0
                assert window.evaluate_js("bargeDestinations.every(d=>d.stream.getTracks().every(t=>t.readyState==='ended'))")
                js("window.pywebview.api.event=bargeOriginalEvent;bargeOsc.stop();await bargeContext.close();return true;")
                outcome['barge_in_waited_for_real_completion_disconnect_dropped_buffer'] = True
                mic_packets = len(live_state['sent'])
                js("Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{throw new Error('Synthetic denied');}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'permission denied' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert not window.evaluate_js("document.getElementById('send').disabled")
                assert window.evaluate_js("document.getElementById('micB').classList.contains('on')")
                js("window.cancelMicContext=new AudioContext();window.cancelMicDestinations=[];"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=cancelMicContext.createMediaStreamDestination();cancelMicDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("cancelMicDestinations[0].stream.getTracks().every(t=>t.readyState==='ended')")
                assert window.evaluate_js("cancelMicDestinations.at(-1).stream.getTracks().every(t=>t.readyState==='live')")
                assert not any('tool_response' in p for p in live_state['sent'][mic_packets:])
                js("testMicOff();await cancelMicContext.close();return true;")
                outcome['microphone_permission_denied_and_stop_discard'] = True
                # Automatic listing should not call getUserMedia; permission courtesy of Mic.
                js("window.deviceContext=new AudioContext();window.deviceStream=deviceContext.createMediaStreamDestination().stream;"
                   "window.deviceList=[{kind:'audioinput',deviceId:'12345',label:'Synthetic microphone'},"
                   "{kind:'audiooutput',deviceId:'missing-test-output',label:'Synthetic speaker'}];"
                   "Object.defineProperty(navigator.mediaDevices,'enumerateDevices',{configurable:true,value:async()=>deviceList});"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async(options)=>{window.lastMicOptions=options;return deviceStream;}});"
                   "const p=await import('./js/panels.js');p.openM('mSet');return true;")
                wait_until(lambda: 'Audio and camera devices listed' in window.evaluate_js("document.getElementById('devMsg').textContent"))
                wait_until(lambda: window.evaluate_js("Array.from(document.getElementById('dIn').options).some(o=>o.value==='12345')"))
                assert window.evaluate_js("window.lastMicOptions===undefined && deviceStream.getTracks().every(t=>t.readyState==='live')")
                js("document.getElementById('dIn').value='12345';document.getElementById('dIn').onchange();"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("lastMicOptions.audio.deviceId.exact==='12345'")
                js("window.deviceList=deviceList.filter(d=>d.kind!=='audioinput');navigator.mediaDevices.dispatchEvent(new Event('devicechange'));return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Selected microphone was removed' in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert window.evaluate_js("document.getElementById('micB').textContent").strip() == 'Microphone On'
                assert window.evaluate_js("deviceStream.getTracks().every(t=>t.readyState==='ended')")
                assert not window.evaluate_js("document.getElementById('send').disabled")
                wait_until(lambda: 'Saved device unavailable' in window.evaluate_js("document.getElementById('dIn').selectedOptions[0].textContent"))
                js("document.getElementById('dIn').value='default';document.getElementById('dIn').onchange();"
                   "document.getElementById('dOut').value='missing-test-output';document.getElementById('dOut').onchange();"
                   "const s=await import('./js/settings.js');return await s.saveSettingsConfirmed();")
                assert api._store.read()['devs']['dIn'] == 'default'
                assert api._store.read()['devs']['dOut'] == 'missing-test-output'
                # Non-existent sink should be rejected in true Web Audio; text
                # It should not be played silently at another output while preserving the result.
                js("document.getElementById('inp').value='Native audio muted';document.getElementById('send').click();return true;")
                wait_until(lambda: 'Selected speaker unavailable' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Native audio muted reply' in window.evaluate_js("document.getElementById('msgs').textContent")
                before_route_stop = len(live_state['sent'])
                js("window.originalSink=AudioContext.prototype.setSinkId;"
                   "AudioContext.prototype.setSinkId=function(){window.routeWaiting=true;return new Promise(()=>{});};"
                   "document.getElementById('dOut').append(new Option('Pending synthetic sink','pending-test-output'));"
                   "document.getElementById('dOut').value='pending-test-output';document.getElementById('dOut').onchange();"
                   "document.getElementById('inp').value='Do not send during sink setup';document.getElementById('send').click();return true;")
                wait_until(lambda: window.evaluate_js("window.routeWaiting===true"))
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Stopped' in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert len(live_state['sent']) == before_route_stop
                js("if(originalSink)AudioContext.prototype.setSinkId=originalSink;else delete AudioContext.prototype.setSinkId;return true;")
                outcome['stop_during_output_setup_did_not_send_model_request'] = True
                js("document.getElementById('dOut').value='default';document.getElementById('dOut').onchange();return true;")
                # Actual API call to default sink; The physical device does not change.
                outcome['web_audio_custom_output_supported'] = js("const c=new AudioContext();let supported=typeof c.setSinkId==='function';"
                          "if(supported)await c.setSinkId('');await c.close();return supported;")
                js("await deviceContext.close();return true;")
                outcome['audio_device_scan_exact_input_missing_sink_and_persistence'] = True
                # Real profile form -> verified disk -> REST/Live SDK setup.
                # The answers are synthetic; It is not claimed that he speaks the correct language.
                js("const p=await import('./js/panels.js');p.openM('mProf');"
                   "document.getElementById('pLang').value='en';document.getElementById('pIns').value='Native preference probe';"
                   "document.getElementById('pMem').value='Native unused memory';document.getElementById('btnSaveProf').click();return true;")
                wait_until(lambda: api._store.read().get('prof', {}).get('pIns') == 'Native preference probe')
                wait_until(lambda: not window.evaluate_js("document.getElementById('mProf').classList.contains('o')"))
                js("document.getElementById('liveLatencyTest').checked=false;document.getElementById('inp').value='Native profile probe';"
                   "document.getElementById('send').click();return true;")
                wait_until(lambda: 'Native profile probe REST' in window.evaluate_js("document.getElementById('msgs').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                rest_instruction = ''.join(p['text'] for p in text_payloads[-1]['systemInstruction']['parts'])
                assert 'English (en)' in rest_instruction and 'Native preference probe' in rest_instruction
                assert 'Native unused memory' not in rest_instruction
                js("document.getElementById('liveLatencyTest').checked=true;document.getElementById('inp').value='Native profile probe';"
                   "document.getElementById('send').click();return true;")
                wait_until(lambda: 'Native profile probe Live' in window.evaluate_js("document.getElementById('msgs').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                live_instruction = ''.join(p['text'] for p in [m['setup'] for m in live_state['sent'] if 'setup' in m][-1]['systemInstruction']['parts'])
                assert rest_instruction == live_instruction
                old_profile_session = api._chat._live._connection.logical_id
                old_opened = live_state['opened']
                js("const p=await import('./js/panels.js');p.openM('mProf');"
                   "document.getElementById('pLang').value='tr';document.getElementById('pIns').value='Native new preference';"
                   "document.getElementById('btnSaveProf').click();return true;")
                wait_until(lambda: api._store.read().get('prof', {}).get('pLang') == 'tr')
                wait_until(lambda: not window.evaluate_js("document.getElementById('mProf').classList.contains('o')"))
                js("document.getElementById('inp').value='Native profile probe';document.getElementById('send').click();return true;")
                wait_until(lambda: live_state['opened'] == old_opened + 1)
                wait_until(lambda: not api._chat.busy and not window.evaluate_js("document.getElementById('send').disabled"))
                profile_setup = [m['setup'] for m in live_state['sent'] if 'setup' in m][-1]
                instruction = ''.join(p['text'] for p in profile_setup['systemInstruction']['parts'])
                assert 'Turkish (tr)' in instruction and 'Native new preference' in instruction
                assert 'handle' not in profile_setup['sessionResumption']
                assert api._chat._live._connection.logical_id != old_profile_session
                assert 'scope_changed' in window.evaluate_js("document.getElementById('textStatus').textContent")
                outcome['saved_profile_form_shared_rest_live_instruction_and_scope_reset'] = True
                # New Chat button has been removed. Temporary memory is maintained in Stop;
                # When the persistent memory preference changes, the old context is not transferred.
                js("testMicOff();document.getElementById('inp').value='Native temporary name is Ada';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                preserved_notes = (home / 'notes.json').read_bytes()
                js("document.getElementById('inp').value='Native Stop';document.getElementById('send').click();return true;")
                wait_until(lambda: api._chat.busy)
                assert window.evaluate_js("document.getElementById('newChat')===null")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                js("document.getElementById('inp').value='Native memory ask';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Native remembered name: Ada' in window.evaluate_js("document.getElementById('msgs').textContent")
                assert 'recent conversation restored' in window.evaluate_js("document.getElementById('textStatus').textContent")
                js("const p=await import('./js/panels.js');p.openM('mProf');"
                   "document.getElementById('pMem').value='Native saved school';"
                   "document.getElementById('pMemory').checked=true;document.getElementById('btnSaveProf').click();return true;")
                wait_until(lambda: api._store.read().get('prof', {}).get('pMemory') is True)
                wait_until(lambda: not window.evaluate_js("document.getElementById('mProf').classList.contains('o')"))
                assert (home / 'notes.json').read_bytes() == preserved_notes
                js("document.getElementById('inp').value='Native memory ask';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Native remembered name: unknown' in window.evaluate_js("document.getElementById('msgs').textContent")
                memory_setup = [m['setup'] for m in live_state['sent'] if 'setup' in m][-1]
                assert 'Native saved school' in json.dumps(memory_setup['systemInstruction'])
                js("document.getElementById('inp').value='Native remember job';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert api._store.read()['prof']['pMem'] == 'Native saved school\nNative saved job'
                assert window.evaluate_js("document.getElementById('pMem').value") == 'Native saved school\nNative saved job'
                assert window.evaluate_js("JSON.parse(localStorage.getItem('taskvex_ui')).prof.pMem") == 'Native saved school\nNative saved job'
                outcome['model_memory_verified_and_ui_refreshed'] = True
                js("const p=await import('./js/panels.js');p.openM('mProf');document.getElementById('pLearn').checked=true;document.getElementById('btnSaveProf').click();return true;")
                wait_until(lambda: api._store.read()['prof'].get('pLearn') is True)
                wait_until(lambda: not window.evaluate_js("document.getElementById('mProf').classList.contains('o')"))
                memory_before=api._store.read()['prof']['pMem']
                js("document.getElementById('inp').value='Native self report Ada';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert api._store.read()['prof']['pMem']==memory_before
                wait_until(lambda: window.evaluate_js("!document.getElementById('memoryProposal').hidden"))
                assert not window.evaluate_js("document.getElementById('mProf').classList.contains('o')")
                assert 'Native self report Ada' in window.evaluate_js("document.getElementById('memoryProposalSource').textContent")
                assert 'Paraphrased source' not in window.evaluate_js("document.getElementById('memoryProposalSource').textContent")
                js("document.getElementById('memoryAccept').click();return true;")
                wait_until(lambda: api._store.read()['prof']['pMem']==memory_before+'\nUser name Ada')
                wait_until(lambda: window.evaluate_js("document.getElementById('memoryProposal').hidden"))
                assert window.evaluate_js("document.getElementById('pMem').value")==memory_before+'\nUser name Ada'
                js("const p=await import('./js/panels.js');p.closeM('mProf');document.getElementById('inp').value='Native self report Beta';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                js("document.getElementById('memoryDismiss').click();return true;")
                wait_until(lambda: window.evaluate_js("document.getElementById('memoryProposal').hidden"))
                assert api._store.read()['prof']['pMem']==memory_before+'\nUser name Ada'
                outcome['memory_suggestion_requires_actual_ui_approval_and_dismiss_preserves_profile']=True
                js("document.getElementById('inp').value='Native self report Delta';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert not window.evaluate_js("document.getElementById('memoryProposal').hidden")
                js("document.getElementById('inp').value='Native approve memory';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert api._store.read()['prof']['pMem']==memory_before+'\nUser name Ada\nUser name Delta'
                wait_until(lambda: window.evaluate_js("document.getElementById('memoryProposal').hidden"))
                outcome['model_answer_and_ui_use_same_memory_decision']=True
                js("const p=await import('./js/panels.js');p.openM('mProf');document.getElementById('pMemoryConfirm').checked=false;document.getElementById('btnSaveProf').click();return true;")
                wait_until(lambda: api._store.read()['prof'].get('pMemoryConfirm') is False)
                wait_until(lambda: not window.evaluate_js("document.getElementById('mProf').classList.contains('o')"))
                js("document.getElementById('inp').value='Native self report Gamma';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert api._store.read()['prof']['pMem']==memory_before+'\nUser name Ada\nUser name Delta\nUser name Gamma'
                assert window.evaluate_js("document.getElementById('pMem').value")==memory_before+'\nUser name Ada\nUser name Delta\nUser name Gamma'
                assert not window.evaluate_js("document.getElementById('mProf').classList.contains('o')")
                assert window.evaluate_js("document.getElementById('memoryProposal').hidden")
                outcome['memory_ask_choice_shows_inline_review_or_saves_directly']=True


                js("const p=await import('./js/panels.js');p.openM('mProf');"
                   "document.getElementById('pMem').value='';document.getElementById('pMemory').checked=false;"
                   "document.getElementById('btnSaveProf').click();return true;")
                wait_until(lambda: api._store.read().get('prof', {}).get('pMem') == '')
                wait_until(lambda: not window.evaluate_js("document.getElementById('mProf').classList.contains('o')"))
                outcome['personal_memory_form_opt_in_and_temporary_context_cleared'] = True
                check_local_sleep(window, api, js, wait_until, live_state, wake_state, outcome)
                check_native_note_batches(api, home, window, js, wait_until, outcome)
                check_native_shutdown_request(window, api, js, wait_until, outcome)
                check_native_clocks(window, api, js, wait_until, outcome)
                js("const a=await import('./js/api.js');for(let i=0;i<250;i++)a.addLog('Native bounded entry '+i);return true;")
                assert window.evaluate_js("document.getElementById('log').childElementCount") == 200
                outcome['engine_log_bounded_to_200_entries'] = True
                tokens_before_disconnect=window.evaluate_js("document.getElementById('tokTxt').textContent")
                js("document.getElementById('disc').click();return true;")
                # Socket shuts down before clearing loop/thread. Intermediate status
                # Don't think it's the end; Wait until the host releases all resources.
                wait_until(lambda: live_state["closed"] and api._chat._live._thread is None)
                assert api._chat._live._thread is None
                assert window.evaluate_js("document.getElementById('tokTxt').textContent")==tokens_before_disconnect
                assert '%' in window.evaluate_js("document.getElementById('ram').textContent")
                outcome['offline_preserves_local_metrics_and_session_tokens']=True
                original_run_live = api._chat.run_live
                api._chat.run_live = lambda text, model, **kwargs: {
                    **original_run_live(text, model, **kwargs), 'ok':False, 'unknown':True}
                js("window.unknownContext=new AudioContext();window.unknownOsc=unknownContext.createOscillator();window.unknownDestinations=[];"
                   "unknownOsc.start();await unknownContext.resume();window.unknownNewTurns=0;window.unknownOriginalEvent=window.pywebview.api.event;"
                   "window.pywebview.api.event=(name,data)=>{if(name==='live_audio_start')window.unknownNewTurns++;return unknownOriginalEvent(name,data);};"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=unknownContext.createMediaStreamDestination();unknownDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                js("document.getElementById('inp').value='Native barge waiting';document.getElementById('send').click();return true;")
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return document.getElementById('send').disabled && m.liveMic.waitingForSpeech;"))
                js("unknownOsc.connect(unknownDestinations.at(-1));return true;")
                wait_until(lambda: "Result unknown" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("document.getElementById('send').disabled && document.getElementById('noteAdd').disabled")
                assert window.evaluate_js('window.unknownNewTurns') == 0
                assert window.evaluate_js("unknownDestinations.every(d=>d.stream.getTracks().every(t=>t.readyState==='ended'))")
                assert window.evaluate_js("document.getElementById('micB').getAttribute('aria-pressed')==='true'")
                js("testMicOff();document.getElementById('micB').click();return true;")
                assert js("const m=await import('./js/live_mic.js');return !m.liveMic.active && document.getElementById('send').disabled;")
                assert window.evaluate_js('window.unknownNewTurns') == 0
                js("window.pywebview.api.event=unknownOriginalEvent;unknownOsc.stop();await unknownContext.close();return true;")
                api._chat.run_live = original_run_live
                outcome['barge_in_unknown_result_dropped_buffer_and_locked_controls'] = True
                outcome.update(ok=True, phase=phase, native=initial, native_chat=True, fallback=True,
                               single_note=True, safe_dom=True, concurrent_rejected=True,
                               bridge_responsive=True, failure_preserved_input=True,
                               model_change_not_online=True, unknown_locked=True, chat_before_notes_confirmation=True,
                               dynamic_live_catalog=True, text_model_separate=True, safe_http_diagnostics=True,
                               live_latency_probe=True, live_no_rest_fallback=True, live_plain_chat_notes_unchanged=True,
                               live_tool_saved=True, live_tool_panel_refreshed=True, live_tool_replay_single_write=True,
                               live_stop_button=True, live_stop_preserved_notes=True, live_stop_next_session_fresh=True,
                               rest_stop_button=True, rest_stop_waited_for_http=True, rest_stop_blocked_late_tool=True,
                               live_goaway_resumed=True, live_resume_scope_preserved=True, live_resume_token_hidden=True,
                               live_session_reused=True, disconnect_closed_live_io=True)
                outcome.update(live_pcm_forwarded=True, live_mute=True, playback_stop_after_model_done=True,
                               audio_drain_before_unlock=True, stale_audio_ignored=True, audio_stale_online_ignored=True)
                return
            if phase == "credentials":
                from app.storage import credentials
                import ctypes as c
                from ctypes import wintypes as w

                store = api._credentials
                assert store.read() is None, "Synthetic profile must not contain an existing credential"
                try:
                    assert key_query_started.wait(5)
                    js("window.keyEvents=[];"
                       "window.vex.onEvent=(name,data)=>{if(name==='apikey')window.keyEvents.push(data);};"
                       "document.getElementById('apiKeyIn').value='TASKVEX_SYNTHETIC_KEY';"
                       "document.getElementById('saveApiKey').click();return true;")
                    wait_until(lambda: store.read() == "TASKVEX_SYNTHETIC_KEY")
                    wait_until(lambda: "Key stored locally" in window.evaluate_js("document.getElementById('apiKeyStatus').textContent"))
                    state = js("const settings=await import('./js/settings.js');return {"
                               "empty:document.getElementById('apiKeyIn').value==='',"
                               "secretAbsent:!JSON.stringify([localStorage,settings.store]).includes('TASKVEX_SYNTHETIC_KEY'),"
                               "observer:window.keyEvents,online:document.getElementById('netP').textContent,"
                               "pending:Object.keys(window.pywebview._returnValuesCallbacks.event)};")
                    assert state["empty"] and state["secretAbsent"] and state["observer"] == ["[REDACTED]"]
                    assert js("return document.getElementById('apiKeyIn').placeholder.startsWith('API key configured');")
                    outcome['key_placeholder_configured_without_secret'] = True
                    assert "OFFLINE" in state["online"]
                    assert state["pending"]
                    release_key_query.set()
                    # PyWebView 6.2.1 deregistering callback converts response to JS
                    # proves that it has been achieved; It is not necessary to have an observer at the beginning.
                    wait_until(lambda: window.evaluate_js(json.dumps(state["pending"]) +
                               ".every(id=>!(id in window.pywebview._returnValuesCallbacks.event))"))
                    assert "Key stored locally" in window.evaluate_js("document.getElementById('apiKeyStatus').textContent")
                    assert api.event("query_apikey") == {"ok": True, "completed": True, "configured": True}
                    environment = dict(os.environ)
                    environment.pop("GEMINI_API_KEY", None)
                    checked = subprocess.run([sys.executable, "-c",
                        "from app.storage.credentials import load_gemini_key; "
                        "print(load_gemini_key() == 'TASKVEX_SYNTHETIC_KEY')"],
                        env=environment, capture_output=True, text=True, timeout=15)
                    assert checked.returncode == 0 and checked.stdout.strip() == "True"

                    original_write = store.write
                    def fail_key(value):
                        raise credentials.CredentialError("TASKVEX_SYNTHETIC_FAILURE_SECRET")
                    store.write = fail_key
                    js("document.getElementById('apiKeyIn').value='TASKVEX_SYNTHETIC_FAILURE_SECRET';"
                       "document.getElementById('saveApiKey').click();return true;")
                    wait_until(lambda: "Key save was not confirmed" in window.evaluate_js("document.getElementById('apiKeyStatus').textContent"))
                    assert store.read() == "TASKVEX_SYNTHETIC_KEY"
                    store.write = original_write
                    safe = js("const api=await import('./js/api.js');"
                              "const original=window.pywebview.api.event;let result;"
                              "try{window.pywebview.api.event=async()=>{throw new Error('TASKVEX_SYNTHETIC_FAILURE_SECRET');};"
                              "result=await api.emit('apikey','TASKVEX_SYNTHETIC_FAILURE_SECRET');}"
                              "finally{window.pywebview.api.event=original;}"
                              "return {ok:result.ok,response:result.response,log:document.getElementById('log').textContent};")
                    assert safe["ok"] is False and safe["response"] is None
                    assert "TASKVEX_SYNTHETIC_FAILURE_SECRET" not in safe["log"]
                    fallback = js("const api=await import('./js/api.js');const original=window.pywebview;"
                                  "let result;window.keyEvents=[];try{window.pywebview=null;"
                                  "result=await api.emit('apikey','TASKVEX_SYNTHETIC_FAILURE_SECRET');}"
                                  "finally{window.pywebview=original;}return {ok:result.ok,events:window.keyEvents};")
                    assert fallback == {"ok": False, "events": []}
                    outcome.update(ok=True, phase=phase, credential_write_read=True,
                                   cross_process_load=True, input_cleared=True, no_key_in_local_storage=True,
                                   observer_redacted=True, native_error_redacted=True,
                                   browser_fallback_blocked=True, failure_preserved_old_key=True,
                                   save_did_not_mark_online=True, stale_status_ignored=True)
                finally:
                    release_key_query.set()
                    # Just clear the synthetic record of this temporary profile.
                    library = credentials._library()
                    library.CredDeleteW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD]
                    library.CredDeleteW.restype = w.BOOL
                    deleted = library.CredDeleteW(store._target, 1, 0)
                    assert deleted or c.get_last_error() == 1168
                return
            if phase == "save":
                wait_until(lambda: window.evaluate_js("document.getElementById('notesConnect').textContent==='Use backend notes'"))
                assert not (home / "notes.json").exists()
                js("window.confirm=()=>false;document.getElementById('notesConnect').click();return true;")
                assert not (home / "notes.json").exists()
                js("window.confirm=()=>true;document.getElementById('notesConnect').click();return true;")
            wait_until(lambda: api._notes_ready)
            wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
            if phase == "notes":
                check_native_note_ui(home, window, js, wait_until, outcome)
                return
            if phase == "export_cancel":
                original_export = (home / "exported-backup.json").read_bytes()
                assert export_backup(False) is None
                assert (home / "exported-backup.json").read_bytes() == original_export
                assert "download requested" in window.evaluate_js("document.getElementById('saveStatus').textContent").lower()
                outcome.update(ok=True, phase=phase, export_cancel_preserved_file=True)
                return
            if phase == "persistence":
                queue = js("const s=await import('./js/settings.js'); const original=window.pywebview.api.event;"
                           "window.vex.onSave=snapshot=>{snapshot.theme='#000000';};"
                           "let active=0,maxActive=0;const themes=[];"
                           "window.pywebview.api.event=async(name,data)=>{if(name!=='save')return original(name,data);"
                           "active++;maxActive=Math.max(active,maxActive);themes.push(data.theme);"
                           "try{await new Promise(r=>setTimeout(r,30));return await original(name,data);}finally{active--;}};"
                           "try{s.store.theme='#4fd8ff';s.saveAll();s.store.theme='#5dffb0';s.saveAll();"
                           "return {ok:await s.saveSettingsConfirmed(),maxActive,themes};}finally{window.pywebview.api.event=original;window.vex.onSave=null;}")
                assert queue == {"ok": True, "maxActive": 1, "themes": ["#4fd8ff", "#5dffb0", "#5dffb0"]}, queue
                assert api._store.read()["theme"] == "#5dffb0"
                backup = {"theme": "#5dffb0", "notes": ["Native local note", "Imported note"],
                          "skills": [{"id": "import-skill", "name": "Imported skill", "steps": []}],
                          "routines": [{"id": "import-routine", "name": "Imported routine", "type": "manual", "steps": "Keep step", "on": 0}]}
                ui_import = js("const input=document.getElementById('impF');const transfer=new DataTransfer();"
                               "window.alert=message=>{window._importAlert=message;};"
                               "transfer.items.add(new File([JSON.stringify(" + json.dumps(backup) + ")],'backup.json',{type:'application/json'}));"
                               "input.files=transfer.files;input.dispatchEvent(new Event('change'));"
                               "for(let n=0;n<100&&input.value;n++)await new Promise(r=>setTimeout(r,30));"
                               "const s=await import('./js/settings.js');return {alert:window._importAlert||null,notes:s.store.notes,skills:s.store.skills.length};")
                assert ui_import["alert"] is None and ui_import["skills"] == 1, ui_import
                assert [note["t"] for note in ui_import["notes"]] == ["Native local note", "Imported note"]
                before = js("const s=await import('./js/settings.js');return JSON.stringify(s.store);")
                raw = api._store.path.read_bytes()
                original_write = api._store.write

                def fail(data):
                    raise StoreError("write_failed", "Simulated native save failure")

                api._store.write = fail
                assert js("const s=await import('./js/settings.js');return await s.importBackup({theme:'#ff5d5d',notes:['Must not apply']});") is False
                assert js("const s=await import('./js/settings.js');return JSON.stringify(s.store);") == before
                assert api._store.path.read_bytes() == raw
                api._store.write = original_write
                assert js("const s=await import('./js/settings.js');return await s.importBackup({notes:[null]});") is False
                partial = js("const s=await import('./js/settings.js');const raw=localStorage.getItem('taskvex_ui');"
                             "const original=Storage.prototype.setItem;let writes=0;"
                             "Storage.prototype.setItem=function(key,value){if(key==='taskvex_ui'&&++writes>=2)throw new DOMException('Full','QuotaExceededError');return original.call(this,key,value);};"
                             "try{return {ok:await s.importBackup({theme:'#4fd8ff',notes:['Must not replace local notes']}),"
                             "sameLocal:localStorage.getItem('taskvex_ui')===raw,notes:s.store.notes,theme:s.store.theme};}"
                             "finally{Storage.prototype.setItem=original;}")
                assert partial["ok"] is False and partial["sameLocal"] is True, partial
                assert partial["theme"] == "#5dffb0" and [n['t'] for n in partial['notes']] == ['Must not replace local notes']
                assert api._store.read()["theme"] == "#4fd8ff"
                # Hiding partial success of individual repositories; with next open Save
                # We set the local current settings of the test equal to native again.
                assert js("const s=await import('./js/settings.js');return await s.saveSettingsConfirmed();") is True

                # The actual export -> import path should not drop metadata in any intermediate transformations.
                dated = {"t": "Timestamp backup", "d": 0, "id": "dated-backup",
                         "created_at": "2024-02-29T12:34:56.789Z"}
                assert js("const s=await import('./js/settings.js');return await s.importBackup(" +
                          json.dumps({"notes": [dated]}) + ");") is True
                dated_export = export_backup(True)
                assert dated_export is not None
                assert dated_export["notes"] == [dated] and dated_export["theme"] == "#5dffb0"
                assert json.loads((home / "notes.json").read_text("utf-8"))["data"]["notes"][0]["created_at"] == dated["created_at"]
                original_notes = (home / "notes.json").read_bytes()
                assert js("const s=await import('./js/settings.js');return await s.importBackup({theme:'#000000',"
                          "notes:[{t:'Invalid timestamp',d:0,created_at:'yesterday'}]});") is False
                assert (home / "notes.json").read_bytes() == original_notes
                # With true core restore for subsequent boot/recovery phases
                # return starting note; The old setter does not have writing.
                assert js("const n=await import('./js/notes.js');return await n.restoreNativeNotes([{t:'Native local note',d:0}]);") is True
                timeout = js("const s=await import('./js/settings.js');const original=window.pywebview.api.event;"
                             "let sent=0,resolveSave;window.pywebview.api.event=(name,data)=>name==='save'?(sent++,new Promise(r=>resolveSave=r)):original(name,data);"
                             "try{const ok=await s.saveSettingsConfirmed();resolveSave({ok:true,completed:true,saved:true});"
                             "await new Promise(r=>setTimeout(r,10));return {ok,sent,status:document.getElementById('saveStatus').textContent};}"
                             "finally{window.pywebview.api.event=original;}")
                assert timeout == {"ok": False, "sent": 1, "status": "Settings save not confirmed"}, timeout
                outcome.update(ok=True, phase=phase, ordered_save_queue=True, file_input_import=True,
                               native_rejection_preserved_ui=True, local_quota_rollback=True,
                               partial_commit_reported=True, actual_export_file=True, note_time_backup_roundtrip=True,
                               observer_cannot_mutate_save=True, timeout_no_repeat=True)
                return
            if phase == "save":
                controls = js("const settings=await import('./js/settings.js');"
                              "const context=new AudioContext(); await context.resume();"
                              "const audio=context.state; await context.close();"
                              "document.getElementById('inp').dispatchEvent(new KeyboardEvent('keydown',"
                              "{key:'F11',bubbles:true,cancelable:true}));"
                              "return {theme:settings.store.theme,audio};")
                assert controls == {"theme": "#a78bfa", "audio": "running"}, controls
                wait_until(lambda: captured["window"].native.is_fullscreen)
                js("document.getElementById('inp').dispatchEvent(new KeyboardEvent('keydown',"
                   "{key:'F11',repeat:true,bubbles:true,cancelable:true})); return true;")
                assert window.native.is_fullscreen
                js("document.getElementById('inp').dispatchEvent(new KeyboardEvent('keydown',"
                   "{key:'F11',bubbles:true,cancelable:true})); return true;")
                wait_until(lambda: not window.native.is_fullscreen)
                outcome.update(default_purple=True, audio_without_gesture=True, f11_toggle=True)
                assert js("const {liveAudio}=await import('./js/live_audio.js');"
                          "if(liveAudio.volume!==1) return false;"
                          "const r=document.getElementById('replyVolR');r.value='35';"
                          "r.dispatchEvent(new Event('input'));r.dispatchEvent(new Event('change'));"
                          "return liveAudio.volume===0.35;")
                wait_until(lambda: (api._store.read() or {}).get('replyVolume') == 0.35)
                outcome['reply_volume_native_saved'] = True
                assert js("const v=document.getElementById('vSel');"
                          "if(v.disabled || v.options.length!==30 || ![...v.options].every(o=>o.textContent.startsWith('[LIVE] ')))return false;"
                          "v.value='Kore';v.dispatchEvent(new Event('change'));return true;")
                wait_until(lambda: (api._store.read() or {}).get('conn', {}).get('voice') == 'Kore')
                outcome['live_only_voices_selected_and_saved'] = True
                assert js("const n=await import('./js/notes.js');if(!(await n.addNote('Native local note')))throw new Error('Note add failed');"
                          "window._events=[]; window.vex.onEvent=(name)=>window._events.push(name);"
                          "window.vex.setSkills([{id:'keep-skill',name:'Keep skill',steps:[]}]);"
                          "window.vex.setRoutines([{id:'keep-routine',name:'Keep routine',type:'manual',steps:'Keep step',on:0}]);"
                          "return window.vex.loadStore({theme:'#4fd8ff',prof:{pIns:'Native profile 📝',pMemory:true,pMem:'Native saved memory',pMemoryConfirm:false},"
                          "devs:{dIn:'7'},conn:{model:'gemini-3.8-flash',voice:'Kore'}});") is True
                assert js("return window._events.includes('save');") is False
                js("const checkbox=document.getElementById('onTop'); checkbox.checked=true;"
                   "checkbox.dispatchEvent(new Event('change')); return true;")
                wait_until(lambda: window.native.TopMost)
                js("const panels=await import('./js/panels.js'); panels.openM('mSet');"
                   "document.getElementById('btnSaveSet').click(); return true;")
                wait_until(lambda: (api._store.read() or {}).get("theme") == "#4fd8ff")
                wait_until(lambda: not window.evaluate_js("document.getElementById('mSet').classList.contains('o')"))
                saved = api._store.read()
                assert saved["prof"]["pIns"] == "Native profile 📝"
                assert "notes" not in saved
                assert saved["onTop"] is True
                previous = api._store.path.read_bytes()
                invalid = js("return await window.pywebview.api.event('save',{vol:9});")
                assert invalid["ok"] is False and api._store.path.read_bytes() == previous
                unsupported = js("return await window.pywebview.api.event('text','hello');")
                assert unsupported["ok"] is False
                outcome.update(settings_saved=True, invalid_save_preserved=True,
                               unsupported_rejected=True, snapshot_no_echo=True, native_on_top=True)
            else:
                restored = js("const settings=await import('./js/settings.js');"
                              "return {theme:settings.store.theme,profile:settings.store.prof.pIns,"
                              "notes:window.document.getElementById('notesL')?.textContent||"
                              "JSON.stringify(settings.store.notes)};")
                assert restored["theme"] == "#4fd8ff", restored
                assert restored["profile"] == "Native profile 📝", restored
                assert js("return document.getElementById('pMemory').checked && document.getElementById('pMem').value==='Native saved memory';")
                assert js("return !document.getElementById('pMemoryConfirm').checked;")
                outcome['memory_review_choice_cross_process_restored'] = True
                outcome['personal_memory_cross_process_restored'] = True
                assert js("const {liveAudio}=await import('./js/live_audio.js');"
                          "return liveAudio.volume===0.35 && document.getElementById('replyVolR').value==='35';")
                outcome['reply_volume_cross_process_restored'] = True
                assert js("return document.getElementById('vSel').value==='Kore';")
                outcome['live_voice_cross_process_restored'] = True
                assert "Native local note" in restored["notes"], restored
                assert window.native.TopMost
                outcome["on_top_restored"] = True

                original_write = api._store.write
                def fail(data):
                    raise StoreError("write_failed", "Simulated test failure")

                api._store.write = fail
                js("const panels=await import('./js/panels.js'); panels.openM('mSet');"
                   "document.getElementById('btnSaveSet').click(); return true;")
                wait_until(lambda: "Failed to send save" in window.evaluate_js("document.getElementById('log').textContent"))
                assert window.evaluate_js("document.getElementById('mSet').classList.contains('o')")
                outcome.update(reopened_settings=True, local_note_preserved=True, failed_save_modal_open=True)
                before_reset = js("const settings=await import('./js/settings.js');"
                                  "return JSON.stringify([settings.store.notes,settings.store.skills,settings.store.routines,"
                                  "settings.store.prof,settings.store.devs,settings.store.conn]);")
                js("window.confirm=()=>true; document.getElementById('resetAll').click(); return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('resetAll').disabled"))
                assert api._store.read()["theme"] == "#4fd8ff" and window.native.TopMost
                api._store.write = original_write
                js("document.getElementById('resetAll').click(); return true;")
                wait_until(lambda: (api._store.read() or {}).get("theme") == "#a78bfa")
                wait_until(lambda: not window.evaluate_js("document.getElementById('resetAll').disabled"))
                after_reset = js("const settings=await import('./js/settings.js');"
                                 "return {theme:settings.store.theme,kept:JSON.stringify([settings.store.notes,"
                                 "settings.store.skills,settings.store.routines,settings.store.prof,settings.store.devs,settings.store.conn])};")
                assert after_reset["theme"] == "#a78bfa" and after_reset["kept"] == before_reset, (after_reset, before_reset)
                assert js("const {liveAudio}=await import('./js/live_audio.js');"
                          "return liveAudio.volume===1 && document.getElementById('replyVolR').value==='100';")
                assert api._store.read()['replyVolume'] == 1
                outcome['reply_volume_reset_to_default'] = True
                assert not window.native.TopMost
                outcome.update(reset_preserved_collections_profile=True, reset_failure_preserved_preferences=True)
            outcome.update(ok=True, phase=phase, native=initial)
            if phase == "save":
                # Native restart actually shuts down window/core. new process
                # we capture the rendering; The successor actual process opens the main process of the test.
                def launch(command, **kwargs):
                    assert not api._core._worker.is_alive()
                    launches.append(command)

                subprocess.Popen = launch
                window.run_js("document.getElementById('restartApp').click()")
                assert window.events.closed.wait(10), "Restart did not close the native window"
                outcome["native_restart_closed"] = True
            else:
                # The actual Shutdown button should destroy the window; Restart screen
                # The process that is shown and remains open cannot exceed this wait.
                window.run_js("document.getElementById('shut').click()")
                assert window.events.closed.wait(10), "Shutdown did not close the native window"
                outcome["native_shutdown"] = True
        except Exception as error:
            outcome.update(ok=False, phase=phase, error=repr(error), trace=traceback.format_exc())
            outcome['wake_state'] = {'sleeping':api._sleeping, 'pending_hit':api._wake_detected,
                                     'sequence':getattr(api._wake,'_sequence',None)}
            outcome["diagnostic"] = window.evaluate_js("({shutdownErrors:window.shutdownErrors,model:document.getElementById('mSel')?.value,live:document.getElementById('liveLatencyTest')?.checked,mic:document.getElementById('micB')?.getAttribute('aria-pressed'),sendDisabled:document.getElementById('send')?.disabled,text:document.getElementById('textStatus')?.textContent,notes:document.getElementById('notesStatus')?.textContent,log:document.getElementById('log')?.textContent,ready:!!window.vex,bridge:typeof window.pywebview?.api?.event})")
            outcome["notes_file"] = (home / "notes.json").read_text("utf-8") if (home / "notes.json").exists() else None
        finally:
            (home / f"report-{phase}.json").write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
            if not window.events.closed.is_set():
                window.destroy()

    def start(**kwargs):
        original_start(func=exercise, **kwargs)

    webview.create_window, webview.start = create, start
    sys.argv = ["taskvex-native-smoke", *(["--debug"] if debug else [])]
    main()
    faulthandler.cancel_dump_traceback_later()
    if phase == "save":
        assert launches == [[sys.executable, "-m", "app.main"]], launches
        outcome["restart_launch_requested"] = True
        (home / f"report-{phase}.json").write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
    assert outcome.get("ok"), outcome


def run() -> None:
    """Limit two separate native processes; Also write the result in the optional report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path,
                        default=Path(__file__).resolve().parents[2] / 'logs/reports/native-smoke.json')
    parser.add_argument("--phase", choices=["save", "reopen", "notes", "persistence", "export_cancel", "credentials", "chat", "unknown", "corrupt", "schema_invalid", "future"])
    parser.add_argument("--home", type=Path)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.phase:
        child(args.home, args.phase, args.debug)
        return
    reports = []
    log_home = Path(__file__).resolve().parents[2] / 'logs/raw/native'
    log_home.mkdir(parents=True, exist_ok=True)
    # Retain phase diagnostics after the temporary synthetic profile is removed.
    run_logs = Path(tempfile.mkdtemp(prefix='run-', dir=log_home))
    with tempfile.TemporaryDirectory(prefix="taskvex-native-", ignore_cleanup_errors=True) as directory:
        home = Path(directory)
        for phase in ["save", "reopen", "notes", "persistence", "export_cancel", "credentials", "chat", "unknown", "corrupt", "schema_invalid", "future"]:
            if phase == "corrupt":
                (home / "settings.json").write_bytes(b'{broken native settings')
            elif phase == "schema_invalid":
                (home / "settings.json").write_text(json.dumps({"version": 1, "data": {
                    "theme": "#4fd8ff", "vol": 9, "prof": {"pIns": "Native profile 📝"}}}), encoding="utf-8")
            elif phase == "future":
                (home / "settings.json").write_bytes(b'{"version":2,"data":{"future":true}}')
            # Windows venv launcher creates a second Python process. run()
            # Only killing the launcher can leave the pipe open; own test
            # We close our tree together at timeout and read the error record from the file.
            log = run_logs / f"{phase}.log"
            phase_home = home / (phase + '-profile') if phase in {'chat', 'unknown'} else home
            with log.open("wb") as output:
                process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--phase", phase,
                                            "--home", str(phase_home)], stdout=output, stderr=subprocess.STDOUT)
                try:
                    code = process.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   capture_output=True, timeout=15)
                    process.wait(timeout=10)
                    raise RuntimeError("Native test timed out:\n" + log.read_text("utf-8", errors="replace")[-5000:])
            path = phase_home / f"report-{phase}.json"
            report = json.loads(path.read_text("utf-8")) if path.exists() else {"ok": False, "phase": phase}
            reports.append(report)
            if code != 0 or not report.get("ok"):
                raise RuntimeError(f"{report}\n{log.read_text('utf-8', errors='replace')[-3500:]}")
    result = {"ok": True, "renderer": "edgechromium", "hidden_window": True, "phases": reports}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # Windows console may not be UTF-8; report file UTF-8, console ASCII-safe.
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    run()
