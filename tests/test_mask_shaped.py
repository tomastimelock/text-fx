"""Tests for the mask shaped base engine (box_reveal, venetian_blinds)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_box_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "box_reveal.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BOX REVEAL",
        effect="box_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_venetian_blinds_produces_output(tiny_video, tmp_path):
    out = tmp_path / "venetian_blinds.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BLINDS",
        effect="venetian_blinds",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_shutter_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "shutter_reveal.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="SHUTTER",
        effect="shutter_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
