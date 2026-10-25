> Historical maintenance findings, translated to English. Current status is in PLAN.md; original bytes remain in Git history.

# Maintenance and architectural inspection

This report describes the limitations of the existing code and the cleanup performed. "No unnecessary
It is not a guarantee of "no more lines" or "no more bugs". Current works
[PLAN](PLAN.md), change record is in [CHANGELOG](CHANGELOG.md).

## Scope and method

source/test/config/documentation, which was tracked by Git and added in this maintenance, was put into inventory.
Python AST and JS syntax scanning, import/caller/export searches; bootstrap,
bridge, model→core, note/meter, audio/wake/Stop and record ownership were followed.
The export was not deleted without checking the dynamic public bridge and test callers.
File based paths/lines/hash and control type
[located in cleanup-inventory.json](reports/cleanup-inventory.json).

This does not mean that all rows are individually proven by hand. critical paths
read and tested with regression; Static inventory/syntax control applied to all resources.
Virtual environment, Git content/cache, user data root, reference Mark-LVI-main and
Installed third-party package sources were not included in the product source check.
The contents of the 133 files in the archive are protected with SHA256; Historical links are not rewritten.
Archive content compared with HEAD: the only difference is the checkout CRLF/LF conversion,
There is no difference in text content. .gitattributes keeps archive bytes constant from now on.
Full license/provenance review of UI assets remains open.

## Cleaning done

| Before | After / reason |
|---|---|
| app.js 1675 lines; start + shell + chat state | app.js 323; shell.js visual shell; assistant_session.js single owner conversation/mic/sleep |
| settings.js 1033 lines; device/layout in the same file | settings.js 701; devices.js and layout.js separate responsibility, preferences.js single common object |
| Unused path MediaRecorder/decode | Removed; real AudioWorklet input and tests left |
| UI routine/calendar browsers, non-native commands | Removed; Without backend it is not said "started" |
| Free shortcut → native event/fake timeline | Removed; saved text preserved, scheduled area disabled |
| Large script blocks in native runner | moved to native_scenarios.py; same runner and temporary fixture |
| REST/Live two separate same tool list | The same module constants are used; permission scheme/core unchanged |
| Conflicting README logs and messy milestone documentation | Current guides and single plan/changelog; old content archive |

Runtime Python+JS total **12,409 → 11,703 lines**, net **706 lines reduction**.
Calculated including moved rows; We did not count the document archive as code deletion gain.
There is no new runtime dependency/framework. Detail [metrics](reports/cleanup-metrics.json).

CSS is the style file for the single view; It was not broken down into just 1582 lines. schema.js
keeps boundary validation together. assistant_session.js is still 942 lines; stop,
To avoid duplicating wake, microphone and delayed response IDs across different owners
kept together. Native test runner's synthetic provider fixture is also in line
It was not converted to the new testing framework in order to reduce the number of tests.

REST protected by user request. Browser-only view and legacy setting reading/bridge
aliases are true means of compatibility. Public read-only widget setters,
The probe and JSON schemas used in the test were not deleted due to "infrequent calls".
Skill/routine editors and existing user definitions are retained; Execution is a separate open business.

## Architecture alignment and kalan findings

Working model actions **ModelTools → registry/policy → TaskManager → field tool**
passes through the line. Note/counter was not moved to the second executor. UI controls and local KWS
It is not a natural language router. Removed shortcut/scheduler paths broke this distinction.

| Priority | Findings and evidence | Decision |
|---|---|---|
| Closed (5.F7.3) | On persistent core, 256 RAM/active is the throughput limit; terminal records are queried from SQLite. | Old IDs remain in the disk index. Open rejection when active queue is full; Disk history is not automatically deleted. |
| Closed (5.F7.2) | TaskManager holds identity/request/result with SQLite FULL transaction; Core has a single owner lock. | Restart does not execute the old one; half-started job unknown, queued cancelled. This is not exactly-once for external services; model session RAM is not revived. |
| P2 | The log is indefinite and unencrypted; unknown locks new jobs profile-wide. | Disk/boot cost grows with history; The old note text may remain. There is no user-facing mediation and secure disk compression yet. |
| P1 | json_store.py uses atomic replace; native main now holds the data root OS lock. | 5.F7.1 native turns off same-profile conflict. JsonStore alone does not provide locks for non-host scripts. |
| P2 | main.py knows private boundaries such as bridge._chat._live.close on closure. | There is no second socket owner, but there is a host/bridge connection. In the next lifecycle change, the current owner's public closure point should be used; A new manager should not be installed. |
| P2 | Skill/routine definitions localStorage; There is no core execution and no backend scheduler. | Editorial coverage today. Advanced integration should be done under single backend ownership. Temporary execution with local scheduler not established. |
| P2 | Google/Telegram/Discord/GUI is not available yet; external data taint/channel principal/risk confirmation system is not OK. | These are not written as if they were available for today's limited local tools. Mandatory before opening external content and risky actions. |
| P2 | There is no backend equivalent of base instruction/greeting/browser preferences in the UI. | It seemed to work quietly before; now planned/disabled, existing text is retained. |
| P3 | NativeBridge 613 lines and assistant_session 942 lines; life cycle branches dense. | For now, the sole owner is protected. The new feature should be released with the actual contract limit, without being crowded into the same file; It should not be divided only by the line threshold. |

P1s do not mean that everything new has been re-architected in this round.
This maintenance is safe dead-code/doc cleaning; long session/deployment close above
cannot be declared “production ready” without accepting clear boundaries.

## Customizable must-haves and constants

| Topic | Real situation | Suggestion |
|---|---|---|
| Response tone | Live conn.voice depends on documented preset Live list and session speech_config; REST speech.py ​​Korean constant | Live selection implemented; Separate scope of preferences when productizing a REST channel |
| Response volume | replyVolume is a 0–1 gain on the same PCM player; Settings Audio bar, permanent recording and reset are connected | Implemented in 5.F8.1; separate from effects. Audio character/voice selection is a separate open job |
| REST default/fallback and TTS model | gemini.py DEFAULT_MODEL/FALLBACK_MODEL, speech.py ​​SPEECH_MODEL constant | The main desktop Live model is selected and registered from the API; Move to separate provider preference when productizing REST channel |
| User instruction/language | pIns/pLang actually goes to common model instruction | It works; security/tool ​​permission cannot be changed with personal prompt |
| Base override / greeting | pSys/pGreet reserved text only | Not yet connected |
| User memory | pMem + open pMemory; by hand and model save/fix/forget, common REST/Live context | 6.1.1–3; single adjustment tank, snapshot/single target/shared lock; In on-demand learning, the user chooses review or direct enrollment; semantic screening provider dependent |
| Browser / new tab / app priority / shortcut | pBr/pTab/pApp/pSc legacy preference only | As for the relevant plugin/resolver, connect it to a single service; currently disabled |
| Wake word | pWake depends on the backend; Vex/Veks/Rex family, English dictionary limit in special word | There is no claim that all languages ​​are free; other language model/lexicon calibration separate job |
| Wake sensitivity, speech threshold, idle sleep | Current settings depend on actual backend/worklet | They are not fixed; wake change applies to next sleep |
| UI text language/date and a few shell messages | UI English; separate from model response language pLang | User wanted English UI before. Single locale layer if multilingual UI is desired; not by copying dictionary |
| Theme/SFX/devices | Default purple, threshold and device selection may vary from current settings | Having a default value is not a hardcoded behavior error |
| Memory 12 laps/16k/2k, audio 15 s, deadline/PCM limits | Technical limits of security/resource | Converting each number to a setting. One advanced config if the need is measured; validation/replay/permission leave limits to user prompt |

The “boss” at the end of the timer is not a fixed pattern address; model personal instruction
uses. UI timer/alarm text and personalized voice response are two different things.

## Validation and limits

Results of the first 5.F6 maintenance [in cleanup-checks.json](reports/cleanup-checks.json), actual
WebView2 synthetic acceptance is in [cleanup-native.json](reports/cleanup-native.json).
5.F6 result: **996 pytest**, **9 JS suite**, **4 browser groups**, **10 native stages**
successful; app and **Pyright 0 error/warning** in affected Python files. pip check
found no dependency conflicts. 78 Python and 34 JS/MJS files were syntax scanned.
Hashes of 133 archive files and current document links have been verified.
Python, JS, browser, type checking and archive/link tests are evaluated together.
The file-location assumption in the first regression was updated to the new import graph in testing;
The first unsuccessful attempt was not disguised as the last success. Legacy MediaRecorder self-test
does not count as evidence of removed active behavior; stream/permission/Stop tests remain.

In this regard, real Google account/paid API, live resume/GoAway and physical
Replacement microphone/echo/device was not retried. Automatic tests acoustic accuracy,
It does not prove indefinite stability, zero bugs, or all possible dynamic third-party callers.

## Short manual accept

1. Open the native application; registered theme/model and get local definitions in place.
2. A temporary note add/complete/delete; verify single registration and renewal.
3. Create Timer/stopwatch, right-click pause/reset and delete; keep it correct tab/ID.
4. If you have live access, try talk/Stop/Sleep/Wake; Do not let Mic Off interrupt the response.
5. Planned Google/voice/inspect etc. controls cannot take action; skill/routine editors
   keep the definition and make it clear that Run is not connected yet.

If the API limit persists, leave item 4 as untestable; don't skip the others. Previous
User acceptance does not replace manual acceptance of this maintenance change.


5.F8.1 current verification: 1024 pytest, 9 JS suite, 5 browser groups, app Pyright 0
and 10 native stages. [Result](reports/reply-volume-checks.json),
[native](reports/reply-volume-native.json). Sound level physical sensation/API
It is not acceptance; The user confirmed that it worked.


6.1.2 open model memory: added memory.read/patch to existing profile; second
authority yok. Snapshot/single target, UI base/shared store lock, readback,
Stop/replay and draft protection verified. 1050 pytest, 9 JS, 7 browser,
10 native and Pyright 0; [evidence](reports/model-memory-checks.json).
There is no acceptance of real model and automatic inference; The user waits for the test.


6.1.3: opt-in recommendations, host resource evidence, single RAM candidate and actual with pLearn
The UI Save/Dismiss decision was connected to the common core line. Suggestion spontaneous profile
there is no truth; source matching is not a guarantee of semantic correctness. 1065 pytest,
9 JS, 8 browser, 10 native and Pyright 0; [evidence](reports/memory-suggestions-checks.json).
Actual model quality/paid API not tested; The user waits for the test.


Reopened with source_unavailable in 6.1.3 manual testing: verbatim model quote
The condition was erroneous in actual speech. Resource connected from current turn owner; quote
Variation regression fails before correction, succeeds after.
1068 pytest, 8 browser, 10 native and Pyright 0; [evidence](reports/memory-source-checks.json).
Re-acceptance is expected at the actual provider; previous synthetic success manual acceptance
It is not presented as. The task log may also contain the actual resource message.


User did not perceive the Review button as visible confirmation on successful recommendation;
It was candidate behavior that expected not to be written in the personal area yet. Confirmation window
It was made automatic opening; If pMemoryConfirm false is selected, the same core
A verified record is added directly to the line. 1074 pytest, 9 JS, 9 browser,
10 native and Pyright 0; [evidence](reports/memory-review-checks.json).
Inference error may be recorded in automatic mode; The actual model awaits acceptance.


6.1.3 current approval flow: user accepted previous slice ask/auto-save;
Commit c5d086c received. In my new language, instead of modal, there is a separate text next to chat.
Save/Dismiss same memory.decide, fresh ID and as next user response
There is the same-kind self-certification barrier. 1081 pytest, 9 JS, 9 browser,
10 native and Pyright 0; [evidence](reports/memory-voice-review-checks.json).
The semantic approval/rejection distinction of the actual model awaits user testing; structural
The identity/turn protection does not claim that this distinction is perfect.
