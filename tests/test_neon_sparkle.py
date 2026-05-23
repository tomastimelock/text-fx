"""Tests for the neon sparkle base engine (lens_dust_sparkle, star_sparkle_text)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_lens_dust_sparkle_produces_output(tiny_video, tmp_path):
    out = tmp_path / "lens_dust.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SPARKLE",
        effect="lens_dust_sparkle",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_star_sparkle_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "star_sparkle.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="STARS",
        effect="star_sparkle_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000
