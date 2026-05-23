"""Tests for the mask linear wipe base engine (left_wipe, right_wipe)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_left_wipe_produces_output(tiny_video, tmp_path):
    out = tmp_path / "left_wipe.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="LEFT WIPE",
        effect="left_wipe",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_right_wipe_produces_output(tiny_video, tmp_path):
    out = tmp_path / "right_wipe.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="RIGHT WIPE",
        effect="right_wipe",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_linear_wipe_reveal_produces_output(tiny_video, tmp_path):
    out = tmp_path / "linear_wipe_reveal.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="REVEAL",
        effect="linear_wipe_reveal",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_diagonal_wipe_produces_output(tiny_video, tmp_path):
    out = tmp_path / "diagonal_wipe.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="DIAGONAL",
        effect="diagonal_wipe",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
