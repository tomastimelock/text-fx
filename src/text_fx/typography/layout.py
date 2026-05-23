# Filepath: text_fx/typography/layout.py
# Condensed Description: Multi-line text layout and per-unit splitting for animation engines
# Architecture Layer: Utility
# Environment: Both
# Script Hierarchy: LayoutResult, compute_layout, split_words, split_chars
# Dependencies: Internal: typography/fonts.py; External: Pillow, stdlib dataclasses; Providers: None
# Exposes: LayoutResult, compute_layout, split_words, split_chars
# Configuration: None
from __future__ import annotations

import logging
from dataclasses import dataclass

from PIL import ImageFont

logger = logging.getLogger(__name__)


@dataclass
class LayoutResult:
    """Result of laying out text with a given font.

    Attributes:
        lines: List of line strings after wrapping.
        line_bboxes: Bounding box (x0, y0, x1, y1) per line, relative to image origin.
        word_bboxes: Bounding box per word token (left, top, right, bottom).
        char_bboxes: Bounding box per character (left, top, right, bottom).
        total_size: (width, height) of the full text block in pixels.
    """

    lines: list[str]
    line_bboxes: list[tuple[int, int, int, int]]
    word_bboxes: list[tuple[int, int, int, int]]
    char_bboxes: list[tuple[int, int, int, int]]
    total_size: tuple[int, int]


def split_words(text: str) -> list[str]:
    """Split text into word tokens, preserving non-empty tokens.

    Args:
        text: Input text string, may contain spaces and newlines.

    Returns:
        List of word strings.
    """
    tokens: list[str] = []
    for line in text.splitlines():
        for word in line.split():
            if word:
                tokens.append(word)
    return tokens


def split_chars(text: str) -> list[str]:
    """Split text into individual characters, skipping whitespace.

    Args:
        text: Input text string.

    Returns:
        List of single-character strings.
    """
    return [ch for ch in text if ch.strip()]


def _wrap_text(
    text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int
) -> list[str]:
    """Wrap text to fit within max_width pixels using the given font.

    Args:
        text: Input text (may include newlines for explicit breaks).
        font: The font used for measurement.
        max_width: Maximum line width in pixels.

    Returns:
        List of line strings.
    """
    # Honour explicit newlines first
    hard_lines = text.splitlines() if text.strip() else [""]
    result_lines: list[str] = []

    for hard_line in hard_lines:
        words = hard_line.split()
        if not words:
            result_lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            test_line = f"{current} {word}"
            try:
                bbox = font.getbbox(test_line)
                w = bbox[2] - bbox[0]
            except AttributeError:
                # PIL default font has getsize
                w, _ = font.getsize(test_line)  # type: ignore[attr-defined]
            if w <= max_width:
                current = test_line
            else:
                result_lines.append(current)
                current = word
        result_lines.append(current)

    return result_lines


def _measure_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> tuple[int, int]:
    """Measure pixel dimensions of a text string.

    Args:
        text: Text to measure.
        font: Font used for measurement.

    Returns:
        (width, height) tuple in pixels.
    """
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return font.getsize(text)  # type: ignore[attr-defined]


def compute_layout(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int | None = None,
    line_height_factor: float = 1.2,
) -> LayoutResult:
    """Compute the layout of text given a font and optional max width.

    Produces bounding boxes for lines, words, and individual characters
    relative to the top-left of the rendered text block.

    Args:
        text: The text to lay out. Newlines produce explicit line breaks.
        font: The Pillow font used for measurement.
        max_width: Maximum line width in pixels; if None, no wrapping is done.
        line_height_factor: Multiplier for line height (1.2 = 20% extra leading).

    Returns:
        A LayoutResult with all bounding boxes and total size.
    """
    # Determine lines
    if max_width is not None:
        lines = _wrap_text(text, font, max_width)
    else:
        lines = text.splitlines() if text.strip() else [""]

    # Measure each line to get line height
    line_heights: list[int] = []
    line_widths: list[int] = []
    for line in lines:
        w, h = _measure_text(line or " ", font)
        line_widths.append(w)
        line_heights.append(h)

    # Single character height as baseline
    _, char_h = _measure_text("Ag", font)
    step = int(char_h * line_height_factor)

    total_w = max(line_widths) if line_widths else 0
    total_h = step * len(lines) if lines else char_h

    # Build line bboxes (left-aligned within the block)
    line_bboxes: list[tuple[int, int, int, int]] = []
    y_cursor = 0
    for i, _line in enumerate(lines):
        x0 = 0
        y0 = y_cursor
        x1 = line_widths[i]
        y1 = y0 + line_heights[i]
        line_bboxes.append((x0, y0, x1, y1))
        y_cursor += step

    # Build word bboxes
    word_bboxes: list[tuple[int, int, int, int]] = []
    y_cursor = 0
    for line in lines:
        words = line.split()
        x_cursor = 0
        for word in words:
            w, h = _measure_text(word, font)
            word_bboxes.append((x_cursor, y_cursor, x_cursor + w, y_cursor + h))
            space_w, _ = _measure_text(" ", font)
            x_cursor += w + space_w
        y_cursor += step

    # Build char bboxes
    char_bboxes: list[tuple[int, int, int, int]] = []
    y_cursor = 0
    for line in lines:
        x_cursor = 0
        for ch in line:
            if ch == " ":
                space_w, _ = _measure_text(" ", font)
                x_cursor += space_w
                continue
            w, h = _measure_text(ch, font)
            char_bboxes.append((x_cursor, y_cursor, x_cursor + w, y_cursor + h))
            x_cursor += w
        y_cursor += step

    return LayoutResult(
        lines=lines,
        line_bboxes=line_bboxes,
        word_bboxes=word_bboxes,
        char_bboxes=char_bboxes,
        total_size=(total_w, total_h),
    )
