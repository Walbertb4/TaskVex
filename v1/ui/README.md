# TaskVex UI

Vanilla HTML/CSS and ES modules. Run the native host from v1 with
`.\.venv\Scripts\python.exe -m app.main`; see [backend setup](../README.md).

## Browser preview

From v1:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory ui --bind 127.0.0.1
```

Open http://127.0.0.1:8000 in Edge/Chrome. ES modules should not use file://.
Standalone mode supports local preferences/layout, notes, skill/routine editors,
backup, palette and a local clock. It does not gain native conversation, backend
notes, multiple native clocks, Windows Credentials or local KWS. Unavailable web
fonts fall back to system fonts.

## Module ownership

| Module | Responsibility |
|---|---|
| app.js | Startup, module connections and validated snapshots |
| assistant_session.js | One conversation/microphone/sleep/Stop lifecycle |
| shell.js | Message bubbles, startup/shutdown visuals and clock |
| api.js | Transport/bridge, acceptance versus completion, safe errors |
| schema.js / storage.js | Pure validation / localStorage with visible failures |
| preferences.js / settings.js | One preference object, profile, backup and native save |
| devices.js / layout.js | Shared-preference device selection and widget layout |
| credentials.js | Secret-free key-status UI and explicit credential storage |
| notes.js | Local or approved backend note ownership; no double mutation |
| skills.js / routines.js | Local definition editors; no backend execution |
| connections.js | Live catalog and compatibility display setters |
| system_view.js / media_view.js | Shared native snapshots via the existing app tick |
| panels.js | Modals, command palette, drawer and local timeline |
| reactor.js / sfx.js | Visual states/animation and local effects |
| live_mic.js / pcm_worklet.js | One AudioWorklet PCM source, VAD and level |
| live_audio.js / live_transcript.js | Request-scoped playback and transcript rendering |
| clocks.js / timers.js | Native multi-clock view / separate standalone fallback |

After native initialization, bridge loss cannot create a second note/clock owner.
Setters never send a second backend save/command. Planned Google/location/camera/
screen/media-control integrations remain disabled; saved definitions/text are preserved.
Media metadata is already read-only; it does not authorize playback controls.

[Contract](../../docs/UI_BACKEND_CONTRACT.md), [commands](../../docs/COMMANDS.md),
[tests](tests/README.md), [audit](../../docs/AUDIT.md).
