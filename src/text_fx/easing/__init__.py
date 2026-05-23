# Filepath: text_fx/easing/__init__.py
# Condensed Description: Easing package init; re-exports all easing callables
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: get_easing, EASING_NAMES
# Dependencies: Internal: easing/curves.py; External: None; Providers: None
# Exposes: get_easing, EASING_NAMES, all individual easing functions
# Configuration: None
from __future__ import annotations

import logging

from text_fx.easing.curves import (
    EASING_NAMES,
    bounce,
    ease_in,
    ease_in_out,
    ease_out,
    ease_out_back,
    ease_out_cubic,
    ease_out_elastic,
    get_easing,
    linear,
    spring,
)

logger = logging.getLogger(__name__)

__all__ = [
    "get_easing",
    "EASING_NAMES",
    "linear",
    "ease_in",
    "ease_out",
    "ease_in_out",
    "ease_out_cubic",
    "ease_out_back",
    "ease_out_elastic",
    "spring",
    "bounce",
]
