# UI/backend contract

This describes the implemented desktop boundary, not planned API drafts.
See [architecture](ARCHITECTURE.md) for owners and [plan](PLAN.md) for current work.

## Transport and readiness

`api.js:emit(name,data)` calls `pywebview.api.event`. The `{ok,response,error}`
transport envelope is distinct from response.completed, verified domain results
and unknown outcomes. Promise rejection is caught and secrets are masked. Native
onEvent is only an observer; its failure cannot resend a delivered command.
An external browser host does not automatically gain native permissions.

`window.vex === window.jarvis` is a compatibility alias. ui_ready is sent once
bridge setters exist. Host readiness does not prove model connectivity. Mutations
remain blocked until initialization; corrupt settings require explicit recovery.

## UI -> native events

| Events | Meaning and boundary |
|---|---|
| ui_ready, retry_startup, recover_settings | Startup snapshot; recovery requires explicit approval |
| save, reset, ontop | Allowed preferences, not secrets or note/skill/routine mutations |
| query_apikey, apikey | Secret-free status / explicit credential storage; no key returned |
| query_catalog, model | API-discovered Live catalog and allowed selection; no fabricated list |
| text, live_text | Request-scoped REST / persistent Live text turn |
| live_audio, live_audio_start, live_audio_feed | Bounded PCM, sequence and request IDs; validated end packet |
| stop_task | Target request_id required; acceptance is not completion |
| read_reply | Tool-free speech for the stored REST reply via the existing audio path |
| disconnect | Release connection resources, preserve eligible RAM context |
| new_chat (internal/test) | Context-reset compatibility endpoint; no UI button |
| sleep_start, wake_feed, wake_close, wake | Local KWS and verified audio boundary; sleeping ambient audio stays local |
| notes_init, note_add, note_done, note_del, notes_replace | Approved backend ownership, real IDs/snapshots/readback |
| memory_decision | `{request_id,arguments:{id,approve}}` through shared memory.decide |
| query_clocks, clock_command | Shared Clocks read / core mutation; deletion is UI-only |
| clock_finished | Tool-free announcement after real id/generation verification |
| system_status, query_system | Core tool / ready-host read of the same Telemetry sample; query has no payload |
| query_media | Ready-host read of the shared Media snapshot; no payload or playback action |
| media_command | Versioned UI mutation submitted to the same media.control tool used by the model |
| fullscreen, shutdown, restart | Window lifecycle without abandoning active work |

Camera, location, Google, skill/routine execution, inspect and screen_share
commands are not implemented. Local timeline/drawer controls do not imply
external execution or verified success.

## Native -> UI and ownership

initApp/startupStatus, Live transcript and audioChunk are active updates. Transcript
request_id/role/sequence must match the current bubble; old turns cannot write into
new messages/audio. Input is 16 kHz mono PCM; bounded output is 24 kHz mono PCM.

initApp/loadStore share validation. Missing collection fields preserve, explicit
null clears, arrays replace. Invalid nested records reject the candidate. Setters
never send backend save/command feedback. Backup restore validates before applying;
notes use their separately verified store. Partial failure is not complete success
or an ACID transaction across both stores. Result setters are display compatibility,
not proof that weather/calendar/camera or other providers are integrated.

Preferences share preferences.store. Native notes use notes.json after approved
transfer. Skill/routine definitions remain localStorage data. Native clocks share
Python Clocks; bridge loss cannot reactivate a second JS engine. Standalone browser
clocks are a separate local mode. TextChat owns the conversation lock, PersistentLive
the socket, and assistant_session the UI turn/mic/wake lifecycle. Credentials are
excluded from JSON/localStorage/backups/errors.

## Stop, sleep, audio and voice

Stop forbids new tools, retry and fallback, preserving real results of started
work. Synchronous REST HTTP may not stop immediately: controls wait for confirmed
termination, or remain locked for unknown. Late Stop cannot affect a new request.
Resume is scoped to model/key/tools/connection identity; interrupted inputs are not
blindly resent. Eligible reconnection preserves side-effect IDs/replay protection
and has a bounded attempt budget.

Persistent `(principal,request_id)` and matching payload retrieve the old result
even after restart. New intended observations/actions need new IDs. Evicted RAM
records remain queryable on disk. Clocks/conversation RAM are not reconstructed by
replaying historical success. Journal failure/unknown blocks new tools; domain
side effects and journal commits are not one transaction.

Mic Off stops input only; Mute silences output only. Sleep requests are pending
until Vex's response/playback finishes. One-time sleep, return-to-sleep and idle
delay are distinct. Shutdown also waits for response completion; Stop, unknown or
stale requests cannot authorize closing. Local KWS/UI controls are not intent parsing.

replyVolume is numeric 0-1, legacy/reset default 1. Native rejects invalid values;
UI skips invalid snapshot fields and preserves an absent partial field. Zero is
silence, not missing. Existing PCM gain changes immediately and Mute preserves it.
Effects volume and microphone are independent.

setCatalog.voices contains documented preset Live voices with [LIVE] labels, not
API-discovered voice availability. conn.voice uses normal settings and next Live
setup speech_config; changes retain the active snapshot but invalidate old resume
identity for the next turn. REST TTS voice is separate. The API-key field stays
empty; a configured placeholder requires confirmed storage, not API acceptance,
and never includes a key or suffix.

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
write authority; the task journal can still retain proposal/source data.

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
can journal title/artist; background polls do not log/journal/send model requests.
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

## Verification boundary

Temporary profiles and synthetic providers validate contracts, not real-account
availability, quota, every player or microphone accuracy. Provider resume/GoAway
acceptance remains separate. See [AUDIT](AUDIT.md) and reports/ for actual evidence.
