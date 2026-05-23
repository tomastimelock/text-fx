"""Tests for the neon glow base engine (neon_glow_text, glow_pulse)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_neon_glow_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "neon_glow.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="NEON",
        effect="neon_glow_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_glow_pulse_produces_output(tiny_video, tmp_path):
    out = tmp_path / "glow_pulse.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="PULSE",
        effect="glow_pulse",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_fire_glow_produces_output(tiny_video, tmp_path):
    out = tmp_path / "fire_glow.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="FIRE",
        effect="fire_glow",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_aura_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "aura.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="AURA",
        effect="aura_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
