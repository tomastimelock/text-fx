# Filepath: text_fx/engines/base.py
# Condensed Description: Abstract base class Engine; defines render_effect contract and frame utilities
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: Engine (ABC), EngineParams, encode_webm
# Dependencies: Internal: exceptions.py; External: abc, numpy, Pillow, subprocess, pathlib; Providers: None
# Exposes: Engine, EngineParams, encode_webm
# Configuration: None
from __future__ import annotations

import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from PIL import Image

from text_fx.exceptions import CompositorError

logger = logging.getLogger(__name__)


def encode_webm(frames_dir: Path, fps: int, output: Path) -> None:
    """Encode a directory of PNG frames to a WebM file with alpha channel using ffmpeg.

    Args:
        frames_dir: Directory containing frame_000000.png, frame_000001.png, etc.
        fps: Frame rate for the output video.
        output: Destination path for the output WebM file.

    Raises:
        CompositorError: If ffmpeg exits with a non-zero return code.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%06d.png"),
        "-c:v",
        "libvpx-vp9",
        "-pix_fmt",
        "yuva420p",
        "-auto-alt-ref",
        "0",
        str(output),
    ]
    logger.debug(f"Encoding WebM: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise CompositorError(
            detail="ffmpeg WebM encoding failed",
            returncode=result.returncode,
            stderr=stderr,
        )


class Engine(ABC):
    """Abstract base class for all text animation engines.

    Each concrete engine takes a pre-rendered text image (RGBA Pillow Image)
    and produces an animated WebM overlay file with alpha channel.

    Attributes:
        name: Engine identifier string.
        bases: Tuple of base effect names this engine handles.
    """

    name: str = "abstract"
    bases: tuple[str, ...] = ()

    @abstractmethod
    def is_available(self) -> bool:
        """Check that runtime dependencies for this engine are present.

        Returns:
            True if all required runtime deps are importable/callable.
        """

    @abstractmethod
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
        """Render the animated effect to a transparent WebM overlay clip.

        Args:
            text_image: Pre-rendered RGBA text image from typography/renderer.
            params: Engine-specific parameters from the effect mapping.
            config: TextEffectConfig instance.
            duration: Effect duration in seconds.
            fps: Output frame rate.
            canvas_size: (width, height) of the destination video canvas.
            output: Destination path for the output .webm file.

        Returns:
            Path to the written WebM file (same as output).

        Raises:
            EngineError: If rendering fails.
        """

    def _make_canvas(self, canvas_size: tuple[int, int]) -> Image.Image:
        """Create a blank transparent RGBA canvas.

        Args:
            canvas_size: (width, height) in pixels.

        Returns:
            New RGBA image filled with transparent pixels.
        """
        return Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    def _paste_text(
        self,
        canvas: Image.Image,
        text_image: Image.Image,
        px: int,
        py: int,
    ) -> None:
        """Paste a text image onto a canvas at the given position.

        Handles clipping when the text is partially off-canvas.

        Args:
            canvas: The destination RGBA canvas.
            text_image: RGBA text image to paste.
            px: X position (may be negative for off-canvas).
            py: Y position (may be negative for off-canvas).
        """
        cw, ch = canvas.size
        tw, th = text_image.size

        # Source crop region
        src_x0 = max(0, -px)
        src_y0 = max(0, -py)
        src_x1 = min(tw, cw - px)
        src_y1 = min(th, ch - py)

        if src_x1 <= src_x0 or src_y1 <= src_y0:
            return  # Entirely off-canvas

        # Destination coordinates
        dst_x = max(0, px)
        dst_y = max(0, py)

        cropped = text_image.crop((src_x0, src_y0, src_x1, src_y1))
        canvas.paste(cropped, (dst_x, dst_y), cropped)

    def _apply_alpha_mult(self, img: Image.Image, alpha_mult: float) -> Image.Image:
        """Multiply the alpha channel of an image by a scalar.

        Args:
            img: RGBA image.
            alpha_mult: Multiplier in range [0.0, 1.0].

        Returns:
            New RGBA image with modified alpha.
        """
        r, g, b, a = img.split()
        a = a.point(lambda p: int(p * max(0.0, min(1.0, alpha_mult))))
        result = img.copy()
        result.putalpha(a)
        return result

    def _scale_image(
        self,
        img: Image.Image,
        scale: float,
        center: tuple[int, int] | None = None,
    ) -> tuple[Image.Image, tuple[int, int]]:
        """Scale an image around its center (or given point).

        Args:
            img: The image to scale.
            scale: Scale factor (1.0 = no change).
            center: Optional (cx, cy) center; defaults to image center.

        Returns:
            (scaled_image, (offset_x, offset_y)) where offset is the translation
            to apply so that the scaled image is centered at the original center.
        """
        w, h = img.size
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        if new_w == w and new_h == h:
            return img, (0, 0)

        scaled = img.resize((new_w, new_h), Image.LANCZOS)
        cx = w // 2 if center is None else center[0]
        cy = h // 2 if center is None else center[1]
        offset_x = cx - new_w // 2
        offset_y = cy - new_h // 2
        return scaled, (offset_x, offset_y)
