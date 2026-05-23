# Filepath: text_fx/engines/mask/shaped.py
# Condensed Description: Structured multi-shape mask engine for blinds, shutter, box, frame, glitch-slice reveals
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: ShapedEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: ShapedEngine
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


class ShapedEngine(Engine):
    """Engine for structured multi-shape mask reveals.

    Shapes:
        circle: expanding circle
        box: expanding rectangle from center
        frame: border-inward reveal
        venetian / horizontal_strips: horizontal strip blinds
        vertical_blinds / vertical_strips: vertical strip blinds
        shutter / panels: multi-panel reveal
        glitch_slices: random-offset slice reveal

    Params:
        shape: shape name string
        count: int — number of strips/panels (default 8)
        stagger_s: float — stagger between strips
    """

    name = "shaped"
    bases = ("shaped",)

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
        """Render shaped mask animation.

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
        shape = params.get("shape", "box")
        count = int(params.get("count", 8))

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
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)
                mask_arr = self._build_shape_mask(tw, th, shape, count, progress, easing_fn, rng)

                masked_text = text_image.copy()
                r, g, b, a = masked_text.split()
                a_arr = (
                    np.frombuffer(a.tobytes(), dtype=np.uint8).reshape(th, tw).astype(np.float32)
                )
                combined = (a_arr * mask_arr / 255.0).clip(0, 255).astype(np.uint8)
                new_a = Image.fromarray(combined, mode="L")
                masked_text.putalpha(new_a)

                self._paste_text(canvas, masked_text, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _build_shape_mask(
        self,
        w: int,
        h: int,
        shape: str,
        count: int,
        progress: float,
        easing_fn: Any,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Build a float32 [0..255] mask array for the given shape and progress.

        Args:
            w: Mask width.
            h: Mask height.
            shape: Shape identifier.
            count: Number of strips/panels.
            progress: 0.0–1.0 overall animation progress.
            easing_fn: Easing function.
            rng: Random number generator.

        Returns:
            Float32 ndarray of shape (h, w) with values in [0, 255].
        """
        mask = np.zeros((h, w), dtype=np.float32)

        if shape in ("circle",):
            cx, cy = w // 2, h // 2
            max_r = np.sqrt(cx**2 + cy**2)
            r_edge = max_r * progress
            xs, ys = np.meshgrid(np.arange(w), np.arange(h))
            dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
            mask = np.clip(r_edge - dist + 4, 0, 1) * 255.0

        elif shape in ("box",):
            cx, cy = w // 2, h // 2
            half_w = int(cx * progress)
            half_h = int(cy * progress)
            x0 = max(0, cx - half_w)
            x1 = min(w, cx + half_w)
            y0 = max(0, cy - half_h)
            y1 = min(h, cy + half_h)
            mask[y0:y1, x0:x1] = 255.0

        elif shape in ("frame",):
            # Reveal from border inward
            border = int(min(w, h) * 0.5 * progress)
            mask[:, :] = 0.0
            if border > 0:
                mask[:border, :] = 255.0
                mask[-border:, :] = 255.0
                mask[:, :border] = 255.0
                mask[:, -border:] = 255.0

        elif shape in ("venetian", "horizontal_strips"):
            strip_h = max(1, h // count)
            for k in range(count):
                # Each strip appears staggered
                strip_progress = np.clip((progress * count) - k, 0.0, 1.0)
                reveal_px = int(strip_h * strip_progress)
                y0 = k * strip_h
                y1 = min(h, y0 + strip_h)
                mask[y0 : y0 + reveal_px, :] = 255.0

        elif shape in ("vertical_blinds", "vertical_strips"):
            strip_w = max(1, w // count)
            for k in range(count):
                strip_progress = np.clip((progress * count) - k, 0.0, 1.0)
                reveal_px = int(strip_w * strip_progress)
                x0 = k * strip_w
                mask[:, x0 : x0 + reveal_px] = 255.0

        elif shape in ("shutter", "panels"):
            panel_w = max(1, w // count)
            for k in range(count):
                panel_progress = np.clip((progress * count) - k, 0.0, 1.0)
                reveal_h = int(h * panel_progress)
                x0 = k * panel_w
                x1 = min(w, x0 + panel_w)
                mask[:reveal_h, x0:x1] = 255.0

        elif shape in ("glitch_slices",):
            n_slices = count
            slice_h = max(1, h // n_slices)
            offsets = rng.integers(-30, 31, n_slices)
            for k in range(n_slices):
                slice_progress = np.clip((progress * n_slices) - k, 0.0, 1.0)
                if slice_progress <= 0:
                    continue
                y0 = k * slice_h
                y1 = min(h, y0 + slice_h)
                off = int(offsets[k] * (1.0 - slice_progress))
                src_x0 = max(0, -off)
                src_x1 = min(w, w - off)
                dst_x0 = max(0, off)
                dst_x1 = min(w, w + off)
                reveal_w = min(src_x1 - src_x0, dst_x1 - dst_x0)
                if reveal_w > 0:
                    mask[y0:y1, dst_x0 : dst_x0 + reveal_w] = 255.0

        else:
            mask[:, : int(w * progress)] = 255.0

        return mask
