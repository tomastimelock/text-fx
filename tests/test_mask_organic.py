"""Tests for the mask organic base engine (ink_matte_reveal)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_ink_matte_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "ink_matte.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="INK",
        effect="ink_matte_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_smoke_matte_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "smoke_matte.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SMOKE",
        effect="smoke_matte_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_paint_brush_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "paint_brush.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BRUSH",
        effect="paint_brush_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
