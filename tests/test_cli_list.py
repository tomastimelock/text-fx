"""Test that `text-fx list` returns exactly 120 non-empty lines."""

from __future__ import annotations

import subprocess


def test_cli_list_returns_120_lines():
    result = subprocess.run(
        ["text-fx", "list"],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
    assert len(lines) == 120, (
        f"Expected 120 lines from `text-fx list`, got {len(lines)}.\nstdout:\n{result.stdout[:500]}"
    )


def test_cli_list_all_lines_nonempty():
    result = subprocess.run(
        ["text-fx", "list"],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
    for line in lines:
        assert line.strip(), "Found empty line in `text-fx list` output"


def test_cli_list_category_filter():
    result = subprocess.run(
        ["text-fx", "list", "--category", "light_neon"],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
    assert len(lines) > 0
    assert len(lines) < 120
