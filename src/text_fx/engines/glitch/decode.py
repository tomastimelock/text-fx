# Filepath: text_fx/engines/glitch/decode.py
# Condensed Description: Character-substitution decode engine for hacker, binary, matrix, terminal effects
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: DecodeEngine
# Dependencies: Internal: engines/base.py, easing/curves.py, typography/fonts.py, typography/layout.py; External: numpy, Pillow; Providers: None
# Exposes: DecodeEngine
# Configuration: None
from __future__ import annotations

import logging
import random
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from text_fx.engines.base import Engine, encode_webm
from text_fx.typography.fonts import load_font
from text_fx.typography.layout import compute_layout
from text_fx.typography.renderer import _parse_color, resolve_position

logger = logging.getLogger(__name__)

_CHARSETS: dict[str, str] = {
    "alphanumeric": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*",
    "binary": "01",
    "matrix": "ｦｧｨｩｪｫｬｭｮｯｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉ0123456789",
    "terminal": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-+=/\\|><^",
    "hud": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:.[]{}",
}


class DecodeEngine(Engine):
    """Engine for character-substitution decode effects.

    Characters appear to scramble through random chars before settling on the real char.

    Params:
        charset: 'alphanumeric' | 'binary' | 'matrix' | 'terminal' | 'hud'
        cycles_per_char: float — number of scramble cycles per character
        stagger_s: float — stagger per character
        background_rain: bool — render matrix-rain in background
        mode: 'decode' | 'matrix' | 'hacker' | 'binary' | 'terminal' | 'hud'
    """

    name = "decode"
    bases = ("decode",)

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
        """Render decode animation.

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
        mode = params.get("mode", "hacker")
        charset_name = params.get(
            "charset",
            {
                "hacker": "alphanumeric",
                "binary": "binary",
                "matrix": "matrix",
                "terminal": "terminal",
                "hud": "hud",
            }.get(mode, "alphanumeric"),
        )
        charset = _CHARSETS.get(charset_name, _CHARSETS["alphanumeric"])
        stagger_s = float(params.get("stagger_s", duration / max(len(config.text), 1) * 0.5))
        background_rain = bool(params.get("background_rain", mode == "matrix"))

        font = load_font(config.font_family, config.font_size, weight=config.font_weight)
        layout = compute_layout(config.text, font, line_height_factor=config.line_height)
        main_color = _parse_color(config.color)
        scramble_color = (
            int(main_color[0] * 0.7),
            int(main_color[1] * 0.7),
            int(main_color[2] * 0.7),
            main_color[3],
        )

        chars = [ch for line in layout.lines for ch in line]
        char_bboxes = layout.char_bboxes
        tw, th = layout.total_size
        if tw == 0:
            tw = config.font_size * max(len(config.text), 1)
        if th == 0:
            th = config.font_size

        px, py = resolve_position(
            config.position,
            canvas_size,
            (tw, th),
            margin_x=config.margin_x,
            margin_y=config.margin_y,
        )

        frames = max(1, int(duration * fps))
        rng_py = random.Random(config.seed)

        # Matrix rain columns if needed
        rain_cols: list[dict] = []
        if background_rain:
            col_w = config.font_size // 2
            n_cols = canvas_size[0] // max(col_w, 1)
            for _ in range(n_cols):
                rain_cols.append(
                    {
                        "x": rng_py.randint(0, canvas_size[0]),
                        "y": rng_py.randint(-canvas_size[1], 0),
                        "speed": rng_py.randint(5, 20),
                        "chars": [rng_py.choice(charset) for _ in range(20)],
                    }
                )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i in range(frames):
                t_sec = i / fps
                canvas = self._make_canvas(canvas_size)
                draw = ImageDraw.Draw(canvas)

                # Background rain
                if background_rain:
                    rain_color = (0, 255, 70, 80)
                    for col in rain_cols:
                        cy = col["y"] + int(t_sec * col["speed"] * 30)
                        for ci, ch in enumerate(col["chars"]):
                            cy_draw = (cy + ci * (config.font_size // 2)) % canvas_size[1]
                            draw.text((col["x"], cy_draw), ch, font=font, fill=rain_color)

                # Render each character (scrambled or final)
                text_canvas = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
                tc_draw = ImageDraw.Draw(text_canvas)

                for j, (ch, bbox) in enumerate(zip(chars, char_bboxes, strict=False)):
                    if not ch.strip():
                        continue
                    char_start_t = j * stagger_s
                    char_elapsed = t_sec - char_start_t
                    total_char_duration = max(0.3, stagger_s * 2)

                    if char_elapsed <= 0:
                        # Not yet started — show nothing
                        pass
                    elif char_elapsed < total_char_duration * 0.7:
                        # Scrambling phase
                        scramble_char = rng_py.choice(charset)
                        tc_draw.text(
                            (bbox[0], bbox[1]), scramble_char, font=font, fill=scramble_color
                        )
                    else:
                        # Settled: show actual character
                        tc_draw.text((bbox[0], bbox[1]), ch, font=font, fill=main_color)

                canvas.paste(text_canvas, (px, py), text_canvas)
                frame_path = tmpdir_path / f"frame_{i:06d}.png"
                canvas.save(frame_path)

            encode_webm(tmpdir_path, fps, output)

        return output
