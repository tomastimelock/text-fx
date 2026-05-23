"""Test that `text-fx categories` returns exactly 6 lines."""

from __future__ import annotations

import subprocess


def test_cli_categories_returns_6_lines():
    result = subprocess.run(
        ["text-fx", "categories"],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
    assert len(lines) == 6, (
        f"Expected 6 lines from `text-fx categories`, got {len(lines)}.\nstdout:\n{result.stdout}"
    )


def test_cli_categories_contains_expected_names():
    result = subprocess.run(
        ["text-fx", "categories"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.lower()
    expected = [
        "basic_editing",
        "kinetic_typography",
        "mask_reveal",
        "glitch_digital",
        "distortion_warp",
        "light_neon",
    ]
    for cat in expected:
        assert cat in output, f"Category '{cat}' not found in `text-fx categories` output"
