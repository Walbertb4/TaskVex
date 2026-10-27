# Documentation map

Start with the task, not every document. Use `rg -n '^#{1,4} ' docs/FILE.md` to
find sections, then read the affected section and its linked reference.

| Document | Read when |
|---|---|
| [Plan](PLAN.md) | Now, open limits and current step; sole current progress record |
| [Architecture](ARCHITECTURE.md) | Shared execution, owners and persistence before code changes |
| [Domain architecture](reference/DOMAIN_ARCHITECTURE.md) | Only the domain being changed: notes/clocks/audio/memory, measurements/media/weather or visual permissions |
| [UI/backend contract](UI_BACKEND_CONTRACT.md) | Shared transport/readiness, events and lifecycle for boundary changes |
| [UI domain fields](reference/UI_DATA_FIELDS.md) | Only the affected memory/usage/telemetry/media/weather fields |
| [Commands](COMMANDS.md) | A working public command changes or usage instructions are needed |
| [Changelog](CHANGELOG.md) | Record completed changes or inspect recent history; not startup context |
| [Third-party notes](THIRD_PARTY_NOTES.md) | Dependency, asset, redistribution and license changes |
| [Audit history](AUDIT.md) | Historical maintenance evidence, not current progress |
| [Development logs](../logs/README.md) | Structured reports, ignored console output and capture commands |
| [2026-10-27 snapshot](archive/2026-10-27/README.md) | Exact pre-cleanup files and independent hash manifest |
| [Older translated archive manifest](archive/MANIFEST.json) | Integrity/provenance of the original 133 historical files |

[logs/](../logs/README.md) holds evidence, not rules. Synthetic results do not certify real accounts
or devices. Archives never override current guides; preserve their bytes and read
only for a specific historical question. Local READMEs remain beside modules.
The working command guide remains complete.
