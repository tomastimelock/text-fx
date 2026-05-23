"""Tests for the kinetic bounce base engine (bounce_text, kinetic_pop)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_bounce_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "bounce_text.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BOUNCE",
        effect="bounce_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_kinetic_pop_produces_output(tiny_video, tmp_path):
    out = tmp_path / "kinetic_pop.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="POP",
        effect="kinetic_pop",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_punch_zoom_title_produces_output(tiny_video, tmp_path):
    out = tmp_path / "punch_zoom.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="PUNCH",
        effect="punch_zoom_title",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
