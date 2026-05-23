# Filepath: text_fx/easing/curves.py
# Condensed Description: Pure easing functions used by every animation engine
# Architecture Layer: Utility
# Environment: Both
# Script Hierarchy: linear, ease_in, ease_out, ease_in_out, ease_out_cubic, ease_out_back, ease_out_elastic, spring, bounce, get_easing
# Dependencies: Internal: None; External: numpy; Providers: None
# Exposes: linear, ease_in, ease_out, ease_in_out, ease_out_cubic, ease_out_back, ease_out_elastic, spring, bounce, get_easing, EASING_NAMES
# Configuration: None
from __future__ import annotations

import logging
from collections.abc import Callable

import numpy as np

logger = logging.getLogger(__name__)

# Type alias for easing functions: accept scalar or ndarray, return same shape
EasingFn = Callable[[float | np.ndarray], float | np.ndarray]


def linear(t: float | np.ndarray) -> float | np.ndarray:
    """Linear interpolation — no easing.

    Args:
        t: Normalized time value(s) in [0, 1].

    Returns:
        Same value as input.
    """
    return t


def ease_in(t: float | np.ndarray) -> float | np.ndarray:
    """Quadratic ease-in — slow start, fast end.

    Args:
        t: Normalized time value(s) in [0, 1].

    Returns:
        Eased value(s).
    """
    return t * t


def ease_out(t: float | np.ndarray) -> float | np.ndarray:
    """Quadratic ease-out — fast start, slow end.

    Args:
        t: Normalized time value(s) in [0, 1].

    Returns:
        Eased value(s).
    """
    return 1.0 - (1.0 - t) * (1.0 - t)


def ease_in_out(t: float | np.ndarray) -> float | np.ndarray:
    """Quadratic ease-in-out — slow at both ends.

    Args:
        t: Normalized time value(s) in [0, 1].

    Returns:
        Eased value(s).
    """
    t = np.asarray(t, dtype=float)
    return np.where(t < 0.5, 2.0 * t * t, 1.0 - 2.0 * (1.0 - t) ** 2)


def ease_out_cubic(t: float | np.ndarray) -> float | np.ndarray:
    """Cubic ease-out — snappier deceleration than quadratic.

    Args:
        t: Normalized time value(s) in [0, 1].

    Returns:
        Eased value(s).
    """
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t: float | np.ndarray, overshoot: float = 1.70158) -> float | np.ndarray:
    """Ease-out with back overshoot — slightly exceeds 1.0 then settles.

    Args:
        t: Normalized time value(s) in [0, 1].
        overshoot: Amount of overshoot; default 1.70158 is the CSS standard.

    Returns:
        Eased value(s) which may exceed 1.0 during overshoot.
    """
    c1 = overshoot
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


def ease_out_elastic(
    t: float | np.ndarray,
    amplitude: float = 1.0,
    period: float = 0.3,
) -> float | np.ndarray:
    """Elastic ease-out — oscillates past the end value before settling.

    Args:
        t: Normalized time value(s) in [0, 1].
        amplitude: Oscillation amplitude (>= 1.0).
        period: Oscillation period.

    Returns:
        Eased value(s).
    """
    t = np.asarray(t, dtype=float)
    result = np.where(
        t == 0.0,
        0.0,
        np.where(
            t == 1.0,
            1.0,
            amplitude
            * np.power(2.0, -10.0 * t)
            * np.sin((t - period / 4.0) * (2.0 * np.pi) / period)
            + 1.0,
        ),
    )
    return result


def spring(
    t: float | np.ndarray,
    frequency: float = 8.0,
    damping: float = 3.0,
) -> float | np.ndarray:
    """Damped sine spring — oscillates then settles at 1.0.

    Args:
        t: Normalized time value(s) in [0, 1].
        frequency: Spring oscillation frequency (higher = faster oscillations).
        damping: Damping coefficient (higher = faster decay).

    Returns:
        Eased value(s).
    """
    t = np.asarray(t, dtype=float)
    return 1.0 - np.exp(-damping * t) * np.cos(frequency * t)


def bounce(t: float | np.ndarray) -> float | np.ndarray:
    """Ease-out bounce — simulates ball bouncing with decreasing height.

    Args:
        t: Normalized time value(s) in [0, 1].

    Returns:
        Eased value(s) in [0, 1].
    """
    t = np.asarray(t, dtype=float)

    def _bounce_scalar(x: float) -> float:
        n1 = 7.5625
        d1 = 2.75
        if x < 1.0 / d1:
            return n1 * x * x
        elif x < 2.0 / d1:
            x -= 1.5 / d1
            return n1 * x * x + 0.75
        elif x < 2.5 / d1:
            x -= 2.25 / d1
            return n1 * x * x + 0.9375
        else:
            x -= 2.625 / d1
            return n1 * x * x + 0.984375

    if t.ndim == 0:
        return float(_bounce_scalar(float(t)))
    return np.array([_bounce_scalar(float(v)) for v in t.flat]).reshape(t.shape)


# Mapping from CSS-like string names to callables
_EASING_MAP: dict[str, EasingFn] = {
    "linear": linear,
    "ease-in": ease_in,
    "ease-out": ease_out,
    "ease-in-out": ease_in_out,
    "ease-out-cubic": ease_out_cubic,
    "ease-out-back": ease_out_back,
    "ease-out-elastic": ease_out_elastic,
    "spring": spring,
    "bounce": bounce,
}

EASING_NAMES: list[str] = list(_EASING_MAP.keys())


def get_easing(name: str) -> EasingFn:
    """Retrieve an easing function by name.

    Args:
        name: One of the EASING_NAMES strings.

    Returns:
        The corresponding easing callable.

    Raises:
        KeyError: If the name is not recognised.
    """
    if name not in _EASING_MAP:
        valid = ", ".join(f"'{n}'" for n in EASING_NAMES)
        raise KeyError(f"Unknown easing '{name}'. Valid names: {valid}")
    return _EASING_MAP[name]
