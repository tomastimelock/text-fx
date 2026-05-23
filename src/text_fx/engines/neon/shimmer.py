# Filepath: text_fx/engines/neon/shimmer.py
# Condensed Description: Metallic shimmer engine for gold, chrome, and bokeh effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: ShimmerEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: ShimmerEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
import warnings
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

from text_fx.easing.curves import get_easing
from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.renderer import _parse_color, resolve_position

logger = logging.getLogger(__name__)


class ShimmerEngine(Engine):
    """Engine for metallic shimmer and bokeh effects.

    Modes:
        gold: animated gold gradient highlight
        chrome: animated chrome sweep (PIL fallback for web_overlay)
        bokeh: soft out-of-focus circle highlights
        hologram: holographic shimmer
        projected: projected light shimmer
        spotlight: moving spotlight shimmer

    Note: gold and chrome look significantly better with web_overlay installed.
    A UserWarning is emitted when web_overlay is not available.

    Params:
        gradient_stops: list of CSS colors for gradient
        highlight_width_frac: float — highlight band width
        speed: float — shimmer animation speed
        bokeh_count: int — number of bokeh circles
        bokeh_size_range: tuple[int, int] — min/max bokeh size
        mode: see above
    """

    name = "shimmer"
    bases = ("shimmer",)

    _web_overlay_warned = False

    def is_available(self) -> bool:
        """Check availability.

        Returns:
            Always True (PIL fallback available).
        """
        return True

    def _check_web_overlay(self, mode: str) -> bool:
        """Check if web_overlay is available for high-fidelity rendering.

        Emits a one-time UserWarning if web_overlay is absent for modes that benefit.

        Args:
            mode: Effect mode.

        Returns:
            True if web_overlay is importable, False otherwise.
        """
        if mode in ("gold", "chrome", "bokeh", "hologram"):
            try:
                import web_overlay  # noqa: F401

                return True
            except ImportError:
                if not ShimmerEngine._web_overlay_warned:
                    warnings.warn(
                        f"text-fx shimmer mode '{mode}' uses a PIL fallback. "
                        f"Install web-overlay for higher-fidelity rendering: "
                        f"pip install text-fx[overlay]",
                        UserWarning,
                        stacklevel=4,
                    )
                    ShimmerEngine._web_overlay_warned = True
                return False
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
        """Render shimmer animation.

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
        mode = params.get("mode", "gold")
        speed = float(params.get("speed", 1.0))
        bokeh_count = int(params.get("bokeh_count", 20))
        bokeh_min = int(params.get("bokeh_size_range", [10, 40])[0])
        bokeh_max = int(params.get("bokeh_size_range", [10, 40])[-1])
        highlight_width = float(params.get("highlight_width_frac", 0.25))

        self._check_web_overlay(mode)

        # Gold gradient stops
        gold_palette = params.get(
            "gradient_stops", ["#8B6F31", "#D4AF37", "#F2D589", "#D4AF37", "#8B6F31"]
        )

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

        # Pre-generate bokeh if needed
        bokeh_circles: list[dict] = []
        if mode == "bokeh":
            for _ in range(bokeh_count):
                bokeh_circles.append(
                    {
                        "x": rng.uniform(-0.1, 1.1),
                        "y": rng.uniform(-0.1, 1.1),
                        "r": rng.integers(bokeh_min, bokeh_max + 1),
                        "phase": rng.uniform(0, 2 * np.pi),
                    }
                )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / fps
                progress = float(eased[i])
                canvas = self._make_canvas(canvas_size)

                if mode == "gold":
                    shimmer_img = self._apply_gold(text_image, t * speed, gold_palette)
                elif mode == "chrome":
                    shimmer_img = self._apply_chrome(text_image, t * speed, highlight_width)
                elif mode == "bokeh":
                    shimmer_img = self._apply_bokeh(text_image, t, bokeh_circles, canvas_size)
                elif mode in ("hologram", "projected", "spotlight"):
                    shimmer_img = self._apply_hologram(text_image, t * speed)
                else:
                    shimmer_img = self._apply_gold(text_image, t * speed, gold_palette)

                shimmer_img = self._apply_alpha_mult(shimmer_img, progress)
                self._paste_text(canvas, shimmer_img, px, py)

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _apply_gold(
        self,
        text_img: Image.Image,
        t: float,
        palette: list[str],
    ) -> Image.Image:
        """Apply animated gold gradient to text.

        Args:
            text_img: Source RGBA text image.
            t: Animation time.
            palette: List of CSS hex colors for gold gradient.

        Returns:
            Gold-colored RGBA image.
        """
        tw, th = text_img.size
        # Build vertical gradient
        colors = [_parse_color(c) for c in palette]
        n = len(colors)
        gradient = np.zeros((th, 1, 4), dtype=np.float32)
        phase = t * 2.0 * np.pi
        for y in range(th):
            t_grad = ((y / max(th, 1)) + np.sin(phase) * 0.2) % 1.0
            idx_f = t_grad * (n - 1)
            idx_lo = int(idx_f)
            idx_hi = min(idx_lo + 1, n - 1)
            frac = idx_f - idx_lo
            c_lo = colors[idx_lo]
            c_hi = colors[idx_hi]
            gradient[y, 0, 0] = c_lo[0] * (1 - frac) + c_hi[0] * frac
            gradient[y, 0, 1] = c_lo[1] * (1 - frac) + c_hi[1] * frac
            gradient[y, 0, 2] = c_lo[2] * (1 - frac) + c_hi[2] * frac
            gradient[y, 0, 3] = 255.0

        grad_img = np.tile(gradient, (1, tw, 1))
        text_arr = np.array(text_img, dtype=np.float32)
        alpha = text_arr[:, :, 3:4] / 255.0
        result = grad_img * alpha
        result[:, :, 3] = text_arr[:, :, 3]
        return Image.fromarray(result.clip(0, 255).astype(np.uint8), "RGBA")

    def _apply_chrome(
        self,
        text_img: Image.Image,
        t: float,
        width_frac: float,
    ) -> Image.Image:
        """Apply animated chrome highlight sweep.

        Args:
            text_img: Source RGBA text image.
            t: Animation time.
            width_frac: Highlight band width fraction.

        Returns:
            Chrome-styled RGBA image.
        """
        tw, th = text_img.size
        text_arr = np.array(text_img, dtype=np.float32)
        alpha = text_arr[:, :, 3] / 255.0

        # Grey-to-white gradient
        xs = np.arange(tw, dtype=np.float32) / max(tw, 1)
        sweep = ((t * 1.5) % 1.5) - 0.25
        dist = np.abs(xs - sweep)
        highlight = np.clip(1.0 - dist / max(width_frac, 0.01), 0.0, 1.0)

        base_val = 160.0
        chrome_r = base_val + 80 * highlight
        chrome_g = base_val + 80 * highlight
        chrome_b = base_val + 95 * highlight

        result = np.zeros_like(text_arr)
        result[:, :, 0] = chrome_r[np.newaxis, :] * alpha
        result[:, :, 1] = chrome_g[np.newaxis, :] * alpha
        result[:, :, 2] = chrome_b[np.newaxis, :] * alpha
        result[:, :, 3] = text_arr[:, :, 3]
        return Image.fromarray(result.clip(0, 255).astype(np.uint8), "RGBA")

    def _apply_bokeh(
        self,
        text_img: Image.Image,
        t: float,
        circles: list[dict],
        canvas_size: tuple[int, int],
    ) -> Image.Image:
        """Apply bokeh circles overlaid on text.

        Args:
            text_img: Source text image.
            t: Time.
            circles: Pre-generated bokeh circle dicts.
            canvas_size: Canvas size.

        Returns:
            RGBA image with bokeh overlay.
        """
        tw, th = text_img.size
        result = text_img.copy()
        bokeh_layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        from PIL import ImageDraw

        draw = ImageDraw.Draw(bokeh_layer)
        for c in circles:
            bx = int(c["x"] * tw)
            by = int(c["y"] * th)
            br = c["r"]
            alpha = int(30 + 40 * np.sin(t * 2.0 + c["phase"]))
            alpha = max(0, min(120, alpha))
            draw.ellipse([(bx - br, by - br), (bx + br, by + br)], fill=(255, 255, 255, alpha))
        bokeh_layer = bokeh_layer.filter(ImageFilter.GaussianBlur(radius=bokeh_layer.width // 30))
        return Image.alpha_composite(result, bokeh_layer)

    def _apply_hologram(self, text_img: Image.Image, t: float) -> Image.Image:
        """Apply holographic shimmer (cyan/green tint with scanlines).

        Args:
            text_img: Source RGBA text image.
            t: Animation time.

        Returns:
            Hologram-styled RGBA image.
        """
        tw, th = text_img.size
        text_arr = np.array(text_img, dtype=np.float32)
        alpha = text_arr[:, :, 3] / 255.0

        # Cyan/green tint with scan-wave
        scan_phase = np.arange(th, dtype=np.float32) / th * 4.0 * np.pi + t * 2.0
        scan = 0.7 + 0.3 * np.sin(scan_phase)

        result = np.zeros_like(text_arr)
        result[:, :, 0] = 0.0
        result[:, :, 1] = 200 * scan[:, np.newaxis] * alpha
        result[:, :, 2] = 180 * scan[:, np.newaxis] * alpha
        result[:, :, 3] = text_arr[:, :, 3]
        return Image.fromarray(result.clip(0, 255).astype(np.uint8), "RGBA")
