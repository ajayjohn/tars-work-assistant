"""Migration v3.3.0-rebuild-alias-registry

Recompute ``_system/alias-registry.md`` from the vault's frontmatter.

Rationale: the alias registry was manually maintained and could drift from
the ``aliases:`` frontmatter on entity notes.  This migration scans all
entity notes under ``memory/`` (people, vendors, competitors, products,
initiatives, decisions, org-context), extracts ``aliases`` from frontmatter,
and rebuilds the registry table.  Existing manual entries that have no
backing note are preserved in a ``## Manual entries`` section so the user
can review and clean them up later.

Contract: run(vault, dry_run) as required by scripts/run-migrations.py.
"""

from pathlib import Path
import re

_REGISTRY_PATH = "_system/alias-registry.md"

# Entity folders that carry aliases worth indexing.
_ENTITY_DIRS = [
    "memory/people",
    "memory/vendors",
    "memory/competitors",
    "memory/products",
    "memory/initiatives",
    "memory/decisions",
    "memory/org-context",
]

# Map folder name → entity type for the registry.
_DIR_TO_TYPE = {
    "people": "person",
    "vendors": "vendor",
    "competitors": "competitor",
    "products": "product",
    "initiatives": "initiative",
    "decisions": "decision",
    "org-context": "org-context",
}

# Regex patterns for frontmatter extraction (stdlib-only, no YAML lib).
_FM_OPEN = re.compile(r"^---\s*$")
_ALIASES_LINE = re.compile(r"^\s*aliases\s*:\s*\[(.+?)\]\s*$")
_ALIASES_BLOCK_START = re.compile(r"^\s*aliases\s*:\s*$")
_ALIASES_BLOCK_ITEM = re.compile(r"^\s*-\s+(.+)$")


def _extract_frontmatter_block(text: str) -> str | None:
    """Return the YAML frontmatter block (between --- markers), or None."""
    lines = text.splitlines()
    if not lines or not _FM_OPEN.match(lines[0]):
        return None
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if _FM_OPEN.match(line):
            end = i
            break
    if end is None:
        return None
    return "\n".join(lines[1:end])


def _extract_aliases(fm: str) -> list[str]:
    """Parse aliases from a YAML frontmatter block (stdlib-only)."""
    aliases: list[str] = []
    lines = fm.splitlines()
    for i, line in enumerate(lines):
        # Inline array: aliases: [foo, bar, baz]
        m = _ALIASES_LINE.match(line)
        if m:
            raw = m.group(1)
            for part in raw.split(","):
                cleaned = part.strip().strip('"').strip("'").strip()
                if cleaned:
                    aliases.append(cleaned)
            return aliases

        # Block array: aliases:\n  - foo\n  - bar
        if _ALIASES_BLOCK_START.match(line):
            for j in range(i + 1, len(lines)):
                bm = _ALIASES_BLOCK_ITEM.match(lines[j])
                if bm:
                    cleaned = bm.group(1).strip().strip('"').strip("'").strip()
                    if cleaned:
                        aliases.append(cleaned)
                else:
                    break
            return aliases

    return aliases


def _extract_title(path: Path) -> str:
    """Derive the canonical name from the filename stem."""
    stem = path.stem
    # Convert slug to title case: jane-smith -> Jane Smith
    return stem.replace("-", " ").title()


def _scan_entities(vault: Path) -> list[dict]:
    """Walk entity directories and extract alias mappings."""
    entries: list[dict] = []
    for dir_rel in _ENTITY_DIRS:
        entity_dir = vault / dir_rel
        if not entity_dir.is_dir():
            continue
        type_key = _DIR_TO_TYPE.get(entity_dir.name, entity_dir.name)
        for md_file in sorted(entity_dir.glob("*.md")):
            if md_file.name.startswith("_"):
                continue
            try:
                text = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
            fm = _extract_frontmatter_block(text)
            if fm is None:
                continue
            canonical = _extract_title(md_file)
            aliases = _extract_aliases(fm)
            rel_path = md_file.relative_to(vault).as_posix()
            entries.append({
                "canonical": canonical,
                "aliases": aliases,
                "type": type_key,
                "path": rel_path,
            })
    return entries


def _parse_existing_registry(text: str) -> list[dict]:
    """Parse an existing alias-registry.md table into row dicts."""
    rows: list[dict] = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and "Canonical" in stripped:
            in_table = True
            continue
        if stripped.startswith("|") and stripped.replace("|", "").replace("-", "").strip() == "":
            continue  # separator row
        if not stripped.startswith("|"):
            in_table = False
            continue
        if not in_table:
            continue
        cells = [c.strip() for c in stripped.split("|")]
        # cells[0] is empty (before first |), cells[-1] is empty (after last |)
        cells = [c for c in cells if c]
        if len(cells) >= 4:
            rows.append({
                "canonical": cells[0],
                "aliases": cells[1],
                "type": cells[2],
                "path": cells[3],
            })
    return rows


def _build_registry_content(entries: list[dict], manual_rows: list[dict]) -> str:
    """Render the alias-registry.md content."""
    lines = [
        "---",
        "tags: [tars/system]",
        "tars-description: Alias registry — auto-rebuilt from vault frontmatter by v3.3.0 migration",
        "---",
        "",
        "# Alias registry",
        "",
        "Canonical name → aliases mapping for name resolution. This file is rebuilt",
        "from entity-note `aliases:` frontmatter by `scripts/migrations/v3.3.0-rebuild-alias-registry.py`.",
        "To add aliases, edit the `aliases:` field on the entity note and re-run the migration",
        "or let the MCP server sync on next write.",
        "",
        "| Canonical | Aliases | Type | Path |",
        "|-----------|---------|------|------|",
    ]
    for e in entries:
        alias_str = ", ".join(e["aliases"]) if e["aliases"] else ""
        lines.append(f"| {e['canonical']} | {alias_str} | {e['type']} | {e['path']} |")

    if manual_rows:
        lines.append("")
        lines.append("## Manual entries")
        lines.append("")
        lines.append("These entries existed in the previous registry but have no backing entity note.")
        lines.append("Review and either create the entity note or remove the row.")
        lines.append("")
        lines.append("| Canonical | Aliases | Type | Path |")
        lines.append("|-----------|---------|------|------|")
        for r in manual_rows:
            lines.append(f"| {r['canonical']} | {r['aliases']} | {r['type']} | {r['path']} |")

    lines.append("")
    return "\n".join(lines)


def run(vault: Path, dry_run: bool = True) -> dict:
    """Rebuild alias-registry.md from vault entity frontmatter.

    Returns a result dict compatible with run-migrations.py expectations:
      {"status": "ok"|"skip"|"error", "changes": [...], "message": str}
    """
    # Scan all entity notes.
    entries = _scan_entities(vault)

    # Read existing registry for manual-entry preservation.
    registry_path = vault / _REGISTRY_PATH
    existing_rows: list[dict] = []
    if registry_path.is_file():
        try:
            existing_text = registry_path.read_text(encoding="utf-8")
            existing_rows = _parse_existing_registry(existing_text)
        except OSError:
            pass

    # Identify manual entries (in old registry but not backed by a scanned entity).
    scanned_paths = {e["path"] for e in entries}
    manual_rows = [r for r in existing_rows if r["path"] not in scanned_paths]

    new_content = _build_registry_content(entries, manual_rows)

    changes = [
        {
            "file": _REGISTRY_PATH,
            "action": "rebuild",
            "detail": f"Rebuilt from {len(entries)} entity notes ({len(manual_rows)} manual entries preserved)",
        }
    ]

    if dry_run:
        return {
            "status": "ok",
            "dry_run": True,
            "changes": changes,
            "message": f"Would rebuild {_REGISTRY_PATH} from {len(entries)} entity notes.",
            "skipped": 0,
        }

    try:
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        return {
            "status": "error",
            "changes": [],
            "message": f"Write failed: {exc}",
            "skipped": 0,
        }

    return {
        "status": "ok",
        "dry_run": False,
        "changes": changes,
        "message": f"Rebuilt {_REGISTRY_PATH} from {len(entries)} entity notes.",
        "skipped": 0,
    }
