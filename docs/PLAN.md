# TaskVex — Current plan

## Forward rule: provider details stay isolated; final migration after features

From this decision onward, new provider-specific SDK/configuration/parsing code
stays in provider-facing modules. Existing Gemini coupling is not claimed removed.
The functional order below remains unchanged; the user requested the final
provider-adapter migration after the planned application capabilities are complete.
This rule does not authorize immediate adapter implementation or automatic commits.

## Now: stage 6 scope closed; stage 7 choices recorded, implementation not started

The user reported successful screen-sharing tests, explicitly deferred additional
audio sharing to stage 9, and authorized closing stage 6. This closes the agreed
functional scope, not every quality/release boundary. No stage 7 implementation
has started, and commit/push remain deferred by explicit user instruction.

- [x] Personal memory, telemetry/network/token views, media/volume and weather accepted.
- [x] Camera/permissions and screen sharing accepted as reported; exact OS/device/
  provider coverage was not independently enumerated.
- [x] Former 6.8.3 additional audio inputs moved to 9.4, unimplemented and scope pending.
- [x] Latest automatic evidence retained: 1,279 pytest, nine JS suites, 29 browser
  groups, Pyright 0 and two targeted native phases; no new test run in this closure.
- [ ] Carry-forward defect: full native chat bootstrap timed out. Earlier intermittent
  startup/teardown stability remains unresolved; targeted success is not full acceptance.
- [ ] Release boundaries: updated demo rebuild, clean-machine/device coverage,
  provider quota/resume coverage and existing source limits remain open as documented.

Next implementation slice: **7.P1 private task journal**, before expanding file
or GUI content handling. The previous 7.0a-first draft is superseded by the
user-selected stage 7 sequence below. Dependency/library choices still marked
pending must be presented to the user before installation or implementation.
Resolve the native instability before claiming full native reliability/distribution
readiness; stage closure does not waive or hide this defect.

## 6.8.2 Screen sharing — accepted by the user; commit deferred

The user confirmed successful tests, clarified that 6.8.1 was already implemented,
and authorized the next slice. Camera/permissions and startup recovery are accepted
as reported; exact hardware/provider coverage was not independently enumerated.
Commit is explicitly deferred by the user.

- [x] Explicit source picker in Live Screen; no automatic selection or saved grant.
- [x] Same visual owner as camera, one source at a time, video only and local preview.
- [x] Existing request-scoped Live JPEG path; screen longest edge 1280 pixels,
  camera 640, shared 256 KiB and one-frame-per-second transmission bounds.
- [x] Off/OS end/denial/timeout/late grant cleanup; Off does not interrupt a reply.
- [x] Existing Stop, sleep, Disconnect, model/key/mode and unknown cleanup ownership.
- [x] Synthetic browser source/consent/lifecycle checks; screen content is untrusted data.
- [x] 1,279 full pytest tests, 128 focused tests, 9 JS suites, 29 browser groups,
  Pyright 0 and 2 targeted native phases. See reports/screen-sharing-checks.json
  and reports/screen-sharing-native.json.
- [ ] Full native regression: the chat-phase window bootstrap timed out before
  its assertions. The clean preceding startup-fix run does not close this recurrence.
- [x] User reported successful screen-sharing tests; exact picker/device/provider
  coverage was not independently enumerated.

No system audio, simultaneous camera/screen, image history, new model connection,
GUI clicks/inspection tools, file attachments or provider-adapter migration.
Additional audio inputs are deferred to **9.4** by the user; next is **7.P1**.

## Startup recovery correction — accepted by the user; commit deferred

Valid settings plus a persisted UNKNOWN media task reproduced the reported
startup lock. TaskManagerError inherited ContractError and was incorrectly shown
as settings_invalid. Retrying/repairing valid settings could not clear that latch.

- [x] Preserve TaskManager error codes; never propose settings reset for uncertainty.
- [x] Explicit local review of actual UNKNOWN IDs, without exposing arguments/results.
- [x] Durable acknowledgement separate from results/replay keys; restart retains
  review, old UNKNOWN remains unchanged and newly unknown tasks still block work.
- [x] Reject unconfirmed/invalid review, active work and unavailable task storage.
- [x] Same complete UI readiness after initial startup, Retry, repair and review.
- [x] Synthetic restart/replay, failure and browser/native recovery checks;
  see reports/startup-recovery-checks.json and startup-recovery-native.json.
- [x] 1,278 full pytest tests, 119 subsequent focused tests, 9 JS suites,
  26 browser groups, Pyright 0 and 11/11 native phases. A clean run does not
  establish that earlier intermittent native startup/teardown failures are fixed.
- [x] User reported successful tests and authorized continuation; specific review/
  restart coverage was not separately enumerated. Do not delete settings/history.
- [ ] Portable demo rebuild is not part of this correction; old EXEs lack the fix.

No real account/provider call, real-data mutation, automatic acknowledgement,
commit or push. Earlier general native startup/teardown instability and camera
manual acceptance remain open; this confirmed root cause does not close them.

## 6.8.1a Permissions settings — accepted by the user; native stability boundary open

The user could not grant camera access from the default-device selector. Selecting
a device does not request access; Camera On also waits for a ready Live session.
This correction adds Settings > System > Permissions independently of model readiness.
The user subsequently confirmed successful tests and continuation. The earlier
publication request explicitly authorized README publication
and committing/pushing this work; that authorization does not imply manual camera
acceptance or advancement to screen sharing.

- [x] Camera, microphone and location request buttons plus browser permission status.
- [x] Short default-device probes close tracks; location is discarded, never saved/shared.
- [x] Skip a second probe for an already open device; pending microphone setup is not a grant.
- [x] Bounded waits, late-grant cleanup, denial/unsupported status and no startup prompts.
- [x] Fixed Windows privacy-page links; opening Settings does not claim permission granted.
- [x] 1,269 pytest, 105 focused tests, 9 JS suites, 25 browser groups,
  2 targeted native phases and Pyright 0. Evidence: reports/permissions-checks.json
  and reports/permissions-native.json.
- [ ] Full native regression: startup timeout and WinForms/Python.NET teardown
  failures remain unresolved; do not treat targeted success as full closure.
- [x] User accepted camera/permissions tests; exact OS/device/provider coverage
  was not independently enumerated, and automatic checks use synthetic capture.

Browser/Windows remain the authorities. Save Settings does not grant/revoke access.
A blocked OS/browser policy cannot be overridden by an application checkbox.
No new model connection, provider call or feature stage is introduced.

## 6.8.1 Camera — accepted by the user

The preceding UI cleanup was accepted and committed as `6e18e99`.
This step connects explicit camera input to the existing Live conversation owner.
It does not start screen sharing, additional audio capture or GUI automation.

- [x] Explicit Camera On/Off, exact saved device selection and automatic device listing.
- [x] Video-only browser permission; late permissions, denial and device end cleanup.
- [x] Bounded JPEG input on the existing Live socket for active user messages only.
- [x] Request IDs, sequence, latest-only RAM, one-frame-per-second send ceiling and expiry.
- [x] Stop ends transmission; Camera Off preserves the current microphone and reply.
- [x] Sleep, Disconnect, model/key/mode change, unknown outcome and page close release capture.
- [x] 1,265 pytest, 13 camera tests, 9 JS suites, 23 browser groups,
  10 native phases, Pyright 0 errors/warnings and clean dependency/diff checks.
  Evidence: reports/camera-checks.json and reports/camera-native.json.
- [x] User reported successful tests and authorized screen sharing. No paid API or
  real camera was used in automatic checks; exact manual coverage was not enumerated.

Camera defaults Off on every launch and after sleep/disconnect; its selected device
can persist through Save Settings. Idle capture stays local; visual data is sent
only inside a Live user turn. Previously sent frames cannot be recalled and may
remain in the provider session context. The portable demo has not been rebuilt.
Current following slice: **6.8.2 screen sharing**; camera is not being reimplemented.

## 6.4 weather/location — accepted; UI cleanup accepted

Accepted weather work: commit `9910ae4`. Requested source-credit, media-label and
memory-help cleanup is implemented; all 21 browser groups and git diff checks
passed. The user accepted the cleanup; it is committed before starting camera work.

The user narrowed remaining stage 6 to weather and multimodal input. No file,
Google, Telegram, Discord or web-search integration belongs to the current step.
Weather (6.4), camera (6.8.1) and screen sharing (6.8.2) are now accepted.
The user moved additional audio sources (former 6.8.3) to 9.4 and closed stage 6
within the remaining agreed scope, retaining the recorded native/release limits.

| Previous scope | Current destination | Dependency |
|---|---|---|
| 6.3 file attachment/read/change | 7.0 local files and task context | Permission/target/content boundaries before sending file contents to a model |
| Web search formerly in 6.4 | 7.3 browser/web tools | Read-only service adapter and untrusted-content handling, then GUI browser interaction |
| 6.5 Google Calendar/Drive/mail | 9.2 external services | 9.1 risk/channel/unknown protections before external writes |
| 6.6 Telegram/Discord | 9.3 channels | 9.1 plus explicit destination/principal and delivery evidence |
| 6.7 external-write safeguards | 9.1 service prerequisites | Required before 9.2/9.3 writes; local file/GUI safeguards stay in stage 7 |
| 6.8.3 additional audio sharing | 9.4 additional audio sources | Agree source/recording scope, explicit consent, retention and cleanup; no implicit system audio capture |
| Remaining 5.F8.3 profile fields | Relevant 6.8/7/8.4/9 slices | Audio/visual preferences with 6.8; browser/apps with 7; bounded greeting/instructions with profile/schema work; service preferences with 9 |

These are moves, not completed capabilities. Existing 7.x and 8.x IDs remain;
stage 9 adds external services after the core desktop/automation milestones.
Weather source/settings/cache/tools/UI are implemented in this step; validation
and manual acceptance remain distinct. Evidence: reports/weather-checks.json.

- [x] Shared Weather owner, weather.read capability and REST/Live tools.
- [x] Explicit manual place selection, approximate Auto consent, persistence and Clear.
- [x] Cache/backoff, source time, stale/unavailable states, validation and attribution.
- [x] 1,252 full pytest, 142 targeted tests (22 weather), 9 JS suites,
  21 browser groups, 10 sequential native phases, app/focused-test Pyright 0.
- [x] Real public-service probe succeeded for a fixed public reference coordinate;
  no user location or paid conversational provider was used.
- [x] User reported successful tests; specific OS/provider coverage was not separately enumerated.

Weather uses the non-commercial public Open-Meteo endpoint; commercial service
terms require review. The native weather location is not in legacy UI backups.
Cached conditions are modelled current weather, not a station reading or daily
forecast. Camera/screen/additional audio, web search and external accounts remain
outside this step; the portable EXE was not rebuilt. Accepted weather work is committed before the requested UI cleanup.

## 6.2.5c Player volume and quiet media UI — accepted

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

## Stage 6 multimodal sequence — accepted scope closed

1. **6.4 Weather/location — accepted:** explicit manual place selection or user-triggered
   approximate geolocation, saved consent, modelled current conditions, shared
   model/UI cache, timestamps and real failure/stale states. Web search is excluded.
2. **6.8.1 Camera — accepted:** permission, device selection, Live frames and cleanup.
3. **6.8.2 Screen sharing — accepted:** explicit source selection, start/stop and Live frames.
4. **Former 6.8.3 additional audio inputs — moved to 9.4:** not required for stage 6 closure.
5. **Stage 6 closure — authorized by the user:** functional acceptance recorded;
   full-native bootstrap instability and release limits remain explicitly open above.

Camera/screen understanding is not L4 clicking/GUI automation. Sensor temperature,
VRAM and actual API transport latency remain documented source limits, not new
mandatory integrations secretly added to stage 6. Skills/GUI remain stage 7,
routines/scheduler stage 8, external services/channels stage 9.

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
| 6 | Agreed functional scope closed by the user; native/release limits carried forward | Memory, measurements, media/weather, camera and screen sharing; additional audio moved to 9.4 |
| 7 | User-selected scope recorded; implementation not started | Private journal and task authorization/lifecycle, general L0-L4 desktop/file/browser operation, read-only Plugins and learned skills |
| 8 | Not started | Single backend routine/scheduler, background lifecycle, maintenance and core packaging |
| 9 | Deferred by user | External-service safeguards, Google integrations, Telegram/Discord channels and additional audio sharing |
| 10 | Planned after functional stages | Provider-adapter separation; remove Gemini assumptions from shared orchestration without changing tool execution ownership |

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
- Restart log does not replay completed actions; interrupted started work becomes
  unknown and queued work is cancelled. Explicit startup review can acknowledge
  uncertainty without changing old results/replay keys; restart alone cannot.
  Disk history grows and can keep old note contents; there is no automatic cleaning.
- Native single-instance lock implemented in 5.F7.1; direct script writers are the same
  Must use host lock agreement. Third party/entity packaging licenses before distribution.
- Short user acceptance for 5.F7.2/3 → commit; before these conditions are considered resolved
  There is no unlimited/production ready claim for Stage 5. Developing with open boundaries
  The decision to continue and the next single step is determined by the user.

## Substeps of subsequent stages

### 7 — General desktop operation, local files and learned skills

**Status: user-selected scope recorded; every implementation slice is planned.**
This replaces the earlier narrow-app/format draft. The goal is operation and
learning across previously unknown applications, not a fixed supported-app list.
Netflix, WhatsApp, YouTube, Discord and music playlists were illustrative tasks,
not instructions to hardcode app-specific commands or promise universal success.
Representative test applications establish evidence, not a product allowlist.

#### Confirmed choices

- General desktop application discovery and switching are allowed within the
  requested task. All routes retain ModelTools -> registry/policy/TaskManager.
  L0 direct tools, L1 learned procedures, L2 DOM, L3 UIA and L4 visual control
  share execution, authorization, cancellation and verification; there is no
  less-controlled executor for unknown applications or phrase-based intent router.
- Explicit tasks proceed directly; irreversible/high-impact steps require one
  confirmation for the concrete operation/scope. Approval is not blanket permission
  for changed targets or effects. File access is limited to task-selected or
  specified files/folders; expansion requires permission.
- Background-capable steps may continue. Physical keyboard/mouse handover asks
  by default, with a user-requested setting to disable that question. A grant
  lasts only for its task and never replaces high-impact confirmation. Check
  focus/user interaction and fresh targets before physical input.
- The task authorizes provider images of the relevant window/area only while
  needed for that task. Stop sending at task completion. No unrelated desktop
  upload or persistent screenshot history; explicit source/scope remains required.
- Visual-only evidence may support continuation when clear; record its evidence
  type without storing the screenshot. Unclear outcomes require clarification,
  never a fabricated verified result or a retry of an uncertain effect.
- Tasks continue until finished or stopped, with bounded operation waits/retries
  and a no-progress stop/explanation rather than an arbitrary total task timeout.
  A Live conversation turn is not the whole logical task.
- While a task runs, answer immediate questions, queue independent application
  tasks, and apply task-related corrections to the current task. Stop has priority.
  Definite failure blocks dependent steps; independent steps may continue and
  receive separate results. UNKNOWN retains existing safety locks; it is not a
  definite failure that permits unrelated mutations to bypass the lock.
- Login, CAPTCHA, two-factor authentication and elevation wait for human
  intervention. Independent work may continue if safe. Reobserve before resuming
  after the user says intervention is complete; do not bypass these boundaries.
- After restart, show interrupted tasks. Only an explicit Continue triggers fresh
  observation and planning of remaining work; completed/uncertain effects are
  never blindly replayed. Permission scope must be revalidated, not inferred from
  a stale target or an old physical-control grant.
- Persist task/result summaries and durable replay protection, not screenshots,
  file bodies or message text. Deliberately saved user files/notes and parameterized
  skills are separate records. The current journal still stores full arguments/
  results; privacy migration is required, not already implemented.
- Both existing browser sessions and a Vex-specific profile are desired, selected
  by the user. Technical access limitations must be shown; do not copy credentials
  or assume every existing session permits DOM attachment.
- Common text/code, CSV/spreadsheet, PDF, Word and image formats are in scope for
  reading/creation/editing where meaningful. Use the actual application when complex
  format-preserving edits require it. Publish exact operation/fidelity limits; do
  not promise lossless editing of every file or treat images as text documents.
- Automatically save only verified, parameterized learned methods without a
  confirmation prompt. Group capabilities dynamically per application: a later
  method extends that application's skill. Users can delete learned skills.
  Do not save passwords/private message bodies or literal old target coordinates.
- Command-driven GUI messages/calls are in stage 7. Automatic replying requires
  explicit person/task activation and ends with that task. Official service/API/bot
  integrations stay in stage 9; persistent scheduled/background lifecycle stays in 8.
- Add a separate **Plugins** screen. Existing built-in domain capabilities such as
  notes/clocks appear as **System default**, read-only, not deletable or toggleable.
  Skills remains the learned-method screen. This does not move every module or
  create a second registry. Frequent-app code plugins can be added in later stages;
  no external plugin installation/import mechanism is authorized in stage 7.
- Maintained dependencies are allowed when needed; reliability takes priority over
  minimum package size. Select actual libraries with the user before adding them.
  Start L4 with the existing visual provider; **propose local OCR to the user if
  text localization/recognition proves inadequate**, rather than silently adding
  it or forgetting this option. OCR does not establish successful action execution.

#### Implementation order and acceptance

Rows are in dependency order; existing 7.0–7.5 IDs are retained and new prerequisites
use 7.P. Each row is reviewable separately; split further only when actual scope
requires it. Tests accompany every slice, not only stage closure.

| Slice | Deliverable | Acceptance and boundary | Status |
|---|---|---|---|
| 7.P1 | Private persistent task journal | Migrate raw arguments/results to content-free summaries and safe replay metadata; old request IDs/conflict detection/UNKNOWN protection survive migration and restart. Test historical records and interrupted/failed migration with temporary journals; no deletion of replay history | Planned; next implementation slice |
| 7.P2 | Shared task authorization | File/window/browser/person scope, high-impact confirmation, relevant image grants and task-duration physical-control approval; UI preference for asking about handover. Same policy regardless of layer | Planned |
| 7.P3 | Shared observations and fresh target references | Real application/window/tab/document IDs and generation, focus, display/DPI/frame geometry; distinguish no match, unsupported, denied, stale and uncertain dispatch. Fallback never retries unknown effects | Planned |
| 7.P4a | Logical tasks and dependency-aware progress | Task/step identities separate from Live turns; existing execution authority, cancellation, queued independent tasks, corrections and immediate questions. Definite failures block dependents only; no worker self-wait or competing executor | Planned |
| 7.P4b | Human intervention, recovery and progress limits | Pending human actions and reobservation; manual Continue after restart; bounded per-operation retries/no-progress detection, without a total task-duration cutoff. Preserve UNKNOWN locks and completed effects | Planned |
| 7.P5 | Read-only Plugins screen | Built-in capability metadata from existing registration/owners; System default badge, no delete/toggle, separate from learned Skills. No runtime auto-import or speculative third-party plugin framework | Planned |
| 7.0a | Selected local files and text/code/CSV reading | Real scoped file references, type/size/path/link checks, encoding and changed-file detection; temporary files first, no unrestricted filesystem exploration | Planned |
| 7.0b | File context and controlled text/code/CSV writes | Deliberately supplied context is untrusted and bounded; explicit destination, expected original snapshot, atomic write/readback and recoverable original where applicable. No silent scope expansion or blind overwrite | Planned |
| 7.0d | PDF, Word, spreadsheet and image reading | Choose necessary libraries first; extract meaningful content with explicit type/size/fidelity limits. No macros/scripts or embedded instruction execution; test malformed and unsupported documents | Planned |
| 7.0e | Common document creation and editing | Verify content/formulas/structure as applicable; preserve recoverable originals. Complex edits requiring the application route depend on 7.1/7.3, rather than silently damaging unsupported layout/features | Planned |
| 7.1a | General Windows application/window observation (L3) | Discovery beyond the current Notepad fixture, trusted process/window identity and UIA targets; select the UIA library/thread owner with the user first | Planned |
| 7.1b | Application launch, switching and UIA actions | Generic fresh-target invoke/edit and post-action verification through the core. Representative apps are fixtures, not app-specific intent commands. Respect focus, physical handover and manual intervention | Planned |
| 7.3a | Read-only web search/page context (L0) | Bounded untrusted source content and source links; select source/access constraints with the user. No new conversation connection or hidden external writes | Planned |
| 7.3b | Browser profiles and DOM actions (L2) | User selects daily session or Vex profile, with truthful attach/launch limitations. Choose browser library/connection approach before implementation; fresh tabs/documents, scoped actions, protected session data | Planned |
| 7.3c | Task-scoped visual fallback (L4) | Relevant fresh window/area capture, known frame/DPI geometry, safe physical input and post-action evidence. Distinguish visual verification; ask on unclear results. Existing passive JPEG sharing is not coordinate automation | Planned |
| 7.4a | One backend skill/procedure store | Stable skill IDs, schema/parameter validation, per-app capability grouping, UI inspection/deletion and safe handling of old UI definitions. Unsupported definitions never become executable by import | Planned |
| 7.2a | Automatic verified procedure learning (L1) | Verified methods saved without prompting, per-app extensions rather than duplicate skills. No secrets/private payloads or success inferred from spoken claims; reuse the 7.4a store | Planned |
| 7.2b | Fresh procedure reuse and invalidation | Bind current task parameters, resolve current targets, recheck context/version and policy; changed interfaces invalidate/relearn methods without replaying old effects | Planned |
| 7.4b | Skill execution and task integration | Use the 7.P task lifecycle and shared core for each step; no second skill runner/queue/authority. Stop, dependency failures, uncertainty and durable replay remain intact | Planned |
| 7.4c | Inspect/teach and generic communication workflows | User-guided observations extend verified methods in the same store. GUI messaging/calls and explicitly activated person/task automatic replies use common target/authorization/verification rules, not per-phrase or per-app intent routers | Planned |
| 7.5 | Integration acceptance and closure | Temporary-data file/app/browser/learning tasks, malicious content, human focus changes, DPI/monitors, Stop, partial failures, restart and UNKNOWN. Verify task-scoped image/input/auto-reply cleanup and private journals; document actual app/format/provider limits | Planned |

The old 7.0c write slice is superseded by 7.0b/7.0e; it is not completed or a
separate duplicate write engine. 7.0e's application-dependent cases can only be
accepted after the corresponding automation route is available.

#### Decisions still requiring user selection before their implementation slice

- Actual UIA/browser/document libraries, licenses, Python/runtime compatibility,
  browser attachment approach and packaging impact: propose verified alternatives
  with their tradeoffs; no library has been chosen or installed by this plan.
- Concrete per-operation timeout/retry/no-progress values for 7.P4b, not an
  arbitrary cutoff for the entire logical task.
- Web-search source and any account/cost requirements before 7.3a.
- Exact built-in metadata grouping and format-operation fidelity matrix when
  implementing their UI/format slices. No universal format-support claim.

#### Gates and deferred scope

Before accepting native GUI control, reproduce the open WebView2 chat-bootstrap
timeout and fix the cause or report the remaining blocker. File/unit checks do
not close native startup/teardown instability; full native checks cannot be
reported passed after a timeout. Use synthetic transport/temporary data first;
real-provider/user acceptance is separate and must be reported honestly.

Every implemented slice updates the current contract/architecture only where
changed, COMMANDS for working capabilities, PLAN for status and CHANGELOG for
changes. No future directory tree, dependency set or provider framework is created
in advance. Commit/push remain deferred by the user's instruction.

Out of stage 7: persistent routine triggers/scheduler/background lifecycle (8),
new frequent-app code plugins in later agreed slices, official Google/channel API
integrations and additional audio sharing (9), and final provider migration (10).
Pull route-independent risk protections forward into 7.P2 rather than allowing
GUI actions to bypass the safeguards planned for service APIs. Nothing here is
implemented merely by recording these decisions.

### 10 — Final provider-adapter migration (planned, not started)

1. Inventory actual dependencies and define the smallest shared request/event,
   error, usage and capability contracts; retain real request/tool IDs.
2. Put existing Gemini transport, catalogs, voice, usage and resume handling behind
   its adapter. Compose it into Vex rather than constructing it in shared orchestration.
3. Remove remaining Gemini assumptions from shared session/bridge/UI contracts;
   preserve single lifecycle ownership, Stop, unknown outcomes, wake/sleep and playback completion.
4. Verify with a synthetic second provider and full regression. Real second-provider
   acceptance needs an explicitly selected provider/account; do not claim all models
   support Live audio, video, tools or resume. Keep the migration behavior-preserving.

These steps follow stages 6–9; they are not a dependency for the next local-file slice.

They have not yet been implemented; The desired single slice in each prompt is also narrowed down.

| ID | Purpose and acceptance limit |
|---|---|
| 6.1 | Manual/from the model memory, suggestion, ask and button/talk decision accepted by the user; last commit 6f52b4c |
| 6.2 | Telemetry/app/media tools; each measurement/process with real source and verification |
| 7.0 (moved from 6.3) | Local file reading/context, then controlled modification; target/permission and readback |
| 6.4 | Weather/location permission, manual selection, shared cache and freshness; web search moved to 7.3 |
| 9.2 (moved from 6.5) | Google Drive/Calendar/mail; OAuth scope, renewal, connection and transaction proof |
| 9.3 (moved from 6.6) | Telegram/Discord input-output; principal/target authorization, no replay on uncertain delivery |
| 9.1 (moved from 6.7) | External-data/risk/channel authorization and unknown reconciliation; prerequisite for 9.2/9.3 writes |
| 9.4 (moved from 6.8.3) | Additional audio-source/recording sharing beyond the existing microphone; agree source scope, consent, retention, bounds, Stop and cleanup before implementation |
| 7.1 | General L3 UIA discovery/actions; representative apps validate shared target and result contracts |
| 7.2 | L1 verified prescription; old target not used in context switch |
| 7.3 | Browser L2 DOM and bounded L4 vision; propose local OCR to the user if a concrete need emerges |
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
| 7.0 | Moved from 6.3: file attachment/read/context and controlled modification |
| 6.4 | Weather, manual/permitted automatic location, cache/freshness; web search moved to 7.3 |
| 9.2 | Moved from 6.5: Google services after 9.1 safeguards |
| 9.3 | Moved from 6.6: Telegram/Discord after 9.1 safeguards |
| 6.8 | Camera/screen sharing accepted; non-microphone audio moved to 9.4; visual understanding remains separate from GUI click automation |
| 5.F8.3 remaining profile areas | The initial greeting, browser/tab/application preferences, and shortcut fields are linked to the corresponding application/file/browser slice; personal instruction will not base override beyond safety limits |
| 8.1 | The only backend scheduler available for true local reminders; The second timer is not written, although it is separate from the skill/routine execution |

Timeline/log remains the current local view; new data producers are only real
feeds events. Inspect/Create Skill, skill execution and routine scope are in this UI
It is outside that UI scope. Camera 6.8.1 and screen sharing 6.8.2 are implemented
and accepted; additional audio is deferred to 9.4 and remains unimplemented.


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
