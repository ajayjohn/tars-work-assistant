"""Frontmatter / schema validators.

Skeleton for Phase 1a. Full rules land in Phase 2 alongside skill rewiring.
"""
from typing import Any


TARS_PREFIX = "tars-"


def is_tars_managed_property(name: str) -> bool:
    """Return True if ``name`` is a tars-managed frontmatter key."""
    return name.startswith(TARS_PREFIX)


def validate_frontmatter_shape(frontmatter: dict[str, Any]) -> list[str]:
    """Return a list of human-readable errors; empty list means OK.

    Placeholder implementation — Phase 2 reads ``_system/schemas.yaml`` and
    enforces it here.
    """
    errors: list[str] = []
    if not isinstance(frontmatter, dict):
        errors.append("frontmatter must be a mapping")
    return errors
