# Filepath: text_fx/engines/kinetic/bounce.py
# Condensed Description: Bounce gravity engine for scale-overshoot and vertical bounce effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: BounceEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: BounceEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

from text_fx.easing.curves import bounce as bounce_fn
from text_fx.easing.curves import ease_out_cubic
from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.renderer import resolve_position

logger = logging.getLogger(__name__)


class BounceEngine(Engine):
    """Engine for bounce-physics text animation.

    Handles scale overshoot (kinetic_pop, punch_zoom) and positional
    bounce (bounce_text, drop_in).

    Params:
        bounce_count: int — number of bounces (default 3)
        decay: float — bounce height decay factor (0-1)
        scale_overshoot: float — peak scale factor (default 1.0 = no scale)
        scale_start: float — starting scale
        motion_blur: bool — apply motion blur on entry
        direction: 'down' — for drop_in (falls from above)
    """

    name = "bounce"
    bases = ("bounce",)

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
        """Render bounce animation.

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
        scale_start = float(params.get("scale_start", 1.0))
        scale_overshoot = float(params.get("scale_overshoot", 1.0))
        direction = params.get("direction")
        motion_blur = bool(params.get("motion_blur", False))
        bounce_height = float(params.get("bounce_height", 0.3))  # fraction of text height

        frames = max(1, int(duration * fps))
        t_array = np.linspace(0.0, 1.0, frames)

        tw, th = text_image.size
        px_c, py_c = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        # Scale animation: scale_start → overshoot → 1.0
        bounce_curve = bounce_fn(t_array)

        if scale_start != 1.0 or scale_overshoot != 1.0:
            # Mix: start at scale_start, peak at scale_overshoot, settle at 1
            scale_curve = scale_start + bounce_curve * (scale_overshoot - scale_start)
            # Correct for overshoot decay: after peak, converge to 1.0
            peak_t_idx = int(frames * 0.3)
            for j in range(peak_t_idx, frames):
                settle_t = (j - peak_t_idx) / max(frames - peak_t_idx - 1, 1)
                scale_curve[j] = scale_overshoot + (1.0 - scale_overshoot) * ease_out_cubic(
                    settle_t
                )
        else:
            scale_curve = np.ones(frames)

        # Positional bounce (drop_in / bounce_text)
        if direction == "down":
            # Text falls from above and bounces at final position
            cw, ch = canvas_size
            py_start = -th
            pos_curve = bounce_curve
            py_array = py_start + (py_c - py_start) * pos_curve
        else:
            # Vertical bounce at rest position
            bounce_amp = th * bounce_height
            py_array = py_c + bounce_amp * (1.0 - bounce_curve)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                canvas = self._make_canvas(canvas_size)
                scale = float(np.clip(scale_curve[i], 0.1, 5.0))

                if abs(scale - 1.0) > 0.01:
                    scaled_img, (off_x, off_y) = self._scale_image(text_image, scale)
                else:
                    scaled_img = text_image.copy()
                    off_x, off_y = 0, 0

                # Apply motion blur on very first frames if requested
                if motion_blur and i < int(frames * 0.2):
                    blur_amount = (1.0 - i / (frames * 0.2)) * 8 * config.intensity
                    if blur_amount > 0.5:
                        scaled_img = scaled_img.filter(ImageFilter.GaussianBlur(radius=blur_amount))

                draw_x = px_c + off_x
                draw_y = int(float(py_array[i])) + off_y

                self._paste_text(canvas, scaled_img, draw_x, draw_y)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
