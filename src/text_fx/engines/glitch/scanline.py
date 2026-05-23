# Filepath: text_fx/engines/glitch/scanline.py
# Condensed Description: Scanline/CRT overlay engine for scanline, flicker, VHS, HUD, pixelate effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: ScanlineEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: ScanlineEngine
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
from text_fx.typography.renderer import resolve_position

logger = logging.getLogger(__name__)


class ScanlineEngine(Engine):
    """Engine for scanline/CRT-style overlay effects.

    Modes:
        scanline: alternating horizontal line darkening
        flicker: rapid alpha flicker
        vhs: VHS noise + scanlines
        bad_signal: horizontal noise displacement
        static: random noise fill
        hud: HUD/heads-up-display line overlay

    Params:
        line_gap_px: int — pixels between scanlines
        line_alpha: float — darkening amount for scanlines (0-1)
        flicker_hz: float — flicker frequency in Hz
        mode: see above
        hud_lines: bool — add HUD overlay lines
    """

    name = "scanline"
    bases = ("scanline",)

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
        """Render scanline animation.

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
        line_gap = int(params.get("line_gap_px", 4))
        line_alpha = float(params.get("line_alpha", 0.5))
        flicker_hz = float(params.get("flicker_hz", 8.0))
        mode = params.get("mode", "scanline")
        hud_lines = bool(params.get("hud_lines", mode == "hud"))

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

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                # Apply reveal fade
                frame_img = self._apply_alpha_mult(text_image, float(np.clip(progress, 0.0, 1.0)))
                self._paste_text(canvas, frame_img, px, py)

                if mode in ("scanline", "crt"):
                    canvas = self._apply_scanlines(canvas, line_gap, line_alpha, tw, th, px, py)

                elif mode == "flicker":
                    flicker_alpha = 0.7 + 0.3 * np.sin(2.0 * np.pi * flicker_hz * t)
                    canvas = self._apply_alpha_mult(canvas, float(flicker_alpha))

                elif mode == "vhs":
                    canvas = self._apply_scanlines(
                        canvas, line_gap * 2, line_alpha * 0.6, tw, th, px, py
                    )
                    canvas = self._apply_vhs_noise(canvas, rng)

                elif mode == "bad_signal":
                    canvas = self._apply_bad_signal_lines(canvas, rng)

                elif mode == "static":
                    canvas = self._apply_static_noise(canvas, rng, density=0.03)

                elif mode == "hud" or hud_lines:
                    canvas = self._apply_hud_overlay(canvas, config)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _apply_scanlines(
        self,
        img: Image.Image,
        gap: int,
        alpha: float,
        text_w: int,
        text_h: int,
        px: int,
        py: int,
    ) -> Image.Image:
        """Apply horizontal scanline darkening.

        Args:
            img: RGBA canvas image.
            gap: Pixels between each dark line.
            alpha: Darkening amount 0-1.
            text_w: Text image width.
            text_h: Text image height.
            px: Text x position on canvas.
            py: Text y position on canvas.

        Returns:
            Modified canvas with scanlines.
        """
        arr = np.array(img, dtype=np.float32)
        darken = 1.0 - alpha
        # Apply only in text region
        y0 = max(0, py)
        y1 = min(img.height, py + text_h)
        for y in range(y0, y1, max(1, gap)):
            if y < arr.shape[0]:
                arr[y, :, :3] *= darken
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")

    def _apply_vhs_noise(self, img: Image.Image, rng: np.random.Generator) -> Image.Image:
        """Add VHS-style horizontal noise bands.

        Args:
            img: RGBA canvas image.
            rng: RNG.

        Returns:
            Modified image.
        """
        arr = np.array(img, dtype=np.float32)
        h = arr.shape[0]
        # Add a few horizontal noise bands
        for _ in range(rng.integers(2, 6)):
            y = rng.integers(0, h)
            band_h = rng.integers(2, 8)
            noise = rng.uniform(0.85, 1.15, arr.shape[1])
            y1 = min(h, y + band_h)
            arr[y:y1, :, :3] *= noise[:, np.newaxis]
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")

    def _apply_bad_signal_lines(self, img: Image.Image, rng: np.random.Generator) -> Image.Image:
        """Randomly displace horizontal lines.

        Args:
            img: RGBA canvas image.
            rng: RNG.

        Returns:
            Modified image.
        """
        arr = np.array(img, dtype=np.uint8)
        h = arr.shape[0]
        n_displaced = rng.integers(3, 12)
        for _ in range(n_displaced):
            y = rng.integers(0, h)
            offset = rng.integers(-20, 21)
            arr[y, :, :] = np.roll(arr[y, :, :], offset, axis=0)
        return Image.fromarray(arr, "RGBA")

    def _apply_static_noise(
        self, img: Image.Image, rng: np.random.Generator, density: float = 0.03
    ) -> Image.Image:
        """Apply random static noise pixels.

        Args:
            img: RGBA canvas image.
            rng: RNG.
            density: Fraction of pixels to add noise to.

        Returns:
            Modified image.
        """
        arr = np.array(img, dtype=np.uint8)
        h, w = arr.shape[:2]
        n = int(h * w * density)
        if n > 0:
            ys = rng.integers(0, h, n)
            xs = rng.integers(0, w, n)
            vals = rng.integers(150, 256, n, dtype=np.uint8)
            arr[ys, xs, 0] = vals
            arr[ys, xs, 1] = vals
            arr[ys, xs, 2] = vals
        return Image.fromarray(arr, "RGBA")

    def _apply_hud_overlay(self, img: Image.Image, config: Any) -> Image.Image:
        """Apply HUD-style decorative line overlay.

        Args:
            img: RGBA canvas image.
            config: TextEffectConfig.

        Returns:
            Modified image.
        """
        draw = ImageDraw.Draw(img)
        cw, ch = img.size
        hud_color = (0, 200, 255, 60)
        # Horizontal lines at top and bottom
        draw.line([(0, 40), (cw, 40)], fill=hud_color, width=1)
        draw.line([(0, ch - 40), (cw, ch - 40)], fill=hud_color, width=1)
        # Corner brackets
        bracket_size = 20
        corners = [(10, 10), (cw - 10, 10), (10, ch - 10), (cw - 10, ch - 10)]
        for cx_, cy_ in corners:
            sign_x = 1 if cx_ < cw // 2 else -1
            sign_y = 1 if cy_ < ch // 2 else -1
            draw.line([(cx_, cy_), (cx_ + sign_x * bracket_size, cy_)], fill=hud_color, width=2)
            draw.line([(cx_, cy_), (cx_, cy_ + sign_y * bracket_size)], fill=hud_color, width=2)
        return img
