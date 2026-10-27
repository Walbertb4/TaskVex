# TaskVex — Current plan

## Now

Stage 6's agreed functional scope is accepted. Stage 7 choices are recorded;
7.P1 is accepted by the user and committed as `1126fba` (not pushed).
7.P2a was accepted and committed as `e9095d2` (not pushed).
7.P3a was accepted and committed as `dd586a1` (not pushed).
**Current: 7.P4a, backend logical task lifecycle and dependency-aware progress.**
Implementation and automatic validation passed; user acceptance is pending.
Conversation UI and scope teardown bindings remain follow-up work, not
capabilities enabled by this backend API.
Real driver bindings (7.P3b) accompany their UIA/DOM/visual steps; those libraries
are not selected or installed. Next prerequisite is 7.P4b human intervention/recovery/progress limits;
concrete budgets require user selection before implementation.
The accepted screen-sharing/startup-recovery baseline and stage 7 plan were
published as `79b5a04`. Documentation/log cleanup remains separate from stage 7.

This file owns current progress only. Completed-step narratives are preserved in
[the 2026-10-27 snapshot](archive/2026-10-27/docs/PLAN.md), with earlier history in
[the older stage archive](archive/stages.md). Changes belong in [CHANGELOG](CHANGELOG.md).
Read Now, open limits and the current step; search other sections only as needed.

## Open limits carried forward

- Full native chat bootstrap timed out in the historical screen-sharing regression;
  earlier Python.NET/WinForms startup/teardown instability is unresolved. Targeted
  successes and the clean 7.P1 eleven-phase run do not prove that intermittent
  underlying issue fixed.
- Real-account resumption/GoAway and provider quota coverage remain unverified
  where recorded; synthetic transport is not real-account evidence.
- A synthetic Live timing test with a 60 ms deadline failed once under concurrent
  validation, passed in isolation and in the next full run. Timing-test stability
  remains a limit; no provider timeout behavior was changed or proven faulty.
- Schema-2 receipts omit arguments/result contents and migrate schema 1 before
  tools start; actual pre-existing user-profile migration was not exercised.
  Metadata/history grows on disk and is unencrypted. Fingerprints are not secret
  storage. Old external backups/OS/forensic copies are outside migration cleanup.
  Explicit UNKNOWN review acknowledges uncertainty, not success. Older builds
  cannot open the migrated schema; do not delete history to downgrade.
- Updated portable demo rebuild, clean-PC/device coverage, frozen restart and
  third-party asset/wake-weight redistribution review remain open.
- CPU/GPU temperature, VRAM capacity, actual provider transport latency and
  unsupported OS/player/hardware readings remain documented limits.
- Remaining greeting/base-instruction/profile fields (former 5.F8.3) are not
  implemented merely because settings exist. Preserve user definitions; attach
  them to their relevant profile/browser/service step rather than claiming success.
- No real/paid API call in Stage 7 prerequisite checks; native runs use temporary profiles and synthetic transports.

## Accepted baseline and evidence

| Capability | State / evidence |
|---|---|
| Shared contracts/policy/TaskManager, notes, Live/REST Stop, audio, wake/sleep and counters | Accepted functional baseline; historical detail in the dated snapshot |
| Personal memory, system/network/Gemini session usage, media/volume and weather | Accepted; exact device/provider coverage is limited to the recorded checks |
| Camera and permission controls | User accepted; [automatic checks](../logs/reports/permissions-checks.json) and [targeted native checks](../logs/reports/permissions-native.json) |
| Startup recovery with explicit UNKNOWN review | User accepted; [checks](../logs/reports/startup-recovery-checks.json) and [eleven-phase native run](../logs/reports/startup-recovery-native-full.json) |
| Screen sharing | User accepted; [1,279 pytest, nine JS suites, 29 browser groups and other checks](../logs/reports/screen-sharing-checks.json); [two targeted native phases](../logs/reports/screen-sharing-native.json), not a clean full-native run |
| Publication of baseline | `79b5a04`; 155 journal/manager/bridge tests passed before push. Not a new full regression |
| 7.P1 private journal | User accepted; committed 1126fba, not pushed. 215 focused tests, 1,290 full pytest, Pyright 0 and eleven native phases. [Checks](../logs/reports/private-journal-checks.json), [native](../logs/reports/private-journal-native.json) |
| 7.P2a backend scopes | User accepted; committed e9095d2, not pushed. 113 focused tests, 1,308 pytest on clean rerun, Pyright 0 and one native UNKNOWN/recovery phase. [Checks](../logs/reports/task-scope-checks.json), [native](../logs/reports/task-scope-native.json). No public UI/lifecycle binding |
| 7.P3a backend targets | 168 targeted/regression tests and Pyright 0 with synthetic adapters; [checks](../logs/reports/targets-checks.json). User accepted; committed dd586a1, not pushed. No real driver/UI/capture/input or full/native rerun |
| 7.P4a logical task backend | 107 focused tests, 1,371 full pytest, Pyright 0 and two synthetic native compatibility phases. [Checks](../logs/reports/workflow-checks.json), [native](../logs/reports/workflow-native.json). Acceptance pending; no public UI/model workflow binding |

## Roadmap

| Stage | State | Scope |
|---|---|---|
| 0–5 | Functional baseline accepted with open limits above | Core/host, notes, conversation, Stop, wake/sleep, persistent task/replay protection |
| 6 | Agreed functional scope accepted | Memory, measurements, media/weather, camera and screen sharing |
| 7 | 7.P1/7.P2a/7.P3a accepted; 7.P4a automatically verified | Remaining: driver-backed targets, lifecycle/permission UI, L0–L4 desktop/file/browser work, Plugins and learned skills |
| 8 | Planned | Routines, scheduler, persistent background lifecycle, maintenance and packaging |
| 9 | Deferred integrations | Official external services/channels and additional audio sharing |
| 10 | Planned after functional stages | Final provider-adapter migration |

New provider SDK/config/catalog/usage/error details stay provider-facing now;
existing coupling is migrated in 10. No new provider framework is authorized.

## Stage 7 — General desktop operation, local files and learned skills

**Status: 7.P1/7.P2a/7.P3a accepted; 7.P4a auto verified; real drivers remain planned.**
This replaces the earlier narrow-app/format draft. The goal is operation and
learning across previously unknown applications, not a fixed supported-app list.
Netflix, WhatsApp, YouTube, Discord and music playlists were illustrative tasks,
not instructions to hardcode app-specific commands or promise universal success.
Representative test applications establish evidence, not a product allowlist.

### Confirmed choices

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
  skills are separate records. 7.P1 implements private receipts and schema-1
  migration; it does not claim erasure of external backups or provider history.
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

### Implementation order and acceptance

Rows are in dependency order; existing 7.0–7.5 IDs are retained and new prerequisites
use 7.P. Each row is reviewable separately; split further only when actual scope
requires it. Tests accompany every slice, not only stage closure.

| Slice | Deliverable | Acceptance and boundary | Status |
|---|---|---|---|
| 7.P1 | Private persistent task journal | Content-free disk receipts, current RAM results, replay/conflict/UNKNOWN/review preservation; atomic legacy migration and restartable SQLite cleanup, without raw backups. Historical results cannot grant fresh targets | User accepted; committed 1126fba, not pushed |
| 7.P2a | Backend task authorization | Host-issued task scopes, exact resource/action grants, operation-bound high-impact approvals and task-duration input handover; shared schema/ModelTools/policy/worker path | User accepted; committed e9095d2, not pushed. Desktop scope issuance/permission UI remain unconnected |
| 7.P3a | Shared target-reference backend | Host-observed identity/generation, task ownership, fresh read before use, physical geometry/frame-age contracts and explicit resolution/fallback statuses. Policy/registry/worker path tested with synthetic adapters | User accepted; committed dd586a1, not pushed. No discovery/capture/input driver or public UI |
| 7.P4a | Logical tasks and dependency-aware progress | Task/step identities separate from Live turns; same worker/registry/policy path, cancellation, queued logical tasks and revision-checked unsent-step corrections. Immediate text-only questions need not hold the worker. No model workflow tool or UI classifier yet | Implemented/auto verified; acceptance pending. Host backend API only, not conversation integration |
| 7.P4b | Human intervention, recovery and progress limits | Pending human actions and reobservation; manual Continue after restart; bounded per-operation retries/no-progress detection, without a total task-duration cutoff. Preserve UNKNOWN locks and completed effects | Planned |
| 7.P2b | Authorization UI and lifecycle binding | Trusted user decisions, scope expansion, physical-input preference and task end/Stop/scope-change revocation. Bind real references from 7.P3 and logical tasks from 7.P4; a Live turn is not the whole task | Planned after 7.P3/P4; full 7.P2 remains open |
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
| 7.P3b | Bind real target adapters | UIA/DOM/visual steps must prove process/window lifetime, tab/document changes, real focus/physical DPI/capture geometry and driver-bound revalidation/cleanup. A bare PID/HWND or model-supplied generation is insufficient | Planned with 7.1a/b and 7.3b/c; full 7.P3 remains open until actual bindings pass |
| 7.4a | One backend skill/procedure store | Stable skill IDs, schema/parameter validation, per-app capability grouping, UI inspection/deletion and safe handling of old UI definitions. Unsupported definitions never become executable by import | Planned |
| 7.2a | Automatic verified procedure learning (L1) | Verified methods saved without prompting, per-app extensions rather than duplicate skills. No secrets/private payloads or success inferred from spoken claims; reuse the 7.4a store | Planned |
| 7.2b | Fresh procedure reuse and invalidation | Bind current task parameters, resolve current targets, recheck context/version and policy; changed interfaces invalidate/relearn methods without replaying old effects | Planned |
| 7.4b | Skill execution and task integration | Use the 7.P task lifecycle and shared core for each step; no second skill runner/queue/authority. Stop, dependency failures, uncertainty and durable replay remain intact | Planned |
| 7.4c | Inspect/teach and generic communication workflows | User-guided observations extend verified methods in the same store. GUI messaging/calls and explicitly activated person/task automatic replies use common target/authorization/verification rules, not per-phrase or per-app intent routers | Planned |
| 7.5 | Integration acceptance and closure | Temporary-data file/app/browser/learning tasks, malicious content, human focus changes, DPI/monitors, Stop, partial failures, restart and UNKNOWN. Verify task-scoped image/input/auto-reply cleanup and private journals; document actual app/format/provider limits | Planned |

### Approved review resolutions — implementation order

The user approved these six clarifications on 2026-10-27. They extend existing
acceptance criteria, not a second architecture or permission to implement all six
in one turn. Resolution 1 is accepted; authorization foundation is implemented.
The remaining resolutions and full UI/lifecycle/resource integration stay planned.

1. **7.P1 — private receipts:** keep full current results in bounded RAM, persist
   a versioned request fingerprint plus identifiers/status and content-free result
   metadata. Historical reads explicitly lack payloads and cannot grant fresh
   targets. Migration preserves replay/UNKNOWN/review identities; test interruption,
   rollback and cleanup of old SQLite content without creating raw-content backups.
2. **7.P4 — nonblocking logical waits:** human intervention/long operations release
   the execution worker and conversation lock when safe. Resume reobserves state;
   immediate questions and independent work can progress. Stop identifies its
   logical task. No second executor or blind retry after uncertain dispatch.
3. **7.P3 / 7.3c — automation capture:** define task-scoped local window capture with
   real window identity, timestamp and DPI/frame geometry, using the existing
   provider transport. Manual screen sharing stays a user control, not an assumed
   automation capture driver. Select the capture implementation with the user.
4. **7.0e — split acceptance by dependency:** direct document editing first;
   application-dependent complex editing only after its UIA/DOM/L4 route passes.
   Both preserve originals and verify actual results; unsupported layout is explicit.
5. **7.P2 / 7.4 — trusted authority:** only host-recorded user task/approval grants
   authority. Pages/files/messages/skills cannot enlarge it or carry old approvals.
   Test malicious content requesting file disclosure, wrong recipients and reused
   approvals; scope/risk checks apply equally through every execution route.
6. **Observation/learning slices — bounded context:** relevant windows/regions,
   paged DOM/UIA results and on-demand skill methods instead of full inventories.
   Avoid redundant unchanged observations and measure calls, observation size and
   provider-reported usage. Do not impose a total task-duration limit or claim
   savings without measurement; preserve capture/Stop/target freshness rules.

The old 7.0c write slice is superseded by 7.0b/7.0e; it is not completed or a
separate duplicate write engine. 7.0e's application-dependent cases can only be
accepted after the corresponding automation route is available.

### Decisions still requiring user selection before their implementation slice

- Actual UIA/browser/document libraries, licenses, Python/runtime compatibility,
  browser attachment approach and packaging impact: propose verified alternatives
  with their tradeoffs; no library has been chosen or installed by this plan.
- Concrete per-operation timeout/retry/no-progress values for 7.P4b, not an
  arbitrary cutoff for the entire logical task.
- Visual frame-age budgets with the actual 7.3c driver/provider latency; 7.P3a
  requires an explicit trusted budget and does not select a production default.
- Web-search source and any account/cost requirements before 7.3a.
- Exact built-in metadata grouping and format-operation fidelity matrix when
  implementing their UI/format slices. No universal format-support claim.

### Gates and deferred scope

Before accepting native GUI control, reproduce the open WebView2 chat-bootstrap
timeout and fix the cause or report the remaining blocker. File/unit checks do
not close native startup/teardown instability; full native checks cannot be
reported passed after a timeout. Use synthetic transport/temporary data first;
real-provider/user acceptance is separate and must be reported honestly.

Every implemented slice updates the current contract/architecture only where
changed, COMMANDS for working capabilities, PLAN for status and CHANGELOG for
changes. No future directory tree, dependency set or provider framework is created
in advance. Commit/push require the current user authorization; the accepted stage 6 baseline
was published as `79b5a04`. No stage 7 implementation has been committed.

Out of stage 7: persistent routine triggers/scheduler/background lifecycle (8),
new frequent-app code plugins in later agreed slices, official Google/channel API
integrations and additional audio sharing (9), and final provider migration (10).
Pull route-independent risk protections forward into 7.P2 rather than allowing
GUI actions to bypass the safeguards planned for service APIs. Nothing here is
implemented merely by recording these decisions.

## Stages 8–10 — retained scope

| ID | Purpose / acceptance boundary |
|---|---|
| 8.1 | One backend scheduler; no competing UI executor/player |
| 8.2 | Routine IDs, CRUD and triggers through shared execution; distinguish notification from mutation |
| 8.3 | User-enabled persistent background services; bounded private logs |
| 8.4 | Schema migration, crash recovery and secure update |
| 8.5 | Packaging, single-instance acceptance, licenses/SBOM and clean installation |
| 9.1 | External-service/channel principals, scope, high-impact approval and unknown reconciliation; route-independent safeguards are pulled into 7.P2 |
| 9.2 | Google Drive/Calendar/mail: OAuth scopes, renewal, connection and verified effects |
| 9.3 | Telegram/Discord official channel/API integrations: explicit destinations/principals, uncertain-delivery replay protection |
| 9.4 | Additional audio sources/recordings, moved from 6.8.3: select scope, consent, retention, bounds and cleanup before implementation |
| 10.1 | Inventory coupling; select minimal common request/event/error/usage/capability contracts |
| 10.2 | Existing Gemini transport, catalogs, voice, usage and resume behind the provider adapter |
| 10.3 | Remove provider assumptions from shared session/bridge/UI, preserving one lifecycle and Stop/replay rules |
| 10.4 | Synthetic second-provider and regression checks; actual account/capabilities require separate acceptance |

Stage 7 GUI messaging does not implement stage 9 official service integrations.
Additional audio sharing remains deferred, not required to close stage 6.
A routine is not a second task engine. Provider migration is behavior-preserving,
not a promise that every provider supports audio/video/tools/resumption.
