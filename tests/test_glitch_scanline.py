"""Tests for the glitch scanline base engine (scanline_text, crt_flicker)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_scanline_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "scanline.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SCANLINE",
        effect="scanline_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_crt_flicker_produces_output(tiny_video, tmp_path):
    out = tmp_path / "crt_flicker.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="CRT",
        effect="crt_flicker",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_pixelated_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "pixelated.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="PIXEL",
        effect="pixelated_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
