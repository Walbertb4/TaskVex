# Changelog

This file is the only current record of TaskVex changes. Architectural decisions are available
The state is in ARCHITECTURE.md, the work to be done is in PLAN.md. The version has not been released yet.

## Unreleased

### Publish camera and permissions status

- Updated README with current camera/permission behavior, actual validation and
  unresolved full-native startup/teardown failures. Replaced stale media acceptance
  and older test totals; historical evidence remains linked rather than implied current.
- Explicit user request authorizes committing/pushing the pending implementation.
  Camera/OS/provider manual acceptance and native stability remain open; the demo
  EXE was not rebuilt and no additional feature stage was started.


### Central permission settings — 6.8.1a

- Added Camera/Microphone/Location requests and honest browser status under
  Settings > System, independent of Live/model readiness or device selection.
- Requests briefly probe default media then release it, or discard a location;
  no feature toggle, sharing, provider call or saved weather preference is changed.
- Added timeout/late-grant cleanup and active-device checks; pending microphone
  setup alone is not treated as granted access. No automatic startup prompts.
- Added allowlisted Windows privacy-page navigation with explicit failure handling;
  it cannot grant permission or open arbitrary caller URLs.
- Validation: 1,269 pytest, 9 JS suites, 25 browser groups, 2 targeted native
  phases and Pyright 0. Full native regression did not finish cleanly: a UI startup
  timeout and a Python.NET teardown failure remain open. Camera/OS manual acceptance
  is separate; see reports/permissions-checks.json and permissions-native.json.


### Camera input on the existing Live session — 6.8.1

- Added explicit camera On/Off and browser camera device selection with video-only
  permission, timeout/late-permission cleanup and no automatic startup capture.
- Added bounded request-scoped JPEG input on the existing Live socket, including
  the speech activity boundary, one-frame-per-second sending, latest-only RAM,
  stale/replay rejection and Stop cleanup. No new package or execution authority.
- Camera Off preserves microphone and reply; sleep/disconnect/scope changes and
  uncertain outcomes release capture. Visual instructions are untrusted observations.
- Source UI cleanup was accepted and committed as 6e18e99 before this step.
- Validation: 1,265 pytest, 9 JS suites, 23 browser groups, 10 native phases and
  Pyright 0 errors/warnings. Evidence: reports/camera-checks.json and camera-native.json;
  real camera/provider acceptance remains pending. No paid API or real camera used.


### Simplify weather, media and memory presentation

- Moved visible weather/place source credits to README; retained location consent and weather freshness status.
- Media controls show only the volume slider underneath; its accessible name and off-screen value remain.
- Reduced personal memory help to one sentence. Domain and backend behavior are unchanged.
- Validation: all 21 existing browser groups passed; git diff checks passed. Backend/native suites were not rerun for this presentation-only change.


### Narrow stage 6 and connect weather — 6.4

- Restricted remaining stage 6 to weather/location, then camera, screen sharing,
  scoped additional audio inputs and closure checks. Moved file/context work to
  7.0, web search to 7.3, external-service safeguards to 9.1, Google to 9.2 and
  Telegram/Discord to 9.3. Existing stage 7/8 IDs and mandatory safeguards remain.
- Added one Weather service owner shared by UI and weather.locations/current
  model tools through the existing registry/policy/TaskManager. No new dependency.
- Added explicit manual place selection, opt-in approximate browser location,
  persistent native preferences and Clear. Geolocation never runs at startup;
  generic preference save/import cannot grant location sharing.
- Added validated public Open-Meteo reads, bounded cache/backoff, visible source
  time/stale state and attribution. Provider failure does not fabricate weather
  or change independent local telemetry. Paid Gemini requests were not used.
- User reported successful weather tests; specific OS/provider coverage was not separately enumerated. Camera, screen,
  system-audio capture, web search and external accounts were not implemented.
### Player application volume and quiet media controls — 6.2.5c

- Replaced visible playback-operation text with an accessible off-screen status;
  failures remain observable in logs/tooltips. Added a theme-bound PLAYER VOLUME range.
- Added media.control set_volume through the same registry/policy/TaskManager for
  UI and REST/Live. Only the unambiguously matched player application is changed;
  browser-wide scope is explicit. Windows master, Vex reply/effects and mute are unchanged.
- Added Core Audio session/process matching, private audio-target identity and real
  volume readback. Stop, replay and persistent unknown protections remain active.
- No dependency added. Prior accepted media work committed as c8d159d; this step
  was accepted after the user reported successful tests. Validation: reports/media-volume-checks.json.
### Fix false media target changes

- Reused the issuing Windows GSMTC manager across polling and controls. Separate
  manager activations can expose unequal wrappers for an unchanged player; those
  cross-manager comparisons incorrectly rejected every dashboard command.
- Preserved genuine session/metadata/capability checks, cancellation and replay
  protection. Source failure discards the private manager and old target before
  reacquisition; an empty session does not force manager recreation.
- Added manager-local identity and cross-thread regression cases. Real read-only
  probes reproduced the original rejection and verified stable targets after the
  fix without controlling user playback. Manual playback retest remains pending.

### Current Windows media controls — 6.2.5b

- Added play/pause/next/previous through the existing shared Media owner and
  registry/policy/TaskManager. Dashboard buttons and REST/Live use the same tool.
- Added separate control permission, fresh observed target IDs, native pre-dispatch
  checks and observable state/track verification. Acceptance alone is not success.
- Preserved Stop/replay rules and the persistent unknown lock; stale, unsupported,
  busy and uncertain controls remain disabled. Late UI replies cannot unlock them.
- Updated command/ownership/bridge documentation. Automated validation is recorded
  in reports/media-control-checks.json; actual player/provider acceptance is pending.
  No new dependencies, later integration, commit or push are included in this slice.

### English repository language and publication preparation

- Converted current guides, archived prose, code comments/docstrings and local
  tool descriptions to English. Functional Unicode normalization and selected
  conversation languages remain supported; this is not an English-only assistant.
- Renamed the historical documentation directory to docs/archive and the archived stage guide to stages.md.
  Updated links and archive hashes; pre-translation hashes and the source Git
  revision remain in the manifest. Translated reports are historical translations,
  not fresh acceptance evidence. The English-only maintenance rule is in AGENTS.md.
- Corrected obsolete README claims about vendor-neutral GPU/network monitoring;
  documented the portable demo and the separate media-read/control acceptance.
- Publication checks and any failures are recorded in
  [the migration report](reports/english-publication-checks.json).

### Portable Windows demo package

- Windows x64 ZIP and reproducible build with Python with PyInstaller
  Added lock/script. Existing host/core is retained; frozen restart starts EXE.
- Demo profile is separate under TaskVexDemo by default; developer key,
  notes and UI tests are not distributed. Third-party license notices are added.
- Wake weights are not distributed; optional setup available verified downloader
  calls. WebView2/.NET target prerequisites are specified in the README.
- Packaged EXE and ZIP temporary profile extracted to different Turkish/gap directory
  opened: [evidence](reports/demo-build-checks.json). Clean PC/real No API acceptance;
  Unsigned demo is not production version. Commit/push not made.

### Windows media session reading — 6.2.5a

- Same Media owner UI connected to query_media and model media.status line.
  OS current session title/artist/state is displayed; No playback control added.
- Incomplete session, unsupported/timeout/source loss and transition are separated; stale title
  and the playing animation is cleared. Native UI/model reads the same cache.
- Added four WinRT 3.2.1 namespace/runtime packages to pyproject and lock;
  The COM lifecycle is stable, there are no new threads/players/timers.
- Previous network quality is in commit 9c607bb. New slice automatic/native control
  completed; Waits for user acceptance. Control buttons are separated into 6.2.5b.
- 1172 pytests, 138 targeted tests, 16 browser groups, 9 JS suites, 10 native stages
  and Pyright 0: [evidence](reports/media-read-checks.json). Old tool catalog
  The first Python/native failed rounds resulting from expectations were preserved in the report.


### Gateway ping and location-free Wi-Fi quality — 6.2.3b

- Local IPv4 gateway RTT and Wi-Fi quality percentage with the same Telemetry/Network
  provides; The UI specifies the target as Gateway ping, there is a tooltip age/status.
- Single ICMP request 250 ms, normal quality cache 10 s; In replacement rota/kart
  old success is abandoned. True zero, timeout and incomplete query are different.
- WLAN realtime opcode 19 location permission does not require; sensitive current_connection/BSS
  There is no fallback. If the source is not supported, the measurement remains.
- Previous local traffic slice is in commit 3e3cb8c by user acceptance. new
  Waits for user acceptance and commit/push for the slice.
- 1154 pytests, 53 targeted tests, 15 browser groups, 9 JS suites, 10 native stages
  and Pyright 0: [evidence](reports/network-quality-checks.json). Single Windows
  actual gateway/Wi-Fi queries passed on his machine; old OS/hardware untested.


### Local network traffic and physical link — 6.2.3a

- Passive Windows IP Helper to existing Telemetry/system.status/query_system line
  meters are connected. UI Receive/Send shows Mbps and local/Wi-Fi shows commitment status.
- First example, counter reset, device cluster change and resource error do not match speed;
  true zero, unknown state and disconnected state are separated.
- Virtual/VPN counters do not count as double; The name SSID/IP/MAC/profile is not given out.
  Active ping/speed testing, no Wi-Fi signal percentage or connection settings added.
- GPU slice is in commit 43c7f28 by user acceptance. This new slice is automatically
  checks completed; manual waits acceptance/commit/push.
- 1132 pytests, 31 targeted tests, 14 browser groups, 9 JS suites, 10 native stages
  and Pyright 0: [evidence](reports/network-local-checks.json). Real Windows
  read-only meter reading passed on it; Physical cutting and binding was not attempted.


### Windows GPU counters and system view fix

- Removed unreleased NVIDIA tool/adapter; manufacturer-independent Windows
  PDH GPU Engine counters are used in the common Telemetry/system.status/UI line.
- The same motor processes are collected; determines the densest motor/kart single bar. First
  instance, zero, counter loss, CPU/RAM independence, and handle closure are preserved.
- Removed system description at the top; fixed GPU tag is not split in narrow space.
  The 0/25/100 width of the bar is verified in the 1280/1920 view.
- Temperature and VRAM capacity are not measured because they do not come from this source.
- Previous vendor attempt was rejected by the user; historical reports
  It is not evidence of new practice. New step manual waits acceptance/commit.
- 1120 pytests, 19 targeted tests, 13 browser groups, 9 JS suites, 10 native stages
  and Pyright 0: [evidence](reports/windows-gpu-checks.json). only on windows
  read common meter check also passed; different physical generators were not tried.

### Common local telemetry — CPU/RAM/disk/battery/active application

- Single Telemetry instance provides real Win32 measurements for model and UI.
  UI reads snapshot from current tick; poll does not enlarge the task log.
- First CPU self-instance/bad counter/lost measurement —; true zero is preserved.
  The active application is shown only by its exe name; The user document title is not read.
- Local metrics and session token total are not deleted when disconnected.
  There is no new dependency/service/thread. GPU/temperature/network/media are the next slices.
- User accepted the token test and postponed the commit; There is no commit/push this round.
- 1109 pytest, 96 targeted tests, 12 browser, 9 JS and Pyright 0. First native
  After the chat timeout, the isolate passed again 10/10; [evidence](reports/local-telemetry-checks.json).

### Gemini session token total

- Python token parsing/collection has been unified in existing gemini.py.
  UI now shows total in app lifetime instead of last response.
- REST tool turns, Live productions and individual TTS responses are counted;
  Search Live snapshots are not collected randomly. Stop and Disconnect preserve the total.
- Underutilization is not considered absolute zero; known total ≥/Incomplete is displayed.
  There is no new API call/repository/dependency; restart resets the counter.
- The actual API/billing has not been verified; User acceptance of this slice is awaited.
- 1101 pytest, 138 targeted test, 11 browser, 9 JS, 10 native and Pyright 0;
  [evidence](reports/session-token-checks.json).

- GitHub README current memory confirmation/automatic record, last token notification and
  Corrected based on validation of 1091 tests. Telemetry/air/network shortcomings and
  Explicitly stated that there could be data proposal/source remaining in the mission log.

### Latest provider token indicator

- Live/REST actual usage metadata linked to existing chat report and UI.
  Incomplete information does not preserve the old value; zero is valid. Limit/quota is not made up.
- Separate API call/repository/dependency not added. It is the last notification shown;
  session total is not account quota or the sum of all tool/audio requests.
- The user requested a direct commit for this small step; No actual API adoption.
- 1091 pytest, 96 targeted test, 9 JS, 10 browser, 10 native and Pyright 0;
  [evidence](reports/token-counter-checks.json).

- User reported successful decision of memory recommendation button/speech;
  app is in commit 6f52b4c, no push. Current acceptance status in the PLAN and
  With telemetry/network/token/media, the order of the remaining UI links was clarified.
  No new app features were added in this round of planning.

### You can decide on the memory suggestion by chatting or by talking.

- Save/Dismiss from personalization to the right of the four controls below the chat,
  moved to separate, theme-related group; Removed automatic modal/Review search button.
- Vex requests permission in the current normal voice/text response. Next open user
  The decision goes to the same memory.decide tool; UI/model is not two separate recording paths.
- The model cannot approve the candidate it created in the same round. Fresh for next round
  pending ID required; The old ID and late decision will not be applied to the new candidate.
- The real backend profile is renewed after the decision; There is no second save.
  In the previous 6.1.3 user acceptance commit c5d086c, no push was made.
- 1081 pytest, 40 targeted memory tests, 9 JS, 9 browser, 10 native and 0 Pyright;
  [evidence](reports/memory-voice-review-checks.json). The real API/microphone has not been tested;
  User acceptance and commit of this change is expected.


### ask/auto-save preference for memory and direct review

- Ask before saving learned information checkbox was added to Personalization;
  true in old record. It is stored in the same profile as learning and memory preferences.
- If confirmation is required, the window opens automatically; There is a review button
  It is not dependent. It does not close the already open panel with toggle.
- If checkbox is false, memory.propose via append/readback of the same domain owner
  saves directly; The UI is refreshed from the backend. The model cannot change this preference.
- memory.write permission, fresh snapshot, replay/Stop and ambiguity rules
  is protected. The new field is included in the snapshot ID.
- 1074 pytest, 9 JS, 9 browser, 10 native and Pyright 0; [proof](reports/memory-review-checks.json),
  [native](reports/memory-review-native.json). Live API/inference accuracy not tested;
  User acceptance and commit is expected.


### Memory suggestion resource denial fix

- User reported memory.propose failure in manual testing. From the diary
  source_unavailable verified; 6.1.3 reopened is not considered accepted.
- The source sentence was reprinted into the model and the one-to-one matching was removed.
  ModelTools real user connects text/ASR itself; quote variation
  It does not downgrade the current recommendation. The recommendation is still not the profile truth before approval.
- Engine log shows safe error code in case of tool failure; private data
  not logged. Unsourced audio processing, snapshot, replay and confirmation protections remain.
- 1068 pytests, 33 targeted memory/suggestion tests, 8 browser groups, 10 native stages,
  Pyright 0 and live-status JS passed. [Proof](reports/memory-source-checks.json),
  [native](reports/memory-source-native.json). It has not been tested by actual calculation;
  User retest and commit are expected.


### Speech memory suggestions and user confirmation (6.1.3)

- Personalization pLearn preference is off by default; Same with pMemory
  memory.propose suggestions are taken from the speech model. Source: This turn is real.
  Binds to transcript text/Live; The model cannot produce proof of host.
- The recommendation is not written to the profile memory; May include daily candidate text. single RAM
  candidate and Save/Dismiss UI resolution are the same core
  is on the line. When learning is on, the model cannot add new information without approval via append.
- Append single profile/same append-readback; old suggestion/permission/snapshot/restart rejection,
  UI update without generating unknown lock and second save. The draft is preserved.
- 6.1.2 accepted by user, in commit 50421c3; no push.
- 1065 pytests, 15 targeted recommendation tests, 9 JS suites, 8 browser groups, 10/10 native
  stage and Pyright 0; [proof](reports/memory-suggestions-checks.json),
  [native](reports/memory-suggestions-native.json). Real/paid API and model
  semantic inference accuracy was not tested; user is expecting acceptance/commit.


### Explicit model memory operations (6.1.2)

- memory.read/patch to line registry/policy/TaskManager available in REST and Live
  added; for open request save/fix/forget, only with active pMemory.
- Fresh turn/snapshot and single target validation; readback, replay/cancellation/unknown
  rules. The same profile file is used, no new memory DB.
- Native core/bridge shares the same JsonStore lock. Common setting scheme
  Moved from bridge/settings.py to storage/settings.py; All callers are up to date.
- UI refreshes memory from backend; old form overwrite and late registration ack
  is protected. There is no automatic merge/retry in the conflict; If necessary, the application will be reopened.
- 6.1.1 accepted by user, in commit e7f3ce4; no push.
- 1050 pytest, 9 JS suite, 7 browser groups, 10/10 native stage and Pyright 0.
  [Evidence and unsuccessful interim trials](reports/model-memory-checks.json),
  [native](reports/model-memory-native.json). The open form outline is preserved;
  There is no real account/paid API. User agreed; In commit 50421c3.


### Manual user storage and New Chat removal (6.1.1)

- Removed New Chat button and unused UI handler/control references.
  Internal reset API is preserved; temporary memory persists in Stop/Disconnect.
- Personalization pMem editor and open pMemory preference to existing profile storage
  connected. Old text will not be sent without approval. Common instruction opt-in information
  receives only data; model inference is not automatically saved.
- When the active personal memory changes, the old Live/RAM context is dropped in the next round;
  In case of indefinite closure, a new round does not start. Active reply/history/backups is not deleted.
- Voice selection step was moved to 2cebea8 commit with continuation approval; no push.
- 6.1.2 model mutation tools and 6.1.3 inference suggestions are separate slices;
  not added this round. New dependency/data no authority.
- 1035 pytest, 9 JS suite, 6 browser groups, Pyright 0 and 10/10 native stage
  passed. Checkbox restore error fixed; two more native old assumptions
  Updated with precise control. Unsuccessful intermediate rounds [in report](reports/personal-memory-checks.json),
  latest native acceptance [here](reports/personal-memory-native.json). Real account/
  no paid API and no physical audio; user agreed, in commit e7f3ce4.


### Live sound selection and key status statement (5.F8.2)

- 30 preset Live sounds documented under Connection are listed with the [LIVE] tag.
  Single conn.voice preference from permanent settings to the same Live setup speech_config
  movable; text/microphone/timer response is common. Voice change old resume token
  does not use, does not interrupt the active turn. REST TTS has not changed; special/TTS-only no sound added.
- API key input registered/missing/uncertain shows the status in the placeholder; real
  It does not show key or end characters. Key existence is not API access confirmation.
- verified gemini-live-api-dev skill and Google Live provider agreement.
  The sound list is sourced from the document; pattern discovery remains from the API. No new dependencies.
- Previous volume step saved in commit 9d67a1d by user acceptance;
  no push. User confirmed continuation/commit; did not report separate physical voice testing.
- 1025 general pytest + 24 final targeted tests, 9 JS suites, 5 browser groups,
  app Pyright passed 0 and 10/10 native stage. [Abstract](reports/live-voices-checks.json),
  [native](reports/live-voices-native.json). Domain name assumption of SDK testing and
  fixed a type ambiguity; Failed attempts are preserved in the report.
  The actual account/paid API and physical sound have not been tested.


### Vex response volume (5.F8.1)

- Theme and keyboard compatible Vex reply volume bar has been added under Settings Audio.
  Instantly changes the gain of a single PCM player; In notification Live/REST/timer
  is common. Mute on/off preserves the selected level; SFX and microphone are unchanged.
- replyVolume is validated between 0–1; default/reset 1, zero is maintained.
  It registers to native and native preference via the same save/snapshot/import-export.
  No new provider call/player added. Voice/personalization 5.F8.2 is waiting.
- Previous step log/capacity moved to commit 5c21156 with user continuation approval
  recorded; No push was made. The user confirmed that this slice is working; commit approved.
- 1024 pytest, 9 JS suite, 5 browser groups, app Pyright 0 and 10/10 native
  The phase has passed. [Abstract](reports/reply-volume-checks.json),
  [native evidence](reports/reply-volume-native.json). Real account/paid API and
  No physical speaker testing was done.


### Persistent task log and capacity (5.F7.2/3)

- Same TaskManager uses standard library SQLite logging; acceptance handler
  Pre- and terminal records are written with a FULL transaction. Second core OS
  is rejected by its lock; new path dependency/executor/model was not added.
- Restart does not rerun the completed job. Queued canceled, half job started
  becomes unknown. Conflict Identity/content is rejected; disk failure new effects
  stops. The verified tool result will not be considered withdrawn due to a late registration error.
- Removed 256 total life limit in native core; RAM registers and active jobs
  is limited. Old get/wait/cancel/replay even though Terminal RAM copies are removed
  gives the same ID/result from disk. The logless test manager maintains the old safe boundary.
- The diary contains plain local data, can keep old note text, not automatically deleted.
  Unknown mediation screen and external service exactly-once guarantee have not been added.
- Old startup tests now only wait for the tasks directory to be created; new
  observation uses new request_id on restart. Old assumption in first round of testing
  Fixed errors and test connection ResourceWarning. In the first general round
  the single Live/asyncio caution was focused and did not recur in the final round; The filter is not loosened.
- Passed 1017 pytest, 17 targeted daily tests, Pyright 0 and 10/10 native stage.
  Details [test proof](reports/task-journal-checks.json) and
  [in native report](reports/task-journal-native.json). No real account/paid API;
  user confirmed continuation/commit; No separate physical tests were reported.


### README and logout

- GitHub README, implemented features/planned scope/data flow/explicit limits and
  English rewritten to separate test evidence. Unmeasured speed/RAM,
  no claims of unlimited autonomy or production-ready security.
- With the acceptance conditions of 5.F7.2 permanent daily and 5.F7.3 secure capacity/retention jobs
  Saved in PLAN.md. Sound preferences and individual response level are waiting at 5.F8.
- User approved continue, commit and GitHub push for 5.F7.1; This is a separate
  It does not mean that the physical test result is reported.


### Single-instance security (5.F7.1)

- For the same data root, the OS file lock is obtained without unlocking worker/window; second
  native instance is rejected with an explicit error. No other data profiles are blocked.
- Closing/exception/crash releases lock; restart the new process only after it is released
  then it starts. PID/stale file deletion, no new dependency or second state owner.
- Main documents that the user moved under docs were preserved; active links and AGENTS
  adapted to new document locations. The historical archive has not been modified.
- Passed 1000 pytest, targeted Pyright 0 and 10/10 synthetic native phases;
  Including real sub process/crash and native login/restart tests.
  Result: reports/instance-checks.json. No real account/paid API was used.
- 256 saves and permanent replay log remain unchanged in this period. 5.F7.2/3 is on.


### Maintenance and documentation order

- 133 legacy document/evidence files with unique relative paths and SHA256 manifest
  Moved below docs/old. Archive is not the current directive.
- Archive bytes are protected from Git end-of-line conversion with .gitattributes;
  The manifest is also valid when checked out in another system.
- ARCHITECTURE.md and PLAN.md rewritten; running commands and bridge contract
  deduplicated in docs. Removed conflicting progress logs in READMEs.
- AGENTS.md enforces new document ownership and maintenance of this record with each change.
- Removed unused path MediaRecorder/decode and the test that tested it alone;
  the actual AudioWorklet stream and its regressions were preserved.
- UI routine/calendar browsers without backend player and skill/routine are fake
  Startup notifications have been removed. Local descriptions and old profile texts were retained;
  non-linked controls are planned to be excluded from the circuit.
- Conversation/microphone/sleep lifecycle to assistant_session.js, visual shell to shell.js,
  The devices were separated into devices.js and the layout into layout.js. preferences.js single preference
  is the object; No new frameworks, dependencies or secondary state owners were added.
- Native acceptance scenarios moved from runner to native_scenarios.py.
- REST/Live tool catalogs have been moved to common constants; old policy test type
  The warnings were fixed by clearly stating the test's intentional invalid inputs.
- Audit findings, customization gaps and actual test coverage are in docs/AUDIT.md.

Verification: 996 pytests, 9 JS suites, 4 browser groups, 10 native stages; targeted
Pyright 0 errors/warnings, pip check is clear. Runtime Python+JS net reduced by 706 lines.
The first location/link test errors and solution are clearly recorded in cleanup-checks.json.

Maintenance accepted by user, in commit ea8aa15. Real account/paid
No API testing; automatic proofs are kept under docs/reports.

### Previous accepted basis

- `526bfed`: delete in counter list via UI only; reactor theme accents
  separation from the situation. This step has been accepted by the user.
- Previous detailed change/acceptance history is preserved under Git and docs/ski;
  old logs are not copied back into the architecture.

Demo additional verification: native bridge/instance lock **92 pytest passed** (9.76 s);
compileall and pip check clean correct venv with package tools/main Pyright **0**.
The first type round found incorrect interpreter import errors and metadata path type;
Fixed by collapsing interpreter selection/path. The package report also includes initial errors.


English cleanup verification: **1,172 pytest passed** (167.09 s), **9 JavaScript
suites**, **16 browser groups**, **10 sequential native phases**, Pyright **0** and
clean dependency checks. The final archive/hash/link check passed **2 tests**.
Initial translated-fixture failures were corrected and are recorded in the report.
One concurrent native run crashed in pythonnet/WinForms teardown after successful
reopen checks; the sequential rerun passed. Its root cause remains open and is not
claimed fixed. Real-account/paid API and clean-PC acceptance were not performed.
Explicit user authorization permits publication; physical media/demo acceptance
remains distinct. See reports/english-publication-checks.json and english-native.json.

Translated archive files use canonical LF bytes under the archive -text rule;
current manifest hashes were recalculated after normalization. Source hashes and
Git provenance remain unchanged. The final staged whitespace check is clean.
