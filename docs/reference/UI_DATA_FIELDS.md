# UI domain field reference

Implemented field/envelope details extracted without changing validation or
behavior. [UI/backend contract](../UI_BACKEND_CONTRACT.md) owns shared transport,
readiness and lifecycle rules. Read the relevant domain section, not every field.

## Personal memory — 6.1.1/2

prof.pMemory defaults false; prof.pMem is text up to 16,000 characters. Both use
normal profile save/snapshot/backup/schema and the same native settings store.
Existing text is not sent without opt-in. Disabling keeps local text but closes
model memory tools. Editing/clearing/disabling enabled memory drops old Live/RAM
context at the next turn. Active snapshots remain fixed. Failed save is not
successful forgetting; previous provider requests, visible history, backups and
journal data are not claimed erased.

memory.read({}) and memory.patch use registry/policy/TaskManager. patch actions:
append(text), replace(text,replacement), forget(text), clear(no text). Each requires
expected_snapshot and a same-turn read, rechecked against disk. Target text must
match exactly one entry. persisted/read_back and the real snapshot verify success.

Generic save includes memoryBase with the last confirmed `{pMem,pMemory}`; this
guard is not stored/backed up. A changed populated/enabled memory with mismatched
base returns memory_changed plus current memory_profile without writing. Initial
empty/disabled legacy profiles may initialize normally; unchanged-memory settings
are unaffected. Successful save returns memory_base. Late acknowledgements cannot
overwrite a newer base; conflicts require reopening/editing current data, not retry
or merge. UI applies returned memory_profile through loadStore({prof}) before
Stop/unknown handling, preserves drafts and sends no second backend save.

## Proposals and approval — 6.1.3

prof.pLearn defaults false, including legacy profiles, and cannot open tools without
pMemory. Scope/profile changes affect the next turn; memory_snapshot includes
permissions and confirmation preference. memory.propose({text,expected_snapshot})
requires same-turn memory.read. Host attaches real user text/ASR as source_quote;
source_verified/source_quote are not model schema fields. Provider hints cannot
replace real input, and replay retains the original source. Missing voice ASR is
blocked by voice_transcript_required; other missing sources fail source_unavailable.
Source/input limit is 20,000 characters. Source presence is not semantic truth.

Review results contain data.proposal={id,text,source_quote,snapshot}, persisted=false,
approval_required=true. Already-saved facts return proposal=null. At most one
1,000-character candidate lives in RAM; a new ID replaces it and restart loses it.
Stop/error/unknown does not auto-display/save it. Historical results grant no new
write authority. Schema-2 task receipts omit proposal/source contents; current
RAM results retain them only while available.

Save/Dismiss appears separately beside conversation controls, not Personalization;
render text/source via textContent. Buttons use memory_decision and a real ID and
boolean approve. Model memory.decide requires a later real user turn, fresh
memory.read and the actual pending ID. Same-turn propose blocks self-approval even
after another read. Ambiguous replies require clarification. With learning enabled,
all additions including explicit remember requests use propose; patch append is
removed from the model schema and blocked at submit. Correction/forgetting remain.

Decisions require completed+verified and current memory_profile. Stale ID/document/
permission, rejection and restart never auto-append. Unknown is not retried and
blocks new model work. Known terminal stale/rejected candidates clear only their
matching UI; a busy rejection permits a later explicit retry. decided_id cannot hide
a newer candidate. Stop does not undo completed saves. Logs contain safe error codes,
not raw arguments, speech, secrets or exceptions. No new inference service is used.

prof.pMemoryConfirm defaults true, including legacy profiles. Vex asks naturally
through the existing reply/audio path, not fixed TTS. Pending proposals are separate
from approved text; changing snapshots invalidates them. False enables existing
_apply append/readback directly, returning proposal=null, saved_automatically=true
and verified/persisted/read_back. UI refreshes once without a second mutation.
memory.write is required. Only the user UI changes confirmation preference; the
model cannot enable auto-save or bypass it. Semantic inference is not guaranteed.

## Session usage

gemini_token_count/GeminiUsage in app/session/gemini.py alone parse and aggregate
provider metadata. TextChat owns the application-lifetime counter. REST adds each
real response's usage_metadata.total_token_count once, including tool rounds.
Live counts final generation snapshots at tool/generation boundaries, not each
intermediate cumulative notice. Turn summaries are added once. Separate Interactions
TTS usage.total_tokens joins the same total, even after Stop/unplayed audio.

Reports carry usage_tokens (safe integer/null), usage_scope='session', usage_partial.
Stop/Disconnect/model/key/context changes do not reset it; app restart does. JS
checks request IDs and displays, never re-sums. Missing metadata/uncertain attempts
preserve known totals and mark incomplete; UI shows >=/Incomplete, or an em dash
before any valid usage. Zero is valid. This is not quota, billing or context size.
Late idle-consumed metadata is not recovered. Legacy tokens(used,max,isEst) remains;
conversation uses setSessionTokens. No extra countTokens call or persistent usage
file. [Usage metadata](https://ai.google.dev/api/live#UsageMetadata).

## Telemetry fields — 6.2.1/2

One Telemetry is injected into core/bridge. query_system requires readiness and no
payload; success is `{ok:true,completed:true,data}`. Data includes monotonic
sampled_at, os/os_release/architecture/logical_cpu_count, cpu_percent, memory_percent,
memory_total/memory_used bytes, disk_total/disk_used bytes, drive-letter disk_volume,
battery_percent/battery_present/ac_connected, executable-only active_process,
GPU/temperature fields and unavailable field names. Initial/unsupported CPU is
None; absent battery differs from unknown. No window title/full path is exported.

UI validates finite numbers/types, rejects older timestamps, converts bytes to GiB
and uses textContent. Failure/twelve-second staleness clears data; pagehide stops
delivery. Start after native initialization/recovery. Offline model status does
not clear local measurements or session tokens; standalone mode invents no CPU.

GPU: gpu_source='windows-pdh'; gpu_status=ok/warming_up/unavailable;
gpu_devices=[{id,utilization_percent}]; gpu_percent is the busiest engine/adapter
or None; gpu_sampled_at shares sampled_at. IDs are OS counter identities, not
product names/Task Manager ordering. Sum processes on one engine, not unrelated
engines/cards. Cache is two seconds. First baseline is not utilization. Errors
clear GPU only. Zero is valid; bar clamps 0-100, unavailable shows em dash/empty.
CPU/GPU temperature and VRAM capacity remain unavailable.
[GPU counters](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/).

## Physical network fields — 6.2.3a/b

network_source='windows-iphelper'; network_link=true/false/None for active physical
link/known absence/unknown; network_kind=wifi/ethernet/other/multiple/None;
network_wifi_connected=true/false/None. network_receive_bps/network_send_bps are
**bytes/s**, initially/reset/changed-interface None. unavailable lists missing fields.
The two-second shared sample converts to UI Mbps via *8/1_000_000, two decimals;
model reads full precision. This is not a speed test, quota, packet inspection or
internet-access proof. Virtual/VPN counters are excluded. No SSID/IP/MAC/interface
name or network configuration changes. Offline model status does not clear data.

Quality: network_ping_ms is physical IPv4 default-gateway RTT or None;
network_ping_status=ok/timeout/unreachable/no_gateway/no_link/unavailable;
network_wifi_signal=0-100 lowest connected physical Wi-Fi quality or None;
network_wifi_status=ok/unsupported/access_denied/not_connected/unavailable;
network_quality_sampled_at is monotonic and must not exceed sampled_at. Cache is
ten seconds, refreshed early on route/interface changes. Tooltip shows age; global
twelve-second staleness clears values/tooltips. Zero is valid. Gateway ping is not
internet/API latency; timeout is not an offline verdict. Connected without quality
shows Connected plus em dash; known absence Not connected; unknown em dash.

No arbitrary host parameter or raw target export. ICMP waits at most 250 ms.
WLAN opcode 19 uses no location-sensitive fallback. Handles/buffers close in finally.
Legacy setNetwork ping/down/wifi/api is preserved, with up Mbps, link enum and
wifiConnected boolean/null additions. API latency is a separate, still unavailable
metric; quality is not inferred from traffic or link speed.
[IP Helper](https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-getiftable2),
[WLAN quality](https://learn.microsoft.com/en-us/windows/win32/api/wlanapi/ns-wlanapi-wlan_realtime_connection_quality).

## Current media — 6.2.5a/b

query_media requires ready native host and no payload; response is
`{ok:true,completed:true,data}`. Model media.status reads the same Media with separate
media.read; system.read does not grant it. Data: source='windows-gsmtc', monotonic
sampled_at; status=available/no_session/unsupported/unavailable/timeout/session_changed;
title/artist string up to 512 or None; state=closed/opened/changing/stopped/playing/
paused/None. no_session is verified absence, unlike source/permission/SDK/timeout
failure, which returns failed/verified=false for the model, not 'nothing playing'.

Two-second cache/WinRT wait, three-second nonoverlapping UI queries, rejection of
older samples and ten-second stale clearing. Titles are textContent data.
setMedia(null) clears explicit loss; legacy title/artist/playing remains. Only Windows current
session metadata is read, not all sounds/tabs or file/URL/audio content. Model reads
persist content-free receipts, not title/artist; background polls do not
log/journal/send model requests.
[Windows media API](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession).

Snapshots additionally contain target_id (opaque 32-character lowercase hex or
null), controls (play/pause/next/previous booleans), and control_unknown (boolean).
The private Agile WinRT manager/session references are never serialized. One manager
is reused for polls and controls; targets are never compared across manager
activations. Transport loss clears the manager and target; no_session retains the
manager while exposing no controllable target. An observed session,
metadata, state or capabilities change rotates the target; missing session clears it.
Metadata alone does not grant control permission.

media_command accepts exactly `{version:1,request_id,arguments:{action,target_id}}`
or `{version:1,request_id,arguments:{action:'set_volume',target_id,percent}}`.
percent is a finite number 0-100, required only for set_volume; other actions reject
it. version is an integer, action is play/pause/next/previous/set_volume. The bridge requires a ready
host and no active model reply or unresolved operation. It submits media.control to
the existing policy/TaskManager with separate media.control permission. ModelTools
requires a fresh media.status result in the current turn; replayed reads from an old
turn do not authorize a new mutation. Repeated mutation IDs retrieve the old result.

Responses bind request_id and distinguish completed/verified/unknown; accepted or
pending is not success. Known rejection is completed with ok:false; late/mismatched
responses or deadline expiry leave controls locked. A later successful poll cannot
clear an unknown mutation. The existing persistent core lock survives restart.
Native dispatch is at most once, with immediate session/signature/cancellation
revalidation. Desired play/pause state or changed title/artist on the same session
is readback evidence; a true native boolean without it is unknown. Same-title skips
and previous restarting the current track are intentionally not claimed verified.
No new action, retry or fallback follows Stop; completed effects are preserved.
Native control timeout is four seconds, bridge wait eight, UI deadline ten.

Snapshots add volume `{scope:'application',status,percent,muted}` and boolean
controls.set_volume. Status is available/unavailable/ambiguous; missing percentage
and mute are null. Zero is valid. Native app/audio target identities remain private.
Exactly one active matching Core Audio session is controllable, or one inactive
match if no active session exists. Multiple applicable matches disable volume; no
fuzzy app matching, arbitrary PID selection or system/master-volume fallback exists.
GSMTC and audio-session identity are revalidated before dispatch and readback.
Core Audio calls are synchronous; the surrounding deadline can report unknown
without claiming that an in-flight OS call was cancelled. Never repeat such a write.

The range displays observed application volume. input only previews the number;
change sends one versioned media_command through the same core as model calls.
Browser volume applies to the browser application's audio, not a single tab.
Vex reply volume, effects volume, system volume and mute stay independent. The
former visible media status is an off-screen aria-live announcement; failures
remain in Engine log and control tooltips. No visible success text is added below
the playback buttons.

## Weather/location — 6.4

One shared Weather owner supplies query_weather (no payload) and model tools
weather.locations `{query}` / weather.current `{location_id?}`. Both tools require
weather.read. Omitting location_id uses only the user-approved native location;
an actual search ID queries another place without changing that preference. Empty
or ambiguous results require clarification, never an invented location or first match.

Native events are weather_search `{query}` and weather_location with exactly
`{confirmed:true,location_id}` (actual searched ID), `{confirmed:true,latitude,longitude}`
(explicit approximate Auto) or `{confirmed:true,clear:true}`. Search and polls do not
write task records. Preferences use the existing settings store/lock; the UI never
emits a second save. A successful preference response requires write/readback; an
uncertain save is not retried automatically. Saved weatherLocation is a validated
native-only object/null; generic UI saves/imports cannot grant location sharing.

Snapshot status is ok/stale/unavailable/location_required/location_changed. Successful
data contains place, temp/feels Celsius, hum percent, wind km/h, desc, modelled:true,
source, UTC observed_at/fetched_at, age_seconds and monotonic sampled_at. Zero is valid.
Only status ok yields verified model success; stale may retain old readings but must
be labelled stale. No recent usable cache means no readings, not fabricated zero.
No tomorrow/daily forecast or station-observation claim is supported in this slice.

The ten-minute cache, one-minute failed-refresh backoff, one-hour stale ceiling and
32-entry bounds belong to Weather. UI queries at most once per minute and clears
disconnected or two-minute-unrefreshed views. Changing location invalidates old query
responses; pure weather setters do not trigger save/commands. Search text is retained
on failure. Geolocation denial keeps manual selection available. Auto never runs at
startup; saved coarse coordinates persist while provider cache/candidate IDs do not.
The existing WebView2/Windows geolocation permission may still depend on OS policy.

