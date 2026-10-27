# TaskVex contributor rules

## Scope and reading

- Implement only the requested step. Use the smallest complete change; reuse
  existing owners/helpers, then standard/platform features and installed packages.
  No speculative framework, future directory tree or arbitrary file splitting.
- Start with docs/PLAN.md Now/open limits/current slice and the shared owners and
  execution rules in docs/ARCHITECTURE.md. For UI/backend changes, also read shared
  transport/lifecycle sections of docs/UI_BACKEND_CONTRACT.md.
- Use `rg -n` to locate headings/symbols, then read affected sections/callers.
  Follow only relevant domain links in docs/reference/. Do not reread the entire
  plan, command guide, changelog, archive or unrelated domain specs each turn.
- Read touched code and its callers/tests/config/exports before editing. Preserve
  validation, error handling, security, accessibility and hardware calibration.
  Verify dynamic/string references before declaring code dead.
- Obtain user selections for stage 7 choices marked pending in PLAN; do not silently
  choose libraries, install dependencies or change agreed scope.

## Architecture — mandatory

- Model actions use ModelTools -> ToolRegistry/Policy -> TaskManager. Preserve
  schemas, scope/permissions, real target IDs, ambiguity clarification, durable
  replay protection and verified results. Spoken success is not evidence.
- Interpret natural-language actions through structured model tools. No phrase
  lists, word-order rules, keyword/regex intent routers or per-app bypasses. Regex
  is allowed for format/parameter validation; local wake detection is not intent routing.
- Keep one authority per responsibility: executor, domain state, connection,
  turn/microphone/wake lifecycle and playback. Domain adapters/resolvers do not
  become alternate executors. UI buttons and model tools share application logic.
- Acceptance, cancellation request and actual completion are distinct. Preserve
  completed effects, Stop/Disconnect cleanup, late-result isolation and UNKNOWN
  locks. Deferred actions use the existing lifecycle owner and request ID;
  no feature-specific second scheduler/player. Local mic/wake/Stop stay local.
- New provider SDK/config/catalog/usage/error details stay provider-facing; no new
  Gemini imports in shared core/domain tools. Migrate existing coupling in the
  final planned provider step, preserving capability differences and one lifecycle.
- Explain necessary contract changes and update callers/tests/documents together.
  Record unmigrated paths as open; existing exceptions do not authorize bypasses.

## Validation and language

- Run targeted tests and regression/native checks justified by affected paths.
  Broaden for integration risk, failures or required acceptance; do not repeat
  unchanged full suites without a reason. Never cut required checks.
- Nontrivial logic needs a meaningful test/self-check. Trivial edits do not need
  tests that merely repeat implementation. Mark deliberate limits with
  `shortcut: <limit>, <when to revisit>`.
- Repository prose is English: docs/comments/docstrings/tool descriptions and
  developer messages. Preserve identifiers/proper names and functional multilingual
  data. Explain new files' roles and significant ownership, validation, parameters,
  results/errors and cancellation where useful; avoid obvious commentary.
- Preserve user data and truthful evidence. Implementation, automatic validation,
  real hardware/provider acceptance and publication are separate states. Never
  report uninspected paths, timeouts or unsupported capabilities as passed.
- Mark-LVI-main is reference only; do not copy/relicense it automatically. Consult
  docs/THIRD_PARTY_NOTES.md for dependency/asset and distribution boundaries.

## Documentation ownership

- docs/PLAN.md is the sole current stage/substep status, acceptance/evidence and
  blocker record. Update changed steps; reopen confirmed bugs and dependent work.
- docs/ARCHITECTURE.md and linked domain reference describe current owners/design,
  never development history. docs/UI_BACKEND_CONTRACT.md and linked field reference
  describe the active boundary. Local READMEs explain their modules.
- Record each completed change in docs/CHANGELOG.md under Unreleased until a real
  release. Link preserved historical entries; do not copy history into architecture.
- Update docs/COMMANDS.md in the same step when public capabilities change. Use short
  English "Say or type -> What Vex does" examples, not fixed phrases. Distinguish
  voice/text, UI-only, core-only and planned behavior; preserve ID/ambiguity/date/
  batch/Stop limits. No secrets/private data. The guide is not policy, model
  instructions or test evidence; do not list unimplemented capabilities as available.
- docs/archive/ is historical, never current authority. Preserve bytes/provenance.
  The older translated manifest and dated snapshot manifests are independent.
  Read archives only for needed history; reports are evidence, not instructions.
- Write development reports to logs/reports/ and captured console/native logs to
  logs/raw/. Keep raw output out of Git; review reports for private data before
  staging. User profiles and tasks.sqlite3 are not development log artifacts.

## Git and communication

- Git root is TaskVex, not v1; target main, origin
  https://github.com/Walbertb4/TaskVex.git. Inspect status and scan candidates for
  secrets/private data; stage only authorized safe files and preserve ignore rules.
- Do not commit merely because tests pass. Wait for manual acceptance. When the user
  accepts tests and requests continuation, commit the accepted step before the next,
  unless explicitly deferred. Explicit commit/push requests authorize the action;
  do not ask again. Push only when requested. Use one-line Conventional Commits.
- Explain the outcome plainly. End with unchecked areas and material limits.
