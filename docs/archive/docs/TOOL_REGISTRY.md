# ToolRegistry — Tier 1 / row 3

Application: v1/app/session/tool_registry.py. Common types: [CORE_CONTRACTS.md](CORE_CONTRACTS.md).

Registry is the tool guide: it keeps track of name, description, parameter scheme and handler. The tool does not run, does not allow, does not install plugins from the file; task execution is in TaskManager. The built-in tool and plugin register with the same ToolSpec.

## Usage order

1. Bootstrap creates a ToolSpec and calls register(spec).
2. Registry receives a copy of the notification; controls the schema. If it is invalid, the record is not added.
3. Returns duplicate_tool if the same name already exists; The first record does not change.
4. When the request arrives validate_request(request) returns valid and copied ToolRequest or throws RegistryError.
5. [TaskManager](TASK_MANAGER.md) calls the synchronous handler after reauthentication, [policy callback](POLICY.md) and cancellation check. Parameter validation does not allow or complete execution.

## Metotlar

| Method | Conclusion |
|---|---|
| register(tool) | Saves the current ToolSpec; return None; In case of error, existing records are preserved |
| get(name) | Standalone ToolSpec copy; unknown name unknown_tool |
| list_tools() | ToolSpec copies sorted by name; is not a catalog filtered by authority |
| validate_request(request) | Separate copy of ToolRequest with validated parameters; handler not called |

RegistryError is a subtype of ContractError. The code field can be duplicate_tool, invalid_tool, invalid_schema, unknown_tool, invalid_request or invalid_arguments. Raw values ​​of tool parameters are not included in the validation error message; The general masking obligation of UI/log layers remains.

## Schema rules

New direct production dependency jsonschema>=4.26,<5; The installed version is 4.26.0. We did not write our own schema engine. Documentation: [authentication API](https://python-jsonschema.readthedocs.io/en/stable/validate/).

- Draft 2020-12 is used. If $schema exists, it should be exactly `https://json-schema.org/draft/2020-12/schema`; Otherwise, the same draft is used.
- The root type=object requirement comes from ToolSpec; The details of the schema are checked with check_schema during registration.
- The first profile rejects $ref/$dynamicRef/$recursiveRef keys in the entire schema document; Including local references. Schemas should be inline, that is, defined within themselves without the need for external references. There is no resolver network/file here.
- Rules such as required, types, enum, length/number bounds, object and array subschemas are evaluated by the library.
- To reject additional parameters, additionalProperties:false must be written in the schema. The registry does not surreptitiously add this rule to the schema.
- Values are not converted and default is not automatically applied. Null is passed only if the schema allows it; zero is preserved; boolean does not replace number. According to JSON Schema, a non-fractional number such as 1.0 can satisfy the integer rule.
- the format is the schema information, not the validation assertion in this version; FormatChecker is not enabled. Areas such as E-mail/URL should be addressed separately in the actual integration. Keys that JSON Schema does not recognize can generally be ignored by standard; check_schema is not a guarantee of finding all typos.

## Copy and borders

Register, get and list_tools copy the schemas. Changing the internal dictionary of the caller or the returned notification does not change the internal validator rules. The request is also copied through contract validation again; Data added to arguments after creation, such as the NaN/special object, is rejected.

There is no parallel recording/hot reload after startup, enabled status, plugin scanning, sandbox, policy, timeout or handler dispatch in this version. Trusted application code can access the handler directly; registry is not a security sandbox. The resource quota or regex runtime limit for Large/malicious schemas was also not applied in this step; Schemes will be reliable notifications that come with the application, user/model will not be able to save schemas.

## Test proof

`.\.venv\Scripts\python.exe -m pytest -q` in v1: 45 contracts + 30 registry tests, 75 in total passed. pip check is clear.

The new tests cover double name, unknown tool, broken/unsupported schema, nested parameter errors, schema snapshot, request copy, zero/null/boolean separation, not leaking input in the error message, and not running the handler. The actual tool, UI/native, and the model integration have not been run.
