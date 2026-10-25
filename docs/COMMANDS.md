# TaskVex command guide

This file describes what you can currently ask Vex to do.
See [architecture](ARCHITECTURE.md), [plan](PLAN.md) and
[UI/backend contract](UI_BACKEND_CONTRACT.md) for ownership and limits. It is a user guide,
not an executable command file or a source of permissions for the model.
Update it whenever an implemented command or its behavior changes.

## Using this guide

- Examples are natural-language requests, not exact phrases you must memorize.
  You can speak or type them in the desktop Live conversation. Replies follow
  the language selected in Personalization.
- Note commands require the initial backend note transfer to be confirmed.
- Replace `<note-id>` with a real ID returned by Vex; do not type the placeholder.
- A request is successful only when the underlying operation is verified.
- Implemented model tools accept Turkish and English requests; this does not
  guarantee recognition of every paraphrase. Sleep uses a structured model
  tool call, not a fixed phrase list. Unconnected features are not made available by changing language.

## Notes — available

| Say or type | What Vex does |
| --- | --- |
| `Add "Buy milk" to my notes.` | Saves a new note with its own ID and creation timestamp. |
| `Show my notes.` | Reads the current saved notes. |
| `List my notes with their IDs.` | Shows the actual record IDs so you can select a specific note. |
| `List my notes newest first, including their creation dates.` | Uses the saved creation timestamps to present the list in date order. See the date limitation below. |
| `Show notes containing "milk".` | Reads the note list and presents matching text. This does not modify notes. |
| `Change the note "Buy milk" to "Buy oat milk".` | Updates the text of one unambiguous existing note. |
| `Mark the note "Buy milk" as completed.` | Sets the selected note's completion state to done. |
| `Mark the note "Buy milk" as not completed.` | Sets the selected note's completion state back to incomplete. |
| `Mark my last two notes as completed.` | Selects the two newest records and completes them together in one verified write. |
| `Complete all notes containing "test".` | Completes exactly the explicitly requested matching group; other notes are preserved. |
| `Mark all my notes as completed.` | Completes the entire current note set without changing text, IDs or creation dates. |
| `Mark all my notes as not completed.` | Reopens the selected entire set using the same verified batch tool. Latest N, matching content and explicit ID groups also work. |
| `Delete the note "Buy milk".` | Deletes one unambiguous existing note. |
| `Delete the note with ID <note-id>.` | Deletes only the selected record, even if other notes have the same text. |
| `Delete the note containing "hell".` | Selects by literal substring and deletes only if there is exactly one match. Quotes are examples, not required command syntax. |
| `Delete my latest note.` | Deletes the uniquely newest note by creation timestamp, not by list position. |
| `Delete my last two notes.` | Selects exactly two newest records by creation timestamp and deletes them together in one atomic write. |
| `Delete all notes containing "test".` | Selects the explicitly requested matching group and deletes exactly those records together. |
| `Delete all my notes.` | Selects the entire current note set and deletes it in one verified write. This is a destructive command; use a temporary-note profile when testing it. |

Before editing, completing or deleting, Vex must call `notes.select` with a structured
selector (`ids`, `text`, `contains`, `latest` with a count, or `all`) and an
explicit single/group scope. The model interprets your wording; the backend
does not match command phrases. It returns real records and a snapshot.
Single-target ambiguity requires clarification and cannot be widened silently
or resolved by guessing another ID in the same turn. Literal substring and
latest selectors also work for a single update/completion. Fuzzy matching is
not supported. A read-only `notes.list` alone does not authorize a mutation.
Unsupported combinations of filters require clarification or explicit IDs.

Date ordering is presentation over `notes.list`, not a separate date-query tool.
Older/imported notes may have no creation timestamp; Vex must not invent one.
If any timestamp is missing or a tie crosses the requested selection boundary,
a latest-note mutation requires explicit IDs. A requested count larger than
the existing set is rejected. Editing preserves creation time and record IDs.

Mutations use the selected snapshot. If any note changes between selection
and execution, nothing is changed by that mutation; Vex must ask you to select
again. Batch deletion and completion require exactly the selected IDs, reject
missing targets without a partial change, and never loop through single mutations.
Batch completion changes only the boolean done state and supports reopening;
its reported updated_count counts targeted records, including already-matching states.
Stop before the write preserves notes; Stop after a verified write does not
restore them. Unknown readback outcomes are not automatically retried.

## Read-only tools — available

| Say or type | What Vex does |
| --- | --- |
| `Which applications are supported?` | Reads the app catalog; this is not a scan of all installed or running apps. |
| `Show my system information.` | Reads the operating system, OS release, architecture and logical CPU count. CPU/RAM usage percentages are not measured by this tool yet. |

App launch/status tools exist in the core but are not currently exposed to the
conversation. Do not assume `Open Notepad` is supported by the model yet.

## Timers and stopwatches — available in the native desktop app

| Say or type | What Vex does |
| --- | --- |
| `Start a five-minute timer called Tea.` | Creates an independent running timer with its own ID. Existing timers continue. |
| `Create another ten-minute timer called Pasta.` | Creates a separate timer; does not replace Tea. |
| `Start a stopwatch called Workout.` | Creates a running stopwatch and automatically selects the Stopwatch tab and record. |
| `Create another stopwatch.` | Creates another independent record; start or ready follows your request. |
| `Show my timers and stopwatches with their IDs.` | Reads their actual labels, states, elapsed and remaining times. |
| `Pause the Tea timer.` / `Stop the Workout stopwatch.` | Pauses the specified unambiguous record without clearing its elapsed time. |
| `Resume the Workout stopwatch.` | Starts/resumes the same record; does not create a replacement. |
| `Reset the Tea timer.` | Stops it and restores its original duration in ready state. |
| `Reset the Workout stopwatch.` | Stops it and returns elapsed time to zero. |

A timer operation selects Timer; a stopwatch operation selects Stopwatch,
even if the other tab was open. The record picker follows the selected theme;
changing it plays the existing UI sound (when SFX is enabled). Automatic refresh
and model focus do not play a selection sound. Use the dropdown for existing records or
**New** for another ready clock. Timer presets create another running timer;
**Set** updates the selected timer duration and resets it to ready, keeping its ID; if none exists it creates a ready timer. Start/resume/pause/reset buttons
control the selected actual ID, through the same backend tools as Vex.

Vex must read a fresh `clocks.list` or create the record in this turn before
control. If the target is unclear or multiple labels match, clarify the ID;
the displayed tab alone does not choose the model's target. One year's duration
is the per-timer maximum. Clocks live only while this app process runs; exit
loses them. Sleep and model disconnect do not reset them. Stop Task stops the
conversation/task, not an already verified running clock. Unknown mutations
are not retried. Clock removal is available only through the native UI list: open the picker,
right-click the actual timer/stopwatch row and choose **Delete**. It removes only
that record after backend confirmation and plays the existing delete sound when
SFX is enabled. This is not a spoken/model command; Vex has no clock-delete tool.
Clock persistence is not implemented.
Without the native backend, the existing single timer/stopwatch UI stays local;
those are not model integrations. Alarm timing depends on the UI being active;
a late UI refresh reads the correct backend deadline but is not a system alarm.

In the native app, a finished timer also requests a brief spoken Live notification
in your saved language and personal style. No fixed “boss” phrase is used; an
honorific is requested only when your personal preferences ask for one. Mic Off
still allows output; Mute suppresses it. The notification exposes no action tools.
It waits for an active conversation to finish and does not speak while asleep.
Stop and connection/model/key/sleep context resets discard older pending events;
failed or stopped notifications are not automatically repeated. Valid Live access
is required for speech; the local alarm still works independently of that access.


## Application shutdown — available

| Say or type | What Vex does |
| --- | --- |
| `Close TaskVex.` / `Shut yourself down.` | Requests closing this assistant app. Vex finishes its reply/playback, then uses the same native cleanup and closure as the Shutdown button. Windows is not shut down. |

The registered tool accepts a pending request; it does not prove that the
window has closed. Stop, interruption, stale connection, failed playback or an
unknown turn prevents the pending closure. Old tool-call replay cannot close
a new turn. Sleep and shutdown together require clarification. A request to
shut down the computer is outside this tool's scope; ambiguous targets should
be clarified. No phrase list is used to interpret application actions.

## Conversation and desktop controls — available

| Request or control | What happens |
| --- | --- |
| `Explain what a CPU does.` | Answers a general question; this is not a system measurement or a saved operation. |
| `For this conversation, my favorite color is purple.` then `What color did I mention?` | Uses recent conversation context, including after a Live session reset. This does not create a permanent user profile. |
| **Microphone Off / On** button | Disables/enables microphone capture. Off does not interrupt Vex's reply. Its label, light and pressed state show only your On/Off input preference. Errors and connection states are shown separately; On does not guarantee a working device. Each click uses the camera click effect, respecting Sound effects and Effects volume. |
| **Stop Task** button | Requests cancellation of the current response/task. Completed actions remain completed; controls wait for confirmed termination. A normal confirmed stop shows neutral LIVE READY, not a connection failure. |
| **Mute / Unmute** button | Mutes/unmutes voice playback; sound effects are separate. |
| **Disconnect** button | Releases the model connection/audio resources. |
| **F11** | Toggles fullscreen in the native desktop app. |

If the browser suspends the microphone audio engine, Vex tries to resume the
same source once, within one second. A failed recovery shows a separate error;
use **Microphone Off**, then **On** to prepare a new source. This does not replay
your previous command. An idle timeout includes PCM sent/event counts and a
wait phase for troubleshooting; these do not prove the provider caused it.

The buttons above are UI controls, not implemented spoken commands. Temporary
memory is held only in RAM: up to 12 recent turns and 16,000 JSON characters,
with each user/assistant text limited to 2,000 characters. Older turns are
dropped, not summarized. Stop, Disconnect and model changes preserve it;
Application exit, an API-key update or a saved-personal-memory change clears it. On a fresh Live
connection, history is supplied as data without replaying old tool calls.
Reused/resumed sessions do not receive duplicate history. This is not perfect
recall or a substitute for reading current saved notes. Restart loses it.

## Sleep and wake — available in desktop Live mode

| Say, type or select | What happens |
| --- | --- |
| `Go to sleep.` / `Switch to sleep mode, please.` / `Sleep mode gir.` | Asks the model to request one-time sleep using `mode=once`. Addressing Vex is optional while awake; these are examples, not fixed matching phrases. |
| **Sleep** button | Sleeps after the current turn has finished. Does not enable or disable the persistent return preference. |
| Say `Vex` while asleep | The local detector wakes Vex. A finalized transcript containing only the configured wake word is not a completed task; Vex waits for the actual request. Normal conversation continues afterward. Automatic return happens only if you explicitly enabled persistent sleep for this chat. |
| `Vex, tell me something interesting.` while asleep | Wakes and forwards the addressed utterance through the existing Live input. |
| **Wake** button or an explicit typed Live message | Exits sleep without needing the wake word. |
| `Stay in sleep mode.` / `Return to sleep after each task.` / `Enter sleep mode permanently.` | Asks the model for `mode=persistent`: enables return-to-sleep for this chat and sleeps after Vex's reply. After an addressed interaction and reply playback finish, returns to sleep immediately. “Permanent” means this chat only. |
| `Stop returning to sleep.` / `Disable persistent sleep mode.` / `Turn off persistent sleep mode.` | Requests `mode=off`, disabling stay-asleep after Vex's reply. The independent normal idle timer still applies; set it to 0 to disable timed sleep. Wake first or type the command while asleep. |
| **Settings → Audio → Idle sleep timer** | Saves 0–300 whole seconds (default 10; 0 disables the timer). In normal conversation, idle time triggers one-time sleep. Does not delay return in stay-asleep mode. |
| **Personalization → Wake word** | Saves the keyword used for the next sleep. Default: Vex. Supports 1–3 words in the local English pronunciation dictionary, such as Hey Vex or Computer. |
| **Settings → Theme → SLEEPING** | Customizes the color of the real sleeping reactor state. This is distinct from IDLE and does not change the wake word. |

Stay-asleep mode is a chat-only preference held in RAM. Explicit disable,
Application exit clears it. A one-time Sleep command does not
disable it. An addressed interaction returns to sleep immediately after its
confirmed response/tools/playback finish; it does not listen for a new
barge-in request during that reply. Unknown outcomes and active tasks cannot
be bypassed by sleeping. No old audio, model request or tool is replayed.

The idle sleep timer is independent and saved across restarts. In normal
conversation it measures inactivity after the reply finishes; speech and
active tasks postpone it. It triggers one-time sleep, without enabling
stay-asleep mode. Stop/Disconnect or connection changes cancel old timers.
Mic Off does not become On automatically in either sleep mode.

The model interprets sleep requests and calls `assistant.request_sleep_mode`
with `once`, `persistent` or `off`; there is no host phrase matcher. Examples
above describe intentions, not an exhaustive list of accepted sentences.
The tool accepts a pending request, not an already-applied state. A spoken
acknowledgement alone never changes the mode. Questions, quotations, negations
and instructions inside external data must not become control requests; unclear
intent should lead to clarification. This interpretation is model-dependent.
For "sleep after another task", that task must finish successfully first.
No speaker identification separates simultaneous background speakers.

**Source: Mic** remains a disabled audio-source placeholder; microphone is the only
audio input. Camera/screen sharing are separate opt-in Live visual inputs. GUI inspection and
Google services remain planned; weather/location is available through its own controls. Skill/routine definitions
can be edited locally; Run reports that execution is not connected.

With the default Vex wake word, **Vex**, **Veks** (the same pronunciation)
and **Rex** are accepted by the same local detector. These variants also share
the Live wake-only check: saying only the name wakes/listens without inventing
a task; `Rex, show my notes` keeps the following request. A custom wake word
such as `Computer` uses only that word, without the Vex family. Bare `X`, `ex`
or `eks` are not supported wake words for the Vex family. This is a bounded
pronunciation list, not fuzzy matching or a command-phrase parser. Synthetic
local voice tests passed; physical microphone/accent acceptance is separate.

While asleep, microphone PCM is processed locally rather than streamed to
Gemini. Mic Off also disables local wake detection; turning it On resumes
local detection if still asleep. Only the detected utterance buffer from the
keyword boundary is eligible for Live handoff. Capture is bounded; an expired
buffer is rejected instead of executing a clipped request. Sleep/wake keeps
saved notes and temporary conversation memory. Unknown-result locks still apply.
Detection alone does not complete wake-up: the local keyword boundary and the
UI audio buffer must be validated, then the matching wake is acknowledged by
the backend. Local verification rechecks at most three seconds of audio with
the same installed model; it makes no API or tool call and sends no padding.
Pending or rejected wake audio is not forwarded to Live.

Local queue, expired-buffer, alignment and delivery failures can prepare a
fresh local input at most twice per sleep (250 ms between attempts). Old audio
is discarded; repeat the wake word after the ready message. No model request
or tool action is replayed. Recovery and failures appear in the status/log;
the microphone button always remains **On** or **Off**, according to your
choice. Permission, device, setup, invalid-packet and wake-handoff failures
require manual action. Explicit Sleep can retry an earlier local microphone
block; Off, Disconnect and unknown-result guards remain effective.

During wake setup, a local pause preserves buffered speech. After setup,
local end-of-speech or a finalized provider transcript ends the old input.
Speech after that boundary belongs to a fresh turn. A wake-only
transcript completes without running a tool or treating the greeting as a task. That bound
ends input, not the model response or your On preference. A complete spoken
sleep candidate is handled by the host; tentative matching phrases that
become questions are not treated as sleep commands.

Sleep first shows **Preparing sleep**. **SLEEPING / Wake** appears only after
the host confirms sleep. A rejected request stays awake; an unknown result
locks controls instead of claiming success. Microphone Off remains usable.
Replayed calls from earlier turns do not schedule another transition. Conflicting
sleep modes in one response are rejected. A failed tool prevents a pending
sleep request from being applied.
Spoken or typed sleep controls receive Vex's own model response. The application
waits for that response and its audio playback to finish before applying sleep
or disabling stay-asleep mode. No packaged voice clips or replacement assistant
messages are used. Stop, a failed response or unknown result does not confirm
the requested change. The Sleep button and idle timer apply sleep directly;
automatic return after a task does not request an extra acknowledgement.

After backend input setup is ready, 700 ms of local silence ends that input.
The host sends explicit activityStart/activityEnd markers with provider VAD
disabled; it does not mix these markers with audioStreamEnd. Setup-time wake
pauses preserve buffered speech. A 15-second cap remains. A temporary input
queue/transport failure may prepare fresh listening at most twice after the
old turn is confirmed finished. It never replays the discarded request;
repeat your request when ready. Permission/unknown failures remain blocked
with an explicit reason rather than only a generic Stopped status.

Wake-only classification still needs the provider's final transcript; it does
not eliminate all API latency or the pending 25-second silence investigation.

The pinned local model must be installed. It is installed on this development
machine; on a new installation, run the following from `v1` once:

```powershell
.\.venv\Scripts\python.exe -m app.session.wake_word --setup
```

If the model or keyword is unavailable, sleep stays active; use Wake to exit.
Explicit Wake retries normal Live microphone preparation after a local detector
failure. It preserves Microphone Off and cannot bypass an unknown active result.
The local stream refreshes every 60 seconds and can miss a word at that
boundary. Real microphone/accent accuracy is pending manual acceptance.
The Wake sensitivity slider now controls the local keyword detector on the next
sleep entry. Higher means easier triggering and potentially more false wakes;
50 preserves the previous threshold. It does not change the wake-word vocabulary.
The speech detection threshold controls the existing microphone worklet live;
browser noise suppression remains enabled. The meter shows measured activity
only while the existing capture is active; Mic Off resets it to zero.
Idle sleep +/- buttons adjust the same saved 0–300 second timer setting.

## Planned — not available yet

- Silent, unapproved personal-memory learning. Optional suggestions with button or spoken approval are available below.
- Model-driven skill/routine/calendar/weather/Google/Telegram/Discord actions.

Move an item into the available tables only after its implementation and
relevant verification. A visible UI panel or saved setting alone is not an
implemented conversational command. REST is reserved for future tool/channel
uses; the intended main desktop experience is Live.

## Connection settings — available UI behavior

Settings → Connection → **Live voice** → Choose a documented prebuilt voice
labelled `[LIVE]`. The saved choice applies to the next Live text, microphone
or timer reply; it does not interrupt the current answer. Changing voice opens
a fresh Live scope rather than resuming the old voice session. REST TTS keeps
its separate voice. The voice list comes from Google documentation, while model
discovery comes from the API; custom/TTS-only voices are not offered.

The API key input shows **API key configured — enter a new key to replace** as
placeholder text after a confirmed configured status. Its actual value stays
empty. This confirms key presence, not successful API access.

Settings → Audio → **Vex reply volume** → Adjust voice replies and spoken timer
notifications from 0 to 100%, independently of Effects volume. Changes apply
to the current reply immediately and are saved across restarts. At 0% playback
is silent; microphone input stays unchanged. Mute temporarily silences output;
unmuting restores the selected level. Reset restores 100%. This is a UI setting,
not a new spoken command or a voice/personality selector.

Save an API key once in Settings → it stays in Windows credential storage for
this TaskVex data profile; the app never puts it in a JSON backup or browser store.
Choose a returned Live model → the selection is saved and restored if still
returned by the API. Live models load automatically at native startup and after
saving a key. There is no Load Live Models button, invented catalog or automatic
retry loop after failure; reopen or explicitly save the key to try again.
Google account integration is still planned; removing the button emoji does not
implement account access.

The record picker supports Enter/Space, Tab, arrow keys, Home/End and Escape.
A click outside closes it. Delete is disabled during a model turn or an uncertain
clock operation. Removing a clock also discards its pending spoken completion
notice when the current snapshot is read. No automatic retry follows failure.

## Starting the desktop app

A second native instance using the same data profile is rejected before starting
its worker/window. Close the existing app first. Separate TASKVEX_HOME profiles
are independent. A crash releases the OS lock; do not delete the lock file.

Native tool requests keep their IDs and results in a local task journal across
restarts. A repeated request ID returns its historical result, rather than
running again. Unfinished started actions become unknown and block new tools;
restarting does not clear that uncertainty. This is separate from conversation
memory and does not restore timers. There is no lifetime 256-task limit in the
native app; active work and in-memory records remain bounded. Do not delete the
journal to bypass a lock.

- **Retry** → Retry native initialization after a transient failure; does not
  reset settings or approve uncertain actions.
- **Back up and repair settings** → Offered for invalid/damaged settings only.
  Confirmation preserves the original file, keeps valid fields and leaves task
  history and backend notes intact. Unsupported versions/access failures are not reset.
- **Review previous actions and continue** → Startup lists unknown tool/task IDs.
  Check their effects first, then confirm accepting uncertainty. This permits new
  work without retrying or rewriting old results. Acknowledgement survives restart;
  newly unknown actions need separate review. It does not verify success or undo
  anything. Cancel keeps work blocked. Storage failure cannot be bypassed here.


## Personal memory — manual Personalization controls

- **Personalization → Personal memory** → Enter facts you want Vex to use.
  **Save profile** stores them locally. Edit and save to correct; clear and save
  to forget. This is one editable document, not automatic learning.
- **Use saved personal memory in replies** → Explicitly enables sending those
  facts to the model in future replies. Off by default, including for old saved
  text. Turning off keeps the document locally without sending it.
- `What do you know about my school?` → When enabled, the model can use the
  facts you saved. Its inference is not automatically stored as a user fact.
- Corrections, deletion or disabling apply to the next reply and drop the old
  Live session/temporary context. They do not interrupt the current reply or
  erase past provider requests, existing messages, backups or task history.
- Restart keeps the saved document and opt-in choice; temporary chat memory
  remains RAM-only. The New Chat button has been removed.
- Explicit spoken or typed memory changes use the model tools described below.


## Personal memory — explicit model commands

Enable **Use saved personal memory in replies** in Personalization first.
REST and Live use the same local profile document; these are examples of intent,
not fixed phrases or a separate language parser.

| Say or type | What Vex does |
|---|---|
| “Remember that I study engineering.” | Reads the current memory, then appends the fact explicitly requested. |
| “What have you saved about me?” | Reads the saved personal-memory document, rather than guessing from chat. |
| “Correct my saved school from Alpha to Beta.” | Replaces one unambiguous exact passage while keeping unrelated facts. |
| “Forget my saved school.” | Reads and removes the uniquely identified saved passage; asks if unclear. |
| “Forget all saved personal information about me.” | Clears the profile memory document; keeps the opt-in preference unchanged. |

The editor refreshes from the backend after tool results without sending another
mutation. Conflicting edits or changed snapshots do not overwrite data or retry
automatically. A stale-form save can require restarting the app before editing
again. Memory changes apply to the next turn and drop old Live/temporary chat
context. Completed changes survive Stop and restart; an uncertain result must
not be retried. Forgetting does not erase existing replies, provider history,
backups or the persistent local task journal. Automatic learning is not enabled.


## Optional memory suggestions

- **Personalization → Learn personal facts from conversation** → Enables
  learning only while **Use saved personal memory in replies** is also on.
  Both choices are saved; learning is off by default.
- “By the way, my name is Ada.” → Vex may propose this durable self-reported
  fact without a “remember” command. With review enabled, a proposal is not saved personal memory.
- **Save** in the separate group to the right of the four conversation controls → Reviews the exact fact and its source
  message, then saves the current candidate through the existing memory tool.
- **Dismiss** → Drops the candidate without changing saved memory.

With learning enabled, all model additions, including explicit “remember”
requests, follow **Ask before saving learned information**. When checked
(default), Vex asks naturally whether to save the specific fact. Say or type
“Yes, save that” or “No, dismiss it”, or use **Save/Dismiss** beside the conversation
controls. Personalization does not open. These examples are not fixed phrases;
ambiguous replies require clarification.
When unchecked and saved, Vex writes verified new facts directly into the
Personal memory field without asking. Corrections and forgetting keep their
explicit-command flow. With suggestions off, existing explicit remember commands
still work. Spoken/text decisions use the same current candidate and verified
core action as the buttons. The model cannot approve its own proposal in the
same turn and must freshly read the actual pending ID in a later user turn.

The model is instructed to exclude third-party facts, quotations, jokes,
hypotheticals, transient states, sensitive details and personality guesses.
These semantic decisions are not guaranteed: review the candidate before saving.
The host attaches the actual current user message/transcript as the source;
Vex does not have to reproduce its wording exactly. Missing user speech
transcription never authorizes a tool call. In review mode only one candidate waits in RAM; a new one
replaces it, and restart discards it. Pending candidates are not exported as
profile memory, but local task history can contain their text. Changed memory or
consent invalidates an old approval. No automatic retry or merge is performed.


## Token display

- Send Live or REST messages → The header shows the application session's
  reported token total, including REST tool rounds and separately requested
  speech synthesis. Open System settings for the scope and completeness label.
- Stop, Disconnect or changing models → The application total remains.
- Restart the application → A new session counter starts; usage is not persisted.
- Missing usage metadata → The known total remains with ≥ and an Incomplete
  label. If no usage has been reported yet, the display is unknown.
- The counter is not account quota, remaining credit, context fullness or a
  billing guarantee. No extra token-counting API request is made.


## Local system readings

| Say or type → | What Vex does |
|---|---|
| “What is my CPU and RAM usage?” | Calls system.status to read the same locally sampled values shown in the UI. CPU averages a sampling interval; the initial sample can be unavailable. |
| “How much disk space am I using?” | Reads used/total space on the application's runtime volume; this is not disk transfer speed. |
| “What is my battery level?” | Reads the OS battery report; no battery and unknown data are distinct. |
| “Which application is active?” | Reads the foreground executable name. It does not read document/window titles or window contents. |

The UI refreshes local readings without requiring a model connection. Missing
values remain unavailable, never invented zeroes. CPU/GPU temperatures and remote
internet probes remain unavailable. Windows GPU readings are described below. System readings use the existing shared
registry/policy/TaskManager model path; UI polling reads the same local owner.


## Windows GPU readings

| Say or type → | What Vex does |
|---|---|
| “What is my GPU usage?” | Calls system.status for the shared Windows performance-counter sample, across vendors when supported by the OS. |
| “Which GPUs are measured?” | Reads gpu_devices with OS adapter IDs and percentages. IDs are not product names or Task Manager display indices. |

Each adapter reports its busiest engine after summing processes on that engine.
The dashboard's single GPU bar displays the busiest adapter; it does not sum
separate cards or engines. First samples and unavailable counters display —;
zero is valid. The shared sample cache is two seconds, with UI polls at least
three seconds apart. No vendor CLI, new driver or monitoring service is used.
GPU/CPU temperature, VRAM capacity and friendly adapter names are unavailable
from this source. Unsupported Windows/WDDM counters remain unavailable.


## Local network traffic and physical link

| Say or type → | What Vex does |
|---|---|
| “What is my current receive and send traffic?” | Calls system.status for interval bytes per second from the same local sample as the dashboard. |
| “Am I connected through Wi-Fi or Ethernet?” | Reads physical adapter link state and connection kind; multiple active kinds are reported explicitly. |

The dashboard shows Receive/Send in Mbps and local link/Wi-Fi connected status.
These are passive OS readings, not an internet speed test, data quota, maximum
link capacity or a guarantee of internet access. First samples, counter resets,
adapter-set changes and unavailable data do not become zero; measured zero is valid.
Only physical interfaces are counted; virtual/VPN/loopback counters are excluded
to avoid duplicate packet accounting. No SSID, IP/MAC or adapter profile names
are returned. No remote requests or network configuration changes are made.
Gateway ping and Wi-Fi signal quality use the bounded source below; API transport latency remains pending.


## Gateway ping and Wi-Fi signal quality

| Say or type → | What Vex does |
|---|---|
| “What is my gateway ping?” | Reads the cached IPv4 physical default-gateway ICMP RTT, status and sample time through system.status. |
| “How strong is my Wi-Fi signal?” | Reads the OS connection quality percentage; with multiple Wi-Fi adapters it reports the weakest connected adapter. |

These use the same Telemetry owner as the dashboard. Gateway ping is a local
router measurement, not internet/API latency or a speed test. One echo waits
up to 250 ms, normally at most once per ten seconds; a card/route change refreshes
it immediately. No arbitrary host, DNS lookup, public probe service or network
scan is offered. A timeout does not prove internet loss. IPv6-only/VPN-only
routing is outside the physical IPv4 gateway scope.

Wi-Fi uses the location-free realtime quality opcode. Older/unsupported Windows
or denied data stays unavailable; TaskVex does not fall back to location-sensitive
queries. 0% signal and 0 ms ping are valid. The UI tooltip shows status and sample
age. No gateway address, SSID, MAC or device GUID is returned. API transport
latency remains unavailable until a separate real transport metric is defined.


## Current Windows media session

| Say or type → | What Vex does |
|---|---|
| “What is playing right now?” | Calls media.status for the current session selected by Windows, including the reported title, artist and playback state. |
| “Is the current media paused?” | Reads the same OS sample as the dashboard; paused and playing are distinguished. |

This is metadata provided to Windows by the source application, not audio
capture, a browser tab scan or all currently audible sounds. Some apps do not
publish a media session. No_session is distinct from unavailable/unsupported/
timeout; missing data must not become a claim that nothing is playing.
The UI updates every few seconds and clears stale/failed samples. Model reads
may store returned metadata in the existing task journal; background UI polling
does not journal each sample or send it to a model.

| Say or type → | What Vex does |
|---|---|
| “Pause the current music.” | Reads the current session and requests pause; verifies the paused state. |
| “Resume playback.” | Reads the current session, requests play and verifies the playing state. |
| “Skip to the next track.” | Requests next once, then verifies changed title/artist on the same session. |
| “Go to the previous track.” | Requests previous once; requires an observed track change for verified success. |
| “Set the player volume to 30%.” | Reads the current media/audio target, sets only its application volume and verifies the Windows readback. |
| “Lower the player volume by 10 percentage points.” | Reads the actual level, then requests an absolute level 10 points lower, bounded to 0-100. |

The Media panel's previous/play-pause/next buttons use the same backend tools.
Unsupported or stale controls stay disabled; manual buttons wait during a model
reply. Only Windows' current session is targeted, with no app/tab picker. These
are examples, not phrase matching rules; REST and Live share structured tools.
An accepted request without observable confirmation remains unknown and is never
automatically retried. Same-title skips or a player restarting the same track may
be unknown. Restart does not clear the persistent safety lock. Real player/provider
acceptance is separate from synthetic/native transport checks.

The volume slider below the Media buttons uses the same media.control action
set_volume. It does not change Windows master volume or Vex reply/effects volume.
Browser audio is application-wide, not a per-tab volume control. Unsupported or
ambiguous audio-session mapping disables the range; it never targets another app
or falls back to system volume. Existing mute is preserved. Windows owns the actual
level; TaskVex does not save a second preference. Operation results stay in the
accessible status/Engine log rather than visible text below the buttons.


## Weather

| Say or type → | What Vex does |
|---|---|
| “What is the weather here?” | Reads modelled current weather for the approved saved location. If unset, asks you to configure one. |
| “What is the weather in London?” | Searches real place candidates; clarifies ambiguous places, then queries the selected actual ID without changing the dashboard's saved place. |

Settings → Connection → Weather Location: enter a city/district, Search, then
explicitly choose its labelled result. Auto asks for sharing consent and browser
location permission, saves only approximate coordinates, and is never triggered
automatically at startup. Clear stops future saved-location requests. The saved
location survives restart; the cache and unsaved search IDs do not.

No Gemini/API key is required for the weather dashboard. Open-Meteo supplies
modelled current conditions in Celsius/km/h, not a local measurement or tomorrow's
forecast. Model requests still use the configured conversational provider. The UI
shows source time and STALE on failed refresh; unavailable values are not zero.
Location consent is native-only and is not imported/exported by legacy UI backups.

## Portable Windows demo

- Extract the entire `TaskVexDemo-Windows-x64.zip`, then open `TaskVexDemo.exe`.
  Python is bundled; Windows 10/11 x64, .NET Framework 4.8 and WebView2 are required.
- Enter your own Gemini key in Settings. The demo uses a separate TaskVexDemo
  profile by default; no developer key or notes are supplied.
- Optional: close the app and run `Setup wake model.cmd` once online. It invokes
  the existing verified upstream download; model weights are not in the ZIP.
  Without setup, local wake from sleep is unavailable. This is setup, not a
  natural-language command or a claim that all hardware has been tested.

## Camera — Live input

- **Camera On** -> explicitly opens the camera selected in Settings > Audio.
  While idle, images stay local; during the next Live voice/text message, current
  images are shared with the model. No camera is opened automatically at launch.
- **Camera Off** -> releases capture and stops new images; the current reply and
  microphone continue. Images already sent remain part of the provider context.
- Say or type **"Describe what you can see through the camera"** -> with Camera On,
  Vex can answer from the current Live images. This is understanding, not GUI control.
- **Stop Task** -> ends this turn's image transmission as well as the model turn.
  Camera may stay locally ready; another explicit user message starts fresh input.
- **Sleep / Disconnect / model or key change** -> releases the camera. Enable it
  manually after wake/reconnect. Device selection persists through Save Settings;
  camera On does not persist, and no permission is silently re-requested.

No REST visual input, image file attachment or model-controlled
camera activation is included. Images are bounded JPEGs; real camera permissions,
lighting and provider understanding require separate manual acceptance.

## Screen sharing — Live input

- **Screen sharing controls (bottom-right information button) -> Share screen** ->
  with an awake, ready Live model and no reply running, choose a screen/window
  through the platform picker. Camera must be Off first. Cancelling leaves sharing Off.
- Say or type **"Describe the window I am sharing"** -> the current Live message
  receives bounded screen images on the existing connection. Idle images and the
  preview stay local; no system audio is captured. Small text may be unreadable.
- **Share screen Off / platform Stop sharing** -> release capture and clear the
  preview without stopping the microphone or current reply. Already sent images
  cannot be recalled. Closing the drawer only hides it; sharing remains enabled.
- **Stop Task** -> ends this turn and its frame transmission. The source may stay
  locally ready; sleep/Disconnect/model or key change/page close releases it.
- **Enable sharing again** -> choose the source again. A screen grant/selection is
  not saved, restored at launch or acquired automatically after sleep/reconnect.

One camera or screen source at a time. Video-only JPEG frames are sent at most
once per second, with 1280-pixel screen edge and 256 KiB frame limits. This is
visual understanding, not GUI clicking or skill creation. The user reported successful
tests; exact platform/provider coverage was not independently enumerated. Additional
audio-source/recording sharing is deferred to stage 9.4 and is not available today.

## Permissions settings

- **Settings > System > Permissions > Request access** -> ask for Camera,
  Microphone or Location independently of Live readiness/device selection.
  Media is briefly opened then closed; location is checked and discarded. This
  does not turn input On, connect Live, share images/audio or set weather location.
- **Windows settings** beside a permission -> open that Windows privacy page;
  enable access there if needed, then return and request access again.
- **Refresh permissions** -> read reported browser states without requesting access.
  Not reported means the browser cannot query this permission. Allowed in browser
  does not prove OS/hardware access. There is no fake Save Settings permission flag.

Permissions can remain blocked by OS/browser policy; the app cannot force a grant.
Use Camera On/Microphone On for ongoing input and Weather Auto for an explicitly
approved saved weather location. Their existing lifecycle/consent rules remain.
