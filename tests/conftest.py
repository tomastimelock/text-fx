"""Shared fixtures for the text-fx test suite."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_venv_on_path():
    """Add the current Python's Scripts/bin dir to PATH so CLI tools are found."""
    scripts_dir = str(Path(sys.executable).parent)
    current_path = os.environ.get("PATH", "")
    if scripts_dir not in current_path:
        os.environ["PATH"] = scripts_dir + os.pathsep + current_path


@pytest.fixture(scope="session")
def tiny_video(tmp_path_factory):
    """Synthesize a 4-second 640x360 dark blue video with audio."""
    out = tmp_path_factory.mktemp("clips") / "bg.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=darkblue:s=640x360:d=4",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=4",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


@pytest.fixture(scope="session")
def short_video(tmp_path_factory):
    """1-second 320x180 black video for fast tests that don't need duration."""
    out = tmp_path_factory.mktemp("clips") / "short.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=black:s=320x180:d=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


@pytest.fixture(scope="session")
def default_config():
    """A minimal TextEffectConfig for reuse in unit tests."""
    from text_fx.config import TextEffectConfig

    return TextEffectConfig(text="HELLO", effect="fade_in", duration=1.0)


@pytest.fixture(scope="session")
def tiny_rgba_image():
    """A small synthetic RGBA Pillow image for engine unit tests."""
    from PIL import Image

    img = Image.new("RGBA", (320, 80), (255, 255, 255, 200))
    return img
