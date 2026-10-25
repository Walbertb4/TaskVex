# Phase 1 — Model-independent core completed

This document maintains the historical three tool/215 test coverage of Phase 1 acceptance. Current
Also includes notes.update/delete/initialize/replace with core Stage 3; [note pass
and the current test result](STAGE3_NOTES.md) are recorded separately. Native host in Stage 2
added; The starting limits below do not describe that stage retrospectively.

This document describes the use of the first real instruments and Phase 1 acceptance results.
Core model, note saves/can list and salt without requiring microphone or UI
Can retrieve readable system information. It is not a native application opened to the user yet.

## Running stream

`create_core()` → single registry + local policy + TaskManager → `submit(ToolRequest)`
→ parameter verification → sequence → rebuild verification/permission/cancellation → real tool → result.

`v1/app/bootstrap.py` combines these components. With rotating manager `with`
should be used; The worker is closed on exit. Host as default principal
`local-user` selects and allows open for three local tools. Source `desktop`
should be. Validating these tags is not user authentication;
Future native adapters must reliably create fields themselves.

## Tool contracts

| Tool | arguments | Successful result.data |
|---|---|---|
| notes.add | {text: non-empty text} | {note: {id, text, done}} |
| notes.list | {} | {notes: [{id, text, done}, ...]} |
| system.status | {} | {os, os_release, architecture, logical_cpu_count, cpu_percent, memory_percent} |

Note text is up to 10,000 characters; Only spaces are not accepted. text
is not trimmed, additional parameters are rejected. The ID is generated with the UUID on each new note;
Does not change when rereading. done is initially false; This is the tool update/delete
It is not within the scope of this phase. The same text can be added twice with different request_id.

The note file is located at `get_data_home()/notes.json`. Data of envelope `version: 1`
field becomes `{notes: [...]}`. Each record carries only fields id/text/done;
done must be boolean, IDs must not be empty and must not repeat. invalid
record or unrecognized domain is error `invalid_notes`; The net is not emptied/crushed.
For corrupted JSON [explicit recovery path of the recording layer](STORAGE.md) is valid.

After typing notes.add, it reads the file back and compares the full list. success
The proof includes persisted/read_back and note_id. The pre-write error is FAILED;
If the write is successful but the verification is unsuccessful, UNKNOWN/commit_unverified is returned.
Manager stops new jobs after indefinite task; the same request will not work again.
If cancellation is observed before writing, no recording will be made; recorded/verified pass note
It is not considered deleted by cancellation. Once the physical write has started, the thread is not forcibly interrupted.

system.status uses standard Python `platform` and `os` queries. Logical
If the CPU count is not found, it is null. CPU/RAM usage percentages have not yet been measured
is always null for ; No zero or fake measurements are given. The tool does not write files, the device
does not open, hostname/user does not return name/token. This output is available UI telemetry
It is not payload; The fields will also be mapped when connecting the native adapter.

## Invocation example

This example writes to the actual data directory. For isolated trial, first open TASKVEX_HOME
set to the absolute path of an empty temporary directory; automated tests do this themselves.

```python
from app.bootstrap import create_core
from app.core.contracts import ToolRequest

with create_core() as core:
    task = core.submit(ToolRequest(
        request_id="ilk-not-1", source="desktop", principal="local-user",
        tool="notes.add", arguments={"text": "My first core note"},
    ))
    result = core.wait(task.task_id, timeout=5)
    print(result.to_dict())  # Terminal case and proof of fact verification.
```

request_id duplication prevention is only in the current manager session. Restart the application
resending the same request ID when opened may lead to reinsertion;
No exactly-once or permanent task logging implemented after crash. wait timeout
It doesn't cancel the task and doesn't mean 'no notes saved'.

## Admission results — October 21, 2026

`v1` in `.\.venv\Scripts\python.exe -m pytest -q -W error`:
**215 passed**. `.\.venv\Scripts\python.exe -m pip check`: no dependency issues.
No new dependencies were added. Distribution: 45 contracts, 30 registry, 36 managers,
29 policy, 44 registration/route and 31 real local tool tests.

| Acceptance criteria | Result and test proof |
|---|---|
| Common request/result formats | Pass — test_contracts.py |
| Faulty parameter does not reach handler | Passed — test_tool_registry.py and test_local_tools.py |
| Same tool name silent not crushed | Passed — test_tool_registry.py |
| One request one true note mutation | Passed — 12 simultaneous replay single missions/notes, test_local_tools.py |
| Order, status and cancellation | Pass — test_task_manager.py; real tail annotation and pre-write cancellation also tested |
| If policy is denied, no file will be written | Passed — test_policy.py and true false user/source tests |
| Note recording/listing/reopening | Passed — identity and content preserved in actual temporary JSON file |
| Writing error is not success | Passed — in replace error FAILED/write_failed, old file not changed |
| Corrupt JSON is recovered while preserving the original | Passed — separate .corrupt file, then actual annotation |
| Indefinite record does not auto-repeat | Passed — post-registration read error/mismatch UNKNOWN; new tasks stopped |
| System tool real and read-only | Passed — actual query platform/CPU; unmeasured fields null |
| Process shutdown during recording | Passed — previous record retained; details in STORAGE.md |

Results were obtained on isolated test arrays. Code Source/reference was not imported;
actual user notes were not carried over. Separate event framework/subscription system
not added; The current submit/get/wait/cancel stream is sufficient for this stage.

## Next border

Step 2: Open existing UI with PyWebView native and get first setting/salt read state
connect the flow. Write ownership of UI notes and transfer of legacy {t,d} format
is not automatically inherited; The Stage 0 decision is retained. Note CRUD traversal is on separately
requires a contract. Model/sound, application plugins and GUI layers next
These are the stages. Native window, real hardware, accounts and multi-process writing
It is not part of the acceptance.
