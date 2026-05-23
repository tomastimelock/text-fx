"""Tests for the alpha fade base engine (fade_in, fade_out)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_fade_in_produces_output(tiny_video, tmp_path):
    out = tmp_path / "fade_in.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="HELLO",
        effect="fade_in",
        output=str(out),
        duration=1.0,
    )
    assert out.exists(), "fade_in output file was not created"
    assert out.stat().st_size > 1000, "fade_in output file is suspiciously small"


def test_fade_out_produces_output(tiny_video, tmp_path):
    out = tmp_path / "fade_out.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="GOODBYE",
        effect="fade_out",
        output=str(out),
        duration=1.0,
    )
    assert out.exists(), "fade_out output file was not created"
    assert out.stat().st_size > 1000


def test_blur_fade_in_produces_output(tiny_video, tmp_path):
    out = tmp_path / "blur_fade_in.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BLUR IN",
        effect="blur_fade_in",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_blur_fade_out_produces_output(tiny_video, tmp_path):
    out = tmp_path / "blur_fade_out.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BLUR OUT",
        effect="blur_fade_out",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_fade_in_returns_path(tiny_video, tmp_path):
    from pathlib import Path

    out = tmp_path / "ret.mp4"
    result = apply_text_effect(
        video=str(tiny_video),
        text="TEST",
        effect="fade_in",
        output=str(out),
        duration=1.0,
    )
    assert isinstance(result, Path)
