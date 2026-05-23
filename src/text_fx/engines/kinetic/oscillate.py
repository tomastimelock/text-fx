# Filepath: text_fx/engines/kinetic/oscillate.py
# Condensed Description: Oscillatory motion engine for wave, jitter, shake, wiggle, orbit, circular, scale_cascade
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: OscillateEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: OscillateEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.fonts import load_font
from text_fx.typography.layout import compute_layout
from text_fx.typography.renderer import render_text_layers, resolve_position

logger = logging.getLogger(__name__)


class OscillateEngine(Engine):
    """Engine for oscillatory motion effects.

    Modes:
        wave: sine-wave displacement per character
        jitter: random per-frame displacement
        shake: decaying random shake
        wiggle: low-frequency noise oscillation
        orbit: circular orbit around rest position
        circular: circular path motion
        scale_cascade: staggered scale oscillation

    Params:
        mode: see above
        amplitude: float — displacement amplitude in pixels
        frequency: float — oscillation frequency
        phase_per_unit: float — phase offset per character/word
        unit: 'char' | 'word' | 'whole'
    """

    name = "oscillate"
    bases = ("oscillate",)

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
        """Render oscillation animation.

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
        mode = params.get("mode", "wave")
        amplitude = float(params.get("amplitude", 20.0)) * config.intensity
        frequency = float(params.get("frequency", 2.0))
        phase_per_unit = float(params.get("phase_per_unit", 0.4))
        unit = params.get("unit", "char")

        frames = max(1, int(duration * fps))
        tw, th = text_image.size
        px_c, py_c = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        rng = np.random.default_rng(config.seed)

        if mode in ("wave", "wiggle") and unit != "whole":
            return self._render_per_unit(
                text_image,
                params,
                config,
                duration,
                fps,
                canvas_size,
                output,
                mode,
                amplitude,
                frequency,
                phase_per_unit,
                unit,
                rng,
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                canvas = self._make_canvas(canvas_size)

                if mode == "shake":
                    # Decaying random shake
                    decay = np.exp(-3.0 * i / frames)
                    dx = int(rng.normal(0, amplitude * decay))
                    dy = int(rng.normal(0, amplitude * 0.3 * decay))
                    frame_img = text_image.copy()
                    self._paste_text(canvas, frame_img, px_c + dx, py_c + dy)

                elif mode == "jitter":
                    dx = int(rng.uniform(-amplitude, amplitude))
                    dy = int(rng.uniform(-amplitude * 0.3, amplitude * 0.3))
                    frame_img = text_image.copy()
                    self._paste_text(canvas, frame_img, px_c + dx, py_c + dy)

                elif mode == "orbit":
                    angle = 2.0 * np.pi * frequency * t
                    dx = int(amplitude * np.cos(angle))
                    dy = int(amplitude * 0.5 * np.sin(angle))
                    frame_img = text_image.copy()
                    self._paste_text(canvas, frame_img, px_c + dx, py_c + dy)

                elif mode == "circular":
                    angle = 2.0 * np.pi * frequency * t
                    dx = int(amplitude * np.cos(angle))
                    dy = int(amplitude * np.sin(angle))
                    frame_img = text_image.copy()
                    self._paste_text(canvas, frame_img, px_c + dx, py_c + dy)

                elif mode == "scale_cascade":
                    scale = 1.0 + 0.15 * np.sin(2.0 * np.pi * frequency * t) * config.intensity
                    scaled_img, (off_x, off_y) = self._scale_image(text_image, float(scale))
                    self._paste_text(canvas, scaled_img, px_c + off_x, py_c + off_y)

                else:
                    # Default: wave on whole text
                    dy = int(amplitude * np.sin(2.0 * np.pi * frequency * t))
                    self._paste_text(canvas, text_image.copy(), px_c, py_c + dy)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _render_per_unit(
        self,
        text_image: Image.Image,
        params: dict,
        config: Any,
        duration: float,
        fps: int,
        canvas_size: tuple[int, int],
        output: Path,
        mode: str,
        amplitude: float,
        frequency: float,
        phase_per_unit: float,
        unit: str,
        rng: np.random.Generator,
    ) -> Path:
        """Render oscillation with per-character or per-word phases.

        Args:
            text_image: Full text image for sizing.
            params: Engine params.
            config: TextEffectConfig.
            duration: Duration in seconds.
            fps: Frame rate.
            canvas_size: Canvas dimensions.
            output: Output path.
            mode: Oscillation mode.
            amplitude: Max displacement.
            frequency: Oscillation frequency.
            phase_per_unit: Phase increment per unit.
            unit: 'char' or 'word'.
            rng: Random generator.

        Returns:
            Path to written WebM.
        """
        layers = render_text_layers(config.text, config, unit=unit)
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

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                canvas = self._make_canvas(canvas_size)

                for j, layer in enumerate(layers):
                    phase = j * phase_per_unit
                    if mode == "wave":
                        dy = int(amplitude * np.sin(2.0 * np.pi * frequency * t + phase))
                        self._paste_text(canvas, layer.copy(), px_c, py_c + dy)
                    elif mode == "wiggle":
                        dx = int(
                            amplitude * 0.3 * np.sin(2.0 * np.pi * frequency * 0.7 * t + phase)
                        )
                        dy = int(amplitude * np.sin(2.0 * np.pi * frequency * t + phase))
                        self._paste_text(canvas, layer.copy(), px_c + dx, py_c + dy)
                    else:
                        self._paste_text(canvas, layer.copy(), px_c, py_c)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
