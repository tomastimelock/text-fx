# Filepath: text_fx/engines/mask/linear_wipe.py
# Condensed Description: Linear mask wipe engine for directional text reveals
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: LinearWipeEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: LinearWipeEngine
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


class LinearWipeEngine(Engine):
    """Engine for straight-line mask reveal effects.

    Reveals text through a moving linear mask edge.

    Params:
        direction: 'left_to_right' | 'right_to_left' | 'top_to_bottom' |
                   'bottom_to_top' | 'split' | 'center_out' | 'diagonal'
        feather_px: int — soft edge feather width in pixels
    """

    name = "linear_wipe"
    bases = ("linear_wipe",)

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
        """Render linear wipe animation.

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
        direction = params.get("direction", "left_to_right")
        feather_px = int(params.get("feather_px", 8))

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
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                # Build alpha mask for the text image
                mask = self._build_mask(tw, th, direction, progress, feather_px)

                # Apply mask to text image
                masked_text = text_image.copy()
                r, g, b, a = masked_text.split()
                # Combine existing alpha with wipe mask
                a_arr = (
                    np.frombuffer(a.tobytes(), dtype=np.uint8).reshape(th, tw).astype(np.float32)
                )
                mask_arr = np.array(mask, dtype=np.float32) / 255.0
                combined_a = (a_arr * mask_arr).clip(0, 255).astype(np.uint8)
                from PIL import Image as PILImage

                new_a = PILImage.fromarray(combined_a, mode="L")
                masked_text.putalpha(new_a)

                self._paste_text(canvas, masked_text, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _build_mask(
        self,
        w: int,
        h: int,
        direction: str,
        progress: float,
        feather_px: int,
    ) -> Image.Image:
        """Build an L-mode alpha mask image representing the wipe at given progress.

        Args:
            w: Mask width.
            h: Mask height.
            direction: Wipe direction string.
            progress: 0.0 = fully hidden, 1.0 = fully revealed.
            feather_px: Soft edge width in pixels.

        Returns:
            Grayscale (L mode) mask image.
        """
        mask = np.zeros((h, w), dtype=np.float32)
        feather = max(1, feather_px)

        if direction == "left_to_right":
            edge = int(w * progress)
            for x in range(w):
                dist = edge - x
                val = np.clip(dist / feather + 0.5, 0.0, 1.0)
                mask[:, x] = val * 255.0

        elif direction == "right_to_left":
            edge = int(w * (1.0 - progress))
            for x in range(w):
                dist = x - edge
                val = np.clip(dist / feather + 0.5, 0.0, 1.0)
                mask[:, x] = val * 255.0

        elif direction == "top_to_bottom":
            edge = int(h * progress)
            for y in range(h):
                dist = edge - y
                val = np.clip(dist / feather + 0.5, 0.0, 1.0)
                mask[y, :] = val * 255.0

        elif direction == "bottom_to_top":
            edge = int(h * (1.0 - progress))
            for y in range(h):
                dist = y - edge
                val = np.clip(dist / feather + 0.5, 0.0, 1.0)
                mask[y, :] = val * 255.0

        elif direction == "split":
            # Both left and right wipe toward center
            cx = w // 2
            half_visible = int(cx * progress)
            for x in range(w):
                dist = half_visible - (cx - x) if x < cx else half_visible - (x - cx)
                val = np.clip(dist / feather + 0.5, 0.0, 1.0)
                mask[:, x] = val * 255.0

        elif direction == "center_out":
            cx, cy = w // 2, h // 2
            max_r = np.sqrt(cx**2 + cy**2)
            r_edge = max_r * progress
            xs, ys = np.meshgrid(np.arange(w), np.arange(h))
            dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
            val = np.clip((r_edge - dist) / feather + 0.5, 0.0, 1.0)
            mask = val * 255.0

        elif direction == "diagonal":
            # Diagonal wipe from top-left to bottom-right
            xs, ys = np.meshgrid(np.arange(w), np.arange(h))
            diag = (xs / w + ys / h) / 2.0
            edge = progress
            val = np.clip((edge - diag) / (feather / max(w, h)) + 0.5, 0.0, 1.0)
            mask = val * 255.0

        else:
            # Default left-to-right
            edge = int(w * progress)
            mask[:, :edge] = 255.0

        from PIL import Image as PILImage

        return PILImage.fromarray(mask.clip(0, 255).astype(np.uint8), mode="L")
