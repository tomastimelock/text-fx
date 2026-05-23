"""Tests for the mask radial base engine (radial_reveal, circle_reveal)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_radial_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "radial_reveal.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="RADIAL",
        effect="radial_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_circle_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "circle_reveal.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="CIRCLE",
        effect="circle_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000
