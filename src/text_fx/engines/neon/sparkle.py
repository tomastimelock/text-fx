# Filepath: text_fx/engines/neon/sparkle.py
# Condensed Description: Sparkle/particle-light engine for lens dust and star sparkle effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: SparkleEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: SparkleEngine
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


class SparkleEngine(Engine):
    """Engine for sparkle and lens-dust light particle effects.

    Modes:
        dust: soft lens dust/bokeh sparkles
        star: crisp multi-point star sparkles
        electric: electric arc sparkles
        lightning: lightning bolt sparkles

    Params:
        count: int — number of sparkle particles
        size_range: list[int] — [min, max] sparkle size in pixels
        twinkle_hz: float — twinkle/blink frequency in Hz
        star_points: int — number of points for star mode
        mode: see above
        seed: int
    """

    name = "sparkle"
    bases = ("sparkle",)

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
        """Render sparkle animation.

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
        count = int(params.get("count", 30))
        size_range = params.get("size_range", [4, 20])
        twinkle_hz = float(params.get("twinkle_hz", 3.0))
        star_points = int(params.get("star_points", 4))
        mode = params.get("mode", "dust")

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

        # Pre-generate sparkle positions (slightly outside text bounds)
        margin_sparkle = 40
        sparkles = []
        for _ in range(count):
            sx = rng.uniform(-margin_sparkle, tw + margin_sparkle)
            sy = rng.uniform(-margin_sparkle, th + margin_sparkle)
            sz = rng.integers(size_range[0], size_range[-1] + 1)
            phase = rng.uniform(0, 2 * np.pi)
            sparkles.append(
                {
                    "x": sx,
                    "y": sy,
                    "size": sz,
                    "phase": phase,
                    "drift_x": rng.uniform(-5, 5),
                    "drift_y": rng.uniform(-8, -2),
                }
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                # Draw base text
                text_alpha = self._apply_alpha_mult(text_image, progress)
                self._paste_text(canvas, text_alpha, px, py)

                # Draw sparkles on top
                sparkle_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
                for sp in sparkles:
                    twinkle = 0.5 + 0.5 * np.sin(twinkle_hz * 2 * np.pi * t + sp["phase"])
                    if twinkle < 0.1:
                        continue
                    sx = px + sp["x"] + sp["drift_x"] * t
                    sy = py + sp["y"] + sp["drift_y"] * t
                    sz = sp["size"] * twinkle * progress
                    alpha = int(200 * twinkle * progress)

                    if mode == "dust":
                        self._draw_dust(sparkle_layer, sx, sy, sz, alpha)
                    elif mode in ("star", "electric", "lightning"):
                        self._draw_star(sparkle_layer, sx, sy, sz, alpha, star_points)

                canvas = Image.alpha_composite(canvas, sparkle_layer)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _draw_dust(
        self,
        layer: Image.Image,
        x: float,
        y: float,
        size: float,
        alpha: int,
    ) -> None:
        """Draw a soft lens-dust bokeh circle.

        Args:
            layer: RGBA layer to draw on.
            x: Center x.
            y: Center y.
            size: Radius.
            alpha: Alpha value 0-255.
        """
        if size < 0.5:
            return
        draw = ImageDraw.Draw(layer)
        r = max(1, int(size))
        # Multiple concentric circles with decreasing alpha
        for k in range(r, 0, -1):
            ring_alpha = int(alpha * (k / r) * 0.5)
            if ring_alpha < 2:
                continue
            x0, y0 = int(x) - k, int(y) - k
            x1, y1 = int(x) + k, int(y) + k
            draw.ellipse([(x0, y0), (x1, y1)], fill=(255, 255, 240, ring_alpha))

    def _draw_star(
        self,
        layer: Image.Image,
        x: float,
        y: float,
        size: float,
        alpha: int,
        points: int,
    ) -> None:
        """Draw a multi-pointed star shape.

        Args:
            layer: RGBA layer to draw on.
            x: Center x.
            y: Center y.
            size: Outer radius.
            alpha: Alpha value 0-255.
            points: Number of star points.
        """
        if size < 0.5:
            return
        draw = ImageDraw.Draw(layer)
        r_outer = max(1.0, size)
        r_inner = max(0.5, size * 0.3)
        coords = []
        for k in range(points * 2):
            angle = k * np.pi / points - np.pi / 2
            r = r_outer if k % 2 == 0 else r_inner
            px_ = x + r * np.cos(angle)
            py_ = y + r * np.sin(angle)
            coords.append((int(px_), int(py_)))
        if len(coords) >= 3:
            draw.polygon(coords, fill=(255, 255, 200, alpha))
        # Cross arms for extra sparkle
        arm_len = r_outer * 1.5
        draw.line(
            [(int(x - arm_len), int(y)), (int(x + arm_len), int(y))],
            fill=(255, 255, 255, alpha // 2),
            width=1,
        )
        draw.line(
            [(int(x), int(y - arm_len)), (int(x), int(y + arm_len))],
            fill=(255, 255, 255, alpha // 2),
            width=1,
        )
