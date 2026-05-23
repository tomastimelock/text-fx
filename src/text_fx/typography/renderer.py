# Filepath: text_fx/typography/renderer.py
# Condensed Description: PIL-based text rendering to RGBA Pillow Image with stroke and shadow
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: render_text, render_text_layers, resolve_position
# Dependencies: Internal: typography/fonts.py, typography/layout.py; External: Pillow, numpy; Providers: None
# Exposes: render_text, render_text_layers, resolve_position
# Configuration: None
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from text_fx.typography.fonts import load_font
from text_fx.typography.layout import LayoutResult, compute_layout

if TYPE_CHECKING:
    from text_fx.config import TextEffectConfig

logger = logging.getLogger(__name__)


def _parse_color(css_color: str) -> tuple[int, int, int, int]:
    """Parse a CSS color string to an RGBA tuple.

    Supports hex (#RGB, #RRGGBB, #RRGGBBAA) and a small set of named colors.

    Args:
        css_color: Color string, e.g. '#FF00FF', '#fff', 'white'.

    Returns:
        (R, G, B, A) tuple with values 0-255.
    """
    named: dict[str, tuple[int, int, int, int]] = {
        "white": (255, 255, 255, 255),
        "black": (0, 0, 0, 255),
        "red": (255, 0, 0, 255),
        "green": (0, 255, 0, 255),
        "blue": (0, 0, 255, 255),
        "transparent": (0, 0, 0, 0),
    }
    s = css_color.strip().lower()
    if s in named:
        return named[s]

    if s.startswith("#"):
        s = s[1:]
        if len(s) == 3:
            s = "".join(c * 2 for c in s)
        if len(s) == 6:
            r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
            return (r, g, b, 255)
        if len(s) == 8:
            r, g, b, a = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16)
            return (r, g, b, a)

    # Fallback: white
    logger.warning(f"Could not parse color '{css_color}'; defaulting to white")
    return (255, 255, 255, 255)


def resolve_position(
    position: tuple,
    canvas_size: tuple[int, int],
    text_size: tuple[int, int],
    margin_x: int = 64,
    margin_y: int = 64,
) -> tuple[int, int]:
    """Resolve a position spec to pixel (x, y) coordinates.

    Args:
        position: Tuple of (x_spec, y_spec) where each is int or keyword.
        canvas_size: (width, height) of the destination canvas.
        text_size: (width, height) of the text image.
        margin_x: Pixel margin used for 'left'/'right' alignment.
        margin_y: Pixel margin used for 'top'/'bottom' alignment.

    Returns:
        (px, py) pixel coordinates for the top-left of the text image.
    """
    cw, ch = canvas_size
    tw, th = text_size
    x_spec, y_spec = position

    if isinstance(x_spec, str):
        if x_spec == "center":
            px = (cw - tw) // 2
        elif x_spec == "left":
            px = margin_x
        elif x_spec == "right":
            px = cw - tw - margin_x
        else:
            px = (cw - tw) // 2
    else:
        px = int(x_spec)

    if isinstance(y_spec, str):
        if y_spec == "center":
            py = (ch - th) // 2
        elif y_spec == "top":
            py = margin_y
        elif y_spec == "bottom":
            py = ch - th - margin_y
        else:
            py = (ch - th) // 2
    else:
        py = int(y_spec)

    return px, py


def render_text(
    text: str,
    config: TextEffectConfig,
    max_width: int | None = None,
) -> Image.Image:
    """Render text to a transparent RGBA Pillow Image.

    The image is sized to fit the text exactly plus room for stroke and shadow.
    Stroke, shadow, and the main text are composited in order.

    Args:
        text: The text string to render. May contain newlines.
        config: TextEffectConfig providing font, color, stroke, shadow settings.
        max_width: If given, wrap text to this pixel width.

    Returns:
        RGBA Pillow Image containing the rendered text.
    """

    font = load_font(config.font_family, config.font_size, weight=config.font_weight)
    layout = compute_layout(text, font, max_width=max_width, line_height_factor=config.line_height)

    tw, th = layout.total_size
    if tw == 0 or th == 0:
        tw, th = config.font_size * max(len(text), 1), config.font_size

    # Margins for stroke and shadow
    stroke_margin = config.stroke_width + 4
    shadow_margin_x = abs(config.shadow_offset[0]) + config.shadow_blur + 4
    shadow_margin_y = abs(config.shadow_offset[1]) + config.shadow_blur + 4
    extra_x = stroke_margin + (shadow_margin_x if config.shadow_enabled else 0)
    extra_y = stroke_margin + (shadow_margin_y if config.shadow_enabled else 0)

    img_w = tw + extra_x * 2
    img_h = th + extra_y * 2
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    text_origin = (extra_x, extra_y)
    main_color = _parse_color(config.color)
    stroke_color = _parse_color(config.stroke_color) if config.stroke_color else None

    # Shadow layer
    if config.shadow_enabled:
        shadow_rgba = _parse_color(config.shadow_color)
        shadow_alpha = int(shadow_rgba[3] * config.shadow_opacity)
        shadow_color = (shadow_rgba[0], shadow_rgba[1], shadow_rgba[2], shadow_alpha)
        shadow_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        sx = text_origin[0] + config.shadow_offset[0]
        sy = text_origin[1] + config.shadow_offset[1]
        _draw_multiline(shadow_draw, layout, font, (sx, sy), shadow_color)
        if config.shadow_blur > 0:
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=config.shadow_blur))
        img = Image.alpha_composite(img, shadow_img)
        draw = ImageDraw.Draw(img)

    # Stroke layer (draw text multiple times offset in a circle)
    if config.stroke_width > 0 and stroke_color is not None:
        for angle_deg in range(0, 360, 30):
            angle_rad = angle_deg * np.pi / 180.0
            dx = int(round(config.stroke_width * np.cos(angle_rad)))
            dy = int(round(config.stroke_width * np.sin(angle_rad)))
            offset = (text_origin[0] + dx, text_origin[1] + dy)
            _draw_multiline(draw, layout, font, offset, stroke_color)

    # Main text
    _draw_multiline(draw, layout, font, text_origin, main_color)

    return img


def _draw_multiline(
    draw: ImageDraw.ImageDraw,
    layout: LayoutResult,
    font,
    origin: tuple[int, int],
    color: tuple[int, int, int, int],
) -> None:
    """Draw all lines of a layout at the given origin with the given color.

    Args:
        draw: ImageDraw instance.
        layout: Pre-computed layout.
        font: PIL font.
        origin: (x, y) top-left of the text block.
        color: RGBA fill color.
    """
    ox, oy = origin
    for i, line in enumerate(layout.lines):
        if not line:
            continue
        lx0, ly0, lx1, ly1 = layout.line_bboxes[i]
        draw.text((ox + lx0, oy + ly0), line, font=font, fill=color)


def render_text_layers(
    text: str,
    config: TextEffectConfig,
    unit: str = "char",
    max_width: int | None = None,
) -> list[Image.Image]:
    """Render text as separate RGBA images per unit (character or word).

    Each image is the same size as the full text bounding box so that engines
    can overlay them at the same position without coordinate arithmetic.

    Args:
        text: The text string to render.
        config: TextEffectConfig.
        unit: 'char' or 'word'.
        max_width: Optional wrap width.

    Returns:
        List of RGBA images, one per unit.
    """
    font = load_font(config.font_family, config.font_size, weight=config.font_weight)
    layout = compute_layout(text, font, max_width=max_width, line_height_factor=config.line_height)

    tw, th = layout.total_size
    if tw == 0 or th == 0:
        tw, th = config.font_size * max(len(text), 1), config.font_size

    main_color = _parse_color(config.color)
    stroke_color = _parse_color(config.stroke_color) if config.stroke_color else None

    bboxes = layout.char_bboxes if unit == "char" else layout.word_bboxes
    units_text = (
        [ch for line in layout.lines for ch in line if ch.strip()]
        if unit == "char"
        else [w for line in layout.lines for w in line.split() if w]
    )

    layers: list[Image.Image] = []
    for _i, (unit_text, bbox) in enumerate(zip(units_text, bboxes, strict=False)):
        img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        x0, y0 = bbox[0], bbox[1]
        if config.stroke_width > 0 and stroke_color is not None:
            for angle_deg in range(0, 360, 45):
                angle_rad = angle_deg * np.pi / 180.0
                dx = int(round(config.stroke_width * np.cos(angle_rad)))
                dy = int(round(config.stroke_width * np.sin(angle_rad)))
                draw.text((x0 + dx, y0 + dy), unit_text, font=font, fill=stroke_color)
        draw.text((x0, y0), unit_text, font=font, fill=main_color)
        layers.append(img)

    return layers
