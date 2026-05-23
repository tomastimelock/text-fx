"""Test that `text-fx render` produces a .webm file."""

from __future__ import annotations

import subprocess


def test_cli_render_produces_webm(tmp_path):
    out = tmp_path / "overlay.webm"
    subprocess.run(
        [
            "text-fx",
            "render",
            "--text",
            "HELLO",
            "--effect",
            "neon_glow_text",
            "--width",
            "640",
            "--height",
            "360",
            "--duration",
            "1",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    assert out.exists(), "text-fx render did not create output file"
    assert out.stat().st_size > 100, "text-fx render output is suspiciously small"


def test_cli_render_output_is_webm(tmp_path):
    out = tmp_path / "test_overlay.webm"
    subprocess.run(
        [
            "text-fx",
            "render",
            "--text",
            "TEST",
            "--effect",
            "fade_in",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    assert out.suffix == ".webm"
    assert out.exists()


def test_cli_render_with_different_effect(tmp_path):
    out = tmp_path / "kinetic.webm"
    subprocess.run(
        [
            "text-fx",
            "render",
            "--text",
            "KINETIC",
            "--effect",
            "kinetic_pop",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    assert out.exists()
