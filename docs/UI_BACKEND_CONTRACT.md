# UI/backend contract

This describes the implemented desktop boundary, not planned API drafts.
See [architecture](ARCHITECTURE.md) for owners and [plan](PLAN.md) for current work.

Read shared transport and lifecycle rules here. Memory/usage/telemetry/media/weather
fields are in the [domain field reference](reference/UI_DATA_FIELDS.md); follow only
the affected section. The original section headings below remain navigation links.

## Transport and readiness

`api.js:emit(name,data)` calls `pywebview.api.event`. The `{ok,response,error}`
transport envelope is distinct from response.completed, verified domain results
and unknown outcomes. Promise rejection is caught and secrets are masked. Native
onEvent is only an observer; its failure cannot resend a delivered command.
An external browser host does not automatically gain native permissions.

Backend task authorization (7.P2a) adds no public UI event or setting yet.
authorization_id is host-selected core/ModelTools metadata, never a field the model
or UI can use to grant itself authority. Scope expansion, approval dialogs, physical
input preference and task lifecycle revocation remain 7.P2b integration work.

Target-reference backend (7.P3a) likewise adds no UI event, capture driver or model
tool. Refresh callbacks, lifetime/document generations, geometry and frame-age
budgets are trusted host adapter inputs, never JSON claims of authority. Current
Live JPEG envelopes are unchanged and do not themselves prove target geometry.

Logical workflows (7.P4a) are currently a trusted backend API, not UI events or
model declarations. Their completed/requires_review/stop_requested fields are
separate from one Live/REST turn's completed flag. Existing Stop targets its current
turn; logical-task Stop/progress, message classification and scope cleanup require
7.P2b binding. Do not render these backend APIs as working spoken commands.

7.P4b.1 adds backend wait_requested/waiting_for_user states and wait_reason /
no_progress_count metadata. These are separate from turn completion. No public
pause/Continue event exists yet. Trusted host callbacks reobserve outside locks;
UI/model assertions cannot supply validation or revive stopped/replaced jobs.
Waiting has no automatic expiry; three unchanged planning observations after a
baseline produce a no_progress wait.

7.P4b.2 adds host-only recoverable_workflows / recover_workflow / cancel_recovery.
They expose content-free, principal-scoped restart metadata and require explicit
fresh replanning/revision checks before continuing. No public UI/model event is
added. Schema-3 history cannot restore private parameters, targets or approvals;
historical_steps is read-only outcome metadata, not a fresh result/context grant.
Normal close differs from explicit Stop; UNKNOWN still requires separate review.

7.P4b.3 operation_progress is host telemetry only, not a new UI/model event.
A configured operation can expose deadline_exceeded=True while completed=False;
never unlock controls or claim cancellation from that flag. Terminal configured
results carry evidence.operation_policy with actual attempts, retry_blocked and
frozen deadline_exceeded. Historical receipt telemetry is unavailable. Host-only
registration selects deadlines/read-only/transient codes; model arguments cannot.
Existing built-ins are not automatically opted in; actual adapter values remain open.

`window.vex === window.jarvis` is a compatibility alias. ui_ready is sent once
bridge setters exist. Host readiness does not prove model connectivity. Mutations
remain blocked until initialization; corrupt settings require explicit recovery.

## UI -> native events

| Events | Meaning and boundary |
|---|---|
| ui_ready, retry_startup, recover_settings | Startup snapshot; recovery requires explicit approval |
| acknowledge_tasks | Local explicit unknown-result review: `{confirmed:true,task_ids:[actual IDs]}`; no model tool, replay, result rewrite or settings repair |
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

Google, skill/routine execution, inspect and legacy screen_share
events are not implemented. Explicit local screen capture uses the existing visual
envelopes below, not a new model tool. Local timeline/drawer controls do not imply
external execution or verified success.

## Native -> UI and ownership

Disk-backed task reads expose historical receipt metadata, not original payloads:
empty request.arguments, result.data=null and
result.evidence={historical:true,content_available:false}. Preserve task/status and
verified execution history; do not display unavailable content as a fresh note,
media target or memory snapshot. Current RAM results keep their normal shape.
No new UI mutation/event or second save is introduced by journal migration.

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
side effects and journal commits are not one transaction. Startup preserves
TaskManager error codes rather than classifying their ContractError base as
settings_invalid. For uncertain_state, startupStatus adds unknown_tasks containing
only task_id/tool; settings repair is hidden. Review requires explicit confirmation
and 1–256 unique actual UNKNOWN task IDs; active work/storage failure prevents it.
Acknowledgements are durable, separate from results and replay keys. Reviewing
old IDs cannot approve newly unknown tasks. If more remain, startup remains blocked
and presents the next bounded page. Unknown effects are not claimed resolved.
Successful Retry, settings repair and task review all finish the normal native
startup path, including shared clocks, approved notes and model catalog loading.

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

See [Personal memory — 6.1.1/2](reference/UI_DATA_FIELDS.md#personal-memory--6112) for the implemented domain details.
Read only the relevant subsection when changing this domain.

## Proposals and approval — 6.1.3

See [Proposals and approval — 6.1.3](reference/UI_DATA_FIELDS.md#proposals-and-approval--613) for the implemented domain details.
Read only the relevant subsection when changing this domain.

## Session usage

See [Session usage](reference/UI_DATA_FIELDS.md#session-usage) for the implemented domain details.
Read only the relevant subsection when changing this domain.

## Telemetry fields — 6.2.1/2

See [Telemetry fields — 6.2.1/2](reference/UI_DATA_FIELDS.md#telemetry-fields--6212) for the implemented domain details.
Read only the relevant subsection when changing this domain.

## Physical network fields — 6.2.3a/b

See [Physical network fields — 6.2.3a/b](reference/UI_DATA_FIELDS.md#physical-network-fields--623ab) for the implemented domain details.
Read only the relevant subsection when changing this domain.

## Current media — 6.2.5a/b

See [Current media — 6.2.5a/b](reference/UI_DATA_FIELDS.md#current-media--625ab) for the implemented domain details.
Read only the relevant subsection when changing this domain.

## Weather/location — 6.4

See [Weather/location — 6.4](reference/UI_DATA_FIELDS.md#weatherlocation--64) for the implemented domain details.
Read only the relevant subsection when changing this domain.

## Verification boundary

Temporary profiles and synthetic providers validate contracts, not real-account
availability, quota, every player or microphone accuracy. Provider resume/GoAway
acceptance remains separate. See [AUDIT](AUDIT.md) and [logs/reports](../logs/reports/) for actual evidence.

## Visual input — camera 6.8.1 and screen 6.8.2

`live_text`, `live_audio_start` and `live_audio` optionally accept `video`, a base64
JPEG without a data-URL prefix, along with their existing request fields. REST,
timer notifications and other event envelopes cannot attach camera input.
Screen selection supplies the same optional video field and live_video_feed
envelopes. No source name, window title, screen grant, frame or display identifier
enters settings, task records or text memory. Camera and screen cannot be enabled
simultaneously in this slice. No provider-specific SDK types enter the UI contract.
`live_video_feed` accepts `{request_id}` for input status or exactly
`{request_id,sequence,data}`. Sequences start at zero; data is base64 JPEG or null
to close video only. Maximum decoded image: 262144 bytes; JPEG start/end markers
and base64 are validated. Sequence/replay errors close video input. Closed old
input can acknowledge a harmless close/status but never accept another image.
Only a ready, awake native host accepts packets; there is no standalone-browser grant.

One LiveVideo object belongs to the matching active request in PersistentLive.
Short feed calls do not wait for the conversation lock. The single-slot buffer,
frame expiry, 120-packet limit and one-second socket send interval bound input.
Stop closes this input immediately; an image already sent cannot be withdrawn.
The result may include video_frames_sent and video_error, never image data.
Camera frames are absent from settings/backups, task records and RAM text summaries.
Camera Off is independent of Stop, microphone On/Off and audio playback.
Screen sharing Off has the same semantics: release capture, clear preview and close
only visual input. Stop ends transmission for this turn but can leave the source
locally ready for a future user message. Sleep, Disconnect, unknown, model/key/mode
change and page close release both source types. A fresh user click/source picker
is required to enable screen capture again. Drawer close does not revoke capture.
getDisplayMedia requests video only; capture/setup has a 15-second bound and late
grants are released. Screen snapshots scale to 1280 pixels maximum longest edge;
camera uses 640. Byte, sequence, expiry and socket cadence bounds are unchanged.
The platform picker is the permission boundary; no saved checkbox grants screen access.

## Permission settings — 6.8.1a

`permission_settings` accepts exactly the string camera, microphone or geolocation,
after native startup. The host opens the corresponding fixed Windows privacy page
and returns `{ok:true,completed:true,opened:true}` only when OS launch succeeds.
This means navigation was requested, not that permission was granted. Caller URLs,
paths, commands and unknown permission kinds are rejected. OS failure does not
become a permission success or tool-unknown lock.

Permission status and explicit probes use browser APIs locally. They neither call
Live/tools nor emit weather_location/save. No coordinates/media or permission grant
flags are persisted by the panel. Camera/microphone checks briefly open the system
default device if there is no active owner; all tracks are stopped, including late
grants. Location checks discard the coordinates. Feature controls still own ongoing
capture/sharing, and browser/OS policy can reject a request despite saved app settings.
