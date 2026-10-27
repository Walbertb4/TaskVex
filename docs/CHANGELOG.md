# Changelog

Changes belong here, progress in [PLAN](PLAN.md), design in
[ARCHITECTURE](ARCHITECTURE.md). No application version has been released.
Older entries remain part of this record through the dated snapshot below.

## Unreleased

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
