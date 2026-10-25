# Phase 2 — Plan, first native slice and manual testing

This document explains the steps to run the ready-made HTML interface as a Windows application.
explains. The functional native steps and automatic acceptance of Stage 2 are ready.
Visible window and actual file dialog acceptance were also later introduced by Computer Use.
completed: [visible acceptance](STAGE3_VISIBLE_ACCEPTANCE.md). It is not a human UX/voice test.
The transfer of Core annotation tools to the UI was implemented in Phase 3; first native in this document
acceptance is the historical Stage 2 limit. Current ownership, eight-process native acceptance
result [STAGE3_NOTES.md](STAGE3_NOTES.md), current 332 test and catalog steps
[Located in STAGE4_APPS.md](STAGE4_APPS.md).

## Application order and status

| Row | Business | Status / acceptance criteria |
|---|---|---|
| 1 | Opening native host and ES modules | Ready; app.main opens current index.html with PyWebView/EdgeChromium |
| 2 | ui_ready and safe UI notification | Ready; true native two-way delivery, idempotent ready declaration, initApp return verified |
| 3 | Settings file and startup snapshot | Completed; registration/reinstallation, corrupt registration/confirmed repair and version rejection confirmed |
| 4 | Read-only status and honest offline | Ready; system.status goes through the common core line; when there is no model MODEL OFFLINE |
| 5 | Lifecycle and error experience | X/Shutdown, F11, Restart app, interface reset and always-on-top connected. Startup warning, Retry and confirmed setting repair ready |
| 6 | Final acceptance | Automatic acceptance passed. Visible window, actual export/import dialogs, cancel and restart later completed with Computer Use; visual appearance observed, no pixel uniformity testing |

No new framework or dynamic plugin system has been added. PyWebView 6.2.1 and its
transport/.NET dependencies installed; Updated pyproject and development lock.
The starting code is app/main.py, the bridge is in app/bridge/webview_bridge.py.

## Run immediately

Open PowerShell and run:

```powershell
cd C:\Users\batue\OneDrive\Desktop\TaskVex\v1
.\.venv\Scripts\python.exe -m app.main
```

A TaskVex window should open. It is not necessary to activate Venv with Activate.ps1.
If the first installation is done on another computer, first install it in this Python environment.
`python -m pip install -r requirements-dev.lock.txt` should be applied. Native engine
Requires Windows Edge/WebView2 Runtime; It does not downgrade to the old Internet Explorer engine.

If you want to test it separately from the actual settings, first in the same PowerShell:

```powershell
$env:TASKVEX_HOME = Join-Path $env:TEMP 'TaskVex-manual-test'
.\.venv\Scripts\python.exe -m app.main
```

This directory should remain the same in the reopening test. To return to the normal data directory
run `Remove-Item Env:TASKVEX_HOME` after closing the application. this alone
removes the environment variable; It does not delete test files.

## Manual admission control

1. When the window opens, check that the view is in place and that the operating system is displayed under System.
   Check that it appears and that it says "Native bridge ready" in the Skill Log.
2. MODEL OFFLINE is the expected situation. CPU/GPU/RAM percentages are also `—`
   is expected; Percentage of usage is not measured yet. The empty listing model/audio is correct.
3. Change the theme color in Settings and press the Save button. From within Profile
   Write a preference text and press Save profile. Open Save buttons Python record
   awaits approval; In a rejected record, the modal remains open and an error appears in the log.
4. Close the window with the upper right X. Reopen with the same command; theme and profile back
   must come. Closing the application process in the terminal is also part of this control.
5. Add native UI note and reopen; It should be preserved in the localStorage of the native profile.
   This is not a Phase 1 export to notes.json. The general setting record does not add notes.
6. Success in unsupported backend operations such as chat, camera or Google
   waiting; not_implemented appears in the log. The Skill/routine designation remains local;
   Running them natively is not yet connected.

Use X or Shutdown for normal closing; native Shutdown Restart screen
does not pass, closes the application. F11 goes to full screen, F11 goes back again.
New after closing Restart app worker/window in Settings > System
requires implementation process; The same data directory and debug preference are preserved. always on top
instant applied to the actual window; It becomes permanent with save. Reset interface preferences
After confirmation, it only resets the interface preferences; not/skill/routine, profile, device
and connection preferences are preserved. If there is an error during reset, previous data will not be deleted.

In profile New/clean, the default theme is purple (#a78bfa); The registered theme is preserved.
Reactor also targets 60 FPS at idle. Native WebView2 autoplay setting
removes click waiting; If the SFX preference is off, no sound will play. physical speaker
His output was not verified by further listening.

`python -m app.main --debug` is available for developer tools. opened
`await window.pywebview.api.event('system_status')` real read-only on console
gives the result. Double-clicking the source HTML does not launch the native application.

## Record and trust limits

The default data directory is `%LOCALAPPDATA%\TaskVex`, if you have TASKVEX_HOME open:

- settings.json: theme, colors, profile, layout, SFX, sound/device/model preferences.
- webview/: native browser profile and localStorage for this application.
- notes.json: Phase 1 core notes tool data; The UI does not use this file yet.

notes/skills/routines and top-level API key fields in save backend
The setting is not recorded. Internal fields are also whitelisted; e.g. conn.apikey is rejected.
This file is not a credential vault; Secrets should not be written in the free text of the profile.
Corrupt settings file will not be auto-deleted or crushed with empty default; start
warning appears and backend save is rejected. Retry the file again without changing it
tries. Back up and repair settings require explicit confirmation, the actual bytes are unique
Moves to settings.json.<identity>.corrupt, preserving valid fields
repairs settings. If corrupt JSON cannot be read, the preferences revert to default; native UI
not/skill/routine/profile and core notes.json is not deleted. Backup is not deleted.

Using a compatible application on an unsupported version may result in permissions being denied in case of access error.
control is requested; In these two cases the repair button is hidden and the file is protected.
Error Backup/write is not considered a success. If a new file cannot be written after repair
Even the original backup created is kept. If the window cannot be opened at all, terminal and Windows
The error box redirects to path setup/WebView2/data; There is no automatic reset.

ui_ready only accepts {version:'1.0'}. Does not include snapshot collections;
The current UI contract that preserves missing fields preserves native not/skill/routines.
initApp/loadStore now returns the application result as boolean.
Only JSON-serialized arguments are sent to UI methods with fixed permissions.
The only public Python method is event; No raw eval or direct file API opening.

The successful save response is `{ok:true,completed:true,saved:true}`; file back
is verified by reading. Error/incomplete is not considered a confirmation success. Automatic tuning records
shipped in a single order with independent copies; Save, Export and Import await approval.
Registration status appears on the Setting/profile panels. 12 second wait limit is real
does not cancel or resubmit the request; A late response cannot crush the newer record.
Import native does not change collections before setting confirmation. More local writing
If it fails then the previous UI/localStorage is retained, native settings may be new;
This partial status is shown as open in log and recording status. Inter-store atomicity
There is no claim. The source backup file is not deleted.
onTop now also applies to the physical window; save device preference real
microphone/camera does not log in.

Run a single application instance for now. native HTTP for persistent localStorage
origin is kept constant (PyWebView's default port 42001); port conflict/lot
application sample support will be discussed separately. Local server only UI directory
presents. If external Google Fonts cannot be loaded, the current system font fallback applies.

## Automatic verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q -W error
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe tests/native_smoke.py
```

267 pytest checks passed; dependency check is clean. Fake-window bridge tests
It was not counted in place of the real native test. native_smoke.py runs the real EdgeChromium engine
production ran through main() in seven separate processes: save, reopen,
registration/import/export, export cancellation, corrupt JSON, invalid field and unsupported
version. Windows is hidden in testing;
The user does not use profile/data.

Evidence: [real native results](stage2-native-smoke.json),
[browser not/setting regression](stage2-browser-regression.json). In native testing
modules, single exposed event, offline status, real OS information, snapshot no-echo,
Save button, reopen, local note preservation, corrupt save rejection and save
In the error, the modal remained open. Browser regression fallback and simulated
Note for native transport adding/completing/deleting confirmed no-echo and explicit Save.

Latest windows update: [true purple theme/sound policy/F11/Shutdown test](stage2-window-controls.json).
F11 was also checked when input focused and on pressed key repeat; Shutdown is real
Reached window closed event and worker closure. [Reactor timing test](reactor-60fps-check.json)
Four oscillators at 60 draws per second and boot synthesis at 60/90/120/144 Hz clocks
confirmed that it was produced. This last test is not a physical FPS or speaker measurement.

[Lifecycle native test](stage2-lifecycle-smoke.json): real WinForms
Changing TopMost and loading it on restart, reset not/skill/routine/profile
and verified connections protection, reset write error, and native Restart shutdown.
Restart process opening call was caught in testing; successive real native process testing
runner started. This will automatically respawn visible on the user's desktop
It is not part of the test. The first native attempt is to the TopMost setter outside the GUI thread.
stuck; It passed again after the Invoke fix. Test timeout Windows venv
Fixed it to clear its own process tree, including its launcher.

[Start/recovery native proof](stage2-startup-recovery.json): alert view,
preservation of the original file in case of repair cancellation, confirmation, exact backup, valid fields
protection and return to a no-echo ready state has passed. Local notes in three error scenarios
preserved; skill/routine/profile in repair was also compared. Repair in new version
It was hidden and the file was not changed. Windows fatal startup error box in unit testing
imitated; Manual interaction with the actual box was not attempted. First test run
After fixing the missing test import, all pytest checks passed.

[Latest registration/import/export native acceptance](stage2-persistence-smoke.json) and
[browser backup check](stage2-persistence-browser.json): queue queue and
data copies, observer not being able to modify the send, actual FileReader import,
native pre-reject UI protection, UI rollback on localStorage quota error, partial
notification of success, single post at 12 second timeout and actual WebView2
Blob export file verified. Native file selection result is simulated in the test
written to temporary test file only; physical dialogue was not used manually. Export
Upon cancellation, the old file did not change. Second synthetic download attempt on the same page
Because it was waiting, the cancellation test was separated into a separate native opening; This is physical succession
It does not mean that clicks are manually verified.

Retry recipe (visible turn is now complete): Select a file with Settings > System > Export and save; same file
Select with import. The registration status should confirm success and the content of not/skill/routine should be returned.
must come. Also check that no files are produced by selecting Cancel in Export. test
Doing so with isolated TASKVEX_HOME prevents applying a backup on top of the real data.

Visible windows and dialogue were not attempted in this historical hidden turn; appears later
Acceptance also completed. Pixel comparison, real camera/sound, Google,
Model and hardware check has not been attempted. Windows console coding in native test runner
Fixed initial report printing error due to; Restart completed successfully.

Technical reference: [PyWebView API](https://pywebview.flowrl.com/api/) and
[Windows engine](https://pywebview.flowrl.com/guide/web_engine). Local HTTP,
storage_path/private_mode and Edge Runtime selections are based on these APIs.
In-process autoplay argument for audio: [WebView2 browser flags](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/webview-features-flags).
