# Stage 5 — common architectural compliance check

## Current 5.R8.2–5 link fixes

Removed fixed boss/say path at timer end. Host real clocks record
confirms and reports in the tool catalogue, available, with TextChat/PersistentLive available.
Natural language actions from the model remained on the same registry/policy/TaskManager line;
The notification adds no action permissions. UI poll view and idle notification queue
nourishes; There is no second worker, timer, microphone or audio player.
The catalog is automated; existing credential/model setting repositories were used.
The portion of the noise/wake sliders that were not displayed but implemented were linked to their respective owners.
Other planned missing integrations remain open below; debloat/closing note made.

October 23, 2026. Scope: model in source code → tooling → core flow, UI events and
current ownership of data/source. All hardware and future integrations are working
not claimed. 5.R4 moved the sleep transition, 5.R5 moved the note targets to the common line;
The application of other findings was not opened in this step.

| Status | Finding and source | Required action |
|---|---|---|
| Ported in 5.R4 — user accepted | The decision to sleep was in sentence patterns `sleep_intent.py` | The file has been removed. `assistant.request_sleep_mode` is now in the path ModelTools → registry/policy/TaskManager. The user was moved to commit 5fb30d3 with testing approval. |
| 5.Ported in R5 — user accepted | Removed endnote and content filter sentence patterns in `model_tools.py::_check_note_target` | Registered `notes.select` produces real ID/cardinality/snapshot; single mutation and atomic `notes.delete_many` use the same core line. 5.R6 adds the same full-group completion as `notes.complete_many`; text/ID/date is protected. Uncertainty, fresh election, date, Stop/unknown/replay protection lasts. |
| On — routine/skill playback integration | `ui/js/routines.js::runRoutine` and `skills.js::runSkill` are sending unsupported `run_routine/run_skill` events; bridge rejects them as not_implemented | Registry/policy/TaskManager player works without adding feature counting. “Routine started” / “Skill run” records in the Timeline are produced before the actual acceptance; Acceptance and initiation should be separated. |
| Open — routine transfer of ownership | `routines.js::initRoutines` has 15 s interval time control of UI and trigger input app/Wi-Fi | Release two triggers at the same time when backend scheduler is added; Close UI scheduler and switch to single execution owner. There is no second backend scheduler at the moment. |
| Planned undercoverage | Routine/skill definitions are stored in UI store/localStorage; native `validate_settings` does not write these to settings.json. Counter/stopwatch moved to single backend Clocks owner and clocks.create/list/control tools in 5.R7.2; browser-only single view maintained in separate environment | Use the configured tool/single data owner when opened to the model. Second mutation binding to generic save. Don't break native UI functionality today. |
| Planned missing links | `settings.py` profile can store pMem/pSys/pGreet/pBr and conn.voice fields; `model_instruction.py` only links pLang/pIns to the model instruction. pWake is used in the native engine, pSc is used in UI shortcuts. Live setup sound selection does not work; REST uses TTS Korea | Counting feature that works on recordable area. User memory and voice/persona preferences should be linked to their current owners when they reach their stage; Hidden or entire profile fields should not be automatically transferred to the model. |
| Planned undercoverage | Weather, Google, Telegram, Discord etc. There is no working core tool yet for | These do not work by changing the language. When the stages come, the provider adapter and the common tool/permission line should be added. |

## 5.R7.2 addition — multiple timer/stopwatch

Native single Clocks example is shared by bootstrap and bridge. Model and
UI mutations are on the registered clocks tools/policy/TaskManager line. pure
The host view read is a snapshot of this object; Not every UI tick will open a quest.
The native fallback engine stops when native starts; It cannot be reopened with the loss of the bridge.
The UI selects a record by id, the model process moves to the correct tab. new framework,
There is no service worker or persistent data authority. Application closing ends the hours.

## 5.R7.1 addition — application closure

assistant.request_shutdown is on the same line as ModelTools/registry/policy/TaskManager.
Core does not close a window; After answer/ring, the application changes the current Shutdown host owner.
calls The second closing path with the button is not established. Stop/old turn/unknown/replay
is protected; There is no OS shutdown authority. Counters were the next tranche during 5.R7.1; Described above in 5.R7.2
Moved to single Clocks owner.

## Protected correct boundaries

- Note CRUD and application tools are registered in bootstrap, policy controlled and
  It is executed via TaskManager. Native not UI events also go to this core.
- The model has no grade authority without grade transfer approval; new sleep tool note
  does not expand its authority. No new permissions were given to resources other than desktop.
- 5.F4 wake variations cater to KWS/Live in single local wake_spellings definition
  shares control. This is not a natural language action parser or new tool executor.
- Microphone, wake-word, Live socket, audio playback and window/setting/key life
  cycles remain with their current owners. These have direct host control
  It is not an architectural violation per se; They are not natural language command parsers.
- Sleep tool acknowledgment only generates pending request (`applied=false`). successful
  talk/play and real `sleep_start` result are separate; old tool replay new
  does not produce transitions. Stop/unknown/failed request is not implemented in round.

## Verification limit

Current 5.R5 proof: 885 full pytest, 62 after last change selection/batch
regression, 7 JS suite, Pyright 0 error/warning, REST/Live batch chat and
[full native 10/10](stage5-note-selection-batch-native.json). text with selection
Rejection, single text, readback, stop and replay were tested in data exchange between .
5.R5 real user acceptance successful; Included in commit `2120113`. 5.User acceptance of R6 completion is also successful.

Synthetic SDK/HTTP/WebSocket tests, core and native WebView2 controls
is used. No real account, user notes or paid API used.
For the synthetic provider to choose the right tool, the real model has all the natural language
It is not proof that you will choose the variations correctly. User acceptance is also required.

Previous 5.R4 proof: 17 targeted tool tests, including 873 full pytest + suffix Stop tests
7 JS suite, Pyright 0 errors/warnings and [10/10 native](stage5-sleep-tool-native.json).
In the first native run, the chat startup gave a readiness timeout; next isolated
chat and full run passed. The cause of the first error was not determined. Four old catalogs
expectation updated to include new tool; Note permissions remain narrow.
