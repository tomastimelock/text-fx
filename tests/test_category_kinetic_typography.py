"""Per-category integration test: kinetic_typography."""

from __future__ import annotations

import pytest

from text_fx import apply_text_effect


@pytest.mark.parametrize(
    "effect",
    ["kinetic_pop", "bounce_text", "slide_left_text", "wave_text"],
)
def test_kinetic_typography_renders(tiny_video, tmp_path, effect):
    out = tmp_path / f"{effect}.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="KINETIC",
        effect=effect,
        output=str(out),
        duration=1.0,
    )
    assert out.exists(), f"Output file not created for effect '{effect}'"
    assert out.stat().st_size > 1000, f"Output file too small for effect '{effect}'"
