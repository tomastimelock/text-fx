# Filepath: text_fx/__init__.py
# Condensed Description: Package root; version, __all__, top-level re-exports
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: apply_text_effect, apply_text_sequence, render_overlay, list_effects, list_categories, get_effect_info, TextEffectConfig, text_effect_schema, parse_llm_response
# Dependencies: Internal: api.py, config.py, catalog/loader.py, schema/__init__.py; External: None; Providers: None
# Exposes: all public API symbols
# Configuration: None
from __future__ import annotations

import logging

from text_fx.api import (
    apply_text_effect,
    apply_text_sequence,
    get_effect_info,
    list_categories,
    list_effects,
    render_overlay,
)
from text_fx.config import TextEffectConfig
from text_fx.schema import parse_llm_response, text_effect_schema

logger = logging.getLogger(__name__)

__version__ = "0.1.0"

__all__ = [
    # Primary API
    "apply_text_effect",
    "apply_text_sequence",
    "render_overlay",
    # Catalog inspection
    "list_effects",
    "list_categories",
    "get_effect_info",
    # Config
    "TextEffectConfig",
    # Schema / LLM
    "text_effect_schema",
    "parse_llm_response",
    # Version
    "__version__",
]
