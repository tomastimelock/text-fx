"""Tests for the kinetic spring base engine (elastic_text, spring_words)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_elastic_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "elastic.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="ELASTIC",
        effect="elastic_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_spring_words_produces_output(tiny_video, tmp_path):
    out = tmp_path / "spring_words.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SPRING WORDS",
        effect="spring_words",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_overshoot_slide_produces_output(tiny_video, tmp_path):
    out = tmp_path / "overshoot_slide.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="OVERSHOOT",
        effect="overshoot_slide",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
