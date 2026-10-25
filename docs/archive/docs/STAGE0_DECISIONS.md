# Phase 0 — Core initial decisions

Date: October 21, 2026. Status: initial scope and contract limits recorded; core application did not start.

## Decisions

| Subject | Decision |
|---|---|
| License | Original contributions of TaskVex MIT. Copyright line TaskVex contributors. Third party terms are maintained separately. |
| Reference | There is no Hermes. Mark LVI reference only; No automatic code transfer. |
| Platform | The first target is the Windows desktop, single local user. User ID Bot/lot is the next stage. |
| UI | In the current location of v1/ui, vanilla ES modules are preserved. There is no new framework. |
| First host | PyWebView; The actual native launch will be confirmed in Phase 2. |
| Working model | Small Python core, single registry and initially single task worker. |
| First tools | notes.add/list in Core tests; In the first slice of the UI bridge are settings and read-only system.status. |
| First plugin | apps.open/apps.status; real Windows trial with Notepad from the authorized catalog. |
| Data | It can be replaced by TASKVEX_HOME; Windows default is %LOCALAPPDATA%/TaskVex. Tests separate temporary root. |
| Model/voice | It is not required for the first core; After the tool line is verified Gemini/Live. |
| Plugin installation | Reliable application plugins that are registered as open at startup. There is no automatic Python import when you drop a file. |
| Authority | Model/plugin does not authorize. The first policy only allows defined low-risk transactions; others are explicitly rejected. In the phase without confirmation UI, risky transaction will not work. |
| Error | Acceptance, completion, failure and uncertain outcome are separate. No fake success or auto-repeat of obscure action. |

## UI status and write ownership

Current 5.R7.2: native timer/stopwatch records are owned by a single RAM Clocks owner;
UI/model goes to the same tools. The following local counter row is the historical value of the first slice.
is the decision; It no longer tells native authority except in browser-only mode.


Updated addition: In Phase 3, native note ownership moved to the backend; old note transfer
It is implemented with explicit user consent and a one-time flag in the same file. generic
does not write save notes; browser-only mode remains local. First slice chart below
It is the historical starting decision; current contract [STAGE3_NOTES.md](STAGE3_NOTES.md).

This table is the decision to be used when applying the backend; It does not change the behavior of the current UI today.

| Area | Current owner | My first native language | Next pass |
|---|---|---|---|
| Theme, colors, profile, layout, SFX, preferences | settings.js + localStorage | The backend persists the settings fields allowed in the save; registration final result required | Update with version/revision; secrets are not included in this field |
| Notes | notes.js, save payload and note_* events | Native note writing is not yet connected; local mode preserved | Const note_id + request_id; single backend CRUD owner; save does not rewrite notes |
| Skill definitions | skills.js + save/skill_* | Only current local definition behavior; backend execution not supported | definition/command distinction with single write owner and version |
| Routine definitions | routines.js + save/routine_* | Current local behavior | Definition storage and triggering are separate; UI scheduler is stopped while the backend takes over |
| Counter/stopwatch | timers.js | UI local owner | When Core tools are added, remaining time and trigger authority are explicitly delegated |
| Timeline | panels.js + taskvex_tl | UI view log; not considered evidence of task execution | Separate backend task log if necessary |
| Device listings and real camera/audio | Backend/hardware required | Not supported; open unavailable/not_implemented | Actual inventory and status from backend; selection preference not evidence of physical action |
| Model/voice catalog and link | Backend required | Offline; empty catalog/appropriate unavailable | Model cannot be sent online (true) without logging in |
| CPU/RAM etc. | connections.js view | system.status generates measurement adapter; UI displays alone | Missing/null/zero leaves based on current contract |
| Google, location, calendar, messaging | Backend required | Not supported | Provider adapter + policy; session/account scope retained |

### Double write limit on notes

In the October 21st base test, a UI note add action produced both save and note_add. This is the observed behavior for the current browser mode; It is not allowed to connect two separate backend write handlers. While the native note protocol is changing, api.js/app.js/notes.js/schema.js/settings.js will be discussed together. Two notes with the same text should be able to be deleted with different IDs. The absence of old backup and backend data files should be managed with open data transfer; The empty backend snapshot should not silently delete local notes.

## Event routing groups

| Event group | Handler owner / first behavior |
|---|---|
| ui_ready | Bridge/bootstrap: verified first snapshot, catalog/support information; the pattern is not an online signal |
| save | Setting handler: verify and save allowed setting fields; Burning the entire incoming object directly to disk. Creating a conflict with notes/skills/routines ownership |
| note_add, note_done, note_del | Not handler: mutation not committed until native CRUD protocol completes |
| skill_save/delete, routine_save/delete | Description record; native ownership is not implemented until designed |
| run_skill, run_routine, text, stop_task | Common command/task line; If the model/skill executor is not yet available not_implemented |
| device, query_devices, mic, mute, audio_listening, camera, screen_share, noise, wake_sens | Hardware/session handler; UI preference and physical result are separate |
| query_camera, query_location | Read-only absolute status query; If there is no real owner, a successful situation cannot be made up |
| reconnect, disconnect, restart, shutdown, closed | Session/app life cycle; restart/closing is verified from the real resource owner |
| google_connect, location, model, voice, media | Related integration/session handler; open rejection if not ready |
| apikey | Credential handler; no support yet. Generic save does not write to log or ordinary JSON |
| layout, timeline, timeline_clear, drawer, inspect, shortcut, export, cal_soon | View/notification or redirect to relevant domain; You cannot run a business by looking at the name. Actual payload and UI behavior is controlled by resource contract |
| reset, ontop | Reset scope only open user settings; ID information/other files are not deleted en masse. ontop native window preference |
| Undefined event | {ok:false,error:{code:"not_implemented",message:"..."}} suggested native raw response. emit wraps this as the failed result transport/request; No fake completed |

The source event inventory is in baseline.json; regex only outputs literal emit names. Names such as Camera/location and conditional/computed were also manually examined. This list is not a list of executive powers.

## First core contract limits

- request_id: same task if repeated with same content; the same identity with different content is rejected. Initially, relapse prevention is included in the session; No claim of exactly-once after crash.
- ToolSpec: name, description, input scheme, handler and the really necessary declaration permission/source.
- Mission: queued/running; awaiting_approval if necessary; Result succeeded/failed/cancelled/unknown. Accepting cancel_requested does not mean that the cancellation is completed.
- If the tool result is empty or does not comply with the contract, it is not considered succeeded. Expiration does not prove that the side effect does not apply.
- Routes Bridge setting/read-only requests; model/tool/skill execution goes through the common TaskManager. A separate player is not produced for the UI and the bot.
- If the waiting worker can continue the physical operation, the desktop lock is not released until the secure end is observed. Thread timeout does not kill the thread.
- Unexpected handler error does not close UI; The log is masked. Subscriber Log/event's bug does not replay the completed side effect.

## Base validation

Evidence: [baseline.json](stage0/baseline.json), [1280×800 baselineimage](stage0/ui-1280x800.png).

6 targeted checks passed: HTTP opening/bridge alias; observation of save + note_add conflict; grade renewal permanence; Applying the backend snapshot without generating outbound; invalid snapshot preserves current note; No pageerror/unhandledrejection in the attempted stream. SHA-256 values ​​of module HTML/CSS and 13 JS were saved, the source did not change during the check.

Environment: headless Edge, new isolated browser profile, localhost HTTP, external network blocked; Non-native onEvent simulation. The user's browser profile/notes was not used. This is not a full UI check or actual PyWebView/hardware testing. The test script is in file work/diagram-check/stage0-baseline.mjs in the current Codex workspace; portable project tests will be added in Phase 1.

## Closing and remaining

October 21 update: note Local recording of add/done/del transactions now uses emitSave:false; The user action only produces the corresponding note_* event. The double event observation at stage 0 is the historical before state; The current validation is in [note-events-fix.json](note-events-fix.json). Verified insertion/completion/deletion, refresh, no-echo and explicit save behavior in two migration scenarios (fallback and simulated native). Fixed identity/native ownership work remains in the next stage.

- User reported taking UI backup; The contents of the backup were not further verified in this round.
- Added MIT LICENSE, reference exclusion rules and THIRD_PARTY_NOTES.md.
- Initial core coverage, event/data ownership and acceptance limits recorded.
- UI files were not modified; No running backend, plugin or model session has been created.
- Complete asset/copyright history and dependency license inventory pre-release open job. The MIT file does not mean that every previous entity's license has been verified.
- Git commit repository/ilk was not installed in this task. New core dependency versions will be selected and verified in the Phase 1 implementation.

Next implementation: Phase 1. First request/result + registry + small TaskManager + policy + atomic registry and isolated core tests. Gemini, GUI layers and plugin store are not included in this package.
