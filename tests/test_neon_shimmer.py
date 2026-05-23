"""Tests for the neon shimmer base engine (hologram_text, gold_shine fallback)."""

from __future__ import annotations

from text_fx import apply_text_effect


def test_gold_shine_produces_output(tiny_video, tmp_path):
    out = tmp_path / "gold_shine.mp4"
    # gold_shine prefers web_overlay but falls back to PIL; should not raise
    apply_text_effect(
        video=str(tiny_video),
        text="GOLD",
        effect="gold_shine",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_chrome_shine_produces_output(tiny_video, tmp_path):
    out = tmp_path / "chrome_shine.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="CHROME",
        effect="chrome_shine",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()


def test_bokeh_text_produces_output(tiny_video, tmp_path):
    out = tmp_path / "bokeh.mp4"
    apply_text_effect(
        video=str(tiny_video),
        text="BOKEH",
        effect="bokeh_text",
        output=str(out),
        duration=1.0,
    )
    assert out.exists()
