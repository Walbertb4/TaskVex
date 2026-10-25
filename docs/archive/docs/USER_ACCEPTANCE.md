# TaskVex — Actual usage checks that the user will participate in

## Current quiz — 5.R8.6

1. When Theme is purple and Sleeping color is orange, turn on Audio: sliders and Speak or Type
   The arrow should remain purple. The theme color should not change when you switch to Listening/Speaking.
2. Create two timers and two stopwatches. Open the list, right to the non-selected record
   click → Delete: only the record you right-clicked should be deleted; others should drive.
3. Delete the last record: “No timer/stopwatch” and 00:00. Reopen with New.
4. Open the list with the keyboard, navigate with the arrows, select Enter and click Escape/outside to close.
   Let the open menu fit the new theme; Delete will play the current deletion sound on success.

Previous five tests accepted with user confirmation applied/00c76ce. New slice user
awaits acceptance; counter deletion from the model was not added, debloat/closing was not done.

## Current quiz — 5.R8.2–5

1. Open the application normally: The catalog will appear without the Load Live Models button.
   Choose a model; Leave the same model selected without re-entering the close/open key.
   It is normal for the switch box to remain empty; The secret value is not returned to the DOM.
2. Save preference dil/form of address in Personalization; Start a 5-second timer.
   End with a single alarm and Vex's own voice sentence. If there is no address in the preference
   A special boss/stable is not expected to appeal. The output should continue on Mic Off; Mute must be silent.
3. Let the timer run out on long answers: notify the current conversation without interrupting it. notification
   Let it stop when you press Stop on your voice; Don't let the same ending start over again. sleep timer
   The voice model should not open the response. Alarm/UI and application open limit are preserved.
4. Speak in Audio: increase the level. Mic Off → 0. Threshold increase/decrease, speech
   Try its effect on perception; This slider does not turn on speaker sound or multiple microphones.
5. Wake sensitivity 50 previous behavior. Change the value and in the next sleep
   try wake-word; Higher value may cause more wake up than easy/wrong.
   50 is the default safe comparison; It cannot be called optimum without physical acceptance.
6. Idle sleep +/- and entering numbers with keyboard: 0–300 limit, new theme and click sound.
   Emoji should be removed from the Google button; account access has not been implemented yet.

Automatic proof: 988 pytest, 10 JS, targeted Pyright 0; native 10/10 and last chat.
New changes await manual acceptance/commit. Debloat and Phase 5 closing were not done.

October 23, 2026: user reported successful multiple timer/stopwatch tests.
This confirmation is from previous meter coverage; does not include subsequent visual/audio tweaks.

## Current quiz — 5.R8.1 selective theming and SFX

1. Reopen the application, create two timers and two stopwatches. In every tab
   switch to different register from selector; The correct duration/situation should appear and a single selection sound should be heard.
2. Change theme: selector, its edge and arrow should match the new color; long label
   It should not extend beyond the widget. Go to the selector with Tab, make selection with arrow keys;
   The focus should remain visible. Also check the open list view.
3. Turn off SFX: there should be no selection sound. Automatic time in normal open use
   Updates/model's focus recording should not produce selection sound.

Personalized voice notification of timer end is next 5.R8.2;
The existing fixed text has not been corrected this round. This slice awaits user acceptance.

## Previous quiz — 5.R7.2 multi timer/stopwatch

Reopen the application. Try buttons as well as automatic voice commands.

1. “Start a two-minute timer for tea,” then “Start a three-minute timer for pasta.”
   Say "start another timer". Let there be two separate records in Dropdown, and both of them will progress.
2. While the Timer tab is open, click "Start a stopwatch named Sports". Automatic Stopwatch
   Select the tab and Sports recording. Another one is hungry; The first record must be preserved.
3. “Stop tea timer”, “Stop sports stopwatch”, “Continue sports”,
   Say “Reset sports stopwatch”. Let each operation focus on the correct tab/ID;
   Let stop/continuation keep the time, reset stopwatch and set it to zero.
4. Select other record from Dropdown; Try UI pause/resume/reset buttons.
   Have the Vex list it: the status of the same records comes correct; Don't let the second one be affected.
5. Start a 3–5 second timer and try a single end alarm. Sleep/Wake or
   Disconnect times should not reset. If the application is close/open, the list should start empty.

Native New produces new ready recording. Timer Set changes the selected timer duration.
resets to ready state; ID is protected. If there is no timer, the first ready timer is created.
It does not affect other records. Counter deletion or persistence is not the scope of this step;
In particular, there is no counter deletion yet. Annotate with real ID on unknown target.
After this slice there are the final minor tweaks and debloat that the user will specify;
Phase 5 is not closed at this time. The real API/hardware acceptance is in this short test.

## Previous quiz — 5.R7.1 Shutdown

1. Re-open the app. Say “Vex, close yourself” or type “Close TaskVex.”
   Let the window close after the short response/sound ends; Keep Windows open.
2. Reopen; Press Stop while the response to the same request is playing. The window must remain open;
   the old answer shouldn't initiate a shutdown afterwards. Normal new message should work.
3. A negative request such as “Don't shut down, stay here” should not close the application.
   “Turn off the computer” should not become this tool; should ask for clarification on the vague target.

The actual language selection is user acceptance; synthetic tests are no guarantee of this.
The previous brief reception of Wake variations is still awaited. Timer/stopwatch multi
control was not added this round; next step is 5.R7.2. Stage 5 does not close.

## Previous quiz — 5.F4 wake variations

Reopen the application; wake-word Vex, microphone On.

1. Press Sleep and say “Vex”; then again in Sleep and “Rex”. Waking up every time
   should receive its next command. The pronunciation “Veks” is in the same family as Vex.
2. Put him back to sleep and say “Rex, show me my notes”; The remaining desire should not disappear.
3. Try “next,” “ex,” or casual conversation; These are not the intended wake.
   If there is a false awakening, let me know with what voice it happened; The probability is not zero in a short address.
4. When you set the wake-word to Computer, Vex/Rex should not trigger, Computer should trigger it.
   None of them should be listened to while the microphone is Off. You can then undo your choice.

This is just a brief acknowledgment of the new wake change. Separate by user request
long use step removed; Stage 5 does not close. Application such as shutdown
Linking controls to Vex will be covered in 5.R7, not added this round.

## Previous quiz — 5.R6 batch grade completion

Reopen the application; Just try it in the test profile with trial notes.

1. Add three different temporary notes, list their dates. “My last two notes have been completed.
   “check”: only check the boxes for the two new records; keep text/ID/date.
2. Say “Complete all my notes”; Let them all be marked. “I left all my notes unfinished
   Click “tick” to clear the boxes. Close/open; keep the current situation.
3. Let the text of two notes contain "experiment" and the other have different content. “Try in
   "Complete all passing grades" and only this group will be marked.
4. Ask for an explanation when requesting to complete a single note for two notes with the same text;
   Don't let him complete both silently. With the open real ID group, only that group should be changed.
5. Notes.select and then notes.complete_many verified should appear in the engine log.
   Also try a phrase like “Mark my last two notes as completed” in English.

REST and Live synthetic/native checks are done by the agent. real
The provider's acceptance of the new scheme and language interpretation are successful by the user.
reported (October 23, 2026). This result is not a guarantee of all future statements.

## Previous quiz — 5.R5 note selection / mass deletion

Reopen the application. It has no real notes, it's just full of temporary notes
use a test profile; Especially the delete all command should be tried in that profile.

1. Add three different essay notes. Say “Delete the last two notes I added”: only
   delete the two new records, keep the remaining note in the UI. Verify with Close/open.
2. Create a single note with “hello” in it. “The memorandum containing the anointing has been completed.
   mark”, then change its text and delete. No fixed phrases or quotes are required.
3. Add two temporary notes with the same text. Explanation for request to delete one with text
   Let him wish and protect both of them. When you select with Real ID, only that one will be deleted.
4. With more than one temporary “test” grade, “Delete all grades containing tests”
   de: only the selected group will be deleted. Then “Delete all my notes” in the test profile
   say; Let the panel and reboot be empty. You can also try the English equivalents.
5. Notes.select then notes.delete_many should be seen in the engine log. oral
   Success is not transaction proof without tool verified result. Notes selection
   If it changes during the time, it should ask you to vote again; It should not change target automatically.

Stop can only prevent deletion before writing; It does not undo a completed deletion.
List notes without sending the same command again after suspicious results. 5.R5 was reported successful by the user and was included in commit `2120113`.

## Previous quiz — Sleep with model 5.R4 tool

Close the app completely and reopen it, temporarily reducing the normal sleep time to 0.
do it Only new local test acceptance; The real account attempt was not made by the agent.

1. “Enter sleep mode permanently” de/yaz. in Engine log
   `assistant.request_sleep_mode: succeeded · verified` must be seen; Vex's own
   When the answer and ringing is finished it should be SLEEPING. This registration is an acceptance of the request;
   actual SLEEPING is the result of separate hosts.
2. Wake him up and ask a short question: when the answer is finished, let him sleep again. Then in writing
   In “Disable persistent sleep mode”; Close the option after the response is finished.
3. Using your own natural expression, such as “Wait a while, only answer when I call.”
   Ask for sleep just once. If the tense is unclear, you should ask questions; His word is not proof of success.
4. “What does sleep mode do?”, “Don't go to sleep” and a sleep sentence with quotes
   One should not sleep in the desire to explain. Report if he/she chooses the wrong tool; No regex patch is added.
5. Interrupt the sleep response with Stop: do not execute the pending transition. Sleep/Wake
   button and Mic On/Off work as before.

If the host just says "I'm passing" without a tool call, he won't sleep; model's tool
Not choosing it is a separate admission error. Share status line and tool registration.

## Previous quiz — 5.R3 natural response then sleep

Reopen the application; Temporarily set sleep duration to 0.

New variant control: “Go to permanent sleep” → response then sleep;
wake up and give short task → sleep again. Then it says “Disable persistent
"sleep mode" → close the option after the response. Reopen it with “Stay asleep”;
Turn it off with “Recover from permanent sleep mode”. Answer language for English audio test
Select English; The language setting is the response language, it does not change the tool permissions.

1. Say “Go to sleep”. Let Vex complete his short answer with his own voice; but
   then let it be SLEEPING. There should be no separate mechanical sound or second constant message.
2. Wake it up, say “Stay in sleep mode from now on”. Let him sleep after the answer is finished;
   When you wake it up and give it a task, the task/answer will automatically go back to sleep.
3. “Turn off permanent sleep mode” de/yaz: let its own response end, stay awake.
4. Interrupt the sleep response with Stop: do not execute the pending sleep command. sleep
   Let the button sleep directly; Mic Off should not mute the response sound.

5.R2 was reported successful by the user; The following are historical tests.

## Previous quiz — 5.R2 audio turn limit

Close the application completely and reopen it from `v1`:
`./.venv/Scripts/python.exe -m app.main --debug`.
First, set the sleep timer to 0 temporarily; on the same Live model:

1. Send “Hello” in text: receive a response as a check.
2. “Hello, how are you?” with Mic On say, then remain silent. three in a row
   Check out the answer, transcript and replay in the audio round.
3. Sleep → Wake up with “Vex, hello”; then ask a new question.
4. Interrupt a response with Stop and speak again. Mic Off should only cover the input.

If it hangs again, share the full status line: PCM sent, events,
before/after input final, **input end: sent/missing**, **speech chars**.
5.R2 is not considered closed or a new feature queue is opened until this test is passed.
Automatic 921 pytest/7 JS/10 native is not a substitute for genuine microphone/API acceptance.

## Previous quiz — 5.R1 unified stability

Reopen the application; Set normal Idle sleep timer to 0. First select the TR language.

1. “Go into sleep mode” de/yaz. “Go into sleep mode” after actual SLEEPING
   It must be both written and heard. The sound of this short confirmation is different from Gemini.
2. Wake up by saying “Vex”, ask a short question; Try three loops. Then a long
   interrupt response; When the response is finished, the normal voice should be received as a new request.
3. “Go into sleep mode permanently”, then wake up and ask short question and text
   “Turn off persistent sleep mode”. The first opening/closing sounds should be heard; every
   In automatic sleep back, confirmation is not required again. Mic Off should not interrupt the response.
4. Same check with mute on: text/status is correct, the sound should be off. wake up
   Available while the stop confirmation sound is playing; The old sound should not start back later.
5. If it gets stuck, check the reason and status of **first Microphone capture** in the Engine log.
   Share your line. Stopped is not the sole cause. “Input discarded…”
   Afterwards, the new listener is prepared; Repeat the lost desire yourself.

There is no physical microphone, actual provider and acceptance of room/echo sound; 920 pytests,
7 JS, native and synthetic real KWS migrations do not replace these. Fixed 700ms
Silence can make the contemplative pause the new turn boundary. new in awakening
Live connection is still established; Total delay is not guaranteed. If the problem persists
The same path will be examined through these measurements without adding the F4/new feature.

## Current quiz — 5.F3

First set the normal Idle sleep timer to 0; Do not accidentally put the timer to sleep for subsequent tests.

1. While awake, type “Enter sleep mode”; It should be SLEEPING. Wake up with Wake
   Try the same word out loud; Vex address shouldn't be mandatory.
2. Say “Go into sleep mode permanently.” Wake him up and ask a quick question;
   When the real response and sound are finished, he should go back to sleep. “Turn off permanent sleep mode”
   type and check that you stay awake after the new short question.
3. “Do not enter sleep mode”, “What does enter sleep mode mean?” and in quotes
   Write `"sleep mode gir"`. None of them should put you to sleep. English equivalents:
   “Please switch to sleep mode”, “Return to sleep after every task”,
   “Stop returning to sleep”.

If no sound is heard, try the same expression in writing: distinguish intention from input liveliness.
separates F2 physical awakening/25 s declaration and F4 local pronunciation are still on;
This step does not seem to have fixed these. No commits without new tests.

## Current quiz — 5.F2

1. Close and reopen the application; Set idle sleep timer to 0. With sleep button
   Put him to sleep, wake him up by saying “Vex” and ask a short question. Try this three times.
2. If it doesn't wake up and receive commands, record the status line first. Microphone Off/On
   and ask the same short question as a new request; Let me know if it's recovered or not.
3. If the 25 s wait is repeated, the `PCM sent`, `events`,
   Share information `before_input_final` / `after_input_final`. key or
   sharing personal note/sound. If the engine cannot recover, “audio engine did not resume”
   must be clearly visible; The on light remains on because it is user preference.

The question of physical awakening is kept open. 853 pytest and synthetic/native tests
It is not a substitute for actual microphone/provider acceptance. “Go into sleep mode” and
Rex/X variants are still F3/F4; this test uses the Sleep button.

## Current quiz — 5.F1

Reopen the application; In the test, first set the Idle sleep timer to 0.

1. Press the Sleep button: first short Preparing sleep, after acceptance SLEEPING
   and it should be Wake. Mic Off during sleep and press Wake: Mic Off must be protected.
2. Do Sleep again with On. Just say “Vex”, then pause briefly and
   Say, “Give me a quick hello.” The original request must be received. The word wake alone
   In persistent mode, a task should not be put back to sleep immediately as if it is finished.
3. Turn on persistent mode with the currently recognized “Vex stay in sleep mode from now on”;
   Wake up and give short request. When the real answer and sound are finished, he should immediately go to sleep.
   In normal mode, the 3 s timer should only put you to sleep once in idle.

This round of “go to sleep” list or perception of Rex/X has not been expanded. Especially
test with these expressions and conclude that 5.F1 corrects them; 5.F3/5.F4
open. If no sound is repeated for 25 s in Thinking or Idle, check the status line.
notify; It is the scope of 5.F2. Real account/microphone acceptance with this short test
is expected; automatic/synthetic evidence is not a substitute for physical achievement.

## Current status — close gaps before requesting new admissions

Examples of user “go to sleep” and “go to sleep permanently”
It is rejected in the host parser. Double space inside can also break the match.
These are not user errors. For five concrete runtimes open
[control](STAGE5_SLEEP_AUDIT.md) and [current sequence](../stages.md) are kept.
In this round, the user is not asked to repeat previous tests; after correction
A brief physical admission targeting relevant vulnerabilities will be given. old successful
native/pytest results do not consider these bugs resolved.

## Current test — correction plan step 1 / two independent sleeps

1. First, set Settings → Audio → Idle sleep timer to 0. “Vex from now on
   "stay in sleep mode"; wake it up and ask a short question. As soon as Reply/voice is finished
   It should be SLEEPING again. Should not wait 10 seconds. Don't talk while responding
   should not start a second task/interrupt; Wake up again for new task.
2. Wake it up and say “Vex wake up permanently.” Normal when time is 0
   must remain alert in conversation. Then set the Idle sleep timer to 3: three seconds in idle
   Then he should sleep for once. You should be able to wake it up with Vex and ask normal questions;
   permanent mode should not go into spontaneous mode.
3. Request long response in normal mode: should not sleep just because three seconds have passed while the sound is ongoing.
   Turning the microphone Off should not change the preference; Wake button available.

25 s Not perceiving in Thinking and Idle will still be examined in the second step. Rex/X wake
and unlisted sleep intent has not been added yet. In these tests, you can find the current recognized expression.
use Telegram operation is not yet integrated; privacy scenario available
Try it with a short answer or temporary test note task. True microphone acceptance
synthetic/native is not a replacement for the test. In the old tests below, the timer's Stay
The explanation related to asleep has been changed by this current step.

## Current quiz — persistent sleep / duration / effect sound

You reported the previous wake/login tests as successful (`701f33f`). New slice:

1. Type 3 in the Settings → Audio → Automatic return-to-sleep delay field and save.
   Press Microphone Off/On with Sound effects on: clicking sound on camera
   should come once per press; On/Off behavior should not change.
2. Say “Vex stay in sleep mode from now on.” Wake him up and ask him a quick question.
   Approximately three seconds after the response and audio ends, SLEEPING should occur again.
   Try this twice. One should not fall asleep just because three seconds have passed while a long answer is in progress.
3. Wake it up and say “Vex wake up permanently.” After next reply
   Wait longer than three seconds: it shouldn't go back to sleep. Normal one-shot “Vex goes to sleep
   branch” should also work; persistent mode should be turned off initially in the new chat.
4. Close/open the app: time should remain 3, persistent mode should not be turned on again.
   If the Mic is Off while sleeping, the word wake is not listened to; Wake button available.

Synthetic/native tests effects from real microphone, provider and speaker
 It does not replace the sensation. The following titles are records of previous tranches.

## Current retest — wake response / contradictory sleep / On–Off

Reopen the app, use Live and Microphone On.

1. Sleep → wait five seconds → just say “Vex”. Answer after a short wait
   or a greeting request should come; It should not remain in Thinking. Repeat three times. In a round
   Say “Vex, hello”; Then ask a normal question.
2. Say “Vex fall asleep” out loud. should switch to SLEEPING; requesting host privileges
   should not give contradictory answers. “What do you mean, fall asleep?” The question should not keep you awake.
3. Turn the Microphone Off while the model is talking: the response should continue, your new voice should not be lost.
   By ten you should be able to talk. Sleep/wake/Stop during button alone
   Microphone On or Off should appear, and its light should follow this preference only.

If an issue occurs again, share the response, transcript, and status line you heard.
Native/synthetic test passed; It is not a substitute for actual microphone and account acceptance.
The Retry/Blocked button expectations at the bottom are historical records of the old version.

## Current short test — local recovery / R1–R3

R0 reported successful by user (`616125d`). Testing my new language
 Re-open the application for; Use Live and Microphone On.

1. Press Sleep, wait five seconds, say “Vex, hello.” Restart after response
   Sleep and try three rounds. The vocal “Vex, fall asleep” should also switch to SLEEPING;
   If the transcript is Veks, the same exact statement should be accepted.
2. Turn Mic Off while sleeping: the light should go off and saying Vex should not wake you up. When you make ten
   local wake should be prepared again. You should be able to return to normal conversation with Wake.
3. If there is an error, share the code in the status line and log. temporary local
   On error queue/tampon · Retrying occurs after a maximum of two attempts
   On · Blocked appears on the obstacle. It shouldn't stay on "Preparing" forever.
   In case of Device/permission error, fix the device and try again with Off/On or on Sleep.

Delayed packet/queue overflow was created and verified in automated native testing;
In manual testing you don't need to create this by force. R4–R5 entry/silence errors
It has not been fixed in this language yet. The following old test titles are historical record.

## R0 time calculation — manual acceptance of this step

Reopen the application. Live/Microphone Press On and Sleep button; five seconds
wait quietly, say "Vex, hello." Response and normal listening should return. this
repeat three times; Wait 65 seconds on one try. "Local wake microphone failed"
If so, save the status line and engine log. Doing this test with the sleep button,
It stands the test of time issue of Veks transcription which has not yet been fixed.
Pressing Wake while Mic is Off should not change the microphone preference to On. R2–R5 yet
error recovery/login boundaries are not complete.

## Readmission of sleep correction

Reopen the application. "Vex fall asleep" with Live and Microphone On or
Say "Vex go to sleep mode"; SLEEPING should appear. "Vex, hello" while asleep
say; wait for response. If not, press Wake: normal listening should return. Mic Off
Pressing Wake while on the phone should not turn the microphone On automatically.
Settings → Change the SLEEPING color in Theme and save; color while sleeping
see and check that it is protected on reboot. The word Wake remains in the profile.
If voice wake-up still doesn't work, check the Asleep status line and engine log error.
notify; English dictionary based native engine expects physical pronunciation acceptance.

## Current quiz — one-time sleep / wake-word

Previous Stop indicator tests were reported successful by the user
(515a531). The new sleep zone awaits manual acceptance. Reopen the application,
Install the Live model and use Microphone On.

1. Say "Vex go to sleep" or press Sleep. Asleep/LOCAL WAKE should appear.
   Speak without saying Vex; reply/model turn should not start.
2. Say "Vex, give me a quick hello." The request in the same sentence must be answered.
   Then ask another question without saying Vex: normal conversation should continue; this
   It is a one-time sleep, it should not fall asleep again on its own.
3. Press Sleep again. Vex should not wake up when the microphone is off. Make it ten
   try again. You should also be able to exit with the Wake button; The written message clearly evokes.
4. Personalization → Wake word: Save to computer. Next Sleeping Computer
   must be shown and awakened with this word. Then go back to Vex if you want.
5. "What does go to sleep mean?" The question should not directly put you to sleep. Previous notes and
   temporary chat context must be preserved during sleep/waking. Sleep/Wake in Unknown lock
   It should not be used to start new tasks or remove locks.

The native model was installed on this machine. From v1 in incomplete installation:
`.\.venv\Scripts\python.exe -m app.session.wake_word --setup`
Sleep remains on unsupported error word/model; Vex dating Wake
correct your selection. True microphone success has yet to be measured. 60 s stream limit
If he misses it, say the word again. Automatic sleep back and seconds setting is the next step.

## Current short test — Stop indicators

Temporary memory tests were reported successful by the user (`dc79318`).
This new minor representation fix awaits manual acceptance.

1. Request long response with Live + Microphone On; Press stop. Header microphone light
   It should not go out and burn for a short time; At the normal end the listening should be ready again.
2. Interrupt while the model is speaking: the previous response can be interrupted, but normal interruption
   The link badge should not be a red error. Neutral LIVE READY after stop is normal;
   The normal last Live response information will still appear on the next verified response.
3. Turn Microphone Off: the light should go off. Disconnect/real permission or device error
   should also turn off the light; this fix should not turn real errors green.

Wake-word/sleep was not added this round; is the next separate application step.

## Current manual test — temporary chat memory

Reopen the application. After the Live model is loaded:

1. "My favorite color for this chat is purple" de/yaz; then "What color did I say?"
   ask. It should follow the same conversation; should not claim permanent profile registration.
2. Request a long response and press Stop. When the controls open, ask for the color again.
   If a new socket is opened, the recent conversation restored diagnosis can be seen;
   previous color should be remembered, old command/not operation should not work again.
3. After Disconnect, send a Live message again and ask for the same information.
   The recent past must be preserved. Very old/long speech limit can be stuck.
4. Press New Chat and reject the confirmation: messages/context should remain. Press again to confirm:
   speech must be cleared; notes and settings should remain. Old conversation when you ask the color
   knowledge should not come from the memory of this new conversation.
5. When you close and open the application, this temporary memory should not remain. New Chat is on active turn
   or should not be used in unknown result lock; It is not a recovery button.

Automation: 787 pytest, 6 Node suites, 10/10 WebView2 phases and Pyright 0 bugs.
This slice expects manual acceptance; developer with real account or paid API
It was not accepted. Persistent user memory, wake-word and sleep are the next tasks.

## Current: Microphone Off not cutting REST audio and response

Previous microphone preference tests accepted by user (`f35a13e`).
The user reported successful manual testing of this slice on October 22, 2026.
The following list is for double checking:

1. Request a long response while Live is on. Microphone while talking or playing back
   Turn off: only the microphone should be turned off; The model should continue speaking/writing.
   If you also press stop, the response should stop. Off preference should not be turned on automatically.
2. Close the Live box, turn off Mute. Send a short Turkish question via text:
   sound should come after the text appears; The status should be playback finished.
3. Turn on Mute in REST and send a message: text should come, but no sound should come. Unmute.
   Press stop while preparing/playing sound of long response; text and completed
   note operations must be protected. If there is pending HTTP, a new message should not be opened before it is finished.
4. If TTS quota/access error occurs, text should remain on the screen, audio unavailable
   should appear. It should not automatically resubmit transaction message/note. this error
   It doesn't mean that the text model has failed.

REST TTS uses separate API request/quota; Korean default is fixed. live sound
selection does not change the REST audio yet. REST microphone/STT not added.
Automation: 780 pytest, 6 Node suites, 10/10 native phase and Pyright 0 bugs.
The real account and physical device were not used in this development; in synthetic testing
Quiet PCM playback is not evidence that it is being heard from the real speaker.

## Previous: Microphone On/Off and listening after error

User acceptance: On/Off and post-error listening on October 22, 2026
The tests were reported successful. If Off does not interrupt the response on active input, the next
Requested as a minor correction.

1. Install the Live model, keep Microphone On. Deleting a temporary note that doesn't exist
   love Rejection/clarification then ask a new question without pressing the button; The answer must come.
2. Cut a long response with Stop. On after the real end and idle in silence
   should stay. Ask a new question; The old command should not be repeated automatically.
3. While answering, turn Microphone Off, then press Stop. microphone off
   should remain; It should not be opened after the next text message or after the model is loaded.
   Obviously when you turn it to Ten it should get your new speech.
4. If there is Permission/device problem or Disconnect, fix the setting/connection and turn Off→On
   use As a result of the indefinite tool, this button should not unlock the command; application
   You need to reopen it and check the record. Ten choices are not the authority to overcome the obstacle.

Passed 765 pytests, 6 Node suites and 10/10 WebView2 phases.
This interim request was implemented alone; REST audio output is the next separate step.
Tests use transient profile and synthetic voice/provider; physical acceptance is expected.

## Previous: step 5 — status and Stop/log quiz

User acceptance: status/log/duration and idle/listening on October 22, 2026
The tests were reported successful by the user; step 5 manual acceptance is completed.

1. Load the live model, pause for a few seconds: even if the microphone is ready, the center idle
   should stay. Listening when speaking in a normal voice; When you keep silent and wait for an answer, thinking,
   Speaking while Vex's voice is playing, idle should appear again at the end. local perception
   includes approximately 200 ms of start/700 ms of silence; It is not a word-based measurement.
2. Speak again or interrupt the response. The old voice/text should not interfere with the new round;
   A new conversation should not be conducted without waiting for the real tool result.
3. Use Stop during response. Controls should be unlocked after the actual finish;
   There should be a normal stop record in the engine log, as well as Failed to send for the same Stop.
   It shouldn't say live_audio_start. Real API/device or ambiguous result errors should not be concealed.
4. Also try text response and Stop in REST. The previously completed provisional note must be preserved.
   In long use, the log panel keeps the last 200 records; old diagnostic records are lost.

765 Python tests, 6 Node suites, and 10/10 WebView2 with synthetic providers passed the phase.
25 s event wait / 120 s total Live limits were reduced in controlled tests
tested; There were no such long waits or paid calls in the real API.
There is no auto-repeat on timeout; unknown keeps the controls locked.
Manual acceptance is expected. REST audio output is the next separate step.

## Previous: step 4 — language and basic customization

User acceptance: Step language/personalization on October 22, 2026
The tests were reported successful by the user; step 4 manual acceptance is completed.

1. In Personalization, select Response language = Turkish; to personal instruction
   "Call me Captain; give short answers." Type it and press Save profile.
   Say "Hi, introduce yourself" in text and voice in Live. Turkish and your preferred
   Call and wait for a response. Try the same written test in REST with Live closed.
2. Response language = English and instruction = "Call me Captain. Use one sentence."
   save. Subsequent REST and Live responses must be in English. a pre-clear
   If there is a Live context, the next message is expected to be session scope_changed/new;
   A request should not be sent again to the old response or old tool action.
3. Close and reopen the application; language and instructions must be preserved and implemented in the new message.
   Then switch back to your preferred Turkish setting. If the save fails, the modal should not close;
   The model uses saved disk preferences.
4. If you save a profile while the live response is ongoing, that response will be updated with its own old instructions.
   may end; the new preference is applied in the next message. Stop/Disconnect and
   The previous note-maintaining behavior should persist.

Passed 762 pytest, 5 Node suites and 10/10 WebView2 phases; Correct instruction to SDK
migration verified with synthetic provider. You will accept dil/style with the real account.
Native voice recognition language remains automatic; The selected language is guided by the prompt.
Transfer of other profile fields to the model and REST audio output are not included in this step.
Manual acceptance of the new step is still awaited.

## Previous: step 3 — Short manual test for VAD and microphone turnover

User acceptance: Testing of step VAD/microphone on October 22, 2026
It was reported by the user to be successful; step 3 manual acceptance is completed.

1. Load Live model with headset first. Ask for a long explanation; keyboard/fare
   Short clicks such as should not interrupt the response. "I give up, just say hello" in normal voice
   interject. The old voice must be cut, the text must be preserved, the new word must appear separately.
2. Start speaking as soon as you finish answering; second without pressing the microphone button
   The response should come and the first syllables should not be lost. Try this a few times.
3. Do the same test with the speaker sound you normally use. Vex in his own voice
   headphone/speaker if you are cutting yourself off or are not able to speak normally.
   report The energy gate is not a definitive echo/speech discriminator.
4. Try Stop/Pause/Disconnect while capturing new conversation. The word waiting is later
   should not be sent; A new conversation should be able to be opened with Resume. A completed temporary
   the grade must remain unchanged; The unknown tool should not open a new command as a result.

742 pytest, 5 Node suites and 10/10 synthetic WebView2 phase passed.
The actual account/hardware was not used during this development. Active Stop context
can reset; This step is not full duplex interruption on the same socket.
Language and personalization is the next separate step. Manual acceptance is still awaited.

## Previous: step 2 — instant transcript display

User acceptance: User instant transcript on October 22, 2026
reported that his tests were successful; step 2 manual acceptance is completed.

1. Re-open the application and load the Live model. When the provider speaks
   the words it recognizes should appear in the single user bubble; It should not be added repeatedly.
2. Ask for a long explanation. The text should grow in the same response bubble as the Vex speaks;
   The same answer should not be added a second time after the round is over.
3. Interrupt or press Stop while Vex is talking. Old text visible so far
   should remain and say Interrupted; new promise different bubble user/model
   must go. The text of the old answer should not appear in the new round.
4. User text must appear once in the written Live message. Disconnect or
   When changing models, the late text should not reopen the old message.

The text appears when the provider transcript arrives; complete with sound at word level
Recognition of synchronous or not-yet-sent local audio is not promised. Barge-in,
Other fixes for language and perception issues are separate steps. real account
this was not used in development control; Synthetic acceptance is not a substitute for physical testing.

## Current: Interrupt when Vex is talking

Automatic listening confirmed in previous user testing. Try the new step with headphones:

1. Load the live model, say "Tell me a long story". Vex talking
   “I give up, just say hello,” you interject. The sound should stop, then a new
   The text of the speech and its short response should come. You shouldn't have to press the button.
2. Add a temporary note and then ask for a long response; stop talking. Previously
   the completed note should not be deleted or added a second time; Check it from the panel.
3. Use Stop/Pause/Disconnect when detecting new words. The word waiting is later
   It should not be sent by itself. With Resume, the new conversation should be able to start separately.
4. Try several times in a row; The old audio should not play again. UI if result is unclear
   should remain locked instead of sending new commands. If the closing of the old turn is prolonged, the sound
   The buffer is disposable; In this case, talk to Resume again.

Active Stop can reset the logical session; don't assume context preserved. This acceptance
It is not a full-duplex provider protocol test on the same socket. real
echo and noise sensitivity not yet calibrated; synthetic WebView2 test
It is not a substitute for physical speaker/microphone acceptance.

## Current: buttonless talk and automatic replay

1. Reopen the application; Load the catalog with Load Live Models while Live is open.
   Gerekirse ilk microphone permission ver. Mic'e without pressing Listening for speech
   should appear. While silent, the request for model response/success or periodic model should not occur.
2. Say "Hi, answer briefly." Automatically after the sound of the answer ends
   Listening for speech should come. Ask the second question without touching the button.
3. Text messages can also be sent on local standby; Must listen again after answering.
4. Press Pause listening or Stop: it should not turn on again by itself. Resume
   Continue with listening. Disconnecting and removing the microphone should also stop.
5. During the response, speech is not received in this slice; This is not a barge-in test.
   Notify if initial clipping: local candidate threshold actual
   not yet calibrated in hardware. The presenter finds the end of the conversation with VAD again.

Controlled testing uses real WebView2 but synthetic voice/provider. real
account/physical microphone/permission persistence is open to user acceptance.

## Current language: talking PCM send and automatic VAD

The automatic device list was reported successful by the user. New VAD
The actual acceptance of the slice account/microphone has not been made yet. Quick quiz:

1. Open the regular application; Live is on and the model is selected from the catalogue. with headphones
   Press Mic, when you see the Listening live text, say "Hello, give a short answer".
   Shut up before pressing the end button; text and voice response should come, microphone should turn off.
2. With only the provisional test note, say "Add VAD trial 001 to my notes". One note,
   A refreshed panel and verified result is expected from the backend; Wipe clean by hand.
3. Press Stop while talking; mic must be turned off, inputs after actual end
   should be opened. The new speech should not be affected by the old packet/Stop. The finished transaction cannot be undone.
4. Denying mic permission or removing device should not switch to another microphone silently.
   Entry exceeding 15 seconds will be cancelled; It is not shown as success.

This is one conversation stream. Spoken interruption and automatic interruption during response
Re-listening is the next step. Controls were made with the temporary profile/synthetic voice;
provider VAD quality and reopening persistence of actual permissions are untested.

This document is for the entire project; It does not say that all features are ready today.

22 October current acceptance: user passes open start/end microphone tests
reported. Basic microphone/transcript/Live audio acceptance is ok; constant listening
and spoken interruption has not been added yet.

On the same day, an empty native window was reported after the device slice. Native UI file
After fixing the cache, the user confirmed that the reboot worked.
Failed to retrieve legacy console error; This approval is not multi-device or permanent VAD acceptance.

The user reported successful device tests. In the last minor device improvement
Scan button removed; listing is an automatic and unauthorized reading. first leave
It's on the Mic button. Continuous listening/VAD is not part of this change.

Brief check of the automatic device list:

1. Open the application, go to Settings → Audio & Camera: the list should appear without the button.
   The microphone or camera should not be turned on just for listing purposes. If there is no first permit yet
   It is given by pressing the Mic button; Afterwards, accessible device names are refreshed.
2. Select your microphone and Live reply speaker device, press Save Settings.
   Next start/end record microphone of your choice, Live response output of your choice
   should use. Effect sounds are still in OS default.
3. If the private device is inaccessible, it should error out instead of ringing silently on the wrong device;
   Try again by selecting System Default. Selected USB microphone while recording
   If you remove it, the record should close before being sent. Don't give the important command for this essay.
4. Your choice should be preserved when you reopen; device due to browser origin/permission
   If the ID has changed, a new selection from the automatically renewed list may be required. Lost preference is on the list
   clearly visible; It cannot be automatically replaced with another device.

Testing with a single device does not count as acceptance of multiple hardware or all drivers.
Code verification, limit cases, simulated network errors, recording/replay and regression
tests are done by developer/agent. After each correction from the user
is not asked to run the same tests again. The following essays feature relevant
Once ready, it is held in a short reception session.

| When? | What does the user try? | Why do you need real users? |
|---|---|---|
| Stage 4 | Close Notepad and accept real open/replay twice | Real Windows session and secure closing of open documents; completed, two reports checked |
| Stage 5 / with text UI ready | Short speech, a synthetic note adding/listing, stopping a task; clarity of appearance and response | Natural language expectation and usage experience; The agent also tests the accuracy of API/tool ​​|
| Stage 5 / with sound ready | Talking to your microphone/speaker or headset; mute/mic on-off, interruption, delay and intelligibility | Heard sound, ambient noise and device behavior cannot be verified by mock testing alone.
| Stage 6 / account integration ready | Completing the login/permission steps of the account he chooses himself, such as Google/Telegram/Discord; try first action on clearly defined test target | Account login and real authority belong to the user; prepares agent permit coverage and automated checks |
| Step 7 / With the GUI process ready | In the application it will use, the only real workflow with the synthetic document in its screen/DPI layout | Actual application pattern, focus and target accuracy; The agent also controls the different layouts that can be accessed |
| Stage 8 / with routine and pack ready | Creating a trial routine, launching the application close/open and the bundled version normally | Daily usage and experience of the distributed application on the target machine |

If there is no more than one monitor or specific device, that condition is not tested.
is recorded; It is not expected to acquire equipment that it does not have. Quota from user
filling in, deleting real data, or configuring accounts just to create errors.
It is not wanted to break it. Network/quota errors are first generated by controlled automation.

## Job pending from user today

Phase 4 acceptance is complete. Controlled tests of the Gemini 5.2 adapter are ready;
3.8 Flash request returned 503; Live catalog and synthetic note acceptance passed with 3.5 Flash-Lite. The combined live acceptance of the new retry/fallback and UI text line has not been made yet; 10 real WebView2 scenarios passed with controlled HTTP. Manual commands using separate blank profiles are at the end of STAGE5_MODEL.md. Local UI key registration
Connected to Windows identity store. In the user application, go to Settings → Connection
can save the key from the field; the next required live admission can be made with this key; There is no need to rerun the past two tests just for repetition.
In this attempt, the old GEMINI_API_KEY environment value comes before the registered key.
The environment variable should be removed. Commands [Related guide](STAGE5_MODEL.md) in the Stage 5 guide.
This is not a code audit task. The key is not sent to the chat message.
Actual API key/account data and microphone were not used in development testing.

When a feature is completed, the agent first performs its own checks, then alone
required actual use trial; command, expected result and test data
clearly states its scope. In addition to the user's pass notification, if any
The report file is examined; An untested point is not marked as completed.

Updated UI fix: normal chat is open while waiting for the first note transfer; Annotation tools are closed until approval. Settings → Connection → Load brings up the Live models API list and shows only those that declare Live capability. This selection does not start the audio connection today; Live voice response to text message is in the next segment. Native opening commands are at the end of STAGE5_MODEL.md.

Current Live control (October 22): first text in user persistent session 0.7 s,
observed a total of 3.4 s; This guarantees that every request will finish in the same amount of time.
It is not. Reopen app in new tool slice, with Load Live models
make a selection, leave the Live session box open. Use backend if transfer is pending
Confirm with notes. Send “Add Live trial 001 to my notes” / “List my notes”;
Wait for single record and correct list. “List supported applications” and “System
"show information" tries the other two tools. Note deletion/editing has not yet been
is not clear; UI buttons work. Check succeeded/verified in the tool log.

In normal two rounds, the session is reused, and a new session is expected after Disconnect.
New login once when grade transfer confirmation changes the tool list
It is normal. The note may actually have been added after the error; without checking
repeating the same insertion command. Tool connection works by user
he confirmed; Current total 560 self-tests passed with the next Stop segment;
Live tool trial with your real account has been approved by the user. Audio playback and REST Stop next
are steps. The full native package of this slice is ready after the closing wait test is corrected.
then 10/10 passed; failed runs and the result are recorded in STAGE5_MODEL.md.

Live Stop acceptance: reopen the application, select the Live model. “Space me”
"Write a 20-item statement about" and hit Stop Task while waiting for a response.
bass. First Cancellation requested and then Stopped should be seen; login again
should be opened. Then send “Hello”; new session and wait for normal response.
Existing grades should be preserved. Normal response appears if pattern ends before Stop
it is true; A completed turn is not deemed to be subsequently cancelled. Write another data
If you try it with the command, note that Stop does not undo previously saved data.
This step passed 10/10 on real hidden WebView2 + synthetic mesh; with your own API account
Live Stop has been confirmed as working by the user. Resumption note with model editing/deleting and
audio are the next slices.

## Current REST Stop acceptance — October 22, 2026

REST Stop is ready; The next stage was not progressed. Re-open the application and click Live
Close the session box. Ask for a long explanation and hit Stop Task while you wait.
Continuation eden HTTP if present “Waiting for the current HTTP request to finish” is expected;
Meanwhile, the login and notes remain locked. “Stopped” and opened when the request returns
wait for checks. Then send “Hello”; wait for normal response. From Model Stop
It is correct for the normal response to appear if it has been completed first. General instead of annotating
It is enough to try it with chat; Stop does not undo a previously completed text.

578 pytest checks and full native package passed 10/10; real account/data or
Paid request was not used. FakeWindow test objects with tracking correction
7 type errors were also fixed; bridge suite 72/72 gave combined Pyright 0 errors/warnings.
STAGE5_MODEL.md holds the past finding and solution. This new REST Stop slice
user acceptance with real account **could not be tested — API limit**: user API
reported that the limit was reached. When the limit is opened, short manual acceptance can be made;
this record is not a failure in automated tests.

## Current Live connection acceptance — October 22, 2026

The resumption period was completed with GoAway and secure idle checkpoint. 601 pytest
check, selected production/resume/bridge type check and full native package 10/10
passed. Native report: stage5-live-resumption-native.json. Real UI/SDK/core,
synthetic transport was used; real account acceptance **could not be tested — API limit**.

When the limit is opened, reopen the application, select the Live model as load and two short
send message: new session → session reused wait. Natural after GoAway/disconnect
If there is a secure checkpoint, session is resumed, otherwise new session and context reset
The reason is expected. Resumption was accepted with just two messages without seeing GoAway
does not count; Synthetic native testing has also tested this limit. Stop or Disconnect
The new message after should be new session. In an error, the note has already been saved
may; resending the same insertion command without checking.
Active broken messages are not automatically resent; just keep going
It is done from checkpoint. Note from sound and model editing/deletion was not added in this slice.


## Note from model editing/deletion acceptance — October 22, 2026

Checked validation: 639 pytest, 38 tests in new annotation target file, selected
Pyright 0 errors/warnings and hidden WebView2 10/10. Native report:
[stage5-model-notes-native.json](stage5-model-notes-native.json). real
account acceptance **could not be tested — API limit**; Send paid request now.
There are no errors blocking local progress in the previous connection step; its real
Account acceptance also remains open.

When the limit is opened, `.\.venv\Scripts\python.exe -m app.main` in the `v1` directory
Open with . If the first transfer is pending, confirm with Use backend notes. Don't try alone
Try this short flow for REST and Live, with notes:

1. “Add Vex temporary CRUD 001 to my notes” and “List my notes with IDs”.
2. “Change note Vex temporary CRUD 001 to Vex temporary CRUD 002”.
   Wait for new text in the panel and the same record ID in the list.
3. “Mark Vex temporary CRUD 002 note as completed”; Wait for the sign on the panel.
4. “Delete Vex temporary CRUD 002 note”; It should disappear from the panel and the new list.
5. Add two test notes with the same text; Request deletion via text. Which registration is the model?
   or the host should ask for clarification with note_target_required;
   Both records must be preserved. Have them listed with their IDs and delete them with the real ID you chose.

Indirect choices such as “delete note Onu/ilk” do not resolve in this narrow safe slice;
restate the exact current text or ID. Each new mutation is newly verified
asks for a list; the model must call this itself. panel/list before after error
check: the article is complete but the model response may be broken. Stop completed
does not undo the transaction. Resending on Unknown lock, reopening the app and
Check out the real records. Audio, microphone and UI cleaning were not added in this mission.


## User acceptance update — October 22, 2026

Adding users for REST and Live → listing with their IDs → changing text →
completed marking → reported that the entire deletion flow had passed. same
Asking for an explanation in two text notes and deleting only the selected one with the open ID was also passed.
Stop on long reply, then new message, opening controls and done
The protection of the memo operation was also reported as passed. This is the previous note above
Turns off the "Could not be tested due to API limit" acceptance for CRUD. real
Testing of GoAway/resumption was not reported; that acceptance remains open.

Two requested improvements were noted. Only time metadata is included in this prompt.
added; target solving is the next separate step. In the new note created_at backend
is UTC time; The ID and date do not change during edit/done. Your old undated note
Its time remains unknown, it is not shown as having been created today.

Short new check: just add a new test note and get the record ID from the model
and ask it to list it with creation time. Change text or done sign,
relist and reopen app: ID/date should remain the same. Take a backup
When explicitly restoring the date should be preserved. This new timestamp change
user acceptance has not yet been made; You don't need to redo the previous CRUD commit.
“Delete last note” and “delete deceased note” are still available full text/ID
subject to the limit; will be addressed in the next target selection step.


## Endnote and partial text selection — short acceptance

October 22: 707 pytest and native passed 10/10. User with real model of new selection
acceptance awaited; The previous note CRUD and Stop assertions are preserved. Restart the app
Open it and try the following flow separately for REST and Live, with only test notes:

1. Add note 'Vex target hello 001'. “The note with 'target hell' in it
   “mark complete”, only this note should be marked, ID/date should be protected.
2. Add note 'Vex target control 002'. Say “Delete last note”; history of all notes
   If known, only the newest control 002 should be deleted. old undated note
   If there is, it is expected to ask for an ID. Automatic latest success path is empty/temporary
   You can try it on the profile; Don't delete your real old notes for this.
3. Add 'Vex target hello 003'. Say “Delete the note containing 'target meh'”;
   Since there are two candidates, they should ask for clarification and both should be protected.
4. List the IDs and delete them by specifying the real ID of one of them; only chosen
   The record should be deleted. Clear trial data again with ID.

Write the partial with solid or typographic quotes. unquote/negative/multiple
filters, unknown target and maximum date equality description in this slice
wants. “Last” is the recorded creation time, not the last edit. A model error
then resending the command without checking panel/list. Next
After this acceptance, the step is Live audio output; audio/microphone has not been added yet.


## Previous slice: Live audio acceptance and first slice of microphone — October 22, 2026

When the current UI is loaded, the user hears Live sound and the delay is very low.
He stated that he felt This is measured zero latency or all device/Stop/Mute
It is not an acceptance of their race. Initial physical audio output acceptance completed.

Re-open the app with the updated UI to test the microphone. If necessary
Use `python -m app.main --debug` and Ctrl+Shift+R; Select Live with load models.
Press the microphone button and allow; When the recording indicator comes on, “Tell me a short text in Turkish”.
"Say hello". Press Finish & Send within 15 seconds at the latest. The recording ends,
microphone is released; A transcript and audio response must be received. The answer is in this first slice
It starts after the registration is finished. Trying with headphones reduces the effect of external noise.

1. Add and list a temporary note by voice; that the transcript is correct and that the panel
   See if it's updated. Check the note before repeating the misdetected command.
2. Press Stop on the new recording: the microphone should be turned off, the recording should not be sent. then
   Written Live message should still work. If the recording exceeds 15 seconds, it will not be sent.
3. Try Stop and Mute during the pattern response; Existing sound rules should be preserved.
4. Microphone permission reject/close: error should appear, controls should open.
   The record should not be moved to the new scope when changing Disconnect/model/key.

Continuous listening, automatic VAD, speech interruption and device in settings
The implementation of the selection is not available in this period. REST is text only. real microphone
and speech recognition accuracy is open to user acceptance; synthetic native recording
It is not marked as actual microphone acceptance.

## Previous note target acceptance and Live volume control — October 22, 2026

The user confirmed the endnote and partial text selection as fully working;
This acceptance has been closed with previous approvals of CRUD/Stop. Next single slice
Live is the audio output; actual voice response acceptance is yet to be awaited.

Reopen the application. The API key of the current profile is in the Windows identity store
the key it was found in was verified without being shown; The record has not been changed. In settings
Key stored locally should be seen. It is normal for the box to be empty; in the same profile
You do not need to enter the key again. Select Live model with Load models, Live session
When it's open, type "Say a short hello to me in Turkish." Text and OS default speaker/
Wait for sound from your headphones. This user request is required to access API/model;
The fact that the key is registered is not proof of access/quota.

Then ask for a slightly longer response: Mute should lower the volume, Unmute should next stream
should open. Stop should cut off the sound in both the ongoing and the remaining sequence; in new message
The old sound should not play. If the pattern is already finished, Stop only cuts the sound; completed
does not undo the note operation. There should be no sound after disconnecting. Then apply
close/reopen and check that the key status remains registered.

The queue is limited to 20 seconds/512 pieces. Very fast/long sound overflow in production
warning is given, the result text/tool is preserved. Implementation of the selected dOut device,
Microphone, VAD and speech interruption are not yet available in this step. These are next
They are separate steps. Native test's silent PCM playback physical audibility
It is not acceptance; This concludes with a short user trial.
