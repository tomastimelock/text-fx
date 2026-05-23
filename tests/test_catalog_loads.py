"""Test that the catalog loads with exactly 120 entries and expected structure."""

from __future__ import annotations

from text_fx import list_categories, list_effects


def test_120_effects():
    effects = list_effects()
    assert len(effects) == 120, f"Expected 120 effects, got {len(effects)}"


def test_6_categories():
    cats = list_categories()
    assert len(cats) == 6, f"Expected 6 categories, got {len(cats)}"


def test_categories_set():
    expected = {
        "basic_editing",
        "kinetic_typography",
        "mask_reveal",
        "glitch_digital",
        "distortion_warp",
        "light_neon",
    }
    assert set(list_categories()) == expected


def test_each_entry_has_required_fields():
    from text_fx.catalog.loader import load_catalog

    catalog = load_catalog()
    assert len(catalog) == 120
    for slug, entry in catalog.items():
        assert slug, "Slug must be non-empty"
        assert entry.name, f"Entry '{slug}' missing name"
        assert entry.categories, f"Entry '{slug}' missing categories"
        assert isinstance(entry.categories, list)


def test_list_effects_filtered_by_category():
    effects = list_effects(category="light_neon")
    assert len(effects) > 0
    assert all(isinstance(e, str) for e in effects)


def test_list_effects_sorted():
    effects = list_effects()
    assert effects == sorted(effects), "list_effects() should return sorted slugs"
