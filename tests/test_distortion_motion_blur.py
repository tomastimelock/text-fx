"""Tests for the distortion motion blur base engine (motion_blur_text)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_motion_blur_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "motion_blur.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BLUR",
        effect="motion_blur_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_pixel_melt_produces_output(tiny_video, tmp_path):
    out = tmp_path / "pixel_melt.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="MELT",
        effect="pixel_melt",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000
