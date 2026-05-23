# Filepath: text_fx/engines/alpha/cascade.py
# Condensed Description: Staggered-unit alpha cascade engine for per-char and per-word fade reveals
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: CascadeEngine
# Dependencies: Internal: engines/base.py, easing/curves.py, typography/fonts.py, typography/layout.py; External: numpy, Pillow; Providers: None
# Exposes: CascadeEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from text_fx.easing.curves import get_easing
from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.fonts import load_font
from text_fx.typography.layout import compute_layout
from text_fx.typography.renderer import _parse_color, resolve_position

logger = logging.getLogger(__name__)


class CascadeEngine(Engine):
    """Engine for staggered fade-in of text units (chars or words).

    Each unit fades in with a time offset relative to the previous, creating
    a cascading reveal effect.

    Params:
        unit: 'char' | 'word' — unit of stagger
        stagger_s: float — seconds between each unit's start (default auto)
        fade_duration_s: float — seconds each unit takes to fully appear
        easing: easing function name override
    """

    name = "cascade"
    bases = ("cascade",)

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
        """Render staggered cascade fade animation.

        Args:
            text_image: Pre-rendered RGBA text image.
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
        do_fade = bool(params.get("fade", True))

        font = load_font(config.font_family, config.font_size, weight=config.font_weight)
        layout = compute_layout(config.text, font, line_height_factor=config.line_height)
        main_color = _parse_color(config.color)
        stroke_color = _parse_color(config.stroke_color) if config.stroke_color else None

        easing_fn = get_easing(config.easing)

        # Build unit list and their bounding boxes
        if unit == "char":
            units_text = [ch for line in layout.lines for ch in line if ch.strip()]
            units_bbox = layout.char_bboxes
        else:
            units_text = [w for line in layout.lines for w in line.split() if w]
            units_bbox = layout.word_bboxes

        n = len(units_text)
        if n == 0:
            # No units: render blank
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                canvas = self._make_canvas(canvas_size)
                (tmpdir_path / "frame_000000.png").write_bytes(b"")
                canvas.save(tmpdir_path / "frame_000000.png")
                encode_webm(tmpdir_path, fps, output)
            return output

        # Stagger: each unit starts at a fraction of duration
        stagger_s = float(params.get("stagger_s", duration / max(n, 1) * 0.7))
        fade_duration_s = float(params.get("fade_duration_s", duration * 0.4))

        frames = max(1, int(duration * fps))
        tw, th = layout.total_size
        if tw == 0:
            tw = config.font_size * max(len(config.text), 1)
        if th == 0:
            th = config.font_size

        px, py = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        # Pre-render each unit as a tiny RGBA image
        unit_imgs: list[Image.Image] = []
        for u_text, u_bbox in zip(units_text, units_bbox, strict=False):
            uw = u_bbox[2] - u_bbox[0]
            uh = u_bbox[3] - u_bbox[1]
            if uw <= 0 or uh <= 0:
                unit_imgs.append(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
                continue
            u_img = Image.new("RGBA", (uw + 2, uh + 2), (0, 0, 0, 0))
            d = ImageDraw.Draw(u_img)
            if config.stroke_width > 0 and stroke_color is not None:
                for angle in range(0, 360, 60):
                    rad = angle * np.pi / 180.0
                    dx = int(round(config.stroke_width * np.cos(rad)))
                    dy = int(round(config.stroke_width * np.sin(rad)))
                    d.text((dx + 1, dy + 1), u_text, font=font, fill=stroke_color)
            d.text((1, 1), u_text, font=font, fill=main_color)
            unit_imgs.append(u_img)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t_sec = i / fps
                canvas = self._make_canvas(canvas_size)

                for j, (u_img, u_bbox) in enumerate(zip(unit_imgs, units_bbox, strict=False)):
                    unit_start = j * stagger_s
                    unit_t = (t_sec - unit_start) / max(fade_duration_s, 0.01)
                    unit_t = float(np.clip(unit_t, 0.0, 1.0))

                    if unit_t <= 0.0:
                        continue

                    alpha = float(easing_fn(np.array([unit_t]))[0]) if do_fade else 1.0

                    u_faded = self._apply_alpha_mult(u_img, alpha)
                    ux = px + u_bbox[0] - 1
                    uy = py + u_bbox[1] - 1
                    self._paste_text(canvas, u_faded, ux, uy)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
