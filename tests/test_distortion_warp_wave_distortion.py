"""Integration test: wave_distortion from distortion_warp category."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_wave_distortion_integration(tiny_video, tmp_path):
    out = tmp_path / "wave_distortion_integration.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="WAVE",
        effect="wave_distortion",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 5000
