"""Centralized wikilink formation.

Skills should never hand-form ``[[...]]`` from raw text. They call
:func:`format_wikilink` (directly in tests, or via the MCP tool wrapper at
``tools/format_wikilink.py``) and trust the result.

The pipeline is documented in the v3.2 plan §R8 and is intentionally
deterministic: same vault state + same input always returns the same dict.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import alias_registry
from .sanitize import normalize_text, sanitize_basename


# Folders we scan when the alias registry has no entry — these are the
# canonical homes for entity notes per CLAUDE.md.
_ENTITY_FOLDERS: tuple[str, ...] = (
    "memory/people",
    "memory/vendors",
    "memory/competitors",
    "memory/products",
    "memory/initiatives",
    "memory/decisions",
    "memory/org-context",
)


def _vault_basenames(vault: Path) -> dict[str, list[str]]:
    """Map normalized-lowercase basename → [actual basenames] across entity folders.

    Two real files might share a normalized form (case variants, smart-quote
    variants); we keep both so the caller can decide whether it's a
    disambiguation case or a true single match.
    """
    out: dict[str, list[str]] = {}
    for folder in _ENTITY_FOLDERS:
        root = vault / folder
        if not root.is_dir():
            continue
        for md in root.rglob("*.md"):
            base = md.stem
            key = normalize_text(base).lower()
            if not key:
                continue
            out.setdefault(key, []).append(base)
    return out


def _build_link(basename: str, display_text: str) -> str:
    """Render ``[[basename]]`` or ``[[basename|display]]`` based on equality."""
    if display_text and display_text != basename:
        return f"[[{basename}|{display_text}]]"
    return f"[[{basename}]]"


def format_wikilink(text: str, *, vault: str | Path, kind: str | None = None) -> dict[str, Any]:
    """Resolve ``text`` into an Obsidian-safe wikilink.

    Returns one of:

    * ``{status: "resolved", link, basename, display, source}`` — high-confidence match.
      ``source`` is one of ``"alias-registry" | "vault-file" | "new"`` and tells the
      caller whether the returned basename is already a real file.
    * ``{status: "disambiguation_needed", candidates: [...]}`` — multiple
      registry entries or vault files match. ``candidates`` items are
      ``{basename, source, kind}``.
    * ``{status: "new_entity", basename, link}`` — no match anywhere; the
      returned ``link`` points at a sanitized basename the caller may create.
    * ``{status: "error", reason}`` — input was empty or unsalvageable after
      sanitization (only happens for whitespace / pure-symbol input).
    """
    if not isinstance(text, str):
        return {"status": "error", "reason": "text must be a string"}

    display = normalize_text(text)
    if not display:
        return {"status": "error", "reason": "text is empty after normalization"}

    sanitized = sanitize_basename(display)
    if not sanitized:
        return {
            "status": "error",
            "reason": "text reduces to empty after stripping illegal characters",
        }

    vault_p = Path(vault).expanduser().resolve()

    # 1. Alias registry — exact (normalized) lookup.
    entries = alias_registry.lookup(vault_p, display, kind_hint=kind)
    if entries:
        # Multiple ambiguous entries → caller chooses.
        if len(entries) > 1:
            return {
                "status": "disambiguation_needed",
                "candidates": [
                    {"basename": e.canonical, "source": "alias-registry", "kind": e.kind}
                    for e in entries
                ],
            }
        canonical = entries[0].canonical
        return {
            "status": "resolved",
            "link": _build_link(canonical, display),
            "basename": canonical,
            "display": display,
            "source": "alias-registry",
        }

    # 2. Vault file lookup — match by normalized basename across entity folders.
    files_map = _vault_basenames(vault_p)
    key = normalize_text(display).lower()
    matches = files_map.get(key, [])
    if len(matches) == 1:
        canonical = matches[0]
        return {
            "status": "resolved",
            "link": _build_link(canonical, display),
            "basename": canonical,
            "display": display,
            "source": "vault-file",
        }
    if len(matches) > 1:
        # De-dupe identical basenames (same file referenced from multiple paths
        # is unlikely, but be safe).
        unique = sorted(set(matches))
        if len(unique) == 1:
            canonical = unique[0]
            return {
                "status": "resolved",
                "link": _build_link(canonical, display),
                "basename": canonical,
                "display": display,
                "source": "vault-file",
            }
        return {
            "status": "disambiguation_needed",
            "candidates": [
                {"basename": b, "source": "vault-file", "kind": ""} for b in unique
            ],
        }

    # 3. No match — return a new-entity proposal so the caller can decide
    # whether to create the underlying note or fall back to plain text.
    return {
        "status": "new_entity",
        "basename": sanitized,
        "link": _build_link(sanitized, display),
    }
