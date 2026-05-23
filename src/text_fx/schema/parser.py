# Filepath: text_fx/schema/parser.py
# Condensed Description: Parses LLM free-text response into a validated TextEffectConfig
# Architecture Layer: Schema
# Environment: Both
# Script Hierarchy: parse_llm_response
# Dependencies: Internal: config.py, catalog/loader.py, resolver.py; External: pydantic, re, json; Providers: None
# Exposes: parse_llm_response
# Configuration: None
from __future__ import annotations

import json
import logging
import re
from typing import Any

from text_fx.catalog.loader import load_catalog
from text_fx.config import TextEffectConfig
from text_fx.exceptions import UnknownEffectError

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> str | None:
    """Extract the first JSON object or array from a text string.

    Searches for the outermost `{...}` block.

    Args:
        text: Raw LLM response text.

    Returns:
        JSON string if found, None otherwise.
    """
    # Try code fences first
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1)

    # Try bare JSON object
    obj_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if obj_match:
        return obj_match.group(0)

    return None


def _normalize_effect_slug(slug_candidate: str) -> str:
    """Normalize a possibly sloppy slug to the closest catalog slug.

    Args:
        slug_candidate: Slug string from LLM output.

    Returns:
        Normalized slug string.
    """
    from text_fx.resolver import _normalize_slug

    catalog = load_catalog()
    try:
        return _normalize_slug(slug_candidate, catalog)
    except UnknownEffectError:
        # Return as-is; downstream validation will handle it
        logger.debug(f"Could not normalize LLM slug '{slug_candidate}'")
        return slug_candidate


def parse_llm_response(llm_text: str) -> TextEffectConfig:
    """Parse an LLM free-text response into a validated TextEffectConfig.

    Handles:
    - JSON embedded in prose
    - JSON in markdown code fences
    - Partial fields (missing fields get defaults)
    - Slug normalization / fuzzy matching

    Args:
        llm_text: Raw text from an LLM response.

    Returns:
        Validated TextEffectConfig instance.

    Raises:
        ValueError: If no parseable JSON is found and the text cannot be interpreted.
    """
    # Try to extract JSON
    json_str = _extract_json(llm_text)
    if json_str is None:
        logger.warning("No JSON found in LLM response; returning default TextEffectConfig")
        return TextEffectConfig()

    try:
        raw: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.warning(f"Failed to parse extracted JSON: {exc}; returning default")
        return TextEffectConfig()

    # Normalize effect slug if present
    if "effect" in raw:
        raw["effect"] = _normalize_effect_slug(str(raw["effect"]))

    # Remove unknown fields that would cause Pydantic extra="forbid" to fail
    known_fields = set(TextEffectConfig.model_fields.keys())
    filtered: dict[str, Any] = {k: v for k, v in raw.items() if k in known_fields}

    try:
        return TextEffectConfig(**filtered)
    except Exception as exc:
        logger.warning(
            f"TextEffectConfig validation failed: {exc}; using defaults for failed fields"
        )
        # Try field-by-field to salvage valid parts
        valid_fields: dict[str, Any] = {}
        for key, value in filtered.items():
            try:
                test_kwargs = {key: value}
                TextEffectConfig(**test_kwargs)
                valid_fields[key] = value
            except Exception:
                logger.debug(f"Skipping invalid field '{key}' = {value!r}")
        try:
            return TextEffectConfig(**valid_fields)
        except Exception:
            return TextEffectConfig()
