"""Tests for the glitch RGB shift base engine (rgb_split_text, chromatic_aberration)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_rgb_split_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "rgb_split.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="RGB SPLIT",
        effect="rgb_split_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_chromatic_aberration_produces_output(tiny_video, tmp_path):
    out = tmp_path / "chromatic.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="CHROMATIC",
        effect="chromatic_aberration",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000
