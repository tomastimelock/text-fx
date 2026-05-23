"""Tests for the distortion radial warp base engine (liquid_ripple)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_liquid_ripple_produces_output(tiny_video, tmp_path):
    out = tmp_path / "liquid_ripple.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="RIPPLE",
        effect="liquid_ripple",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_bulge_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "bulge.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BULGE",
        effect="bulge_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_twirl_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "twirl.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="TWIRL",
        effect="twirl_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
