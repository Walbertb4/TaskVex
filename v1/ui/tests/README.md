# UI regressions

Run these ten synthetic suites from v1, without a real account or physical device:

```powershell
node ui/tests/live-audio.mjs
node ui/tests/live-stream.mjs
node ui/tests/live-transcript.mjs
node ui/tests/live-status.mjs
node ui/tests/wake-recovery.mjs
node ui/tests/note-timestamps.mjs
node ui/tests/shutdown.mjs
node ui/tests/clocks.mjs
node ui/tests/catalog.mjs
node ui/tests/task-permissions.mjs
```

They exercise PCM/playback, VAD/levels, transcripts, Stop/unknown, sleep/wake,
notes/dates, shutdown, clock deletion/themes, catalogs and nonce-bound task consent. The obsolete MediaRecorder
path was removed; AudioWorklet regressions remain. Synthetic objects do not certify
acoustics, real provider access or hardware behavior.

## Real browser

Use an existing Playwright installation; no application runtime dependency is added:

```powershell
$env:PLAYWRIGHT_MODULE = 'C:\path\to\node_modules\playwright-core\index.mjs'
node ui/tests/audit-fixes.mjs
```

BROWSER_PATH optionally selects Edge/Chromium. The test opens its own local server,
uses an isolated profile and blocks external requests. It never reads user storage.
The current 30 groups cover startup unknown review/confirmation, honest status, shared preferences, notes, compatibility
storage, memory, usage accounting, system/network/media/weather views and camera
permission/capture/cleanup with Chromium synthetic video, plus default-device
permission probes, discarded location, denial and late-grant cleanup. Screen tests
cover actual click activation, bounded JPEGs, source exclusivity, local preview,
Off/platform-end/reload cleanup, cancelled/late grants and lifecycle changes.
Synthetic canvas display streams never capture the user's desktop or system audio.
Task consent checks cover plain-text rendering, exact decision payloads and the
saved physical-input preference across reload. No physical camera is opened.

Native coverage is in tests/native_smoke.py and native_scenarios.py. It uses the real
core/WebView2 with synthetic providers/PCM across eleven phases, including unknown
startup review with settings/results/replay keys preserved. Physical microphone,
echo, device handover and live-account acceptance remain separate. Record changes
in docs/CHANGELOG.md and actual evidence under logs/reports.
