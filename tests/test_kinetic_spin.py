"""Tests for the kinetic spin base engine (spin_in, spin_out)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_spin_in_produces_output(tiny_video, tmp_path):
    out = tmp_path / "spin_in.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SPIN IN",
        effect="spin_in",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_spin_out_produces_output(tiny_video, tmp_path):
    out = tmp_path / "spin_out.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SPIN OUT",
        effect="spin_out",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_flip_x_produces_output(tiny_video, tmp_path):
    out = tmp_path / "flip_x.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="FLIP X",
        effect="flip_x",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_flip_y_produces_output(tiny_video, tmp_path):
    out = tmp_path / "flip_y.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="FLIP Y",
        effect="flip_y",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
