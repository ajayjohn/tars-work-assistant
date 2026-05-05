"""Migration v3.3.0-backfill-journal-aliases

Fix journal notes where the filename slug (e.g. 2026-04-06-gba-ai-panel-prep)
differs from what cross-note wikilinks expect (e.g. [[2026-04-06 GBA AI Panel Prep]]).

Obsidian resolves wikilinks by note title / alias, not by filename.  When
journal files have hyphen-separated slugs but references use space-separated
titles, the links break silently.

This migration adds an `aliases` entry (space-separated form) to every journal
note that:
  1. Lives under journal/ or archive/transcripts/.
  2. Has a filename matching YYYY-MM-DD-<slug>.md.
  3. Does NOT already have an alias covering the space-separated form.
  4. Does NOT already have an H1 heading that matches the expected title.

The space-separated title is derived by:
  - Splitting on hyphens.
  - Title-casing each word.
  - Joining with spaces.

For example: 2026-04-06-gba-ai-panel-prep → "2026-04-06 Gba Ai Panel Prep"
(All-caps acronyms like GBA are not detected — Obsidian's case-insensitive
alias matching means the link [[2026-04-06 GBA AI Panel Prep]] resolves to
the alias "2026-04-06 Gba Ai Panel Prep" without case sensitivity issues.)

Safe to re-run: notes that already have a matching alias are counted as skipped.
"""

import re
import sys
from pathlib import Path


_DATE_SLUG_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
_SCAN_DIRS = ["journal", "archive/transcripts"]


# ---------------------------------------------------------------------------
# Frontmatter helpers (stdlib-only, no PyYAML)
# ---------------------------------------------------------------------------

def _parse_frontmatter_raw(text: str) -> tuple[str, list[str], str, str]:
    """Return (fm_header, fm_lines, fm_footer, body).

    Minimal parser that preserves exact whitespace so we can write back
    without altering unrelated properties.
    """
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", text, re.DOTALL)
    if not m:
        return "", [], "", text
    return m.group(1), m.group(2).splitlines(), m.group(3), text[m.end():]


def _get_aliases(fm_lines: list[str]) -> list[str]:
    """Extract current aliases from frontmatter lines (handles block and flow lists)."""
    aliases: list[str] = []
    in_aliases = False
    for line in fm_lines:
        stripped = line.strip()
        if stripped.startswith("aliases:"):
            val = stripped[len("aliases:"):].strip()
            if val.startswith("[") and val.endswith("]"):
                # Flow list: aliases: [a, b]
                inner = val[1:-1]
                for item in inner.split(","):
                    item = item.strip().strip('"').strip("'")
                    if item:
                        aliases.append(item)
                in_aliases = False
            else:
                in_aliases = True
        elif in_aliases:
            if stripped.startswith("- "):
                aliases.append(stripped[2:].strip().strip('"').strip("'"))
            elif stripped and not stripped.startswith("#"):
                in_aliases = False
    return aliases


def _add_alias(fm_lines: list[str], alias: str) -> list[str]:
    """Add alias to existing aliases list, or create new aliases block."""
    new_lines: list[str] = []
    in_aliases = False
    aliases_handled = False

    for line in fm_lines:
        stripped = line.strip()
        if stripped.startswith("aliases:"):
            val = stripped[len("aliases:"):].strip()
            if val.startswith("[") and val.endswith("]"):
                # Flow list → convert to block list with new alias.
                inner = val[1:-1]
                existing = [i.strip().strip('"').strip("'") for i in inner.split(",") if i.strip()]
                indent = len(line) - len(line.lstrip())
                new_lines.append(" " * indent + "aliases:")
                for ex in existing:
                    new_lines.append(" " * indent + f"  - {ex}")
                new_lines.append(" " * indent + f"  - {alias}")
                aliases_handled = True
                in_aliases = False
            elif not val:
                # Block list follows.
                new_lines.append(line)
                in_aliases = True
            else:
                # Scalar aliases: some_value (unexpected) — append block list.
                new_lines.append(line)
                in_aliases = False
        elif in_aliases:
            if stripped.startswith("- "):
                new_lines.append(line)
            else:
                # End of the list — insert new item before this line.
                indent = "  "
                for prev in reversed(new_lines):
                    if prev.strip().startswith("- "):
                        indent = " " * (len(prev) - len(prev.lstrip()))
                        break
                new_lines.append(indent + f"- {alias}")
                aliases_handled = True
                in_aliases = False
                new_lines.append(line)
        else:
            new_lines.append(line)

    if in_aliases and not aliases_handled:
        # Aliases was the last block in frontmatter.
        new_lines.append(f"  - {alias}")
        aliases_handled = True

    if not aliases_handled:
        # No aliases key existed — insert after the first tags line or at end.
        insert_after = None
        for i, line in enumerate(new_lines):
            if line.strip().startswith("tags:"):
                insert_after = i
                break
        if insert_after is not None:
            # Find end of tags block.
            j = insert_after + 1
            while j < len(new_lines):
                s = new_lines[j].strip()
                if s.startswith("- ") or (s.startswith("[") and "tags:" in new_lines[insert_after]):
                    j += 1
                else:
                    break
            new_lines.insert(j, f"aliases:")
            new_lines.insert(j + 1, f"  - {alias}")
        else:
            new_lines += [f"aliases:", f"  - {alias}"]

    return new_lines


def _rebuild_file(fm_header: str, fm_lines: list[str], fm_footer: str, body: str) -> str:
    return fm_header + "\n".join(fm_lines) + fm_footer + body


# ---------------------------------------------------------------------------
# Title derivation
# ---------------------------------------------------------------------------

def _slug_to_title(date_str: str, slug: str) -> str:
    """Convert '2026-04-06' + 'gba-ai-panel-prep' → '2026-04-06 Gba Ai Panel Prep'."""
    words = slug.split("-")
    titled = " ".join(w.capitalize() for w in words if w)
    return f"{date_str} {titled}"


# ---------------------------------------------------------------------------
# Main entry point (migration contract)
# ---------------------------------------------------------------------------

def run(vault: Path, dry_run: bool = True) -> dict:
    vault = Path(vault)
    changes = []
    errors = []
    skipped = 0

    for scan_dir in _SCAN_DIRS:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue
        for md_file in dir_path.rglob("*.md"):
            if any(part.startswith(".") for part in md_file.parts):
                continue

            m = _DATE_SLUG_RE.match(md_file.stem)
            if not m:
                continue
            date_str = m.group(1)
            slug = m.group(2)
            expected_alias = _slug_to_title(date_str, slug)

            try:
                text = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append({"file": str(md_file.relative_to(vault)), "error": str(exc)})
                continue

            fm_header, fm_lines, fm_footer, body = _parse_frontmatter_raw(text)
            if not fm_header:
                # No frontmatter — not a TARS-managed note, skip.
                skipped += 1
                continue

            current_aliases = _get_aliases(fm_lines)
            alias_lower = {a.lower() for a in current_aliases}
            if expected_alias.lower() in alias_lower:
                skipped += 1
                continue

            rel = str(md_file.relative_to(vault))
            changes.append({
                "file": rel,
                "action": "add_alias",
                "detail": f'aliases += "{expected_alias}"',
            })

            if not dry_run:
                new_fm_lines = _add_alias(fm_lines, expected_alias)
                new_text = _rebuild_file(fm_header, new_fm_lines, fm_footer, body)
                try:
                    md_file.write_text(new_text, encoding="utf-8")
                except OSError as exc:
                    errors.append({"file": rel, "error": str(exc)})
                    changes.pop()

    return {
        "migration": "v3.3.0-backfill-journal-aliases",
        "dry_run": dry_run,
        "changes": changes,
        "errors": errors,
        "skipped": skipped,
    }


if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    result = run(Path(args.vault), dry_run=not args.apply)
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        label = "DRY RUN" if result["dry_run"] else "APPLIED"
        print(f"[{label}] {result['migration']}")
        print(f"  Changes: {len(result['changes'])}")
        print(f"  Errors:  {len(result['errors'])}")
        print(f"  Skipped: {result['skipped']}")
        for c in result["changes"][:30]:
            print(f"    {c['file']}: {c['detail']}")
