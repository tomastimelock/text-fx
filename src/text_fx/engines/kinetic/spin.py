# Filepath: text_fx/engines/kinetic/spin.py
# Condensed Description: Rotational motion engine for spin_in, spin_out, flip_x, flip_y effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: SpinEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: SpinEngine
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


class SpinEngine(Engine):
    """Engine for rotational motion effects.

    Rotates text around z, x, or y axis. Axis x and y are approximated
    via horizontal/vertical squish (perspective-approximate).

    Params:
        axis: 'z' | 'x' | 'y' | 'perspective' — rotation axis
        direction: 'in' | 'out' | 'cw' | 'ccw'
        degrees: float — total rotation (default 360 for full spin, 90 for flip)
        fade_with_spin: bool — fade alpha along with rotation
    """

    name = "spin"
    bases = ("spin",)

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
        """Render spin/rotation animation.

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
        axis = params.get("axis", "z")
        direction = params.get("direction", "in")
        degrees = float(params.get("degrees", 360.0 if axis == "z" else 180.0))
        fade_with_spin = bool(params.get("fade_with_spin", direction in ("in", "out")))

        easing_fn = get_easing(config.easing)
        frames = max(1, int(duration * fps))
        t_array = np.linspace(0.0, 1.0, frames)
        eased = easing_fn(t_array)

        tw, th = text_image.size
        px_c, py_c = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                if direction == "in":
                    # Spin from full rotation to 0
                    angle = degrees * (1.0 - progress)
                    alpha_mult = progress
                elif direction == "out":
                    # Spin from 0 to full rotation
                    angle = degrees * progress
                    alpha_mult = 1.0 - progress
                else:
                    angle = degrees * progress
                    alpha_mult = 1.0

                if axis == "z":
                    rotated = self._rotate_z(text_image, angle)
                    # Re-center after rotation
                    rw, rh = rotated.size
                    draw_x = px_c - (rw - tw) // 2
                    draw_y = py_c - (rh - th) // 2
                elif axis == "x":
                    rotated = self._flip_x_approx(
                        text_image, progress if direction == "in" else 1.0 - progress
                    )
                    draw_x = px_c
                    draw_y = py_c
                elif axis == "y":
                    rotated = self._flip_y_approx(
                        text_image, progress if direction == "in" else 1.0 - progress
                    )
                    draw_x = px_c
                    draw_y = py_c
                elif axis == "perspective":
                    rotated = self._perspective_approx(text_image, angle % 360)
                    rw, rh = rotated.size
                    draw_x = px_c - (rw - tw) // 2
                    draw_y = py_c - (rh - th) // 2
                else:
                    rotated = self._rotate_z(text_image, angle)
                    rw, rh = rotated.size
                    draw_x = px_c - (rw - tw) // 2
                    draw_y = py_c - (rh - th) // 2

                if fade_with_spin:
                    rotated = self._apply_alpha_mult(rotated, alpha_mult)

                self._paste_text(canvas, rotated, draw_x, draw_y)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _rotate_z(self, img: Image.Image, angle_deg: float) -> Image.Image:
        """Rotate image around Z axis (standard rotation).

        Args:
            img: RGBA image to rotate.
            angle_deg: Rotation angle in degrees.

        Returns:
            Rotated RGBA image (size may change to fit rotated content).
        """
        return img.rotate(-angle_deg, expand=True, resample=Image.BICUBIC)

    def _flip_x_approx(self, img: Image.Image, progress: float) -> Image.Image:
        """Approximate X-axis flip by vertically squishing the image.

        At progress=0 the image is invisible (zero height); at 1.0 it's full height.

        Args:
            img: RGBA image.
            progress: 0.0–1.0 progress.

        Returns:
            Resized image approximating a flip.
        """
        w, h = img.size
        new_h = max(1, int(h * abs(progress)))
        if new_h == h:
            return img
        resized = img.resize((w, new_h), Image.LANCZOS)
        # Pad back to original height centered
        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        y_off = (h - new_h) // 2
        result.paste(resized, (0, y_off), resized)
        return result

    def _flip_y_approx(self, img: Image.Image, progress: float) -> Image.Image:
        """Approximate Y-axis flip by horizontally squishing the image.

        Args:
            img: RGBA image.
            progress: 0.0–1.0 progress.

        Returns:
            Resized image approximating a flip.
        """
        w, h = img.size
        new_w = max(1, int(w * abs(progress)))
        if new_w == w:
            return img
        resized = img.resize((new_w, h), Image.LANCZOS)
        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x_off = (w - new_w) // 2
        result.paste(resized, (x_off, 0), resized)
        return result

    def _perspective_approx(self, img: Image.Image, angle_deg: float) -> Image.Image:
        """Approximate perspective rotation by combining scale and rotation.

        Args:
            img: RGBA image.
            angle_deg: Perspective rotation angle.

        Returns:
            Transformed image.
        """
        w, h = img.size
        # Approximate 3D rotation via horizontal scale
        x_scale = abs(np.cos(np.radians(angle_deg)))
        x_scale = max(0.05, x_scale)
        new_w = max(1, int(w * x_scale))
        resized = img.resize((new_w, h), Image.LANCZOS)
        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x_off = (w - new_w) // 2
        result.paste(resized, (x_off, 0), resized)
        return result
