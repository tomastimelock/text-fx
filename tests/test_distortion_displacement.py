"""Tests for the distortion displacement base engine (broken_glass_text, paper_tear_text)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_broken_glass_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "broken_glass.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SHATTER",
        effect="broken_glass_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_paper_tear_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "paper_tear.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="TEAR",
        effect="paper_tear_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000
