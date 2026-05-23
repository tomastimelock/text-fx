# Filepath: text_fx/api.py
# Condensed Description: Primary public API — apply_text_effect, apply_text_sequence, render_overlay, list_effects, list_categories, get_effect_info
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: apply_text_effect, apply_text_sequence, render_overlay, list_effects, list_categories, get_effect_info
# Dependencies: Internal: config.py, resolver.py, typography/renderer.py, engines/base.py, compositor.py, catalog/loader.py, catalog/mapping.py, exceptions.py; External: tempfile, pathlib; Providers: None
# Exposes: apply_text_effect, apply_text_sequence, render_overlay, list_effects, list_categories, get_effect_info
# Configuration: None
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from text_fx.catalog.loader import load_catalog
from text_fx.catalog.mapping import load_mapping
from text_fx.compositor import composite_overlay, probe_video
from text_fx.config import TextEffectConfig
from text_fx.resolver import resolve_effect
from text_fx.typography.renderer import render_text

logger = logging.getLogger(__name__)


def apply_text_effect(
    video: str | Path,
    text: str,
    effect: str,
    output: str | Path,
    duration: float = 2.0,
    start_time: float = 0.0,
    config: TextEffectConfig | None = None,
    **kwargs: Any,
) -> Path:
    """Apply a named text effect to a video file.

    Orchestrates the full pipeline: typography → engine → compositor.

    Args:
        video: Path to the input video file.
        text: Text string to render and animate.
        effect: Effect slug or display name (e.g. 'neon_glow_text').
        output: Destination path for the output video.
        duration: Effect duration in seconds (default 2.0).
        start_time: When the effect starts in the video (default 0.0).
        config: Optional TextEffectConfig override. If None, a default config is built.
        **kwargs: Additional fields passed to TextEffectConfig if config is None.

    Returns:
        Path to the composited output video file.

    Raises:
        ZeroDurationError: If duration is 0 or negative.
        UnknownEffectError: If the effect slug/name is not in the catalog.
    """
    video = Path(video)
    output = Path(output)

    if config is None:
        config_kwargs = {
            "text": text,
            "effect": effect,
            "duration": duration,
            "start_time": start_time,
            **kwargs,
        }
        config = TextEffectConfig(**config_kwargs)
    else:
        # Ensure config has the right text/effect fields
        if not config.text:
            config = config.model_copy(update={"text": text})
        if config.effect != effect:
            config = config.model_copy(update={"effect": effect})

    # Probe video for canvas dimensions
    try:
        video_info = probe_video(video)
        canvas_size = (video_info["width"], video_info["height"])
        fps = int(video_info.get("fps", 30))
    except Exception as exc:
        logger.warning(f"Could not probe video '{video}': {exc}. Using defaults 1920x1080@30fps.")
        canvas_size = (1920, 1080)
        fps = 30

    # Render text to static RGBA image
    text_image = render_text(config.text, config)

    # Resolve engine and params
    engine, params = resolve_effect(config.effect, config)

    # Render overlay to a temporary WebM
    with tempfile.TemporaryDirectory() as tmpdir:
        overlay_path = Path(tmpdir) / "overlay.webm"
        engine.render_effect(
            text_image=text_image,
            params=params,
            config=config,
            duration=config.duration,
            fps=fps,
            canvas_size=canvas_size,
            output=overlay_path,
        )

        # Composite onto base video
        end_time = config.start_time + config.duration
        composite_overlay(
            base_video=video,
            overlay=overlay_path,
            start_time=config.start_time,
            end_time=end_time,
            output=output,
            video_codec=config.video_codec,
            audio_codec=config.audio_codec,
        )

    logger.info(f"Applied effect '{effect}' to '{video}' → '{output}'")
    return output


def apply_text_sequence(
    video: str | Path,
    effects: list[dict[str, Any]],
    output: str | Path,
) -> Path:
    """Apply a sequence of text effects to a video, chaining them in order.

    Args:
        video: Path to the input video file.
        effects: List of effect specification dicts, each with at minimum
                 'text', 'effect', 'start_time', 'duration' keys.
        output: Destination path for the output video.

    Returns:
        Path to the final composited output video.
    """
    video = Path(video)
    output = Path(output)

    if not effects:
        logger.warning(
            "apply_text_sequence called with empty effects list; copying input to output"
        )
        import shutil

        shutil.copy2(video, output)
        return output

    # Chain: each effect's output becomes next effect's input
    current_video = video

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, effect_spec in enumerate(effects):
            effect_spec = dict(effect_spec)
            text = effect_spec.pop("text", "")
            effect_name = effect_spec.pop("effect", "fade_in")
            duration = float(effect_spec.pop("duration", 2.0))
            start_time = float(effect_spec.pop("start_time", 0.0))

            is_last = i == len(effects) - 1
            next_output = output if is_last else Path(tmpdir) / f"seq_{i:04d}.mp4"

            apply_text_effect(
                video=current_video,
                text=text,
                effect=effect_name,
                output=next_output,
                duration=duration,
                start_time=start_time,
                **effect_spec,
            )
            current_video = next_output

    return output


def render_overlay(
    text: str,
    effect: str,
    width: int = 1920,
    height: int = 1080,
    duration: float = 2.0,
    fps: int = 30,
    output: str | Path | None = None,
    config: TextEffectConfig | None = None,
) -> Path:
    """Render a text effect to a transparent WebM overlay (no input video required).

    This is the function used by caption-cast and title-fx to obtain pre-rendered
    text overlays for their own compositing pipelines.

    Args:
        text: Text to render.
        effect: Effect slug or display name.
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        duration: Effect duration in seconds.
        fps: Output frame rate.
        output: Destination path; if None, uses a temp file.
        config: Optional TextEffectConfig override.

    Returns:
        Path to the .webm overlay file with alpha channel.
    """
    if output is None:
        fd, tmp_path = tempfile.mkstemp(suffix=".webm")
        import os

        os.close(fd)
        output = Path(tmp_path)
    else:
        output = Path(output)

    if config is None:
        config = TextEffectConfig(text=text, effect=effect, duration=duration)

    canvas_size = (width, height)
    text_image = render_text(config.text or text, config)
    engine, params = resolve_effect(effect, config)

    engine.render_effect(
        text_image=text_image,
        params=params,
        config=config,
        duration=duration,
        fps=fps,
        canvas_size=canvas_size,
        output=output,
    )

    logger.info(f"Rendered overlay for '{effect}' → '{output}'")
    return output


def list_effects(category: str | None = None) -> list[str]:
    """List all available effect slugs, optionally filtered by category.

    Args:
        category: If provided, return only effects in this category.

    Returns:
        Sorted list of effect slug strings.
    """
    catalog = load_catalog()
    if category is None:
        return sorted(catalog.keys())
    return sorted(slug for slug, entry in catalog.items() if category in entry.categories)


def list_categories() -> list[str]:
    """List all available effect category strings.

    Returns:
        Sorted list of category name strings.
    """
    catalog = load_catalog()
    categories: set[str] = set()
    for entry in catalog.values():
        categories.update(entry.categories)
    return sorted(categories)


def get_effect_info(effect: str) -> dict[str, Any]:
    """Get metadata for a named effect.

    Args:
        effect: Effect slug or display name.

    Returns:
        Dictionary with name, slug, categories, base_engine, params, duration_default.

    Raises:
        UnknownEffectError: If the effect is not in the catalog.
    """
    from text_fx.resolver import _normalize_slug

    catalog = load_catalog()
    slug = _normalize_slug(effect, catalog)
    entry = catalog[slug]

    try:
        mapping = load_mapping()
        map_entry = mapping.get(slug)
        base_engine = map_entry.base_engine if map_entry else "unknown"
        params = map_entry.params if map_entry else {}
        prefer_engine = map_entry.prefer_engine if map_entry else "auto"
    except Exception:
        base_engine = "unknown"
        params = {}
        prefer_engine = "auto"

    return {
        "name": entry.name,
        "slug": slug,
        "categories": entry.categories,
        "description": entry.description,
        "base_engine": base_engine,
        "params": params,
        "prefer_engine": prefer_engine,
        "duration_default": 2.0,
    }
