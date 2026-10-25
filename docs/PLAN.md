# TaskVex — Current plan

## Now: 6.2.5c accepted; next planned slice is 6.3 file reading

User accepted 6.2.5b after the identity fix; committed as c8d159d before this step.
The requested new scope is application volume, explicitly excluding Windows master
volume. The user reported successful tests and accepted this step. No 6.3 implementation
has started; the accepted changes are committed under AGENTS.md.

- [x] Remove visible operation text below playback buttons; retain accessible status/logs.
- [x] Theme-bound PLAYER VOLUME range, confirmed OS level, one write on change.
- [x] Shared media.control set_volume action for UI, REST and Live, with fresh targets.
- [x] Exact source/process matching, active-session selection and ambiguity refusal.
- [x] Readback, Stop/unknown/replay, device/session identity, mute and master-volume boundaries.
- [x] 1,230 full pytest, 76 focused media tests, 9 JS suites, 19 browser groups,
  10 sequential native phases, app/focused-test Pyright 0 and clean dependency check.
- [x] User reported successful tests. Specific provider/hardware coverage was not separately enumerated.

Core Audio controls the matching application's shared-mode audio session. Browser
volume affects that browser's audio, not just one tab. Multiple active matches,
unmapped app IDs, inaccessible/unsupported sessions or exclusive-mode audio may
disable control; no fallback to system volume or another application is allowed.
Mute is preserved, and TaskVex does not save a competing volume preference.
Native and aggregate evidence: reports/media-volume-native.json and
reports/media-volume-checks.json. Existing persistent-unknown and native-test
teardown/type-complexity limits remain unchanged. The portable demo was not rebuilt.

## Remaining stage 6 work — current summary

- 6.2's implemented telemetry/network/token/media slices are accepted. Sensor
  temperatures/VRAM and a real API transport-latency metric remain explicit source
  limits, not silently completed functionality.
- 6.3: file attachment/reading first, then authorized modification with exact
  targets, bounded reads, readback and cancellation/replay protection.
- 6.4: weather/location and web search; permission/manual location, caching,
  freshness and untrusted external-content boundaries.
- 6.7 prerequisites: approve risky external writes, enforce channel/principal
  authority, handle untrusted content and reconcile unknown delivery outcomes.
  These relevant protections must precede 6.5/6.6 writing, despite their numbering.
- 6.5: Google OAuth and Calendar/Drive/mail in separately verified slices.
- 6.6: Telegram/Discord channels with real destination IDs and delivery evidence.
- 6.8 remains a scope recommendation: camera, Live screen sharing and additional
  audio sources, each with permission/cleanup; separate from GUI automation.
- Remaining 5.F8.3 profile fields (greeting, bounded personal instructions,
  browser/application preferences and shortcuts) attach to their relevant slices.
- Stage 6 closure needs current regression and accurate documentation of remaining
  limits. Skill execution and GUI layers remain stage 7; routines/reminders and
  the single backend scheduler remain stage 8.

## 6.2.5b Windows media controls — accepted by the user

The current user instruction authorizes this next slice. The preceding read-only
implementation is already published; the user has now accepted the media tests and authorized continuation;
the accepted step is committed before the requested volume/UI work under AGENTS.md. No later integration is included.

Manual acceptance failed: all dashboard media controls returned media_target_changed.
A read-only Windows probe reproduced unequal session identities from two separate
manager activations despite identical metadata. Media now retains and reuses its
issuing manager for polls and control revalidation. Synthetic identity-regression
tests cover all four actions, worker-thread use, empty sessions and source recovery.
Real read-only polling now preserves the target; cancelled preflight reaches
cancelled instead of false target_changed, with no playback action dispatched.
User retest passed. See reports/media-identity-fix.json for verification and remaining provider boundaries.

- [x] Shared Media owner, explicit media.control capability and versioned UI command.
- [x] REST/Live structured calls with fresh current-turn media.status target IDs.
- [x] Play/pause state and previous/next track readback; no success from acceptance alone.
- [x] Pre-dispatch target/cancellation checks; replay protection and persistent unknown lock.
- [x] UI capability/staleness/chat locks, pending deadlines and late-response isolation.
- [x] Identity-fix checks: 1,196 pytest, 42 focused media tests,
  10 sequential native phases, app/focused-test Pyright 0 and clean dependency check.
  UI code is unchanged in this fix; the preceding 9 JS suites and 18 browser groups passed.
- [x] User reported successful media tests after the identity fix. Actual provider coverage was not specified.

Only the OS-selected current session is controlled. Same-title skips or a previous
command restarting the current track cannot be verified by metadata alone and may
lock as unknown. Unsupported players/actions remain disabled. There is no arbitrary
app/session picker, volume command or automatic retry/reconciliation UI.
Current native evidence is in reports/media-identity-native.json and the fix summary
in reports/media-identity-fix.json. Original slice evidence remains in
reports/media-control-native.json and reports/media-control-checks.json.
The earlier intermittent pythonnet/WinForms teardown race remains an open boundary.
Expanded type checking of native_smoke.py also reproduces its existing function
complexity diagnostic on both HEAD and this change; it was not hidden or called fixed.

Previous 5.R8.6 user acceptance successful, in commit 526bfed.
5.F6 maintenance accepted by user; In commit ea8aa15.
5.F7.1 single-instance slice implemented and auto-verified. User continues and
gave push approval to GitHub; Released with 5c338e8. No separate physical test results were reported.
5.F7.2/3 implemented: 1017 pytest, 17 targeted log tests, Pyright 0 and 10 native
The phase has passed. User confirmed continuation/commit; In commit 5c21156, there is no push.
5.F8.1 only binds the response volume to the current preferences and player. sound
character connects at 5.F8.2; Other profile areas are covered separately as 5.F8.3.

- [x] Initial inventory and confirmed commit of the previous step.
- [x] Move historical documents under docs/archive with their original path.
- [x] Remove dead paths; used/nearby keep planned UI data.
- [x] Separate growing UI modules according to liability boundaries.
- [x] Source/test/config/document inventory, architecture and stable setting review: docs/AUDIT.md.
- [x] Current architecture/plan/changelog/contract/READMEs; archive hash record.
- [x] 996 pytests, 9 JS suites, 4 browser groups, 10 native stages and targeted Pyright 0.
- [x] Archive hash, current document links and open border report: docs/AUDIT.md.
- [x] Maintenance user acceptance → ea8aa15 commit. Phase 5 closure awaits the following open jobs.

Debloat does not remove security/authentication/Stop protections. REST and standalone browser
UI mode is preserved. Pending skill/routine definitions are not deleted. Future features
It is not shown as if it is working today.

## Roadmap

| Stage | Status | Scope |
|---|---|---|
| 0 | Basic ok | MIT, data ownership and the reference/license limit |
| 1 | The basics are okay; permanent daily/retention accepted | Contracts, registry, policy, single TaskManager, JSON record |
| 2 | Basic ok | PyWebView2 host, bridge, settings/identity repository, native lifecycle |
| 3 | OK/accept was | Backend note CRUD/transfer/backup and real IDs |
| 4 | First plugin ok | Allowlist Notepad catalog/status/open; not general GUI automation |
| 5 | Functional basic acceptance; remaining limits saved, user requested to move to stage 6 | Gemini REST/Live, sound, Stop/interrupt, resume, temporary memory, sleep, note/counter/shutdown |
| 6 | 6.1 memory slices accepted by the user; next 6.2 | Persistent user memory, L0 capabilities, Google/Telegram/Discord and profile fields |
| 7 | Did not start | GUI resolver, L1 recipe, L2 DOM, L3 UIA, L4 vision and skill execution |
| 8 | Didn't start | Single backend routine/scheduler, services, distribution/packaging |

Current architecture ARCHITECTURE.md, modifications CHANGELOG.md. Old detailed acceptance and
step numbers are historically preserved in docs/archive/stages.md.

## Stage 5 closing limits

- Functional slices (REST/Live Stop, resume contract, note selection/CRUD/batch
  transaction, audio/transcript, volatile memory, sleep/wake, closing and counters) applied;
  The user reported successful testing for the latest slices. Acceptance of this care is separate.
- The old 5.F5 long/physical test was removed from the separate step by user request;
  The overall regression is preserved. A new forced long user test is not invented.
- Real account resume/GoAway and provider delay acceptance API limit
  could not be retested due to Synthetic success is not proof of real provider.
- In persistent core, 256 is now the work limit of RAM/active; disk history is preserved.
  The logless isolated TaskManager retains the old safe total limit.
- Restart log does not replay what has been completed; started half job unknown, queue
  will be cancelled. Unknown has no mediation screen; The lock is not removed with a restart. disc
  history grows and can keep old note contents; There is no automatic cleaning.
- Native single-instance lock implemented in 5.F7.1; direct script writers are the same
  Must use host lock agreement. Third party/entity packaging licenses before distribution.
- Short user acceptance for 5.F7.2/3 → commit; before these conditions are considered resolved
  There is no unlimited/production ready claim for Stage 5. Developing with open boundaries
  The decision to continue and the next single step is determined by the user.

## Substeps of subsequent stages

They have not yet been implemented; The desired single slice in each prompt is also narrowed down.

| ID | Purpose and acceptance limit |
|---|---|
| 6.1 | Manual/from the model memory, suggestion, ask and button/talk decision accepted by the user; last commit 6f52b4c |
| 6.2 | Telemetry/app/media tools; each measurement/process with real source and verification |
| 6.3 | File reading, then controlled modification; target/permission and readback |
| 6.4 | Weather/location permission and web search; approval and external content limit |
| 6.5 | Google Drive/Calendar/mail; OAuth scope, renewal, connection and transaction proof |
| 6.6 | Telegram/Discord input-output; principal/target authorization, no replay on indefinite delivery |
| 6.7 | External data taint/risk approval/channel authorization and unknown reconciliation on the current task log; 6.5/6.6 writing prerequisite |
| 7.1 | L3 UIA target and result verification in one application |
| 7.2 | L1 verified prescription; old target not used in context switch |
| 7.3 | Browser L2 DOM, budget L4 when needed vision/OCR |
| 7.4 | Skill JSON execution; same registry/policy/TaskManager, no free eval |
| 7.5 | DPI/window/old target/permission/unknown regression |
| 8.1 | Single backend scheduler; no second UI player |
| 8.2 | Routine ID CRUD/trigger; notification separation with double operation |
| 8.3 | Background services opened by the user and limited/masked log |
| 8.4 | Schema migration, crash recovery and secure update |
| 8.5 | Packaging, single-instance integration acceptance, license/SBOM and clean installation |


## 5.F7 — Closing the first three audit findings

The order was chosen based on dependency; With user approval, 5.F7.2 and 5.F7.3 were combined in the same round.

| Step | Scope | Status |
|---|---|---|
| 5.F7.1 | OS single-instance lock for the same data root; crash/exception/restart/separate profile | Implemented: 1000 pytest, 10 native stages, Pyright 0; [evidence](reports/instance-checks.json). User confirmed continue/commit/push; no separate physical test report |
| 5.F7.2 | Persistent task/request log; After restart, old completed or indefinite operation will not be executed again | Implemented/auto verified; [evidence](reports/task-journal-checks.json). User continuation/commit approval; In commit 5c21156, no push |
| 5.F7.3 | Terminal record retention by maintaining permanent dedup; The 256 limit is for active jobs, not lifetime total | Implemented/auto verified; 300 jobs (capacity 4/256), active queue and legacy replay. User continuation/commit approval; In commit 5c21156, no push |
| 5.F8.1 | Vex reply volume separate from effects under Settings Audio; same PCM gain, record/snapshot/reset/Mute | Implemented: 1024 pytest, 9 JS, 5 browser, 10 native, Pyright 0; [evidence](reports/reply-volume-checks.json). The user confirmed that it worked; commit approved |
| 5.F8.2 | Documented preset Live voices, [LIVE] tag, conn.voice → speech_config; key input status statement | Implemented: 1025 public pytest + 24 final targeted tests, 9 JS, 5 browser, 10 native, Pyright 0; [evidence](reports/live-voices-checks.json). The user gave confirmation to continue; did not report separate physical sound test |
| 5.F8.3 | Further determine the required scope of the remaining profile/base instruction/greeting constants | It has not been implemented yet; persistent memory and stage 6 limit of integrations are preserved |

5.F7.1 lock is for native host. 5.F7.2 create_core entry also log/core
Adds OS lock; The direct JsonStore writer still cannot bypass this ownership. daily
and not/outer transaction is not a single transaction; By deleting lock/daily files
“Cleaning” should not be done.


### 5.F7.2/3 — applied scope and acceptance

- **5.F7.2 — persistent task log:** under sole ownership of the same data root
  request ID/finger keep trace and execution state persistent. completed same
  Don't let the request run again; Reject conflict identity/content. during crash
  A job that has started but whose outcome is unknown should remain unknown and should not be repeated automatically.
  Safely prevent daily side effect if it cannot be written/broken; with temporary data
  separate process/restart/crash tests and current Stop regressions are mandatory.
- **5.F7.3 — capacity/retention:** only after 5.F7.2 is verified. 256
  During the process, the total work ceases to be a limit; RAM/active tail limited again
  let it stay. Old terminal records should not delete move/store replay information.
  More than 256 consecutive jobs, full active queue, repeat of old request and restart
  Verify with tests. Just enlarging the border is not a solution.

Two implemented: **1017 pytest**, 17 targeted log test, targeted Pyright **0** and
**10/10 native** stage passed. [Test proof](reports/task-journal-checks.json),
[native evidence](reports/task-journal-native.json). Real account/API and physical sound
not tried again. User confirmed continue/commit; did not report separate physical tests. 5.F8.1 response volume applied/auto verified; voice character 5.F8.2
It is implemented as; Other profile gaps are waiting as 5.F8.3.


### 5.F8.1 — scope of acceptance

- Same live_audio GainNode: current percentage, selected level when mute;
  Live/REST/timer sounds common; microphone and effect level are independent.
- UI preference and native schema: 0–1 validation, default 1 on legacy registration,
  zero protection, snapshot/native reopening and reset in process 1.
- No new scripts, provider requests, frameworks or second players.
- Targeted PCM tests, browser/native setting-recording-closing and necessary regression.
  Physical speaker acceptance lies with the user; Paid API is not used in testing.


5.F8.1 latest verification: **1024 pytest**, **9 JS suite**, **5 browser groups**,
**10/10 native stage**, app Pyright **0**. [Abstract](reports/reply-volume-checks.json),
[native evidence](reports/reply-volume-native.json). Paid API and physical speaker
acceptance was not attempted. The user confirmed that it worked; Commit approved, no push.


### 5.F8.2 — limit for this round

- Single allowlist from 30 ready-made Live sounds in Google documents; [LIVE] UI tag.
  Voice discovery does not appear to be from the API. conn.voice is in the global settings repository.
- The selection goes to the next Live text/microphone/timer round; active response is not interrupted.
  Voice change does not use the old resume handle. REST TTS and security pipeline are protected.
- Presence of key in input placeholder; the actual value/secret is not kept in the DOM.
  Unsuccessful registration is not offered as successful API connection.
- 5.F8.1 confirmed as working by user; In commit 9d67a1d.
  The new slice's user waits separately for acceptance/commit; Stage 5 is not considered closed.


5.F8.2 verification: **1025 public pytest**, including additional final catalog check **24 targets
profile/sound/document test**, **9 JS suite**, **5 browser groups**, app Pyright **0**,
**10/10 native stage**. [Abstract](reports/live-voices-checks.json),
[native evidence](reports/live-voices-native.json). Real account and physical voice
not accepted; the user has given approval to proceed to stage 6; did not report separate physical voice testing. The clear boundaries of Stage 5 are maintained.


## 6.1 — user memory slices

The user requested a move to stage 6; provider/physical acceptance of stage 5,
unknown mediation, license and remaining profile fields are not considered closed.
Previous Live sound selection is in the 2cebea8 commit; no push.

| Step | Scope | Status |
|---|---|---|
| 6.1.1 | Open shipping preference in Personalization; save/view/edit/clear, REST/Live context, dropping old chat context; Remove New Chat button | Implemented: 1035 pytest, 9 JS, 6 browser, 10 native, Pyright 0; [evidence](reports/personal-memory-checks.json). User agreed; In commit e7f3ce4 |
| 6.1.2 | See/add/correct/forget model via memory; ModelTools with single record authority and snapshot verification → registry/policy/TaskManager | Implemented: 1050 pytest, 9 JS, 7 browser, 10 native, Pyright 0; [evidence](reports/model-memory-checks.json). User agreed; In commit 50421c3 |
| 6.1.3 | Consensus with model inference, ask/auto-save preference, button or next user response | Last verification: 1081 pytest, 9 JS, 9 browser, 10 native, Pyright 0; [evidence](reports/memory-voice-review-checks.json). User agreed; In commit 6f52b4c |

6.1.1 does not automatically learn; legacy legacy pMem text is off by default. permanence
is the current settings.json profile; There is no additional database. Remember, it does not interrupt the active response,
The history provider does not delete records/backups. Invalid record/disk error success
does not count. New Chat UI and unused handler removed; internal reset
The endpoint is retained for the existing core test/future channel contract.


6.1.1 latest verification: **1035 pytest**, **9 JS suite**, **6 browser groups**,
**10/10 native stage**, app + new memory test Pyright **0**. first browser
checkbox bug fixed; native history-text wait and profile recovery
The expectation was clarified according to the new contract. [Report](reports/personal-memory-checks.json),
[native](reports/personal-memory-native.json). Real account/paid API and physical
recall/sound no test. User tests reported success; commit approved.


### 6.1.2 — explicit model memory operations

- The previous slice was moved to commit e7f3ce4 with user testing approval; no push.
- memory.read/patch on single settings.json/prof.pMem; explicit pMemory preference,
  fresh turn/snapshot, unique text target and verified readback.
- Short repository lock shared with UI save/reset; restore memory of old form
  memoryBase comparison preventing it from writing. Public schema moved to storage.
- REST/Live is on the same line as catalog/ModelTools; Timer notifications are tool-free.
  As a result, the current profile returns to the UI, there is no second mutation. Next round old
  Drops context socket/RAM; Late Stop does not undo the completed recording.
- Automatic exit decision/recommendation 6.1.3 waits. No real account/paid API;
  automatic verification does not replace user acceptance.

6.1.2 latest verification: **1050 pytest**, **9 JS suite**, **7 browser groups**,
**10/10 native stage**, app + new model memory test Pyright **0**.
[Abstract](reports/model-memory-checks.json), [native](reports/model-memory-native.json).
Failed intermediate attempts are preserved in the report; paid API/real model and physical
No audio was accepted. The open form outline is preserved; Restart the application in case of conflict
It may be necessary to open it. User tests reported success; commit approved.


### 6.1.3 — offering personal information without speaking and confirmed registration

- The previous slice was moved to commit 50421c3 with user testing approval; no push.
- Default off pLearn; Same REST/Live conversation with pMemory
  Opens memory.propose in the model. There is no additional inference API or new repository.
- The source quote links to the actual text/Live transcript of this round;
  Host proof is not taken from the model. If there is no source, the suggestion is skipped and the conversation continues.
- Single RAM candidate; approval/rejection only UI memory.decide → registry/policy/TaskManager.
  The model cannot confirm the suggestion; In this mode, the new addition cannot exceed the append path.
- The confirmation is written to a single profile with the existing append/readback. Old ID, rejected, changed
  permission/snapshot and restart do not automatically turn the candidate information into reality.
- The third person/quote/joke of the model/sensitive information separation agreed with the actual provider
  not done; human review is therefore protected. Voice confirmation is not available in this language.

6.1.3 latest verification: **1065 pytest**, **15 targeted recommendation tests**, **9 JS suite**,
**8 browser groups**, **10/10 native stage**, app + new recommendation test Pyright **0**.
[Abstract](reports/memory-suggestions-checks.json), [native](reports/memory-suggestions-native.json).
Interim test assumptions and open limits are in the report; real/paid API and semantics
Inference quality was not tested. User expects acceptance/commit; The new phase was not progressed.


### 6.1.3 fix — disclaimer of source citation in actual conversation

- User reported failure in manual testing; previous synthetic success user
  It is not acceptance. Step reopened, no stage commit/next.
- Read-only diagnosis: actual memory.propose result source_unavailable,
  source_verified=false. Private conversation text Output/report not received.
- The source sentence rewritten by the model is identical to the real transcript.
  It was the wrong contract to match. Source now from current turn owner
  connects directly; The model does not generate source_quote. Replay preserves the old source.
- User approval, fresh snapshot, native decision and missing ASR protection are the same
  remains. The engine log only shows the safe error code.
- Paragraph regression test failed before correction; same sample after
  passed. REST/Live/long source and real native UI verification completed.

Source fix last check: **1068 pytest**, **memory/recommendation test with 33 targets**,
**8 browser groups**, **10 native stages**, app + recommendation testing Pyright **0** and
live-status JS package passed. [Report](reports/memory-source-checks.json),
[native](reports/memory-source-native.json). No real account was used; user
will reopen the application and test again. There is no step commit/next yet.


### 6.1.3 — visible review and optional prompt registration

- Memory.propose successful and Review memory suggestion on the user screen
  it seemed; The permanent space being vacant was the expected situation for the candidate awaiting approval.
  The user found this view inadequate and requested the ask/auto-save preference.
- pMemoryConfirm default is true: the confirmation window opens automatically. User
  if it saves false the same directly via propose → _apply append/readback
  is saved and refreshed from the editor backend. There is no new repository/executor.
- Preference permanent on UI/native/backup/snapshot; Can't choose model. In old profile
  The default is ask, changing the approval preference overrides the old snapshot.
- Direct recording capability memory.write, Stop/replay/readback protections
  is the same. After the decision, disk proof is required before the Save becomes a success.
- No user acceptance yet; The current 6.1.3 is not committed, there is no next step.

Latest ask/auto-save verification: **1074 pytest**, **33 targeted memory tests**, **9 JS
suite**, **9 browser groups**, **10 native stages**, app + recommendation test Pyright **0**.
[Report](reports/memory-review-checks.json), [native](reports/memory-review-native.json).
Actual API/inference accuracy has not been tested; user testing for both modes and
commit is expected. The new step was not taken.


### 6.1.3 — separate approval group and decision by natural conversation

The previous slice ask/auto-save was reported successful by the user; c5d086c
It was committed, no push was made. This round only changes to confirmation presentation/decision.

- Save/Dismiss, separate theme compatible group to the right of four controls under chat;
  There is no aday/approval in Personalization, the automatic modal will not open.
- Vex normally asks for permission on the response/voice line; next user reply
  memory.read → memory.decide → moves to the line registry/policy/TaskManager.
- Recommendation and self-approval block in the same round, fresh real ID, snapshot,
  The old UI/model decision, the verified result before replay and Stop are preserved.
- No separate TTS, sentence list, second registrar or API request added.
- Acceptance: button and buzzer yes/no saves/rejects same candidate first;
  indifferent/undecided should not be a response confirmation. Semantic decision also depends on the real model.
  It will be evaluated in user testing. Automatic verification is in progress.
- User acceptance/commit is expected for this new change; The next stage was not progressed.


Validation for this tick submission slice: **1081 pytest** (106.65 s), **40 targeted
memory test**, **9 JS suite**, **9 browser groups**, **10 native stages**,
app + recommendation test Pyright **0**. [Report](reports/memory-voice-review-checks.json),
[native](reports/memory-voice-review-native.json). Separate group on the right at 1920px,
Verified non-bleed view at 1280px. Actual API, physical microphone and model
Semantic confirmation accuracy was not tested. Waits for user acceptance and commit of this slice.


## 6.1 adoption and order of remaining UI bindings

User reported successful decision tests with button/speech. Related applications
Included in commit 6f52b4c; No push was made. Previous acceptance standby above
his notes describe rounds of historical verification; The current 6.1 status is accepted.
This type of new feature was not coded; The following tranches have not started yet.

| Row | Scope / acceptance condition |
|---|---|
| 6.2.1 | CPU/RAM/disk/battery/active exe co-owned and periodic UI/model connection implemented; automatic/native and user acceptance of this round are below |
| 6.2.2 | Windows PDH GPU usage adapter implemented; CPU/GPU temperature and VRAM capacity supported resource waiting |
| 6.2.3 | Network/Wi-Fi, instantaneous sending/receiving speed, link and latency; distinction between transfer speed and internet speed test; offline does not delete local CPU meter |
| 6.2.4 | Token counter from provider's actual usage data; turn/session and context boundary are separate; unknown account quota or estimated usage will not be shown as exact value |
| 6.2.5 | Current Windows media session: track info, play/pause/previous/next; UI and model have the same tool/area |
| 6.3 | File attachment/file reading followed by controlled modification; target/permission/readback |
| 6.4 | Weather, manual/permitted automatic location and web search; cache/last update and actual error status |
| 6.5 | Google link, Calendar/Drive/mail; before 6.7's relevant risk/channel/write protections |
| 6.6 | Telegram/Discord; again relevant protections of 6.7 prerequisite |
| 6.8 — scope recommendation | Separate slices for camera, Live screen sharing, and non-microphone audio sources in the UI; permission, visual/audio stream and resource cleanup; Separate from GUI click automation |
| 5.F8.3 remaining profile areas | The initial greeting, browser/tab/application preferences, and shortcut fields are linked to the corresponding application/file/browser slice; personal instruction will not base override beyond safety limits |
| 8.1 | The only backend scheduler available for true local reminders; The second timer is not written, although it is separate from the skill/routine execution |

Timeline/log remains the current local view; new data producers are only real
feeds events. Inspect/Create Skill, skill execution and routine scope are in this UI
It is outside the desire to prioritize. 6.8 approval or completion of a new application
It is not a claim; It is the proposed location of missing multimodal coverage in the current plan.


### 6.2.4 first tranche — final provider token notification

The user can complete the lightest phase 6 and commit directly with a limited round budget.
wanted; 6.2.4 was therefore brought forward. Live/REST usage metadata from current report
Connected to UI. If the limit is unknown, the number is shown alone; new turn/without data
The response clears the old value, zero is valid. The old setter limit agreement is retained.
Session total, fee/quota and model context limit were not applied in this small slice;
For 6.2.4 these are not considered done. The next feature step is still 6.2.1.
Real/paid No API call was made. The user has given explicit permission to this type of commit;
There is no physical user acceptance yet. Automatic results will be recorded in the report.


Token slice: **1091 pytest** (86.85 s), **96 targeted Python test**,
**10 browser groups**, **9 JS suite**, app Pyright **0**.
[Abstract](reports/token-counter-checks.json). Physical user/API awaits acceptance;
The explicit commit permission given by the user in this type is not presented as manual acceptance.

**10/10 native stage** also passed: [native regression](reports/token-counter-native.json).
SDK synthetic migration + browser view testing for token count; There is no real account.


### 6.2.4 — Calculation and execution session total in Gemini

The user wanted the entire session instead of the last notification this round. python token
The calculation is collected in existing gemini.py; Live and speech adapters
transmits its own metadata. The only RAM total in TextChat life is Stop,
Maintained in change Disconnect/model/key/context; It is reset on application restart.
REST tool turns and separate audio request are included. Live intermediate snapshots are the same
counted once in production; If metadata is missing, known total ≥/Incomplete is shown.
This change replaces the previous post-notification slice; quota/context/billing
There is no claim to accuracy. Metadata arriving late and not sent by the provider in Idle
usage is not questioned. Real/paid API is not used.

Added targeted SDK and app tests; general/native verification in progress.
This round commit/push was not requested: the new slice awaits manual user acceptance.
The next feature remains 6.2.1; No public provider framework added.


Session total last verification: **1101 pytest** (102.68 s), **138 targeted SDK/
session test**, **11 browser groups**, **9 JS suite**, app Pyright **0**,
**10/10 native stage**. Native UI confirmed the sum 10 → 20 in two answers.
[Abstract](reports/session-token-checks.json), [native](reports/session-token-native.json).
No actual API/billing inspection performed; User testing by reopening the application
is expected. No commits or pushes were made. The previous post-notice report is historical evidence.


### 6.2.1 — local measurements completed together

The user reported the token session test successful; commit later with explicit instruction
was left. User asked for things that can be done together in 6.2. This round is CPU/RAM, disc,
battery and active app connections are combined into the same Telemetry instance.
Win32 + standard Python was used; dependency not established. CPU is the difference of two samples,
RAM/disk GiB, battery missing/unknown and initial/missing/zero measurement separation is preserved.
The UI query does not poll the task log; model existing common tool line
uses. Only the exe name of the active application is taken; There is no document title and full path.
Also fixed local metric and session token total deletion when model is offline.

Scoped later: 6.2.2 Source hardware/sensor suitable for GPU/temperature;
6.2.3 Wi-Fi/network interface and traffic/latency; 6.2.5 Windows media session/controls.
These are not considered to be working in this language. Next scope 6.2.2 source selection and
It is the first supported hardware adapter; If necessary, unreadable hardware is clearly reported.
Weather/Google/skill/routine not covered. No commit/push with user instruction.


6.2.1 latest auto-verification: **1109 pytest** (160.19 s), **96 targeted tests**,
**12 browser groups**, **9 JS suite**, app + telemetry test Pyright **0**.
The first native turn was stuck in the 60 s time limit during the chat phase; concurrent pytest
The entire native suite repeated alone with the same time limit when finished
**10/10 passed**. The exact reason was not proven, the unsuccessful turn was not hidden.
[Abstract](reports/local-telemetry-checks.json), [native](reports/local-telemetry-native.json),
[initial timeout](reports/local-telemetry-native-first-run.json).
The real Windows CPU also passed the second sample/RAM/disk/battery read-only measurement check.
The actual API and model's interpretation of these new questions awaits user acceptance.
Previous token step user accepted; The commit of two slices was postponed by instruction.


### 6.2.2 — Windows GPU usage and system view

Previous token/local measurement steps are in eba75a5 commit with user acceptance;
No push was made. The first NVIDIA attempt was removed by user request. old
[nvidia report](reports/nvidia-telemetry-checks.json) and [native report](reports/nvidia-telemetry-native.json)
It is only evidence of the abandoned attempt; It is not an acceptance of current practice.

- windows_gpu.py: Windows PDH counters, single Telemetry owner, same
  registry/policy/TaskManager model line; There is no separate worker/model/store.
- Processes in the same engine are collected; The most intense engine of the card, the most powerful engine on the dashboard.
  The dense card is shown. The manufacturer executable/driver API is not called.
- First sample reference, real zero valid, lost counter unavailable; even old
  No GPU data remains and CPU/RAM is preserved. Native closing releases the PDH resource.
- Removed top comment line; GPU tag fixed. Your bar is the same as the percentage
  Width tested at 1280/1920 and 0/25/100.
- Adapters that provide Windows counters are supported; warranty for every old card
  There is no. CPU/GPU temperature and VRAM capacity are clear limits. There is no NVIDIA fallback.
- Direct read-only counter query on real Windows is successful;
  meter IDs are not presented as product name/Task Manager sequence number.
- Next standalone feature 6.2.3 network/Wi-Fi; This type of new feature phase is not possible.

Last verification: **1120 pytest** (127.49 s), **19 targeted tests**, **13 browser
group** (1280/1920 and GPU bar 0/25/100), **9 JS suite**, **10 native stages**,
app + GPU test Pyright **0**. [Abstract](reports/windows-gpu-checks.json),
[native](reports/windows-gpu-native.json). Fake PDH test at first type control
None-only field gave an error; It passed when the open type was added. True common Windows
Telemetry returned warming_up in the first example, GPU 8.4% and valid RAM in the second example;
The source was closed after reading. Physical devices from other manufacturers and real
model/paid API not tested. No manual user acceptance, commit and push.


6.2.2 user testing reported successful; Windows GPU/system view slice accepted.
In accordance with AGENTS.md, a commit is taken before the next step; push was not requested.


### 6.2.3a — passive physical network measurements

View GPU/system was accepted by the user and moved to commit 43c7f28.
received; no push. This type applies only to the network slice.

- Single Telemetry instance with IP Helper to view physical interface link status and 64 bit
  RX/TX exemplifies the meter difference; UI same query_system, model same system.status
  It uses the registry/policy/TaskManager line. There is no new worker/timer/store.
- UI Receive/Send gives information about Mbps, local connection and not Wi-Fi connected.
  This data is not an internet access test or maximum bandwidth.
- First example, reset, device cluster change and resource error do not generate speed; zero
  It is the actual measurement. VPN/virtual interfaces are excluded to avoid double counting.
- The name SSID/IP/MAC/profile is not imported into the model or report; The system table is left in finally.
- 6.2.3b: Wi-Fi with specific target limits ping/accessibility and permission/resource
  The signal percentage will also be done. API latency will not be mistaken for overall response time.
- This narrowing does not half accept the next feature: acceptance of slice a
  local counter/UI/model/reconnection tests; b remains open.

Last verification: **1132 pytest** (142.83 s), **31 targeted tests**, **14 browsers
group**, **9 JS suite**, **10 native stages** and app + network testing Pyright **0**.
[Abstract](reports/network-local-checks.json), [native](reports/network-local-native.json).
Failed two test isolation points in the first targeted round; insulation DLL
It passed when it was moved to its loader. Real Windows passive reading speed in the first example
did not produce, in the second example it returned RX/TX; private network ID is not registered.
The actual model/paid API and physical disconnection have not been attempted.
The user waits for acceptance; The new slice was not commit/push. Next up is 6.2.3b.


6.2.3a reported successful by the user; local network slice accepted.
Before the next step, a commit is made, no push is made.


### 6.2.3b — target on ping and Wi-Fi signal quality

6.2.3a accepted by user, in commit 3e3cb8c; no push.
The owner of this slice is the current Telemetry → Network; measurement adapter network_quality.py.
The model reads from the same line system.status → registry/policy/TaskManager.

- The lowest route for the active physical card among Windows IPv4 default routes.
  metric gateway is selected. UI Gateway ping only to this target, not to the internet.
  ICMP is round-trip. The address is not given out; There is no free target/DNS/speed test.
- ICMP wait 250 ms, normal quality query interval 10 s; rota/kart replacement
  clears old success. Source error, timeout, are divided into no_gateway/no_link.
- WlanQueryInterface opcode 19, which does not require a location, is used. current_connection,
  There is no BSS scanning or location requesting fallback. Unsupported OS/permission error
  does not produce a signal. A multi-connected Wi-Fi card shows the lowest quality percentage.
- Measurement in age/status tooltip; true 0% and 0 ms valid. Error old number
  does not make it appear as if it is up to date; CPU/RAM/GPU and traffic continues.
- No additional worker/timer/packet/store/model connection; ICMP/client handles and
  WLAN buffers are closed on all outputs. In native tests, every source is synthetic.
- API transport latency is still open limit; total model response time to this area
  It is not written. There is no external internet access, IPv6-only gateway or other hardware acceptance.
- Next standalone UI link 6.2.5 Windows media session/checks.
  6.2.4 session token sum has already been accepted; cannot be redone. API latency
  It is not complete until the actual source/contract is determined.

Last verification: **1154 pytest** (137.49 s), **53 targeted tests**, **15 browser
group**, **9 JS suite**, **10 native stage** and app + quality test Pyright **0**.
[Abstract](reports/network-quality-checks.json), [native](reports/network-quality-native.json).
Possible uninitialized two DLL variables in finally in first type check
found; Fixed with open condition startup/cleanup. Real Windows single instance
gateway 2 ms, Wi-Fi returned 91%; private address/identity not registered. Other hardware/old
Windows, physical reconnection and actual model interpretation have not been attempted.
User acceptance is awaited; This new slice was not commit/push.


6.2.3b user tests reported successful; quality bracket accepted.
A commit is taken before the next step; Pushing is not done.


### 6.2.5a — reading current Windows media session

Network quality moved to commit 9c607bb by user acceptance; no push.
Media coverage was divided into two slices: a reading alone, a verified mutation.
So you can verify the actual completion of the check by connecting the new OS adapter.
they are not combined in the same claim of acceptance.

- The media field owner is given as the same example from main to core and bridge.
  query_media returns a pure snapshot to the UI; model media.status → registry/policy/
  Uses TaskManager + media.read privilege. REST/Live is in the same catalogue.
- WinRT GSMTC: title/artist/state information of the current session selected by Windows.
  The browser tab or any output sounds are not read; There is no audio capture.
- 3s poll with current app tick; 2 s space cache, 2 s WinRT read limit,
  10s UI stale cleanup. There is no new thread/player/scheduler.
- Separated into session no, unsupported, timeout and unreadable. during transit
  if the session changes, the old title is dropped; The failed sample does not retain the old part.
- Four narrow WinRT 3.2.1 packages for Windows API projection to pyproject and lock
  added; dependency check passed. COM apartment init/uninit is balanced.
- True read-only query on Windows is successful; real title/artist
  not recorded. Automated tests use synthetic media; There is no control call.
- 6.2.5b: play/pause/previous/next, actual session target, stale/Stop/replay
  and provider acceptance-actual completion distinction. UI control buttons are off in a.

Last verification: **1172 pytest** (128.92 s), **138 targeted tests** (18 media
including field testing), **16 browser groups**, **9 JS suite**, **10 native stages**,
app + media test Pyright **0**, pip check clean.
[Abstract](reports/media-read-checks.json), [native](reports/media-read-native.json),
[first native failed turn](reports/media-read-native-first-run.json).
4 failed/1168 passed due to legacy catalog expectations in first full Python round
there was; When the expectations were updated with media.status, it was targeted and full circle.
The overly wide selector and SDK nullable metadata control in the browser have also been fixed.
The actual Windows reading returned available/paused; title/artist not registered.
No actual model/paid API or playback control attempted. New slice user
commit/waits; no push The next step is 6.2.5b.


### Windows x64 portable demo — packaging on request

User requested demo EXE; This does not mean that the production distribution phase is complete.
6.2.5a media still awaits user acceptance; 6.2.5b has not been upgraded.

- PyInstaller onedir ZIP: `v1/dist/TaskVexDemo-Windows-x64.zip`, about 40 MB.
  Python comes with; The whole folder should be moved. Windows 10/11 x64, .NET Framework
  4.8 and WebView2 required. Signature/installer/automatic does not have a runtime installation.
- The normal app.main owner is used; frozen restart opens the same EXE.
  The default demo profile is `%LOCALAPPDATA%/TaskVexDemo`; developer note/keys
  not taken The user enters his own key. UI tests/archive documents are not packaged.
- Wake weights were not ZIPed because the redistribution license is unclear.
  The open `Setup wake model.cmd` request uses the existing hash verification setup.
- Real packaged EXE: native UI/WebView2 in temporary keyless profile,
  CSS, RAM, sherpa runtime and WinRT import check passed. ZIP Turkish/with spaces
  It was extracted to another directory, Python environment variables were removed and passed again.
- Build entries `v1/tools/README.md`, fixed build versions are in separate lock.
  [Packet test report](reports/demo-build-checks.json).
- Clean Windows/other hardware, real Gemini, microphone, wake download and frozen
  restart has not been tried end-to-end; It is not assumed to work on all computers.
  Waiting for user packet acceptance; commit/push not made.

Demo additional verification: native bridge/instance lock **92 pytest passed** (9.76 s);
compileall and pip check clean correct venv with package tools/main Pyright **0**.
The first type round found incorrect interpreter import errors and metadata path type;
Fixed by collapsing interpreter selection/path. The package report also includes initial errors.


## English repository cleanup and requested GitHub publication

Scope: English guides/comments/docstrings/tool descriptions; source and archived
README accuracy; archive relocation and integrity; publish authorized outstanding
changes. This does not implement media playback, new integrations or later stages.

- Documentation is now maintained in English; AGENTS.md supersedes its former
  language preference. Turkish conversation and functional Unicode remain supported.
- Architecture and bridge contracts were manually edited for technical meaning.
  Historical files are translated under docs/archive; original hashes/revision are
  retained. Current archive hashes and links are checked separately.
- README corrects obsolete GPU/network claims and describes the portable demo,
  actual acceptance and remaining media-control/real-provider limits.
- Automated regression and publication evidence:
  [English cleanup checks](reports/english-publication-checks.json).
- The user explicitly requested commit/push. Publication authorization does not
  convert pending physical media/demo acceptance into a passed manual test.


English cleanup verification: **1,172 pytest passed** (167.09 s), **9 JavaScript
suites**, **16 browser groups**, **10 sequential native phases**, Pyright **0** and
clean dependency checks. The final archive/hash/link check passed **2 tests**.
Initial translated-fixture failures were corrected and are recorded in the report.
One concurrent native run crashed in pythonnet/WinForms teardown after successful
reopen checks; the sequential rerun passed. Its root cause remains open and is not
claimed fixed. Real-account/paid API and clean-PC acceptance were not performed.
Explicit user authorization permits publication; physical media/demo acceptance
remains distinct. See reports/english-publication-checks.json and english-native.json.
