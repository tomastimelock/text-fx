# Filepath: text_fx/engines/distortion/sine_warp.py
# Condensed Description: Sinusoidal warp engine for wave, heat haze, stretch, smear, echo effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: SineWarpEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: SineWarpEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.renderer import resolve_position

logger = logging.getLogger(__name__)


class SineWarpEngine(Engine):
    """Engine for sinusoidal displacement warping.

    Modes:
        wave: vertical sine wave displacement
        heat: slow undulating heat haze
        stretch: horizontal scale oscillation
        smear: blurred shifted copy blend
        echo: delayed copies of the text

    Params:
        amplitude_x: float — horizontal warp amplitude in pixels
        amplitude_y: float — vertical warp amplitude in pixels
        frequency: float — spatial frequency of the wave
        speed: float — animation speed (waves per second)
        mode: see above
        echo_count: int — number of echo copies
    """

    name = "sine_warp"
    bases = ("sine_warp",)

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
        """Render sinusoidal warp animation.

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
        amp_y = float(params.get("amplitude_y", 12.0)) * config.intensity
        amp_x = float(params.get("amplitude_x", 0.0)) * config.intensity
        frequency = float(params.get("frequency", 2.0))
        speed = float(params.get("speed", 1.0))
        mode = params.get("mode", "wave")
        echo_count = int(params.get("echo_count", 3))

        frames = max(1, int(duration * fps))
        tw, th = text_image.size
        px, py = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        text_arr = np.array(text_image, dtype=np.uint8)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                canvas = self._make_canvas(canvas_size)

                if mode == "wave":
                    warped = self._warp_sine_y(text_arr, amp_y, frequency, speed, t)
                elif mode == "heat":
                    warped = self._warp_heat(text_arr, amp_y * 0.5, frequency * 0.5, speed * 0.3, t)
                elif mode == "stretch":
                    warped = self._warp_stretch(text_image, amp_x, frequency, speed, t)
                    warped = np.array(warped)
                elif mode == "smear":
                    warped = self._warp_smear(text_arr, amp_y, frequency, speed, t)
                elif mode == "echo":
                    self._render_echo(canvas, text_image, echo_count, amp_x, amp_y, t, px, py)
                    frame_path = tmpdir_path / f"frame_{i:06d}.png"
                    canvas.save(frame_path)
                    continue
                else:
                    warped = self._warp_sine_y(text_arr, amp_y, frequency, speed, t)

                warped_img = Image.fromarray(warped.clip(0, 255).astype(np.uint8), "RGBA")
                self._paste_text(canvas, warped_img, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _warp_sine_y(
        self,
        arr: np.ndarray,
        amp: float,
        freq: float,
        speed: float,
        t: float,
    ) -> np.ndarray:
        """Apply vertical sine wave displacement to each row.

        Args:
            arr: RGBA pixel array.
            amp: Amplitude in pixels.
            freq: Spatial frequency (cycles per image height).
            speed: Time speed multiplier.
            t: Current time in seconds.

        Returns:
            Warped RGBA array.
        """
        h, w = arr.shape[:2]
        result = np.zeros_like(arr)
        for y in range(h):
            phase = 2.0 * np.pi * (y / h * freq + t * speed)
            offset = int(amp * np.sin(phase))
            result[y, :, :] = np.roll(arr[y, :, :], offset, axis=0)
        return result

    def _warp_heat(
        self,
        arr: np.ndarray,
        amp: float,
        freq: float,
        speed: float,
        t: float,
    ) -> np.ndarray:
        """Apply slow undulating heat-haze displacement.

        Args:
            arr: RGBA pixel array.
            amp: Max displacement amplitude.
            freq: Spatial frequency.
            speed: Time speed.
            t: Current time.

        Returns:
            Warped RGBA array.
        """
        h, w = arr.shape[:2]
        result = np.zeros_like(arr)
        for y in range(h):
            phase_x = 2.0 * np.pi * (y / h * freq * 1.3 + t * speed)
            phase_y = 2.0 * np.pi * (y / h * freq + t * speed * 0.7)
            offset_x = int(amp * np.sin(phase_x))
            offset_y = int(amp * 0.3 * np.sin(phase_y))
            src_y = max(0, min(h - 1, y + offset_y))
            result[y, :, :] = np.roll(arr[src_y, :, :], offset_x, axis=0)
        return result

    def _warp_stretch(
        self,
        img: Image.Image,
        amp: float,
        freq: float,
        speed: float,
        t: float,
    ) -> Image.Image:
        """Apply horizontal scale oscillation (stretch).

        Args:
            img: RGBA PIL Image.
            amp: Amplitude of scale variation.
            freq: Frequency.
            speed: Speed.
            t: Time.

        Returns:
            Stretched PIL Image.
        """
        w, h = img.size
        scale_x = 1.0 + (amp / max(w, 1)) * np.sin(2.0 * np.pi * freq * t * speed)
        new_w = max(1, int(w * abs(scale_x)))
        stretched = img.resize((new_w, h), Image.BILINEAR)
        if new_w == w:
            return stretched
        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x_off = (w - new_w) // 2
        result.paste(stretched, (x_off, 0), stretched)
        return result

    def _warp_smear(
        self,
        arr: np.ndarray,
        amp: float,
        freq: float,
        speed: float,
        t: float,
    ) -> np.ndarray:
        """Create a smear by blending original with shifted copy.

        Args:
            arr: RGBA pixel array.
            amp: Smear displacement.
            freq: Frequency.
            speed: Speed.
            t: Time.

        Returns:
            Smeared RGBA array.
        """
        phase = 2.0 * np.pi * freq * t * speed
        shift_x = int(amp * np.sin(phase))
        shifted = np.roll(arr, shift_x, axis=1)
        # Blend with 30% shifted copy
        result = arr.astype(np.float32) * 0.7 + shifted.astype(np.float32) * 0.3
        return result.astype(np.uint8)

    def _render_echo(
        self,
        canvas: Image.Image,
        text_img: Image.Image,
        count: int,
        amp_x: float,
        amp_y: float,
        t: float,
        px: int,
        py: int,
    ) -> None:
        """Render echo/trail copies with decreasing alpha.

        Args:
            canvas: Destination canvas.
            text_img: Source text image.
            count: Number of echo copies.
            amp_x: Horizontal offset per echo step.
            amp_y: Vertical offset per echo step.
            t: Time.
            px: Base x position.
            py: Base y position.
        """
        for k in range(count, -1, -1):
            alpha = (1.0 - k / (count + 1)) * 0.8
            off_x = int(amp_x * k * np.sin(t * 2.0))
            off_y = int(amp_y * k * np.cos(t * 2.0))
            echo = self._apply_alpha_mult(text_img, alpha)
            self._paste_text(canvas, echo, px + off_x, py + off_y)
