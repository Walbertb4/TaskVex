# UI/backend contract

## Updated 5.R8.6 — counter right-click menu and theme accents

- Range sliders and inputArrow now use --gold (theme); --c reactor status
  it doesn't affect them. The reactor and timer's own run/done indicators are retained.
- clockSelect is no longer a native OS select, but a summary in clockPicker details.
  clockList is the actual ID rows with secure textContent; selection local view
  process Enter/Space opens, Tab/ok/Home/End goes to lines; Escape/external clicks close.
  The context menu closes when the list closes. Row selection uses existing blip.
- The row contextmenu targets that ID, it does not delete another selected ID. clockMenu →
  Delete only the clocks.delete({id}) command with the current version clock_command
  sends. New module/second no status authority; task, policy clocks.write and
  Passes through exclusive clocks lock. The menu theme uses --gold/--bg/--fg.
- Core result verified=true contains snapshot+deleted_id; no success list
  It is not deleted locally. Unknown, busy/chat lock and again request_id protection are the same.
  Late Stop does not undo the completed deletion. When the last record is deleted, an empty view appears;
  New/start can open new registration again. Running/paused/finished timer and stopwatch
  can be deleted; The pending notification queue of the deleted timer is cleared from the snapshot.
- clocks.delete is registered in core only for UI; REST/Live ModelTools catalog
  did not change. If the model calls delete directly it will be rejected at the exposed-tool boundary.
- There is no multi-record menu in the browser-only single old meter; native ownership and
  In case of bridge loss, the rule of not returning to the second engine is preserved.

## Updated 5.R8.2–5 — automatic catalog, notification and sound settings

- nativeReady → loadLiveModels; taskvex-key-saved → same installer. single pending
  transaction, 65 s unknown lock and queue ID are preserved. Manual refreshModels button
  removed. The Error/empty catalog does not produce automatic loop or fixed named fallback;
  Re-opening the app or explicitly saving the key is a new try.
- The API key remains in the existing Windows Credentials store; store/localStorage/
  JSON is not included in the backup. conn.model is stored in the settings; registered in the backend catalog
  Returns the selection. If not available, the first API result is selected and the UI setting is updated.
  Model change requires completed=true and model ID confirmation.
- clock_finished: {request_id,id,generation}. UI alone idle, awake and valid
  Sends in catalog/link; native busy/sleep/unknown boundaries are also preserved.
  Backend verifies timer/finished/generation from the same Clocks object and checks each ID
  Accepts generation only once. Reset/old/made up target is rejected.
- Notification TextChat.run_live(notification=true) → same line PersistentLive/audio.
  The ModelTools catalog is empty; There is no mutation authority. Profile pLang/pIns
  used, no fixed boss answer/TTS. No fake user messages are added to the UI;
  The response appears with the stream and plays in the same liveAudio queue. Scoped session if required
  renovated by the current owner; The second Live connection owner does not open.
- The ending does not interrupt the busy round. The same poll tries pending notifications; separate timer
  There is no. Waits for sound notification in sleep, still the same after wake up context/reality
  If generation is valid, it can be delivered. Stop/Disconnect/model/key/sleep
  Resetting drops old pending events. After acceptance, error/Stop does not produce again.
  Mute turns off audio output, Mic Off turns off input only; notification on Mic Off
  can also play. Scanner-only alarm and “Timer finished.” It is limited to the text.
- noise 0–1000: current save scheme is the same. Local taskvex-noise-changed event is the same
  Sends minimum RMS=max(.001, noise/28000) to the microphone worker. 420 is the old .015;
  The adapted noise floor and tighter barge-in threshold are also maintained. This setting
  influences the speech candidate; browser noiseSuppression is on, PCM wire format is the same.
  The worker transmits the energy measured in 100 ms as 0–1000 meters, the old source result
  is ignored. When closing Off/source the indicator is 0; No separate measurement stream is opened.
- wake 0–100: the saved setting goes to KWS in the next sleep. Threshold=.45-.004*wake;
  50 → .25, 100 → .05, 0 → .45. Higher sensitivity may increase false arousal;
  physical calibration is user acceptance. When cache (word, sensitivity) changes
  is reinstalled; restart does not preserve old input ID/hit/PCM. noise/wake_sens
  Removed unsupported instant backend events; Persistence is a generic save.
- Idle sleep +/- same sleepDelay field/change validation and 0–300 limit
  uses; theme/SFX available. There are no emojis on the Google button; Google integration
  has not yet been implemented.

## Current 5.R8.1 — meter selector rollout

Previous 5.R7.2 user acceptance successful; In commit af834ff. clockSelect still
native select with keyboard and screen reader support; real ID/change contract
is the same. Theme variables determine the appearance of color/focus/ok. Lone user
In the change event, the current sfx.blip is executed; model focus/poll does not produce sound. new
preserves its own voice as a result of existing verified create. Backend payload,
data ownership and lifecycle have not changed. Timer end text/audio next
5.R8.2; Personalized voice notification has not been implemented yet.

## Current 5.R7.2 — multi-meter owner and view protocol

- main single Clocks instance create_core(clocks=...) and NativeBridge(...,clocks=...)
  Shares with. Native UI and model do not produce separate counter/clock states. Records
  in process RAM only; does not carry over to reopening. It is not added to the generic save.
- clocks.create: kind=timer/stopwatch, start boolean mandatory; label optional
  1–80 characters. Timer requires duration_seconds >0 and <=31536000; stopwatch this
  does not accept the field. Each create generates a new UUID; The same name does not overwhelm the old one.
- clocks.list: current full view without parameters. clocks.control: real id and
  action=start/pause/reset. start does not reset the running clock; resume paused
  It makes you do it. The finished timer starts with the new generation. Reset makes it ready; timer
  set duration, stopwatch returns to zero. Optional duration_seconds only
  In timer reset, the old time setting of the Set button retains its meaning; other action/genre
  It is rejected with . Missing ID doesn't change any of it.
- Uses this round's successful new ID list/create for model control;
  A previous reading of turn/replay is not considered new control evidence. In label uncertainty
  the model should ask for clarification; The tab user target appearing in the UI is not assumed.
- Model tools are in clocks.read/write policy, same clocks are in resource lock
  It runs via TaskManager. Stop cancels before writing; completed clock
  process/duration does not roll back the stream. New channel authorization was not granted.
- UI clock_command payload: {version:1,request_id,tool,arguments}; tool alone
  clocks.create/control. UI mutation is explicitly rejected in the pending model round; UI available chat
  It also shares its lock and does not open a new counter mutation as a result of model unknown.
  Success includes completed=true,verified=true,data. Post acceptance timeout/unknown
  locks new mutation and model requests until reopening; There is no auto-repeat.
- query_clocks is a view-only query with no parameters: same Clocks.snapshot
  reads directly, does not create TaskManager records for every 500 ms. The model is pure
  Its reading is also registered clocks.list tool. Snapshot: clocks,revision,sampled_at.
  Record: id,kind,label,duration_seconds,state,generation,elapsed_seconds,
  remaining_seconds (null for stopwatch). The internal start moment is not given to the UI.
- UI does not apply old sampled_at data; The old tool result is still in the current list
  Can focus ID. The result for the model create/control is the correct tab and record.
  selects automatically. The Dropdown and New button use the same registers; ID instead of sequence.
- Native UI displays backend time. Current notification SFX/completion id/generation
  once per second, the tick effect for the last five seconds is preserved. Your first opening is old finished
  recording does not generate an alarm again. If a measurement cannot be taken, “— / unavailable” is displayed.
- Native ownership latch does not open the old local interval in case of bridge loss. never alone
  native uninitialized browser-only mode preserves the previous single timers.js behavior.

## Previous 5.R7.1 — closing TaskVex from model

- `assistant.request_shutdown({})`, available desktop regardless of notes transfer
  It is under the authority of assistant.control. There is no OS shutdown, restart, executable/argument.
- Core result action=shutdown, scope=taskvex, apply_after=reply_playback,
  applied=false: acceptance is not window closing. The model only approves the plan.
- REST/Live uses the same assistant_control_request inference. Fail/Stop/
  unknown turn, another failed tool or old call replay does not produce new closure.
  If sleep+shutdown comes together, it is not implemented with conflicting_assistant_requests.
- UI remains the same only after successfully completed round and actual playback ends
  Current shutdownApplication if request_id and connectionRevision are still valid
  gets in the way. Stop, new interrupt, change connection/key/model or sound
  error drops the pending closure. The new message will not be started while waiting for closing.
- Shutdown button also uses the same function; native shutdown payload accepted
  It doesn't. It does not destroy the window without closing the host chat/source/core. Open rejection appears;
  Lost response or window destroy error unknown, no automatic repeat.
- Personalization pWake is saved in the settings.json profile. At the entrance of new sleep
  bridge returns this value to the local KWS; custom name change old engine cache
  rebuilds. Live alone-address distinction also gets the same profile value.
- In Multi timer/stopwatch 5.R7.2; Today's native single UI behavior is preserved.

## Previous 5.F4 — local wake variations

- Personalization pWake remains the selected address; new setting or payload
  There is no. Vex/Veks/Rex family caters to KWS and Live alone with single wake_spellings definition
  connected to its control. Veks phonemes are the same as Vex; Proper names are not expanded.
- Single native KWS engine loads Vex and Rex phoneme lines; all the same WAKE
  It uses the result, current volume limit validation and request_id acceptance.
  There is no new microphone, no model session, no tool player or network sleep listening.
- The exact transcript is wake_only if it is addressed to the family. “Rex show me my notes”
  The sentence followed by like goes to the normal pattern; The task is not swallowed. Private Computer
  Just mentioning Rex in your profile is not considered an empty address.
- X/ex/eks is not supported standalone. This is a limited list of acoustic variations;
  It is not a router that interprets application commands with sentence patterns.
- Current Mic Off, Stop/unknown, old wake_feed ID, cache on profile change
  Refresh, wake limit and host approval rules have not been changed.

## Previous 5.R6 — batch note completion

- When the grade transfer is approved, `notes.complete_many` is added to the REST/Live catalogue;
  notes.write and the same notes resource lock are mandatory. There is no new channel authorization.
- Parameters only ids (non-empty unique real ID list),
  expected_snapshot and boolean done. True completes, False reopens.
  The text is not changed en masse; ID, date, sequence and ui_migrated are preserved.
- The model is the exact result of the successful `notes.select(cardinality=many)` in the same round.
  uses the set. Lower/upper/empty set, single uncertainty propagation and legacy selection
  is blocked. Core does not replace any changed snapshot or missing target.
- Next to the single `_commit` and the verified notes/migrated after full readback
  updated_ids, updated_count, done returns. The number is the targeted records; already
  This includes records that are in the same state. Pre-write Stop protects, late Stop
  does not undo the actual result; UNKNOWN readback loss, no automatic replay.
- Backend reading after the current notes.* result refreshes the panel. New save or
  No note_done echo, separate UI executor or single update loop added.

## Previous 5.R5 — structured note selection / bulk delete

- Note that after transfer confirmation, REST and Live are the same notes.add/list/select/update/
  Sees the catalog delete/delete_many. select notes.read, mutations notes.write
  requires. initialize/replace does not open to model; New channel authorization was not granted.
- `notes.select` gets kind=ids/text/contains/latest/all, cardinality=one/many;
  The corresponding ids/text/count field is required, the incompatible/extra field is rejected. none
  The request statement is not parsed with regex. Result notes/cardinality/selection_ready/
  Includes snapshot. Snapshot data is a fingerprint, not an authorization per se.
- Full ID and expected_snapshot in single fresh selection for Model update/delete
  sends. Full ID set of multi-select for delete_many + expected_snapshot
  It is mandatory. Missing/excess/double The text is not started with ID and indefinite selection.
- zero/multiple in one selection after match, unsuccessful selection or changed data
  Mutation is prevented with the new predicted target in the same round. New user description
  opens a new round. The intermission transcript does not count as a new round. Old select replay
  and rereading the result does not produce new mutation authority.
- Core worker compares the snapshot again before writing; notes_changed or
  In the missing target, transaction single/batch does not change any records. Latest selection
  unknown date, equality exceeding the limit and over-requested quantity are rejected.
- delete_many uses single `_commit` write and full readback. Result deleted_ids/
  Contains deleted_count and last verified list; ui_migrated is preserved. Stop
  no pre-write, late Stop does not undo the actual result; readback loss UNKNOWN.
- The panel is refreshed with a single backend reading after the current notes.* results;
  There is no new save/note_del cycle. Native single UI CRUD replaces legacy ID protocol
  protects; In the narrower model contract, snapshot is mandatory. mutation selection
  exhausts his evidence. Parallel file writers other than core are not supported with the UI.

## Previous 5.R4 — common sleep request tool

- Added `assistant.request_sleep_mode` to the model catalogue; mode alone
  once/persistent/off, additional parameter prohibited. Independent of grade transfer approval
  desktop is `assistant.control` authorization; Notes remain closed until approval.
- Core tool returns only `mode/apply_after=reply_playback/applied=false`.
  The successful mission is an acceptance of this request; It is not claimed that you fell asleep. of the model
  Removed `sleep_intent.py` and regex decision path interpreting the transcript.
- REST and Live use the same validated inference. only successful
  The new call in the round becomes report fields sleep_mode/sleep_requested.
  Previous round mission ID, error/Stop/unknown, failed tool or conflicting
  The modes do not create new sleep transitions. The success statement alone is not enough.
- Existing UI response/playback ending and connectionRevision/Stop/handoff protections
  uses; then the same sleep_start asks for real host acknowledgment. new sound
  There is no queue, regex routing, second model session or separate executor.
- Local Sleep/Wake and idle timer do not call model. Normal sound during sleep
  Again it goes to the local wake engine alone. Acceptance of the actual dil/account remains open.

## Previous 5.R3 — Sleep after Vex's response

- Removed local_sleep/model=local short circuit and fixed text/WAV path.
  A written or voiced open sleep command is answered on the normal Live transcript/PCM line.
- Successful model completion via actual input_text (text sent in the text)
  return sleep_mode and sleep_requested; These do not mean that you are asleep.
  UI first waits for the current liveAudio.finish result, then the same sleep_start
  asks for acceptance. The off preference is also applied after the model response/playback is completed.
- Stop, intervening new entry, connection change, audio/model error or unknown
  It does not execute the pending command. Tool bid on sleep command without initiating side effects
  is rejected; No sleep tool added. Response words are not fixed in the code.
- Sleep button, normal idle timer and automatic return after mission
  The model does not ask for the response. The only current owner of microphone/Live/playback is retained.
- “as” is not mandatory in TR modal address: “go to permanent sleep”
  becomes persistent. Switch on/activate, EN stay/remain asleep, keep sleeping,
  permanent/persistent sleep mode and disable/turn off/exit variants are the same
  passes through the complete-sentence parser. Question/negative/quote/addition takes duty protection;
  It is not guaranteed for unlimited natural language or other languages.

## Current voice protocol 5.R2 — manual activity

- Replaces the previous automatic VAD + audioStreamEnd selection in audio setup
  automatic_activity_detection.disabled=true is used. Single LiveInput owner
  activityStart becomes ready after delivery; activityEnd after sequential PCM
  sends. audioStreamEnd is not sent. The setup of the Written Live turn does not change.
- Data:null ending and local 700ms silence from UI are preserved. Definitive transcript
  or the same owner is missing if the actual output/tool closes the input stream early
  sends activityEnd; During the stop, no new end transmission is started.
- The report contains input_boundary='manual_activity'. UI on timeout
  input end: Shows sent/missing and speech chars; to get to know the text itself
  There is no need to explain. The 25 s limit was not changed; Timeout is not success.
- REST, replay, model fallback, GoAway/resumption and note permissions
  not changed. Real microphone/provider acceptance is clear; undergo synthetic transport
  It does not prove the exact cause of the user's error or that it has been completely resolved.

## Previous 5.R1 — open audio end and actual audio confirmation

- Worklet `arm-end` is sent only after backend input ready confirmation.
  Next/current 700 ms silence input is EOS. From all pending PCM deliveries
  then data:null goes; It is not the completion of a stop or pattern response.
- EOS previously on LiveInput closed with final input_transcription.finished
  If it is not sent, the sender sends it to the same socket owner after it is cleared.
- Wake→Live source error moves to normal path microphone/Stop. definitive terminal
  report and temporary loss of queue/transport after the same connectionRevision
  A maximum of two empty resource preparations are allowed; Old data is not sent again.
  Permission/device/unknown and user Off preference cannot be overcome; why appears/logs.
- English internal control text in the local_sleep report as a response to the user
  not printed. Successful selection for host sleeping=true, off for once/persistent
  After closing the UI confirms the selected pLang TR/EN text and fixed WAV.
- WAV from current LiveAudio owner, selected output device/gain/Mute/Stop plays with;
  late fetch/decode cannot play the result on the new request. Automatic post-task return
  sleep confirmation does not repeat. Assertion file error does not revert real host mode.
- Wake model cache holds weight; Active old ID/PCM/hit is not kept. word
  or engine type change/failure requires new engine. There are no new public events.

## Current 5.F3 — sleep intention

- sleep_mode once/persistent/off format unchanged. Public host parser is no longer available
  TR enter/switch/sleep and EN enter/switch/go/stay/return variants in full sentence
  recognizes Address is not mandatory; please/please, spaces and letters are normalized.
- “go to sleep permanently” is persistent; not permanent preference to disk,
  is the chat's current post-task sleep-back behavior. sleepDelay is independent.
- The question mark is no longer deleted; quote/negation/addition is not passed in the job parser.
  No host migration until the voice candidate is finalized; If the candidate changes, the pending output
  is left back. The parser result still does not replace the sleep_start confirmation.
- Sensing local wake word/phonetics, Stop/unknown and resource rules are the same.
  Free is not all natural language, but limited and tested TR/EN full sentence grammar.

## Current 5.F2 — source liveness and latency measurement

- Subsequently, the suspended/interrupted context is resumed once on the same resource;
  Audio_context_unavailable hardcode present error if not working within 1s
  goes to the line, the source is turned off. Mic On/Off user preference remains unchanged.
  release closes old handler/timer; The late result is not applied to the new resource.
- input_sent_packets (number of completed SDK PCM sends) to the live report,
  input_first_sent_ms / input_end_sent_ms (SDK first sound/EOS), received_events /
  last_received_ms (events reaching the probe) is added to input_final_ms. Durations
  ms from turn start, otherwise null; Voice or user text is not included in these metrics.
- before_input_final or before_input_final in wait_phase stream for live_idle_timeout
  after_input_final, provider_reply on other input. UI PCM/events/stage
  adds it to the error line. Timeout success, safe replay or sure provider
  It is not evidence of malfunction. 25 s/120 s, Stop/unknown rules remain unchanged.

## Current 5.F1 — final login end and sleep acceptance

- sleep_start rejection/success/engine-error results completed:true and true
  carries sleeping:boolean. ok:false, sleeping:true
  its host is in a dormant state; ok:false, sleeping:false are absolute rejection.
- UI preparation sleepPending/Preparing keeps with sleep; without host acceptance
  It does not show SLEEPING and Wake. 15 s deadline or missing/uncertain in reply
  unknown lock is preserved. Stop/Disconnect/model replacement pending control
  does not count as withdrawn; A late reply cannot open a new resource. Mic Off preference is retained.
- finished=true input_transcription turns off accepting old LiveInput; sender
  Cancel only PCM sender. Continue on track to receive result Model/core
  It does. The blank final transcript package is also the introduction ending; It is not thought-only.
- Local 700 ms silence after wake-to-live is activity display only;
  It does not discard the PCM and turn off the source. The current package cap of 15 s/150 continues.
- If the exact transcript is only the word wake set wake_only:true/ok:true/
  completed:true returns; the tool is not executed and the actual mission is not considered finished.
  In persistent mode, the UI waits for the actual request rather than going to sleep immediately. different phonetics
  words and flexible sleep intention are separate steps. The provider has no certainty
  Failure to provide a transcript is still subject to the incident timeout limit.

## Current: two independent sleep behaviors — replacing the previous time binding

sleep_mode=persistent is not a timed countdown: it is called in the only interaction
model/tool and after playback is finished the UI is the same enterSleep/sleep_start
He falls asleep immediately with his phone line. In this mode, the barge-in listener for the response is not opened and the old
The reply listener is not protected. without completed:true, unknown/active is on duty,
There is no backlinking with the old connection report or just accepting the cancellation.

sleepDelay is the idle time in normal speech only; default 10, range 0–300
full second, 0 off. When the time is up, it activates a one-time sleep, persistent preference.
doesn't open. Idle timer is not used when persistent is on. On off only persistent
closes the profile; It does not change the normal timer setting. On/Off microphone preference
remains independent of these two behaviors. Setting/snapshot/backup/reset contract
It also carries sleepDelay=0. The host control agreement once/persistent/off is unchanged.
The commands are still from the full Turkish/English list; no name requirement, flexible intent
and alternative local wake pronunciations were not added in this step.

## Current permanent sleep preference and duration

Local full sleep control now sleep_mode: once | persistent | returns off.
sleep_requested is true, off for once/persistent in the successful check report
is false for . Current local_sleep result, Stop lock and tool_results
is protected. Typed does not call a control provider; voice control only full transcript
Once finalized, it is covered by the host. Control is not tool authority.

UI persistent/off gets its result only from the current success report. permanent
preference remains in RAM; a one-time Sleep will not delete this. New Chat/exit/on off
Clears the preference. Single timer, current connection and check its own revision
Only idle uses enterSleep in Live. Talk/tool/play
ending/unknown and the device barrier is not bypassed; Stop/Disconnect/source cancellation old
overrides the timer. Mic Off preference does not turn off permanent mode and cannot be turned On.

sleepDelay is 1–300 integer seconds, default is 10, in Settings → Audio.
Backend permission setting scheme and UI default/save/load/snapshot/backup/reset
included in the streams. The duration is recorded, the persistent sleep preference is not written to disk.
Mic On/Off calls the same sfx.blip as the camera once on each click; effect
settings are applied. Source: Mic / PC Audio / App UI tags in the future
is a resource contract; Only microphone capture works on the native side.

## Current microphone and input end — replacing previous display convention

micB only user choice Microphone On/Off; light/aria-pressed alone
Monitors the microphoneEnabled value. Connection/sleep/error/retry/unknown button
does not change its label or preference. These states remain separate textStatus/log;
background permission, device and indeterminate result locks were not removed. Off alone
closes the input, sends data:null/EOS after the PCM sequence; The response does not stop.

700 ms of silence after the wake cycle triggers the end of the entry. 15 s/150 packs
The limit is only the entrance end, including the wake front bumper; Stop or microphone Off
It is not. EOS will not be sent until the final PCM approvals are completed. thought-only model_turn
does not close the entrance; true exit/tool/end closes. Full sleep transcript candidate
output is kept at most 64 event/2 MB; Once finalized, local sleep result, if there is any question
sequential output processing is applied. The old audio or tool will not be replayed.

## Current local wake fault and recovery agreement

When the `sleep_start` motor cannot be installed, `code: wake_engine_unavailable` returns.
`wake_feed` errors raw exception-free `wake_alignment_failed`
(no reliable volume limit), `wake_packet_rejected` (row/base64/PCM verification)
and `wake_engine_failed`; resource is released, sleep is preserved.
UI source errors are also permission/device/worklet, tail, front bumper and rev
Declared by hard codes. Unknown code falls into a secure global delivery error.

UI only on local queue/obsolete buffer/alignment/delivery error, sleep on,
New 250ms delay for up to two times while Mic On, idle and result are determined
prepares resources. Each time the old token and PCM are canceled; Live/model/tool
There is no replay. Off/Wake/Stop/Disconnect/pagehide or revision replacement old
Overrides timer/callback. Permission/device/installation/package/transfer error is automatic
It is not repeated. On Sleep can retry local blocking; Disconnect and
The Off preference is preserved with the unknown block. `Microphone On · Retrying` / `On ·
Blocked` and tooltip show the reason; aria-pressed is the user's On preference.
It has the same tight tolerance as the Veks address Rex/Max in full sleep expression.

Sleep admission fix: colors.sleeping stored like other reactor states
is a color; The SLEEPING state is separate from IDLE. Open Wake, local wakener
Clear the remaining micBlocked error and re-control device/permission.
does; Microphone Off and indeterminate result lock are preserved. Host's narrow sleep
Fall asleep matching and address Rex/Max in front of the phrase full sleep alone
also accepts; these are not fuzzy matches for the general perception of command/wake.

## Current: one-time sleep and local wake PCM

pWake is a 1–64 character/1–3 ASCII English word in profile; default Vex.
It is recorded, it is not given to the model as a system instruction; local engine next
Further confirms dormant dictionary/phoneme support. Sleep preference is in RAM.

- sleep_start(): ready/idle turns off host Live, preserves RAM chat, local
  Creates WakeWord; Returns {ok,completed,request_id,wake_word}. fail
  Sleeping: remains true in the engine, there is no automatic Live fallback.
- wake_feed({request_id,sequence,data}): single base64 3200-byte PCM16LE/16kHz
  package. The sequence increases from 0. {ok,completed,detected,start_sequence} returns;
  start_sequence is the 100 ms packet index of the start of the hit. Old ID, wrong
  queue/encoding/overflow is rejected; The corrupted resource is released, sleep is preserved.
  detected:true is just the pending hit; host sleeping=True remains. UI own
  Waking up is not complete without verifying your front bumper.
- wake_close(request_id): leaves only the matching local resource, does not remove sleep.
- wake(): idle/ready manually wakes the host and releases the local resource.
- wake({request_id}): just the UI acknowledgement of the current, detected hit. Buffer
  Sent after verification; Live is not required before completed:true.
  Old/closed/unapproved ID is rejected. wake_close cancels the pending hit
  and keeps the host asleep. This acceptance does not interfere with the Mic Off preference.

Live audio start/clip with sleeping code on host after sleep_start acceptance
is rejected. A hit or plain text Live request accepted by the UI removes this block.
The UI also maintains a separate sleep gate; ordinary energy does not count as awakening the candidate. wake up
button/typed is the request explicit user action. New Chat clears sleep status.
Mic Off releases resources while sleeping; On again turns on local listening.

Typed tam sleep expression local_sleep/sleep_requested:true with report without modeling
is welcomed. In the audio statement, only the finished transcript or the actual end of the turn
full expression is accepted; Half a question is not a command. Tool with side effects has started
It does not translate into sleep. The UI implements sleep_requested after the actual end.
This is lifecycle control; The second tool worker/CRUD/registry line was not added.

The current liveMic source sends only local packets with waitForWake. waiting 1 s
There is IPC and 3s front buffer limit. The PCM before the start of the hit is dropped;
then switches to the existing LiveInput line from the same source. Insufficient/old buffer
does not run commands by clipping; capture obstacle is shown. late callbacks
It is protected by ID micRevision/session. 60s model stream is at the refresh limit
wake can escape; physical acceptance is obvious. There is no auto-repeat sleep/duration setting.

R0 fix: timestamp is not directly global sequence. Maximum 3 s on Hit
the local window is verified with the same KWS on the stream whose origin is known; internal reset
The token is controlled from the duration/silence margin. Artificial forward-looking
silence is local verification only, it is not added to the PCM output. verified global
the border must again be located in the 3s front buffer of the UI; The old audio is not trimmed and sent.

## Current minor fix — display

There is no new host event/payload. paintMic ten class is now available model native/Live,
On is selected and source/unknown indicates user preference without disability;
Short cycling of the physical track during Stop does not turn off the light. Tooltip welding
It separates the preparation from the actual capture. Off/Disconnect/permission/device/unknown barrier
extinguishes. The physical recording/Stop/re-listening protocol has not changed.

setConnectionStatus('idle', text) is the internal UI state: neutral battery net idle,
isConnected=false, reconnect timer is cleared; open socket is not asserted.
Stop or completed:true and not unknown on the current matching connection
live_interrupted may go into this state. General errors remain red off.
There is no transport error in normal interrupted log; unknown, old identity and
Failed cancellation is not hidden. idle badge click does not initiate reconnect.

## Current: temporary memory and new_chat

The temporary chat RAM save belongs to TextChat; into UI localStorage/settings/backup
not transferred. memory_restored:boolean in live turn report limited to new socket
Indicates that history data has been transferred. UI does this "recent conversation restored"
It can show as; It is not a full recall or tool result verification.
History only JSON and turn_complete:false in the model role in the fresh connection
goes as ; used/resumed is not duplicated in socket. Current commands remain separate.
There is raw PCM/tool payload and no new tool run for restoration.

`new_chat` is only accepted in TextChat ready host/idle without payload. Success:
`{ok:true, completed:true, memory_cleared:true}`. If there is an active chat or
If the closing is not verified, a rejection is issued; RAM is not cleared while busy. UI user first
prompts for confirmation, then login/new locks chat controls until completion.
15 s confirmation exceeded or lost transport becomes unknown; Late reply cannot write to new chat.
On success, msgs and stream records are cleared; notes/settings/key is protected.
Unknown command cannot unlock new chat button. Old PCM/transcript
receivers are left with resetLiveAudio. Microphone On preference in new conversation
is protected; Capture is not started during cleaning.

RAM limit is 12 turn/16.000 JSON characters, 2,000 characters per text;
old round is thrown away, there is no automatic summary API request. Stop/Disconnect/model and
Profile switching preserves recent history. New Chat, app closure or API
clears the key update. Past tool results as old data
is labeled; The current list/target control is the same as the new notes.update/delete.
No memory connected to REST. The PMem domain is still not a permanent memory engine.

## Current: REST read_reply and Microphone Off

`text` returns success report text/tool first. Native UI displays this text immediately
shows; then only `{request_id:string(1..128)}` to the `read_reply` event
sends. Matching the ready host and the last successful REST response is required; additional space
and free text is rejected. Incorrect ID does not consume the pending response. correct answer
consumed once; new chat/Stop/Disconnect/closing drops old text.

Audio to existing audioChunk receiver in the same TextChat lock, with the same request_id
PCM16LE/24 kHz/mono goes. Result `ok`, `completed:true`, `request_id`,
Carries `speech_model`, `audio_bytes_forwarded`, `audio_error`. As a result of the stop
`code:stopped, stopped:true` is added. The initial text/tool report remains separate; TTS
error does not count them as failed or rolled back. UI notes from backend
reads; There is no second note mutation/save. When Mute is on, the new TTS call is skipped;
While playing, Mute silences the current audio. Mute default on dedicated speaker error
There is no device fallback. Text/tool/TTS does not auto-repeat.

Stop acceptance `completed:false, waiting_for:speech_response|speech_completion`
may; UI will not be unlocked until synchronous HTTP is finished. Audio stage UI limit110s;
late PCM cannot write to new response with old request_id. TextChat ownership and unknown
The result lock is preserved. TTS is a single separate API request; tool/declaration does not exist, store:false,
Kore, gemini-3.8-flash-lite-tts; model to the list TTS is not added. Limitler:
20,000 characters, 20 s HTTP, 60 s PCM; bot/CLI is silent without calling read_reply.

Mic Off, input end with `live_audio_feed({request_id,sequence,data:null})`
reports. PCM and EOS are sent serially; EOS only once, after setup confirmation
goes. The hardware shuts down immediately; Live response/transcript/output is not cut. Stop separate
is the way to cancel. It is not converted to Stop during Off setup. Sent audio back
not taken; If no sound is received, the provider may not respond. There is no REST microphone path.

## Current interim fix — Microphone On/Off

There are no new events or payloads. microphoneEnabled UI session preference, micBlocked
resource barrier. Error Stop/model does not turn the preference Off. completed:true and final
After host termination, if the scope has not changed, the On preference waits for new conversations locally.
The diagnosis of Error/Stop is retained. The old voice/tool/model message is not repeated; silence
It does not create an API request. Transferring the pending new voice before the old task is completed
and unknown lock rules are the same. Off selection is not turned on with late callback/model-ready.

Mic button Microphone On/Off and aria-pressed with preference, real with ten class
Shows capture. It can also be turned Off in Unknown; Does not exceed ten command locks.
There is no automatic permit cycle at the Permit/device/login limit barrier. Disconnect or
key exchange leaves the source; It does not change user preference. ready model
Can prepare notification or open Off→On again; Uncertain is still an obstacle.
The choice is in RAM; No permanent settings, REST microphone paths or new permissions added.
Live model/mod availability continues. Silent capture is idle, speech is listening.

## Current: step 5 — activity, closure and duration diagnosis

There are no new public events. AudioWorklet's local activity:boolean message is lonely
is rendered on the current liveMic source. prepareStream(onError, deviceId, onActivity)
and speaking getter is for display: ready silence idle, speaking listening,
In the active round, 700 ms of silence is thinking, the output PCM is speaking. This notification
does not end the server turn, tool/command does not start it. The old resource callback is ignored.

PersistentLive.input adds failed:boolean to the feed return; closed/old in request
failed:false becomes true in corrupted queue/overflow. emit normal failed:false/closed:true
It does not log the rejection, it preserves the ok:false return. Matching only in model call
request_id + code:stopped + stopped:true + completed:true + unknown absent
the result is normal stopping; unknown or true errors are not suppressed. Cancellation acceptance
Does not open controls. On normal feed closure, the old microphone is released; The answer that rings
His new microphone remains untouched. There is no new tool path/worker or automatic replay.

Common addLog last 200 records/2.000 characters, textContent and secret masking
implements; schema warnings are also limited to size/adet. The transcript is not logged.
Live backend uses 25 s event silence / 120 s total round limit:
live_idle_timeout and live_timeout codes carry the diagnosis of timeout_seconds.
UI createPendingOperation.begin(deadline) Live 210 s / REST 240 s waits.
UI expiration is not cancellation/completion; The old response cannot open the new request.
The previous microphone, buffer, playback and instrument size limits are the same.

## Current: step 4 — saved model preferences

There are no new public events or payload fields. save/saved/completed verification
is the same; At startup of NativeBridge text/live_text/live_audio/live_audio_start
Takes an independent snapshot of the disk profile with _load_settings. If the profile cannot be read
profile_unavailable/completed:true/ok:returns false; model/tool does not initialize.
At this point completed means the rejected request is over, registration or model success
It is not. The internal profile keyword of TextChat and adapters is not a public UI field.

model_instruction.py only transfers the pLang/pIns fields to the common system instruction.
translates. tr/en is fixed mapping; missing/unsupported old value tr is assumed.
It remains at the 16,000 character limit in the pIns setting scheme. Selected response language and
tool/result/cancellation rules prevail over personal style instruction. Profile text
is not added to results/diagnosis/logs; Sent to SDK. Other profile fields are not sent.
REST retry/fallback uses the same instruction. Live scope hash of the instruction
covers; The effective change clears the old resume/call scope in the next message,
returns context_reset_reason:scope_changed. The snapshot of the active response does not change;
There is no automatic replay or second worker. Junk/uncommitted field change
It does not break the existing connection. UI Save profile closes only when the registration is verified.

The UI Response language tag indicates that recognition remains automatic. Provider
Since native audio does not support language_code, such a field is not sent;
this is not an STT language lock. Model integration of other profile areas,
REST audio output or new track is not part of this step.

## Current: step 3 — local candidate and microphone handover

Backend event/payload is unchanged. waitForSpeech(callback, replyPlaying=false)
requests 200 ms/0.015 at idle or 300 ms/0.025 base filtered RMS during response;
If it is three times higher than the non-candidate background, that threshold applies. Original PCM
and 500 ms front buffer remains unchanged. autoGainControl:false is the device preference.
continueListening() only returns the wait that has not yet been triggered track/buffer
gets into idle mode; caught/active does not reset the flow. app.js target id and
Leaves the mode in the same synchronous block after the last await. Audio error/Stop/unknown/
This continuation does not apply in case of scope change; the source is turned off. There is no new tool/executor.
Barge-in still awaits sequential Stop and actual finish; The context can be reset.
This energy gate does not guarantee physical echo or speech classifier.

## Current: instant Live transcript with request ID — step 2

New permission notification: window.vex.liveTranscript({request_id,role,sequence,text});
jarvis alias is the same object. relay u/j; positive integer increasing in sequence round,
text is cumulative snapshot (not delta). Entry maximum 20,000, exit 32,000
is character. request_id comes from trusted host; The model cannot choose a new target.
UI gives boolean delivery confirmation. Old/finalize received request or repeat/unordered
The packet is rejected. Reports backend display error with transcript_error,
Does not repeat tool or model call. Text outside normal chat file/log
not added; Audio playback line and tool permissions have not changed.

live_transcript.js keeps one balloon per role; snapshot with textContent
new. The late entry is placed before the response of the same round. The final report is a backup,
The second bubble does not produce. Stop/barge-in freezes the exit bubble; next old
The snapshot is consumed and not shown. Interrupt Interrupted, error Incomplete, ambiguity
Result is the unknown tag; These are not cases of instrumental success. Scope change
turns off the receiver. The unknown result does not unlock the current command.

Provider parts are displayed as they arrive; native voice recognition and voice/text
No word synchronization added. Native audio buffer not yet sent to the API
There are no fake transcripts for. Legacy streamMsg(c,t) compatibility is preserved; new live
The line does not use anonymous streamMsg. The REST view and note CRUD are unchanged.

Evidence: ../../../docs/stage5-transcript-full-native.json — 10/10 hidden native
phase has passed. 0 in 742 pytest, 5 Node suites and changed files Python/native
Pyrright error. Real account and physical voice acceptance remains open.

## Previous: conversational interruption / round robin transfer — October 22, 2026

Microphone local speech from the first accepted PCM part of the response
waits for the candidate. liveAudio.stop(old_request_id) queue when new audio is detected
discharges; The current stop_task is sent to the active model. If the lonely voice is playing
host is already finished and no second Stop is required. New sound in RAM for up to 3 seconds
is kept. New live_audio_start before host completed and ok/stopped result is finalized
not sent. In unknown or waiting tool, the entry is blocked and the controls remain locked.

This is the sequential application of Stop → actual finish → new round; on the same socket
simultaneous multi-turn input/output is not. Can reset active Stop context;
The UI shows normal context_reset_reason information. There is no new backend event.
Existing transcript/identity/policy/TaskManager/not transport ports are retained.

Pending audio is bound by old request_id, micRevision and connectionRevision.
Stop/Pause/Disconnect, scope change, device error, overflow and ambiguity
invalidates the transfer. Although the truncated old PCM is checked out in the same active request
thrown away without being stolen; old id as normal after new request starts
is rejected. While the old request is being completed, the microphone clearing will prevent the new conversation from starting.
Can't turn off buffer. Realized tools are preserved by backend reading and are not duplicated.

Controlled acceptance: 737 pytest, 4 Node suites, 0 Pyright bugs and 10/10 native phase.
Evidence: ../../../docs/stage5-barge-in-full-native.json. New native scenarios
active/only playback cycle, preservation of completed note, buffer with Disconnect
confirms that it should be discarded and that no new round should be opened with an uncertain outcome. real account and
physical echo/noise remains acceptance open.

## Previous: automatic local listen and return after response — October 22, 2026

If Native is ready and the Live model is selected from the API catalog, the microphone is turned on automatically.
The user does not press Mic during every conversation; button Pause listening / Resume listening
in its function. Catalog upload is the current explicit user action; model selection
Its success is signaled by the taskvex-live-model-ready native UI event. event provider
It does not mean that the connection online or the tool operation is successful.

AudioWorklet waits for audio candidate locally: 2 consecutive 100 ms blocks for RMS >=0.015,
maximum 5 blocks front bumper. In silence, no API messages or new model turns are generated.
The existing live_audio_start/feed line is used in the audio candidate without losing the front bumper.
Setup buffer 3 seconds, send queue 1 second, backend queue 2 seconds,
total entry is 15 seconds. Overshoot is not silent trimming/success, listening stops.
Intent resolution of model, server VAD, note transfer/transcript/policy/TaskManager
gates and available payloads remain unchanged. No new public backend event has been added.

After the audio queue of the successful response ends, automatic listening is turned on again.
During response, the input is closed; There is no barge-in. Text message local standby
It does not compete with. Stop, Pause, Disconnect, key change, device/permission/provider
error and uncertainty stops automatic mode; Resume prompts to restart.
The microphone does not turn on before the model change is ready confirmation; It does not remove manual Pause.
Permission rejection does not remain on the preparation letter. The permission window may be shown for the first time;
Automatic opening does not mean bypassing the platform's permission. real physical
microphone/noise sensitivity and reopening permission acceptance has not been done yet.

Last moderated acceptance: 737 pytest, 4 Node suites, 0 Pyright bugs and 10/10
hidden native phase has passed. Evidence: ../../../docs/stage5-auto-listen-full-native.json.
Voice and provider are synthetic; not actual hardware or paid API adoption.

## Previous: live mic / monologue VAD — October 22, 2026

Mic obtains permission through user gesture; AudioWorklet talking mono 16 kHz PCM
It sends in 100 ms packets. VAD automatic, silence setting 700 ms; Finish & Send
not necessary At the first tool/model response the input is closed. Barge-in, spontaneous repetition
There is no listening or wake word. The stop waits for the real end; audio remains in RAM.

New events via a single public event method:

- `live_audio_start:{request_id}`: long Promise actual turn result;
  ready, current catalog/model, notes_ready and single chat lock are preserved.
- `live_audio_feed:{request_id}`: short ready query; only matching active
  The stream returns ready:true. No sound is sent before setup.
- `live_audio_feed:{request_id,sequence,data}`: sequence starts from 0; data solid
  base64 is exactly 3,200 bytes/4.268 characters PCM. data:null is the open end of the stream
  (SDK audio_stream_end); Order control also applies here. UI normal
  leaves the ending to the server VAD. Repeat/skip/overflow stops the turn.

Total login 15 seconds, backend queue 20 packets, UI queue 10 packets
is limited. The late package cannot be moved to the new request. The tail is just the carrying limit;
The second tool does not have a worker or Live owner. First sound/closed introduction/conclusion,
Stop and device error turn off the UI's own microphone. Note refresh same backend
is to read; The second mutation/save does not produce. Old live_audio clip contract
remains for compatibility; native Mic uses the new path. audioChunk output is unchanged.
The actual account/VAD and physical microphone are awaited user acceptance. last automatic
accepted: 737 pytest, 4 Node suite, 10/10 hidden WebView2 native phase and 0 Pyright
error. Evidence: ../../../docs/stage5-stream-vad-full-native.json. Native audio
its source and provider transport are synthetic; It is not the actual audio/VAD adoption.

## Updated: automatic audio device list — October 22, 2026

Scan button removed. queryDevices() reads only with enumerateDevices;
nativeReady calls settings panel opening and devicechange. Start listing
It does not keep note synchronization waiting. Listing never calls getUserMedia; permission
and microphone activation is only on the Mic button. After Mic permission is successful
device/names is displayed, which can be accessed by refreshing the list. Old ask parameter and
temporary permission stream removed; The browser-only query_devices transport is preserved.
Native dIn/dOut store/onchange authority unchanged, auto list new preference
or does not generate a save event. Save Settings confirms the permanent selection. Before leave
There is no fake listing or automatic permission prompt for device/names that the platform hides.
Continuous listening/VAD is discrete step. Device tests are user approved.

## Update of Native UI files — October 22, 2026

Native host has the same 127.0.0.1:DEFAULT_HTTP_PORT origin and storage_path
It provides the existing Bottle UI with WSGI support while preserving it. Varies per opening
The asset prefix is applied to all relative module imports; no-store real
The file is in the response. Prevents old JS/new export interference. User note,
The setting, localStorage, or identity store is not deleted. public event(name,data) and
Allowed backend notifications have not changed. Browser-only direct HTML/localhost
the opening method has not changed; No new framework or second server was added.

## Previous slice: Live audio device selection — October 22, 2026

The user reported that the start/end microphone tests were successful. Native dIn/dOut
selection is now the WebView MediaDevices ID; It is not a hardware index. open
Scan button temporary getUserMedia({audio:true,video:false}) permission, enumerateDevices
and manages the closing of its own temporary tracks. The camera does not turn on. Browser-only
query_devices/device return protected; to the backend for native audio device
An unimplemented device command is not sent, and a new backend method is not added.

The choices are in the current store.devs: System default is registered as 'default';
The private ID is read as an opaque string with getAudioDeviceId. old integer
indexes require Scan/selection; The numeric string can be the actual device ID.
The change is written to the UI cache; Save Settings available verified native save
makes it permanent with its tail. The lost device preference is preserved and cannot be used in the list
is shown. The choice applies to the next response record/Live; active flow does not change.

The third parameter of liveMic.start is the selected deviceId; special device exact
It opens with restrictions. liveAudio.begin(request_id,deviceId) is now awaited;
The special output is prepared with setSinkId for a maximum of 3 seconds. Stop/Disconnect/setup
If the replacement interrupts the preparation, the model request will not be sent. Unsupported/inaccessible
sink or device removal returns output_device_unavailable; silent fallback
There is no. liveAudio.fail local verbose safe error code global backend audio
It does not crush it with a delivery error. Text/real tool results are retained.

Two modules leave only their selected resource in devicechange; list access
failure alone does not constitute device removal. After Native Scan
devicechange refreshes the list without asking for permission. Device IDs browser origin/permission
is within the scope of; Scan may be required again in new origin. SFX to selected Live speaker
immovable. True multi-device adoption is available to the user; There is no permanent VAD.

## Previous slice: open start/end microphone — October 22, 2026

User confirmed that Live audio output was heard. Next slice microphone:
`live_mic.js` turns MediaRecorder on with just the open button; up to 15 s/1 MiB RAM
slipped. Finish & Send finishes recording and closes the tracks and OfflineAudioContext
with mono/16 kHz/16-bit produces PCM. No audio is sent to the network until the recording is finished; duration
Expiration, Stop, Disconnect, key/model change and pagehide delete the record.
If permission is granted late, the canceled request does not leave the track vulnerable.

New event `live_audio:{request_id,mime_type:'audio/pcm;rate=16000',data}`;
The data layer is base64, up to 640,000 character/480.000 bytes, and 16-bit aligned,
is at least 0.1 seconds. The host maintains the current transfer port catalog/model/not.
A single TextChat/PersistentLive/ModelTools line is used. from the model
`input_text` is shown as a normal user message; PCM is not reported.
No tool will be launched without a transcript. Actual ID of note mutations and
Current verified listing condition is the same; As a result, the panel is refreshed from the backend.

In this setup, automatic VAD is turned off; activityStart → limited PCM parts →
activityEnd is sent. Text/audio setup change cancels old resume information
and opens a new session. Stop/unknown/playback rules after shipping
is the current Live contract. Mute is just the response sound; Registration cancellation is Stop.
REST audio, continuous listening, automatic VAD/barge-in and dIn/dOut routing
not yet connected. Physical microphone acceptance is open to user testing.

## Previous slice: Live audio output and persistent API key — October 22, 2026

The user reported that the final note/partial text selection is fully working; this is manual
admission closed. The next single slice is audio output to the written Live message. microphone,
VAD and input device did not turn on. Normal UI's request `live_text:{text,request_id}`
Plays PCM audio along with text transcript; The REST text line is preserved.
The old `live_text:string` and receiverless developer probe do not play sound.

The live session host transmits the audio tracks to the receiver at the host's request.
Bridge's only new notification is `window.vex.audioChunk({request_id,mime_type,data})`
(jarvis alias is the same object) and data is base64, mime_type is audio/pcm; rate=24000.
The JS method only accepts part of the current request and gives a boolean delivery confirmation.
gives. This is not physical speaker acceptance. Another request ID from the model
not used; late/old packet cannot affect the new response. Backend fragment size up to
128 KiB, 16-bit aligned; Limited to a maximum of 2,880,000 bytes per round.

`live_audio.js` owns its own Web Audio context/gain/source resources.
PCM little-endian 16-bit mono/24 decoded as kHz; OS default output
is used. There are up to 20 seconds/512 source queues. Overflow, corrupt format,
autoplay/device issue produces clear warning in sound; text and verified tool
The result is preserved. PCM files are not written to log, history, localStorage or backup.
audio_bytes_forwarded/ audio_bytes_discarded in the API response is numeric;
audio_error is null or safe code, not raw error driver/provider.

The UI shows text as soon as it arrives; login/not lock and Stop until the end of the remaining audio
is kept until. The end of playback is monitored with an event, a maximum of 22 seconds is expected.
The Stop button cuts the sound immediately; If the model continues, native Stop with the same request_id
The result is also expected. If the model is already finished, only local playback is stopped,
The completed tool is not considered to be withdrawn or the model cancelled. mute alone
Live is the output gain; microphone/sound is not an effects control. Disconnect,
Changing model/key drops the error/unknown and page closing sound sources.
The context for the sound is separate from the GoAway/resumption owner; voice/message is not executed again.

The persistent record of the API key is already in Windows Credential Manager
(same Windows user/machine, data profile dependent recording). This record at startup
reused; If the password box is empty, it does not mean that the record has been deleted.
The record was not moved to display/JSON. For current profile in read-only control
configured=true, environment key override=false seen; the actual record has not been modified.
Different TASKVEX_HOME profile requires separate key. Registration is not proof of API access/quota.

New audio adoption is expected with the actual model/audio device. Native synthetic sound
rendering does not verify the audibility of the speaker or microphone.

## Current grade target selection — October 22, 2026

Extended common ModelTools control for REST/Live update/delete. First
Transfer confirmation and new, successful verified notes.list result mandatory in this round
remained. Tool schematic `{id,text?,done?}` / `{id}` unchanged; selected target
Again, it is the actual registration ID. Core CRUD, policy and TaskManager are not skipped.

Selection order: single open record ID; quoted literal in user message
content filter; “endnote” expression outside quotes; The only full text available.
`note containing 'hell'`, `note containing 'hell'` and `note containing 'hell'`
formats, scans **all** records that contain a literal query in their text. One candidate and
It is allowed if the model ID is the same. There is a note with the full text 'hell',
If other notes also contain this part, it does not eliminate the ambiguity.
Turkish capital I, letter/space and plain/typographic quotation differences are tolerated;
Similarity to regex/fuzzy is not interpreted without quotes or negative filter.

“Your last note/son note”, “the last note I added” and “last/latest/newest note”
largest is selected by created_at; the last edited or last recorded record
It doesn't mean. The date of each record must be known and the maximum date must be odd.
ID equal to Missing/null date or maximum date is requested. Registered UTC
times are compared; time deviation or authenticity of date from backup
not guaranteed. To select a literal note named 'end note', its name is given in quotes.

Multiple queries, latest + content filter, zero/multiple candidate or model
choosing another ID prompts for clarification with `note_target_required`; mutation does not occur.
Support is limited to these open patterns in TR/EN, generic natural language parser
There is no claim. Open ID removes ambiguity. Replay of the same call from the previous
preserves the real result; The old list does not allow selection in the new message. Stop, break,
unknown lock and UI refresh from backend only remained unchanged.
Manual acceptance of this slice was confirmed by the user as fully functional;
The previous CRUD commit is preserved.

## Note creation time and user acceptance — October 22, 2026

User REST/Live note adding/listing/editing/completing/deleting, same
selection with description and real ID in the text note, new message after Stop and
reported that the completed transaction had passed the protection tests. below
The “API limit” record in the previous note CRUD acceptance is closed with this notification.
This notification is not actual account acceptance of GoAway/resumption or the new time area.

New notes `created_at:"YYYY-MM-DDTHH:mm:ss.sssZ"` carry UTC time.
Native when adding time backend determines; normal add/update parameters
time cannot be cent. Update/completion preserves the ID and creation time.
Backend list/transaction responses and UI `{id?,t,d,created_at?}` cache space
carries; backup export/import and initial open transfer do not drop metadata.
Browser-only the time of the new note is retrieved from the browser. Open restore/transfer
can move the current date; This date is not evidence of observed occurrence on the server.

In the old record, missing/null means time **unknown**. Read file
does not change, does not assign new date/ID. Undated old backups can be loaded; restored
date is not shown as creation time. Invalid date normalized
not shifted to another day: backend rejects; From UI snapshot/import setting writing
first rejects the entire candidate. The date is a UTC wall clock record; equal time or
It alone does not guarantee an exact sequence for resetting the machine clock.

This previous separate slice was historical information. Next target selection slice up
updated. There is no audio or UI cleanup in these changes.

## Current model note edit/delete contract — October 22, 2026

REST and Live are from the same line ModelTools → registry/policy/TaskManager
Uses `notes.update:{id,text?,done?}` and `notes.delete:{id}`. CRUD schema,
persistent IDs and file/readback authentication remain unchanged. First native note
None of the add/list/update/delete tools will be opened to the model until the transfer is confirmed.
`notes.initialize/replace` is not in the model catalogue; UI remains on path transfer/restore.

The host refreshes the selection context with `begin_turn(text)` on each user round.
Successful and verified with new call ID in this round for new update/delete
Result `notes.list` is required. The user message represents a single real record ID.
or contain the text of a single existing full note or single above
You must comply with your choice. Letter uppercase/lowercase in the text and
clearance differences are tolerated; word limit is observed. Multiple with the same text
filter that cannot separate multiple notes, more than one matching text/ID, unknown ID or
Unsupported indirect recipe/order number selection is not counted. This narrow matching is a natural language resolver
is not; In the uncertain target, the full text or ID is requested, no mutation is made by guessing.

The rejected selection is sent to the user with `ok:false,code:note_target_required,error`.
asks which note is meant. A core task is not created for this target;
Previous verified transactions and tool_results are preserved. Only this rejection is unknown
does not count. Mutation or failed new list invalidates old evidence of selection;
Rereading the old roster result does not turn it into current election evidence.

It does not make a new post again with the same logical ID session/call; deleted target
You may also return the old completed result. Content changed again manager
It is rejected by. Live resume preserves call IDs, but new message
selection cannot be based on the old list. The behavior of Stop/unknown/disconnect is preserved.

UI with current reading `notes_init:{notes:null}` after each note tool round
refreshes the backend; The second does not send update/delete/note_done/note_del/save.
Success is just the proof of core succeeded + verified + read_back; model
The text is not considered evidence. Even if the model link is broken after the text, the actual result is preserved.
New tests: tests/test_model_note_mutations.py; native evidence:
docs/stage5-model-notes-native.json (REST/Live CRUD panel refresh, zero save echo).
In my first run, actual account acceptance was on due to API limit; above
user notification not Turns off CRUD acceptance. Audio/microphone is not available in this slice.

## Current Live connection lifecycle — October 22, 2026

This section updates the historical “no resumption” coverage below. in Setup
session_resumption is enabled; The text is not sent before the actual setup_complete arrives.
GoAway does not resend the active message: the turn will end within the current 25 second limit.
works; If left unfinished, the error and previous tool results are preserved and the old context is forgotten.

Existing socket before new user text with up to 50 ms/32 control messages
is checked. resumable=true received only in idle state after completed round
and a full new_handle is considered a safe checkpoint. Checkpoint in active production
not used; resumable=false/empty handle overrides the old one. GoAway or
Same ModelTools, call IDs and if there is safe checkpoint in idle break
continues with the logical session. Old text is not automatically resent.

The most a resume setup is attempted in a user request; 400/404/1008 or
In case of missing setup confirmation, a fresh setup will be executed before the user text is sent yet.
can be tried. There is no automatic setup repeat for Permission/quota/503/network error. safe
If the checkpoint is missing/outdated, a new session is opened. Handle is in memory only; local
not used within 2 hours after processing; The provider may also reject it before.
Stop, Disconnect, model/key/tool change and failed active turn old
Clears attendance information. Unexpected content/tool does not run on Idle.

Result fields: session_reused same socket, session_resumed successful resume
Specifies the setup. logical_session_id is the opaque ID of the host; stays on resume,
fresh changes at startup. context_reset_reason is a known secure code or
is null. UI session reused / session resumed / new session and when necessary
context reset indicates the reason. If GoAway is seen, goaway_received=true.
The provider's ID handle/session is not transferred to the UI, log, file or backup.
Idle break momentary background is not monitored; noticed in the preflight of the next message.

## Current REST Stop contract — October 22, 2026

Native `text` now uses the same `{text:string,request_id:string}` envelope as Live
uses; The old string call is preserved. The stop ID must be 1–128 characters.
`stop_task:{request_id}` is the same entry for REST and Live; non-legacy/active
identification is denied. REST acceptance returns `ok:true,accepted:true,completed:false`;
The value `waiting_for` becomes `http_response`, `tool_result`, or `turn_completion`.
If HTTP is in progress, the UI explicitly tells you that it is waiting for it to finish; login/not takes the lock.

The stop is lined up with the start gate HTTP/tool. The next tool is not accepted,
retry and fallback do not start; The retry standby wakes up with the signal. already accepted
synchronous HTTP is not force-killed; response/error/timeout with content after waiting
No new transactions are made. Short local core task is given abort signal, actual result
is protected. Completed text cannot be withdrawn. HTTP timeout setting is 30 seconds; transport
It is expected that the layer will return, the exact 30-second total finish is not guaranteed.

If the actual `text` result is `ok:false,completed:true,stopped:true,request_id`, HTTP and
The waiting for the tool is over. Pending/unknown or in an unreadable task as a result of cancellation
`unknown:true,stopped:false` comes up and the UI remains locked until reboot.
The new message receives separate client/signal; old Stop and new round of late Stop response
does not affect. UI reads notes from backend; The second mutation does not send. of Live
socket cancellation is unchanged. Resumption/audio/not edit-delete is not included in this scope.

## Current Live Stop contract — October 22, 2026

This section updates the historical coverage of the Stop closed below. UI
Sends `live_text:{text:string,request_id:string}`; ID is 1–128 characters.
The old `live_text:string` is retained. `stop_task:{request_id:string}` matching only
accepted in active Live round; `ok:true,accepted:true,completed:false` finish
It is not. The UI retains the input/not lock until the actual live_text result.

If the actual result is `stopped:true,completed:true,ok:false` then turn/socket is indeed
it is over; previous tool_results are preserved and read from the annotation panel backend.
Tool Pending/unknown has `stopped:false,unknown:true`; controls do not open.
Stop does not undo the completed note. Repeated Stop is the same signal; old request
id cannot interrupt the new round, delayed Stop response cannot change the new UI state.
The next message opens a new session. Thread I/O remains idle, Disconnect closes it too.
REST Stop was added in the next slice; The current rule is above. Resumption was not added.

## Current Live tool contract — October 22, 2026

This section updates the historical tool-free testing coverage below. `live_text:string`
uses the same lock/catalog authentication. Model only `apps.catalog` and
`system.status` sees; `notes.add` if the backend has verified the initial note transfer,
`notes.list`, `notes.update` and `notes.delete` also open. Opening an application does not open for the model.
If the tool list changes, the old Live connection is closed and opened with the new scope.

Sets the host ID resource/user; call provider `id/name/args`
It falls into the line ModelTools → registry/policy/TaskManager. Same open session
call ID uses the same task; It is rejected again with different arguments.
The terminal actual result is returned with the call ID as `FunctionResponse`.
Waiting/uncertainty is no success; There is no automatic resubmission.

`mode=live_session`, `session_reused`, `tools_enabled`, `tool_results` in response
and durations. Each tool registration carries `id,name,task_id,status,result`;
`result` is the result of `verified/data/error/evidence` core. UI tool status
logs read notes from backend after note call; does not send a second text.
Finalized tool results are retained even if the model response fails. `unknown`
As a result, the conversation/not controls remain locked until power-on again.

Turn is 25 seconds, tool wait is 5 seconds, maximum 8 calls. These undo the transaction
It is not a guarantee of receiving. Disconnect still only works while idle. audio output
is thrown away; Playback, microphone and normal Stop are not available in this slice. New session/different
call ID does not automatically prevent the same intent from being executed a second time.

## Current Live session — same link between messages

This section updates the weld life rule for the cold joint test below.
If `live_text` uses the same API Live model and the same key as SDK/WebSocket
remains open. PersistentLive has a single I/O thread/event loop; TaskManager
It is not an alternative to worker. The one lap at a time rule is maintained. Tool coverage
It is in the current section above; the chat context remains in the session on the provider,
No local chat history or voice bytes are recorded.

The response has mode=live_session and session_reused:boolean. UI in the first round
new session indicates session reused in the following round. connect_ms again
does not involve connection costs in use; first_text_ms/elapsed_ms every message
It is relative to its own beginning. Permanent residence is not guaranteed to live forever.

socket/SDK/event closes loop/thread while `disconnect:null` idle alone
waits; After `{ok:true,completed:true,disconnected:true}` the UI goes offline.
Open rejection is given in the active round; It is not Stop/cancellation. Next message new session
can open. Model switching and key registration will first shut down the old Live source.
Window closing normally waits with idle; If the GUI loop ends unexpectedly
The active network job is canceled and the Live resource is left in finally.

Error/timeout/GoAway/partial socket cannot be used again after the turn. Failed message
There is no automatic resending and no switching to REST. New user message new
can open a connection; It is not assumed that the old context remains. Session continuation,
Automatic reconnect and idle health notification are not available in this slice. Disconnect with remote idle
can be understood during the next I/O; LAST LIVE TEST is the final response information.

## Transient Live latency test — no sound playback/instrument

The `liveLatencyTest` box under chat is checked at launch; this is a temporary test
preference is not recorded in the backup. When checked, native UI sends `live_text:string`.
The backend requires the Live model selected from the latest successful API catalogue; catalog
Before it is loaded, the request is rejected with an explicit error. Closing the box available REST text
returns to its flow. The REST 3.8/3.5 retry line was not changed.

TextChat.run_live uses the same lock busy/closing; asyncio in API thread
Opens a single cold WebSocket session with . Asenkron/synchronous SDK clients and socket
It closes at every exit. 25 seconds timeout for connection+turn, maximum 2000 messages and
There is a limit of 32000 characters. There is no automatic retry/model fallback. model sound
produces as a forced AUDIO response; output_audio_transcription enabled, audio
It is thrown away without being accumulated. The microphone and speaker do not turn on. Provider voice quota again
can be consumed. No tool notified/operated; The grades panel is not updated.

Success in addition to the normal text/elapsed_ms fields mode=live_latency_test,
connect_ms, first_event_ms, first_text_ms, audio_bytes_discarded returns.
first_event first is audio/content, first_text is first transcript/text; both are cold
Includes connection setup. All parts are read; text and transcript together
If there is a transcript, it is preferred not to be shown twice. If interaction_status exists
IDLE end, otherwise turn_complete is expected; truncated/empty/partial result will not be success.

The UI shows the text and the first text/total time when the full response arrives; does not play sound.
LAST LIVE TEST indicates the last completed request, not an open persistent connection.
Errors are returned as coded safe text; WebSocket code like HTTP code
not tagged. This is a latency smoke way; persistent Live session, voice assistant,
note tools do not mean cancellation or bot integrations are complete.

## Text error/duration diagnosis

GeminiText results `elapsed_ms` (entire turn; including tool and retry hold) and
Carries `model_attempt_details:[{model,outcome,elapsed_ms,http_status?}]`. Every try
The duration belongs to that generate_content call only. outcome response, http_error,
timeout is network_error or failed; The raw exception/provider response is not retained.
Error fields Model/API are codes in the current open list. UI is failing
Shows HTTP code, application error code, latest model and total time. each model
trial result/duration is added to the Engine Log as secure text. This measurement
It separates errors quota/service/request; It does not predict the cause of a particular error.
The total time also appears in the success response. Retry/timeout and tool execution policy
did not change; Timeout is not offered as a performance improvement or Live connection.

## Current fix — regular chat and Live catalog from API

This section covers the note transfer and model selection rules of the first text segment below.
replaces. Normal chat is open while waiting for grade confirmation; host only apps.catalog
and system.status tools. After confirmation, notes.add/list is added. Continue
The UI stops sending messages during a note operation that is interrupted or has an uncertain outcome.
If there is no real backend in browser-only opening, the app.main opening command under chat
is shown; the input is preserved. Grade transfer is never automatically confirmed.

`query_catalog:null` only works on open Load Live models click. official
bidiGenerateContent in SDK models.list supported_actions on all pages
selects reporting models; It is not enough to have live in the name. Maximum 5 pages,
100 requested per page; HTTP wait 10 seconds, SDK retry is off. empty list
is the true null result. On error or limit partial/fixed/backup the list is not applied. UI
Considers the result indeterminate at 65 seconds and locks the reload; Late response does not apply.
Meanwhile, the backend rejects the key exchange and the second catalog query.

Success `{ok:true,completed:true,models:[{id,name,live:true}],currentModel}`.
The list does not prove that Live connection or audio output is working on the account.
`model:string` only accepts the ID from the last successful API list. This is
future Live session preference; REST text is not the same variable as the model name.
The result contains live_connected:false; The UI clearly tells you that no audio is connected yet.
The general settings save stores the preference in the current save line. When the API key changes
the catalog becomes invalid and the user reloads it; model names key spare
It is not recorded with . Catalog error also invalidates the previous selection on the server side.

REST text adapter 3.8 Flash → controlled retry → 3.5 Flash-Lite policy
protects. The Live preference in the UI is not sent to this REST request. for Telegram/Discord
this line of text has been preserved; bot integrations have not been written yet.
Live audio response to the written desktop message will be connected in the next slot; It doesn't exist today.

## Stage 5.3 text slice — single message, real model and note refresh

- In the first implementation, `text: string` required a ready-made native host and initial note transfer;
  Current behavior is above.
  Message is 1–20000 characters; empty text is rejected. One model turn at a time
  There is. Each message is independent; The past conversation/profile instruction is not sent.
- Long network turn does not retain bridge RLock. PyWebView API runs the thread;
  The second worker/dispatcher is not installed. TextChat closes the SDK client at the end of the round.
- Allowed model tools are apps.catalog, system.status, notes.add and notes.list.
  Native notes can be user data; When the user requests a listing, this
  The tool ultimately goes to the Gemini service. Delete/edit/apply opening in this slice
  It does not open to the model. Registry/policy/TaskManager is not skipped.
- Success returns `ok:true,completed:true,text,tool_results,model,model_attempts`.
  completed means that the turn function is finished; alone that the tools are successful
  does not prove. Pending/unknown results in UI remains locked. unexpected error
  Returns `{ok:false,unknown:true,error}`; The raw exception or key is not shared.
- app.js native sendText shows the response with textContent; model HTML does not work.
  Accepting an emit in a native text is not considered a success. Send/input/model until response
  and Stop is closed; note mutation/import stands with separate chat lock. in 240 seconds
  If no definitive result is obtained, unknown is displayed, late response is ignored, do not reopen
  must. Resubmission is not automatic. The actual cancellation is not yet due.
- Notes_init may be written before the unsuccessful response during normal termination.
  read-only is queried again. Native setter/mutation/save echo is not produced.
  If renewal cannot be verified, the existing unknown lock of the annotation module is retained.
- The first catalog reports two supported text models; this list account access
  or online proof. `model: string` only accepts these two names and
  is rejected in the active round. UI waits for confirmation first, then current setting via save
  saves the choice. Default instead of legacy unsupported model at startup
  is selected. Fallback during text does not permanently change the selected model.
- Net pill shows `TEXT · <model>` only after successful real text round;
  This is the last successful request information, not the permanent Live connection. fail
  offline/error in round; When the model selection changes, NOT CHECKED is displayed. Reconnect,
  disconnect, stop_task and audio are the next slices; They are not considered successful today.
- Closing Shutdown/Restart/X is rejected in the active text round; when the turn is over
  can be closed again. Fake cancellation is not shown as if the transaction is completed.

Validation and use: [Step 5](../../../docs/STAGE5_MODEL.md).

## Stage 5.3 first slice — native registration of API key

- credentials.js API Key field, Save API key button and apiKeyStatus status
  is the owner. Change/blur does not auto-transmit; button or Enter required.
- `apikey: string` is only supported on ready-made native host. Your host key profile
  It writes to the Windows Credential Manager registry and verifies it by reading it back.
  The success has the format `{ok:true,completed:true,saved:true,configured:true}`;
  The key itself does not return. Empty entry does not delete the record, it is rejected.
- `query_apikey: null` gives only `{ok:true,completed:true,configured:boolean}`.
  This is the registry entity in Windows; does not verify media key or API access.
- There is no network request/model online signal in the API key record. Key general save,
  It does not go into settings.json, notes.json, localStorage, export or timeline.
  When recording starts, the password input is cleared; The success sound will not be played before confirmation.
- If confirmation is not received within 12 seconds, the status becomes unknown; No resending.
  Controls remain locked. Native error result does not translate into verified success.
- `apikey` browser fallback is not sent to onEvent transport. Native onEvent
  observer receives only `[REDACTED]`; logs key event error/answers
  It is not transferred in its raw form. Existing observer agreements for other events are retained.
- Backend text client open GEMINI_API_KEY environment, if not existing profile
  Uses Windows registry. TASKVEX_HOME profiles do not use each other's records.
  In this first key slice the chat was not connected; The current text agreement is above.

## Stage 3 — Single backend authority in native notes

Native UI with Use backend notes if necessary after the first notes_init query
requires explicit transfer confirmation; In case of cancellation, old notes are preserved. Sign of approved transfer
in the same file as the notes will not be re-added when the opening/last note is deleted.
Native not events use the {version:1,request_id,arguments} envelope:
notes_init -> notes.initialize; note_add -> notes.add; note_done -> notes.update;
note_del -> notes.delete; notes_replace -> notes.replace. source/user
bridge selects. All transactions pass through the registry/policy/TaskManager line.
UI only implements completed:true/verified:true; 12 seconds/unknown
then it won't resend, ignores the late reply, and locks the notes.
Restart reads the result from the backend. Local copy cache/backup.
Native addNote/setNotes and annotated initApp/loadStore return false; notes
It cannot be written with these setters. Browser-only setter and legacy native event formats
is protected. Details: [note pass](../../../docs/STAGE3_NOTES.md).

## All setting records and backup confirmation

- saveAll() preserves native boolean API; native save requests independent JSON
  copies are sent from a single Promise queue. loadStore(...,{emitSave:true})
  It also uses the same tail. The onSave observer makes a separate copy of the sent data.
  cannot change. In snapshot setters, emitSave:false/no-echo is preserved.
- Settings/Profile open Save and Export native completed:true/saved:true confirmation
  waits. setting/profile panels saving/saved/approval in automatic recordings
  Indicates the status of not received. If confirmation is not received within 12 seconds, the result is uncertain;
  The actual request is not canceled, the queue queue is not broken, and there is no auto-repeat.
- importBackup async returns boolean. First, check the supported backup areas and
  controls collection structure; External states such as runtime telemetry/catalog
  It does not apply from backup. In Native, first the setting confirmation is made, and the file containing the notes is also
  Notes_replace confirmation awaited; then the local skill/routine and settings are applied.
  Ret/missing UI areas that have not yet been implemented in the assertion are preserved. During import
  form controls are temporarily turned off; It opens back at the limit success/error/wait.
- Two warehouses are not one transaction: native setting registration is successful and then
  If localStorage write fails, previous local preferences are restored; native
  settings and restored notes may be new. Backend notes are authority,
  It is not displayed as if the old UI notes have been reverted. Partial success is reported openly. Source
  the backup file is not deleted; There is no automatic re-import.
- After registration confirmation in Export native, WebView2 opens the Save File dialog. UI
  It says that download only is requested; Opening the dialog, confirming that the file has been written
  It is not. Browser-only export uses the browser's download. unused
  The export backend event is not sent; The blob URL is then released.
- Skill/routine definitions are local. Native notes are owned by the backend; generic
  save does not write collections a second time. Import with notes, front of the file
  waits for notes_replace confirmation after verification and setting save; ui note
  It does not reapply the snapshot. The old backup gets ID; new backup id
  protects. With two backend files, the local repository is not a single transaction; next
  The error does not undo the previous successful write. Partial success is reported openly.

## Startup error and settings repair

- Starting with Backend `startupStatus({ok:false,code,message,recoverable})`
  shows the warning. `startupStatus({ok:true})` removes the warning. This situation is a model
  It is separate from the case online/offline; The message is written securely with textContent.
- `retry_startup` without payload retries the start without changing the register.
  The same validation and no-echo snapshot path is used as the first ui_ready. fail
  native save continues to be rejected on startup.
- `recover_settings:{confirmed:true}` is sent only after clear UI approval;
  this flag is not authentication, it is the approval flow of the trusted native UI.
  Corrupt JSON or settings schema, actual settings.json bytes unique .corrupt
  It cannot be changed without moving it to the file. Valid readable parent fields are preserved;
  invalid/unreadable preferences return to default. Native UI collections and
  core notes.json is immutable. The backup field in success is just the backup file name.
- Unsupported version and file access error repair is not authorized; repair
  button is not shown. If the file is corrected at this time, the startup is checked again,
  healthy file is not backed up/reset. Cancel does not call the backend.
- If the backup or writing a new file fails, no success will be shown. Formed backup
  is protected; Retry is available. The repair is separate from the normal interface reset.
- Run() terminal message and Windows error in CLI error that occurs without opening the window
  box shows, the exit code is 1. Raw exception content to user message
  not added; startup error does not cause automatic data reset.

## Restart, interface reset and always-on-top

- `restart` without payload stops the core and closes the native window. main, GUI
  When loop/worker closes, it opens a new process with the same Python + app.main; available
  TASKVEX_HOME and debug selection are preserved. executable/argument is not received from the UI.
  The Restart app and the legacy Restart button in Settings > System use this path.
- `ontop:boolean` is instant applied to the real window; checkbox on unverified request
  returns to its previous position. Persistence is in the current Save model. Registered onTop both
  It is applied both to the native window after Save/import in the initial snapshot.
- `reset` without payload theme/color only, layout, SFX/sound, wake/noise, onTop, compact
  Returns the appearance and active settings tab to default. Profile, device/model/sound
  preferences, local not/skill/routines and core notes.json are preserved. The button asks for confirmation.
  The local record will not be deleted before Backend record/read-back approval and snapshot.
  No-echo is implemented with Snapshot loadStore; The page is not refreshed. Browser-only is on the way
  the same fields are reset locally, collections/profile is preserved.
- WinForms on_top setter works with Invoke in GUI thread; From API thread
  direct control is not changed. True native testing covers this limit as well.

## Native window and view update — October 21, 2026

- Default theme and idle reactor color is `#a78bfa` (purple). Registered theme/colors
  takes priority; The update does not change user preference.
- F11 sends event `fullscreen` without payload, also in text field; backend real
  Changes the full screen state of the window. Pressed key repetitions are ignored.
  In browser-only mode, the browser's Fullscreen API is used.
- Native Shutdown sends `shutdown` without payload, once worker shutdown is completed
  The window is destroyed. The old Restart overlay does not open in the native path. If the worker does not stop
  the window remains open and the error returns; No fake closing approval will be given.
- The local native host sets the WebView2 autoplay argument in this process; opening sound
  It doesn't wait for a click. The SFX off/audio preference is retained. Browser audio policy does not change.
- 60 FPS drawing targets including Reactor idle; With 60/90/120/144 Hz timings
  tested. Actual FPS depends on hardware, load and background limitations.

## My first real native language — October 21, 2026

`python -m app.main` opens the current UI with PyWebView/EdgeChromium. PublicPython
API only includes `event(name,data)`. Supported events: `ui_ready:{version:'1.0'}`,
`save` with allowed setting fields, and `system_status` read-only without payload.
Successful save returns `{ok:true,completed:true,saved:true}`. Incorrect registration or
returns unsupported event `{ok:false,error:string}`; The error text contains no secrets.

Native ready declaration is not a model link; UI shows `MODEL OFFLINE`.
The initial snapshot does not include not/skill/routine collections; current local data
is protected. initApp/loadStore returns the boolean result of the applied snapshot.
Generic save does not write these collections or credential fields to the backend.
CPU/RAM is null because usage percentages are not measured; OS information is from the actual core tool.

`saveAll()` maintains the synchronous local boolean contract. On Settings/Profile Save
waits for native completed/saved confirmation with buttons `saveSettingsConfirmed()`;
error/missing modal remains open on confirmation. Browser/fallback mode current local behavior
protects Automatic registration/import details are in the single registration queue section above.
Unsupported execution of skill/routine and device/model/Google
receives open rejection of events; native UI behavior does not count as physical native achievement.

[Phase 2 plan, testing and limits](../../../docs/STAGE2_NATIVE.md).

## Note events — October 21, 2026

Adding/completing/deleting user note actions update local storage with `saveAll({emitSave:false})`; only sends the corresponding `note_add`, `note_done` or `note_del` mutation event before. These actions also do not produce full `save`. View events, such as Timeline, can be discrete; It is not a note mutation. Backend `addNote`/`setNotes` calls do not produce outbound notes or saves.

The old payloads of this section are preserved only in browser-only mode: note_add text,
note_done `{t,d}`, note_del text. Native version envelope in the upper Phase 3 section
defines. Even though the open Settings Save collection contains a second note, the backend
It does not count mutation. Native backup restoration only goes through the notes_replace tool.

The browser-only path does not provide backend authentication. Verified result in Native,
there is a fixed identity and a one-time initial transfer; There is no permanent global quest log.

## UI staging closure: wait and audio lifecycle

- Camera and location operations wait for final response/notification no more than 12 seconds. Expiration is not proof of success or failure: UI shows **status unknown**; overrides the old Promise response. The next press of the same button does not repeat the physical action, but only queries the status.
- New read-only events `query_camera:null` and `query_location:null`. The backend should also report whether the previous process is still running. `{pending:false,active:boolean}` for camera, `{pending:false,saved:boolean,name?,error?}` for location is the exact case. Only the `{ok:true}`, `pending:true`, or just the active/saved field does not allow reprocessing in the query path. If the backend does not support these events, the UI retains the unknown state and can be queried again; It does not produce fake success or automatic transaction repeats.
- `setCamera(boolean)` / `setLocation(...)` final notifications from backend can also terminate indeterminate state. Without RequestId, the sequential authoritative notification requirement of the protocol continues. While the page is hidden, the pending transaction is not translated to success/idle.
- `weather(undefined)` protects data; `weather(null)` clears the temperature, description, and additional fields to unknown status.
- `setSfxConfig` reduces the non-finite or non-number volume to 0.8; restricts finite numbers to the range 0–1. The wrong type is still rejected in Snapshot.
- `attachAudio` uses a single, shared reactor AudioContext; MediaElementSource is not created again for the same HTMLMediaElement. When the resource changes, the old graph is separated. `detachAudio()` leaves only reactor node connections; It does not stop MediaStream tracks owned by the caller. If the backend is the resource owner, it must terminate the tracks itself. Shutdown separates the graph; The context is closed when the page is actually abandoned. When hiding for BFCache, the graph is separated and the reusable context is preserved.
- Removed unused `window.vex.eval` / `window.jarvis.eval`. No caller found in the current resource. If an external legacy backend uses this, it should be moved to the allowed native evaluate_js path during integration.
- The device preference preserves the current Save Settings model; The backend device event at the time of selection is an instant choice, Save Settings is required for browser persistence.

## Additional rules after independent audit

- The fields of additional panels consumed within the Snapshot are also pre-validated: calendar, reminder, timeline, device, catalog, metrics and related settings types. Invalid snapshot is rejected without changing existing live/persistent data. Failure of the storage itself also produces visible error.
- Missing skill/routine IDs get conflict-checked UUID (counter fallback if not supported). Duplicate open IDs in the same list are rejected; Valid existing IDs are retained. Direct collection setters also use this limit.
- Local record recovery is field-wise: invalid field/record is skipped, valid notes are preserved. Bad colors null value turns into a safe empty map. Old timeline records are also validated.
- Backend `setLocation` notification can update local save but does not generate outbound save or onSave. User-generated completion uses a separate registration path.
- Native onEvent observer's Promise completion does not hold the emit result; rejection is also captured. Since Fallback is the actual migration, its completion is expected.
- Camera handler state is installed before ui_ready is sent. Synchronous ready callback is supported in browser testing; actual native delivery should also be verified.
- The conversation scheduler can only idle while its own state version is valid. Restart cancels the old shutdown timers and closed event.
- startTimer(0) resets the counter to state READY/00:00. Invalid, negative or non-finite time does not change the running counter. Not providing a parameter uses the available time.
- Open empty model/sound list clears and disables the menu; Preserves incomplete list. The saved preference can be selected again in the current catalog in the future.
- If persistence fails on form Skill/routine, the memory change is rolled back and the form is preserved; Retrying does not create a double registration. Setting/profile modal remains open on failed registration.
- Modals use dialog semantics, background inert state and focus boundary. Focus is placed when the opening animation is visible; Escape closure and modal transitions restore the previous focus correctly.

## Transport and start

`window.vex === window.jarvis`. Native port `window.pywebview.api.event(name, data)`; If native is not available, `onEvent(name, data)` is an alternative. When Native is present, onEvent is called only as an observer; do not connect it to a second player. Observer rejection does not cause the native submission to be repeated.

`ui_ready: {version:'1.0'}` is sent once after the global bridge is ready, whether native is loaded early or late. This does not indicate that the model session is online. Backend reports model status with `online(boolean, text?)`.

`emit` Promise result `{ok, error, response}`. `false`, `{ok:false}` or `{success:false}` is obvious failure; The error thrown and the Promise rejection are caught. Other answers accept move/request; It does not mean that the transaction is completed. Known key/token patterns are masked when error texts are written to the screen; The backend should not include confidential information in error messages.

## Snapshot and collections

`initApp(snapshot)` and `loadStore(snapshot)` use the same verification/normalization line. missing/undefined preserves existing data for notes, skills, routines; null clears; changes the string. Invalid record rejects the entire snapshot without being applied. Successful bulk update uses a single registration step. Backend sourced updates do not produce outbound saves; user backup import produces a save. The storage error becomes visible and the save is not sent; This does not mean that the live UI is persisted.

Direct methods: `addNote(text)`, `setNotes(array)`, `setSkills(array)`, `addSkill(object)`, `skillResult(id,ok)`, `setRoutines(array)`, `routineResult(id,ok)`, `routineEvent(type,value)`, `setTimeline(array)`. It should not be assumed that snapshot verification will be directly replaced by setters; The backend must comply with the applicable contract.

Skill steps: object array. The empty string is valid; null/object/text/number is invalid in the form. The step_type of each step is open_app, interact_element, hotkey, type_text or wait. If given, target/text/action/app_name is text, press_enter is boolean, wait_after is finite and non-negative number. The backend also verifies tool-specific requirements and permissions; This UI scheme is not execution authority. The snapshot boundary parses the old JSON text into the same string contract. The new form record gets non-conflicting ID; The edit flow preserves the current ID.

## Camera, location, cancellation

- `camera: boolean`: old payload is preserved. It only waits for the response of acceptance/undefined. Completed if `active` matches the target or completed:true is given without reverse active. boolean true is the legacy completion response for camera opening. Final backend status notification `setCamera(boolean)`.
- `location: {name,auto:false}` or `{auto:true}`. completed:true without saved:true or saved:false indicates completion; only ok:true is waiting. Final notice `setLocation({saved,name,error?,completed?})`; The old string declaration is supported as saved name. Only the name field is not complete.
- Simultaneously waits for a user request on camera and location; automatic and manual position share the same lock. The final notification ends the wait and overrides the previous Promise response. Since notifications do not carry requestIds, the backend must send them in authoritative current status order; There is no identification of old independent pushes in this old protocol.
- `stop_task`: ok:true is the acceptance of the cancellation request. UI does not show idle while task is active. stopped:true/state:'idle' response or `setState('idle')` reports final status. If the final notification is not received, the situation will be unknown after 12 seconds; Acceptance is not considered automatic success. Cancel button does not send command again in case of waiting/unknown; The task cannot be done idle without proof of state value. Unknown is shown on the button and in the log. Old Promise arriving late is ignored; authoritative `setState('idle')` removes the lock.

## Device and catalog

`setDevices({inputs,outputs,cameras})`: registration `{index:integer,name}` or `{deviceId:string,label}`. If both fields exist, the current index takes precedence. User event `device:{id,index,deviceId,label}`; Only one of the index and deviceId fields is full. index=0 is valid; The deviceId text consisting of numbers remains. Selection IDs are maintained in store.devs.

`setCatalog({models,voices,currentModel?,currentVoice?})`: Id and name are used in model/sound list records. Selection priority is current backend active preference → current saved preference → first option. Placeholder is not saved as an identity.

## Measurements and offline coverage

`telemetry({cpu,gpu,ram,cpuT,gpuT,ramTxt,bat,disk,win})` and `network({ping,down,wifi,api})`: undefined/missing saves space; explicit null makes the corresponding field '—'; finite zero is valid. If the entire object is null, all fields of that group are cleared. If an invalid type enters the numeric fields, the measurement is displayed as unknown.

`online(false)` model/API tells you that the session is closed: API latency and token information are invalidated. It does not delete local CPU/GPU/RAM and Wi-Fi measurements. The backend reports the loss of physical internet/ping/download with separate `network({ping:null,down:null,...})` fields. The 0 used in `tokens(used,max,isEstimated)` is valid.

Other display methods: weather, media, setCalendar, setReminders, googleStatus, screen, task, taskDone, msg, streamMsg, streamReset, say, user, log. Calling them does not provide evidence from outside the UI that the relevant external action has been performed.

## Scheduler ownership

A time-based routine check runs within the UI in 15 seconds, and a calendar alert scan runs in 30 seconds. The backend should call `window.vex.stopRoutineScheduler()` before starting its own scheduler, and `window.vex.stopCalendarScheduler()` if it will also take over calendar alerts. Methods can be called again; It does not generate outbound events. It is exported from ES modules with the same names. The pause is valid for the life of the page; On reinstallation, the backend must re-establish ownership. Normal pagehide clears the loops; BFCache migration maintains timers (browser loads freeze/restore). Manual routine execution and routineEvent are not affected. Replay prevention with trigger ID on the backend side should also be implemented in the integration.

## Local storage

The settings are written only to the key `taskvex_ui`, timeline `taskvex_tl`. `jarvis_ui` is only used to read old data if there is no primary record; Normal save and snapshot do not write this key. The existing old record is not deleted; reset clears both setting switches. Local storage is not a vault of confidential information. Error Writing/deleting is visible; Do not put production API key in localStorage.

## Adding files

`file` now carries the filename string `{name:string,type:string,size:number,encoding:'base64',content:string}` instead. content is the Base64 equivalent of raw file bytes; data does not contain a URL prefix. The empty file is valid; MIME type can be empty. UI limit is 10 MiB; larger file is not sent and visible error occurs. The backend must support this new payload, revalidate the types, Base64 validity, decoded byte length, and size limit. The filename is not a local path or write privilege; is treated as untrusted input. Acceptance does not mean that the analysis is complete. If Read/Move is rejected, no success message is displayed; the same file can be selected again. There is no Python backend in the project that handles this event yet.

## Event and method inventory extracted from the source

This list shows fixed-name emit calls; Payload rules are defined in the above sections and relevant handler resources. The new backend should not consider this inventory as authority to implement it.

| UI → backend event | Calling modules |
|---|---|
| apikey / query_apikey | credentials.js |
| audio_listening | app.js |
| cal_soon | connections.js |
| camera | app.js |
| closed | app.js |
| device | settings.js |
| disconnect | app.js |
| drawer | panels.js |
| file | app.js |
| google_connect | connections.js |
| inspect | skills.js |
| layout | settings.js |
| location | connections.js |
| media | connections.js |
| mic | app.js |
| model | connections.js |
| mute | app.js |
| noise | settings.js |
| note_add | notes.js |
| note_del | notes.js |
| note_done | notes.js |
| ontop | settings.js |
| query_devices | settings.js |
| reconnect | api.js |
| reset | settings.js |
| restart | app.js |
| routine_delete | routines.js |
| routine_save | routines.js |
| run_routine | routines.js |
| run_skill | skills.js |
| save | settings.js |
| screen_share | panels.js |
| shortcut | panels.js |
| shutdown | app.js |
| skill_delete | skills.js |
| skill_save | skills.js |
| stop_task | app.js |
| text | app.js |
| timeline | panels.js |
| timeline_clear | panels.js |
| ui_ready | api.js |
| voice | connections.js |
| wake_sens | settings.js |

| Backend → UI method | Arguments |
|---|---|
| msg | c, t |
| streamMsg | c, t |
| streamReset |  |
| detachAudio | — |
| say | t |
| user | t |
| log | t, l4 |
| setState | k |
| level | v |
| micLevel | v |
| setAudioListening | d |
| attachAudio | src |
| wake |  |
| wakeWait | on |
| startTimer | s |
| pauseTimer |  |
| resumeTimer |  |
| resetTimer |  |
| startStopwatch |  |
| pauseStopwatch |  |
| stopStopwatch |  |
| resumeStopwatch |  |
| resetStopwatch |  |
| telemetry | o |
| tokens | u, m, isEst |
| network | o |
| weather | o |
| media | o |
| setCalendar | a |
| setReminders | a |
| setCamera | active |
| setLocation | d |
| setDevices | d |
| setCatalog | c |
| googleStatus | s |
| screen | d |
| initApp | snapshot |
| loadStore | o |
| task | id, t |
| taskDone | id, ok, t |
| addNote | t |
| setNotes | a |
| setSkills | a |
| addSkill | o |
| skillResult | id, ok |
| setRoutines | a |
| routineResult | id, ok |
| routineEvent | type, val |
| stopRoutineScheduler | — |
| stopCalendarScheduler | — |
| action | x, ok, k |
| setTimeline | a |
| online | ok, txt |
| reconnecting | n |

