# Gemini connection review — October 21, 2026

Scope: user-selected gemini-live-api-dev skill and migration
Comparison of existing GeminiText, ModelTools and live acceptance script with reference.
Skill resources are in the user's .agents/skills/gemini-live-api-dev directory.
This is not a Live app development turn; The existing text adapter was examined.

## The correct ones

- SDK google-genai 2.32.0; The old google-generativeai is obsolete.
- The current path is turn Generate Content text/tool. gemini-3.8-flash text model
  This path is compatible with; gemini-3.8-live is a separate WebSocket/audio protocol.
  For Live, simply changing the model name is not enough. CLI help
  Added explicitly that the --model field is not for the Live model.
- SDK's automatic function calling feature is disabled; direct switch to handler
  no. The host's permission catalog, registry, policy and TaskManager are protected.
- Tool schematics are transferred without discarding rules; model Content and think signature
  It is added verbatim to the next request. FunctionResponse provider's information id/name
  It protects. Tools that come in a single response are executed sequentially in the current worker.
- The key is received only from the process/host input; general setting, log or backup
  don't hide HTTP retry is off; turn/tool limits available. partially completed
  job is stored on network error; pending/UNKNOWN does not translate into success.
- This sync client is being shut down explicitly. UI, microphone or Live receiver loop is not yet available
  There is no claim to block the Live receive loop here since it does not depend on it.

## Two issues recreated and fixed

### 1 — Tool call ID confusion on individual user turns

GeminiText.run defines a new user request with each call; but the provider
Its id depended only on the ModelTools session. If two independent runs use the same id
The second request could be mistaken for a replay of the old mission. The test requests two separate grades
While expecting two notes, he observed a lone note and failed before correcting it.

The call ID passed to Core is now the once-generated turn_id of the user turn
It is covered with. Replay within the same run goes to the same quest; separate rune
creates different tasks. The id and original Content returned to Gemini are not changed.
The empty provider id is again rejected before being added to this scope. Permanent crash
No logging or self-merging of new semantically identical calls was added.

### 2 — Incorrect success for readback in grade acceptance test

The script allows the notes.add and notes.list tools to appear, a single note in the final file.
He considered his presence sufficient. When the model first reads the empty list and then adds notes
acceptance_verified=true could appear even if the note was not read back. new test
verified the false success before fixing it by creating this sequence.

Accepted, the records in the successful notes.list result are now the only ones written to the file.
Requests that it match the synthetic note, including its ID. Empty list before insertion
cannot pass the acceptance. The test still does not access the user's actual grades.

## Evidence and remaining limit

Targeted harness before correction: two new limit states fail, three existing accept
status is successful. Full pytest after fix: **460 passed**. Gemini tests:
**41 passed**. Pyright for GeminiText, ModelTools, acceptance script and tests:
**0 errors, 0 warnings**. pip check is clear. No new dependencies or automatic retry were added.

User's last live catalog report HTTP 503 / UNAVAILABLE and empty tool_results
Contains. No new live requests were made in this review; 503 of local fixes
It is not claimed to fix it. Key/quota/model account and Live audio connection
This is not evidence of controlled testing. 5.2 live admission remains open.

Send_realtime_input of the skill during the live phase, processing all event parts,
Rules for clearing audio queues on interruption and session resumption
will be implemented. NON_BLOCKING and interaction_status if Extended Thinking is selected
requirements will be discussed separately. Minimal thinking level in skill main text
statement contradicts the migration reference; this value was not added to the existing code and
The live application turn will be based on the model's official card.

## Control processed official sources

Skill's llms.txt directory was read and the relevant pages were selected. Gemini documentation
Since there is no MCP tool available, official web sources were used:

- [Document index](https://ai.google.dev/gemini-api/docs/llms.txt)
- [Generate Content toolcalls](https://ai.google.dev/gemini-api/docs/generate-content/function-calling.md.txt)
- [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
- [Gemini 3.8 Live and migration rules](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live)
