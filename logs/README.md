# Development logs and evidence

| Path | Contents |
|---|---|
| reports/ | Reviewed structured test/build reports, moved byte-for-byte from docs/reports |
| raw/root/ and raw/v1/ | Previous console output, preserving filenames and original source grouping |
| raw/native/run-*/ | Per-run native child-process diagnostics retained after temporary profiles close |

Raw output is ignored by Git and may contain local paths or diagnostic text.
Review structured reports for secrets/private data before committing. Existing
reports are historical evidence, not new test runs or current instructions.
Native reports are written on successful completion; after failure consult that
run's raw logs and do not treat a previous successful report as current evidence.

The four Python acceptance scripts default to logs/reports with script-specific
names; --report still accepts an explicit destination and creates parent folders.
The demo builder records its frozen-app smoke result here as demo-build-smoke.json.
None of these changes moves user data, credentials, the persistent task journal
or the application's in-memory Engine & Skill Log.

To capture pytest output from the repository root without filling the root/v1
directories (PowerShell):

```powershell
New-Item -ItemType Directory -Force logs/raw | Out-Null
& .\v1\.venv\Scripts\python.exe -m pytest v1/tests/test_documentation.py -q 2>&1 | Tee-Object -FilePath logs/raw/documentation-tests.log
```

Capture JS/browser/type-check output in the same directory when needed. Capture
does not start automatically for every tool or application action. Real-account
smoke scripts still need explicit authorization and may incur provider charges.

Historical documents/report payloads retain their original path text. When they
refer to docs/reports/NAME, the same report now lives at logs/reports/NAME. Dated
archive manifests and report bytes were not rewritten to conceal their provenance.
