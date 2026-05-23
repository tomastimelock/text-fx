"""Integration test: circle_reveal from mask_reveal category."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_circle_reveal_integration(tiny_video, tmp_path):
    out = tmp_path / "circle_reveal_integration.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="REVEAL",
        effect="circle_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 5000
