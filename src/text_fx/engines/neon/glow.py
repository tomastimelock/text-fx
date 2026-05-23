# Filepath: text_fx/engines/neon/glow.py
# Condensed Description: Glow/pulse/aura/fire/electric/shadow neon engine
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: GlowEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: GlowEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

from text_fx.easing.curves import get_easing
from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.renderer import _parse_color, resolve_position

logger = logging.getLogger(__name__)


class GlowEngine(Engine):
    """Engine for glow, pulse, aura, fire, electric, and shadow effects.

    Modes:
        glow: constant neon glow halo
        pulse: pulsing glow
        aura: soft aura halo
        fire: warm upward-rising glow
        electric: electric/arc outline
        lightning: jagged lightning glow
        hologram: hologram scan-line glow
        projected: spotlight projection effect
        shadow: drop shadow + glow
        strobe: strobe flash
        flash: single flash

    Params:
        color: CSS hex color for the glow
        blur_radius: int — glow blur radius
        intensity: float — glow brightness
        flicker: bool — add random flicker
        mode: see above
    """

    name = "glow"
    bases = ("glow",)

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
        """Render glow animation.

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
        glow_color_str = params.get("color", "#FF00FF")
        blur_radius = int(params.get("blur_radius", 24)) * config.intensity
        glow_intensity = float(params.get("intensity", 1.5)) * config.intensity
        flicker = bool(params.get("flicker", False))
        mode = params.get("mode", "glow")
        pulse = bool(params.get("pulse", mode == "pulse"))

        glow_color = _parse_color(glow_color_str)
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

        # Expand canvas for glow bleed
        margin = int(blur_radius) + 20
        layer_w = tw + margin * 2
        layer_h = th + margin * 2

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                canvas = self._make_canvas(canvas_size)

                # Glow intensity modulation
                if mode == "strobe":
                    glow_mult = 1.0 if (i % max(1, int(fps / 4))) < int(fps / 8) else 0.1
                elif mode == "flash":
                    glow_mult = max(0.0, 1.0 - t * 2.0)
                elif pulse:
                    glow_mult = 0.5 + 0.5 * np.sin(2.0 * np.pi * t * 2.0)
                elif flicker:
                    glow_mult = float(rng.choice([0.6, 0.8, 1.0, 1.0, 1.2]))
                else:
                    glow_mult = float(np.clip(eased[i], 0.0, 1.0))

                current_intensity = glow_intensity * glow_mult

                # Build glow layer
                glow_layer = self._build_glow(
                    text_image,
                    glow_color,
                    int(blur_radius),
                    current_intensity,
                    mode,
                    t,
                    layer_w,
                    layer_h,
                    margin,
                    rng,
                )

                # Composite: glow under text
                full_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
                gx = px - margin
                gy = py - margin
                full_layer.paste(glow_layer, (gx, gy), glow_layer)

                # Main text on top
                text_with_alpha = self._apply_alpha_mult(
                    text_image, float(np.clip(eased[i], 0.0, 1.0))
                )
                full_layer.paste(text_with_alpha, (px, py), text_with_alpha)

                canvas = Image.alpha_composite(canvas, full_layer)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _build_glow(
        self,
        text_img: Image.Image,
        glow_color: tuple,
        blur_r: int,
        intensity: float,
        mode: str,
        t: float,
        layer_w: int,
        layer_h: int,
        margin: int,
        rng: np.random.Generator,
    ) -> Image.Image:
        """Build the glow halo layer.

        Args:
            text_img: Source text RGBA image.
            glow_color: RGBA glow color tuple.
            blur_r: Blur radius.
            intensity: Brightness multiplier.
            mode: Glow mode.
            t: Time.
            layer_w: Layer width.
            layer_h: Layer height.
            margin: Margin around text.
            rng: RNG.

        Returns:
            RGBA glow layer image.
        """
        tw, th = text_img.size
        glow_base = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))

        # Colorize the text image for the glow
        r_ch, g_ch, b_ch, a_ch = text_img.split()
        a_arr = np.array(a_ch, dtype=np.float32)
        glow_r = int(glow_color[0])
        glow_g = int(glow_color[1])
        glow_b = int(glow_color[2])

        glow_r_ch = Image.fromarray(
            np.clip(a_arr * glow_r / 255.0 * intensity, 0, 255).astype(np.uint8), "L"
        )
        glow_g_ch = Image.fromarray(
            np.clip(a_arr * glow_g / 255.0 * intensity, 0, 255).astype(np.uint8), "L"
        )
        glow_b_ch = Image.fromarray(
            np.clip(a_arr * glow_b / 255.0 * intensity, 0, 255).astype(np.uint8), "L"
        )
        glow_a_ch = Image.fromarray(
            np.clip(a_arr * min(255.0, intensity * 180), 0, 255).astype(np.uint8), "L"
        )

        colored_glow = Image.merge("RGBA", (glow_r_ch, glow_g_ch, glow_b_ch, glow_a_ch))
        glow_base.paste(colored_glow, (margin, margin), colored_glow)

        # Blur for the halo effect
        effective_blur = max(1, blur_r)
        if mode in ("fire",):
            # Asymmetric blur: more upward
            for _ in range(3):
                glow_base = glow_base.filter(ImageFilter.GaussianBlur(radius=effective_blur // 2))
                arr = np.array(glow_base, dtype=np.float32)
                arr = np.roll(arr, -2, axis=0)  # Shift up
                glow_base = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
        elif mode in ("shadow",):
            effective_blur = blur_r // 2
            glow_base = glow_base.filter(ImageFilter.GaussianBlur(radius=effective_blur))
            # Shift down-right for shadow
            arr = np.array(glow_base, dtype=np.float32)
            arr = np.roll(arr, 8, axis=0)
            arr = np.roll(arr, 8, axis=1)
            glow_base = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
        elif mode in ("hologram",):
            glow_base = glow_base.filter(ImageFilter.GaussianBlur(radius=effective_blur // 3))
            # Add scanline effect
            arr = np.array(glow_base, dtype=np.float32)
            for y in range(0, layer_h, 4):
                arr[y, :, 3] *= 0.3
            glow_base = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
        else:
            glow_base = glow_base.filter(ImageFilter.GaussianBlur(radius=effective_blur))

        return glow_base
