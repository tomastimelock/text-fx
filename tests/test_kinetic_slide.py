"""Tests for the kinetic slide base engine (slide_left_text, slide_right_text)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_slide_left_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "slide_left.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SLIDE LEFT",
        effect="slide_left_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_slide_right_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "slide_right.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SLIDE RIGHT",
        effect="slide_right_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_slide_up_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "slide_up.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SLIDE UP",
        effect="slide_up_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_drop_in_produces_output(tiny_video, tmp_path):
    out = tmp_path / "drop_in.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="DROP",
        effect="drop_in",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
