"""Tests for the alpha cascade base engine (character_fade_cascade, word_fade_cascade)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_character_fade_cascade_produces_output(tiny_video, tmp_path):
    out = tmp_path / "char_cascade.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="HELLO",
        effect="character_fade_cascade",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_word_fade_cascade_produces_output(tiny_video, tmp_path):
    out = tmp_path / "word_cascade.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="ONE TWO THREE",
        effect="word_fade_cascade",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_character_fade_cascade_multiword(tiny_video, tmp_path):
    out = tmp_path / "char_cascade_mw.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="HELLO WORLD",
        effect="character_fade_cascade",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
