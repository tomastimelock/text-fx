# Filepath: text_fx/engines/__init__.py
# Condensed Description: Top-level engines package init; exposes ENGINE_REGISTRY and get_engine
# Architecture Layer: Engine
# Environment: Both
# Script Hierarchy: ENGINE_REGISTRY, get_engine
# Dependencies: Internal: all six bucket __init__.py files, engines/base.py; External: None; Providers: None
# Exposes: ENGINE_REGISTRY, get_engine, Engine
# Configuration: None
from __future__ import annotations

import logging

from text_fx.engines.alpha import CascadeEngine, FadeEngine, TypewriterEngine
from text_fx.engines.base import Engine
from text_fx.engines.distortion import (
    DisplacementEngine,
    MotionBlurEngine,
    ParticleEngine,
    RadialWarpEngine,
    SineWarpEngine,
)
from text_fx.engines.glitch import DecodeEngine, RgbShiftEngine, ScanlineEngine, SliceCorruptEngine
from text_fx.engines.kinetic import (
    BounceEngine,
    OscillateEngine,
    SlideEngine,
    SpinEngine,
    SpringEngine,
)
from text_fx.engines.mask import LinearWipeEngine, OrganicEngine, RadialEngine, ShapedEngine
from text_fx.engines.neon import GlowEngine, ShimmerEngine, SparkleEngine, SweepEngine

logger = logging.getLogger(__name__)

# Registry maps engine name string → engine instance
ENGINE_REGISTRY: dict[str, Engine] = {
    # Alpha
    "fade": FadeEngine(),
    "typewriter": TypewriterEngine(),
    "cascade": CascadeEngine(),
    # Kinetic
    "slide": SlideEngine(),
    "spring": SpringEngine(),
    "bounce": BounceEngine(),
    "spin": SpinEngine(),
    "oscillate": OscillateEngine(),
    # Mask
    "linear_wipe": LinearWipeEngine(),
    "radial": RadialEngine(),
    "shaped": ShapedEngine(),
    "organic": OrganicEngine(),
    # Glitch
    "rgb_shift": RgbShiftEngine(),
    "slice_corrupt": SliceCorruptEngine(),
    "decode": DecodeEngine(),
    "scanline": ScanlineEngine(),
    # Distortion
    "sine_warp": SineWarpEngine(),
    "radial_warp": RadialWarpEngine(),
    "displacement": DisplacementEngine(),
    "motion_blur": MotionBlurEngine(),
    "particle": ParticleEngine(),
    # Neon
    "glow": GlowEngine(),
    "sweep": SweepEngine(),
    "shimmer": ShimmerEngine(),
    "sparkle": SparkleEngine(),
}


def get_engine(name: str) -> Engine:
    """Retrieve an engine instance by name.

    Args:
        name: Engine name string from ENGINE_REGISTRY.

    Returns:
        Engine instance.

    Raises:
        KeyError: If the engine name is not in the registry.
    """
    if name not in ENGINE_REGISTRY:
        valid = ", ".join(sorted(ENGINE_REGISTRY.keys()))
        raise KeyError(f"Unknown engine '{name}'. Valid engines: {valid}")
    return ENGINE_REGISTRY[name]


__all__ = ["ENGINE_REGISTRY", "get_engine", "Engine"]
