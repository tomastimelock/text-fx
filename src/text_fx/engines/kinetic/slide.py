# Filepath: text_fx/engines/kinetic/slide.py
# Condensed Description: Translational motion engine for slide effects in any direction
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: SlideEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: SlideEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from text_fx.easing.curves import ease_out_back, get_easing
from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.renderer import resolve_position

logger = logging.getLogger(__name__)


class SlideEngine(Engine):
    """Engine for translational slide motion effects.

    Text slides onto the canvas from off-screen in a given direction.

    Params:
        direction: 'left' | 'right' | 'up' | 'down'
        overshoot: bool — apply ease_out_back for overshoot effect
        fade: bool — also fade alpha during slide
        shake: bool — add random jitter for impact_slam
        impact_frames: int — number of frames to apply shake
    """

    name = "slide"
    bases = ("slide",)

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
        """Render slide-in animation.

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
        direction = params.get("direction", config.direction or "left")
        overshoot = bool(params.get("overshoot", False))
        fade = bool(params.get("fade", False))
        shake = bool(params.get("shake", False))
        impact_frames = int(params.get("impact_frames", 4))

        # Choose easing
        easing_fn = ease_out_back if overshoot else get_easing(config.easing)

        tw, th = text_image.size
        cw, ch = canvas_size
        px_end, py_end = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        # Start position off-canvas
        if direction == "left":
            px_start, py_start = -tw, py_end
        elif direction == "right":
            px_start, py_start = cw, py_end
        elif direction == "up":
            px_start, py_start = px_end, ch
        elif direction == "down":
            px_start, py_start = px_end, -th
        else:
            px_start, py_start = -tw, py_end

        frames = max(1, int(duration * fps))
        t_array = np.linspace(0.0, 1.0, frames)
        eased = easing_fn(t_array)

        rng = np.random.default_rng(config.seed)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                progress = float(np.clip(eased[i], -0.5, 1.5))
                px = int(px_start + (px_end - px_start) * progress)
                py = int(py_start + (py_end - py_start) * progress)

                # Shake jitter for impact_slam
                if shake and i < impact_frames and progress >= 0.95:
                    jitter_mag = int(8 * config.intensity)
                    px += int(rng.integers(-jitter_mag, jitter_mag + 1))
                    py += int(rng.integers(-jitter_mag // 2, jitter_mag // 2 + 1))

                canvas = self._make_canvas(canvas_size)

                frame_img = text_image.copy()
                if fade:
                    alpha_mult = float(np.clip(eased[i], 0.0, 1.0))
                    frame_img = self._apply_alpha_mult(frame_img, alpha_mult)

                self._paste_text(canvas, frame_img, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
