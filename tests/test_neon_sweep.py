"""Tests for the neon sweep base engine (light_sweep, gold_shine)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_light_sweep_produces_output(tiny_video, tmp_path):
    out = tmp_path / "light_sweep.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SWEEP",
        effect="light_sweep",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_laser_scan_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "laser_scan.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="LASER",
        effect="laser_scan_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_spotlight_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "spotlight.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SPOTLIGHT",
        effect="spotlight_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
