# Filepath: text_fx/engines/glitch/slice_corrupt.py
# Condensed Description: Horizontal slice corruption engine for digital glitch effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: SliceCorruptEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: SliceCorruptEngine
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


class SliceCorruptEngine(Engine):
    """Engine for horizontal slice and block corruption effects.

    Modes:
        slices: standard horizontal slice offset
        datamosh: moshing-style block repetition
        pixel_sort: pixel sorting within slices
        blocks: random block corruption
        tear: jagged tearing apart
        flash: rapid flash + slice
        static: noise fill
        pixelate: pixelation reveal
        bad_signal: noise + displacement combination

    Params:
        slice_count: int — number of slices
        max_offset_px: int — max pixel offset per slice
        mode: see above
        noise_density: float — fraction of pixels to corrupt with noise
    """

    name = "slice_corrupt"
    bases = ("slice_corrupt",)

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
        """Render slice corruption animation.

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
        slice_count = int(params.get("slice_count", 12))
        max_offset = int(params.get("max_offset_px", 40)) * config.intensity
        mode = params.get("mode", "slices")
        noise_density = float(params.get("noise_density", 0.05))
        block_size = int(params.get("block_size", 16))

        frames = max(1, int(duration * fps))
        tw, th = text_image.size
        px, py = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        rng = np.random.default_rng(config.seed)
        text_arr = np.array(text_image, dtype=np.uint8)  # (h, w, 4)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t = i / max(frames - 1, 1)
                canvas = self._make_canvas(canvas_size)

                if mode == "slices":
                    result = self._apply_slices(text_arr, slice_count, max_offset, t, rng)
                elif mode == "datamosh":
                    result = self._apply_datamosh(text_arr, slice_count, max_offset, t, rng)
                elif mode == "pixel_sort":
                    result = self._apply_pixel_sort(text_arr, slice_count, t, rng)
                elif mode == "blocks":
                    result = self._apply_blocks(text_arr, block_size, noise_density, t, rng)
                elif mode == "tear":
                    result = self._apply_tear(text_arr, slice_count, max_offset, t, rng)
                elif mode == "flash":
                    result = self._apply_flash(text_arr, slice_count, max_offset, i, rng)
                elif mode == "static":
                    result = self._apply_static(text_arr, noise_density, t, rng)
                elif mode == "pixelate":
                    result = self._apply_pixelate(text_arr, t)
                elif mode == "bad_signal":
                    result = self._apply_bad_signal(
                        text_arr, slice_count, max_offset, noise_density, t, rng
                    )
                else:
                    result = self._apply_slices(text_arr, slice_count, max_offset, t, rng)

                glitched_img = Image.fromarray(result.clip(0, 255).astype(np.uint8), "RGBA")
                self._paste_text(canvas, glitched_img, px, py)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output

    def _apply_slices(
        self,
        arr: np.ndarray,
        n: int,
        max_off: float,
        t: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Apply horizontal slice offsets.

        Args:
            arr: RGBA pixel array (h, w, 4).
            n: Number of slices.
            max_off: Max offset pixels.
            t: Normalized time.
            rng: RNG.

        Returns:
            Corrupted RGBA array.
        """
        h, w = arr.shape[:2]
        result = arr.copy()
        slice_h = max(1, h // n)
        # Glitch intensity decays or pulses
        intensity = 0.5 + 0.5 * np.sin(t * np.pi * 6)
        for k in range(n):
            y0 = k * slice_h
            y1 = min(h, y0 + slice_h)
            if rng.random() > 0.4:  # Only some slices glitch
                offset = int(rng.integers(-int(max_off), int(max_off) + 1) * intensity)
                result[y0:y1, :, :] = np.roll(arr[y0:y1, :, :], offset, axis=1)
        return result

    def _apply_datamosh(
        self,
        arr: np.ndarray,
        n: int,
        max_off: float,
        t: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Apply moshing-style block repetition.

        Args:
            arr: RGBA pixel array.
            n: Number of slices.
            max_off: Max offset.
            t: Time.
            rng: RNG.

        Returns:
            Corrupted array.
        """
        h, w = arr.shape[:2]
        result = arr.copy()
        slice_h = max(1, h // n)
        for k in range(n):
            y0 = k * slice_h
            y1 = min(h, y0 + slice_h)
            if rng.random() > 0.5:
                src_k = rng.integers(0, n)
                src_y0 = src_k * slice_h
                src_y1 = min(h, src_y0 + slice_h)
                src_slice = arr[src_y0:src_y1, :, :]
                dst_h = y1 - y0
                src_h = src_y1 - src_y0
                copy_h = min(dst_h, src_h)
                result[y0 : y0 + copy_h, :, :] = src_slice[:copy_h, :, :]
        return result

    def _apply_pixel_sort(
        self,
        arr: np.ndarray,
        n: int,
        t: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Sort pixels within slices by luminance.

        Args:
            arr: RGBA pixel array.
            n: Number of slices.
            t: Time.
            rng: RNG.

        Returns:
            Pixel-sorted array.
        """
        h, w = arr.shape[:2]
        result = arr.copy()
        slice_h = max(1, h // n)
        for k in range(n):
            y0 = k * slice_h
            y1 = min(h, y0 + slice_h)
            if rng.random() > 0.3:
                lum = 0.299 * arr[y0:y1, :, 0] + 0.587 * arr[y0:y1, :, 1] + 0.114 * arr[y0:y1, :, 2]
                for row_off in range(y1 - y0):
                    idx = np.argsort(lum[row_off])
                    result[y0 + row_off, :, :] = arr[y0 + row_off, idx, :]
        return result

    def _apply_blocks(
        self,
        arr: np.ndarray,
        block_size: int,
        density: float,
        t: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Corrupt random blocks with noise.

        Args:
            arr: RGBA pixel array.
            block_size: Block size in pixels.
            density: Fraction of blocks to corrupt.
            t: Time.
            rng: RNG.

        Returns:
            Block-corrupted array.
        """
        h, w = arr.shape[:2]
        result = arr.copy()
        bh = max(1, block_size)
        bw = max(1, block_size)
        for y0 in range(0, h, bh):
            for x0 in range(0, w, bw):
                if rng.random() < density:
                    y1 = min(h, y0 + bh)
                    x1 = min(w, x0 + bw)
                    noise = rng.integers(0, 256, (y1 - y0, x1 - x0, 3), dtype=np.uint8)
                    result[y0:y1, x0:x1, :3] = noise
        return result

    def _apply_tear(
        self,
        arr: np.ndarray,
        n: int,
        max_off: float,
        t: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Tear the image apart along horizontal slices.

        Args:
            arr: RGBA pixel array.
            n: Tear count.
            max_off: Max displacement.
            t: Time (increasing = more tear).
            rng: RNG.

        Returns:
            Torn array.
        """
        h, w = arr.shape[:2]
        result = np.zeros_like(arr)
        slice_h = max(1, h // n)
        for k in range(n):
            y0 = k * slice_h
            y1 = min(h, y0 + slice_h)
            offset = int(rng.integers(-int(max_off * t), int(max_off * t) + 1))
            result[y0:y1, :, :] = np.roll(arr[y0:y1, :, :], offset, axis=1)
        return result

    def _apply_flash(
        self,
        arr: np.ndarray,
        n: int,
        max_off: float,
        frame_idx: int,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Rapid flash with glitch slices every few frames.

        Args:
            arr: RGBA pixel array.
            n: Slice count.
            max_off: Max offset.
            frame_idx: Current frame index.
            rng: RNG.

        Returns:
            Flashed/sliced array.
        """
        if frame_idx % 4 < 2:
            # Brief flash: whiten alpha partially
            result = arr.copy()
            result[:, :, 3] = np.minimum(arr[:, :, 3], 200)
            return result
        return self._apply_slices(arr, n, max_off, 1.0, rng)

    def _apply_static(
        self,
        arr: np.ndarray,
        density: float,
        t: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Fill a fraction of pixels with static noise.

        Args:
            arr: RGBA pixel array.
            density: Fraction of pixels to fill.
            t: Time.
            rng: RNG.

        Returns:
            Static-filled array.
        """
        h, w = arr.shape[:2]
        result = arr.copy()
        n_pixels = int(h * w * density)
        if n_pixels > 0:
            ys = rng.integers(0, h, n_pixels)
            xs = rng.integers(0, w, n_pixels)
            noise = rng.integers(180, 256, n_pixels, dtype=np.uint8)
            result[ys, xs, 0] = noise
            result[ys, xs, 1] = noise
            result[ys, xs, 2] = noise
            result[ys, xs, 3] = arr[ys, xs, 3]  # preserve alpha
        return result

    def _apply_pixelate(self, arr: np.ndarray, t: float) -> np.ndarray:
        """Pixelate reveal: start blocky, become sharp.

        Args:
            arr: RGBA pixel array.
            t: Time (0 = very pixelated, 1 = sharp).

        Returns:
            Pixelated array.
        """
        h, w = arr.shape[:2]
        max_block = 32
        block_size = max(1, int(max_block * (1.0 - t)))
        if block_size <= 1:
            return arr.copy()
        small = Image.fromarray(arr, "RGBA").resize(
            (max(1, w // block_size), max(1, h // block_size)), Image.NEAREST
        )
        pixelated = small.resize((w, h), Image.NEAREST)
        return np.array(pixelated)

    def _apply_bad_signal(
        self,
        arr: np.ndarray,
        n: int,
        max_off: float,
        density: float,
        t: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Combine slice displacement and static noise.

        Args:
            arr: RGBA pixel array.
            n: Slice count.
            max_off: Max offset.
            density: Noise density.
            t: Time.
            rng: RNG.

        Returns:
            Bad-signal array.
        """
        result = self._apply_slices(arr, n, max_off * 0.5, t, rng)
        return self._apply_static(result, density, t, rng)
