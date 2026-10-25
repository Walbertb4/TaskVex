# Initial policy rules — Stage 1, row 5

This document describes permission control in `v1/app/policy/engine.py`. policies,
"can this user run this tool?" answers the question; does not start the tool.
The first release is for a single local user and resource `desktop`.

## Permission table

| Tool | Required capability | Current situation |
|---|---|---|
| notes.add | notes.write | Real file tool connected and tested |
| notes.update | notes.write | Update with fixed ID; native UI bound |
| notes.delete | notes.write | Deletion with fixed ID; native UI bound |
| notes.initialize | notes.write | Reading the first transfer or applying it once with explicit UI confirmation |
| notes.replace | notes.write | Changing full list in open backup installation |
| apps.catalog | apps.read | Read-only supported application catalogue; installation/operation or is not authorized to open |
| apps.status | apps.read | Read-only process/window observation of permissioned application; on/off is not authorized |
| apps.open | apps.read + apps.launch | Starting Notepad with permission and verifying the window; arbitrary path/argument or no shutdown |
| notes.list | notes.read | Real file tool connected and tested |
| system.status | system.read | Read-only real system tool connected and tested |
| All other tools | No permission | Rejected |

The host explicitly chooses the privileges it will grant to the user at the beginning. If authorization is not given
All executions are rejected. Read and write are separate permissions; There is no wildcard authority.
Unknown authorization name is a configuration error; It is not accepted silently.

## Usage on existing line

```python
from app.policy.engine import PolicyEngine
from app.tasks.manager import TaskManager

# The registry is created by the trusted host. This example does not start the application;
# the actual core installation is in app.bootstrap.create_core; There is no native window.
policy = PolicyEngine(
    principal="local-user",
    capabilities=frozenset({"notes.read", "notes.write", "system.read"}),
)
with TaskManager(registry, authorize=policy.authorize) as manager:
    pass  # The ToolRequest from the trusted adapter will be submitted here.
```

Flow: registry validates parameters → manager enqueues → before execution
registry re-verifies → policy permission returns/rejects → handler works if there is permission.
Policy denial is the result of `FAILED / permission_denied`; handler is not called. to TaskManager
Not giving a callback means rejection. This step does not add a new dispatcher.

The request source for permission is exactly `desktop`, the user configured as principal,
The request tool name must also be the given ToolSpec name. With permissions on the Core table
ToolSpec.required_capabilities must match exactly and must be available to the user. Plugin
cannot bypass this check by declaring empty authorization or typing another authorization name. Permissions
is copied and stored immutable; Changing the initially given set does not add permissions.

## Confidence limit and scope

principal/source are text; pairing them is not authentication.
In the future, the reliable native input adapter will use these fields from the user/model payload.
It must create itself without copying. Telegram/Discord/model resources currently
is rejected. Python plugins are reliable application code; This policy is a sandbox
is not and does not isolate malicious Python code in the process.

Confirmation window, dynamic authorization change, file root/account scopes and risky
transactions are not available at this stage. When a new tool is added in the future, the core permission table and
The necessary target/parameter constraints should be examined together. Just register to the registry
Being or typing approval in the request arguments field does not grant authorization.

## Indirect Prompt Injection and Taint Tracking (Untrusted External Data)

A session is considered contaminated (`tainted`) when content read from L2 (DOM), L4 (screen/OCR), the Web, incoming email, or external files enters the model context. PolicyEngine does not automatically allow (`ALLOW`) side effective/critical tools (`terminal.exec`, `gmail.send`, `notes.delete`, `files.delete`, etc.) in a tainted session, even if the model mistakes this data for instructions and calls dangerous tools; necessarily raises the decision to `CONFIRM`, which asks for physical confirmation from the user in the interface. The authorization decision is made based on the RequestContext and the taint status of the session, not on the assertion of the prompt.

## Validation

`v1` directory `.\.venv\Scripts\python.exe -m pytest -q -W error`:
45 contracts + 30 registry + 36 TaskManager + 29 policy tests = **140 passed**.
Policy tests unknown tool/resource/user, missing/different authorization notification,
Includes broken configuration and immutable permissions. Permission denial with real TaskManager,
The continuation of the next job and the single execution of the repeat request are verified.

The actual not/disk tool and read-only system information are now also verified; current
Acceptance results of 215 tests are in [STAGE1_CORE.md](STAGE1_CORE.md). Native UI,
hardware check and calculations not tried; There is no UI connectivity yet.
