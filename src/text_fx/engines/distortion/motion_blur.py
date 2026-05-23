# Filepath: text_fx/engines/distortion/motion_blur.py
# Condensed Description: Directional motion blur engine for motion_blur_text and pixel_melt
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: MotionBlurEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: MotionBlurEngine
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


class MotionBlurEngine(Engine):
    """Engine for directional motion blur and pixel melt effects.

    Modes:
        directional: linear motion blur along an angle
        echo: directional echo trails
        zoom: radial zoom blur
        melt: column drift (pixels flow downward)

    Params:
        angle_deg: float — blur direction in degrees
        kernel_length: int — blur kernel length in pixels
        mode: 'directional' | 'zoom' | 'melt' | 'echo'
        melt_variance: float — per-column melt speed variance
    """

    name = "motion_blur"
    bases = ("motion_blur",)

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
        """Render motion blur animation.

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
        angle_deg = float(params.get("angle_deg", 0.0))
        kernel_length = int(params.get("kernel_length", 30)) * config.intensity
        mode = params.get("mode", "directional")
        melt_variance = float(params.get("melt_variance", 0.5))

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

        rng = np.random.default_rng(config.seed)
        text_arr = np.array(text_image, dtype=np.float32)

        # For melt: per-column speed
        col_speeds = 1.0 + rng.uniform(-melt_variance, melt_variance, tw)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                progress = float(eased[i])
                t = i / fps
                canvas = self._make_canvas(canvas_size)

                if mode == "directional":
                    blur_px = int(kernel_length * (1.0 - progress) + 1)
                    blurred = self._directional_blur(text_arr, angle_deg, blur_px)
                    result_img = Image.fromarray(blurred.clip(0, 255).astype(np.uint8), "RGBA")

                elif mode == "zoom":
                    result_img = self._zoom_blur(text_image, int(kernel_length * (1.0 - progress)))

                elif mode == "echo":
                    result_img = self._echo_blur(
                        text_image, angle_deg, int(kernel_length * 0.5), 4, progress
                    )

                elif mode == "melt":
                    result_img = self._melt(text_arr, col_speeds, progress, t, th, tw)

                else:
                    blur_px = int(kernel_length * (1.0 - progress) + 1)
                    blurred = self._directional_blur(text_arr, angle_deg, blur_px)
                    result_img = Image.fromarray(blurred.clip(0, 255).astype(np.uint8), "RGBA")

                self._paste_text(canvas, result_img, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _directional_blur(
        self,
        arr: np.ndarray,
        angle_deg: float,
        kernel_len: int,
    ) -> np.ndarray:
        """Apply a directional motion blur kernel.

        Args:
            arr: Float32 RGBA array.
            angle_deg: Blur direction angle.
            kernel_len: Number of blur samples.

        Returns:
            Blurred float32 RGBA array.
        """
        if kernel_len <= 1:
            return arr.copy()
        rad = np.radians(angle_deg)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
        result = np.zeros_like(arr)
        for k in range(kernel_len):
            dx = int(cos_a * k)
            dy = int(sin_a * k)
            result += np.roll(arr, (dy, dx), axis=(0, 1))
        return result / kernel_len

    def _zoom_blur(self, img: Image.Image, steps: int) -> Image.Image:
        """Apply a radial zoom blur.

        Args:
            img: Source RGBA image.
            steps: Number of zoom levels to blend.

        Returns:
            Zoom-blurred RGBA image.
        """
        if steps <= 1:
            return img.copy()
        w, h = img.size
        result = np.zeros((h, w, 4), dtype=np.float32)
        for k in range(steps):
            scale = 1.0 + k * 0.02
            scaled, (ox, oy) = self._scale_image(img, scale)
            arr = np.zeros((h, w, 4), dtype=np.float32)
            sw, sh = scaled.size
            # Paste centered
            dest_x = max(0, -ox)
            dest_y = max(0, -oy)
            src_x = max(0, ox)
            src_y = max(0, oy)
            copy_w = min(sw - src_x, w - dest_x)
            copy_h = min(sh - src_y, h - dest_y)
            if copy_w > 0 and copy_h > 0:
                scaled_arr = np.array(scaled, dtype=np.float32)
                arr[dest_y : dest_y + copy_h, dest_x : dest_x + copy_w] = scaled_arr[
                    src_y : src_y + copy_h, src_x : src_x + copy_w
                ]
            result += arr
        result /= steps
        return Image.fromarray(result.clip(0, 255).astype(np.uint8), "RGBA")

    def _echo_blur(
        self,
        img: Image.Image,
        angle_deg: float,
        dist_px: int,
        count: int,
        fade: float,
    ) -> Image.Image:
        """Create directional echo ghost copies.

        Args:
            img: Source RGBA image.
            angle_deg: Echo direction.
            dist_px: Distance between echoes.
            count: Number of echo copies.
            fade: Overall alpha fade.

        Returns:
            Composited echo image.
        """
        w, h = img.size
        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        rad = np.radians(angle_deg)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
        for k in range(count, -1, -1):
            alpha = (1.0 - k / (count + 1)) * (1.0 - fade * 0.5)
            dx = int(-cos_a * dist_px * k)
            dy = int(-sin_a * dist_px * k)
            ghost = self._apply_alpha_mult(img, alpha)
            shifted = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            shifted.paste(ghost, (dx, dy), ghost)
            result = Image.alpha_composite(result, shifted)
        return result

    def _melt(
        self,
        arr: np.ndarray,
        col_speeds: np.ndarray,
        progress: float,
        t: float,
        th: int,
        tw: int,
    ) -> Image.Image:
        """Apply downward column-melt distortion.

        Args:
            arr: Float32 RGBA array.
            col_speeds: Per-column speed multipliers.
            progress: Animation progress.
            t: Time in seconds.
            th: Image height.
            tw: Image width.

        Returns:
            Melted RGBA image.
        """
        result = np.zeros_like(arr)
        for x in range(tw):
            melt_shift = int(progress * col_speeds[x] * th * 0.8)
            result[:, x, :] = np.roll(arr[:, x, :], melt_shift, axis=0)
            if melt_shift > 0:
                fade_start = max(0, th - melt_shift)
                n_fade = th - fade_start
                if n_fade > 0:
                    fade = np.linspace(1.0, 0.0, n_fade)
                    result[fade_start : fade_start + n_fade, x, 3] = (
                        result[fade_start : fade_start + n_fade, x, 3] * fade
                    ).clip(0, 255)
        return Image.fromarray(result.clip(0, 255).astype(np.uint8), "RGBA")
