"""Integration test: rgb_split_text from glitch_digital category."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_rgb_split_text_integration(tiny_video, tmp_path):
    out = tmp_path / "rgb_split_integration.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="GLITCH",
        effect="rgb_split_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 5000
