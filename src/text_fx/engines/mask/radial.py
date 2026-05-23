# Filepath: text_fx/engines/mask/radial.py
# Condensed Description: Radial/circular mask reveal engine for circle_reveal and radial_reveal
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: RadialEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: RadialEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from text_fx.easing.curves import get_easing
from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.renderer import resolve_position

logger = logging.getLogger(__name__)


class RadialEngine(Engine):
    """Engine for circular/radial mask reveal effects.

    Modes:
        circle: expanding circle from a center point
        wedge: clockwise angular sweep (like a clock wipe)

    Params:
        mode: 'circle' | 'wedge'
        cx_frac: float — center x as fraction of image width (default 0.5)
        cy_frac: float — center y as fraction of image height (default 0.5)
        feather_px: int — soft edge in pixels
    """

    name = "radial"
    bases = ("radial",)

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
        """Render radial mask animation.

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
        mode = params.get("mode", "circle")
        cx_frac = float(params.get("cx_frac", 0.5))
        cy_frac = float(params.get("cy_frac", 0.5))
        feather_px = int(params.get("feather_px", 8))

        easing_fn = get_easing(config.easing)
        frames = max(1, int(duration * fps))
        t_array = np.linspace(0.0, 1.0, frames)
        eased = easing_fn(t_array)

        tw, th = text_image.size
        px, py = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        cx_px = int(tw * cx_frac)
        cy_px = int(th * cy_frac)
        max_r = np.sqrt((max(cx_px, tw - cx_px)) ** 2 + (max(cy_px, th - cy_px)) ** 2)

        xs, ys = np.meshgrid(np.arange(tw), np.arange(th))
        dist = np.sqrt((xs - cx_px) ** 2 + (ys - cy_px) ** 2)

        if mode == "wedge":
            angles = np.arctan2(ys - cy_px, xs - cx_px)  # -pi to pi
            # Normalise to 0..1 starting from -pi/2 (12 o'clock)
            angles_norm = (angles + np.pi / 2.0) % (2.0 * np.pi) / (2.0 * np.pi)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                if mode == "circle":
                    r_edge = max_r * progress
                    feather = max(1, feather_px)
                    val = np.clip((r_edge - dist) / feather + 0.5, 0.0, 1.0)
                elif mode == "wedge":
                    val = np.where(angles_norm <= progress, 1.0, 0.0).astype(np.float32)
                else:
                    r_edge = max_r * progress
                    feather = max(1, feather_px)
                    val = np.clip((r_edge - dist) / feather + 0.5, 0.0, 1.0)

                masked_text = text_image.copy()
                r, g, b, a = masked_text.split()
                a_arr = (
                    np.frombuffer(a.tobytes(), dtype=np.uint8).reshape(th, tw).astype(np.float32)
                )
                combined = (a_arr * val).clip(0, 255).astype(np.uint8)
                new_a = Image.fromarray(combined, mode="L")
                masked_text.putalpha(new_a)

                self._paste_text(canvas, masked_text, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
