"""Tests for the glitch slice corrupt base engine (digital_glitch_title)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_digital_glitch_title_produces_output(tiny_video, tmp_path):
    out = tmp_path / "digital_glitch.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="GLITCH",
        effect="digital_glitch_title",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_vhs_title_produces_output(tiny_video, tmp_path):
    out = tmp_path / "vhs_title.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="VHS",
        effect="vhs_title",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_pixel_sort_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "pixel_sort.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SORTED",
        effect="pixel_sort_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
