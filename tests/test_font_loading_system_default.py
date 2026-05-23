"""Test that missing font families fall back to a system default with a UserWarning."""

from __future__ import annotations

import warnings


def test_missing_font_emits_user_warning():
    from text_fx.typography.fonts import load_font

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        font = load_font("ThisFontDefinitelyDoesNotExist_xyz123", size=48)

    assert font is not None, "load_font should return a fallback font, not None"
    warning_messages = [str(warning.message) for warning in w]
    assert any(
        "not found" in msg.lower() or "fallback" in msg.lower() or "default" in msg.lower()
        for msg in warning_messages
    ), f"Expected a UserWarning about missing font, got: {warning_messages}"


def test_fallback_font_is_usable():
    """The fallback font should be usable for rendering."""
    from PIL import Image, ImageDraw

    from text_fx.typography.fonts import load_font

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        font = load_font("ThisFontDefinitelyDoesNotExist_xyz123", size=24)

    img = Image.new("RGBA", (200, 50), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Should not raise
    draw.text((0, 0), "Test", font=font, fill=(255, 255, 255, 255))


def test_missing_font_warning_category():
    from text_fx.typography.fonts import load_font

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        load_font("NoSuchFontXYZABC999", size=48)

    user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
    assert len(user_warnings) >= 1, "Expected at least one UserWarning"
