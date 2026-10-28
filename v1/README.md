# TaskVex v1 — development and operation

This guide explains running the current app, not progress history.
See the [architecture](../docs/ARCHITECTURE.md), [plan](../docs/PLAN.md) and
[UI/backend contract](../docs/UI_BACKEND_CONTRACT.md).

## Environment

Windows, WebView2 and Python are required. The declared Python minimum is 3.11;
the tested interpreter is 3.14. Run from v1:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m app.main
```

Reuse an existing .venv. Activation is optional; direct interpreter invocation
requires no PowerShell execution-policy change. Add --debug for developer tools.
Enter your own key in Settings. The Live catalog loads automatically and restores
a saved model if the API still lists it. Storage success does not guarantee access.

pyproject.toml declares dependencies; requirements-dev.lock.txt snapshots the tested
runtime/development environment, not a cross-platform hash-locked release. Recreate
that lock from a controlled environment after dependency changes. .venv is local
and ignored by Git. Do not install the reference project's requirements here.

## Local wake model

Explicit optional setup, requiring internet:

```powershell
.\.venv\Scripts\python.exe -m app.session.wake_word --setup
```

Startup never silently downloads weights. Setup verifies a pinned upstream hash
and places the model outside the repo in the data root. Supported wake spellings
include the Vex/Veks/Rex family and supported English dictionary words. Weight
redistribution licensing remains open: [third-party notes](../docs/THIRD_PARTY_NOTES.md).

## Data

Default profile: %LOCALAPPDATA%\TaskVex; set an absolute TASKVEX_HOME for isolation.
settings.json holds allowed preferences, notes.json backend notes, and Windows
Credentials the key. Skills/routines use localStorage; clocks/chat context use RAM.
Profile OS locks prevent a second native app or persistent core worker on the same
profile. Distinct profiles are independent; direct scripts must respect ownership.

The unencrypted tasks/tasks.sqlite3 schema-3 journal retains IDs/status and request
fingerprints, not note/message/file/proposal contents. Disk reads explicitly lack
historical payloads; bounded current RAM results remain available. Logical restart
metadata also remains content-free; host Continue requires fresh replanning and
restores no scopes/targets. The public task UI is not connected. Schemas 1/2 migrate
before execution without losing replay keys or UNKNOWN review; older builds cannot
open migrated profiles. External backups/provider history are not erased.
The 256-record limit bounds active work/RAM, not
lifetime tasks. Unknown outcomes still block new tools after restart. The journal
is not part of JSON backup; deleting it removes replay protection and is not recovery.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tests/native_smoke.py --report ../logs/reports/english-native.json
```

Native checks require Windows/WebView2 and use temporary profiles plus synthetic
HTTP/WebSocket/audio. They do not use real notes or paid APIs. See [UI tests](ui/tests/README.md).
Separate live-account smoke scripts can incur costs and are not general regression.
For a portable Windows demo, see [packaging](tools/README.md).
