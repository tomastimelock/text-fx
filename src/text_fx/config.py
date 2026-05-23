# Filepath: text_fx/config.py
# Condensed Description: TextEffectConfig pydantic model and global defaults
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: TextEffectConfig, parse_color, DEFAULT_CONFIG
# Dependencies: Internal: exceptions.py; External: pydantic>=2.5, stdlib typing; Providers: None
# Exposes: TextEffectConfig, parse_color, DEFAULT_CONFIG
# Configuration: None
from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from text_fx.exceptions import ZeroDurationError

logger = logging.getLogger(__name__)


def parse_color(css_color: str) -> tuple[int, int, int, int]:
    """Parse a CSS color string to an (R, G, B, A) tuple.

    Supports hex (#RGB, #RRGGBB, #RRGGBBAA) and a limited set of named colors.

    Args:
        css_color: CSS color string, e.g. '#FF00FF', '#fff', 'white', 'black'.

    Returns:
        (R, G, B, A) tuple with all values in range 0-255.
    """
    named: dict[str, tuple[int, int, int, int]] = {
        "white": (255, 255, 255, 255),
        "black": (0, 0, 0, 255),
        "red": (255, 0, 0, 255),
        "green": (0, 128, 0, 255),
        "lime": (0, 255, 0, 255),
        "blue": (0, 0, 255, 255),
        "yellow": (255, 255, 0, 255),
        "cyan": (0, 255, 255, 255),
        "magenta": (255, 0, 255, 255),
        "orange": (255, 165, 0, 255),
        "transparent": (0, 0, 0, 0),
    }
    s = css_color.strip().lower()
    if s in named:
        return named[s]

    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
        if len(h) == 8:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))

    logger.warning(f"Could not parse color '{css_color}'; using white")
    return (255, 255, 255, 255)


class TextEffectConfig(BaseModel):
    """Configuration for a single text effect application.

    All fields have sensible defaults. Override only what you need.

    Attributes:
        text: The text content to render and animate.
        effect: Effect slug or display name; resolved via the catalog.
        start_time: Seconds into the video at which the effect begins.
        duration: Duration of the effect in seconds.
        out_duration: Separate out-animation duration; used by in/out effects.
        font_family: System font name or path to a .ttf/.otf file.
        font_size: Font size in pixels.
        font_weight: Font weight.
        line_height: Line height multiplier.
        position: (x, y) position spec; each element is pixels or a keyword.
        margin_x: Horizontal margin used when position is 'left' or 'right'.
        margin_y: Vertical margin used when position is 'top' or 'bottom'.
        color: Main text color (CSS hex or named).
        stroke_color: Outline color; None for no outline.
        stroke_width: Outline thickness in pixels.
        shadow_enabled: Whether to render a drop shadow.
        shadow_color: Shadow color (CSS hex or named).
        shadow_blur: Shadow blur radius in pixels.
        shadow_offset: (dx, dy) shadow offset in pixels.
        shadow_opacity: Shadow opacity multiplier, 0.0–1.0.
        easing: Named easing function for the animation curve.
        intensity: Scales effect strength, 0.0–2.0.
        direction: Optional direction override for slide/wipe effects.
        video_codec: Output video codec for composited clips.
        audio_codec: Output audio codec; 'copy' passes through source audio.
        seed: Optional random seed for reproducible particle/glitch effects.
        prefer_engine: Engine selection hint.
    """

    model_config = ConfigDict(extra="forbid")

    text: str = Field(default="", description="Text content to render")
    effect: str = Field(default="fade_in", description="Effect slug or display name")

    # Timing
    start_time: float = Field(default=0.0, ge=0.0, description="Start time in seconds")
    duration: float = Field(default=2.0, description="Effect duration in seconds")
    out_duration: float | None = Field(default=None, description="Out-animation duration")

    # Typography
    font_family: str = Field(default="Inter", description="Font family name or .ttf path")
    font_size: int = Field(default=96, gt=0, description="Font size in pixels")
    font_weight: Literal["regular", "medium", "bold", "black"] = Field(
        default="bold", description="Font weight"
    )
    line_height: float = Field(default=1.2, gt=0.0, description="Line height multiplier")

    # Position
    position: tuple[
        int | Literal["center", "left", "right"], int | Literal["center", "top", "bottom"]
    ] = Field(default=("center", "center"), description="Position spec (x, y)")
    margin_x: int = Field(default=64, ge=0, description="Horizontal margin in pixels")
    margin_y: int = Field(default=64, ge=0, description="Vertical margin in pixels")

    # Style
    color: str = Field(default="#FFFFFF", description="Main text color (CSS hex or named)")
    stroke_color: str | None = Field(default=None, description="Stroke/outline color")
    stroke_width: int = Field(default=0, ge=0, description="Stroke width in pixels")
    shadow_enabled: bool = Field(default=False, description="Enable drop shadow")
    shadow_color: str = Field(default="#000000", description="Shadow color")
    shadow_blur: int = Field(default=12, ge=0, description="Shadow blur radius in pixels")
    shadow_offset: tuple[int, int] = Field(default=(0, 0), description="Shadow (dx, dy) offset")
    shadow_opacity: float = Field(default=0.35, ge=0.0, le=1.0, description="Shadow opacity")

    # Animation
    easing: Literal[
        "linear",
        "ease-in",
        "ease-out",
        "ease-in-out",
        "ease-out-cubic",
        "ease-out-back",
        "ease-out-elastic",
        "spring",
        "bounce",
    ] = Field(default="ease-out-cubic", description="Easing function name")
    intensity: float = Field(default=1.0, ge=0.0, le=2.0, description="Effect intensity 0-2")
    direction: Literal["left", "right", "up", "down", "center", "out"] | None = Field(
        default=None, description="Direction override for directional effects"
    )

    # Output
    video_codec: str = Field(default="libx264", description="Output video codec")
    audio_codec: str = Field(default="copy", description="Output audio codec")
    seed: int | None = Field(default=None, description="Random seed for reproducibility")

    # Engine selection
    prefer_engine: Literal["auto", "pillow", "opencv", "web_overlay"] = Field(
        default="auto", description="Engine preference hint"
    )

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        """Ensure duration is positive.

        Args:
            v: Duration value to validate.

        Returns:
            Validated duration.

        Raises:
            ZeroDurationError: If duration is <= 0.
        """
        if v <= 0:
            raise ZeroDurationError(v)
        return v

    def shadow_dict(self) -> dict:
        """Return shadow parameters as a dictionary for renderer use.

        Returns:
            Dictionary with shadow_color, shadow_blur, shadow_offset, shadow_opacity.
        """
        return {
            "color": self.shadow_color,
            "blur": self.shadow_blur,
            "offset": self.shadow_offset,
            "opacity": self.shadow_opacity,
        }


# Module-level default config instance (immutable reference)
DEFAULT_CONFIG = TextEffectConfig()
