"""Tests for the distortion sine warp base engine (wave_distortion)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_wave_distortion_produces_output(tiny_video, tmp_path):
    out = tmp_path / "wave_distortion.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="WAVE",
        effect="wave_distortion",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_heat_haze_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "heat_haze.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="HEAT",
        effect="heat_haze_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_stretch_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "stretch.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="STRETCH",
        effect="stretch_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
