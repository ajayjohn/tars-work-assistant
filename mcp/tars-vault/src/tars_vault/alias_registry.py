"""Alias-registry parsing with file-mtime cache.

The registry lives at ``_system/alias-registry.md`` and contains markdown
tables under canonical section headers. This module reads those tables and
exposes a normalized ``alias → canonical-basename`` map plus a richer
``alias → [candidate, ...]`` view for disambiguation.

Format we recognize (lifted from the file's own examples):

  ## Ambiguous Names
  | Short Name | Default Resolution | Context Override |
  |-----------|-------------------|-----------------|
  | Dan       | [[Dan Rivera]]    | infrastructure → [[Dan Chen]] |

  ## Team Abbreviations
  | Abbreviation | Canonical |
  |--------------|-----------|
  | eng          | Engineering |

  ## Product Abbreviations
  | Abbreviation | Canonical |
  |--------------|-----------|
  | DP           | [[Data Platform]] |

Pure stdlib. Comment-only example rows (HTML comments) are ignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .sanitize import normalize_text, sanitize_basename


REGISTRY_RELATIVE = "_system/alias-registry.md"


def registry_path(vault: Path) -> Path:
    return Path(vault) / REGISTRY_RELATIVE


@dataclass
class AliasEntry:
    alias: str  # normalized form (smart-quote folded, whitespace collapsed, lowercased)
    canonical: str  # basename without .md
    kind: str = ""  # "ambiguous" | "team" | "product" | ""
    contexts: list[tuple[str, str]] = field(default_factory=list)  # [(context_keyword, canonical), ...]


_WIKILINK_INNER = re.compile(r"\[\[([^\[\]\n|]+)(?:\|[^\]]*)?\]\]")


def _strip_wikilink(value: str) -> str:
    value = value.strip()
    m = _WIKILINK_INNER.match(value)
    if m:
        return m.group(1).strip()
    return value


def _parse_context_overrides(cell: str) -> list[tuple[str, str]]:
    """Parse a "context_keyword → [[Name]]" list, comma- or semicolon-separated."""
    out: list[tuple[str, str]] = []
    cell = cell.strip()
    if not cell or cell.lower() in ("-", "—"):
        return out
    # Support multiple separators in one cell.
    for piece in re.split(r"[;,]", cell):
        piece = piece.strip()
        if not piece:
            continue
        # Accept both ASCII -> and unicode → arrow.
        m = re.match(r"^(.*?)\s*(?:->|→)\s*(.*)$", piece)
        if not m:
            continue
        keyword = normalize_text(m.group(1)).lower()
        canonical = _strip_wikilink(m.group(2))
        if keyword and canonical:
            out.append((keyword, canonical))
    return out


def _is_example_or_separator(row: list[str]) -> bool:
    """Drop header separator (---) rows and HTML-commented examples."""
    if not row:
        return True
    if all(re.match(r"^[-:\s]+$", c) for c in row):
        return True
    joined = " ".join(row)
    if "<!--" in joined or "-->" in joined:
        return True
    if joined.strip().lower().startswith("example"):
        return True
    return False


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.match(r"^[-:\s]+$", c) for c in cells)


def _parse_table(lines: list[str]) -> list[list[str]]:
    """Parse markdown tables out of ``lines``, dropping headers + examples.

    A header row is the row immediately preceding a separator row (``|---|``).
    """
    parsed: list[list[str]] = []
    for line in lines:
        line = line.rstrip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        parsed.append(cells)

    rows: list[list[str]] = []
    skip_next = False
    for i, cells in enumerate(parsed):
        if skip_next:
            skip_next = False
            continue
        if _is_separator_row(cells):
            # Separator itself is dropped; the row right before it was the
            # header, so retroactively drop the previous row from `rows`.
            if rows and parsed[i - 1] == rows[-1]:
                rows.pop()
            continue
        if _is_example_or_separator(cells):
            continue
        rows.append(cells)
    return rows


def _split_sections(text: str) -> dict[str, list[str]]:
    """Return {section_title_lower: [lines]}."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def parse_registry(text: str) -> list[AliasEntry]:
    sections = _split_sections(text)
    entries: list[AliasEntry] = []

    # Ambiguous Names: 3-column table with default + context overrides.
    for row in _parse_table(sections.get("ambiguous names", [])):
        if len(row) < 2:
            continue
        alias_raw, default_raw = row[0], row[1]
        alias = normalize_text(alias_raw).lower()
        canonical = _strip_wikilink(default_raw)
        if not alias or not canonical:
            continue
        contexts = _parse_context_overrides(row[2]) if len(row) >= 3 else []
        entries.append(AliasEntry(alias=alias, canonical=canonical, kind="ambiguous", contexts=contexts))

    # Team Abbreviations: 2-column.
    for row in _parse_table(sections.get("team abbreviations", [])):
        if len(row) < 2:
            continue
        alias = normalize_text(row[0]).lower()
        canonical = _strip_wikilink(row[1])
        if alias and canonical:
            entries.append(AliasEntry(alias=alias, canonical=canonical, kind="team"))

    # Product Abbreviations: 2-column.
    for row in _parse_table(sections.get("product abbreviations", [])):
        if len(row) < 2:
            continue
        alias = normalize_text(row[0]).lower()
        canonical = _strip_wikilink(row[1])
        if alias and canonical:
            entries.append(AliasEntry(alias=alias, canonical=canonical, kind="product"))

    return entries


# ---------------------------------------------------------------------------
# Cached loader (per-vault, mtime-keyed).
# ---------------------------------------------------------------------------


_CACHE: dict[Path, tuple[float, list[AliasEntry]]] = {}


def load_entries(vault: Path) -> list[AliasEntry]:
    """Return parsed registry entries, with file-mtime invalidation."""
    path = registry_path(vault)
    if not path.is_file():
        return []
    mtime = path.stat().st_mtime
    cached = _CACHE.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    entries = parse_registry(path.read_text(encoding="utf-8"))
    _CACHE[path] = (mtime, entries)
    return entries


def lookup(vault: Path, alias: str, kind_hint: str | None = None) -> list[AliasEntry]:
    """Return matching registry entries for ``alias``.

    Lookup is case-insensitive on the alias key. ``kind_hint`` (e.g.
    ``"product"``) restricts to entries declared with that kind. Returns an
    empty list when no match is found.
    """
    needle = normalize_text(alias).lower()
    if not needle:
        return []
    matches: list[AliasEntry] = []
    for entry in load_entries(vault):
        if entry.alias != needle:
            continue
        if kind_hint and entry.kind and entry.kind != kind_hint:
            continue
        matches.append(entry)
    return matches


def all_canonicals(vault: Path) -> set[str]:
    """Set of canonical basenames declared in the registry."""
    return {e.canonical for e in load_entries(vault)}
