"""Tests for the glitch decode base engine (hacker_decode, binary_decode)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_hacker_decode_produces_output(tiny_video, tmp_path):
    out = tmp_path / "hacker_decode.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="DECODED",
        effect="hacker_decode",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_binary_decode_produces_output(tiny_video, tmp_path):
    out = tmp_path / "binary_decode.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="01001000",
        effect="binary_decode",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_terminal_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "terminal.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="TERMINAL",
        effect="terminal_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
