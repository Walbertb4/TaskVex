# Small TaskManager — Tier 1 / row 4

Application: v1/app/tasks/manager.py. No new production dependency added. Registry and common contracts are used; no real UI/model/account connection.

## Ne does?

Application → registry validation → queue → single worker → reauthentication → explicit permission callback → revocation control → handler → typed result.

Worker is a separate Python thread; activates the handlers one by one. Even while the handler is waiting, another handler does not start. That's why in this first version, all tasks, including desktop, run serially; There is no resource-wise parallelism or separate lock manager yet.

## API

| Method | Behavior |
|---|---|
| TaskManager(registry, authorize=None, capacity=256) | Creates Worker. If there is no callback, execution permission is denied. |
| describe_tools() | Provides Registry-independent name/description/parameters notifications; handler/permission does not return an object and does not grant execution permission. The model adapter further selects the visible subset. |
| submit(request) | Validates parameters; Queued Task gives the current status of a copy or the same request. It is not considered complete. |
| get(task_id) | Independent current copy of Task |
| wait(task_id, timeout=None) | The terminal waits for the result; if wait time expires TimeoutError |
| cancel(task_id) | If it is in the queue, it is cancelled; cancel_requested and Event signal if running |
| close(timeout=5.0) | Closes the new acceptance, cancels the pending ones, requests cancellation to the employee; True if worker is finished, False if it is still running |
| with TaskManager(...) | close on block exit; open shutdown_timeout error if worker does not finish |

TaskManagerError.code: closed, request_conflict, uncertain_state, capacity_exceeded, unknown_task, invalid_timeout, worker_wait and constructor validation codes. Invalid reference may also produce RegistryError. This API is the trusted in-app API; Authentication must then be performed on the login adapter to prevent a bot user from get/cancel get/cancel the task belonging to another user.

## Do not run the same request twice

- Key (principal, request_id). Different users can use the same request_id.
- Content comparison covers request data including source, principal, tool and arguments. The object key order does not change the comparison; Other differences, such as JSON number representation, can be conservatively considered different content.
- The same key and content gives the current task ID/status; The handler is not called again for queued, running, canceled or succeeded.
- Same key gives different content request_conflict. The previous task is not changed.
- In simultaneous applications, control and registration are made under the same Condition lock.
- capacity also counts terminal records. Instead of weakening relapse prevention by deregistering, new identities are rejected; query/repeat of existing records are preserved.
- The record is only in the memory of this manager instance. There is no exactly-once guarantee between a reboot, second manager or process crash. The need for permanent log/provider key/monitoring will be evaluated separately when adding actual side effects.

## Cancellation and waiting times

The task in the queue may be canceled immediately because it has not yet gone to the handler. In the running task, Event.set only sends requests. The Handler should check the signal and release its own resources safely, then return CANCELLED ToolResult.

When a late cancellation occurs, success is preserved if the handler returns a verified SUCCEEDED result. We do not ignore the completed transaction by saying "I canceled it". Cancellation after the delivery limit to the Handler does not yet guarantee that there are no side effects.

wait(timeout) is the caller's waiting time; is not the execution time of the task. TimeoutError does not cancel the task, make it unknown, or kill the thread. This version does not provide execution deadline/watchdog; ToolContext.deadline remains None. If an automatic time limit is to be added, it should be designed separately by preserving physical resource ownership.

If the close method returns False, it means that the close is not completed. Worker is not a daemon; The stuck handler is not silently abandoned at the normal process exit. Handler's closing cooperation required; The security of forced process termination is not guaranteed. Worker cannot wait on its own queue synchronously with wait or close.

## Reliability of results and standing in uncertainty

Handler returns only ToolResult. None, text, {ok:true}, incorrect task ID, or corrupted result will not translate to success; It becomes UNKNOWN. The exception thrown after the handler starts is also UNKNOWN because it does not prove that the operation was never executed. The raw exception text result/log is not added.

When UNKNOWN, subsequent handlers do not start automatically: pending tasks are canceled and new requests are rejected with uncertain_state. The status of the current ambiguous task can be queried and replayed with the same identity; cannot be restarted. There is no automatic recovery/resume API in this version. Opening a new manager and repeating the process without understanding the external situation is not considered a safe recovery.

If the Handler returns the clear result that the operation was not executed with FAILED or the verified result with SUCCEEDED, the sequence can continue. The accuracy of this statement again depends on the observation of the author of the instrument; The manager does not measure the outside world itself.

Only synchronous handler is supported. If async def is registered directly it becomes FAILED/unsupported_handler without working. If the sync function returns a coroutine, the coroutine is closed before it is started and the invalid result is considered UNKNOWN. If the Handler initiates child thread/process, it should also own their lifecycle; It should not leave an unattended background side effect after returning successfully.

## Policy link

authorize(request_copy, tool_copy) on Should return True; None, 1 or "allow" are not considered permissions. Giving a copy prevents the callback from accidentally changing the internal register or handler parameter. If the callback produces an exception, the handler does not work and the task becomes FAILED.

TaskManager is not a policy engine/approval system; [initial policy](POLICY.md) can be connected to this point with `authorize=policy.authorize` and this combination has been tested. The allow function in tests allows only test tools; A default that returns True to all tools in production has not been created.

## Validation

`.\.venv\Scripts\python.exe -m pytest -q -W error`: 45 contracts + 30 registry + 36 manager tests; A total of 111 passed. pip check is clear.

Important scenarios: 16 simultaneous replays into a single call; FIFO and queue cancellation; operation and preflight cancellation; verified success in late cancellation; Declaring the worker that does not actually finish at closing with False; standing in line in uncertainty; separation of copies; capacity/identity scope; async/null/false result; Exception data does not leak into the result.

The tests use real Python threads and Event gates; No random sleep required. Handlers in Manager unit tests are test functions. Integration with real annotation tools and system.status was also tested; Current **215 tests** and acceptance results are in [STAGE1_CORE.md](STAGE1_CORE.md). No native UI or model testing done.
