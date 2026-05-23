"""Tests for the alpha typewriter base engine (typewriter, cursor_typewriter)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_typewriter_produces_output(tiny_video, tmp_path):
    out = tmp_path / "typewriter.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="HELLO",
        effect="typewriter",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_cursor_typewriter_produces_output(tiny_video, tmp_path):
    out = tmp_path / "cursor_typewriter.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="TYPE ME",
        effect="cursor_typewriter",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_word_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "word_reveal.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="ONE TWO THREE",
        effect="word_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_backspace_delete_produces_output(tiny_video, tmp_path):
    out = tmp_path / "backspace_delete.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="DELETE ME",
        effect="backspace_delete",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
