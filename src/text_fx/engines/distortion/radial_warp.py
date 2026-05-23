# Filepath: text_fx/engines/distortion/radial_warp.py
# Condensed Description: Radial/lens warp engine for ripple, bulge, pinch, twirl, zoom_blur effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: RadialWarpEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: RadialWarpEngine
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


class RadialWarpEngine(Engine):
    """Engine for radial/lens distortion effects.

    Modes:
        ripple: expanding radial ripple
        bulge: barrel distortion pushing outward
        pinch: pincushion distortion pulling inward
        twirl: rotational twisting
        zoom_blur: radial blur from center
        magnify: lens magnification

    Params:
        mode: see above
        strength: float — warp strength 0-1
        radius_frac: float — warp radius as fraction of image size
        center_frac: tuple[float, float] — warp center (default image center)
    """

    name = "radial_warp"
    bases = ("radial_warp",)

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
        """Render radial warp animation.

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
        mode = params.get("mode", "bulge")
        strength = float(params.get("strength", 0.5)) * config.intensity
        radius_frac = float(params.get("radius_frac", 0.5))

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

        cx = tw // 2
        cy = th // 2
        radius = min(tw, th) * radius_frac

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                warped_arr = self._apply_warp(
                    np.array(text_image, dtype=np.float32),
                    tw,
                    th,
                    cx,
                    cy,
                    radius,
                    mode,
                    strength,
                    progress,
                    t,
                )

                warped_img = Image.fromarray(warped_arr.clip(0, 255).astype(np.uint8), "RGBA")
                self._paste_text(canvas, warped_img, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _apply_warp(
        self,
        arr: np.ndarray,
        w: int,
        h: int,
        cx: int,
        cy: int,
        radius: float,
        mode: str,
        strength: float,
        progress: float,
        t: float,
    ) -> np.ndarray:
        """Apply radial warp distortion to a pixel array.

        Uses bilinear sampling to avoid aliasing.

        Args:
            arr: Float32 RGBA array (h, w, 4).
            w: Width.
            h: Height.
            cx: Center x.
            cy: Center y.
            radius: Warp radius.
            mode: Warp mode.
            strength: Warp strength.
            progress: Eased animation progress.
            t: Raw time in seconds.

        Returns:
            Warped float32 RGBA array.
        """
        result = np.zeros_like(arr)
        ys, xs = np.mgrid[0:h, 0:w]

        # Vectors from center
        dx = xs.astype(np.float32) - cx
        dy = ys.astype(np.float32) - cy
        dist = np.sqrt(dx**2 + dy**2)
        # Normalised distance to radius
        norm_dist = dist / max(radius, 1.0)

        if mode == "bulge":
            factor = np.where(
                norm_dist < 1.0, 1.0 - strength * progress * (1.0 - norm_dist**2), 1.0
            )
            src_x = cx + dx * factor
            src_y = cy + dy * factor

        elif mode == "pinch":
            factor = np.where(
                norm_dist < 1.0, 1.0 + strength * progress * (1.0 - norm_dist**2), 1.0
            )
            src_x = cx + dx * factor
            src_y = cy + dy * factor

        elif mode == "twirl":
            angle = np.where(
                norm_dist < 1.0,
                strength * np.pi * progress * (1.0 - norm_dist),
                0.0,
            )
            cos_a = np.cos(angle)
            sin_a = np.sin(angle)
            src_x = cx + dx * cos_a - dy * sin_a
            src_y = cy + dx * sin_a + dy * cos_a

        elif mode == "ripple":
            phase = 2.0 * np.pi * dist / (radius * 0.5) - t * 3.0
            ripple = strength * 10.0 * np.sin(phase) * np.exp(-norm_dist)
            src_x = xs + dx / np.maximum(dist, 1.0) * ripple
            src_y = ys + dy / np.maximum(dist, 1.0) * ripple

        elif mode in ("zoom_blur",):
            # Pull pixels toward center
            factor = 1.0 - strength * 0.3 * progress
            src_x = cx + dx * factor
            src_y = cy + dy * factor

        elif mode == "magnify":
            # Magnify within radius
            factor = np.where(
                norm_dist < 1.0,
                norm_dist / np.maximum(norm_dist + strength * (1.0 - norm_dist), 0.01),
                1.0,
            )
            src_x = cx + dx * factor
            src_y = cy + dy * factor

        else:
            src_x = xs.astype(np.float32)
            src_y = ys.astype(np.float32)

        # Bilinear sampling
        src_x = np.clip(src_x, 0, w - 1.001)
        src_y = np.clip(src_y, 0, h - 1.001)
        x0 = src_x.astype(np.int32)
        y0 = src_y.astype(np.int32)
        x1 = np.minimum(x0 + 1, w - 1)
        y1 = np.minimum(y0 + 1, h - 1)
        fx = (src_x - x0)[..., np.newaxis]
        fy = (src_y - y0)[..., np.newaxis]

        result = (
            arr[y0, x0] * (1 - fx) * (1 - fy)
            + arr[y0, x1] * fx * (1 - fy)
            + arr[y1, x0] * (1 - fx) * fy
            + arr[y1, x1] * fx * fy
        )
        return result
