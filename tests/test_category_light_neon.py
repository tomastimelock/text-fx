"""Per-category integration test: light_neon."""

from __future__ import annotations

import pytest

from text_fx import apply_text_effect


@pytest.mark.parametrize(
    "effect",
    ["neon_glow_text", "glow_pulse", "light_sweep", "lens_dust_sparkle"],
)
def test_light_neon_renders(tiny_video, tmp_path, effect):
    out = tmp_path / f"{effect}.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="NEON",
        effect=effect,
        output=str(out),
        duration=1.0,
    )
    assert out.exists(), f"Output file not created for effect '{effect}'"
    assert out.stat().st_size > 1000, f"Output file too small for effect '{effect}'"
