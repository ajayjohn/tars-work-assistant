"""Frontmatter / schema / content validators."""
from __future__ import annotations

from typing import Any

from .sanitize import find_bad_wikilinks


TARS_PREFIX = "tars-"


def is_tars_managed_property(name: str) -> bool:
    """Return True if ``name`` is a tars-managed frontmatter key."""
    return name.startswith(TARS_PREFIX)


def validate_frontmatter_shape(frontmatter: dict[str, Any]) -> list[str]:
    """Return a list of human-readable errors; empty list means OK."""
    errors: list[str] = []
    if not isinstance(frontmatter, dict):
        errors.append("frontmatter must be a mapping")
    return errors


def validate_no_bad_wikilinks(content: str) -> list[str]:
    """Return error messages for any wikilink with smart quotes / illegal chars.

    Pure: takes text, returns one human-readable message per offender. Empty
    list means the content is clean. The pre-tool-use hook calls the same
    helper for defense-in-depth.
    """
    if not isinstance(content, str) or not content:
        return []
    findings = find_bad_wikilinks(content)
    if not findings:
        return []
    out: list[str] = []
    for item in findings:
        raw = item.get("raw", "")
        issue = item.get("issue", "")
        if issue == "smart_quote":
            out.append(
                f"wikilink [[{raw}]] contains smart quotes — normalize to straight "
                "quotes (use mcp__tars_vault__format_wikilink)"
            )
        elif issue == "illegal_char":
            out.append(
                f"wikilink [[{raw}]] contains characters Obsidian forbids in "
                'filenames (\\ / : * ? " < > |) — sanitize the basename'
            )
        elif issue == "empty":
            out.append(f"wikilink [[{raw}]] has an empty target")
        else:
            out.append(f"wikilink [[{raw}]] failed validation ({issue})")
    return out
