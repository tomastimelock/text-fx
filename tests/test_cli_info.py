"""Test that `text-fx info <slug>` returns JSON with expected keys."""

from __future__ import annotations

import json
import subprocess


def test_cli_info_returns_json():
    result = subprocess.run(
        ["text-fx", "info", "neon_glow_text"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


def test_cli_info_has_slug_field():
    result = subprocess.run(
        ["text-fx", "info", "neon_glow_text"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    assert data["slug"] == "neon_glow_text"


def test_cli_info_has_expected_keys():
    result = subprocess.run(
        ["text-fx", "info", "neon_glow_text"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    for key in ("name", "slug", "categories", "base_engine"):
        assert key in data, f"Key '{key}' missing from `text-fx info` output"


def test_cli_info_for_fade_in():
    result = subprocess.run(
        ["text-fx", "info", "fade_in"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    assert data["slug"] == "fade_in"
    assert "basic_editing" in data["categories"]


def test_cli_info_unknown_slug_exits_nonzero():
    result = subprocess.run(
        ["text-fx", "info", "this_slug_does_not_exist"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Expected non-zero exit for unknown slug"
