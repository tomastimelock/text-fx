# Filepath: text_fx/engines/neon/sweep.py
# Condensed Description: Light sweep and scan engine for sweep, laser, spotlight, strobe, flash effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: SweepEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: SweepEngine
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
from text_fx.typography.renderer import _parse_color, resolve_position

logger = logging.getLogger(__name__)


class SweepEngine(Engine):
    """Engine for light sweep and scan effects.

    Modes:
        linear_sweep: bright band sweeps left to right
        laser: sharp laser scan line
        spotlight: oval spotlight that moves
        strobe: rapid strobe flash
        flash: single bright flash
        chrome: chrome/metallic shine sweep (fallback for web_overlay absent)

    Params:
        color: CSS hex color for the sweep highlight
        width_frac: float — sweep band width as fraction of image width
        speed: float — sweep speed (passes per second)
        strobe_hz: float — strobe frequency
        mode: see above
    """

    name = "sweep"
    bases = ("sweep",)

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
        """Render sweep animation.

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
        sweep_color_str = params.get("color", "#FFFFFF")
        width_frac = float(params.get("width_frac", 0.2))
        speed = float(params.get("speed", 1.0))
        strobe_hz = float(params.get("strobe_hz", 4.0))
        mode = params.get("mode", "linear_sweep")

        sweep_color = _parse_color(sweep_color_str)
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

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                # Base text (revealed on progress)
                base_text = self._apply_alpha_mult(text_image, progress)
                self._paste_text(canvas, base_text, px, py)

                if mode == "linear_sweep":
                    sweep_pos = (t * speed) % 1.5 - 0.25  # Overscan
                    self._apply_linear_sweep(
                        canvas, text_image, sweep_pos, width_frac, sweep_color, px, py, tw, th
                    )

                elif mode == "laser":
                    laser_y_frac = (t * speed) % 1.0
                    self._apply_laser(canvas, laser_y_frac, sweep_color, tw, th, px, py)

                elif mode == "spotlight":
                    spot_x = 0.5 + 0.4 * np.sin(2.0 * np.pi * t * speed)
                    spot_y = 0.5 + 0.1 * np.cos(2.0 * np.pi * t * speed * 1.3)
                    self._apply_spotlight(canvas, spot_x, spot_y, sweep_color, tw, th, px, py)

                elif mode in ("strobe",):
                    strobe_on = np.sin(2.0 * np.pi * strobe_hz * t) > 0.5
                    if strobe_on:
                        flash = self._apply_alpha_mult(text_image, 0.5)
                        flash_arr = np.array(flash, dtype=np.float32)
                        flash_arr[:, :, :3] = np.clip(flash_arr[:, :, :3] + 80, 0, 255)
                        self._paste_text(
                            canvas, Image.fromarray(flash_arr.astype(np.uint8), "RGBA"), px, py
                        )

                elif mode in ("flash",):
                    flash_alpha = max(0.0, 1.0 - t * 3.0)
                    if flash_alpha > 0:
                        bright = self._apply_alpha_mult(text_image, flash_alpha)
                        bright_arr = np.array(bright, dtype=np.float32)
                        bright_arr[:, :, :3] = np.clip(bright_arr[:, :, :3] + 100, 0, 255)
                        self._paste_text(
                            canvas, Image.fromarray(bright_arr.astype(np.uint8), "RGBA"), px, py
                        )

                elif mode == "chrome":
                    sweep_pos = (t * speed) % 1.5 - 0.25
                    self._apply_chrome_sweep(
                        canvas, text_image, sweep_pos, sweep_color, px, py, tw, th
                    )

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _apply_linear_sweep(
        self,
        canvas: Image.Image,
        text_img: Image.Image,
        sweep_pos: float,
        width_frac: float,
        color: tuple,
        px: int,
        py: int,
        tw: int,
        th: int,
    ) -> None:
        """Add a bright band sweep over the text.

        Args:
            canvas: Destination canvas.
            text_img: Source text image.
            sweep_pos: Band center as fraction of image width (can be outside 0-1).
            width_frac: Band width as fraction.
            color: RGBA highlight color.
            px: Text x offset.
            py: Text y offset.
            tw: Text width.
            th: Text height.
        """
        # Build a highlight mask for the sweep band
        xs = np.arange(tw, dtype=np.float32) / max(tw, 1)
        band_center = sweep_pos
        band_half = width_frac / 2.0
        dist = np.abs(xs - band_center)
        highlight = np.clip(1.0 - dist / max(band_half, 0.01), 0.0, 1.0)

        text_arr = np.array(text_img, dtype=np.float32)
        alpha = text_arr[:, :, 3] / 255.0

        # Add highlight to visible pixels
        sweep_layer = np.zeros_like(text_arr)
        sweep_layer[:, :, 0] = color[0]
        sweep_layer[:, :, 1] = color[1]
        sweep_layer[:, :, 2] = color[2]
        sweep_layer[:, :, 3] = alpha * highlight[np.newaxis, :] * 180

        sweep_img = Image.fromarray(sweep_layer.clip(0, 255).astype(np.uint8), "RGBA")
        self._paste_text(canvas, sweep_img, px, py)

    def _apply_laser(
        self,
        canvas: Image.Image,
        y_frac: float,
        color: tuple,
        tw: int,
        th: int,
        px: int,
        py: int,
    ) -> None:
        """Draw a thin horizontal laser scan line.

        Args:
            canvas: Destination canvas.
            y_frac: Vertical position as fraction.
            color: RGBA laser color.
            tw: Text width.
            th: Text height.
            px: Text x offset.
            py: Text y offset.
        """
        laser_y = py + int(th * y_frac)
        if 0 <= laser_y < canvas.height:
            from PIL import ImageDraw

            draw = ImageDraw.Draw(canvas)
            laser_color = (color[0], color[1], color[2], 200)
            draw.line([(px, laser_y), (px + tw, laser_y)], fill=laser_color, width=2)
            # Glow around laser line
            glow_color = (color[0], color[1], color[2], 60)
            for offset in range(1, 4):
                draw.line(
                    [(px, laser_y - offset), (px + tw, laser_y - offset)], fill=glow_color, width=1
                )
                draw.line(
                    [(px, laser_y + offset), (px + tw, laser_y + offset)], fill=glow_color, width=1
                )

    def _apply_spotlight(
        self,
        canvas: Image.Image,
        spot_x: float,
        spot_y: float,
        color: tuple,
        tw: int,
        th: int,
        px: int,
        py: int,
    ) -> None:
        """Draw an oval spotlight overlay.

        Args:
            canvas: Destination canvas.
            spot_x: Spotlight center x fraction.
            spot_y: Spotlight center y fraction.
            color: RGBA color.
            tw: Text width.
            th: Text height.
            px: Text x offset.
            py: Text y offset.
        """
        cx = px + int(tw * spot_x)
        cy = py + int(th * spot_y)
        radius = min(tw, th) // 3

        xs, ys = np.meshgrid(np.arange(canvas.width), np.arange(canvas.height))
        dist = np.sqrt(((xs - cx) / max(radius, 1)) ** 2 + ((ys - cy) / max(radius * 0.6, 1)) ** 2)
        spot_alpha = np.clip(1.0 - dist, 0.0, 1.0) * 120

        spot_layer = np.zeros((canvas.height, canvas.width, 4), dtype=np.uint8)
        spot_layer[:, :, 0] = color[0]
        spot_layer[:, :, 1] = color[1]
        spot_layer[:, :, 2] = color[2]
        spot_layer[:, :, 3] = spot_alpha.astype(np.uint8)

        spot_img = Image.fromarray(spot_layer, "RGBA")
        composited = Image.alpha_composite(canvas, spot_img)
        canvas.paste(composited, (0, 0))

    def _apply_chrome_sweep(
        self,
        canvas: Image.Image,
        text_img: Image.Image,
        sweep_pos: float,
        color: tuple,
        px: int,
        py: int,
        tw: int,
        th: int,
    ) -> None:
        """Apply a chrome-style gradient highlight sweep.

        Args:
            canvas: Destination canvas.
            text_img: Source text image.
            sweep_pos: Sweep position (0-1).
            color: Highlight color.
            px: Text x offset.
            py: Text y offset.
            tw: Text width.
            th: Text height.
        """
        xs = np.arange(tw, dtype=np.float32) / max(tw, 1)
        dist = np.abs(xs - sweep_pos)
        highlight = np.clip(1.0 - dist / 0.3, 0.0, 1.0)

        text_arr = np.array(text_img, dtype=np.float32)
        alpha = text_arr[:, :, 3] / 255.0

        # Multi-tone chrome gradient
        chrome_layer = np.zeros_like(text_arr)
        chrome_layer[:, :, 0] = np.clip(color[0] + 50, 0, 255)
        chrome_layer[:, :, 1] = np.clip(color[1] + 50, 0, 255)
        chrome_layer[:, :, 2] = np.clip(color[2] + 50, 0, 255)
        chrome_layer[:, :, 3] = alpha * highlight[np.newaxis, :] * 200

        chrome_img = Image.fromarray(chrome_layer.clip(0, 255).astype(np.uint8), "RGBA")
        self._paste_text(canvas, chrome_img, px, py)
