# Domain architecture reference

Implemented domain details extracted without changing their contracts. Start with
[Architecture](../ARCHITECTURE.md) for shared owners and execution rules. Search
headings and read the affected domain only; this is not a progress or change log.

## Domain rules

### Notes

Model note tools remain closed until the initial browser-note transfer is approved.
Real UUIDs and known creation times are preserved; old undated notes do not receive
invented dates. Before a model mutation, notes.select must produce a fresh result
in the same turn. Ambiguous single targets require clarification. Structured
latest/all/contains/ids selection supplies real IDs and expected_snapshot. Batch
deletion/completion uses one atomic write. Backend snapshots refresh the UI without
a second note_add/save mutation.

### Timers and stopwatches

Clocks is shared by bootstrap and bridge. The model exposes create/list/control;
deletion is UI-only. UI mutations also use registry/policy/TaskManager. The 500 ms
display query reads the owner without journaling every tick. Pause preserves
elapsed time; reset stops. Loss of the native bridge does not reactivate a second
browser clock engine. Clocks do not survive application exit.

Completion notifications are verified by ID/generation and use the existing
TextChat/Live/audio path in a tool-free turn. There is no second scheduler, TTS
engine or connection owner. Notifications wait while busy and are not spoken while
asleep. Stop, connection changes, deletion or restart invalidate stale notifications.
Failed/stopped announcements are not automatically repeated. This is not an OS alarm.

### Audio, sleep and conversation context

One AudioWorklet produces 16 kHz mono input. live_audio plays 24 kHz output under
the matching request ID. Speech thresholds, the prebuffer and bounded queues belong
to the same microphone owner. Mic Off stops input only; Mute silences output; Stop
ends the turn. Late PCM/transcripts never migrate to a new request. Unknown outcomes
keep relevant controls locked.

replyVolume is the existing PCM player's GainNode gain (0–1, default 1), shared
by Live/REST speech and timer announcements. Effects volume is separate. Changing
gain does not interrupt playback; unmuting restores the selected level. The setting
uses normal settings snapshot/save/backup/reset and does not change microphone or
model-session identity.

The model requests sleep through a tool; the host applies it after Vex's response
and playback finish. One-time sleep differs from return-to-sleep after each
interaction. Idle sleep is a separate 0–300 second preference. While asleep, local
wake processing does not stream ambient audio to the provider. Local wake spelling
variants and microphone calibration are not a general natural-language action parser.
Connection/Stop/scope changes must preserve existing request and cleanup rules.

ConversationMemory is bounded process-memory context. Session replacement can
retain eligible logical conversation context without blindly resending interrupted
inputs or replaying side effects. PersistentLive alone owns reconnect/resumption;
completed and unknown tool calls retain their identities and replay protections.

### Personal memory and proposals

Saved personal context is opt-in. `model_instruction` embeds enabled context as
JSON data, not instructions or permissions. REST, Live and timer turns use the
same profile snapshot. TextChat checks the enabled-memory fingerprint on the next
turn and drops old Live/RAM context when it changes; unconfirmed cleanup blocks a
new turn. Active replies are not interrupted solely to update a profile. Forgetting
does not erase earlier provider requests, visible messages, backups or task history.

With learning enabled, the model may propose clear durable self-reported facts.
Third parties, quotations, jokes, temporary/hypothetical states, secrets and sensitive
facts are excluded by model instruction, not a deterministic semantic guarantee.
ModelTools attaches the real current text/transcript as source; model-rewritten
quotations are not evidence. Missing real input is never invented. The shared
transcript gate blocks tools when appropriate; a source-less domain proposal fails.
When proposal mode is enabled, even explicit additions use memory.propose rather
than memory.patch append. Explicit correction/forgetting retain their normal path.

Review mode holds at most one pending candidate in RAM: 1,000 characters, with
source bounded by the 20,000-character input limit. A new candidate invalidates
the old ID. Restart is not approval and loses the pending RAM candidate. Candidates
are not profile/backup data. Private task receipts do not retain proposal/source
contents; full results and immutable replay provenance live only in the current RAM session.
memory.decide requires a fresh memory.read and the real pending ID in a later user
turn; another read in the proposal's own turn cannot self-approve it.

prof.pMemoryConfirm defaults to true. Separate Save/Dismiss controls appear beside
conversation controls, not inside Personalization. Vex asks naturally through the
existing response/audio path. A later explicit unambiguous spoken/typed decision
uses memory.read -> memory.decide. Ambiguous replies are not consent; semantic
interpretation remains a model responsibility. Buttons use the same registry,
policy and TaskManager path, not UI-supplied approval text.

If the user disables confirmation, memory.propose uses the existing append/readback
logic to save directly to the single profile. Only the UI can select this preference;
the model cannot enable auto-save or approve its own same-turn proposal. The
preference belongs to the snapshot, so changing it invalidates an old read.
memory.propose therefore requires memory.write. Save verifies persistence/readback;
dismiss does not change the profile. Failed or unknown outcomes do not trigger an
automatic retry/merge. Late decided_id results cannot hide a newer candidate.
UI profile refresh preserves drafts and never starts a second save cycle.

### Live voices

conn.voice is separate from pLang/pIns. catalog.py contains one allowlist of
Google's 30 documented preset Live voices; it is not an API-discovered voice list.
Model discovery still uses the API. Empty/legacy voice preferences fall back to
Puck. Native input snapshots language/instructions/voice together; Live text,
microphone and timer replies use the same TextChat/PersistentLive path.
speech_config sets the selected voice. A voice change changes connection identity,
invalidating old resumption handles/call maps without changing an active turn's
snapshot. The separate REST TTS voice is not controlled by this preference.

## Local system measurements

Telemetry owns the two-second cache and CPU baseline. Windows GetSystemTimes,
GlobalMemoryStatusEx, GetSystemPowerStatus and foreground-process queries supply
CPU/RAM/battery/process data; shutil.disk_usage supplies runtime-volume occupancy,
not disk throughput. Only the foreground executable name leaves the adapter;
document/window titles and full paths are not collected. Initial/reset CPU samples
and systems beyond the supported 64-logical-processor scope return None.

system.status uses system.read through the normal model tool path. query_system
reads the same owner without adding a journal task. The existing one-second UI
tick starts nonoverlapping queries at least three seconds apart. No second sampler
thread/timer/state exists. Failure or twelve-second staleness clears readings.
Model offline status does not invalidate local CPU/RAM measurements.

### GPU

windows_gpu.py reads GPU Engine counters through Windows PDH, using
PdhAddEnglishCounterW independently of OS display language. It does not run vendor
commands, open Task Manager or add a sampler/package. One WindowsGpu belongs to
Telemetry; query handles close on errors/shutdown, with a finalizer fallback.
First collection establishes a baseline; a recreated query warms up again.

Process counters are summed per adapter/physical engine. An adapter's reported
utilization is its busiest engine; the dashboard shows the busiest adapter, not
the sum of unrelated engines/cards. gpu_devices IDs are OS counter identities,
not product names or Task Manager GPU 0/1 ordering. Process IDs are not exported.
Intel/AMD/NVIDIA adapters work when Windows exposes suitable WDDM counters; there
is no universal old-driver/hardware guarantee. Temperature and VRAM capacity remain
unavailable. CPU temperature is not inferred from GPU/ACPI values. Sampling and
adapter choice can differ from Task Manager.

### Physical network traffic and quality

network.py adapts GetIfTable2. One Network inside Telemetry owns prior RX/TX
samples and uses the same two-second lock/cache. Select physical, non-filter,
non-endpoint, non-loopback, non-tunnel interfaces. Divide 64-bit active-interface
byte deltas by elapsed time; interface changes/counter resets establish a new
baseline. First speed is None; unchanged counters produce real zero. FreeMibTable
releases allocated tables in finally. Source failure does not invalidate CPU/RAM/GPU.

Outputs contain link kind/status, Wi-Fi connected status and RX/TX bytes per second;
the UI converts rates to Mbps. No SSID, IP/MAC, profile/interface name is exported.
Traffic is not a speed test, link capacity or proof of internet access. VPN/virtual
counters are excluded to prevent double counting, so virtual-only setups are outside
complete physical-traffic coverage. Model/API status is not local-link status.

network_quality.py is a bounded Win32 adapter; Network owns its ten-second cache
under the Telemetry lock. Physical-interface/route changes refresh quality early.
The lowest-metric active physical IPv4 default route selects a local gateway.
One small IcmpSendEcho waits at most 250 ms; there is no DNS, arbitrary target,
public-server probe or scan. The shared measurement lock can wait during this
probe. Timeout is not proof of internet failure. VPN-only/IPv6-only gateways are
outside this scope.

Wi-Fi uses WlanQueryInterface realtime_connection_quality, without sensitive
current_connection/BSS/scan fallbacks or location permission. Read at most 16
connected physical Wi-Fi adapters; report the lowest quality for multiple adapters,
or None if a required query fails. Zero quality is valid. Output contains only
milliseconds/percentage, status and monotonic sample time, not route addresses,
GUID/index or SSID/MAC. Query polling can trigger the bounded gateway probe but
does not journal every sample. WLAN clients/buffers and ICMP handles close in finally.
API transport latency is not derived from local traffic or total reply time.

### Current Windows media session

main gives the same Media instance to create_core and NativeBridge. media.status
uses media.read and the shared model execution path; query_media reads the same
snapshot without growing the task journal. Model reads persist only content-free execution receipts, not title/artist.

Read Windows GSMTC's current session, not every application/tab or raw speaker
output. Metadata is title/artist/playback state published by the source app; no
album art, window title, tab URL, file path or microphone capture is collected.
Treat metadata as data, never instructions. WinRT runtime/Foundation/Media/
Media.Control projections supply API types, not a new player or model framework.

The backend caller runs a temporary asyncio loop with a two-second wait bound.
MTA initialization/uninitialization is balanced without forcing another apartment
mode. The owner retains the private Agile manager and its session reference for exact target identity;
WinRT objects never enter JSON, UI snapshots or task records. One lock/cache shares two-second
samples; session changes during await invalidate old results. media_view.js uses
the existing tick, at least three seconds between nonoverlapping queries, and clears
after ten seconds without fresh data. no_session is distinct from unsupported,
unavailable, timeout and session_changed. Failures clear stale titles/animations.
media.control has separate media.control permission and shares this owner through
the registry/policy/TaskManager path. UI media_command submits the same tool; it is
not a second executor. The model must read media.status in the current turn and
use its opaque target_id. Session, metadata, state or capability changes invalidate
that target. Native revalidation occurs immediately before a single dispatch.

Play/pause succeed only after observing the desired state; next/previous require
changed title/artist on the same session. The native acceptance boolean alone is
not completion. A same-title skip or previous-track restart cannot be proved with
this metadata contract and may be unknown. Unknown results latch the existing
persistent TaskManager safety lock; polling/restart do not authorize a retry.
Stop prevents undispatched actions but preserves confirmed effects already made.
The native control wait is four seconds, bridge wait eight and UI deadline ten.
Model replies and manual media controls exclude each other; stale/unsupported
controls remain disabled. There is no arbitrary session/app selector or system/master-volume tool.

Manager activation is lazy and reused across UI polls and worker controls. Different
GSMTC manager instances can expose unequal session objects for the same underlying
player; identity comparisons are valid only within the issuing manager. Source loss
invalidates that manager and its target before a later read reacquires it. An empty
current session retains the manager so a newly opened player can be observed.

Player volume is media.control action set_volume, through the same permission,
queue, replay and Stop rules. media_volume.py is a native adapter, not a second
state owner: it enumerates active render endpoints and matches audio-session
process identity to the GSMTC source app ID or exact executable name/stem. A
single active match takes precedence over old inactive sessions; multiple active
matches, or multiple inactive matches with no active session, disable control.
Private endpoint/session instance IDs bind the observed target and never enter
snapshots or journals. An audio target change rotates the existing media target ID;
volume-level changes do not. Core Audio references/strings/process handles are
released on the same calling thread, including failure paths.

Only ISimpleAudioVolume changes application volume, with an absolute 0-100 value
and readback within 0.1 percentage points. No endpoint/master volume, keyboard
shortcut, Vex reply-volume or mute write is used. A browser target is browser audio,
not one tab. Unknown/unsupported mapping never falls back to system volume. Polling
reads Windows' actual level; this is not a saved TaskVex preference. The UI range
commits once on change and shows confirmed values; its status remains screen-reader
accessible without visible dashboard text. Controls and range use the saved UI theme.
[Session volume API](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nn-audioclient-isimpleaudiovolume).

## Weather and approved location

main shares one Weather instance and settings JsonStore between core and bridge.
weather.locations/current use weather.read through ModelTools/registry/policy/
TaskManager. query_weather reads the same cache without journaling each dashboard
poll. Open-Meteo is a public L0 service adapter, independent of Gemini connectivity.
No provider request occurs before a saved location or an explicit place search.

Manual search returns up to five actual place IDs/labels. Neither UI nor model may
silently choose the first ambiguous result. The UI's explicit selection saves a
default location. Auto requests browser geolocation only after a user click and
sharing confirmation; coordinates are rounded to two decimal places before transfer
and persistence. Startup reuses the approved place without asking for geolocation.
Clear removes it. Model reads/searches cannot change this preference or request GPS.
The setting uses JsonStore's existing lock and write/readback, preserving other
preferences; generic save/import cannot grant or replace location consent.

Forecast and geocoding URLs are fixed HTTPS endpoints, without redirects, keys,
arbitrary URLs or automatic retries. Responses are size/time bounded and validated
for units/ranges/timestamps. Data is modelled current weather, not a local sensor
or a future forecast. A ten-minute cache avoids continuous provider calls; failed
refreshes back off for one minute. Cached values remain explicitly stale for at
most one hour, then clear. Missing measurements never become zero. UI polling uses
the existing tick once per minute; late responses from a former selection cannot
replace the current view. Source/model time remains visible; provider attribution is in README.md and THIRD_PARTY_NOTES.md.

Location preferences are native-only and currently excluded from the legacy UI JSON
backup, avoiding silent geolocation consent through imports. City/provider data in
tool results is untrusted content; saved coarse coordinates stay out of model results
and polling logs, but remain ordinary local settings, not credential storage.
Provider terms/attribution are recorded in THIRD_PARTY_NOTES.md.

## Camera input ownership

Camera On is a local user input control, like microphone On/Off, not a model tool.
Only the user can enable capture. Device IDs use the same browser device preference
adapter, with exact selection and no fallback to another camera. The browser owns
permission and its video-only track; settings store a device preference, never an
active camera grant. Startup does not open the camera or request permission.

During an active Live user turn, the camera owner supplies bounded JPEG input through
NativeBridge -> TextChat -> PersistentLive -> probe_live_text on the existing socket.
Text turns receive an initial image before their prompt; speech frames follow the
same explicit activity start as PCM. One sender samples at most once per second,
retaining only the latest frame and dropping queued images older than two seconds.
Images are capped at 256 KiB; browser capture scales the longest edge to 640 pixels.
JPEG framing/size are checked at the boundary; actual image decoding is the provider's
responsibility. No second connection, tool executor, audio player or frame history exists.

Screen sharing reuses this same owner and Live path. getDisplayMedia is invoked
synchronously from the explicit user click so browser activation/source selection
remains authoritative. The screen and camera are mutually exclusive; switching
requires turning the current source off. No display identity/grant is saved and
there is no automatic reacquisition. A local muted preview shows the selected
screen/window. Screen frames are downscaled to a longest edge of 1280 pixels;
camera retains 640. Both retain the same 256 KiB, expiry and cadence limits.
Only video is requested; unexpected audio tracks reject and release the stream.
Browser/OS Stop sharing, permission cancellation, timeout and late-grant cleanup
use the same release path. Closing the drawer only hides controls/preview, not capture.
Screen content is untrusted input, never authority for tools or user instructions.
Provider contract: [Live video input](https://ai.google.dev/gemini-api/docs/live-api/capabilities#sending-video).

Idle camera frames stay local. Camera Off releases the device and closes only the
video input; microphone and model output continue. Stop ends current transmission,
while camera may remain locally ready for a future user message. Sleep, Disconnect,
model/key/mode change, unknown results, shutdown and pagehide release capture.
Request IDs/sequences reject stale or duplicate frames; no reconnect replays pixels.
Already sent/in-flight images cannot be recalled; Camera Off does not erase provider
conversation context. Image content is observation data, not action authorization;
model actions still require the existing tools, policy and TaskManager.

## Permission settings

Settings > System > Permissions is owned by ui/js/permissions.js. It queries
browser permission status only when opened/refreshed; status queries never start
capture or geolocation. Explicit Request access uses a short default-device probe
and stops every returned track immediately, or requests one approximate position
and discards it. Existing live_mic/live_video capture is not replaced; an active
device does not need a second probe. No toggle, profile grant flag, Live socket,
weather preference or provider request is created. Timeouts/pagehide reject stale
results, and a late media grant still releases its tracks.

The browser and Windows control actual permission and persistence. Unsupported
status queries remain Not reported; browser Allowed is not a guarantee of working
hardware or OS policy. NativeBridge.permission_settings opens one of three fixed
Windows privacy URIs from a user button. It cannot take arbitrary URLs or grant
access; remembered browser denials and Windows policy may still require user action.

## Shared GUI target references — backend foundation

TargetReferences issues opaque IDs only for active host task scopes. Snapshots bind
application/process-or-connection lifetime, window lifetime and target generation;
DOM targets also bind tab/document/element identities. IDs/versions must come from
trusted real adapters, never the model or a guessed bare HWND/PID. Scope permission
is separate: issuing a target does not grant control or image upload authority.

access() provides scope metadata to the existing PolicyEngine callback; resolve()
reobserves through a trusted read-only adapter inside the normal domain/core path.
Readers run outside the cache lock; cancellation, scope end, replacement, focus and
identity/version changes are rechecked before returning. Driver code must still
revalidate at its actual OS/input boundary and distinguish preflight rejection
from uncertain effects after dispatch. No target method executes an action.

The store keeps at most 256 live references by default, replaces current slot/
document/frame observations and never silently evicts active targets to admit more.
Adapters release closed/paged-out refs; lifecycle calls release_scope on task end.
Inactive scopes are also pruned at issue. No reference, image or reader is persisted.
Existing notes/media selectors retain their domain ownership; this is not a second
executor or an alternate registry for those domain IDs.

Visual geometry explicitly uses physical desktop capture bounds, captured image
dimensions, frame ID, host-monotonic capture time and DPI. Negative monitor origins
are valid; DPI is not applied twice. Logical/unknown geometry, unknown/background
focus, stale/future frames and out-of-image points cannot produce physical input.
resolve_point requires an explicit host-selected frame-age budget; no production
budget is selected here. A changed frame/region invalidates old coordinate use.

Resolution preserves no-match, unsupported, permission-denied, stale, unavailable
and cancelled states. can_fallback only admits explicit no-match/unsupported when
dispatch is known not to have begun. Started or uncertain dispatch never permits
fallback/replay. This predicate is not a router or authority to execute another tool.

This foundation is tested with synthetic adapters. Current Notepad observation is
not upgraded to lifetime-safe GUI targeting, passive Live frames are not an input
driver, and no UIA/DOM/visual library is installed. Actual bindings/OS acceptance
belong to 7.P3b with 7.1/7.3. Task/Stop cleanup wiring remains 7.P4/7.P2b.
Read deadlines/cooperative cancellation belong to those adapters and the logical
task lifecycle. This store does not force-stop synchronous readers or add a worker.
