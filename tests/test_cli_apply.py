"""Test that `text-fx apply` produces an .mp4 output."""

from __future__ import annotations

import subprocess


def test_cli_apply_produces_mp4(tiny_video, tmp_path):
    out = tmp_path / "out.mp4"
    subprocess.run(
        [
            "text-fx",
            "apply",
            "--video",
            str(tiny_video),
            "--text",
            "HELLO",
            "--effect",
            "fade_in",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    assert out.exists(), "text-fx apply did not create output file"
    assert out.stat().st_size > 1000, "text-fx apply output is suspiciously small"


def test_cli_apply_output_has_mp4_extension(tiny_video, tmp_path):
    out = tmp_path / "result.mp4"
    subprocess.run(
        [
            "text-fx",
            "apply",
            "--video",
            str(tiny_video),
            "--text",
            "TEST",
            "--effect",
            "neon_glow_text",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    assert out.suffix == ".mp4"
    assert out.exists()


def test_cli_apply_with_duration_flag(tiny_video, tmp_path):
    out = tmp_path / "duration_test.mp4"
    subprocess.run(
        [
            "text-fx",
            "apply",
            "--video",
            str(tiny_video),
            "--text",
            "DURATION",
            "--effect",
            "typewriter",
            "--duration",
            "1.0",
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    assert out.exists()


def test_cli_apply_unknown_effect_exits_nonzero(tiny_video, tmp_path):
    out = tmp_path / "bad.mp4"
    result = subprocess.run(
        [
            "text-fx",
            "apply",
            "--video",
            str(tiny_video),
            "--text",
            "X",
            "--effect",
            "this_does_not_exist_at_all",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Expected non-zero exit for unknown effect"
