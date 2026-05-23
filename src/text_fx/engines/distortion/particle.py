# Filepath: text_fx/engines/distortion/particle.py
# Condensed Description: Particle simulation engine for sand, ash, disperse, explode, assemble effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: ParticleEngine
# Dependencies: Internal: engines/base.py, easing/curves.py; External: numpy, Pillow; Providers: None
# Exposes: ParticleEngine
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from text_fx.easing.curves import ease_out_cubic, get_easing
from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.renderer import resolve_position

logger = logging.getLogger(__name__)


class ParticleEngine(Engine):
    """Engine for particle-based text dissolution and assembly.

    Modes:
        disperse: particles fly outward
        assemble: particles fly inward from random positions to form text
        dissolve: sand-grain settling dissolution
        ash: upward drifting particles with fade
        explode: explosive outward burst with gravity
        melt: downward drip

    Params:
        mode: see above
        particle_count: int — number of particles (sampling density)
        gravity: float — downward acceleration (pixels/sec^2)
        wind: float — horizontal drift
        seed: int
    """

    name = "particle"
    bases = ("particle",)

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
        """Render particle simulation animation.

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
        mode = params.get("mode", "disperse")
        particle_count = int(params.get("particle_count", 2000))
        gravity = float(params.get("gravity", 200.0)) * config.intensity
        wind = float(params.get("wind", 0.0))

        easing_fn = get_easing(config.easing)
        frames = max(1, int(duration * fps))

        tw, th = text_image.size
        px_off, py_off = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        rng = np.random.default_rng(config.seed if config.seed is not None else 0)
        text_arr = np.array(text_image, dtype=np.uint8)

        # Sample particles from visible text pixels
        alpha_ch = text_arr[:, :, 3]
        visible_mask = alpha_ch > 30
        ys_vis, xs_vis = np.where(visible_mask)

        if len(ys_vis) == 0:
            # No visible pixels — render blank
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                blank = self._make_canvas(canvas_size)
                blank.save(tmpdir_path / "frame_000000.png")
                encode_webm(tmpdir_path, fps, output)
            return output

        n = min(particle_count, len(ys_vis))
        idx = rng.choice(len(ys_vis), size=n, replace=False)
        px_src = xs_vis[idx].astype(np.float32)
        py_src = ys_vis[idx].astype(np.float32)
        colors = text_arr[ys_vis[idx], xs_vis[idx], :]  # (n, 4)

        # Initial velocities
        if mode == "disperse":
            cx_local, cy_local = tw / 2.0, th / 2.0
            vx = (px_src - cx_local) / max(tw, 1) * 200.0 * config.intensity
            vx += rng.normal(0, 20, n)
            vy = (py_src - cy_local) / max(th, 1) * 200.0 * config.intensity
            vy += rng.normal(0, 20, n)
        elif mode == "explode":
            cx_local, cy_local = tw / 2.0, th / 2.0
            angles = rng.uniform(0, 2 * np.pi, n)
            speeds = rng.uniform(100, 400, n) * config.intensity
            vx = np.cos(angles) * speeds
            vy = np.sin(angles) * speeds
        elif mode == "ash":
            vx = rng.normal(wind * 30, 15, n)
            vy = rng.uniform(-80, -30, n) * config.intensity  # upward
        elif mode == "dissolve":
            vx = rng.normal(wind * 10, 8, n)
            vy = rng.uniform(20, 60, n) * config.intensity
        elif mode == "melt":
            vx = rng.normal(0, 3, n)
            vy = rng.uniform(30, 100, n) * config.intensity
        elif mode == "sand":
            vx = rng.normal(wind * 15, 12, n)
            vy = rng.uniform(40, 100, n) * config.intensity
        elif mode == "assemble":
            # End at text positions; start scattered
            end_px = px_src.copy()
            end_py = py_src.copy()
            cw, ch = canvas_size
            px_src = rng.uniform(0, cw, n).astype(np.float32) - px_off
            py_src = rng.uniform(0, ch, n).astype(np.float32) - py_off
            vx = np.zeros(n)
            vy = np.zeros(n)
        else:
            vx = rng.normal(0, 30, n)
            vy = rng.normal(-30, 30, n)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Current positions (copies)
            cur_px = px_src.copy()
            cur_py = py_src.copy()
            dt = 1.0 / fps

            for i in range(frames):
                t = i / max(frames - 1, 1)
                progress = float(easing_fn(np.array([t]))[0])
                canvas = self._make_canvas(canvas_size)

                if mode == "assemble":
                    # Interpolate toward final position
                    cur_x = px_src + (end_px - px_src) * ease_out_cubic(t)
                    cur_y = py_src + (end_py - py_src) * ease_out_cubic(t)
                    alpha_mult = progress
                else:
                    # Physics integration
                    if mode == "disperse":
                        cur_px = cur_px + vx * dt * progress
                        cur_py = cur_py + vy * dt * progress
                    elif mode == "explode":
                        cur_px = cur_px + vx * dt
                        cur_py = cur_py + vy * dt + 0.5 * gravity * dt**2
                        vy = vy + gravity * dt
                    elif mode in ("ash", "dissolve", "sand", "melt"):
                        cur_px = cur_px + vx * dt
                        cur_py = cur_py + vy * dt
                        if mode in ("dissolve", "sand", "melt"):
                            vy = vy + gravity * 0.1 * dt
                    else:
                        cur_px = cur_px + vx * dt
                        cur_py = cur_py + vy * dt

                    cur_x = cur_px
                    cur_y = cur_py
                    alpha_mult = max(0.0, 1.0 - progress * 1.2)

                # Draw particles
                draw = ImageDraw.Draw(canvas)
                for j in range(n):
                    cx_ = int(cur_x[j]) + px_off
                    cy_ = int(cur_y[j]) + py_off
                    if 0 <= cx_ < canvas_size[0] and 0 <= cy_ < canvas_size[1]:
                        r, g, b, a = (
                            int(colors[j, 0]),
                            int(colors[j, 1]),
                            int(colors[j, 2]),
                            int(colors[j, 3]),
                        )
                        pa = int(a * alpha_mult)
                        if pa > 0:
                            draw.point((cx_, cy_), fill=(r, g, b, pa))

                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
