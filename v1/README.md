# TaskVex v1 development

Latest slice (step 4): saved pLang/pIns preferences build a shared REST/Live
system instruction. The native host reads a per-request disk snapshot; these
preferences grant no tool permissions. Effective instruction changes start a
fresh Live context on the next message and discard the old resume scope.
Other profile fields are not sent to the model. Native speech recognition
remains automatic; response language is guided by instruction. REST audio is
still out of scope. Step 3 was manually accepted and committed as 85648b9.

Latest slice (step 3): reply-time speech candidates require 300 ms and a
higher energy floor; detection filters DC/low frequencies and adapts to quiet
background energy. Original PCM is preserved. A waiting microphone and its
pre-roll now survive successful reply completion without reopening the device.
Stop/errors/unknown/scope changes still close resources. This remains sequential
turn handoff; active Stop can reset context. Physical echo/noise acceptance is
pending. Transcript step 2 was manually accepted and committed as 3daf152.

Current transcript slice: Live input/output text is pushed before turn completion
as request-scoped, sequenced snapshots. One bubble per role updates safely;
interrupted/failed/unknown partial text remains visible, with no final duplicate.
Final reports provide a fallback. Provider transcript timing is not word-level
audio synchronization; unsent local microphone buffers have no transcript yet.
REST and note behavior are unchanged. Real-device acceptance remains open.

Current barge-in slice: local speech detection cuts queued reply audio, asks
the existing request-scoped Stop when the model is active, waits for the real
terminal result, then submits buffered speech as a new turn. Unknown results
block handoff. Stop/Disconnect/scope changes discard pending audio; completed
tools remain committed. This is sequential turn handoff, not same-socket full
duplex; active Stop can reset conversation context. Physical echo acceptance
remains open. No real account or paid API is used by automated tests.

Current automatic listening: after native startup and loading an API Live
catalog, speak without clicking Mic. A bounded local speech gate holds up to
500 ms of pre-roll; idle silence does not open provider turns. Replies pause
input, then automatically return to listening. The header control is now
Pause/Resume listening. Stop, Disconnect and errors pause automatic listening;
there is no automatic retry after failure. Barge-in remains a separate step.
Real microphone/noise sensitivity and permission persistence still need acceptance.

Current microphone slice: explicit Mic streams 100 ms mono 16 kHz PCM through
AudioWorklet to the existing single Live owner. Server VAD ends one utterance;
input closes when the reply/tool call starts. Maximum input is 15 seconds with
bounded queues and request-scoped Stop. No always-on listening or barge-in yet.
Native synthetic checks do not prove physical microphone/provider VAD quality.
The start/finish clip description below records the previous accepted slice.

Native UI assets use a fresh path per launch and real no-store response
headers to prevent cached module/version mismatches. The HTTP origin and
WebView data profile are preserved; no user storage is cleared.

Latest Stage 5 slice: Live speaker output was accepted by the user. Explicit
microphone start/finish now captures up to 15 seconds in memory and sends
mono 16 kHz PCM through the existing Live/core path. Recording is sent only
after Finish & Send; Stop discards it. The user accepted this microphone slice.
Input/output device choices now use browser device IDs through Settings;
missing custom devices report errors without silent fallback. Physical
multi-device acceptance and continuous streaming/VAD remain open. REST is text-only.

The user accepted the device tests. Device lists now refresh automatically
at native startup, on opening Settings and on device changes; the Scan button
was removed. Enumeration never opens the microphone. Permission is requested
only when starting Mic; device names refresh after permission is granted.

## Python environment

Run PowerShell in this directory. Python 3.11+ is the declared minimum; the environment uses the locally installed Python 3.14.7. PyWebView/WebView2 is installed and tested. The Gemini text/tool adapter is implemented with controlled HTTP tests; REST catalog/notes live acceptance passed with an alternative model. Native UI and persistent Live local tools are connected; REST/Live note CRUD was accepted by the user; Live speaker and start/finish microphone were accepted; live-account resumption, continuous VAD and physical multi-device acceptance remain open.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip check
```

The snapshot installs both runtime and test packages. `pip install --group dev` alone installs only the development group, not the project's runtime dependencies. The created environment uses pip 26.2.1. Calling the environment's interpreter directly avoids PowerShell activation policy changes.

Dependency declarations live only in pyproject.toml. requirements-dev.lock.txt is an exact, generated snapshot of the tested development environment (runtime and development packages together), not a second hand-maintained dependency list. To reproduce its versions in a fresh environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
```

Regenerate the snapshot with `python -m pip freeze` from this virtual environment after a deliberate dependency update. It has no artifact hashes and is not a cross-platform release lock.

## Tests and data isolation

The current suite contains 727 passing tests. The pytest configuration treats warnings as errors except for the exact Python 3.14 typing deprecation emitted by google-genai 2.32.0; see [Stage 5](../docs/STAGE5_MODEL.md) for the diagnostic and live-test limitations.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

tests/conftest.py gives every core test its own temporary TASKVEX_HOME. get_data_home() reads configuration when called; imports do not create data directories. Stage 1 is complete: contracts, registry, TaskManager, local policy, atomic storage and real notes.add/list + system.status work together. Stage 3 connects native notes CRUD, confirmed one-time legacy transfer and backup restore to the same core. Visible-window acceptance using real Windows file dialogs and restart is complete. Stage 4 adds apps.catalog/status/open. Opening requires explicit read + launch capabilities, reuses an existing verified window and verifies a new launch using OS identity/window evidence; uncertain launches are not automatically retried. Status uses OS package/system-path identity, process creation times and window/PID matching; unavailable observation is not reported as closed. The current suite passes **727 tests**. See [Stage 1 acceptance and usage](../docs/STAGE1_CORE.md), [Stage 3 notes transition](../docs/STAGE3_NOTES.md), [contracts](../docs/CORE_CONTRACTS.md), [registry](../docs/TOOL_REGISTRY.md), [TaskManager](../docs/TASK_MANAGER.md), [policy](../docs/POLICY.md) and [storage](../docs/STORAGE.md).

app.bootstrap.create_core() returns the configured TaskManager; use it with a with block to close its worker. It uses get_data_home()/notes.json and grants only the six note CRUD/transfer/restore tools, system.status and apps.catalog/status/open to the configured local desktop principal. The native entry point and settings/status bridge are available:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

Use `--debug` for developer tools. [Stage 2 plan and manual tests](../docs/STAGE2_NATIVE.md) explain the initial scope, isolated TASKVEX_HOME, native smoke command and remaining work. Current pytest validation: **727 tests passed**. The native suite runs ten real hidden WebView2 processes covering notes CRUD, persistence, import/export, credentials, text/Live chat with synthetic HTTP/WebSocket transport, dialog cancellation and startup recovery. Browser-only and simulated-native notes checks also passed. Existing browser-only instructions remain in [ui/README.md](ui/README.md).

## Scope

TaskManager executes the real local tools, handles cancellation/replays and denies execution without an explicit authorization callback. Policy allows only explicitly granted notes.add/list/update/delete/initialize/replace, system.status and apps.catalog/status/open operations for the configured desktop principal. Notes use stable IDs and verify writes by reading the file back; native UI notes use the backend after an explicit one-time transfer confirmation; browser-only mode remains local. Generic settings save does not write notes. Storage assumes a single writer. system.status reads basic platform/CPU-count information; CPU/RAM utilization is null because it is not measured. PyWebView opens the UI and persists allowlisted preferences to settings.json, excluding collections/credentials. General approval UI and external-account authentication adapters remain pending. REST and Live expose apps.catalog, system.status, and notes.add/list/update/delete after initial notes confirmation through the same core. Model updates/deletes require a fresh verified list and an explicit record ID, unique exact text, a unique quoted literal contains filter, or a unique latest creation time. Missing dates or tied latest times require an ID. Live replies now stream bounded PCM playback through Web Audio; model-driven apps.open and microphone input remain disconnected. Settings saves are serialized and confirmed; import/export is tested, with cross-store partial failures reported explicitly. Visible-window acceptance and real Windows file-dialog interaction passed using Computer Use; see [visible acceptance](../docs/STAGE3_VISIBLE_ACCEPTANCE.md). Human UX and physical audio-device testing were not performed. The first application-plugin steps are in [Stage 4](../docs/STAGE4_APPS.md). Gemini uses the declared google-genai SDK; reference-repository dependencies were not installed. Do not copy the reference requirements file into this environment.

Configuration references: [PyPA pyproject specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/), [pytest configuration](https://docs.pytest.org/en/stable/reference/customize.html).


Notes now retain optional `created_at` metadata in canonical UTC ISO format
(`YYYY-MM-DDTHH:mm:ss.sssZ`). New native notes get the backend clock; edits
preserve it. Legacy missing/null dates remain unknown. UI cache, backups and
confirmed migration/restore preserve valid dates without inventing old ones.
Quoted literal contains filters and last/latest-note selection now share the REST/Live gateway. Latest requires all creation times to be known and a unique maximum; list position is ignored. TR/EN explicit phrases are supported; ambiguous, compound and unsupported filters ask for an ID. The user accepted these new selectors. Live PCM playback is implemented; physical audio acceptance is pending.
Run `node ui/tests/note-timestamps.mjs` for the DOM-free backup/date checks.


Live desktop text requests stream PCM to `ui/js/live_audio.js`; no audio
package was added. The output queue is capped at 20 seconds/512 sources.
Stop clears playback immediately and still waits for native cancellation if
needed; model completion and audio drain are separate. Mute affects Live
reply audio, not the microphone or sound effects. The OS default output is
used. Audio errors preserve text and verified tool results. PCM is not saved.
Run `node ui/tests/live-audio.mjs` for the device-free playback ownership tests.
Saved API keys already persist in Windows credentials for the same data
profile; an empty password input on reopen does not mean the key was removed.
