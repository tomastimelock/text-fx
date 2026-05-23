# Filepath: text_fx/engines/mask/organic.py
# Condensed Description: Noise/texture-driven organic mask engine for ink, smoke, brush, scratch reveals
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: OrganicEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: OrganicEngine
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
from text_fx.typography.renderer import resolve_position

logger = logging.getLogger(__name__)


class OrganicEngine(Engine):
    """Engine for noise/texture-driven organic mask reveals.

    Modes:
        ink: flowing ink-style threshold noise
        smoke: blurry drifting smoke-style reveal
        brush: horizontal brushstroke-style reveal
        scratch: jagged scratch-style wipe
        venetian: horizontal strip blinds
        vertical_blinds: vertical strips
        shutter: panel wipe
        glitch: random glitch slice mask

    Params:
        mode: see above
        noise_scale: float — noise feature scale
        blur_px: int — blur applied to noise before thresholding
    """

    name = "organic"
    bases = ("organic",)

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
        """Render organic mask animation.

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
        mode = params.get("mode", "ink")
        blur_px = int(params.get("blur_px", 6))

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
        # Pre-generate a noise field — same across all frames, threshold moves
        noise_field = self._generate_noise(tw, th, mode, rng, blur_px)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                # Threshold moves from 1.0 (all hidden) to 0.0 (all visible)
                threshold = 1.0 - progress
                mask_arr = np.clip(
                    (noise_field - threshold) / max(0.05, 1.0 - threshold + 0.001), 0.0, 1.0
                )
                masked_text = text_image.copy()
                r, g, b, a = masked_text.split()
                a_arr = (
                    np.frombuffer(a.tobytes(), dtype=np.uint8).reshape(th, tw).astype(np.float32)
                )
                combined = (a_arr * mask_arr).clip(0, 255).astype(np.uint8)
                new_a = Image.fromarray(combined, mode="L")
                masked_text.putalpha(new_a)

                self._paste_text(canvas, masked_text, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _generate_noise(
        self,
        w: int,
        h: int,
        mode: str,
        rng: np.random.Generator,
        blur_px: int,
    ) -> np.ndarray:
        """Generate a static noise field [0..1] for the given mode.

        Args:
            w: Field width.
            h: Field height.
            mode: Noise mode affecting the noise characteristics.
            rng: Random number generator.
            blur_px: Blur radius for smoothing.

        Returns:
            Float32 ndarray of shape (h, w) with values in [0, 1].
        """
        if mode in ("ink", "smoke"):
            # Multi-octave noise for organic look
            noise = np.zeros((h, w), dtype=np.float32)
            amplitude = 1.0
            scale = 1
            total_amp = 0.0
            for _ in range(4):
                nh = max(1, h // scale)
                nw = max(1, w // scale)
                octave = rng.random((nh, nw)).astype(np.float32)
                oct_img = Image.fromarray((octave * 255).astype(np.uint8), mode="L")
                oct_img = oct_img.resize((w, h), Image.BILINEAR)
                noise += amplitude * np.array(oct_img, dtype=np.float32) / 255.0
                total_amp += amplitude
                amplitude *= 0.5
                scale *= 2
            noise /= total_amp

            # Blur for softness
            if blur_px > 0:
                noise_img = Image.fromarray((noise * 255).astype(np.uint8), mode="L")
                noise_img = noise_img.filter(ImageFilter.GaussianBlur(radius=blur_px))
                noise = np.array(noise_img, dtype=np.float32) / 255.0

        elif mode in ("brush",):
            # Gradient with horizontal noise for brush stroke look
            noise = np.zeros((h, w), dtype=np.float32)
            for y in range(h):
                row_noise = rng.random(w).astype(np.float32) * 0.3
                gradient = np.linspace(0.1, 0.9, w)
                noise[y] = gradient + row_noise * (y / h)
            noise = np.clip(noise, 0.0, 1.0)

            if blur_px > 0:
                noise_img = Image.fromarray((noise * 255).astype(np.uint8), mode="L")
                noise_img = noise_img.filter(ImageFilter.GaussianBlur(radius=blur_px // 2))
                noise = np.array(noise_img, dtype=np.float32) / 255.0

        elif mode in ("scratch",):
            # Jagged diagonal scratches
            noise = np.zeros((h, w), dtype=np.float32)
            for y in range(h):
                jag = rng.integers(-3, 4)
                t = (y + jag) / h
                noise[y, :] = t + rng.random(w) * 0.05

        elif mode in ("venetian", "vertical_blinds", "shutter", "glitch"):
            # For these modes use simple noise
            noise = rng.random((h, w)).astype(np.float32)
        else:
            noise = rng.random((h, w)).astype(np.float32)

        # Normalize to [0, 1]
        mn, mx = noise.min(), noise.max()
        if mx > mn:
            noise = (noise - mn) / (mx - mn)

        return noise
