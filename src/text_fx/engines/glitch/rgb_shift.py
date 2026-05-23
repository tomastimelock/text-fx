# Filepath: text_fx/engines/glitch/rgb_shift.py
# Condensed Description: RGB channel separation engine for chromatic aberration and split effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: RgbShiftEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: RgbShiftEngine
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


class RgbShiftEngine(Engine):
    """Engine for RGB channel separation (chromatic aberration) effects.

    Shifts R, G, B channels independently to create a color-split glitch look.

    Params:
        offset: int — max pixel offset for channel separation
        r_offset: int — explicit R channel offset (overrides offset)
        g_offset: int — explicit G channel offset
        b_offset: int — explicit B channel offset
        animate: bool — animate offset over time (pulses in/out)
        flicker: bool — random per-frame flicker
        glow: bool — add a soft glow to the shifted channels
        mode: 'shift' | 'flash' — flash = rapid on/off shifts
    """

    name = "rgb_shift"
    bases = ("rgb_shift",)

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
        """Render RGB shift animation.

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
        base_offset = int(params.get("offset", 10)) * config.intensity
        animate = bool(params.get("animate", True))
        flicker = bool(params.get("flicker", False))
        add_glow = bool(params.get("glow", False))
        mode = params.get("mode", "shift")

        frames = max(1, int(duration * fps))
        t_array = np.linspace(0.0, 1.0, frames)

        tw, th = text_image.size
        px, py = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        rng = np.random.default_rng(config.seed)

        # Pre-split channels
        r_ch, g_ch, b_ch, a_ch = text_image.split()
        r_arr = np.array(r_ch, dtype=np.float32)
        g_arr = np.array(g_ch, dtype=np.float32)
        b_arr = np.array(b_ch, dtype=np.float32)
        a_arr = np.array(a_ch, dtype=np.float32)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = t_array[i]
                canvas = self._make_canvas(canvas_size)

                if mode == "flash":
                    # Rapid on/off: shift only on even frames
                    active = (i % 3) != 0
                    current_offset = float(base_offset) if active else 0.0
                elif animate:
                    # Oscillate offset with a sine wave
                    current_offset = float(base_offset * (0.5 + 0.5 * np.sin(t * np.pi * 4)))
                else:
                    current_offset = float(base_offset)

                if flicker:
                    current_offset *= float(rng.choice([0.0, 0.5, 1.0, 1.5]))

                co = int(current_offset)

                # Shift channels: R right, B left (classic chromatic aberration)
                r_shifted = np.roll(r_arr, co, axis=1)
                b_shifted = np.roll(b_arr, -co, axis=1)

                # Recombine
                out_r = r_shifted.clip(0, 255).astype(np.uint8)
                out_g = g_arr.clip(0, 255).astype(np.uint8)
                out_b = b_shifted.clip(0, 255).astype(np.uint8)
                out_a = a_arr.clip(0, 255).astype(np.uint8)

                # For glow, brighten areas where channels diverge
                if add_glow and co > 0:
                    diverge = (np.abs(r_shifted - b_shifted) / 255.0 * 0.5).clip(0, 1)
                    glow_val = (diverge * 80).astype(np.uint8)
                    out_r = np.clip(out_r.astype(np.int32) + glow_val, 0, 255).astype(np.uint8)
                    out_g = np.clip(out_g.astype(np.int32) + glow_val // 2, 0, 255).astype(np.uint8)
                    out_b = np.clip(out_b.astype(np.int32) + glow_val, 0, 255).astype(np.uint8)

                shifted_img = Image.merge(
                    "RGBA",
                    (
                        Image.fromarray(out_r, "L"),
                        Image.fromarray(out_g, "L"),
                        Image.fromarray(out_b, "L"),
                        Image.fromarray(out_a, "L"),
                    ),
                )

                self._paste_text(canvas, shifted_img, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
