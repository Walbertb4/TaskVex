# Sleep / latency / Stopped review

## Updated 5.R3 — separate confirmation sound removed

5.R2 tests were reported successful by the user. Then the user
Removed six WAV and confirmation playback codes upon request; Sleep on command is now Vex's
It is applied after its own response and ringing are finished. R1 native audio below
The narrative is historical. Current contract UI_BACKEND_CONTRACT.md, acceptance
USER_ACCEPTANCE.md and progress are in stages.md.

## Current 5.R2 note — replaces R1 protocol selection

After the user, the text works, the sound is 14 PCM / 2 events / before input
He reported that he was stuck for 25 seconds with the finale. Therefore the following R1 hybrid VAD/EOS
description is historical application: current audio protocol automatically with VAD off
activityStart → PCM → activityEnd. Local 700 ms silence is maintained.
The new limit diagnosis shows input end: sent/missing and speech chars.
Passed 921 pytest, 7 JS, Pyright 0 and 10/10 native; evidence
[native report](stage5-manual-activity-native.json). Real account/microphone
not tried; The reported fault has not been completely resolved or its exact cause has been proven.
Manual acceptance is at the beginning of [USER_ACCEPTANCE.md](USER_ACCEPTANCE.md).

October 23, 2026. User sleep confirmation not audible, awakening/detection
reported lag and sometimes no commands being received in Idle after Stopped.
This review is not a new feature phase; It is the 5.R1 stabilization taken before F4.
AGENTS, architecture/contract, engineering:debug, Gemini Live and Ponytail were watched.

## Proven causes and changes

| Finding | Evidence | Correction |
|---|---|---|
| S01: login is being closed, EOS may not be sent to the server | However, the synthetic socket that produced a response after EOS could not respond in the old code | When leaving the sender with the final transcript, the missing EOS is sent from the same Live owner; previous/previous no tool duplication |
| S02: learned noise during response interferes with normal sound | .02 level sound for 5 s, then .03 candidate in normal mode never triggered in old worklet | Response → at normal listening limit only the noise floor is reset; half candidate/pre-buffer is protected |
| S03: local sleep response skips audio line | local_sleep was not falling into either of the Live PCM and REST read_reply branches | After host acceptance, the selected TR/EN fixed text and local WAV are played from the same LiveAudio host |
| S04: expensive wake engine is installed every sleep | Local measurement: 1177 ms new engine, .21 ms readiness decoder/input | The only confirmed engine is in RAM; every sleep new stream/ID/queue/buffer. Engine is refreshed on error or wake word change |
| S05: Resource error delegated from wake is mistaken for local wake error | stream_backpressure in wake state was getting blocked in old wake handler | Normal microphone error/Stop way is used; maximum two new free listeners only in case of temporary error after the actual end |

S05 is compatible with the last state in the user: `Stopped. Completed actions were not
'undone' alone does not mean provider failure. UI disappears during setup
When it sees the source, it can send Stop itself. Old success/Stopped text micBlocked
He could cover up why. The login error is now logged; limited to definitive finish
The need for readjustment or open Off/On appears. Every event on the user
It is not remotely proven that this is the exact reason.

S01 is a gap left by the previous 5.F1 input-shutdown fix. old
The synthetic server EOS was responding without waiting; That's why the tests passed are real
It did not meet the protocol requirement. The new test ties the server response to the EOS condition.

## End of conversation: make the protocol clear

The speech ending of the local speaking candidate and the presenter is different. Previous road some
In these conditions, he is waiting for the finale from the presenter alone, and he will wait for the end of the audio for up to 15 seconds.
It wasn't reporting. Now after backend ready confirmation, worklet gets `arm-end`;
At 700 ms of local silence, EOS goes away after all pending PCM acknowledgments are finished.
A pause during wake preparation alone does not generate EOS. 15 s/150 packs
security limit, Stop and unknown are preserved. Lost audio is not automatically repeated.

This is Google's [hybrid VAD guide](https://ai.google.dev/gemini-api/docs/live-api/capabilities)
Compatible with: local end of conversation while auto VAD remains on `audio_stream_end`
It can be reported with . [Protocol reference](https://ai.google.dev/api/live) is
Defines the field as the end of the audio-stream to be used with automatic VAD.
700 ms is not a calibrated guarantee for all user/room conditions.

## Confirmation sound and correct success meaning

- once: “I went into sleep mode.”
- persistent: “I went into permanent sleep mode.”
- off: “I turned off permanent sleep mode.”

There are also English equivalents based on the choice of Personalization pLang. once and
persistent sounds are played only after host sleeping=true confirmation; off available
after successful closing of the chat preference. Ret/unknown does not produce success sound.
The same confirmation is not repeated when automatically sleeping back after each task.
Local wake preparation is not held while the sleep entry confirmation is playing; user
You don't have to wait for the confirmation sound to wake you up.

Six WAVs were produced with native Windows Tolga/Zira sounds. Model/TTS HTTP,
There are no new dependencies or user registrations. Gemini is the voice of these short affirmations.
It is different from the speaking voice. Mute, selected speaker, with the same LiveAudio owner
Stop, old fetch/decode result and connection change limits are preserved.
Error File/output does not roll back real mode; Audio error is logged clearly.

## REST doubt and remaining costs

Normal microphone path `live_audio_start → TextChat.run_live → PersistentLive`
It goes over. There is no REST model fallback or REST TTS in this path. Git's
The first available commit already contains two Live/REST; Before adding REST
Could not compare measurements with the fully working version. Therefore the whole problem
There is no evidence for binding to REST; The above reproductions are our audio
the lifecycle is in our code.

Sleep still turns off the Live socket. When you wake up again, you will have a new secure connection.
There is setup time; The wake_only turn may also require reconnection.
Text/stream/clip setup scope changes may refresh the connection. these are this
The turn was not hidden by removing security rules. Provider without real account
No numbers are promised for latency or overall end-to-end speed.

## Validation and explanations

- S01 and S02 tests were shown to fail before the change, but then passed.
- 920 pytest; 7JS suites; app/targeted Pyright 0 errors/warnings.
- Native 10/10: stage5-sleep-stability-native.json; last hybrid/cache slice
  Additional chat for: stage5-sleep-stability-final-chat.json.
- The first attempt of the additional chat is in the test trying to capture the Thinking moment over time
  failed: stage5-sleep-stability-chat-timing-failure.json. Fast EOS
  The actual status after the answer was Idle/reply OK. Test open server
  Fixed with barrier; Failed attempts are not deleted.
- True KWS, three restart/detection with single WAV produced: every cycle successful,
  new ID, .19–.21 ms restart; new engine 1036.93 ms (single local measurement).
  Report stage5-sleep-stability-real-kws.json. These are CPU/model preparation
  are measurements; it is not the actual microphone or total response latency.
- No real user notes, voices, keys or paid APIs used.
  Physical device/room/echo with different speech levels and actual provider
  Long-term admission is still open. F4 pronunciation/incorrect wake operation was not performed.

## Next acceptance sequence

1. Normal timer 0 to three at the same time, without adding new features Sleep/Wake/speech
   cycle; then persistent and off confirmations.
2. Short/pause command, long response, barge-in, Stop and new command; same
   Compare initial audio/EOS/final/answer times on size workload.
3. If the problem persists, new status line/log in PCM/EOS with **initial login error**
   take your measurement. Don't accept the last line of Stopped alone as a reason.
4. Then F4/F5 real local wake/negative sound and physical long use.
   Without this acceptance, the sleep layer cannot be called fully stable or Stage 5 closed.
