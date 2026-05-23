# Filepath: text_fx/engines/kinetic/spring.py
# Condensed Description: Spring physics engine for elastic text animations
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: SpringEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: SpringEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from text_fx.easing.curves import spring as spring_fn
from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.fonts import load_font
from text_fx.typography.layout import compute_layout
from text_fx.typography.renderer import render_text_layers, resolve_position

logger = logging.getLogger(__name__)


class SpringEngine(Engine):
    """Engine for spring-physics text animation.

    Applies a spring motion to scale or position, with optional per-word stagger.

    Params:
        scale_start: float — initial scale factor (e.g. 0.8 = 80%)
        scale_overshoot: float — overshoot scale factor (e.g. 1.1)
        frequency: float — spring frequency (default 8)
        damping: float — spring damping (default 3)
        per_word: bool — animate each word separately with stagger
        stagger_s: float — stagger seconds between words
        motion_blur: bool — apply motion blur to early frames
        shake: bool — add jitter on arrival
    """

    name = "spring"
    bases = ("spring",)

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
        """Render spring animation.

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
        scale_start = float(params.get("scale_start", 0.8))
        scale_overshoot = float(params.get("scale_overshoot", 1.0))
        frequency = float(params.get("frequency", 8.0))
        damping = float(params.get("damping", 3.0))
        per_word = bool(params.get("per_word", False))
        stagger_s = float(params.get("stagger_s", 0.1))

        frames = max(1, int(duration * fps))
        tw, th = text_image.size
        px_c, py_c = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        if per_word:
            return self._render_per_word(
                text_image,
                params,
                config,
                duration,
                fps,
                canvas_size,
                output,
                frequency,
                damping,
                scale_start,
                stagger_s,
            )

        # Single-unit spring on scale
        t_array = np.linspace(0.0, 1.0, frames)
        # Spring curve: starts at scale_start, overshoots toward scale_overshoot, settles at 1
        spring_curve = spring_fn(t_array, frequency=frequency, damping=damping)
        # Map spring [0,1] to [scale_start, 1+overshoot_delta]
        overshoot_delta = scale_overshoot - 1.0
        scale_range = 1.0 - scale_start
        scale_curve = (
            scale_start
            + spring_curve * scale_range
            + spring_curve * overshoot_delta * (1.0 - spring_curve)
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                scale = float(np.clip(scale_curve[i], 0.1, 4.0))
                canvas = self._make_canvas(canvas_size)
                scaled_img, (off_x, off_y) = self._scale_image(
                    text_image, scale, center=(tw // 2, th // 2)
                )
                draw_x = px_c + off_x
                draw_y = py_c + off_y
                self._paste_text(canvas, scaled_img, draw_x, draw_y)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _render_per_word(
        self,
        text_image: Image.Image,
        params: dict,
        config: Any,
        duration: float,
        fps: int,
        canvas_size: tuple[int, int],
        output: Path,
        frequency: float,
        damping: float,
        scale_start: float,
        stagger_s: float,
    ) -> Path:
        """Render spring animation with per-word stagger.

        Args:
            text_image: Full text image for sizing.
            params: Engine params.
            config: TextEffectConfig.
            duration: Duration in seconds.
            fps: Frame rate.
            canvas_size: Canvas size.
            output: Output path.
            frequency: Spring frequency.
            damping: Spring damping.
            scale_start: Starting scale.
            stagger_s: Stagger between words.

        Returns:
            Path to written WebM.
        """
        word_layers = render_text_layers(config.text, config, unit="word")
        font = load_font(config.font_family, config.font_size, weight=config.font_weight)
        layout = compute_layout(config.text, font, line_height_factor=config.line_height)

        tw, th = layout.total_size
        if tw == 0:
            tw = config.font_size * max(len(config.text), 1)
        if th == 0:
            th = config.font_size

        px_c, py_c = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        frames = max(1, int(duration * fps))
        _n_words = len(word_layers)  # noqa: F841

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t_sec = i / fps
                canvas = self._make_canvas(canvas_size)

                for j, w_layer in enumerate(word_layers):
                    word_start = j * stagger_s
                    wt = (t_sec - word_start) / max(duration - j * stagger_s, 0.1)
                    wt = float(np.clip(wt, 0.0, 1.0))

                    if wt <= 0.0:
                        continue

                    spring_v = float(
                        spring_fn(np.array([wt]), frequency=frequency, damping=damping)[0]
                    )
                    scale = scale_start + spring_v * (1.0 - scale_start)
                    scale = float(np.clip(scale, 0.1, 3.0))

                    scaled_w, (off_x, off_y) = self._scale_image(w_layer, scale)
                    alpha = float(np.clip(spring_v, 0.0, 1.0))
                    scaled_w = self._apply_alpha_mult(scaled_w, alpha)
                    self._paste_text(canvas, scaled_w, px_c + off_x, py_c + off_y)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
