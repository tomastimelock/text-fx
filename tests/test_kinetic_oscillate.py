"""Tests for the kinetic oscillate base engine (wave_text, jitter_text)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_wave_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "wave_text.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="WAVE",
        effect="wave_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_jitter_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "jitter_text.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="JITTER",
        effect="jitter_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_shake_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "shake.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SHAKE",
        effect="shake_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_wiggle_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "wiggle.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="WIGGLE",
        effect="wiggle_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
