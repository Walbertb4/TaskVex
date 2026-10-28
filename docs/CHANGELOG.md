# Changelog

Changes belong here, progress in [PLAN](PLAN.md), design in
[ARCHITECTURE](ARCHITECTURE.md). No application version has been released.
Older entries remain part of this record through the dated snapshot below.

## Unreleased

### 2026-10-29 - Source publication with manual test deferred

- The user explicitly authorized committing/pushing the current source, including
  7.P2b.2b.1, without having manually tested that slice. Automatic checks remain
  distinct from manual acceptance; no binary release or updated demo is claimed.
- Updated README validation/limits and the PLAN continuation warning. The next
  implementation turn must remind the user about the deferred chat/Stop/microphone
  smoke check. Existing native instability, timing-test stability, real-account
  coverage, profile migration and packaging limits remain open in PLAN.


### 2026-10-29 - Host task progress and revision-bound Stop (7.P2b.2b.1)

- Accepted 7.P2b.2a was committed as d1a807f; no push.
- Added detached current-process progress filtered by trusted native principal and
  source. Queries do not execute tasks or expose private arguments/grants.
- Added exact-ID/revision Stop with atomic ownership checks in TaskManager, plus
  an actual native task selector/progress panel. Started effects keep their real
  result; acceptance is separate from completion. Unknown delivery locks controls
  without retry; stale replies cannot operate on the next selection.
- Existing conversation Stop/Disconnect stays unchanged. Split remaining work into
  trusted conversation production/classification and fresh Continue/recovery plus
  logical conversation mapping. No dummy tasks, new executor, phrase routing,
  provider change or library added.
- Passed 270 targeted/regression plus three documentation tests, Pyright 0,
  eleven JS suites, 31 browser groups, and native chat/UNKNOWN checks. Final chat
  rerun covers explicit selection; no new full pytest/eleven-phase native claim.
  Evidence: [checks](../logs/reports/workflow-view-checks.json),
  [targeted native](../logs/reports/workflow-view-native.json). Current step awaits
  acceptance; not committed or pushed. No real account/user data/paid API used.

### 2026-10-29 - Concrete task permission UI (7.P2b.2a)

- Accepted 7.P2b.1 was committed as 8365d55; no push.
- Added actual pending-step permission decisions to the existing TaskManager:
  separate scope expansion, task-duration physical input and exact high-impact
  approval. Nonces bind revision, current requirements and request fingerprints.
  Stop/changes invalidate old decisions; repeated identical outcomes add no grant.
- Added native plain-text Approve/Reject UI, ready-gated queries and explicit
  acceptance versus completion. Unknown delivery stays locked without retry;
  denial stays paused even if input questioning is subsequently switched off.
- Added verified saved askBeforeInput, default true, under Settings > System.
  It affects physical-input questioning only. Bootstrap shares scope/reference
  owners and denies scoped work without a trusted resolver. Legacy model tools
  retain their existing unscoped behavior.
- Browser regression caught and fixed both initial checkbox restoration and the
  snapshot field allowlist. No new dependency, executor, phrase router or model
  permission-grant tool. Normal conversation task production/Continue/recovery
  and Stop/Disconnect mapping remain 7.P2b.2b; actual drivers remain 7.P3b.
- Passed 132 focused/documentation tests, 1,474 full pytest, Pyright 0, ten JS
  suites, 30 browser groups and eleven native phases. Validation is in [checks](../logs/reports/task-permissions-checks.json)
  and [native evidence](../logs/reports/task-permissions-native.json). Synthetic
  transports/temporary profiles only, no real user data or paid API. This slice
  awaits manual acceptance; no current-step commit or push.

### 2026-10-28 — Managed task scope and target lifetime (7.P2b.1)

- Accepted 7.P4b.3 was committed as ac3e6e1; no push.
- Added opt-in binding of the existing TaskScopes/TargetReferences owners to
  TaskManager. Composition validates matching stores before worker startup;
  scoped workflows must own the scope for their actual logical task/principal.
- Added automatic end/Stop/close/UNKNOWN revocation and reference-cache cleanup.
  Planning and intervention waits retain task-duration authority; real in-flight
  results are preserved. History stubs cannot revoke another task's proposed grant.
- Added safe revisioned replacement with fresh host-issued scope, no active child,
  old-reference cleanup and no inherited input/high-impact approval. Restart
  recovery rejects stale scope before observation and rechecks before admission.
- Cleanup faults lock new work without erasing successful effects or allowing
  UNKNOWN acknowledgement to clear the fault. No new executor/permission store,
  public command or provider coupling.
- 238 focused tests and 1,460 final full pytest passed. Application/new-test
  Pyright reported zero errors/warnings; compileall and three documentation checks
  passed. Eleven native phases passed for unchanged unscoped desktop behavior;
  [native evidence](../logs/reports/workflow-resources-native.json). Final managed
  observer-guard changes were validated by the final complete Python regression.
- [Validation](../logs/reports/workflow-resources-checks.json). Desktop decision UI,
  physical-input setting, task/conversation Stop/Disconnect and real driver binding
  remain 7.P2b.2/P3b. This is host-backend composition, not general GUI control.
  Current slice awaits acceptance; no current-step commit/push or paid API use.

### 2026-10-28 — Explicit operation deadlines and safe read retry (7.P4b.3)

- Accepted 7.P4b.2 was committed as 959a64f; no push.
- Added validated host-only ToolSpec timeout/read-only/transient-code metadata.
  A configured read may retry once after a definite allowlisted failure, through
  the existing worker, registry/policy and same request ID/deadline/cancel Event.
- Rechecked authority, Stop and time before every handler delivery. Mutations,
  preflight failures, UNKNOWN and unconfirmed exceptions never retry. No handler
  was force-killed and no production timeout/classification was silently selected.
- Added honest host operation telemetry and configured-result evidence. Deadline
  expiry while I/O runs does not imply completion; late real success/failure is
  retained. Frozen terminal and unavailable historical telemetry avoid false claims.
- 315 focused tests, 1,438 full pytest, Pyright with zero errors/warnings,
  compileall and three documentation checks passed. All eleven synthetic native
  phases passed; [native evidence](../logs/reports/operation-policy-native.json).
- Existing registrations/evidence and Live/REST lifecycle remain unchanged.
  [Validation](../logs/reports/operation-policy-checks.json). Production adapter
  values and public task/permission UI remain follow-up work. Current slice
  awaits acceptance; no current-step commit/push or paid API use.

### 2026-10-28 — Persistent logical task recovery (7.P4b.2)

- Added schema-3 content-free logical records in the existing task journal, with
  atomic schema-1/2 migration preserving private tool receipts and UNKNOWN review.
  Old schema-1/2 builds reject the new schema; no downgrade by deleting history.
- Checkpointed plan identities before dispatch. Startup reconciles private tool
  receipts across the result/checkpoint crash window without restoring executable
  arguments, result bodies, resources, approvals or scopes.
- Normal close preserves unfinished logical work for explicit recovery; explicit
  Stop remains stopped. Added bounded principal-scoped recovery pages, revision-
  checked cancellation and trusted-host Continue with unlocked fresh replanning.
- Preserved logical IDs and historical call identities/outcomes; remaining work
  requires fresh step IDs. Failed/stale replanning cannot dispatch, and historical
  UNKNOWN is never upgraded to success after later steps finish.
- 146 focused checks, 1,410 full pytest and Pyright with zero errors/warnings passed.
  All eleven synthetic native phases also passed, including save/reopen, chat/Stop,
  UNKNOWN/recovery and invalid settings.
  [Native evidence](../logs/reports/workflow-recovery-native.json).
  Tests include actual synthetic process exits, migration rollback, late Continue,
  metadata corruption, storage failure after real synthetic success and replay
  protection. [Evidence](../logs/reports/workflow-recovery-checks.json).
- Public task/Continue UI and host scope cleanup remain 7.P2b. Deadlines/read retry
  remain 7.P4b.3. Legacy receipts without logical metadata cannot recover a lost
  plan. Real user-profile/provider acceptance and demo rebuild remain open.
  Current slice awaits acceptance; no commit/push or paid API use.

### 2026-10-27 — README and prerequisite publication

- Updated README with the accepted Stage 7 backend foundations and latest
  synthetic evidence, explicitly separating them from unimplemented GUI control,
  whole-task restart recovery and permission/lifecycle UI.
- Publication includes accepted prerequisite changes through 7.P4b.1. No new
  functional slice or demo rebuild was attempted in this documentation turn.
- Marked the generated Gemini smoke report as synthetic regression output; its
  mocked transport is not real-account/provider acceptance evidence.

### 2026-10-27 — Human waits and trusted progress checkpoints (7.P4b.1)

- Recorded user acceptance of 7.P4a and committed it as 57a49d3; no push.
- Recorded approved policies: indefinite user-intervention waits, three unchanged
  evaluations after a baseline, and at most one read-only transient retry with
  explicit operation deadlines. Retry/deadline execution remains 7.P4b.3.
- Added revisioned host pause/Continue to the existing TaskManager. Accepted child
  effects finish before yielding intake; safe independent jobs proceed while a
  task waits. Continue requires unlocked trusted reobservation, then rechecks
  revision/object identity, Stop/close and UNKNOWN before admitting any step.
- Added digest-only planning observations and a no_progress intervention. Failed
  observations leave state unchanged; polling/rewording plans cannot reset the
  counter. Fresh changed evidence or verified completed steps reset it.
- Preserved real late success, per-step policy/replay checks, private receipts and
  UNKNOWN locks. Old callbacks cannot revive stopped or evicted/recreated tasks.
  127 focused tests and 1,391 full pytest passed; application/new-test Pyright
  reported zero errors/warnings. Compileall and three documentation checks also
  passed. Two synthetic native chat/Stop and UNKNOWN compatibility phases passed;
  the initial temporary launcher failed to collect its result file and was corrected
  before repeating the checks, as recorded in
  [native evidence](../logs/reports/workflow-waits-native.json).
  [Validation record](../logs/reports/workflow-waits-checks.json).
- Backend only: no public UI/model command, automation driver or real provider
  request. Persistent logical recovery is next (7.P4b.2); actual operation wait
  values accompany the relevant adapters. The user accepted this slice for
  publication with the README refresh; 7.P4b.2 remains unstarted.

### 2026-10-27 — Logical task backend (7.P4a)

- Recorded user acceptance of 7.P3a and committed it as dd586a1; no push.
- Added validated dependency graphs, logical intake ordering, stable step IDs and
  revision-checked sparse corrections under the existing TaskManager Condition.
  Each child uses the existing registry/policy/worker and durable private receipts.
- Definite failure blocks dependants while independent branches can continue.
  UNKNOWN retains the global lock. Logical Stop distinguishes acceptance from
  actual completion, preserves late success and cannot stop a different job.
- Bounded RAM progress excludes private bodies; terminal arguments are cleared.
  An indexed receipt-history probe requires review before a lost plan can dispatch
  anything, including a reordered new-first step. No blind restart or effect retry.
- Passed 107 focused tests, 1,371 full pytest, Pyright with zero errors/warnings,
  compileall and two synthetic native chat/Stop and UNKNOWN compatibility phases.
  [Checks](../logs/reports/workflow-checks.json),
  [native evidence](../logs/reports/workflow-native.json).
- Host backend only: no model workflow tool, conversation classifier, UI progress
  binding or automatic scope/target teardown. Human waits, persisted logical
  recovery/manual Continue and selected progress budgets remain 7.P4b/7.P2b.
  No paid/real provider request, new driver/dependency or public command added.
  Current work awaits acceptance and remains uncommitted; no push.

### 2026-10-27 — Shared target-reference backend (7.P3a)

- Recorded user acceptance of 7.P2a and committed it as e9095d2; no push.
- Added one bounded, RAM-only target reference owner tied to active host task
  scopes. Trusted refresh callbacks revalidate identity/version, tab/document,
  focus, replacement and cancellation before use; issuing a ref grants no control.
- Added physical capture-region/DPI/frame-time contracts and guarded pixel mapping.
  Negative monitor origins are valid; logical coordinates, stale/future frames and
  unknown focus are rejected. Frame-age budgets remain explicit host decisions.
- Preserved no-match/unsupported/denied/stale/unavailable/cancelled status distinctions.
  Fallback is eligible only before known dispatch for no-match/unsupported, never
  after started/uncertain effects. This does not add a router or executor.
- Synthetic policy/ModelTools/registry/worker integration and lifecycle/geometry
  checks passed: 168 targeted/regression tests; application/new-test Pyright 0.
  [Evidence](../logs/reports/targets-checks.json). No full/native rerun: no existing
  UI, bootstrap, driver, transport or execution behavior was changed.
- Real native/DOM/visual bindings and acceptance remain 7.P3b alongside 7.1/7.3;
  the current Notepad probe and passive JPEG stream are not relabelled GUI control.
  No dependency install, actual desktop capture/input, provider call or new push.
  7.P3a awaits acceptance; 7.P4a logical tasks is the next prerequisite.

### 2026-10-27 — Backend task authorization foundation (7.P2a)

- Recorded user acceptance of 7.P1 and committed the accepted privacy/log/docs
  work as 1126fba; no push. Split 7.P2 into backend scopes and later UI/lifecycle
  binding, ordered after the real-target/logical-task prerequisites.
- Added host-issued RAM-only task scopes with exact resource/action grants,
  operation-fingerprint high-impact approval and independent physical-input
  handover. Revocation removes the task's grants; journal receipts never restore them.
- ToolRequest/ModelTools carry optional host authorization metadata outside model
  arguments. Policy keeps its existing capability checks and denies missing,
  foreign, revoked or out-of-scope access when a trusted resolver is configured.
  No new tool executor, public UI setting, file access or desktop grant issuance.
- Centralized the existing fingerprint helper in core contracts; unscoped wire
  shapes and digests remain identical, preserving schema-1 migration/replay.
- 113 focused tests and a clean 1,308-test full rerun passed, with Pyright 0 and
  one temporary-profile native UNKNOWN/recovery compatibility phase. The first
  full run had 1 failure/1,307 passes in an existing 60 ms Live timing test; that
  test plus 107 related tests passed in isolation. No provider code was changed.
  [Evidence](../logs/reports/task-scope-checks.json).
- Full 7.P2 remains open: real reference validation, lifecycle/Stop binding,
  permission decisions and input preference UI are later integration work.
  No real API, actual user files, new automation driver or new commit/push.

### 2026-10-27 — Approved review resolutions and private task receipts (7.P1)

- Recorded all six approved resolutions in existing stage 7 slices: private
  receipts, nonblocking waits, automation capture, document dependency order,
  host-owned authority and bounded observation/context. Only 7.P1 is implemented.
- Schema 2 stores identifiers/status, a versioned SHA256 equality fingerprint
  and content-free historical results. Full current results remain in bounded RAM;
  disk reads explicitly lack content and cannot grant fresh model targets.
- Migrated strict schema 1 in one transaction, preserving replay/UNKNOWN/review
  identities. Secure deletion plus a restartable VACUUM gate remove old SQLite
  payload pages; failed migration/cleanup blocks execution without deleting history
  or writing raw backups. Older builds reject the migrated schema.
- Kept memory-proposal replay provenance in the existing logical RAM session;
  payload eviction cannot trigger a duplicate append or a new source quotation.
- Verified 215 focused tests, 1,290 full pytest, zero Pyright errors/warnings,
  compileall, pip check and all eleven native phases. Tests use synthetic content,
  transports and temporary profiles, including migration process exit and rollback.
  [Evidence](../logs/reports/private-journal-checks.json) and
  [native regression](../logs/reports/private-journal-native.json).
- No paid API or actual user-profile migration, demo rebuild, commit or push.
  Digests are not encryption; external backups/provider/OS/forensic copies remain
  outside cleanup. A clean native run does not close earlier intermittent failures.

### 2026-10-27 — Central development logs and reports

- Moved 63 structured reports from docs/reports to logs/reports, and 58 loose
  console logs into ignored logs/raw/root and logs/raw/v1. SHA256 verification
  confirmed unchanged bytes; historical archives/report payloads remain intact.
- Updated current evidence links and contributor instructions. Four acceptance
  CLIs default to script-specific logs/reports outputs, preserving explicit
  --report overrides and creating destination folders. Native child diagnostics
  remain in per-run logs/raw/native folders after temporary profile cleanup.
- Demo build smoke evidence now writes to logs/reports. Application logging,
  credentials, task database and user profiles are unchanged.
- Six focused documentation/output-routing tests passed using temporary files,
  missing-key provider stubs and synthetic child processes. No real account,
  application launch, wake audio, native window or demo build was exercised.
- At this output-layout step, the six stage 7 review proposals still awaited
  approval; this entry did not add them to plan/contracts. No commit/push.

### 2026-10-27 — Focused documentation and reading rules

- Preserved exact pre-cleanup AGENTS.md and all eight top-level docs Markdown files
  in [the dated snapshot](archive/2026-10-27/README.md), with source revision and
  SHA256 hashes. The earlier 133-file translated archive/manifest is unchanged.
- Removed completed-step narratives from the plan while preserving stage 7 choices,
  planned slices, later-stage scope, open limits and evidence links. Corrected
  baseline publication status to commit 79b5a04.
- Moved domain architecture and UI field details into two focused references,
  preserving their text and links at the original section headings.
- Condensed contributor rules: heading/symbol searches, affected callers/domain
  sections and risk-based validation. Required checks and safety rules remain.
- Retained the command guide and third-party notices. The previous audit is linked
  as historical evidence, not a second current progress record.
- Documentation only; no runtime behavior, dependency, provider call or stage 7
  implementation. No new full/native regression, commit or push in this cleanup.
- Validation: both existing documentation tests passed; nine snapshot hashes,
  twelve moved sections and 74 current local links checked. Command guide and
  third-party notices are byte-identical; the older archive manifest is unchanged.
  The five common guides contain 70.6% fewer characters; this is not a measured
  token-cost or response-latency improvement.

### Earlier unreleased changes — preserved history

The [pre-cleanup changelog](archive/2026-10-27/docs/CHANGELOG.md) retains all entries
for stage 5 maintenance, personal memory, telemetry/network/media/weather,
camera/permissions, startup recovery, screen sharing and stage 7 planning.
Historical evidence is not a newly rerun check or a newly released feature.

The accepted baseline was published as 79b5a04; native startup/teardown,
real-provider and distribution limits remain in the current plan. Journal privacy
is addressed by the later 7.P1 entry, with its explicitly recorded boundaries.
