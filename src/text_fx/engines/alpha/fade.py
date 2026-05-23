# Filepath: text_fx/engines/alpha/fade.py
# Condensed Description: Alpha-fade engine handling in/out/cross/dip/blur variants
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: FadeEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: FadeEngine
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


class FadeEngine(Engine):
    """Engine for alpha-based fade effects.

    Handles directions: in, out, cross, hard, dip_black, dip_white,
    and blur variants (blur=True in params applies Gaussian blur).

    Params:
        direction: 'in' | 'out' | 'cross' | 'hard' | 'dip_black' | 'dip_white'
        blur: bool — if True, apply decreasing/increasing Gaussian blur
        blur_max_radius: Maximum blur radius in pixels (default 20)
    """

    name = "fade"
    bases = ("fade",)

    def is_available(self) -> bool:
        """Check availability — only requires Pillow and numpy.

        Returns:
            Always True since Pillow and numpy are required deps.
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
        """Render a fade animation to a WebM overlay.

        Args:
            text_image: Pre-rendered RGBA text image.
            params: Engine params; 'direction' and optionally 'blur'.
            config: TextEffectConfig.
            duration: Effect duration in seconds.
            fps: Output frame rate.
            canvas_size: (width, height) of the output canvas.
            output: Destination .webm path.

        Returns:
            Path to the written WebM.
        """
        direction = params.get("direction", "in")
        use_blur = bool(params.get("blur", False))
        blur_max = int(params.get("blur_max_radius", 20))

        easing_fn = get_easing(config.easing)
        frames = max(1, int(duration * fps))
        t_array = np.linspace(0.0, 1.0, frames)
        eased = easing_fn(t_array)

        # Build alpha curve
        if direction == "in":
            alpha_curve = eased
        elif direction == "out":
            alpha_curve = 1.0 - eased
        elif direction == "cross":
            # Fade in first half, fade out second half (cross dissolve)
            alpha_curve = np.where(t_array < 0.5, eased * 2.0, 2.0 - eased * 2.0)
            alpha_curve = np.clip(alpha_curve, 0.0, 1.0)
        elif direction == "hard":
            # Hard cut: instant appearance at frame 0
            alpha_curve = np.ones(frames)
        elif direction == "dip_black":
            # Fade in through black: alpha ramps up, black overlay fades
            alpha_curve = eased
        elif direction == "dip_white":
            # Fade in through white: alpha ramps up
            alpha_curve = eased
        else:
            alpha_curve = eased

        # Position the text on canvas
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
                canvas = self._make_canvas(canvas_size)
                alpha_mult = float(np.clip(alpha_curve[i], 0.0, 1.0))

                # Blur variant
                current_text = text_image.copy()
                if use_blur:
                    if direction in ("in", "dip_black", "dip_white"):
                        # Start blurry, end sharp
                        blur_radius = blur_max * (1.0 - alpha_mult)
                    else:
                        # Start sharp, end blurry
                        blur_radius = blur_max * alpha_mult
                    if blur_radius > 0.5:
                        current_text = current_text.filter(
                            ImageFilter.GaussianBlur(radius=blur_radius)
                        )

                # Apply dip overlays
                if direction == "dip_black":
                    # Draw black layer under text during dip
                    dip_alpha = int(255 * max(0.0, 1.0 - alpha_mult * 2))
                    if dip_alpha > 0:
                        overlay = Image.new("RGBA", canvas_size, (0, 0, 0, dip_alpha))
                        canvas = Image.alpha_composite(canvas, overlay)

                elif direction == "dip_white":
                    dip_alpha = int(255 * max(0.0, 1.0 - alpha_mult * 2))
                    if dip_alpha > 0:
                        overlay = Image.new("RGBA", canvas_size, (255, 255, 255, dip_alpha))
                        canvas = Image.alpha_composite(canvas, overlay)

                faded = self._apply_alpha_mult(current_text, alpha_mult)
                self._paste_text(canvas, faded, px, py)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
