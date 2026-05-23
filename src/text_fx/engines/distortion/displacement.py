# Filepath: text_fx/engines/distortion/displacement.py
# Condensed Description: Displacement map engine for broken_glass and paper_tear effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: DisplacementEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: DisplacementEngine
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


class DisplacementEngine(Engine):
    """Engine for displacement-map warping effects.

    Modes:
        shatter: broken-glass polygon shard displacement
        tear: paper tear with jagged horizontal cuts

    Params:
        mode: 'shatter' | 'tear' | 'stretch' | 'smear'
        shard_count: int — number of shards for shatter mode
        velocity_scale: float — outward velocity for shards
        seed: int — random seed
    """

    name = "displacement"
    bases = ("displacement",)

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
        """Render displacement animation.

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
        mode = params.get("mode", "shatter")
        shard_count = int(params.get("shard_count", 12))
        velocity_scale = float(params.get("velocity_scale", 1.0)) * config.intensity

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

        rng = np.random.default_rng(config.seed if config.seed is not None else 42)

        # Pre-generate shard geometry
        if mode == "shatter":
            shards = self._generate_shards(tw, th, shard_count, rng)
        elif mode == "tear":
            shards = self._generate_tear_strips(tw, th, shard_count, rng)
        elif mode in ("stretch", "smear"):
            shards = []
        else:
            shards = self._generate_shards(tw, th, shard_count, rng)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                if mode == "shatter":
                    result = self._apply_shatter(
                        text_image, shards, progress, velocity_scale, canvas_size, px, py
                    )
                    canvas = result
                elif mode == "tear":
                    result = self._apply_tear(
                        text_image, shards, progress, velocity_scale, canvas_size, px, py
                    )
                    canvas = result
                elif mode == "stretch":
                    warped = self._apply_stretch_displacement(text_image, progress, velocity_scale)
                    self._paste_text(canvas, warped, px, py)
                elif mode == "smear":
                    warped = self._apply_smear_displacement(text_image, progress, velocity_scale)
                    self._paste_text(canvas, warped, px, py)
                else:
                    self._paste_text(canvas, text_image.copy(), px, py)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _generate_shards(
        self,
        w: int,
        h: int,
        count: int,
        rng: np.random.Generator,
    ) -> list[dict]:
        """Generate random polygon shards covering the image.

        Args:
            w: Image width.
            h: Image height.
            count: Approximate number of shards.
            rng: RNG.

        Returns:
            List of shard dicts with 'bbox' and 'velocity' keys.
        """
        shards = []
        grid_n = max(2, int(np.sqrt(count)))
        cell_w = w // grid_n
        cell_h = h // grid_n
        cx = w // 2
        cy = h // 2
        for gi in range(grid_n):
            for gj in range(grid_n):
                x0 = gi * cell_w
                y0 = gj * cell_h
                x1 = min(w, x0 + cell_w)
                y1 = min(h, y0 + cell_h)
                # Velocity: outward from center
                shard_cx = (x0 + x1) // 2
                shard_cy = (y0 + y1) // 2
                vel_x = (shard_cx - cx) / max(w // 2, 1) + rng.uniform(-0.1, 0.1)
                vel_y = (shard_cy - cy) / max(h // 2, 1) + rng.uniform(-0.1, 0.1)
                shards.append(
                    {
                        "bbox": (x0, y0, x1, y1),
                        "velocity": (vel_x, vel_y),
                        "rotation": rng.uniform(-30, 30),
                    }
                )
        return shards

    def _generate_tear_strips(
        self,
        w: int,
        h: int,
        count: int,
        rng: np.random.Generator,
    ) -> list[dict]:
        """Generate horizontal tear strips.

        Args:
            w: Image width.
            h: Image height.
            count: Number of strips.
            rng: RNG.

        Returns:
            List of strip dicts.
        """
        strips = []
        strip_h = h // max(count, 1)
        for k in range(count):
            y0 = k * strip_h
            y1 = min(h, y0 + strip_h)
            vel_x = rng.uniform(-1.0, 1.0)
            vel_y = rng.uniform(-0.2, 0.2) * (1 if k % 2 == 0 else -1)
            strips.append(
                {
                    "bbox": (0, y0, w, y1),
                    "velocity": (vel_x, vel_y),
                    "rotation": 0.0,
                }
            )
        return strips

    def _apply_shatter(
        self,
        text_img: Image.Image,
        shards: list[dict],
        progress: float,
        vel_scale: float,
        canvas_size: tuple[int, int],
        px: int,
        py: int,
    ) -> Image.Image:
        """Composite shards onto canvas with outward displacement.

        Args:
            text_img: Source text image.
            shards: List of shard dicts.
            progress: Animation progress 0-1.
            vel_scale: Velocity multiplier.
            canvas_size: Canvas size.
            px: Text x offset.
            py: Text y offset.

        Returns:
            Composited canvas image.
        """
        canvas = self._make_canvas(canvas_size)
        tw, th = text_img.size
        for shard in shards:
            x0, y0, x1, y1 = shard["bbox"]
            if x1 <= x0 or y1 <= y0:
                continue
            piece = text_img.crop((x0, y0, x1, y1))
            vx, vy = shard["velocity"]
            disp_x = int(vx * tw * vel_scale * progress * 2)
            disp_y = int(vy * th * vel_scale * progress * 2)
            alpha_mult = max(0.0, 1.0 - progress * 1.5)
            piece = self._apply_alpha_mult(piece, alpha_mult)
            dest_x = px + x0 + disp_x
            dest_y = py + y0 + disp_y
            self._paste_text(canvas, piece, dest_x, dest_y)
        return canvas

    def _apply_tear(
        self,
        text_img: Image.Image,
        strips: list[dict],
        progress: float,
        vel_scale: float,
        canvas_size: tuple[int, int],
        px: int,
        py: int,
    ) -> Image.Image:
        """Composite tear strips onto canvas.

        Args:
            text_img: Source text image.
            strips: List of strip dicts.
            progress: Animation progress.
            vel_scale: Velocity scale.
            canvas_size: Canvas size.
            px: Text x offset.
            py: Text y offset.

        Returns:
            Composited canvas image.
        """
        canvas = self._make_canvas(canvas_size)
        tw, th = text_img.size
        for strip in strips:
            x0, y0, x1, y1 = strip["bbox"]
            piece = text_img.crop((x0, y0, x1, y1))
            vx, vy = strip["velocity"]
            disp_x = int(vx * tw * 0.3 * vel_scale * progress)
            disp_y = int(vy * th * vel_scale * progress)
            alpha_mult = max(0.0, 1.0 - progress * 1.2)
            piece = self._apply_alpha_mult(piece, alpha_mult)
            self._paste_text(canvas, piece, px + x0 + disp_x, py + y0 + disp_y)
        return canvas

    def _apply_stretch_displacement(
        self, img: Image.Image, progress: float, vel_scale: float
    ) -> Image.Image:
        """Stretch the image horizontally over time.

        Args:
            img: Source image.
            progress: Animation progress.
            vel_scale: Stretch velocity.

        Returns:
            Stretched image.
        """
        w, h = img.size
        scale = 1.0 + progress * vel_scale * 0.5
        new_w = max(1, int(w * scale))
        stretched = img.resize((new_w, h), Image.BILINEAR)
        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x_off = (w - new_w) // 2
        result.paste(stretched, (x_off, 0), stretched)
        return self._apply_alpha_mult(result, max(0.0, 1.0 - progress * 0.8))

    def _apply_smear_displacement(
        self, img: Image.Image, progress: float, vel_scale: float
    ) -> Image.Image:
        """Smear text horizontally with decreasing alpha.

        Args:
            img: Source image.
            progress: Animation progress.
            vel_scale: Smear velocity.

        Returns:
            Smeared image.
        """
        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]
        result = arr.copy()
        smear_px = int(w * 0.15 * vel_scale * progress)
        for k in range(1, smear_px + 1):
            alpha = 0.3 * (1.0 - k / (smear_px + 1))
            shifted = np.roll(arr, k, axis=1)
            result = result * (1 - alpha) + shifted * alpha
        return self._apply_alpha_mult(
            Image.fromarray(result.clip(0, 255).astype(np.uint8), "RGBA"),
            max(0.0, 1.0 - progress * 0.7),
        )
