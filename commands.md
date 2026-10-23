# TaskVex command guide

This file describes what you can currently ask Vex to do. It is a user guide,
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
| `Delete the note "Buy milk".` | Deletes one unambiguous existing note. |
| `Delete the note with ID <note-id>.` | Deletes only the selected record, even if other notes have the same text. |
| `Delete the note containing "merh".` | Deletes a note only if the quoted literal text identifies exactly one match. |
| `Delete my latest note.` | Deletes the uniquely newest note by creation timestamp, not by list position. |

Before editing or deleting, Vex must read the current notes and use their real
IDs. If several notes match, it should ask which ID you mean and preserve them.
The literal substring and latest-note selectors also work for a single update.
Do not combine them in one target description; fuzzy matching is not supported.

Date ordering is presentation over `notes.list`, not a separate date-query tool.
Older/imported notes may have no creation timestamp; Vex must not invent one.
If any timestamp is missing or the newest timestamp is tied, a latest-note
mutation requires an explicit ID. Editing a note preserves its creation time.

Bulk deletion such as `Delete all my notes` or `Delete my last two notes` is
not currently offered as a supported command.

## Read-only tools — available

| Say or type | What Vex does |
| --- | --- |
| `Which applications are supported?` | Reads the app catalog; this is not a scan of all installed or running apps. |
| `Show my system information.` | Reads the operating system, OS release, architecture and logical CPU count. CPU/RAM usage percentages are not measured by this tool yet. |

App launch/status tools exist in the core but are not currently exposed to the
conversation. Do not assume `Open Notepad` is supported by the model yet.

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
Rex/X-like local wake alternatives are not implemented yet.
No speaker identification separates simultaneous background speakers.

**Source: Mic** is a separate audio-source selector placeholder. The UI has
PC/app audio labels, but only microphone capture is currently implemented in
the desktop backend. Those other sources are not working integrations yet.

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
The existing Wake sensitivity slider is not yet connected to this detector.

## Planned — not available yet

- Persistent user facts and editable/forgettable user memory in Personalization.
- Model-driven skill/routine/calendar/weather/Google/Telegram/Discord actions.

Move an item into the available tables only after its implementation and
relevant verification. A visible UI panel or saved setting alone is not an
implemented conversational command. REST is reserved for future tool/channel
uses; the intended main desktop experience is Live.
