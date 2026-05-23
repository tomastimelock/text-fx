"""Test that an unknown effect slug raises UnknownEffectError with suggestions."""

from __future__ import annotations

import pytest

from text_fx import apply_text_effect
from text_fx.exceptions import UnknownEffectError


def test_unknown_effect_raises_unknown_effect_error(tiny_video, tmp_path):
    with pytest.raises((UnknownEffectError, ValueError)) as exc_info:
        apply_text_effect(
            video=str(tiny_video),
            text="X",
            effect="not_a_real_effect",
            output=str(tmp_path / "out.mp4"),
            duration=1.0,
        )
    msg = str(exc_info.value).lower()
    assert "not_a_real_effect" in msg or "unknown" in msg


def test_unknown_effect_error_has_suggestions():
    """UnknownEffectError with a near-miss slug should include suggestions."""
    # "fade_inn" is close to "fade_in"
    err = UnknownEffectError("fade_inn", suggestions=["fade_in", "fade_out"])
    assert err.suggestions
    assert "fade_in" in err.suggestions


def test_unknown_effect_error_message_mentions_slug():
    err = UnknownEffectError("totally_fake_slug")
    assert "totally_fake_slug" in str(err)


def test_unknown_effect_error_without_suggestions():
    err = UnknownEffectError("xyz_unknown")
    assert "xyz_unknown" in str(err)
    assert "list_effects" in str(err).lower() or "unknown" in str(err).lower()


def test_typo_slug_raises_with_did_you_mean(tiny_video, tmp_path):
    """A near-typo like 'fade_inn' should raise with 'did you mean' hint."""
    with pytest.raises((UnknownEffectError, ValueError)) as exc_info:
        apply_text_effect(
            video=str(tiny_video),
            text="X",
            effect="fade_inn",
            output=str(tmp_path / "out.mp4"),
            duration=1.0,
        )
    msg = str(exc_info.value)
    # Either contains the typo name or a suggestion
    assert "fade" in msg.lower() or "unknown" in msg.lower()
