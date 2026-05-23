# Filepath: text_fx/exceptions.py
# Condensed Description: All custom exception classes for the text-fx library
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: TextFxError, UnknownEffectError, EffectMappingError, EngineError, CompositorError, TypographyError, ZeroDurationError
# Dependencies: Internal: None; External: stdlib; Providers: None
# Exposes: TextFxError, UnknownEffectError, EffectMappingError, EngineError, CompositorError, TypographyError, ZeroDurationError
# Configuration: None
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class TextFxError(Exception):
    """Base class for all text-fx library errors."""


class UnknownEffectError(TextFxError):
    """Raised when a requested effect slug or name is not in the catalog.

    Args:
        slug: The requested slug or name that was not found.
        suggestions: A list of close matches from the catalog.
    """

    def __init__(self, slug: str, suggestions: list[str] | None = None) -> None:
        self.slug = slug
        self.suggestions = suggestions or []
        if self.suggestions:
            suggestion_str = ", ".join(f"'{s}'" for s in self.suggestions[:3])
            msg = f"Unknown effect: '{slug}'. Did you mean: {suggestion_str}?"
        else:
            msg = f"Unknown effect: '{slug}'. Use list_effects() to see available effects."
        super().__init__(msg)


class EffectMappingError(TextFxError):
    """Raised when the effect mapping JSON is malformed or incomplete.

    Args:
        slug: The slug that failed to resolve.
        detail: Additional context about the failure.
    """

    def __init__(self, slug: str, detail: str = "") -> None:
        self.slug = slug
        msg = f"Effect mapping error for '{slug}'"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)


class EngineError(TextFxError):
    """Raised when an engine fails to render frames.

    Args:
        engine_name: The name of the engine that failed.
        detail: Additional context about the failure.
    """

    def __init__(self, engine_name: str, detail: str = "") -> None:
        self.engine_name = engine_name
        msg = f"Engine '{engine_name}' failed"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)


class EngineUnavailableError(TextFxError):
    """Raised when a required engine or its dependencies are not available.

    Args:
        effect: The effect that requires the engine.
        engine_name: The engine that is not available.
        fix: Installation hint.
    """

    def __init__(self, effect: str, engine_name: str, fix: str = "") -> None:
        self.effect = effect
        self.engine_name = engine_name
        msg = f"Engine '{engine_name}' required for effect '{effect}' is not available"
        if fix:
            msg = f"{msg}. {fix}"
        super().__init__(msg)


class CompositorError(TextFxError):
    """Raised when ffmpeg compositing fails.

    Args:
        detail: Details about the ffmpeg failure.
        returncode: The ffmpeg process return code if available.
        stderr: The ffmpeg stderr output if available.
    """

    def __init__(
        self,
        detail: str = "",
        returncode: int | None = None,
        stderr: str | None = None,
    ) -> None:
        self.returncode = returncode
        self.stderr = stderr
        msg = "Compositor error"
        if detail:
            msg = f"{msg}: {detail}"
        if returncode is not None:
            msg = f"{msg} (ffmpeg exit code {returncode})"
        super().__init__(msg)


class TypographyError(TextFxError):
    """Raised when text rendering fails, e.g. font load failure after all fallbacks exhausted.

    Args:
        detail: Context about what was tried.
    """

    def __init__(self, detail: str = "") -> None:
        msg = "Typography error"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)


class ZeroDurationError(TextFxError):
    """Raised when duration is zero or negative.

    Args:
        duration: The invalid duration value provided.
    """

    def __init__(self, duration: float) -> None:
        self.duration = duration
        super().__init__(
            f"Effect duration must be positive, got {duration}. "
            "Set duration > 0 in TextEffectConfig."
        )
