# Changelog

Changes belong here, progress in [PLAN](PLAN.md), design in
[ARCHITECTURE](ARCHITECTURE.md). No application version has been released.
Older entries remain part of this record through the dated snapshot below.

## Unreleased

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
