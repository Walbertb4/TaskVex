# TaskVex

TaskVex is an early-stage Windows desktop assistant built with Python,
PyWebView/WebView2 and a vanilla JavaScript interface. It uses Google's Gemini
API for conversation; the main desktop path is Gemini Live.

The project focuses on connecting natural-language requests to a small set of
validated local tools. The model selects tools, while the application validates
arguments, checks permissions, queues execution and reports verified results.
It is a development project, not a production-ready general computer-use agent.

## Implemented

- Live voice and text conversation, streamed transcripts and audio replies.
- Microphone input control, playback mute, Stop and interruption handling.
- Local wake-word detection, one-time sleep, return-to-sleep mode and an idle timer.
- Temporary conversation context held in memory.
- Personal memory edited in Personalization or through explicit model commands, with opt-in before
  sending it to the model; correction and deletion drop the old chat context.
- Optional conversation-derived memory, with a saved choice between asking first
  and automatic verified saving. Pending facts can be saved/dismissed beside the
  conversation controls or through a later spoken/typed decision; proposals are
  not treated as saved facts before approval.
- Backend notes with stable IDs and timestamps: add, list, edit, complete and
  delete, including structured selection and atomic batch deletion/completion.
- Multiple timers and stopwatches shared between the UI and model tools.
- Periodic local CPU/RAM, runtime-volume disk usage, battery and foreground
  executable readings shared by the UI and system.status tool. Initial or
  unavailable readings are not replaced with invented numbers.
- Passive physical network receive/send rates and link/Wi-Fi connected status
  shared with system.status. This is not a speed test or proof of internet access;
  local IPv4 gateway ping and location-free Wi-Fi signal quality are available
  when Windows exposes them. These are not internet/API latency measurements.
- Saved interface preferences, Live voice selection and separate reply volume,
  plus a limited set of active personalization fields.
- Gemini API key storage in Windows Credential Manager and automatic Live model
  catalog loading. The saved selection is restored when returned by the API.
- GPU utilization through Windows performance counters across supported vendors;
  the dashboard shows the busiest engine/adapter. No vendor command is run.
  GPU/CPU temperatures and VRAM capacity remain unavailable from this source.
- A per-data-profile OS lock prevents a second native app instance from opening.
- An application-session token total from reported Live/REST usage, including
  REST tool rounds and separately requested speech synthesis. It survives Stop,
  Disconnect and model changes; restarting the app resets it. Missing usage
  marks the total incomplete. It is not account quota or a billing guarantee.

A small allowlisted application plugin exists in the core. The conversational
model currently sees its catalog, not unrestricted app-launch or desktop control.
Skill and routine editors store definitions locally; they do not execute them yet.
A separate REST adapter remains available for development and future channels.

## Not implemented yet

Google Drive/Calendar/mail access, Telegram/Discord integration,
general GUI automation and
backend skill/routine scheduling are planned.
Camera, screen inspection, location, weather and media controls are not connected.
Intel/AMD GPU monitoring, CPU temperature and Wi-Fi/network monitoring are not implemented. CPU sampling
currently supports Windows processor groups with at most 64 logical processors;
unsupported readings remain unavailable.
Some saved legacy profile fields have no backend effect and are marked as planned.

## Run from source

Windows, Python 3.11+ and the Microsoft Edge WebView2 Runtime are required.
The tested development interpreter is Python 3.14. From the repository root:

```powershell
cd v1
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m app.main
```

For an existing environment, skip its creation and dependency installation.
Add `--debug` for development tools. Set the Gemini API key in Settings; access
requires an eligible account, available quota and network connectivity. API usage
may incur charges. No credentials are included in this repository.

Local wake detection requires a separate, explicit model download. Setup, data
locations and test commands are in [the development guide](v1/README.md).
The dependency snapshot reproduces the tested development environment; it is
not a cross-platform, hash-locked release installer.

## Data and current limits

Active conversation input and model tool results are sent to Google. During
sleep, wake detection processes microphone audio locally. This is not a fully
offline assistant. API keys use Windows Credential Manager; notes and settings
are local files. Skill/routine definitions use browser storage. Timers and
conversation context do not survive application exit. User-edited personal memory
is saved separately in the profile and sent to the model only when explicitly enabled.

Native tool requests and results are kept in a local SQLite journal. Reusing
the same request ID does not run the action again, including after restart.
The 256-record limit bounds active work and RAM records, rather than lifetime
usage; historical records stay on disk. Unknown outcomes block new tools and
currently require manual investigation; there is no reconciliation UI yet.
The journal is not encrypted, can retain deleted note content and proposed
personal facts/source messages even after profile memory is cleared, and grows with
usage. It is not an exactly-once guarantee for external services. Native and
core ownership locks reject a second worker sharing the same data profile.

There are no general latency, memory-footprint or acoustic-accuracy guarantees.
Model availability, network conditions and hardware affect behavior.

## Verification and documentation

The latest gateway/Wi-Fi quality change passed 1,154 Python tests, 9 JavaScript
suites, 15 browser groups, 10 native phases and targeted type checking using
temporary profiles and synthetic providers. A local gateway echo and Windows
Wi-Fi quality query also succeeded on the development machine.
[Test evidence](docs/reports/network-quality-checks.json).

Manual acceptance of this quality slice is pending; preceding local traffic,
GPU dashboard, memory decisions and session token counting were reported working.
These checks do not establish real-account availability, physical microphone
accuracy, support for every adapter/Windows version or production readiness.
Gateway ping is not internet/API latency. The API latency field remains unavailable
until a real transport metric is defined.

- [Architecture](docs/ARCHITECTURE.md): current ownership and planned boundaries.
- [Plan](docs/PLAN.md): remaining work and acceptance status.
- [Changelog](docs/CHANGELOG.md): recorded changes.
- [Commands](docs/COMMANDS.md): implemented user-facing requests and limits.
- [UI/backend contract](docs/UI_BACKEND_CONTRACT.md) and [audit](docs/AUDIT.md).
- [UI preview and modules](v1/ui/README.md).

## License

Original TaskVex contributions are [MIT licensed](LICENSE). This does not
relicense dependencies, existing UI assets or downloaded model weights.
See [third-party notes](docs/THIRD_PARTY_NOTES.md); asset provenance and release
packaging review remain open.
