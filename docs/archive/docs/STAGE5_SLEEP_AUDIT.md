# TaskVex — October 23, 2026 general audit and findings of sleep/voice

## Current reopening — 5.R1

User Stopped→Idle reported lag and lack of voice confirmation. new
[review](STAGE5_SLEEP_STABILITY_REVIEW.md) two failed reproductions
confirmed EOS and post-response noise floor deficits. local approval,
Added limited post-terminal capture recovery and wake engine cache.
There is evidence of 920 pytest/7 JS/native and artificial real KWS; physical/provider
There is no acceptance. R1 was accepted before F4, all delays were not closed.

## Status after previous inspection — 5.F3

Common parser for U03 with variants gir/permanent gir/kindness/gap and EN
corrected; The question mark deletion that turns a question into a command has also been removed.
916 pytest/seven JS and type check passed; real microphone/API acceptance is on.
F2 keeps the physical awakening/25 notification and F4 the pronunciation on. Latest and evidence
The native result is in STAGE5_MODEL.md / ../stages.md.

## Previous current status — 5.F2

U04's post-suspended AudioContext vulnerability is limited to the same source
Fixed by cleaning resume/error. 853 pytest/seven JS and type check passed.
Notification for not receiving physical awakening/command is still open; without content for 25 s
Added measurements of delivery/event, the reason for the real sample has not been proven yet.
The final proof and native result is in STAGE5_MODEL.md / ../stages.md.

## Previous current status — 5.F1

The following experiments show the code at check time; is historical evidence. U01,
Fix 5.F1 kod/test has been applied for U02 and U05 and awaits manual acceptance.
850 pytest/7 JS/10 native + additional chat check passed. Detail STAGE5_MODEL.md,
The current status is in ../stages.md. U03 (intent), U04 (vocal vividness) and
The real chain of reasons for waiting 25 s is clear. In old test scripts
"There is a bug" assertions are not current acceptance tests.

TaskVex via audio on single local user's Windows desktop UI/Live
speaks and operates limited tools via registry/policy/TaskManager
It is an application. The expected load is one desktop session, one active model turn, and one
is the microphone source. The review covers the current working tree; mark reference
product repos, backup checkouts, and L1–L4 integrations that have not yet been implemented
code was not counted. Today's action is inspection; The application code has not been changed.

## Result

**Sleep/sound layer is not stable.** The following five runtime findings are source and
confirmed by synthetic experiment. UI/host status separation, speech limit and volume
It is enough to add one more expression to the word list before its source vitality is resolved.
no way Source/tail/tool ownership basis and grade today for data line
no new failures were found in the regressions; This is not a guarantee of error free.

## Things to fix first

### U01 — Old microphone turn continues to receive PCM after finished transcript [P1]

- **What is it:** `input_transcription.finished=true`
  is the end of the transcript; `live_probe.py:157` adds this to the text. Login closure
  The real model door `live_probe.py:204` is waiting for the completion of the door box/tool/turn.
- **Problem / evidence:** Synthetic socket sends complete and finished transcript
  was kept waiting. The actual LiveInput is still `closed=False`; next 100 ms accept PCM
  (`later_pcm_accepted=true`). Friend talking old while thinking of model
  can interfere with the turn; Turning off the separate barge-in does not turn off this old source.
- **Minor ok fix:** Exact login end, reply to user and task
  Separate from the ending. Provider transcript/EOS events with single login owner
  match; Terminate old PCM acceptance without stopping the active agent or response.
- **If we leave it:** Stay-asleep's purpose of isolating background conversation is missing
  remains. This is not the only proven reason for the 25s wait on the real account.

### U02 — UI may appear to sleep while backend rejects sleep request [P1]

- **What is it:** `ui/js/app.js:461` enterSleep before `sleeping=true`, SLEEPING and Wake
  adjusting the button. If `app/bridge/webview_bridge.py:243` reset_live is accepted
  If not, it can reject it without changing the actual sleeping state.
- **Problem / proof:** Reset_live rejection on real host → `ok=false`,
  `backend_sleeping=false`. Same rejection in real UI functions →
  `ui_sleeping=true`, button `Wake`. Rejection also by `app.js:408`
  In this case, it boils down to engine deficiency code; The real reason is lost.
- **Minimum ok fix:** Preparation/waiting status from actual sleep admission
  separate; maintain denial and uncertainty. Local KWS readiness with host sleep acceptance
  have separate results; Old acceptance should not be carried over to the new fashion.
- **If we leave it:** While the user thinks he is sleeping, the two parties are in a different situation
  remains; Next Wake/Stop/re-listening symptoms are misleading.

### U03 — Sleep intention sensitive to narrow list and internal spaces [P1]

- **What is it:** `app/session/sleep_intent.py:10,20,30` performs full text matching.
  The initial address is optional; There is no Vex requirement. But there is no general perception of intent.
- **Problem / proof:** User `Vex sleep mode gir` and `Vex permanently
  go into sleep mode` examples `None`. `go into sleep mode` → before while two
  with space `go to sleep` → None. `enter sleep mode` → once; so English
  There is a list, but it does not provide unlimited expression support.
- **Minimum ok correction:** Surface normalization and intent/host result
  Fix your contract together. Model's understanding of intent transition permission/success
  do not count; Let there be no mismatch in questions, negations, quotes and compound requests.
- **If we leave it:** The model may say “understood”, but the host does not sleep. Just “enter”
  Adding does not solve the next similar variant. This round the parser was not changed.

### U04 — Suspended AudioContext can be mistaken for an active microphone [P1]

- **What is it:** `ui/js/live_mic.js:28–48` initially verifies the audio context, then
  Listening for error track.onended/worklet. AudioContext statechange is not handled.
- **Problem / proof:** Real liveMic module with a synthetic running context
  prepared; The context was suspended. `mic_active=true`, error number is 0 and
  There is no state handler. `listenAutomatically` sees the current active source and creates a new one.
  does not prepare. On/Idle can wait even though the suspended PCM is not flowing.
- **Minor ok fix:** Single source of audio context and track liveliness
  eye on the owner; report safe status without reviving the canceled resource
  and implement limited recovery. Off/unknown/Disconnect should not be skipped.
- **If we let it go:** Resource silence may remain invisible. Each user's Idle
  This is not the exact reason why it crashes; Physical incident registration is still required.

### U05 — Wake-only and task entry are considered the same flow [P2]

- **What is it:** Assuming `pcm_worklet.js:9–12,74–81` is being spoken during wake cycle
  It gives EOS in 700 ms of silence and deactivates the worker. `app.js` wake acceptance
  The following opens the model turn directly with `sendText('', {stream:true})`.
- **Problem/evidence:** Wake → 700 ms silence → a speechEnd; then
  The number of messages did not increase when speech samples were given. Say “Vex” and make short
  The person who pauses can leave his task to the next piece. Wake in persistent mode
  The end of a greeting may put you to sleep as if the task that has not yet been said has been completed.
- **Minimum ok fix:** Wake-up acknowledgment, addressable task start, login
  separate end and end response/task. Do not consider the first word as the task itself; short
  With wake, test the actual request and the subsequent request in the same sentence separately.
- **If we leave it:** Silent pattern waiting or request after short wake
  abduction may occur. Reason for real provider to wait 25 s
  The chain is not complete here; provider/device not tested.

## Fixes in documentation

### D01 — README said security not implemented and incorrect phase order [P2, document corrected]

PolicyEngine is actually bool allow/deny while the README is auto-tainted data and
It was describing the CONFIRM upgrade as if it had been implemented. The code does not have this mechanism;
L1–L4 and external data integrations are not yet available. Like “Zero race conditions”
Fixed unconditional expression and roadmap that only counts Stage 8 as L2/L4.
New source `stages.md`; Stage 7 is GUI/skill, Stage 8 is routine/service/packaging.
This hotfix does not implement a security feature; accurately describes the current limit.

## Test proof and coverage limit

- 843 pytest: PASS (today's repeat, previous report count not copied).
- 7 JS suite: PASS. Wake covers source, transcript, audio and note history.
- Native all 10 processes/scenarios: PASS. Report: `stage5-general-audit-native.json`.
  Opening/re-opening, notes, persist/import/export, export cancellation,
  credential temporary profile, chat, corrupted/schema corrupted/advanced version file included.
- `pyright app`: 0 errors / 0 warnings. This is type checking, not behavior guaranteeing.
- Separate experiments confirmed U01–U05. Passing current tests eliminates these vulnerabilities
  does not turn off; these limit states must be converted into correction tests.
- Machine-readable result: `stage5-general-audit.json`. This file is experiment/test
  includes the results; The setting is not a backup of user data or credentials.

Experiment scripts are in the outputs of this work; They were not added to the application code:

```powershell
cd C:\Users\batue\OneDrive\Desktop\TaskVex\v1
.\.venv\Scripts\python.exe C:\Users\batue\Documents\Codex\2026-10-20\mi\outputs\taskvex-audit-20261023.py
node C:\Users\batue\Documents\Codex\2026-10-20\mi\outputs\taskvex-audit-20261023.mjs
```

## Reviewed and unreviewed scope

Entry point, manifest setup/dependency, native bridge, setting/credential
limit, core setup, registry/policy/TaskManager, note mutation/verification and
model target protection; REST retry/Stop, Live owner/PCM/Stop/resume and UI
sound/sleep/setting paths were examined. Production of UI skills/routines and saving/HTML
connections were also reviewed; Placeholders are not counted as running backends.
Independent security check of every line of every file or entire hardware,
No acceptance of installation and user behavior is claimed.

Physical microphone/pronunciation, real API/GoAway, speaker sound, production
credential/note, actual Notepad opening, packaged installation and reference repo
This round has not been tried. 60 s wake stream refresh, 256 total TaskManager records and
Persistent lack of dedup after restart remained within documented limits;
It is not presented as a new, hidden finding or solved feature of this kind.

Priority: login/sleep protocol and liveness first, then flexible intent and wake
calibration followed by combined physical acceptance. Exact viewing order
It is 5.F1–5.F6 in `stages.md`. General framework or new dependency
not recommended; ownership/ending gates should be fixed in existing code.
