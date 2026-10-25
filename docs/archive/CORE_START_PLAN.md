# TaskVex — Mark LVI review and core starter plan

## Current priority — 5.R3 natural response then sleep

5.R2 audio protocol approved by user. Separate local confirmation sounds
removed by user request; sleep on command, Vex's normal response and ringing
It is applied after completion. Current acceptance [stages.md](stages.md).

## Previous application — 5.R1 stabilization

sleep/sound review was placed before F4. EOS and post-response candidate threshold
their reproduction has been corrected; Expensive wake installation cached. real host
post TR/EN local confirmation sounds pass through the same player; API/TTS was not added.
Physical acceptance is obvious. [Review](docs/STAGE5_SLEEP_STABILITY_REVIEW.md) and
[stages.md](stages.md) shows current scope; The next integration did not open.

## Previous application — 5.F3

TR/EN sleep intent extended in common host parser; enter/pass and permanent
back-sleep separation, question/negative/quote/addition has work protection. Confirmation of the model
host does not replace sleep acceptance. New dependency/tool/architecture no layer.
F2 physical awakening/25 s and F4 pronunciation open; [stages.md](stages.md)
is the current progress record. Runtime expects manual acceptance.

## Previous application — 5.F2

If the microphone context is subsequently suspended, limited resume and
Added error cleaning. transmission/event measurements without sound for 25 s standby
there is; physical awakening notification is on. Current sequence and acceptance [stages.md](stages.md)
is in. There is no commit because the runtime expects manual acceptance.

## Previous application — 5.F1

5.F1 kod/targeted regression/native verification ok; It waits for manual acceptance.
Strict conversation termination closes the old PCM, the result model/tool continues.
The UI separates sleep preparation from actual host acceptance; is locked in uncertainty.
Wake-only is not a task completion. Single ownership of Live/core/microphone
preserved; no new framework/service. Current sequence [stages.md](stages.md)
is in; next 5.F2 is the current Idle/25 s problems.

## Current status — October 23 general inspection

The current step/sub step record is now in [steps.md](stages.md).
Five reproduced runtime vulnerabilities are vulnerable in layer Sleep/sound; existence of code
and passing regression doesn't close them. Detail: [sleep/general audit](docs/STAGE5_SLEEP_AUDIT.md).
This round of application code was not changed; phase update obligation to AGENTS.md
recorded. Stage 5 was not closed, and Stage 6 was not moved on. Previous subheadings
are historical work records; The current sequence is 5.F1–5.F6 in stages.md.

## Current scope — fixing sleep behavior / first step

User corrected the meaning of Stay asleep, task/answer back immediately after finishing
don't sleep; sleepDelay is divided into one-time idle sleep in normal speech.
Persistent barge-in is not opened in response; The only microphone/Live/core line available,
active/unknown/old welding barriers are maintained. Duration can be closed with 0.
This slice awaits manual acceptance, the previous slice was not fully counted as acceptance/commit.
Remaining row: (2) wake/idle login lifecycle, (3) flexible TR/EN sleep intent,
(4) local wake pronunciation and false wake, (5) combined acceptance. detail
and the proof is in docs/STAGE5_MODEL.md; The next stage was not opened.

## Current slice — automatic return-to-sleep and seconds setting

Fixes for Sleep/login were included in commit `701f33f` with user approval; push
no. Persistent sleep preference and explicit shutdown were added to the same host control line.
Preference in chat RAM, sleepDelay (1–300 s/default 10) in settings file
remains. Single UI timer only available after cut ending/idle sleep_start
uses; active/unknown/talk is not skipped, there is no new worker or tool replay.
Mic On/Off paired with camera effect. This slice expects manual acceptance; next
Step 5 is open limits/general acceptance and debloat check. evidence and
limits at docs/STAGE5_MODEL.md; The old slices at the bottom are the historical record.

## Current reception — wake input end and plain microphone

Adjustments were made for R4–R5 and reported sleep rejection outcome; physical acceptance
waits micB is only user preference On/Off; error/connection separate case
remains. thought-only login does not close, wake silence and 15 s limit EOS only
produces. The sleep candidate output waits in limited RAM for the host decision. Single Live /
microphone/core ownership and Stop security are preserved. User in previous language
No new commits since it reported a problem; detail in docs/STAGE5_MODEL.md.

## Current priority — October 23 R1–R3 acceptance

R0 was moved to commit `616125d` with user approval; no push. R2–R3 local wake
error classes, up to two source refreshes and correct microphone states
with small R1 Veks sleep chant applied; It waits for manual acceptance. single microphone,
single Live owner and core tool line maintained; There is no replay of the old PCM/tool/model.
Next are the R4–R5 input limits and early thought closure. These and
Automatic return-to-sleep or the next feature phase will not be turned on until the last acceptance is finished.
Detail/evidence: docs/STAGE5_MODEL.md. The old slices at the bottom are historical records.

Priority after October 23 review: R0 wake time alignment/host acceptance
It is applied in this step and awaits manual acceptance. Then R2–R3 error/tail
recovery, R4–R5 input limits, R1 safe sleep recognition are switched off.
Automatic return-to-sleep or the next feature stage will not be opened until these tasks are completed.

## Current slice — one-time sleep and local wake-word

Stop indicators were moved to commit 515a531 with user approval; no push.
This new slice awaits manual acceptance. PCM lonely local sherpa-onnx while sleeping
goes; After hitting or requesting open Wake/written, the only available Live line is opened.
Personalization pWake selection is saved; default Vex, supported English dictionary
words. The same microphone/AudioWorklet and limited buffer are used; new core
There is no worker. Model files are in the local data cache and are called MIT.
not tagged. Physical microphone acceptance is on. Next step auto sleep back
and is the second setting; UI cleanup at the end of Phase 5. Detail STAGE5_MODEL.md.

## Current minor correction — Stop indicators

Temporary memory was included in commit dc79318 with user acceptance; no push.
This type only occurs when the microphone On light remains constant at the source speed and is normal.
Implemented the interrupt to display neutral LIVE READY instead of connection error.
The physical capture/Stop protocol is unchanged; real source/unknown obstacle and
errors are preserved. The new slice awaits manual acceptance. Local wake-word and odd
One-time sleep is the next separate application step.

## Current application language — temporary chat memory

Command placement guide/setting moved to commit d4ffb16 with user approval;
no push. This new implementation slice expects manual acceptance. TextChat's only
limited RAM history is kept in the lock; Fresh Live socket only history
data is transferred, old tools are not operated. Stop/Disconnect protects; NewChat,
Closing and key update clears. The current core/not authority is unchanged.
Limit: 12 turn/16.000 JSON characters and 2,000 characters per text; summary API
There is no request or permanent profile. commands.md updated. Next separate job
local wake-word/single one-time sleep; full behavior is in STAGE5_MODEL.md.

## Current coverage decision — Live main product, memory and sleep

October 22, 2026: previous audio/Mic Off with user acceptance `ba47710`
taken into commit; no push. The main desktop experience will be Live alone;
The REST will then be preserved for different uses of tool/channel. in main UI
REST test control was subjected to targeted cleanup; It hasn't been removed from the code yet.

Current execution order: Limited ad-hoc chat with app ownership to Stage 5
memory, one-time sleep with local wake-word, then after each work
The choice to return to sleep is added as separate steps. Then integrated acceptance,
followed by the targeted UI/debloat and the final close regression/document. permanent user
information/inference memory is planned per Stage 6, before integrations.
These features have not been implemented yet. Detailed behavior and limits:
[STAGE5_MODEL.md](docs/STAGE5_MODEL.md), "October 22, 2026" scope decision.
The next implementation step is the temporary chat memory. In future application steps
CORE_START_PLAN.md current processing order is followed; following old target stages
this should not show the new scope as an implemented feature.

## Current progress — Phase 5 REST voice slice

User accepted previous microphone preference correction; Commit `f35a13e`
saved, no push. The next REST audio gap is via the same TextChat/PCM
Completed as separate TTS request without tools. The text appears first; audio error text
and does not corrupt completed grades. Mic Off only signals end of input, Live response
it doesn't cut it. This new slice awaits manual acceptance. The next discrete step is integrated truth
acceptance; then the targeted close of UI/debloat and the final close of regression/document. Stage 5 is open.

Current interim request: Microphone On/Off preference left error Stop/model;
A new speech is expected at the definitive end. Old command is not repeated, source/unknown
obstacles are preserved. Step 5 was moved to commit 78c292a with user acceptance.
After manual acceptance of this slice, the next separate task is still the REST audio output.

Latest step 5: status/log/duration management and desired idle/listening separation
was implemented. Tool and proof of cancellation are preserved; Normal Stop is not considered an error. Evidence
It's in STAGE5_MODEL.md. Step 4 was moved to commit 73a87df with user approval.
Next separate job REST audio output, then integrated acceptance and targeted debloat/closing.

Latest step 4: pLang/pIns connected to common instruction REST/Live. saved
The profile is a turn-specific snapshot; Effective change in Live opens new context.
Core/tool authorizations remain the same. Controlled test evidence is in STAGE5_MODEL.md;
Acceptance of real account dil/style is expected. With 85648b9 after step 3 acceptance
committed The next discrete step is the status/log/time limit; Phase 5 has not closed.

Latest step 3: local VAD candidate strengthened; microphone at the end of the response and
It is transferred to idle listening without closing the front bumper. Targeted/automatic test proof
It is in docs/STAGE5_MODEL.md; actual hardware adoption is awaited. Step 2 user
After approval, it was committed with 3daf152. This new step cannot be committed without approval.
The next separate step is the 4 languages and basic customization. The following records are historical.


Current fix order: user announced note suspicion, step 1 postponed.
Step 2 Live snapshot user/model transcript and preservation of cut text
was implemented. Controlled proof is in docs/STAGE5_MODEL.md; physical acceptance is obvious.
The next separate job is to fix VAD/barge-in in step 3 determined before; personalization,
log/duration maintenance, integrated acceptance and debloat have not been done yet in this prompt.

Current audio step: automatic listening user acceptance passed. Spoken response
cutoff applied as a sequential lap cycle with existing Stop and single Live/core line;
If the old result is ambiguous, no new sound is sent. Real account/echo acceptance is on.
Next is job closing acceptance checks and planned targeted maintenance/debloat coverage;
No debloat or new features were made in this prompt. Phase 5 has not yet closed.

Last little slice of audio: removed Mic click on every conversation. Live model is ready
local automatic hold, same Live stream in conversation and post-response
There is waiting again. Stop/error/Disconnect pauses; Pause/Resume is protected.
Silence is not sent to the API. Barge-in separate is the next step; Stage 5 did not close.
Control and physical acceptance limits are at the beginning of docs/STAGE5_MODEL.md.

Current slice: automatic device list user acceptance passed. in one conversation
implemented real-time PCM and server VAD; 737 pytest, 4 Node suites,
10/10 hidden native phase and type check passed. The proof is in docs/STAGE5_MODEL.md.
Real account/VAD acceptance is on. Next
separate step barge-in; There was no phase 5 closure or transition to new integrations.

Last update: user Live audio output, limited start/end microphone and
Approved device tests. dIn/dOut is in the same line as setup/record and Live/core.
Scan button removed; automatic on device list opening/setting/devicechange,
microphone permission is only on the Mic button. The next step is continuous flow/VAD.
Bulk note deletion to STAGE5_MODEL.md as separate enhancement
recorded; has not been implemented yet. Phase 5 has not closed.

Updated: October 22, 2026. Status: Phase 0–4 planned acceptance completed. In Stage 5, the common tool adapter and Gemini SDK text turns are ready; Controlled tests passed. Live catalog/not acceptance passed with 3.5 Flash-Lite. Added safe retry/fallback, keeping base model 3.8 Flash; The lively acceptance of the united policy is clear. Permanent Live, Disconnect and catalog/system/not add-list tool connection ready; REST/Live Stop and safe idle resumption ready; note from model editing/completion/deletion confirmed by user REST/Live; time creation and single partial text/last note selection are ready with controlled testing; the new selection is confirmed by the user; Live audio output is user approved; start/end microphone is user approved; device selection is ready with controlled testing, true multiple device/VAD acceptance is on.

Stage 0 initial decisions saved: [STAGE0_DECISIONS.md](docs/STAGE0_DECISIONS.md). User chose MIT for TaskVex's original contributions; root LICENSE added. Mark sources will be kept separate for reference. Initial coverage and current base testing evidence is in this decision document.

Progress: current 727 pytest checks passed; This includes 15 tests at the new Live car limit. apps.open verified on real Windows by launching once, process/window proof, replay and using current window. Phase 3 is completed with eight hidden native processes and two browser scripts, plus [visible Windows acceptance](docs/STAGE3_VISIBLE_ACCEPTANCE.md) real dialogs and a restart. [Acceptance of STAGE4_APPS.md](docs/STAGE4_APPS.md) application plugin; [STAGE5_MODEL.md](docs/STAGE5_MODEL.md) describes the current slice of the model link.

| Stage | Completed | Status |
|---|---|---|
| 0 — Basic decisions | MIT, scope, architecture/responsibility and UI data ownership, base testing | Completed |
| 1 — Model-independent core | Environment, contracts, registry, TaskManager, policy, atomic JSON, real notes.add/list and system.status | Completed |
| 2 — Native UI | PyWebView, ui_ready/snapshot, settings save, system status, window controls, error/recovery, queued save and confirmed import/export | Scheduled automatic and visible acceptance OK |
| 3 — Delegating UI notes to backend | CRUD with immutable ID, native commands, certified one-time legacy data transfer, backup import/export | Scheduled automatic and visible acceptance OK |
| 4 — First application plugin | apps.catalog/status/open, authentication with OS authentication, separate open permission, error/repeat/cancel and open with user close/restart | Scheduled acceptance completed |
| 5 — Model and sound | Shared tool line; Gemini SDK text turns; Windows identity store; UI and modal Live tools | 5.1 ok; REST live acceptance passed with the alternative model; Live tools are ready with controlled tests; REST/Live Stop and safe idle resumption ready; note from model editing/completion/deletion confirmed by user REST/Live; time creation and single partial text/last note selection are ready with controlled testing; the new selection is confirmed by the user; Live sound and start/end microphone approved by user; device selection is ready with controlled tests; continuous VAD/multi-device and missing account acceptances open |
| 6–8 | Other L0 integrations, GUI/skill, routines/packaging | Did not start |

This plan builds on existing ARCHITECTURE.md and v1/ui/docs/UI_BACKEND_CONTRACT.md. Hermes will not be used. Mark LVI was reviewed for reference; It was not adopted as the backend of TaskVex. The plan describes future files; does not claim that they exist today.

## 1. Decision and ilk target

TaskVex will have its own little Python core. The stock HTML/JS UI will be preserved. Application-specific direct capabilities will be added to the L0 tool registration as a plugin; skill will be able to turn one or more tool/GUI steps into a task. GUI operations that are not supported by the plugin will go to the existing L1–L4 resolver line.

First goal: application that opens the current UI in a native window, loads state, runs a native tool and an application plugin from the same pipeline, without connecting the model and microphone. Verify kernel behavior first, then add Gemini Live. Creating all target folders on the first day.

## 2. Source and limit of review

Reference index: Mark-LVI-main/. Upstream README points to: https://github.com/FatihMakes/Mark-LVI . The analysis is based on the current content of local files; Git revision is not authenticated in the ZIP folder.

The file tree, input stream, action/plugin loading, result format, approval, registration, vendor agreements, and relevant code paths of selected tools were examined. Not all Python files have been security or behavior validated. The application, setup.py and tools were not run; No dependencies were installed, no real accounts and hardware were used.

### Licensing decision

Mark-LVI-main/LICENSE reports CC BY-NC 4.0 on behalf of FatihMakes. There are non-commercial use and attribution terms; Changing it does not automatically remove these conditions. Official synopsis: https://creativecommons.org/licenses/by-nc/4.0/ .

Therefore, the following technical transfer candidates should not be read as automatic copying permission. Default start: write TaskVex contracts according to our own requirements; external code transfer. If transfer is selected, keep a record of the source file, version/hash, changes, copyright, and license. If there is a commercial target, transport without appropriate permission or other licensed alternatives for the relevant code. This note is not a legal assurance about the license compliance of the entire project.

## 3. What can be taken from Mark LVI?

### Core and providers

| Source | Observed useful point | TaskVex decision |
|---|---|---|
| core/action_loader.py, core/plugin_loader.py | Tool name/schema/handler notification, conflict checking, separation of loading errors | Use your design; Install a single ToolRegistry instead of two parallel dispatchers. Let the first version use an open registration list. |
| plugins/_template.py | Description, parameter and run input in one file | Write new template according to our ToolSpec + ToolContext + ToolResult convention; player/speak export objects. |
| core/outcome.py | done, unverified, failed, ask, started distinction | Use the idea; Define machine contract as typed result instead of natural dil/key=value. |
| core/appidentity.py, actions/open_app.py | Application name mapping, running process/window observation, post-boot check | Strong adaptation candidate for Windows adapter; Use limited app catalog and single target in first release. |
| core/confirm.py | Model's inability to self-certify | Use the policy; Instead of a single global pending callable, design an approval record based on user, task, parameters and duration. |
| core/undo.py | Compensation posting for some file/setting transactions | Handle it at the file modification stage. Considering every transaction reversible; Verify existing data before compensation. |
| core/audio_devices.py, core/echo.py, core/hotkey.py, core/wake_word.py | Device selection, echo and listening experience | Separate examine/measure in audio stage; Don't depend on core now. |
| core/gemini.py | Centralize time, quota, and provider access in model calls | Reference for ModelGateway design. Verify the current SDK/model integration without moving the old model list. |
| providers/base.py, providers/registry.py | LLM/STT/TTS/Engine capabilities and optional installation | Setting up a multi-vendor system on day one. Set up the small limit required for Gemini and the helper text client; expand in the future. |
| providers/schema.py | Converting tool schema to provider format, tool budget | Keep internal schema vendor independent; Put the converter into the model adapter. The visible tool list does not replace permission. |
| providers/llm_openai.py, engine_pipeline.py | Compatible endpoint and STT→LLM→TTS path | Delay to local model phase; Don't assume it has the same features as Gemini Live. |
| memory/memory_manager.py | User information and history search idea | Design separate user memory when needed. Merging with Notes, task log, and L1 locator memory. |
| memory/config_manager.py | List of setting read/write requirement | Porting writing code; Set up atomic registry and separate credential store for TaskVex. |
| main.py, ui.py | Example of Live, audio and tools working together | Transport. Bringing PyQt UI and extensive orchestration into our main.py. |
| dashboard/server.py | Remote control example | Initial release; server/remote access is not required for the native desktop bridge. |
| core/installer.py, setup.py | Installation automation | Operation/transportation. Dependencies must be installed with an explicit command in the development environment; pip should not work when starting core. |
| core/avatar*.py, core/viseme.py, ui.py | Avatar and Qt visual behavior | Unrelated to current UI; leave it out. |

### placement of 21 files in actions folder

| File | Location / decision on TaskVex |
|---|---|
| open_app.py | L0 behavior reference for apps.open; Redesign with proof and target catalog process/window. |
| system_monitor.py | L0 system.status + optional telemetry service; UI object independent measurement adapter. The get_system_status function of the source code turns the missing GPU/temperature into None. |
| computer_settings.py | Windows settings tools; separate for each action scope/policy. Initializing power, network and similar effects. |
| file_controller.py | File tools; permissive root, symlink/junction, migration without adding overwrite and compensation checks. |
| file_processor.py | Document reading/analysis service; Separate file reading from model analysis. |
| browser_control.py | Scanner adapter and reference for L2 in the future. Copying the behavior of real user profile unlocking/locking; Start with ownership specific test profile. |
| computer_control.py | General GUI application primitives; Don't put it directly into L0 like trusted application API. Use behind Resolver/policy/verification line. |
| screen_processor.py | Screen/camera capture and vision input; It is not a validated GUI process or L4 resolver alone. |
| send_message.py | PyAutoGUI/clipboard based messaging path. Telegram/Discord is not API integration; It will not be ported directly as a L0 message medium. |
| weather_report.py | Google opens weather search; It does not produce the temperature/condition data that the widget needs. TaskVex air adapter should be written separately. |
| web_search.py ​​| Search reference provider/fallback; Moving without parsing the model call, quota and display code. |
| reminder.py | OS timing reference. Creating a second player parallel to our routine/scheduler ownership. |
| background_monitor.py | Optional tracking service; outside the scope of the first core. |
| proactive.py | Optional behavior service; Adding to default startup behavior. |
| desktop.py | Separate Windows desktop capabilities by action; Transport as a large single tool. |
| game_updater.py | Candidate for Steam/game plugin in the future; proof of success and client/GUI paths should be examined separately. |
| video_player.py | Qt player/UI dependent; Does not fit directly into the existing HTML media space. Postpone it. |
| youtube_video.py | Separate YouTube operations to provider/media adapter; Except for the first core. |
| flight_finder.py | Candidate for Search/field plugin; Except for the first core, authorization to receive transaction/purchase is not assumed. |
| code_helper.py | Separate code generation and execution; Don't count model output as direct local execution authority. Postpone it. |
| dev_agent.py | General code agent; It is not required for the first personal assistant core. Postpone it. |

There are only __init__.py and _template.py in the local plugins folder. Plugin support in the README does not mean that there are ready-made application plugins in this folder. The plugin template is different from the actions modules.

## 4. Concrete behaviors that we will not carry verbatim

- plugin_loader.py:117–128: null/non-return handler result "Done." It's happening. In TaskVex, a null or out-of-contract result does not translate into a verified success.
- plugin_loader.py:288 et seq.: module is loaded with exec_module, then its declaration is verified. The code may have already run during import. The first version only installs the explicitly registered trusted plugins that come with the application. This is not a sandbox.
- _template.py: player/UI object is given to the handler and the text to be read to the user. Our plugin does not directly access the UI or model session; Returns data and events.
- confirm.py: there is a single global _pending record; The new request may replace the old one. Do not use the same model for multiple tasks/channels in the future. After approval, the current target and prerequisites must be checked again.
- memory/config_manager.py writes settings directly to JSON; It also keeps API keys in the same data field. memory_manager.py:118–127 uses write_text. Atomic replacement, version, recovery and visible write error required in our persistence.
- Subprocess.Popen is changed to global at the beginning of main.py. Our Windows adapter only opens its own child processes with appropriate flags; Global monkey patch is not possible.
- main.py:_execute_tool is nested with model SDK type and self.ui. The TaskVex executor should be independent of the model SDK and HTML/PyQt.

These are incompatibilities detected from the relevant code; It's not a claim that the entire app is unsafe or broken.

## 5. Core contract

### Tools and plugins

- ToolSpec: name, description, input_schema, handler; required_capabilities and exclusive_resources when necessary. Built-in tools and plugin tools are registered in the same registry.
- Plugin: id, version, ToolSpec records it offers; Open registration that comes with the first version application. No dynamic file scanning, no hot reload and no plugin store.
- Tool name must be specific to the application/process: notes.add, system.status, apps.open, spotify.play in future. A second record with the same name cannot silently overwrite.
- The internal schema is maintained in standard JSON Schema format; Gemini's OBJECT/STRING format is generated at the adapter limit. The UI schema.js file is not a replacement for Python execution validation.
- ToolContext only carries ID task/request/user, cancel signal, deadline and required narrow services. The public context service network that is not used initially is not written.
- The plugin declares the required authorization; user/core policy gives the authority. A plugin cannot grant permissions to itself. If native Python code is running in the process, it can access OS authority; ToolContext does not turn this into a security sandbox.

### Task and result

- Request: request_id, source, principal, tool, arguments. The user ID comes from the input adapter, not from the text sent by the model.
- Task: queued → running → terminal; awaiting_approval if necessary. Terminal states succeeded, failed, canceled, unknown. cancel_requested is a request; It is not terminal success.
- Result: task_id, status, data, error, verification/evidence. The sentence to be spoken to the user is not the sole authority of the machine result.
- Parameters are verified on application; Plugin activity, policy and changes at execution time target/preconditions are checked again.
- Jobs that require desktop access are sorted on the same desktop resource. In the first version, a simple worker was sufficient; No distributed queue or public DAG.
- Cancellation before the work starts does not produce side effects. The running job uses collaborative cancellation points. Applying a timeout to a Python thread does not stop the thread. If the physical process is in progress, the desktop lock is not released and the second process is not started; status is monitored or the resource is kept unavailable.
- Returns current task/result when same request_id + same content arrives again; the same identity with different content is rejected. In the first release, in-session replay prevention is open-limit. Global exactly-once after crash is not promised; external side effects require registration/provider key and query.
- The ambiguous result is not automatically repeated. In appropriate cases, such as the proof that Method unsupported/operation has not been implemented, one can switch to the GUI alternative. Authorization denial cannot be overcome with the alternative GUI.

### Plugin, skill and L1–L4

Just because the plugin is installed does not mean that it supports every operation. Selection is based on action/ability. In fact, the plugin using keyboard/coordinate also requires desktop lock and GUI authentication; The name of the plugin is not a direct API guarantee.

Skill task recipe/plan; The plugin may call the tool or GUI step. L1 is the learned GUI target information, L2 is the DOM, L3 is the UIA and L4 is the vision parsing line. Mark's generic click/screenshot functions are not a ready-made implementation of these four layers.

## 6. The issue to be solved first in UI integration

In the current notes.js user action, it first modifies the local collection, produces a full save with saveStoreCb({emitSave:true}), then issues note_add/note_done/note_del. There are delete and {t,d} records that use text instead of ID. If two backend handlers write separately, double annotation or conflicting authority may occur.

Recommended contract migration:

1. First determine in a table which field the current events are written in; For a single field, both snapshot save and command handler should not have mutations.
2. In native notes mode, the backend will be the authority: notes CRUD will carry explicit request_id and note_id; will not rewrite the full save note collection. The backend sends the exact result/snapshot. The Pending/faulty record is visible to the user; The input is preserved on failure.
3. The existing native annotation mode, which works without a backend in the browser, is preserved. Native/local mode is selected by an explicit initial agreement; A transport error is not silently downgraded to the other write mode.
4. Relevant paths in UI api.js, app.js, notes.js, schema.js and settings.js are updated together; existing payloads are not silently interpreted differently. The new contract is versioned and UI_BACKEND_CONTRACT.md is updated.
5. Existing browser notes are not automatically deleted at the first native startup. With the absence of the backend data file, the current empty collection is allocated; Importing local data becomes an explicit transfer to the user. The existing JSON fallback import path can be used.
6. ui_ready just means the bridge is ready; online(true) is sent only when the actual model session is verified.
7. At the stage when routine ownership passes to the backend, stopRoutineScheduler is called; If the calendar is also inherited, stopCalendarScheduler is called. This ownership is reestablished on every page load.

Before this protocol change, we will not be binding native annotation. The first secure bridge attempt could be settings and read-only system.status.

## 7. Recommended small starter tree

The current v1/ui is not carried over. The following files are created at the relevant stage with their contents to be used; An empty skeleton cannot be opened in advance.

```text
TaskVex/
├─ AGENTS.md
├─ ARCHITECTURE.md
├─ CORE_START_PLAN.md
├─ Mark-LVI-main/                    # reference; Not imported, not distributed
└─ v1/
   ├─ app/
   │  ├─ __init__.py
   │  ├─ main.py                    # native window and application login
   │  ├─ bootstrap.py               # installation of concrete components
   │  ├─ config.py                  # TASKVEX_HOME, environment and version
   │  ├─ core/
   │  │  ├─ contracts.py            # desire, means, task, result
   │  │  └─ events.py               # only needed event transfer
   │  ├─ tasks/manager.py           # queue, status, cancellation, and resource ownership
   │  ├─ policy/engine.py           # Explicit permission/denial rules for early tools
   │  ├─ session/tool_registry.py   # single point of registration and parameter verification
   │  ├─ bridge/webview_bridge.py   # event(name, data), secure UI update
   │  ├─ bridge/dispatcher.py      # Redirect UI event to corresponding function
   │  ├─ tools/local/notes.py       # notes.add/update/delete/list
   │  ├─ tools/local/telemetry.py   # system.status
   │  ├─ integrations/plugins.py  # Reliable plugin registry list when needed
   │  ├─ integrations/apps.py      # tools of the first app plugin
   │  ├─ platform/windows/applications.py
   │  ├─ services/notes.py          # UI/model common note business logic
   │  └─ storage/json_store.py      # atomic and versioned data file
   ├─ ui/                          # existing HTML/CSS/JS
   ├─ tests/                       # few significant tests by stage
   └─ pyproject.toml               # project, dependency and test configuration
```

This is not a file count target. In the first setting slice, notes/platform/plugins files are not created if they are not needed yet. Simple aids keep the person responsible in the file. main.py does not collect business logic.

Recommendation for permanent working data: If there is TASKVEX_HOME, that path; Windows default is %LOCALAPPDATA%/TaskVex. Tests use temporary separate root. No user data is written to the source directory or the config/ area of ​​the reference repo. Existing JARVIS_HOME names are not considered automatic data move instructions.

## 8. Development stages and acceptance conditions

### Stage 0 — Baseline and contract decision

- Get hash/backup reference of existing UI files and current test results. Don't count the previous success report as tests run today.
- Separate UI events into settings, collection command, model session, hardware and view responsibilities; Record who wrote which field in the document.
- Save mark transfer matrix and license preference. The startup can proceed with our own core code; This step does not stop further development.
- Acceptance: the first slice's input, output, persist owner and unsupported event response are clear. There is no import from the mark directory.

### Phase 1 — Model-independent core

Completed: [acceptance results and actual tool contracts](docs/STAGE1_CORE.md).

- Write contracts, single registry, small TaskManager, initial policy and atomic JSON store.
- First set up the line with notes.add/list and read-only system.status called from tests; The UI doesn't depend on them yet.
- Establishing a persistent framework for states and events; narrow callback/subscription is sufficient. Do not rerun the process that was executed by event subscriber error.
- Test: invalid parameter does not reach the handler; name conflict is rejected; The same desire does not produce two mutations; Cancel in queue is not executed; Writing errors are not successes; Corrupted JSON is recovered, preserving the original.
- Acceptance: tool call in real temporary file without model, microphone and UI and the result is verified.

### Step 2 — Open ready-made UI as native application

- Open existing index.html with PyWebView; Present event(name, data) in accordance with the current API expectation. Verify boot method for native ES modules in real native environment.
- Forward UI main thread to core without blocking. UI updates are done with allowed method names and JSON serialization; raw data is not merged into JS source text.
- First mount setting snapshot and read-only status. Do not display online when the model is not connected. Return not_implemented result to event not yet supported.
- Test: early/late ui_ready, initApp/no-echo, setting save-close-open, broken setting, write error, reopening, handler error and native window closing.
- Accepted: the appearance is preserved, the native bridge actually works and the settings data is available on restart. Mock browser testing does not count as native testing.

### Stage 3 — Link notes to backend with single authority

Scheduled automatic and visible acceptance completed: [current contract and test](docs/STAGE3_NOTES.md).

- Implement versioned annotation commands and immutable IDs from Chapter 6. Update the UI according to the final result of the backend; Generic save should not write the same note again.
- Add ID generation migration and user-controlled local data transfer to legacy {t,d} backups. Two notes with the same text can work with separate identities.
- Testing: add/complete/delete, restart, delayed response, double click, duplicate request, stale backup, invalid record, disk error and browser-only regression.
- Accepted: UI → bridge → TaskManager → policy → notes tool → registration → final UI result flow runs once; Can be used without model.

### Phase 4 — First real app plugin

Step by step plan: [STAGE4_APPS.md](docs/STAGE4_APPS.md). Catalog/identity, working
status query and verified trip ready. Error/repeat/cancel also passed the tests;
The actual close/re-hungry check has been completed by the user and its reports have been verified.

- Recommended first goal: open Notepad in the catalog with apps.open and query its status with apps.status. No new custom plugin UI panel required; The acceptance scenario can be done first by calling test/command.
- Use the same ToolRegistry/TaskManager/policy line. Adding UI search or random coordinate fallback; Select supported Windows startup method and target proof.
- Proofs are different, such as the process has started, the window has been found and the target document is ready. State in conclusion the level that the tool guarantees; Don't give data just because Popen returned.
- Test: unsupported application, application already open, startup failure, delayed startup, timeout/uncertain result and cancellation. Actual Windows testing is done separately.
- Acceptance: the built-in notes tool and the app plugin follow the same execution contract; The plugin does not capture the core/UI object.

### Stage 5 — Gemini text/Live and sound

- First connect text→tool call→same TaskManager→tool result round. The model does not become a separate executor. Unknown tool and non-schema parameters are rejected.
- The cancellation line is completed after the first narrow model tools; Then notes.update/delete is opened in a separate slice for the model. CRUD in Phase 3 is not rewritten; The actual registration ID, unspecified target annotation, and result/UI verification are preserved.
- Then add single Live session owner, microphone/speaker lifecycle, limited queues and reconnection. Live may be the first provider; The text turn does not have to be a separate second product feature.
- Identities are preserved on return model→core→provider. On reconnection, the previous side effect tool is not automatically replayed.
- Testing: faulty tool call, error quota/network, logout, actual completion of stop_task and tool result when disconnecting. Report physical sound testing separately from mock.
- Adoption: sound and UI call the same real tool; online represents a verified session only.

### Phase 6 — More L0 and integration on a transaction-by-transaction basis

- Sequence: telemetry/counter → application/media → file reading → controlled file modification → weather/search → Google → Telegram/Discord.
- First single transaction in each integration; for example calendar listing. Account/permission refresh, bulk add tool without errors and verification.
- Add OS credential adapter for secrets when first real secret is needed; UI/localStorage/backup is not a storehouse of secrets.
- Sending message carries clear user/channel/target/scope and proof of result. The general GUI send_message.py is not the API replacement infrastructure of this phase.
- Acceptance: local notes work when external service is interrupted; indefinite reference is not made a second time; A plugin failure does not shut down the core.

### Stage 7 — GUI resolver and skill execution

- Build single application scenario with L3 UIA; learn verified targets to L1. Then add browser L2 DOM and last resort L4 vision.
- Link proof Snapshot/window/monitor/DPI to target. Re-verify target before running; Don't use the old coordinate blindly.
- Export skill steps to the same TaskManager. GUI and direct plugin steps can be found in the same task; Permission and resource rules of child steps are preserved.
- Acceptance: operation that is not supported by the plugin can go to the GUI line; Uncertain side effects or policy rejections do not produce automatic fallback.

### Stage 8 — Routines, background services and packaging

- Install a single scheduler owner; Explicitly inherit UI scheduler ownership. Prevent again with trigger ID; Separate notification delivery from job completion.
- Verify daily rotation/masking, data schema migrations, normal shutdown, crash recovery and packaged native boot.
- Opening the application does not automatically initiate a proactive request, actual message, new monitoring or dependency installation; Enabled features depend on user setting.
- Acceptance: packaging does not include reference repo and test data; With native tests, actual account/hardware limits are clearly reported.

## 9. Our first work package

The scope of the first round of implementation is setting/read-only tranche in Phase 0 + Phase 1 + Phase 2. Then Stage 3 note agreement; Then comes the first application plugin. No Gemini, voice, Google, bot, GUI automation or plugin store written in the first round.

Required dependencies are added gradually. Recommendation: project environment and testing tool; pywebview in native stage; The only schema validator to choose for parameter validation; psutil in the telemetry phase. Mark requirements.txt is not installed in bulk. New SDK versions are validated in the actual implementation round and fixed in a single dependency source; Unverified version number is not recommended here.

For the first round to be considered complete: Python core tests pass; the actual PyWebView window opens the current UI; a setting is permanent; The read-only tool result is visible; unsupported event returns an explicit error; worker/subscription is not released at closing; mock success is not confused with real integration.

## 10. Rule for finishing each stage

A working flow + relevant error/cancellation scenarios + required contract document. Add meaningful testing to changed critical path; Targeting just the number of tests or number of rows. Introducing the same scope into an unlimited audit cycle for no new reason.

This turn is only a plan and source review. No changes were made to TaskVex production code or Mark sources; native/account/hardware test result is not claimed.


### October 22 — Note user acceptance and creation time

REST/Live note CRUD, after selection and Stop with description/ID on the same text target
The new message was reported as passed by the user. This acceptance is previous
Closes slice notes.update/delete; GoAway/resumption account and physical sound
It also remains open. UTC created_at to new notes with single step rule prompt/single
added; no dummy date/ID is assigned to the old undated record. UI cache, backup and open
The restore preserves historical information. In the next separate slice, “endnote” and single partial text matching were applied;
Verified with 707 tests and native packages. Short user acceptance for new selection
Then comes the planned Live audio step. Details are in STAGE5_MODEL.md.


### October 22 — Live PCM release and API key persistence

The note target selection was accepted by the user as fully working.
The PCM output was connected to the Live response written in the next slice. Tailed Web Audio,
Mute and Stop; same request_id, real text/tool result, unknown and Live source
Works with ownership. There are no new dependencies. 727 pytest,JS sound/history
Passed checks, selected Pyright 0 errors and native 10/10. Physical sound acceptance
expected from the user. Pre-registered API key Windows credential
Verified as available in repository; record not displayed/modified. Next
It is microphone/device/VAD after one-step short voice acceptance. Stage 5 closing
The last integrated usage in the list is targeted UI maintenance/debloat and document/reload
The review of launch limits is not over yet; Phase 6 was not progressed.
