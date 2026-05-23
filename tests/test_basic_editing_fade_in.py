"""Integration test: fade_in from basic_editing category."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_fade_in_integration(tiny_video, tmp_path):
    out = tmp_path / "fade_in_integration.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="FADE IN",
        effect="fade_in",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 5000
