"""Registry'nin araç çalıştırmadan kayıt ve parametre sınırlarını koruduğunu test eder.

Test araçları yalnız bir çağrı listesine işaret koyabilecek fonksiyonlardır.
Beklenen sonuç bu listenin boş kalmasıdır; bu adım dosya/uygulama/hesap işlemez.
"""

from dataclasses import replace

import pytest

from app.core.contracts import ToolRequest, ToolSpec
from app.session.tool_registry import RegistryError, ToolRegistry


@pytest.fixture
def sample():
    """Her test için ayrı registry, şema ve çağrı gözlemcisi oluştur."""
    calls = []

    def handler(arguments, context):
        calls.append(arguments)
        raise AssertionError("Registry must not execute handlers")

    schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 1},
            "priority": {"type": "integer", "minimum": 0, "maximum": 5},
            "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 2},
            "options": {
                "type": "object", "properties": {"pin": {"type": "boolean"}},
                "additionalProperties": False,
            },
            "mode": {"enum": ["personal", "work"]},
            "due": {"type": ["string", "null"]},
        },
        "required": ["text"], "additionalProperties": False,
    }
    spec = ToolSpec(name="notes.add", description="Not ekleme", input_schema=schema,
                    handler=handler, required_capabilities=("notes.write",))
    return ToolRegistry(), spec, calls


def make_request(arguments=None, tool="notes.add"):
    """Geçerli üst sözleşme içine test edilecek araç parametrelerini yerleştir."""
    return ToolRequest(request_id="r1", source="test", principal="test-user",
                       tool=tool, arguments={"text": "Hello"} if arguments is None else arguments)


def test_register_list_and_validate_never_execute_handler(sample):
    """Başarılı parametre kontrolü bile aracı çalıştırma yetkisi değildir."""
    registry, spec, calls = sample
    registry.register(spec)
    item = registry.validate_request(make_request({"text": "Hello", "priority": 0, "due": None}))
    assert item.arguments == {"text": "Hello", "priority": 0, "due": None}
    assert registry.get("notes.add").handler is spec.handler
    assert [s.name for s in registry.list_tools()] == ["notes.add"]
    assert calls == []


def test_duplicate_name_keeps_first_registration(sample):
    """İkinci kayıt reddedilirken ilk handler ve şema korunmalı."""
    registry, spec, calls = sample
    registry.register(spec)
    with pytest.raises(RegistryError) as raised:
        registry.register(replace(spec, description="Different", handler=lambda a, c: None))
    assert raised.value.code == "duplicate_tool"
    assert registry.get(spec.name).handler is spec.handler
    assert len(registry.list_tools()) == 1
    assert calls == []


@pytest.mark.parametrize("arguments", [
    {}, {"text": ""}, {"text": 4}, {"text": "x", "unknown": True},
    {"text": "x", "priority": True}, {"text": "x", "priority": "1"},
    {"text": "x", "priority": -1}, {"text": "x", "priority": 6},
    {"text": "x", "tags": [1]}, {"text": "x", "tags": ["a", "b", "c"]},
    {"text": "x", "options": {"pin": 1}}, {"text": "x", "options": {"other": 1}},
    {"text": "x", "mode": "unknown"}, {"text": "x", "due": False},
])
def test_invalid_parameters_rejected_before_handler(sample, arguments):
    """Zorunlu alan, tür, sayı sınırı ve iç içe kurallar handler'dan önce denetlenir."""
    registry, spec, calls = sample
    registry.register(spec)
    with pytest.raises(RegistryError) as raised:
        registry.validate_request(make_request(arguments))
    assert raised.value.code == "invalid_arguments"
    assert calls == []


@pytest.mark.parametrize("schema", [
    {"type": "object", "required": "text"},
    {"type": "object", "properties": {"x": {"type": "not-a-type"}}},
    {"type": "object", "properties": {"x": {"pattern": "["}}},
    {"type": "object", "$schema": "http://json-schema.org/draft-07/schema#"},
    {"type": "object", "$ref": "https://example.invalid/schema.json"},
    {"type": "object", "properties": {"x": {"$ref": "#/$defs/item"}}},
    {"type": "object", "$dynamicRef": "https://example.invalid/schema"},
])
def test_invalid_or_unsupported_schema_cannot_leave_partial_registration(sample, schema):
    """Bozuk şema veya desteklenmeyen referans daha kayıt aşamasında reddedilir."""
    registry, spec, calls = sample
    with pytest.raises(RegistryError) as raised:
        registry.register(replace(spec, input_schema=schema))
    assert raised.value.code == "invalid_schema"
    assert registry.list_tools() == []
    assert calls == []


def test_unregistered_tool_does_not_fall_back_to_another_tool(sample):
    """Bilinmeyen isim, benzer isimli başka bir aracı seçmemeli."""
    registry, spec, _ = sample
    registry.register(spec)
    for action in [lambda: registry.get("notes.delete"),
                   lambda: registry.validate_request(make_request(tool="notes.delete"))]:
        with pytest.raises(RegistryError) as raised:
            action()
        assert raised.value.code == "unknown_tool"


def test_registry_owns_schema_and_returns_independent_copies(sample):
    """Kayıttan sonra dışarıdaki şema değişikliği kabul kurallarını gevşetmemeli."""
    registry, spec, _ = sample
    registry.register(spec)
    spec.input_schema["required"].clear()
    registry.get(spec.name).input_schema["required"].clear()
    registry.list_tools()[0].input_schema["properties"]["text"]["minLength"] = 0
    for arguments in [{}, {"text": ""}]:
        with pytest.raises(RegistryError):
            registry.validate_request(make_request(arguments))


def test_validation_returns_copy_without_inserting_defaults(sample):
    """Parametreler sessizce değiştirilmez; dönüş ve giriş aynı sözlüğü paylaşmaz."""
    registry, spec, _ = sample
    spec.input_schema["properties"]["priority"]["default"] = 2
    registry.register(spec)
    original = make_request({"text": "x", "tags": ["a"]})
    validated = registry.validate_request(original)
    original.arguments["tags"].append("b")
    assert validated.arguments == {"text": "x", "tags": ["a"]}
    assert "priority" not in validated.arguments


def test_mutated_request_rechecks_json_boundary(sample):
    """Constructor'dan sonra iç sözlüğe eklenen geçersiz nesne de engellenmeli."""
    registry, spec, _ = sample
    registry.register(spec)
    item = make_request()
    item.arguments["text"] = object()
    with pytest.raises(RegistryError) as raised:
        registry.validate_request(item)
    assert raised.value.code == "invalid_request"


def test_error_does_not_echo_sensitive_argument(sample):
    """Doğrulama hatası kütüphane mesajındaki ham kullanıcı değerini sızdırmamalı."""
    registry, spec, _ = sample
    registry.register(spec)
    secret = "private-example-value"
    with pytest.raises(RegistryError) as raised:
        registry.validate_request(make_request({"text": "x", "mode": secret}))
    assert secret not in str(raised.value)
    assert raised.value.__suppress_context__


def test_empty_registry_and_sorted_catalog(sample):
    """Katalog sırası dosya yükleme veya kayıt sırasına bağlı kalmamalı."""
    registry, spec, _ = sample
    assert registry.list_tools() == []
    registry.register(replace(spec, name="system.status"))
    registry.register(spec)
    assert [s.name for s in registry.list_tools()] == ["notes.add", "system.status"]


def test_wrong_top_level_objects_rejected(sample):
    """Sözleşme nesnesi yerine ham dict yanlışlıkla geçerse kontrollü hata verilir."""
    registry, _, _ = sample
    with pytest.raises(RegistryError):
        registry.register({})
    with pytest.raises(RegistryError):
        registry.validate_request({})
