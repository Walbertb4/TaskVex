# Stage 4 — First app plugin

This document explains how to convert TaskVex from note tools to a real Windows application.
It tells you that it will expand. The first target is just Notepad. The plugin is a separate
It is not a task system; open registered tools same registry/policy/TaskManager
It works from the line. No mockups or a new UI panel required yet.

## Step by step plan and acceptance

| Step | Job to be done | How will we know when it's over? | Status |
|---|---|---|---|
| 1 — Catalog and identity | apps.catalog without parameters; fixed notepad id and explicit apps.read permission | The actual core line returns only authorized catalog information; command/path does not take; does not write files | Completed |
| 2 — Windows status monitoring | apps.status({app_id:"notepad"}); monitor process and window status with reliable Windows adapter | Closed/open/unobservable states are divided into; window title alone is not an identity | Completed; real Windows closed/open passed observation |
| 3 — Verified open | apps.open({app_id:"notepad"}); supported startup method chosen by the host | After initialization, the target is observed again; initiation acceptance alone is not success | Completed; real closed to on passed |
| 4 — Error, repetition and cancellation | Registry/policy, current open application, initialization error, delay, cancellation, timeout and replay scenarios | In uncertainty, the second process does not open automatically; no fallback to unsupported target | Completed with controlled tests |
| 5 — True Windows adoption | Open Notepad/status over core in isolated trial; close/open and call again | The proven level of process/window is reported; test clears only the empty window it has | Completed; the user confirmed two actual rounds of opening by closing all windows; two reports checked |

It is intentional that the second step comes before opening: learning how to observe the target.
We should not say "opened" without knowing it. With Modern Notepad's launcher process
actual window owner may differ; Installed when Windows adapter is applied
version reviewed on real machine; modern Microsoft.WindowsNotepad suite
The launcher and window owner processes could be different. Observation distinguishes these.

## The first step is the employee agreement

`app/tools/local/apps.py` maintains the built-in permission catalog. Today's recording:
`notepad -> Notepad`. `create_core()` registers the parameterless apps.catalog tool.
The request, like other tools, uses source=desktop and the principal of the trusted host.
carries The tool requires `apps.read`; opening new authorization note reading/writing or application
It is not the authority. apps.status is also registered with the same apps.read permission;
apps.open also requires apps.launch permission; It is not enough to open apps.read alone.

```python
from app.bootstrap import create_core
from app.core.contracts import ToolRequest

with create_core() as core:
    task = core.submit(ToolRequest(
        request_id="apps-catalog-1", source="desktop", principal="local-user",
        tool="apps.catalog", arguments={},
    ))
    result = core.wait(task.task_id, timeout=3)
    print(result.result.to_dict())
```

Successful data: `{"apps":[{"id":"notepad","name":"Notepad"}]}`.
Proof: `{"source":"builtin_allowlist"}`. verified=True only this catalog
It means that the reading is confirmed. "Notepad is installed", "running", or
It does not mean "window ready". The list is new with each call; result outside
The change cannot change the catalogue. Application scan/startup is not done at startup.

## Second step — Condition observation contract

`apps.status` only receives `{"app_id":"notepad"}`. Registry parameters,
policy controls the user/resource/apps.read permission. apps.py common tool
manages the result, windows_apps.py narrow Win32 observation. There are no new dependencies;
The ctypes standard library is used. Windows DLL is not loaded when installing Core.

Result data fields:

| Area | Meaning |
|---|---|
| app_id | Fixed notepad id |
| running | true if there is a verified process; false if not in full observation; null in missing negative observation |
| visible_window | true if the verified process has a WS_VISIBLE top-level window; false if not in full observation; null in missing negative observation |
| processes | Verified processes with pid, identity and created (Win32 creation time text) |
| windows | Observed windows containing hwnd, pid, minimized |
| complete | Is the observation complete? |
| observed_at | UTC instant observation time |

The fully closed observation is also SUCCEEDED/verified=True: the query is successfully executed.
means completed; It does not mean that the application is open. partial scan
Returns FAILED/observation_incomplete, positive findings in the data may remain.
Read-only error does not stop the manager with UNKNOWN. Native API/platform
If it cannot be used, the data is not fitted; FAILED/observation_unavailable or
It comes from platform_unsupported. Cancellation is observed between scan process/window.

Authentication: only to notepad.exe candidates in the current Windows session
PROCESS_QUERY_LIMITED_INFORMATION and SYNCHRONIZE access are requested for the zero-time life check. operating system package
family should be Microsoft.WindowsNotepad_8wekyb3d8bbwe and image name should be Notepad.exe;
The classic version is from the allowed system paths in the directory declared by Windows.
should be in one. EXE of the same name in the user directory is not accepted. title,
The document content or executable path is not put into the result/log payload. Process title
evaluated by OS ID, not by match; It is not an antivirus/signature audit.

Windows are read with EnumWindows and PID mapping. Then the process ID and
The formation time is compared again; If the process is terminated with WaitForSingleObject(handle,0), it is not considered alive; Old HWND if PID reused
it follows from the conclusion and the observation becomes incomplete. created count JS integer limit
The text is moved because it may exceed All opened process/snapshot handles
It is closed with finally. The callback exception is not escaped out of the C boundary.

WS_VISIBLE is not a real preliminary plan/interaction ready guarantee; scaled down
or the window on another virtual desktop may carry this flag. Other Windows
Sessions are excluded, windows are observed on the current desktop. This result is instantaneous
is the image; must be rechecked before the next launch/GUI action.

## Limits of next steps

- app_id will be selected only from the built-in catalog; user/model executable,
  The shell will not be able to give command line or arbitrary arguments. Opening a document is not available in this first slice.
- Process observation and visible window observation will be separate evidence. Title
  match will not be enough to count another application as Notepad. like PID/HWND
  identities belong to the moment of observation; We do not use the old result as a permanent live state.
- If there is already a verified window, no new launch will be made. Process var/window
  Otherwise, the current opening is waited. Timeout after startup, "never turned on"
  is not; There is no automatic second opening.
- No new dependency or plugin scanning framework was added to the first step. Before
  The required narrow adapter will be applied with the standard Windows/Python facilities.
- Initial plugin acceptance can be done via call test/command. binding UI/model
  This is the separate intake job on the tools; today's native bridge general tool
  not extended to execution API.

## Test result — October 21, 2026

`.\.venv\Scripts\python.exe -m pytest -q -W error`: **396 tests passed**.
The apps/Win32/policy suite in the previous state observation slice was 77 tests.
test_apps.py common core, permission,
parameter, error and cancellation; test_windows_apps.py packet/system path ID,
handle shutdown, access denial, another session, PID reuse, and
C verifies callback error/cancellation. Low level ABI tests non-Windows
jumps on the platform; Other platforms are not really tested.

[Actual Windows result](stage4-status-windows.json): first before opening the application
core query returned running=false/visible_window=false. blank for checking
Notepad was opened from outside with the TaskVex-Status-Test.txt file; apps.status
Microsoft correctly mapped the processes and window owner to the package ID. in the product
In this historical status acceptance, initialization was only a test setup; new below
Apps.open acceptance was actually run through the product tool.
The terminal output of the first closed call was also stored in the report.

Notepad brought back the old session tabs. The content has not been changed; alone
The test file tab was closed, the returning user tabs were left untouched.
Attempt to close window after test, Computer Use user input
It was not implemented because he perceived it; after_test_tab_close still open status in report
shows. This result was not counted as a closed test. Real minimize/another session and
classic Windows Notepad testing was not performed; these are limited to controlled API tests.
Catalog support is not installation detection on the computer; apps.status is also installed
but it does not guarantee to distinguish the closed application from the non-installed application.

Technical resources: Microsoft's [process snapshot](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot),
[image query](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew),
[packet family](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagefamilyname),
[window observation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows)
and [occurrence time](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)
and [life control](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject) contracts were checked during execution.

## Step three — Verified open

apps.open gets only `{app_id:"notepad"}`; Same narrow input scheme as status
is used. ToolSpec declares the source of apps.read + apps.launch and apps.notepad.
Policy requests both, trusted local host explicitly grants it. new dispatcher,
No plugin scanning, UI panels or dependencies added.

First, the full observation is taken with the apps.status business logic. Missing/incorrect monitoring trip
not tried. If there is a verified window, success/already_open=true and
launch_requested=false. Up to 5 seconds window if there is only one process
is expected; The second initialization is not performed. If it is verified that there are no processes at startup
GetSystemDirectoryW resolves the fixed notepad.exe path; target from PATH/env/cwd
not called, user/model cannot send file/command/argument.

Startup is communicated to Windows once via os.startfile. This is based on ShellExecute
is the standard library method; cmd/PowerShell command is not executed. startfile
Its return is not proof of completion. The application exits as pending/killing.
Popen owner is not created; external application may outlive TaskVex. Then
The target is verified with the same OS packet/system path ID and window observation.

Success data in addition to status snapshot launch_requested and already_open
carries. The proof has window_observed=true. Warranty is valid only in verified process.
WS_VISIBLE is the window presence; bring forward, unminimize, blank document
or interaction readiness is not a guarantee. another user at the same time
An OS mechanism that atomicly locks application launch has not been established.

Launcher not found / startup observation error is FAILED while there are no side effects yet.
Once the initialization call is entered, the exception, timeout, or cancellation is UNKNOWN;
The application may actually have been opened. Manager stops new jobs and runs the same
request_id returns the old result. There is no automatic second start or kill.
timeout FAILED/window_not_observed while waiting for window in previously running process
cancel is CANCELLED because this task has not been initialized. Local wait limit
is 5 seconds; It does not forcibly interrupt the Windows launcher's own call duration.

Tests: test_app_open.py; already open target, delayed window, process var/window
none, first observation error, initializer error, post-call error, cancellation limits,
After 12 simultaneous identical requests/replay and UNKNOWN tried to stop the new job.
test_windows_apps.py also system path solution and user command/argument
Checked for non-native start call. These controlled limit tests are physical
It does not mean that Windows permission error is created.

## Real apps.open acceptance

It is operated voluntarily in `v1`; You can open Notepad and restore the old session.
can bring. Does not automatically close user tabs:

```powershell
.\.venv\Scripts\python.exe tests/apps_open_smoke.py --report ../docs/stage4-open-windows.json
```

[Actual result](stage4-open-windows.json): first observation with temporary TASKVEX_HOME
it was closed. The product apps.open tool only made **1 actual start call**; period
and the window is authenticated. The same task returned with the same request_id iteration;
second apps.open with new request_id used existing window and second start
There was no call. Initialization/observation is not emulated; only by hugging the number of calls
was measured. After the test, the application was left open and user tabs were left untouched.

The final real acceptance was completed with the following user testing. UI/model entry to tools
attachment is not an acceptance of this stage; native bridge general tool operation
Its API is not opened. Solkme/restart there is no persistent request logging after startup.

### 21 October — Type inspection and subsequent acceptance control

Fixed the source of three Pylance issues in the screenshots: bridge window
Identified as `Window | None`; accessing and creating a window that does not exist
Failure gives a clear error. Save payload object before setting verification
should be. `System` is a .NET namespace generated at runtime by pythonnet
is the area; It is loaded with `import_module` and Invoke to WinForms GUI thread is maintained.
No stimulus suppression or new production dependencies added.

Using venv Python for `app/main.py` and `app/bridge/webview_bridge.py`
Pyright result: 0 errors, 0 warnings. Pytest: **397 passed**. If the window cannot be created
Added test to verify that the GUI does not start and the worker closes.
[The actual WebView2 report](stage4-typefix-native-smoke.json) passed eight scenarios;
on_top, F11, save/reload including loading, shutdown and error data protection.
The windows for this test are hidden; export file selection is provided by the test.

With Computer Use, go to File → New window without touching the existing personal window.
A separate Untitled window has been created. Its only tab was unchanged and 0 characters.
Closing could not be verified after the first Alt+F4; Close the window again
button was used. There was no test window in the next window list, personal
The window was standing. Then try the real core apps.open/replay
[passed successfully](stage4-after-blank-close-windows.json): current target used,
new start count was 0. This will close all Notepad processes and open the new process.
It is not an opening test. Evidence of actual opening from previous closed is in separate report;
all closed at the time of this trial → reopen acceptance was still on; following
user testing closed this item.

### Closing and reopening acceptance with user — completed

The user closes all Notepad windows, preserving any open work.
ran the smoke script; then turned it off again and started it a second time and
He reported that the test passed. [First trip](stage4-manual-first.json) and
[reopen](stage4-manual-reopen.json) reports also read and checked:
running=false/visible_window=false, launch_count=1, on both startups
fresh_launch_checked=true, replay_same_task=true and second_request_reused_window=true.
The opened target was verified with verified=true and visible window in both rounds.
The shutdown was made by the user; script did not implement shutdown/kill. Two rounds apart
are core processes; The guarantee of permanent inter-process replay is not considered tested.

The five planned steps of Phase 4 have been completed. Model connection is included in Stage 5.

Additional reference: Python's [os.startfile](https://docs.python.org/3/library/os.html#os.startfile)
and Microsoft'un [GetSystemDirectoryW](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getsystemdirectoryw)
Checked when choosing the method of initiating contracts.
