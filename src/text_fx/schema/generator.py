# Filepath: text_fx/schema/generator.py
# Condensed Description: Generates JSON schema for LLM use with all 120 effect slugs enumerated
# Architecture Layer: Schema
# Environment: Both
# Script Hierarchy: text_effect_schema, schema_json
# Dependencies: Internal: catalog/loader.py, config.py; External: pydantic, json; Providers: None
# Exposes: text_effect_schema, schema_json
# Configuration: None
from __future__ import annotations

import json
import logging
from typing import Any

from text_fx.catalog.loader import load_catalog
from text_fx.config import TextEffectConfig

logger = logging.getLogger(__name__)


def text_effect_schema() -> dict[str, Any]:
    """Generate a JSON schema dict for LLM-targeted text effect requests.

    Enumerates all 120 effect slugs from the catalog in the 'effect' field's enum.
    Merges with the TextEffectConfig pydantic JSON schema.

    Returns:
        JSON-serialisable schema dict.
    """
    catalog = load_catalog()
    all_slugs = sorted(catalog.keys())

    # Get pydantic schema
    base_schema = TextEffectConfig.model_json_schema()

    # Override 'effect' field to have a proper enum
    if "properties" in base_schema:
        base_schema["properties"]["effect"] = {
            "type": "string",
            "enum": all_slugs,
            "description": "Effect slug. Choose one of the 120 named effects.",
        }

    # Add catalog descriptions as $defs for reference
    effect_descriptions: dict[str, str] = {
        slug: entry.description for slug, entry in catalog.items()
    }

    # Build the final schema
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "TextEffectRequest",
        "description": (
            "Schema for requesting a text effect via the text-fx library. "
            f"There are {len(all_slugs)} named effects across 6 categories."
        ),
        "type": "object",
        "properties": base_schema.get("properties", {}),
        "required": ["text", "effect"],
        "additionalProperties": False,
        "$defs": {
            "effect_descriptions": effect_descriptions,
            "categories": {
                "basic_editing": "Fade, dissolve, typewriter and cascade reveals",
                "kinetic_typography": "Kinetic motion: slide, spring, bounce, spin, oscillate",
                "mask_reveal": "Mask-based reveals: wipe, radial, shaped, organic",
                "glitch_digital": "Digital glitch: RGB shift, slice corrupt, decode, scanline",
                "distortion_warp": "Distortion: sine warp, radial warp, displacement, motion blur, particle",
                "light_neon": "Light and neon: glow, sweep, shimmer, sparkle",
            },
        },
    }

    # Carry over required/defs from pydantic
    if "$defs" in base_schema:
        schema["$defs"].update(base_schema["$defs"])

    return schema


def schema_json(pretty: bool = False) -> str:
    """Serialise the text effect schema to a JSON string.

    Args:
        pretty: If True, indent with 2 spaces for readability.

    Returns:
        JSON string.
    """
    schema = text_effect_schema()
    indent = 2 if pretty else None
    return json.dumps(schema, indent=indent, ensure_ascii=False)
