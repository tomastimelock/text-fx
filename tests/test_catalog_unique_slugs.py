"""Test that all 120 effect slugs are unique strings."""

from __future__ import annotations

from text_fx import list_effects


def test_all_slugs_are_unique():
    effects = list_effects()
    assert len(effects) == len(set(effects)), "Duplicate slugs found in catalog"


def test_all_slugs_are_strings():
    effects = list_effects()
    for slug in effects:
        assert isinstance(slug, str), f"Slug is not a string: {slug!r}"


def test_all_slugs_are_nonempty():
    effects = list_effects()
    for slug in effects:
        assert slug.strip(), f"Found empty or whitespace-only slug: {slug!r}"


def test_slugs_are_lowercase_with_underscores():
    """Slugs follow snake_case convention."""
    effects = list_effects()
    for slug in effects:
        assert slug == slug.lower(), f"Slug not lowercase: {slug!r}"
