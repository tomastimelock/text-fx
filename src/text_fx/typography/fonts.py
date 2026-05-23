# Filepath: text_fx/typography/fonts.py
# Condensed Description: Font loading with system discovery and fallback chain
# Architecture Layer: Utility
# Environment: Both
# Script Hierarchy: load_font, find_system_font, list_system_fonts
# Dependencies: Internal: exceptions.py; External: Pillow, stdlib pathlib/warnings; Providers: optional fonttools/matplotlib
# Exposes: load_font, find_system_font, list_system_fonts
# Configuration: None
from __future__ import annotations

import logging
import warnings
from pathlib import Path

from PIL import ImageFont

from text_fx.exceptions import TypographyError

logger = logging.getLogger(__name__)

# Weight name → typical filename substring or style name
_WEIGHT_HINTS: dict[str, list[str]] = {
    "regular": ["Regular", "Normal", "Roman", ""],
    "medium": ["Medium", "SemiBold"],
    "bold": ["Bold"],
    "black": ["Black", "ExtraBold", "Heavy"],
}


def find_system_font(family: str, weight: str = "regular") -> Path | None:
    """Locate a system font file by family name and weight.

    Uses matplotlib.font_manager if available, then falls back to a simple
    platform-specific directory scan.

    Args:
        family: Font family name, e.g. 'Inter', 'Arial', 'DejaVu Sans'.
        weight: One of 'regular', 'medium', 'bold', 'black'.

    Returns:
        Path to the font file, or None if not found.
    """
    # 1. Try matplotlib font_manager
    try:
        from matplotlib import font_manager as fm  # type: ignore[import]

        weight_map = {"regular": 400, "medium": 500, "bold": 700, "black": 900}
        props = fm.FontProperties(family=family, weight=weight_map.get(weight, 400))
        path_str = fm.findfont(props, fallback_to_default=False)
        if path_str and Path(path_str).exists():
            resolved = Path(path_str)
            logger.debug(f"Found font via matplotlib: {resolved}")
            return resolved
    except Exception as exc:
        logger.debug(f"matplotlib font discovery failed for '{family}': {exc}")

    # 2. Filesystem scan of common font directories
    import platform

    font_dirs: list[Path] = []
    system = platform.system()
    if system == "Windows":
        font_dirs = [
            Path("C:/Windows/Fonts"),
            Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
        ]
    elif system == "Darwin":
        font_dirs = [
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
            Path.home() / "Library/Fonts",
        ]
    else:
        font_dirs = [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
            Path.home() / ".local/share/fonts",
        ]

    weight_hints = _WEIGHT_HINTS.get(weight, [""])
    family_lower = family.lower().replace(" ", "")

    # Collect candidates
    candidates: list[tuple[int, Path]] = []
    for font_dir in font_dirs:
        if not font_dir.exists():
            continue
        for font_file in font_dir.rglob("*"):
            if font_file.suffix.lower() not in {".ttf", ".otf"}:
                continue
            stem_lower = font_file.stem.lower().replace(" ", "").replace("-", "").replace("_", "")
            if family_lower not in stem_lower:
                continue
            # Score by weight match
            score = 0
            for hint in weight_hints:
                if hint and hint.lower() in stem_lower:
                    score = 1
                    break
            candidates.append((score, font_file))

    if candidates:
        candidates.sort(key=lambda x: -x[0])
        chosen = candidates[0][1]
        logger.debug(f"Found font via filesystem scan: {chosen}")
        return chosen

    return None


def list_system_fonts() -> list[str]:
    """List all discoverable system font family names.

    Returns:
        Sorted list of font family name strings.
    """
    try:
        from matplotlib import font_manager as fm  # type: ignore[import]

        names = sorted({f.name for f in fm.fontManager.ttflist})
        return names
    except Exception:
        pass

    # Fallback: scan directories
    import platform

    font_dirs: list[Path] = []
    system = platform.system()
    if system == "Windows":
        font_dirs = [Path("C:/Windows/Fonts")]
    elif system == "Darwin":
        font_dirs = [Path("/Library/Fonts"), Path("/System/Library/Fonts")]
    else:
        font_dirs = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]

    names: set[str] = set()
    for font_dir in font_dirs:
        if not font_dir.exists():
            continue
        for font_file in font_dir.rglob("*"):
            if font_file.suffix.lower() in {".ttf", ".otf"}:
                # Strip weight suffixes heuristically
                stem = font_file.stem
                for suffix in ["-Regular", "-Bold", "-Medium", "-Black", "-Italic", "-Light"]:
                    stem = stem.replace(suffix, "")
                names.add(stem)
    return sorted(names)


def load_font(
    family: str,
    size: int,
    weight: str = "regular",
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a Pillow ImageFont.

    Resolution order:
      1. If family is a path to an existing .ttf/.otf file, load it directly.
      2. Try system font registry via find_system_font().
      3. Warn and fall back to PIL's default bitmap font.

    Args:
        family: Font family name (e.g. 'Inter') or path to a .ttf/.otf file.
        size: Font size in pixels.
        weight: One of 'regular', 'medium', 'bold', 'black'.

    Returns:
        A Pillow ImageFont instance.

    Raises:
        TypographyError: If an explicit file path is given but the file cannot be loaded.
    """
    # 1. Direct file path
    candidate_path = Path(family)
    if candidate_path.suffix.lower() in {".ttf", ".otf"}:
        if not candidate_path.exists():
            raise TypographyError(f"Font file not found: '{candidate_path}'")
        try:
            font = ImageFont.truetype(str(candidate_path), size=size)
            logger.debug(f"Loaded font from explicit path: {candidate_path}")
            return font
        except Exception as exc:
            raise TypographyError(f"Failed to load font from '{candidate_path}': {exc}") from exc

    # 2. System font registry
    font_path = find_system_font(family, weight=weight)
    if font_path is not None:
        try:
            font = ImageFont.truetype(str(font_path), size=size)
            logger.debug(f"Loaded font '{family}' ({weight}) from {font_path}")
            return font
        except Exception as exc:
            logger.warning(f"Failed to load discovered font '{font_path}': {exc}")

    # 3. Default fallback with warning
    warnings.warn(
        f"Font '{family}' (weight='{weight}') not found on this system. "
        f"Falling back to PIL default font (no size control). "
        f"Install the font or use 'pip install text-fx[fonts]' for better discovery. "
        f"Tried: explicit path (not a .ttf/.otf), matplotlib font_manager, filesystem scan.",
        UserWarning,
        stacklevel=3,
    )
    logger.debug(f"Using PIL default font for '{family}'")
    return ImageFont.load_default()
