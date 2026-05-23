# Filepath: text_fx/typography/__init__.py
# Condensed Description: Typography package init; re-exports primary rendering API
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: render_text, load_font, compute_layout
# Dependencies: Internal: typography/fonts.py, typography/renderer.py, typography/layout.py; External: None; Providers: None
# Exposes: render_text, load_font, compute_layout, render_text_layers, resolve_position
# Configuration: None
from __future__ import annotations

import logging

from text_fx.typography.fonts import find_system_font, list_system_fonts, load_font
from text_fx.typography.layout import LayoutResult, compute_layout, split_chars, split_words
from text_fx.typography.renderer import render_text, render_text_layers, resolve_position

logger = logging.getLogger(__name__)

__all__ = [
    "render_text",
    "render_text_layers",
    "load_font",
    "compute_layout",
    "resolve_position",
    "find_system_font",
    "list_system_fonts",
    "split_words",
    "split_chars",
    "LayoutResult",
]
