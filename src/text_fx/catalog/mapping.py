# Filepath: text_fx/catalog/mapping.py
# Condensed Description: Loads effect_mapping.json; resolves slug to engine/base/params
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: MappingEntry, load_mapping, resolve_slug
# Dependencies: Internal: exceptions.py; External: stdlib json/importlib.resources; Providers: None
# Exposes: MappingEntry, load_mapping, resolve_slug
# Configuration: None
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any

from text_fx.exceptions import EffectMappingError, UnknownEffectError

logger = logging.getLogger(__name__)


@dataclass
class MappingEntry:
    """Represents one slug's engine routing in effect_mapping.json.

    Attributes:
        slug: Effect slug.
        base_engine: Base engine name (e.g. 'fade', 'glow').
        engine_bucket: Engine category bucket (e.g. 'alpha', 'neon').
        params: Default parameters dict for this mapping.
        prefer_engine: Engine preference hint ('auto', 'web_overlay', etc.).
    """

    slug: str
    base_engine: str
    engine_bucket: str
    params: dict[str, Any]
    prefer_engine: str = "auto"


@lru_cache(maxsize=1)
def load_mapping() -> dict[str, MappingEntry]:
    """Load the effect_mapping.json and return a slug-to-MappingEntry dict.

    Returns:
        Dictionary mapping slug → MappingEntry.

    Raises:
        EffectMappingError: If the mapping file is missing or malformed.
    """
    try:
        with resources.open_text("text_fx.data", "effect_mapping.json", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise EffectMappingError(
            "effect_mapping.json",
            detail=f"Mapping file not found in package data. Run scripts/generate_mapping.py: {exc}",
        ) from exc
    except json.JSONDecodeError as exc:
        raise EffectMappingError(
            "effect_mapping.json",
            detail=f"Mapping JSON is malformed: {exc}",
        ) from exc

    mapping: dict[str, MappingEntry] = {}
    for item in data:
        slug = item.get("slug")
        if not slug:
            continue
        mapping[slug] = MappingEntry(
            slug=slug,
            base_engine=item.get("base_engine", "fade"),
            engine_bucket=item.get("engine_bucket", "alpha"),
            params=item.get("params", {}),
            prefer_engine=item.get("prefer_engine", "auto"),
        )

    logger.debug(f"Loaded {len(mapping)} effect mapping entries")
    return mapping


def resolve_slug(slug: str, mapping: dict[str, MappingEntry]) -> MappingEntry:
    """Resolve a slug to its MappingEntry.

    Args:
        slug: Effect slug to look up.
        mapping: The loaded mapping dict from load_mapping().

    Returns:
        MappingEntry for the slug.

    Raises:
        UnknownEffectError: If the slug is not in the mapping (with fuzzy suggestions).
    """
    if slug in mapping:
        return mapping[slug]

    # Fuzzy suggestions
    suggestions = _fuzzy_suggest(slug, list(mapping.keys()))
    raise UnknownEffectError(slug, suggestions)


def _fuzzy_suggest(query: str, candidates: list[str], max_results: int = 3) -> list[str]:
    """Generate fuzzy-match suggestions for an unknown slug.

    Uses simple substring containment and character overlap scoring.

    Args:
        query: The unknown slug.
        candidates: List of known slugs.
        max_results: Maximum number of suggestions.

    Returns:
        Sorted list of closest candidate strings.
    """
    query_lower = query.lower().replace("_", " ")
    scored: list[tuple[float, str]] = []
    for c in candidates:
        c_lower = c.lower().replace("_", " ")
        # Substring containment
        if query_lower in c_lower or c_lower in query_lower:
            scored.append((0.9, c))
            continue
        # Word overlap
        q_words = set(query_lower.split())
        c_words = set(c_lower.split())
        overlap = len(q_words & c_words)
        if overlap > 0:
            score = overlap / max(len(q_words | c_words), 1)
            scored.append((score, c))
        else:
            # Character overlap
            q_chars = set(query_lower)
            c_chars = set(c_lower)
            char_score = len(q_chars & c_chars) / max(len(q_chars | c_chars), 1)
            if char_score > 0.5:
                scored.append((char_score * 0.3, c))

    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:max_results]]
