# Filepath: text_fx/engines/alpha/typewriter.py
# Condensed Description: Typewriter engine for sequential character/word/line reveal and backspace
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: TypewriterEngine
# Dependencies: Internal: engines/base.py, easing/curves.py, typography/fonts.py, typography/layout.py; External: numpy, Pillow; Providers: None
# Exposes: TypewriterEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.fonts import load_font
from text_fx.typography.layout import compute_layout
from text_fx.typography.renderer import _parse_color, resolve_position

logger = logging.getLogger(__name__)


class TypewriterEngine(Engine):
    """Engine for sequential text reveal effects.

    Params:
        unit: 'char' | 'word' | 'line' — what unit appears each step
        reverse: bool — if True, characters disappear (backspace_delete)
        show_cursor: bool — if True, show a blinking cursor at the write position
        cursor_blink_hz: float — cursor blink frequency in Hz
        cursor_char: str — character to use as cursor (default '|')
    """

    name = "typewriter"
    bases = ("typewriter",)

    def is_available(self) -> bool:
        """Check availability.

        Returns:
            Always True.
        """
        return True

    def render_effect(
        self,
        text_image: Image.Image,
        params: dict[str, Any],
        config: Any,
        duration: float,
        fps: int,
        canvas_size: tuple[int, int],
        output: Path,
    ) -> Path:
        """Render typewriter animation.

        Args:
            text_image: Pre-rendered RGBA text image (used for sizing only).
            params: Engine params.
            config: TextEffectConfig.
            duration: Effect duration in seconds.
            fps: Output frame rate.
            canvas_size: Output canvas size.
            output: Destination WebM path.

        Returns:
            Path to written WebM.
        """
        unit = params.get("unit", "char")
        reverse = bool(params.get("reverse", False))
        show_cursor = bool(params.get("show_cursor", False))
        cursor_blink_hz = float(params.get("cursor_blink_hz", 1.5))
        cursor_char = str(params.get("cursor_char", "|"))

        text = config.text
        font = load_font(config.font_family, config.font_size, weight=config.font_weight)
        layout = compute_layout(text, font, line_height_factor=config.line_height)
        main_color = _parse_color(config.color)
        stroke_color = _parse_color(config.stroke_color) if config.stroke_color else None
        cursor_color = main_color

        # Build ordered unit list
        if unit == "char":
            units = list(text)
        elif unit == "word":
            units = []
            for line in layout.lines:
                units.extend(line.split())
        elif unit == "line":
            units = layout.lines
        else:
            units = list(text)

        n_units = max(len(units), 1)
        frames = max(1, int(duration * fps))

        # Text bounding box for positioning
        tw, th = layout.total_size
        if tw == 0:
            tw = config.font_size * max(len(text), 1)
        if th == 0:
            th = config.font_size
        px, py = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / max(frames - 1, 1)
                # How many units are visible this frame
                visible = int(round(t * n_units))
                if reverse:
                    visible = n_units - int(round(t * n_units))

                # Reconstruct partial text
                if unit == "char":
                    partial_text = "".join(units[:visible])
                elif unit == "word":
                    partial_text = " ".join(units[:visible])
                elif unit == "line":
                    partial_text = "\n".join(units[:visible])
                else:
                    partial_text = "".join(units[:visible])

                # Render partial text directly
                canvas = self._make_canvas(canvas_size)
                part_img = self._render_partial(
                    partial_text, font, main_color, stroke_color, config, canvas_size
                )
                self._paste_text(canvas, part_img, px, py)

                # Cursor
                if show_cursor and not reverse:
                    cursor_visible = int(i * cursor_blink_hz / fps) % 2 == 0
                    if cursor_visible:
                        self._draw_cursor(
                            canvas,
                            partial_text,
                            font,
                            cursor_char,
                            cursor_color,
                            px,
                            py,
                            config,
                            layout,
                        )

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _render_partial(
        self,
        text: str,
        font: Any,
        main_color: tuple,
        stroke_color: tuple | None,
        config: Any,
        canvas_size: tuple[int, int],
    ) -> Image.Image:
        """Render partial text to an RGBA image sized to the canvas.

        Args:
            text: Text substring to render.
            font: PIL font.
            main_color: RGBA fill color.
            stroke_color: Optional RGBA stroke color.
            config: TextEffectConfig.
            canvas_size: (width, height) of the canvas.

        Returns:
            RGBA image.
        """
        if not text.strip():
            return Image.new("RGBA", canvas_size, (0, 0, 0, 0))

        layout = compute_layout(text, font, line_height_factor=config.line_height)
        tw, th = layout.total_size
        if tw == 0:
            tw = config.font_size
        if th == 0:
            th = config.font_size

        img = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        import numpy as _np

        if config.stroke_width > 0 and stroke_color is not None:
            for angle in range(0, 360, 45):
                rad = angle * _np.pi / 180.0
                dx = int(round(config.stroke_width * _np.cos(rad)))
                dy = int(round(config.stroke_width * _np.sin(rad)))
                for j, line in enumerate(layout.lines):
                    if line:
                        lx, ly, _, _ = layout.line_bboxes[j]
                        draw.text((lx + dx, ly + dy), line, font=font, fill=stroke_color)

        for j, line in enumerate(layout.lines):
            if line:
                lx, ly, _, _ = layout.line_bboxes[j]
                draw.text((lx, ly), line, font=font, fill=main_color)

        return img

    def _draw_cursor(
        self,
        canvas: Image.Image,
        partial_text: str,
        font: Any,
        cursor_char: str,
        cursor_color: tuple,
        px: int,
        py: int,
        config: Any,
        original_layout: Any,
    ) -> None:
        """Draw a cursor character after the last rendered character.

        Args:
            canvas: The canvas to draw on.
            partial_text: Currently visible text.
            font: PIL font.
            cursor_char: Cursor character string.
            cursor_color: RGBA cursor color.
            px: X offset of text block on canvas.
            py: Y offset of text block on canvas.
            config: TextEffectConfig.
            original_layout: Layout of full text (for consistent vertical sizing).
        """
        draw = ImageDraw.Draw(canvas)
        layout = compute_layout(partial_text or " ", font, line_height_factor=config.line_height)
        if layout.lines:
            last_idx = len(layout.lines) - 1
            lx0, ly0, lx1, ly1 = layout.line_bboxes[last_idx]
            cx = px + lx1
            cy = py + ly0
            draw.text((cx, cy), cursor_char, font=font, fill=cursor_color)
