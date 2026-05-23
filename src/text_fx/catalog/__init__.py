# Filepath: text_fx/catalog/__init__.py
# Condensed Description: Catalog package init; re-exports loader and mapping
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: load_catalog, load_mapping, CatalogEntry, MappingEntry
# Dependencies: Internal: catalog/loader.py, catalog/mapping.py; External: None; Providers: None
# Exposes: load_catalog, load_mapping, CatalogEntry, MappingEntry, resolve_slug
# Configuration: None
from __future__ import annotations

import logging

from text_fx.catalog.loader import CatalogEntry, load_catalog
from text_fx.catalog.mapping import MappingEntry, load_mapping, resolve_slug

logger = logging.getLogger(__name__)

__all__ = [
    "load_catalog",
    "load_mapping",
    "CatalogEntry",
    "MappingEntry",
    "resolve_slug",
]
