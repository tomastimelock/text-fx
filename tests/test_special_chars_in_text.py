"""Test that special characters in text do not cause crashes."""

from __future__ import annotations

import pytest

from text_fx import apply_text_effect

SPECIAL_TEXTS = [
    "Hello & World",
    '"Quoted text"',
    "Café",
    "héllo",
    "1 + 2 = 3",
    "<script>",
    "It's a test",
    "\U0001f525 Fire",  # emoji
    "\U0001f600 Hello",  # emoji
    "100% done",
]


@pytest.mark.parametrize("text", SPECIAL_TEXTS)
def test_special_chars_render_without_crash(tiny_video, tmp_path, text):
    out = tmp_path / f"special_{hash(text) & 0xFFFFFF}.mp4"
    # Should not raise
    apply_text_effect(
        video=str(tiny_video),
        text=text,
        effect="fade_in",
        output=str(out),
        duration=1.0,
    )
    assert out.exists(), f"Output not created for text: {text!r}"


def test_empty_text_does_not_crash(tiny_video, tmp_path):
    """Empty text should produce output without crashing."""
    out = tmp_path / "empty_text.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="",
        effect="fade_in",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
