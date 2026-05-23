"""Test basic text rendering to RGBA Pillow image."""

from __future__ import annotations

import pytest
from PIL import Image

from text_fx.config import TextEffectConfig
from text_fx.typography.renderer import render_text


@pytest.fixture
def basic_config():
    return TextEffectConfig(text="Hello", effect="fade_in", duration=1.0, font_size=48)


def test_renders_to_rgba(basic_config):
    img = render_text("Hello", basic_config)
    assert img.mode == "RGBA"


def test_output_has_positive_dimensions(basic_config):
    img = render_text("Hello", basic_config)
    assert img.size[0] > 0
    assert img.size[1] > 0


def test_output_has_nonzero_alpha(basic_config):
    img = render_text("Hello", basic_config)
    pixels = list(img.getdata())
    alpha_values = [p[3] for p in pixels]
    assert max(alpha_values) > 0, "All pixels are fully transparent — text did not render"


def test_larger_font_produces_larger_image():
    cfg_small = TextEffectConfig(text="Hi", effect="fade_in", duration=1.0, font_size=24)
    cfg_large = TextEffectConfig(text="Hi", effect="fade_in", duration=1.0, font_size=96)
    img_small = render_text("Hi", cfg_small)
    img_large = render_text("Hi", cfg_large)
    assert img_large.size[0] >= img_small.size[0]
    assert img_large.size[1] >= img_small.size[1]


def test_returns_pillow_image(basic_config):
    img = render_text("Hello", basic_config)
    assert isinstance(img, Image.Image)


def test_renders_with_stroke():
    cfg = TextEffectConfig(
        text="Hello",
        effect="fade_in",
        duration=1.0,
        font_size=48,
        stroke_color="#000000",
        stroke_width=4,
    )
    img = render_text("Hello", cfg)
    assert img.mode == "RGBA"
    assert img.size[0] > 0 and img.size[1] > 0


def test_renders_with_shadow():
    cfg = TextEffectConfig(
        text="Hello",
        effect="fade_in",
        duration=1.0,
        font_size=48,
        shadow_enabled=True,
        shadow_color="#000000",
        shadow_blur=8,
    )
    img = render_text("Hello", cfg)
    assert img.mode == "RGBA"
    assert img.size[0] > 0 and img.size[1] > 0
