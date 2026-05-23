# Filepath: text_fx/catalog/loader.py
# Condensed Description: Loads and validates effects_catalog.json; provides typed catalog entries
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: CatalogEntry, load_catalog
# Dependencies: Internal: exceptions.py; External: stdlib json/importlib.resources; Providers: None
# Exposes: CatalogEntry, load_catalog
# Configuration: None
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

from text_fx.exceptions import EffectMappingError

logger = logging.getLogger(__name__)


@dataclass
class CatalogEntry:
    """Represents one entry in the effects catalog.

    Attributes:
        slug: URL-safe identifier, e.g. 'neon_glow_text'.
        name: Human-readable display name, e.g. 'Neon Glow Text'.
        categories: List of category strings.
        description: Short description of the effect.
        implementation_note: Optional technical note.
    """

    slug: str
    name: str
    categories: list[str]
    description: str
    implementation_note: str = ""


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, CatalogEntry]:
    """Load and validate the effects catalog JSON.

    The catalog is read from the package data directory using importlib.resources
    so it works in both editable installs and installed wheels.

    Returns:
        Dictionary mapping slug → CatalogEntry for all 120 entries.

    Raises:
        EffectMappingError: If the catalog file is missing or malformed.
    """
    try:
        with resources.open_text("text_fx.data", "effects_catalog.json", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise EffectMappingError(
            "effects_catalog.json",
            detail=f"Catalog file not found in package data: {exc}",
        ) from exc
    except json.JSONDecodeError as exc:
        raise EffectMappingError(
            "effects_catalog.json",
            detail=f"Catalog JSON is malformed: {exc}",
        ) from exc

    transitions = data.get("transitions", [])
    catalog: dict[str, CatalogEntry] = {}

    for entry_data in transitions:
        slug = entry_data.get("slug")
        if not slug:
            logger.warning(f"Catalog entry missing 'slug' field: {entry_data}")
            continue
        catalog[slug] = CatalogEntry(
            slug=slug,
            name=entry_data.get("name", slug),
            categories=entry_data.get("categories", []),
            description=entry_data.get("description", ""),
            implementation_note=entry_data.get("implementation_note", ""),
        )

    logger.debug(f"Loaded {len(catalog)} catalog entries")
    return catalog
