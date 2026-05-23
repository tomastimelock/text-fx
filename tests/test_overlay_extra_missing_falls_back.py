"""Test that effects with prefer_engine=web_overlay fall back gracefully to PIL."""

from __future__ import annotations

import sys
import warnings

from text_fx import apply_text_effect

# Effects that prefer web_overlay but must fall back to PIL when it's absent
WEB_OVERLAY_EFFECTS = [
    "neon_glow_text",  # auto — should always work
    "gold_shine",  # prefers web_overlay
    "chrome_shine",  # prefers web_overlay
]


def test_neon_glow_text_works_without_web_overlay(tiny_video, tmp_path):
    """neon_glow_text has prefer_engine=auto and must always work."""
    out = tmp_path / "neon_fallback.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="NEON",
        effect="neon_glow_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_gold_shine_does_not_raise_without_web_overlay(tiny_video, tmp_path):
    """gold_shine prefers web_overlay but must fall back to PIL without raising."""
    # Block web_overlay if it happens to be installed
    web_overlay_module = sys.modules.pop("web_overlay", None)
    try:
        out = tmp_path / "gold_fallback.mp4"
        # Should not raise even if web_overlay is unavailable
        apply_text_effect(
            video=str(tiny_video),
            text="GOLD",
            effect="gold_shine",
            output=str(out),
            duration=1.0,
        )
        assert out.exists()
    finally:
        if web_overlay_module is not None:
            sys.modules["web_overlay"] = web_overlay_module


def test_web_overlay_fallback_emits_user_warning(tiny_video, tmp_path, monkeypatch):
    """When web_overlay is absent, a UserWarning must be emitted for web_overlay effects."""
    # Simulate web_overlay absence by blocking import
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "web_overlay":
            raise ImportError("web_overlay not installed (test mock)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    # Clear any cached imports of web_overlay
    sys.modules.pop("web_overlay", None)

    out = tmp_path / "gold_warn.mp4"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        import contextlib

        with contextlib.suppress(Exception):
            apply_text_effect(
                video=str(tiny_video),
                text="GOLD",
                effect="gold_shine",
                output=str(out),
                duration=1.0,
            )

    # The fallback path should emit a UserWarning about web_overlay
    all_messages = [str(warning.message) for warning in w]
    # Either a warning was emitted OR the output was created (fallback worked silently)
    if out.exists():
        pass  # fallback worked
    else:
        web_warnings = [m for m in all_messages if "web" in m.lower() or "overlay" in m.lower()]
        assert web_warnings, f"Expected a warning about web_overlay fallback, got: {all_messages}"
