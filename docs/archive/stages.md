# TaskVex — Stages and current steps

This file is the current progress record of the project. Recap historical development notes
It shows you what's running, what's open, and what's next without reading it.
Last updated: October 23, 2026. Current stage: **Stage 5, sleep/voice stability**.
Phase 5 did not close; Phase 6 implementation has not been started.

**Updated 5.R8.6:** Fixed theme and only timer/stopwatch deletion from UI implemented.
994 passed full pytest, 10 JS and targeted Pyright 0. [Native chat](docs/stage5-clock-delete-native-chat.json)
Tested delete/empty record view and regressions with color/real ID. latest keyboard
control was also added to the same report. User physical/visual acceptance and new commit
waits. The previous five manual tests were successful/in commit 00c76ce; No debloat/closing.

**Previous 5.R7.1:** User UI control scope shutdown and multiple timer/stopwatch.
This type of shutdown is connected to the shared appliance/host line; 957 pytest, 8 JS and app/tool/native
Pyright 0. [Full native](docs/stage5-shutdown-native.json) 10/10 passed. 5.R7.2 multi timer/stopwatch next
It is a separate language. User reported that it worked for the previous wake/shutdown slice;
Approved changes are committed.
The user removed the long usage step from the separate plan. **Stage 5 does not close.**

**Previous 5.R5:** user reported successful sleep tests; 5.R4
Moved to commit `5fb30d3` (no push). Note targets to configured selector
moved, added atomic bulk delete. 885 pytest, 7 JS, Pyright 0 and native
10/10 passed; REST/Live batch panel control also verified. User 5.R5
reported success; commit `2120113`. 5.R6 user acceptance is also successful.

Previous 5.R3: removed separate local audio; Vex's own response and
After it rings, sleep is applied (d9caf91). User “go to permanent sleep”
reported statement escaped: TR/EN variants expanded in the same parser.
955 pytest and native chat passed; but “Enter sleep mode permanently”
Again, it did not produce any transition for the user. Variation issue **open**; It cannot be closed by the number of tests.
Common architecture/tool line obligation and private access to AGENTS.md by user decision.
Added ban on natural language command paths. Structured tool of sleep judgment
The move to the line has not yet been implemented; This turn only project rule has been updated. Detail:
[sleep stability review](docs/STAGE5_SLEEP_STABILITY_REVIEW.md).

## How to update?

- When the phase is divided into new steps, the scope/order changes, and at the end of each step
  update this file. Preserve existing identities; Give new ID to new substeps.
- **Basic acceptance complete:** previous scope has been applied and there is an acceptance record. later
  An issue found may reopen that substep; It does not mean that the entire product is error-free.
- **Implemented, awaiting acceptance:** code and automatic proof available; no real user acceptance.
- **Open / Block / Planned:** is not completed. Successful regression is a clear
  It does not shut down reproduction. Record the finding, correction, and acceptance separately.
- Architectural decisions ARCHITECTURE.md, running commands commands.md, detailed model
  The proofs are in docs/STAGE5_MODEL.md. This file does not delete history; current status
  shows. The README roadmap should remain the same as the phase numbers here.
- No commit without user manual acceptance; After acceptance, the AGENTS.md flow is applied.

## General roadmap

| Stage | Scope | Current situation |
|---|---|---|
| 0 | Baseline, data ownership, MIT, and reference/license boundaries | Initial decisions recorded |
| 1 | Model independent core | Basic acceptance is ok; long session capacity limit will be evaluated separately |
| 2 | Native host, UI bridge and settings | Basic acceptance is ok; today's 10 native regression scenarios passed |
| 3 | Backend authoritative note CRUD and transfer/backup | Basic acceptance is ok; has real user acceptance and current regression record |
| 4 | First Windows application plugin | Notepad catalog/status/open acceptance OK; not all apps or models are opening apps.open |
| 5 | Gemini, Live, tools, audio, temporary memory and sleep | **Continues; steps 5.F below on** |
| 6 | Persistent user memory, new L0 operations and external integrations | It was planned; did not start |
| 7 | GUI resolver, L1 recipe, L2 DOM, L3 UIA, L4 vision and skill execution | It was planned; did not start |
| 8 | Routine/scheduler, background services, distribution and packaging | It was planned; did not start |

## Stage 0 — Beginning

- 0.1 UI baseline/reserve and contract decisions saved.
- 0.2 TaskVex original contributions MIT; third parties were kept separate.
- 0.3 Data ownership and explicit denial of unsupported operation defined.
- Source: docs/STAGE0_DECISIONS.md and CORE_START_PLAN.md.

## Stage 1 — Core

- 1.1 Python environment, pyproject and development lock file are ready.
- 1.2 Request/task/tool/result contracts and JSON validation ready.
- 1.3 ToolRegistry registration, parameter validation and name conflict rejection are ready.
- 1.4 Single worker TaskManager, queue, request_id replay protection, status/cancellation ready.
- 1.5 Policy and atomic JSON storage ready with explicit authorization list.
- 1.6 Local notes and read-only system tool verified in core line.
- Limit: TaskManager holds 256 records, including all task records; when capacity is full
  rejects new request. Persistent exactly-once or multi-process after restart
  There is no guarantee of writing. These are not presented with the implicit assumption of unlimited scale.
- Source: docs/STAGE1_CORE.md, docs/TASK_MANAGER.md, docs/POLICY.md, docs/STORAGE.md.

## Stage 2 — Native UI

- 2.1 PyWebView/EdgeChromium real boot, ES modules and ui_ready bridge ready.
- 2.2 Allowed settings snapshot/save/read-back/reboot and controlled recovery ready.
- 2.3 Shutdown/restart, F11, default purple theme and effects startup paths are ready.
- 2.4 Incorrect backend writing of collections such as note/skill/routine with generic save
  The failure to transform and the rejection of the unsupported event were confirmed.
- Source: docs/STAGE2_NATIVE.md; Today's native report is separate experimental evidence.

## Stage 3 — Notes

- 3.1 Approved first transfer, fixed ID and backend single authority ready.
- 3.2 Add/list/edit/commit/delete and verified UI refresh ready.
- 3.3 Backup import/export, error/cancellation/late response and restart ready.
- CRUD from model, target selection by date/partial text added in Phase 5.
- Source: docs/STAGE3_NOTES.md and docs/STAGE3_VISIBLE_ACCEPTANCE.md.

## Stage 4 — First app plugin

- 4.1 apps.catalog, fixed Notepad ID and authorization limit ready.
- 4.2 apps.status and real process/window observation ready.
- 4.3 apps.open and post-open proof ready.
- 4.4 Repeat/cancel/initialization error/uncertainty acceptance ready.
- 4.5 Real Windows Notepad opening acceptance is available in previous reports.
- Source: docs/STAGE4_APPS.md. During today's audit, the real Notepad was not reopened.

## Stage 5 — Applied base slices

| ID | Slice | Status and boundary |
|---|---|---|
| 5.1 | REST → ModelTools → registry/policy/TaskManager | Basic acceptance is ok; REST is not the main desktop product path |
| 5.2 | API key and Windows credential storage | Basic acceptance is ok; production key not read on audit |
| 5.3 | API Live catalog, single Live owner, text and PCM output | Implemented; current entry/sleep findings also on |
| 5.4 | REST/Live Stop, real end and late response protection | Basic acceptance and today's regression passed |
| 5.5 | GoAway and session resumption | There is synthetic/native evidence; real provider GoAway acceptance open |
| 5.6 | Note from model CRUD, date, unique partial target and ID validation | User acceptance available; Coverage that has not yet been opened, such as bulk deletion, is not counted as added |
| 5.7 | Microphone/device/VAD, transcript, barge-in, language/personal instruction | Basic slices work; audio lifecycle reopened |
| 5.8 | Limited RAM chat memory and New Chat | It has been implemented and there is a record of acceptance; is not permanent user memory |
| 5.9 | One-time sleep and local wake | Implemented but **not considered stable due to clear findings** |
| 5.10 | Separation of stay asleep and normal idle timer | There is code/synthetic evidence; normal timer running on user, unified sleep acceptance on |
| 5.11 | 23 October general inspection and reproductions | Completed: docs/STAGE5_SLEEP_AUDIT.md; audit is not correction |

## Stage 5 — Current trimming order

This list is the updated equivalent of the previous fragmented sleep schedules. concrete explanations
[numbered ](docs/STAGE5_SLEEP_AUDIT.md) in the audit report.

| ID | Job to be done | Admission condition | Status |
|---|---|---|---|
| 5.F1 | Make single round audio/input end and UI/host sleep consistent (U01, U02, U05) | After the finished transcript, the new environment PCM does not go to the old round; Backend rejection does not say UI is sleeping; However, wake and duty do not interfere with each other; Stop/unknown maintained | **Implemented; awaiting manual acceptance** |
| 5.F2 | Diagnose Idle microphone liveness and 25s Thinking separately (U04) | After the AudioContext suspend/device/sleep turn, the real source status is understood; safe recovery and legacy resource protection are tested; Prove why with event times for 25 s | **U04 correction/measurements applied; physical awakening and 25 s cause verification on** |
| 5.F3 | Turkish/English connect sleep intention to actual host result (U03) | natural variants such as “go to sleep” and “go to sleep permanently”; no wrong passage in question/negative/quote/additional work; Model approval alone is not considered a success | **Implemented; awaiting physical acceptance** |
| 5.R1 | Voice authentication, EOS/Idle lock and wake setup cost | TR/EN audio after host; End of round on EOS pending provider; post-response candidate perception; Limited recovery without replay after temporary login error | **F4 is placed in front; code applied, physical acceptance on** |
| 5.R2 | Audio turn stuck for 25 seconds while text running | Goes to local end provider as explicit activityEnd; does not interfere with automatic VAD/EOS; three audio turns and sleep/wake are verified on real account | **921 pytest, 7 JS, 10/10 native; user tests reported successful (October 23)** |
| 5.R3 | Wait for Vex's natural response instead of native voice confirmation | No fixed WAV/text path; sleep is not implemented until command response and playback are completed; error/Stop/unknown does not turn into success | **Implemented; 923 pytest, 7 JS, Pyright 0, 10/10 native + [Stop/play control](docs/stage5-natural-sleep-stop-chat.json) passed. The new physical acceptance is clear; user granted commit permission** |
| 5.R4 | Move the sleep decision to the carpool line; check for architectural deviations | Configured tool + registry/policy/TaskManager, response/post-play application; no regex intent path; old call does not produce new transition; other deviations are recorded with evidence | **User tests successful; 5fb30d3 commit received, no push** |
| 5.R5 | Move note selection to configured tool and add bulk delete | Single/multiple real target, fresh selection, reject on data change, single atomic write/readback; no action to uncertain target; REST/Live same line | **Implemented; 885 pytest + last 62 selection/batch checks, 7 JS, Pyright 0, [native 10/10](docs/stage5-note-selection-batch-native.json). User acceptance successful; commit `2120113`** |
| 5.R6 | Bulk complete selected notes | The last N changes to all or just done in the content group; fresh selection, full ID set, snapshot, single text and readback; REST/Live trunk | **Implemented; 929 pytest, 7 JS, Pyright 0 in app/not line; [native 10/10](docs/stage5-note-completion-native.json). User tests were completely successful; Commit confirmation received. 6 type errors of old policy tests are registered in STAGE5_MODEL.md** |
| 5.F4 | Wake pronunciation and wrong wake up | Vex/Veks/Rex in one local definition; KWS and Live use the same family; the proper name is preserved; X/ex/eks does not add alone | **Implemented; 947 pytest, 7 JS, app/wake Pyright 0; [native chat](docs/stage5-wake-variants-native-chat.json) and 15/15 real KWS/artificial voice. The user reported that it worked; In commit `20c755c`** |
| 5.F5 | Combined long-term use and physical acceptance | The user reported that he had already done this check; separate application/testing step not desired | **Removed from separate plan by user request; general regression requirement continues** |
| 5.R7 | Link existing UI app controls to Vex tools | Determine the scope/owner/permissions of desired buttons such as shutdown; configured tool and current host are used, successful request acceptance is separated | **5.R7.1 / 20c755c and 5.R7.2 / af834ff user acceptance successful. 5.R8 tweaks then debloat; Stage 5 on** |
| 5.R7.1 | Closing the application via Vex | The registered tool only accepts requests; Shutdown host path available after successful response/ring; Stop/old turn/unknown does not close; Windows won't shut down | **Implemented; 957 pytest, 8 JS, app/tool/native Pyright 0, native 10/10. The user reported that it worked; In commit `20c755c`** |
| 5.R7.2 | Multiple timer and stopwatch | Create/list/start/stop/resume/reset with actual record IDs; UI/model single state owner; different meters do not crush each other | **Implemented; 980 full pytest + last 40 counters/profiles, 9 JS, app/targeted Pyright 0 and [native 10/10](docs/stage5-clocks-native.json). User manual acceptance successful; In commit af834ff** |
| 5.R8.1 | Timer/stopwatch selector view and sound | Available theme variants, keyboard access, single SFX in selection; poll/model focus produces no sound, real ID is preserved | With user continuation approval, in commit 6918038; 9 JS + native CSS proof preserved |
| 5.R8.2 | Vex's personalized voice notification when the timer ends | Current Live response and voice owner instead of fixed boss/local say; busy, Sleep, Mic Off, Stop/Disconnect, repeat and overdue event limits are set; second TTS/no session | Implemented: fixed boss removed; verified ending, empty instrument catalog and same Live/Stop/audio line. 988 pytest, 10 JS and native 10/10; user acceptance successful/00c76ce |
| 5.R8.3 | Key/model restoration and automatic Live catalog | Existing Windows credentials and conn.model are preserved; Registration and reopening are audited. Manual Load is removed; native ready/single catalog request, stale response and error protection on key exchange | Implemented: automatic single load on startup/key save, conn.model restore; Windows credential cross-process native acceptance passed. User acceptance successful/00c76ce |
| 5.R8.4 | Audio filter, microphone level and wake sensitivity | End-to-end effect of the filter and actual level in the single microphone owner available; Mic Off/local sleep limit is maintained. Wake slider connects to KWS threshold from saved setting; sensitivity increase/false awakening limit is measured | Implemented: same worklet threshold/meter, Off reset; wake The threshold recorded in the next sleep. Switched to synthetic/native; user tests pass/00c76ce |
| 5.R8.5 | Minor tweak UI cleanup | Removal of google link emoji, idle sleep plus/minus controls compatibility with existing theme/SFX and 0–300 validation | Implemented: emoji removed; themed/voiced +/- uses the same 0–300 validation; native limit test passed. User acceptance successful/00c76ce |
| 5.R8.6 | Fixed theme and UI counter deletion | The latches/input arrow are not affected by the reactor state; The real ID selected by right-clicking on the list is deleted on the same core line and is not opened to the model; no fake deletion in error | Implemented; 994 pytest, 10 JS, targeted Pyright 0 and native chat. User waits for physical right click/visual accept/commit |
| 5.F6 | Closing care and documentation | UI cleanup/debloat moderate; old plans do not seem current; Decision for 256 mission limit and restart replay limit; README scope correct | It started; did not close |

5.R3 variant tracking: “as” requirement for “permanent sleep”
removed; toggle TR/EN equivalents added. 955 pytest and
[native chat](docs/stage5-sleep-phrases-native-chat.json) passed. in Native
the reported Turkish opening and English closing went through the actual UI/host;
provider/microphone synthetic, physical acceptance and commit of this additional fix are on.

No new integrations are added until 5.F1–5.F4 is completed. Around the faulty contract
Adding one more if/word is not a permanent solution. Every fix fixes the old mistake.
There must be targeted testing that shows failure.

### 5.F1 application proof

- 850 pytest, 7 JS suites, app/targeted type checking 0 errors/warnings.
- 10 native scenarios: docs/stage5-f1-native.json; additional host rejection/delayed acceptance:
  docs/stage5-f1-native-chat.json. Actual provider/microphone not tested.
- U01: new PCM is rejected after finished transcript; model response/tool
  unstoppable. U02: preparation/rejection/unknown/real sleep are separate. U05: local
  pause stream does not beat; definitive wake-only does not count as actual mission completion.
- 5.F2 (vitality/25 s), 5.F3 (intention) and 5.F4 (pronunciation) remained open.
- Approved audit documents were moved to commit 06d8e8f; new runtime code
  awaiting manual acceptance. Historical control experiments show the old error;
  Current acceptance tests are the tests of this correction period.

### 5.F2 — sound engine liveness and standby diagnostics

- When the user woke up after F1, he reported that there were still no commands received; full manual
  Acceptance/commit was not counted. F2 was applied upon the user's request to continue.
- Subsequently suspended/interrupted AudioContext resume once in the same source
  is done. Fixed bug and resource cleaning if not fixed within 1 s; endless again
  There is no permission/device unlocking. Mic On preference does not change; on Off/On prepares again.
- The old resume/device callback cannot turn off the new microphone. local recovery
  does not call for new model/tool or resend old PCM.
- 25 s duration was not reduced. Number of PCMs whose turn report was actually sent to the SDK,
  initial audio/EOS carries the received event and exact transcript times; timeout
  numbers/stage appear in the status line. Synthetics were divided into three separate holds.
- 853 pytest, 7 JS suites, app/targeted Pyright 0 errors/warnings. Native evidence:
  docs/stage5-f2-native.json (10/10, including new context recovery).
  First native attempt with wrong cwd was unsuccessful; again in the correct v1 directory
  passed, detail in STAGE5_MODEL.md. No real account/microphone used.
- **Open:** all causes of physical awakening problem and real 25 s example
  The cause chain has not yet been proven. Test success does not dismiss this notification.
  F3/F4 was not applied at the time of this F2 recording; The current F3 record is below.

### 5.F3 — Turkish/English sleep intention

- The common sleep_mode parser is used in text and precise audio transcription.
  “go to sleep”, “go to sleep permanently”, courtesy/space/big
  The letter and its English variants preserve the once/persistent/off distinction.
- Saying names is not necessary while awake. Permanently back here throughout the chat
  is sleeping; No preferences or operating system hibernation were added to the disk.
- Complete sentences are matched; The question mark is no longer deleted. quote, negative,
  A sentence containing explanation and additional work does not translate into sleep control. Fragmented transcript
  If there is any question/negative/additional work later, the held model output is returned.
- No new model agent/intent model; current host accept/reject/unknown and odd
  Live/core/resource ownership has not changed. Failed tests of U03 first
  verified (24 failed / 24 successful), then fixed.
- 916 pytest and 7 JS suites passed; app/targeted Pyright 0 errors/warnings.
  Native passed 10/10; report: docs/stage5-f3-native.json. With new expressions
  Host-approved one-time/permanent mode check passed. Physical voice/API acceptance is on.
- The user has given permission to continue alone; did not report the manual test result.
  The physical awakening/25 s gap of F1/F2 was not closed; There is no runtime commit.
  F4 pronunciation/miswake is the next planned step.

### 5.R1 — delay / voice confirmation / Stopped review

- Report: docs/STAGE5_SLEEP_STABILITY_REVIEW.md. EOS pending transport and response
  Post-noise threshold issues were first produced by failed testing, then fixed.
- 700 ms local silence generates EOS after the backend is ready; final
  In the entry that closes with the transcript, the missing EOS is clearly sent. Old PCM/tool
  no replays; Stop/unknown and 15 s upper limit are maintained.
- TR/EN text + fixed local WAV after host confirmation; Mute/Stop/custom output and
  late fetch is preserved. Windows sound different from Gemini; No API/TTS requests.
- Single wake engine RAM cache, new decoder/ID/empty buffer every sleep; real
  Three restarts of KWS with the same artificial WAV were successful. docs/stage5-sleep-stability-real-kws.json.
- Wake→Live source error goes to normal error/Stop line. After the definitive ending
  up to two new empty listeners on temporary login error; permission/unknown impenetrable.
- 920 pytest, 7 JS suites, Pyright 0 errors/warnings. Native 10/10:
  docs/stage5-sleep-stability-native.json. Additional for latest hybrid/cache version
  chat passed: docs/stage5-sleep-stability-final-chat.json.
- The first additional chat failed the short Thinking moment test;
  Fixed with test server barrier. Failed evidence was not deleted:
  docs/stage5-sleep-stability-chat-timing-failure.json.
- No real user voice/note, API key or paid API used.
  Physical and provider acceptance is open; Not all 25 s examples are considered solved.
  User acceptance of this combined path is required before proceeding to F4; There is no commit.

### Evidence today — October 23

- 843 pytests passed; 7 JavaScript suites passed; Pyright 0 errors/warnings throughout the app.
- Native 10/10 scenario passed: docs/stage5-general-audit-native.json.
- However, 5 independent runtime vulnerabilities were confirmed in synthetic experiments. These experiments
  proves the existence of the old error; It is not an acceptance test pass.
- Experiment scripts and detailed results in docs/STAGE5_SLEEP_AUDIT.md.
- No paid/real API, physical microphone and user notes used.
- This turn application code has not been changed; Documents/AGENTS rule updated.
  Previous pending codes were not committed because the user reported a bug.

## Phase 6 — Persistent memory and new L0 integrations

It's all planned; It will be narrowed down again as the sub-steps are implemented.

- 6.1 Seeing/correcting/forgetting user-removed information and open memory
  preference under Personalization. The current pMem space is not working memory.
- 6.2 Linking telemetry, application and media operations to the individual model. Timer/stopwatch was addressed in 5.R7.2.
- 6.3 File reading; then controlled modification and verification.
- 6.4 Weather state/location permission and web search.
- 6.5 Google Drive, Calendar and mail: OAuth, scope, renewal and acceptance in one transaction.
- 6.6 Telegram receive/send and Discord bot: user/channel/target authority,
  proof of delivery and non-repetition in uncertain shipping.
- 6.7 Decide on permanent call recording and restart dedup before external side effects.

## Stage 7 — GUI resolver and skill execution

- 7.1 L3 UIA targeting and re-authentication in one application.
- 7.2 Reusing verified stream with L1 recipe/memory.
- 7.3 Browser L2 DOM; L4 vision/OCR and budget when necessary.
- 7.4 Skill Executing JSON steps from the same registry/policy/TaskManager line.
- 7.5 DPI/window switching, legacy target, permission denial and unspecified side effect acceptance.

## Stage 8 — Routines, services and distribution

- 8.1 has a single backend scheduler; clear transfer of ownership from existing UI timer.
- 8.2 Routine CRUD, trigger ID, double execution and notification/result separation.
- 8.3 Background services opened by the user; log masking/rotation.
- 8.4 Data schema migration, crash recovery, normal shutdown and update.
- 8.5 Bundled native install, model/third party licenses and clean distribution.
