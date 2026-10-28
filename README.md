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
- Player application volume from a themed range or model request, with Windows
  readback. It does not change system/master or Vex reply volume; browser scope
  covers that browser's audio, and ambiguous session mapping stays disabled.
- Current weather from Open-Meteo, with manual place selection or explicit
  approximate-location permission, saved location and a shared model/dashboard
  cache. Source time and stale/unavailable states are shown; this is modelled
  weather, not a local sensor or daily forecast. The dashboard needs no Gemini key.
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

Settings > System > Permissions can request camera, microphone and location access
without a Live connection; probes do not save/share content or turn input On.
Windows privacy links are provided for blocked access. Media permission probes
briefly open the system-default device and immediately close it; location probes
discard coordinates. Browser/Windows remain the permission authorities.

Camera input is available through explicit Camera On/Off and the selected device.
Images stay local while idle and are shared only during Live user messages, using
the existing connection: bounded JPEG frames at most once per second, rather than
a full-frame-rate video stream. Sleep/disconnect release capture; Camera Off preserves
microphone and reply. The user reported successful camera tests; exact hardware/
provider coverage was not separately enumerated.

Screen sharing uses the bottom-right screen controls and an explicit platform
screen/window picker. It shares the same Live visual path as camera, one source
at a time, with video-only capture and a local preview. No selection/grant is
restored at launch. Screen Off preserves the microphone/reply; sleep/disconnect
release the source. Frames are capped at 1280 pixels longest edge and 256 KiB.
This is visual understanding, not desktop control. The user reported successful
screen-sharing tests; exact picker/device/provider coverage was not separately recorded.

A small allowlisted application plugin exists in the core. The conversational
model currently sees its catalog, not unrestricted app-launch or desktop control.
Skill and routine editors store definitions locally; they do not execute them yet.
A separate REST adapter remains available for development and future channels.

## Stage 7 backend foundations

The accepted backend prerequisites now include host-issued task scopes, fresh
GUI-target reference contracts, and logical tasks with dependency-aware progress.
They use the existing registry, policy and single TaskManager worker. A definite
failure blocks dependent steps while independent branches can continue; Stop
acceptance remains separate from actual completion, preserving completed effects.

Trusted host intervention checkpoints can wait indefinitely for explicit Continue
or Cancel without occupying the worker. Continue requires fresh reobservation and
cannot revive stopped or replaced tasks. Three unchanged planning observations
after a baseline produce a no-progress wait; only a RAM digest is retained.

These foundations do not yet form a general GUI agent.
No UIA/DOM/visual automation driver is installed. Host-only logical recovery now
retains content-free restart metadata and requires explicit fresh replanning;
there is no public task Continue control. Cooperative operation deadlines and one
safe-read retry are available as host registration primitives; existing tools keep
their defaults. Configured host workflows now clean up their existing task grants/target refs
on completion, Stop and close. Production adapter policies and actual desktop task
issuance remain planned. A native permission panel now handles real host-issued
requests, with a saved ask-before-physical-input setting. Acceptance requires host
rechecking before continuation. Current host tasks also have a native progress
selector and exact-ID/revision Stop control; normal chat does not yet create desktop tasks. Existing per-tool durable replay protection is separate
from whole-task recovery; historical receipts do not restore private arguments.

The latest source checks passed 270 targeted/regression tests, three documentation
checks, eleven JavaScript suites and 31 browser groups, plus targeted native chat
and UNKNOWN checks. [Evidence](logs/reports/workflow-view-checks.json).
The host-task progress/Stop change has **not been manually tested by the user**;
it is published by explicit request, not as a release or manual acceptance.
These checks are not a new full Python regression or eleven-phase native run.

## Not implemented yet

Google Drive/Calendar/mail access, Telegram/Discord integration,
general GUI automation and
backend skill/routine scheduling are planned.
GUI inspection/clicking and additional audio-input sources are not connected.
CPU/GPU temperature and VRAM capacity are not available from the current sources.
CPU sampling currently supports Windows processor groups with at most 64 logical processors;
unsupported readings remain unavailable.
Some saved legacy profile fields have no backend effect and are marked as planned.
Stage 6's agreed functional scope is accepted. File/web/GUI work belongs to stage 7,
routines/maintenance to stage 8, and external accounts/channels plus deferred
additional audio sharing to stage 9. Native startup/teardown and release limits
remain open; functional acceptance does not establish production readiness.

Weather uses the provider's non-commercial public endpoint with attribution;
commercial deployment needs a provider-terms/configuration review. Approximate
coordinates remain native settings and are excluded from legacy UI JSON backups.

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
[Build evidence](logs/reports/demo-build-checks.json). This is not clean-machine,
microphone, real-account or all-hardware certification. No signed installer or
GitHub binary release is provided by the source repository.

## Data and current limits

Active conversation input and model tool results are sent to Google. During
sleep, wake detection processes microphone audio locally. This is not a fully
offline assistant. API keys use Windows Credential Manager; notes and settings
are local files. Skill/routine definitions use browser storage. Timers and
conversation context do not survive application exit. User-edited personal memory
is saved separately in the profile and sent to the model only when explicitly enabled.

Camera/screen frames are not saved to disk, task records or text conversation summaries.
Already sent images can remain in the provider session context; Camera Off does
not recall them. Location permission checks do not set the saved weather location.

Native tool execution receipts are kept in a local SQLite journal. Reusing
the same request ID does not run the action again, including after restart.
The 256-record limit bounds active work and RAM records, rather than lifetime
usage; historical records stay on disk. Unknown outcomes block new tools until
explicit local review. Startup lists the affected tool/task IDs; after checking
the effects, users can acknowledge uncertainty and continue. This does not turn
an unknown result into success, undo it or repeat the old action. Settings repair
is offered for damaged preferences, not unknown tasks.
Schema 3 retains IDs/status and a request fingerprint, not note/file/message bodies
or personal proposal/source text. Original results remain in bounded RAM; disk
reads explicitly report unavailable historical content. Existing schema 1/2 profiles
migrate before tools start; replay keys and UNKNOWN review remain intact. Do not
downgrade migrated profiles to schema-1/2 builds. Metadata is unencrypted, digests
are not secret storage, and history grows with usage. Migration cannot erase old
external backups, provider requests or OS/forensic copies. This is not an
exactly-once guarantee for external services. Native and
core ownership locks reject a second worker sharing the same data profile.

There are no general latency, memory-footprint or acoustic-accuracy guarantees.
Model availability, network conditions and hardware affect behavior.

## Verification and documentation

Latest Stage 7 managed-resource validation passed **1,460 Python tests**,
including **238 focused checks**, Pyright with zero errors/warnings, and eleven
native legacy-compatibility phases. [Backend checks](logs/reports/workflow-resources-checks.json) ·
[Native evidence](logs/reports/workflow-resources-native.json).
These checks use temporary profiles and synthetic tools/adapters, not paid APIs,
real user tasks or actual GUI control. Managed task scope cleanup is host-only;
real permission UI, conversation task binding and driver acceptance remain pending.
Successful native checks do not eliminate earlier intermittent startup/teardown issues.

Earlier camera/permission and startup evidence follows; its test counts belong
to those changes and are not a new rerun of every hardware/provider scenario.

The latest camera/permission work passed **1,269 Python tests**, **nine JavaScript
suites**, **25 browser groups**, focused type checking and dependency checks.
Two targeted native phases verified default-camera permission checks, immediate
probe cleanup and restart persistence with temporary profiles and synthetic input.
[Current validation](logs/reports/permissions-checks.json) ·
[Targeted native evidence](logs/reports/permissions-native.json).

**Earlier camera/permission native runs did not complete cleanly.** They encountered a UI
startup timeout and a Python.NET/WinForms teardown failure, including a process
failure after successful chat assertions. Their root causes are not established;
targeted successes do not close these issues. Camera/permission tests were later
accepted by the user; exact OS/device/provider coverage was not independently recorded.
Automatic checks used no paid API or real camera/user content.

Weather and media controls were reported working by the user; precise hardware
and provider coverage was not separately enumerated. Historical evidence is in
[weather checks](logs/reports/weather-checks.json),
[player-volume checks](logs/reports/media-volume-checks.json) and
[camera checks](logs/reports/camera-checks.json). These checks do not establish
production readiness, all-player/hardware support or real-account availability.

Startup recovery now distinguishes unknown tasks from invalid settings. Synthetic
restart tests preserve old results/replay keys, and a focused native test verifies
explicit review plus notes/clocks readiness. See
[startup recovery checks](logs/reports/startup-recovery-checks.json).
This correction passed 1,278 Python tests, 119 subsequent focused tests, nine JS
suites, 26 browser groups, Pyright with zero errors and all eleven native phases.
The clean native run does not prove earlier intermittent startup/teardown issues
are eliminated. [Native recovery regression](logs/reports/startup-recovery-native-full.json).
Unknown tool outcomes still require review and do not clear merely on restart.
Screen-sharing validation and remaining native/manual limits are recorded in
[screen sharing checks](logs/reports/screen-sharing-checks.json).
API latency is not measured. The existing portable demo predates these camera
and permissions changes; it was not rebuilt for this update.

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

## Weather data attribution

Weather data is provided by [Open-Meteo](https://open-meteo.com/) under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); place data comes from
[GeoNames](https://www.geonames.org/) via Open-Meteo.
