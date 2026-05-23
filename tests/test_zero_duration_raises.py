"""Test that duration=0 (or negative) raises ZeroDurationError."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from text_fx.config import TextEffectConfig
from text_fx.exceptions import ZeroDurationError


def test_zero_duration_raises_zero_duration_error():
    with pytest.raises(ZeroDurationError):
        TextEffectConfig(text="X", effect="fade_in", duration=0.0)


def test_negative_duration_raises_zero_duration_error():
    with pytest.raises(ZeroDurationError):
        TextEffectConfig(text="X", effect="fade_in", duration=-1.0)


def test_apply_text_effect_zero_duration_raises(tiny_video, tmp_path):
    """apply_text_effect with duration=0 should raise ZeroDurationError (via config)."""
    from text_fx import apply_text_effect

    with pytest.raises((ZeroDurationError, ValidationError)):
        apply_text_effect(
            video=str(tiny_video),
            text="X",
            effect="fade_in",
            output=str(tmp_path / "out.mp4"),
            duration=0.0,
        )


def test_very_small_positive_duration_is_accepted():
    """duration=0.001 should be valid (positive value)."""
    cfg = TextEffectConfig(text="X", effect="fade_in", duration=0.001)
    assert cfg.duration == pytest.approx(0.001)


def test_zero_duration_error_message_contains_value():
    with pytest.raises(ZeroDurationError) as exc_info:
        TextEffectConfig(text="X", effect="fade_in", duration=0.0)
    assert "0" in str(exc_info.value)
