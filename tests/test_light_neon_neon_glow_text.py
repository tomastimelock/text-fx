"""Integration test: neon_glow_text from light_neon category."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_neon_glow_text_integration(tiny_video, tmp_path):
    out = tmp_path / "neon_glow_integration.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="NEON",
        effect="neon_glow_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 5000
