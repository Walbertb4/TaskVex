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
| **Microphone Off / On** button | Disables/enables microphone capture. Off does not interrupt Vex's reply. Its light shows the ready, unblocked On preference and stays steady during a normal Stop resource handoff. |
| **Stop Task** button | Requests cancellation of the current response/task. Completed actions remain completed; controls wait for confirmed termination. A normal confirmed stop shows neutral LIVE READY, not a connection failure. |
| **Mute / Unmute** button | Mutes/unmutes voice playback; sound effects are separate. |
| **Disconnect** button | Releases the model connection/audio resources. |
| **F11** | Toggles fullscreen in the native desktop app. |

The buttons above are UI controls, not implemented spoken commands. Temporary
memory is held only in RAM: up to 12 recent turns and 16,000 JSON characters,
with each user/assistant text limited to 2,000 characters. Older turns are
dropped, not summarized. Stop, Disconnect and model changes preserve it;
New Chat, application exit or an API-key update clears it. On a fresh Live
connection, history is supplied as data without replaying old tool calls.
Reused/resumed sessions do not receive duplicate history. This is not perfect
recall or a substitute for reading current saved notes. Restart loses it.

## One-time sleep and wake — available in desktop Live mode

| Say, type or select | What happens |
| --- | --- |
| `Vex, go to sleep.` / `Enter sleep mode.` | Enters one-time sleep. Exact Turkish equivalents include `Vex uyku moduna geç` and `uykuya geç`. Quotes, questions and compound requests are not treated as sleep commands. |
| **Sleep** button | Enters the same sleep mode after the current turn has finished. |
| Say `Vex` while asleep | The local detector wakes Vex. Normal conversation continues afterward; it does not automatically sleep again. |
| `Vex, tell me something interesting.` while asleep | Wakes and forwards the addressed utterance through the existing Live input. |
| **Wake** button or an explicit typed Live message | Exits sleep without needing the wake word. |
| **Personalization → Wake word** | Saves the keyword used for the next sleep. Default: Vex. Supports 1–3 words in the local English pronunciation dictionary, such as Hey Vex or Computer. |

While asleep, microphone PCM is processed locally rather than streamed to
Gemini. Mic Off also disables local wake detection; turning it On resumes
local detection if still asleep. Only the detected utterance buffer from the
keyword boundary is eligible for Live handoff. Capture is bounded; an expired
buffer is rejected instead of executing a clipped request. Sleep/wake keeps
saved notes and temporary conversation memory. Unknown-result locks still apply.

The pinned local model must be installed. It is installed on this development
machine; on a new installation, run the following from `v1` once:

```powershell
.\.venv\Scripts\python.exe -m app.session.wake_word --setup
```

If the model or keyword is unavailable, sleep stays active; use Wake to exit.
The local stream refreshes every 60 seconds and can miss a word at that
boundary. Real microphone/accent accuracy is pending manual acceptance.
The existing Wake sensitivity slider is not yet connected to this detector.

## Planned — not available yet

- Persistent user facts and editable/forgettable user memory in Personalization.
- Automatic return-to-sleep after an interaction.
- A sleep-delay setting in Settings.
- Model-driven skill/routine/calendar/weather/Google/Telegram/Discord actions.

Move an item into the available tables only after its implementation and
relevant verification. A visible UI panel or saved setting alone is not an
implemented conversational command. REST is reserved for future tool/channel
uses; the intended main desktop experience is Live.
