"""Integration test: kinetic_pop from kinetic_typography category."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_kinetic_pop_integration(tiny_video, tmp_path):
    out = tmp_path / "kinetic_pop_integration.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="POP!",
        effect="kinetic_pop",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 5000
