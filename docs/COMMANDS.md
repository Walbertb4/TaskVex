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
| `Delete the note containing "merh".` | Selects by literal substring and deletes only if there is exactly one match. Quotes are examples, not required command syntax. |
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
| **New Chat** button | After confirmation, clears the temporary conversation memory and displayed messages. Saved notes and preferences stay. Unavailable during an active/unknown request. |
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
New Chat, application exit or an API-key update clears it. On a fresh Live
connection, history is supplied as data without replaying old tool calls.
Reused/resumed sessions do not receive duplicate history. This is not perfect
recall or a substitute for reading current saved notes. Restart loses it.

## Sleep and wake — available in desktop Live mode

| Say, type or select | What happens |
| --- | --- |
| `Go to sleep.` / `Switch to sleep mode, please.` / `Uyku moduna gir.` | Asks the model to request one-time sleep using `mode=once`. Addressing Vex is optional while awake; these are examples, not fixed matching phrases. |
| **Sleep** button | Sleeps after the current turn has finished. Does not enable or disable the persistent return preference. |
| Say `Vex` while asleep | The local detector wakes Vex. A finalized transcript containing only the configured wake word is not a completed task; Vex waits for the actual request. Normal conversation continues afterward. Automatic return happens only if you explicitly enabled persistent sleep for this chat. |
| `Vex, tell me something interesting.` while asleep | Wakes and forwards the addressed utterance through the existing Live input. |
| **Wake** button or an explicit typed Live message | Exits sleep without needing the wake word. |
| `Stay in sleep mode.` / `Return to sleep after each task.` / `Uyku moduna kalıcı olarak gir.` | Asks the model for `mode=persistent`: enables return-to-sleep for this chat and sleeps after Vex's reply. After an addressed interaction and reply playback finish, returns to sleep immediately. “Permanent” means this chat only. |
| `Stop returning to sleep.` / `Disable persistent sleep mode.` / `Kalıcı uyku modunu kapat.` | Requests `mode=off`, disabling stay-asleep after Vex's reply. The independent normal idle timer still applies; set it to 0 to disable timed sleep. Wake first or type the command while asleep. |
| **Settings → Audio → Idle sleep timer** | Saves 0–300 whole seconds (default 10; 0 disables the timer). In normal conversation, idle time triggers one-time sleep. Does not delay return in stay-asleep mode. |
| **Personalization → Wake word** | Saves the keyword used for the next sleep. Default: Vex. Supports 1–3 words in the local English pronunciation dictionary, such as Hey Vex or Computer. |
| **Settings → Theme → SLEEPING** | Customizes the color of the real sleeping reactor state. This is distinct from IDLE and does not change the wake word. |

Stay-asleep mode is a chat-only preference held in RAM. Explicit disable,
New Chat or application exit clears it. A one-time Sleep command does not
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

**Source: Mic** is a disabled placeholder: only microphone capture is implemented.
Camera, screen inspection, Google/location, voice selection and media controls
are disabled until their backend integrations exist. Skill/routine definitions
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

- Persistent user facts and editable/forgettable user memory in Personalization.
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
journal to bypass a lock. Manual unknown reconciliation is not available yet.
