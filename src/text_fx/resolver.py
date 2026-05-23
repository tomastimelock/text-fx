# Filepath: text_fx/resolver.py
# Condensed Description: Effect slug/name resolution to engine instance and merged params
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: resolve_effect, suggest_similar
# Dependencies: Internal: catalog/loader.py, catalog/mapping.py, engines/__init__.py, config.py, exceptions.py; External: None; Providers: None
# Exposes: resolve_effect, suggest_similar
# Configuration: None
from __future__ import annotations

import logging
import warnings
from typing import Any

from text_fx.catalog.loader import CatalogEntry, load_catalog
from text_fx.catalog.mapping import load_mapping, resolve_slug
from text_fx.engines import get_engine
from text_fx.engines.base import Engine
from text_fx.exceptions import EffectMappingError, UnknownEffectError

logger = logging.getLogger(__name__)


def _normalize_slug(slug_or_name: str, catalog: dict[str, CatalogEntry]) -> str:
    """Normalize a slug or display name to a catalog slug.

    Tries exact slug match first, then display name match (case-insensitive),
    then underscore/space normalisation.

    Args:
        slug_or_name: Effect slug or display name.
        catalog: Loaded catalog dict.

    Returns:
        Matched catalog slug string.

    Raises:
        UnknownEffectError: If no match found.
    """
    # 1. Direct slug match
    if slug_or_name in catalog:
        return slug_or_name

    # 2. Name match (case-insensitive)
    name_lower = slug_or_name.lower().strip()
    for slug, entry in catalog.items():
        if entry.name.lower() == name_lower:
            return slug

    # 3. Normalized: spaces → underscores
    normalized = slug_or_name.lower().strip().replace(" ", "_").replace("-", "_")
    if normalized in catalog:
        return normalized

    # 4. Fuzzy suggestions
    suggestions = suggest_similar(slug_or_name, catalog)
    raise UnknownEffectError(slug_or_name, suggestions)


def suggest_similar(slug_or_name: str, catalog: dict[str, CatalogEntry]) -> list[str]:
    """Generate fuzzy-match slug suggestions for a query string.

    Args:
        slug_or_name: Unknown slug or name to match against.
        catalog: Loaded catalog.

    Returns:
        List of up to 3 closest slug strings.
    """
    query = slug_or_name.lower().replace("_", " ").replace("-", " ")
    scored: list[tuple[float, str]] = []
    for slug, entry in catalog.items():
        target_slug = slug.lower().replace("_", " ")
        target_name = entry.name.lower()

        # Substring match
        if query in target_slug or query in target_name:
            scored.append((0.95, slug))
            continue

        # Word overlap
        q_words = set(query.split())
        s_words = set(target_slug.split())
        n_words = set(target_name.split())
        overlap_s = len(q_words & s_words) / max(len(q_words | s_words), 1)
        overlap_n = len(q_words & n_words) / max(len(q_words | n_words), 1)
        score = max(overlap_s, overlap_n)

        if score > 0.2:
            scored.append((score, slug))
        else:
            # Character overlap fallback
            q_chars = set(query.replace(" ", ""))
            s_chars = set(target_slug.replace(" ", ""))
            char_score = len(q_chars & s_chars) / max(len(q_chars | s_chars), 1)
            if char_score > 0.6:
                scored.append((char_score * 0.3, slug))

    scored.sort(key=lambda x: -x[0])
    return [slug for _, slug in scored[:3]]


def resolve_effect(
    slug_or_name: str,
    config: Any,
) -> tuple[Engine, dict[str, Any]]:
    """Resolve an effect slug or name to an Engine instance and merged params.

    Resolution order:
    1. Normalize slug/name → catalog slug
    2. Load mapping entry → (base_engine, params, prefer_engine)
    3. If prefer_engine == 'web_overlay' and web_overlay is not installed,
       emit UserWarning and fall back to mapped engine
    4. Merge mapping params with config-level overrides
    5. Return (engine_instance, merged_params)

    Args:
        slug_or_name: Effect slug or display name.
        config: TextEffectConfig instance.

    Returns:
        Tuple of (Engine instance, merged params dict).

    Raises:
        UnknownEffectError: If slug/name is not in the catalog.
        EffectMappingError: If the slug has no mapping entry.
    """
    catalog = load_catalog()
    mapping = load_mapping()

    slug = _normalize_slug(slug_or_name, catalog)
    mapping_entry = resolve_slug(slug, mapping)

    base_engine_name = mapping_entry.base_engine
    prefer_engine = mapping_entry.prefer_engine

    # Check web_overlay availability
    if prefer_engine == "web_overlay" or (
        hasattr(config, "prefer_engine") and config.prefer_engine == "web_overlay"
    ):
        try:
            import web_overlay  # noqa: F401

            # Use web_overlay engine if available (future integration point)
            logger.debug(
                f"web_overlay available for '{slug}'; using PIL engine (web_overlay integration pending)"
            )
        except ImportError:
            warnings.warn(
                f"Effect '{slug}' prefers web_overlay for best quality, "
                f"but web_overlay is not installed. Using PIL fallback. "
                f"Install for best results: pip install text-fx[overlay]",
                UserWarning,
                stacklevel=3,
            )

    # Get engine
    try:
        engine = get_engine(base_engine_name)
    except KeyError as exc:
        raise EffectMappingError(
            slug,
            detail=f"Mapped engine '{base_engine_name}' is not in ENGINE_REGISTRY: {exc}",
        ) from exc

    # Merge params: mapping defaults overridden by config-level direction/intensity
    merged_params = dict(mapping_entry.params)

    # Apply config direction override if present
    if hasattr(config, "direction") and config.direction is not None:
        merged_params["direction"] = config.direction

    return engine, merged_params
