"""Test that the JSON schema's effect field enum contains all 120 slugs."""

from __future__ import annotations

from text_fx import list_effects, text_effect_schema


def test_schema_effect_enum_contains_all_slugs():
    schema = text_effect_schema()
    effect_prop = schema["properties"]["effect"]
    enum_slugs = set(effect_prop["enum"])
    catalog_slugs = set(list_effects())

    missing = catalog_slugs - enum_slugs
    assert not missing, f"Slugs in catalog but not in schema enum: {sorted(missing)}"


def test_schema_effect_enum_count():
    schema = text_effect_schema()
    enum_slugs = schema["properties"]["effect"]["enum"]
    assert len(enum_slugs) == 120, f"Expected 120 slugs in enum, got {len(enum_slugs)}"


def test_schema_is_valid_json_schema():
    schema = text_effect_schema()
    assert "$schema" in schema
    assert "properties" in schema
    assert "type" in schema
    assert schema["type"] == "object"


def test_schema_has_required_fields():
    schema = text_effect_schema()
    required = schema.get("required", [])
    assert "text" in required
    assert "effect" in required


def test_schema_json_serialisable():
    import json

    from text_fx.schema import text_effect_schema

    schema = text_effect_schema()
    # Must not raise
    serialized = json.dumps(schema)
    assert len(serialized) > 100
