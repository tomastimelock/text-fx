"""Test that every catalog slug has a corresponding entry in effect_mapping.json."""

from __future__ import annotations

import json
from pathlib import Path

import text_fx


def _load_mapping_as_dict() -> dict:
    """Load effect_mapping.json (list format) as a slug-keyed dict."""
    mapping_path = Path(text_fx.__file__).parent / "data" / "effect_mapping.json"
    raw = json.loads(mapping_path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {entry["slug"]: entry for entry in raw if "slug" in entry}
    return raw  # already a dict


def test_every_slug_has_mapping():
    catalog_path = Path(text_fx.__file__).parent / "data" / "effects_catalog.json"
    catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
    mapping_slugs = set(_load_mapping_as_dict().keys())
    catalog_slugs = {e["slug"] for e in catalog_data["transitions"]}
    missing = catalog_slugs - mapping_slugs
    assert not missing, f"Slugs in catalog but not in mapping: {sorted(missing)}"


def test_mapping_has_no_extra_slugs():
    """Mapping should not contain slugs that aren't in the catalog."""
    catalog_path = Path(text_fx.__file__).parent / "data" / "effects_catalog.json"
    catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
    mapping_slugs = set(_load_mapping_as_dict().keys())
    catalog_slugs = {e["slug"] for e in catalog_data["transitions"]}
    extra = mapping_slugs - catalog_slugs
    assert not extra, f"Slugs in mapping but not in catalog: {sorted(extra)}"


def test_mapping_entries_have_base_engine():
    for slug, entry in _load_mapping_as_dict().items():
        assert "base_engine" in entry, f"Mapping entry for '{slug}' missing 'base_engine'"
        assert entry["base_engine"], f"Mapping entry for '{slug}' has empty 'base_engine'"


def test_load_mapping_returns_all_slugs():
    from text_fx import list_effects
    from text_fx.catalog.mapping import load_mapping

    mapping = load_mapping()
    catalog_slugs = set(list_effects())
    mapping_slugs = set(mapping.keys())

    missing = catalog_slugs - mapping_slugs
    assert not missing, f"Mapping missing slugs: {sorted(missing)}"
