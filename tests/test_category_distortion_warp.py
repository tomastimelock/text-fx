"""Per-category integration test: distortion_warp."""

from __future__ import annotations

import pytest

from text_fx import apply_text_effect


@pytest.mark.parametrize(
    "effect",
    ["wave_distortion", "liquid_ripple", "motion_blur_text", "particle_disperse"],
)
def test_distortion_warp_renders(tiny_video, tmp_path, effect):
    out = tmp_path / f"{effect}.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="WARP",
        effect=effect,
        output=str(out),
        duration=1.0,
    )
    assert out.exists(), f"Output file not created for effect '{effect}'"
    assert out.stat().st_size > 1000, f"Output file too small for effect '{effect}'"
