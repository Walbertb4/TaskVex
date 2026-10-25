"""Single point of registration and parameter validation of TaskVex tools.

The registry works like a guide: which tool is there, what parameters it expects and
Which one is the handler? Handler is not called here. Queue and serial execution in TaskManager;
The actual permission rules will be connected to this execution pipeline in the next policy phase.

Tools will be explicitly registered during bootstrap; Scan folder and file Python
We do not import. There is no separate registration system for the built-in tool and the plugin tool.
"""

from dataclasses import replace
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from app.core.contracts import ContractError, ToolRequest, ToolSpec


class RegistryError(ContractError):
    """Indicates the Register/parameter error in a machine-readable code.

    code could be duplicate_tool or invalid_arguments for example. To the error text
    We do not put the incoming parameter values; they may contain confidential or personal data.
    In the future, the executor may turn this error into a ToolError.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _check_inline_schema(node: Any) -> None:
    """Check the initial version's explicit schema boundary within the document.

    We use Draft 2020-12; Another draft notification with wrong rules
    Do not interpret. This version does not support referenced schemas: $ref and similar
    cannot be found in any part of the document. Thus outsourcing schema validation
    does not download or leave the unresolved reference to the first user call.

    This little profile control is not a JSON Schema engine; required, enum,
    jsonschema controls actual rules like minLength, nested object/array.
    """
    if isinstance(node, list):
        for item in node:
            _check_inline_schema(item)
    elif isinstance(node, dict):
        if any(key in node for key in ("$ref", "$dynamicRef", "$recursiveRef")):
            raise RegistryError("invalid_schema", "Schema references are not supported")
        if "$schema" in node and node["$schema"] != Draft202012Validator.META_SCHEMA["$id"]:
            raise RegistryError("invalid_schema", "Only JSON Schema Draft 2020-12 is supported")
        for item in node.values():
            _check_inline_schema(item)


class ToolRegistry:
    """Stores tools by name; does not allow silent overwriting.

    Records are created initially; hot reload or parallel during operation
    registry change is not a contract of this version. Exported ToolSpec
    Even if the schema of the copies is changed, the record inside should not be changed.
    """

    def __init__(self) -> None:
        # Validator reuses the previously checked schema; in every request
        # It is not necessary to re-examine the structure of the same tool schema.
        self._tools: dict[str, tuple[ToolSpec, Draft202012Validator]] = {}

    def register(self, tool: ToolSpec) -> None:
        """Save current ToolSpec; Changing the registry in case of error.

        If the same name appears twice, duplicate_tool is given even if it is the same function.
        No additions to the dictionary are made until the schema and declaration control is completed.
        """
        if not isinstance(tool, ToolSpec):
            raise RegistryError("invalid_tool", "Expected ToolSpec")
        if tool.name in self._tools:
            raise RegistryError("duplicate_tool", f"Tool already registered: {tool.name}")

        # The dictionary in frozen dataclass is not deep immutable. replace,
        # It runs the ToolSpec constructor again and copies the schema again.
        # Thus, the object held by the registrar does not become an internal record of the registry.
        owned = replace(tool)
        _check_inline_schema(owned.input_schema)
        try:
            Draft202012Validator.check_schema(owned.input_schema)
        except SchemaError:
            # The library's detailed error may include examples of schema/default.
            # We do not give a general error and carry this data out in the error chain.
            raise RegistryError("invalid_schema", "Invalid JSON Schema declaration") from None
        validator = Draft202012Validator(owned.input_schema)
        self._tools[owned.name] = (owned, validator)

    def get(self, name: str) -> ToolSpec:
        """Find tool by name and return independent notification copy.

        Unknown name does not fallback or select default tool; unknown_tool error
        produces. The returning handler is still a callable Python function; a sandbox
        or authority control. The product execution path will go through the TaskManager.
        """
        if not isinstance(name, str) or name not in self._tools:
            raise RegistryError("unknown_tool", "Tool is not registered")
        return replace(self._tools[name][0])

    def list_tools(self) -> list[ToolSpec]:
        """List tools in fixed order by name, with individual notification copies.

        The result contains all records; It means that the user has the authority to call
        It doesn't come. Visible catalog filtering for Model/UI will be added later.
        """
        return [self.get(name) for name in sorted(self._tools)]

    def validate_request(self, request: ToolRequest) -> ToolRequest:
        """Find the broker, re-request copy/verify and return the current copy.

        Return parameters do not normalize: text is not numbered, null is not thrown,
        Default fields in the schema are not added automatically. Incorrect value is rejected.
        This control does not run any handler and does not grant policy permissions.
        """
        if not isinstance(request, ToolRequest):
            raise RegistryError("invalid_request", "Expected ToolRequest")
        try:
            # The arguments dictionary may have been changed after the request was created.
            # to_dict and constructor double-check the valid JSON bound.
            owned = ToolRequest(**request.to_dict())
        except ContractError:
            raise RegistryError("invalid_request", "Request violates the core contract") from None
        if owned.tool not in self._tools:
            raise RegistryError("unknown_tool", "Tool is not registered")
        validator = self._tools[owned.tool][1]
        try:
            validator.validate(owned.arguments)
        except ValidationError as error:
            # For example, 'minLength' declares the name of the control, not the user's actual name.
            # It does not put the text or parameter values such as password into the error.
            raise RegistryError(
                "invalid_arguments", f"Arguments violate schema rule: {error.validator}"
            ) from None
        return owned
