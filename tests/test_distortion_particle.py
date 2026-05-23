"""Tests for the distortion particle base engine (particle_disperse)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_particle_disperse_produces_output(tiny_video, tmp_path):
    out = tmp_path / "particle_disperse.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="DISPERSE",
        effect="particle_disperse",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_sand_dissolve_produces_output(tiny_video, tmp_path):
    out = tmp_path / "sand_dissolve.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SAND",
        effect="sand_dissolve",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_ash_disintegration_produces_output(tiny_video, tmp_path):
    out = tmp_path / "ash.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="ASH",
        effect="ash_disintegration",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_magnetic_assemble_produces_output(tiny_video, tmp_path):
    out = tmp_path / "magnetic.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="ASSEMBLE",
        effect="magnetic_assemble",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
