"""Test that load_font loads from an explicit .ttf path without warnings."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest


def _find_any_ttf() -> Path | None:
    """Find any .ttf file on this system to use as a test fixture."""
    import platform

    search_dirs = []
    system = platform.system()
    if system == "Windows":
        search_dirs = [Path("C:/Windows/Fonts")]
    elif system == "Darwin":
        search_dirs = [Path("/Library/Fonts"), Path("/System/Library/Fonts")]
    else:
        search_dirs = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]

    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.ttf"):
            return f
    return None


def test_load_font_from_explicit_ttf_path():
    ttf_path = _find_any_ttf()
    if ttf_path is None:
        pytest.skip("No .ttf file found on this system")

    from text_fx.typography.fonts import load_font

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        font = load_font(str(ttf_path), size=36)

    assert font is not None
    # No warning expected when path is explicit and valid
    font_warnings = [
        warning
        for warning in w
        if issubclass(warning.category, UserWarning) and "not found" in str(warning.message).lower()
    ]
    assert not font_warnings, f"Unexpected UserWarning when loading explicit path: {font_warnings}"


def test_load_font_from_explicit_path_renders():
    ttf_path = _find_any_ttf()
    if ttf_path is None:
        pytest.skip("No .ttf file found on this system")

    from PIL import Image, ImageDraw

    from text_fx.typography.fonts import load_font

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        font = load_font(str(ttf_path), size=32)

    img = Image.new("RGBA", (300, 60), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), "Test text", font=font, fill=(255, 255, 255, 255))
    pixels = list(img.getdata())
    assert any(p[3] > 0 for p in pixels), "Text should have some visible pixels"


def test_load_font_bad_path_raises():
    from text_fx.exceptions import TypographyError
    from text_fx.typography.fonts import load_font

    with pytest.raises(TypographyError):
        load_font("/nonexistent/path/to/fake_font.ttf", size=36)
