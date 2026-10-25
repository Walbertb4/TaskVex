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
- Title, artist and playback state from the current Windows media session, with
  play/pause/previous/next shared by dashboard buttons and model tools. Control
  success requires observed state/track changes; unsupported actions stay disabled.
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
Camera, screen inspection, location and weather are not connected.
CPU/GPU temperature and VRAM capacity are not available from the current sources.
CPU sampling currently supports Windows processor groups with at most 64 logical processors;
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

## Windows demo build

A portable Windows x64 development demo can be built with
[the packaging guide](v1/tools/README.md). Extract the complete ZIP and open
`TaskVexDemo.exe`; Python is bundled. Windows 10/11 x64, .NET Framework 4.8
or newer 4.x, and Microsoft Edge WebView2 Runtime are required. Standard Windows
11 includes the latter two components; modified installations can differ.

The unsigned demo uses `%LOCALAPPDATA%/TaskVexDemo` by default, separately from
the source application's profile. No developer key, notes or personal settings
are bundled. Supply your own Gemini key. Wake-model weights are not distributed;
the optional `Setup wake model.cmd` invokes the existing verified upstream setup.

The actual EXE passed startup checks and a second check after extracting its ZIP
to a different directory, without Python environment variables or a model key.
[Build evidence](docs/reports/demo-build-checks.json). This is not clean-machine,
microphone, real-account or all-hardware certification. No signed installer or
GitHub binary release is provided by the source repository.

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

The media-control slice passed 1,191 Python tests, 9 JavaScript suites,
18 browser groups, 10 sequential native phases, type checking and dependency checks
using temporary profiles and synthetic providers. Native UI buttons reached the
same core as both model transports; no real player was mutated during these tests.
[Media evidence](docs/reports/media-control-checks.json).

Manual testing then exposed false stale-target rejection from recreating Windows
media managers. The manager-identity fix passed 1,196 Python tests and a real
read-only identity/cancelled-preflight check; playback acceptance awaits retest.
[Identity fix](docs/reports/media-identity-fix.json).

The English repository cleanup reran 1,172 Python tests, nine JavaScript suites,
16 browser groups and ten sequential native phases. Archive hashes/links and the
rebuilt demo startup/relocation were also checked.
[Publication checks](docs/reports/english-publication-checks.json). One concurrent
native run failed during pythonnet/WinForms teardown after successful reopen
assertions; the sequential rerun passed, but that intermittent teardown issue
was not diagnosed or fixed.

Initial fixture/type failures and their corrections are recorded in the reports.
Manual acceptance of media controls is pending. Preceding local network/quality, GPU dashboard,
memory decisions and session token counting were reported working.
These checks do not establish real-account availability, support for every player
or production readiness. Same-title skips may remain unknown; existing persistent
safety locks do not clear on restart. API latency remains unavailable until a real
transport metric is defined. The portable demo predates this media-control change.

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
