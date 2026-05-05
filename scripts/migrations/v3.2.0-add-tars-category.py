"""Migration v3.2.0-add-tars-category

Backfill the `tars-category` property on task notes that were created before
v3.2.0 introduced the field.

Assignment rule (from the backlog item):
  - active    — owner is the vault user AND the note has a tars-due date
  - delegated — owner is NOT the vault user AND the note has a tars-due date
  - backlog   — no tars-due date (regardless of owner)

The vault user is read from _system/config.md (tars-user-name or the first
person alias); falls back to "user" and "me" heuristics when unset.

Safe to re-run: notes that already have tars-category are counted as skipped
and never overwritten.
"""

import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Frontmatter helpers (stdlib-only)
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Both may be empty/None."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm: dict = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            if val.lower() in ("null", "~", ""):
                fm[key.strip()] = None
            elif val.lower() == "true":
                fm[key.strip()] = True
            elif val.lower() == "false":
                fm[key.strip()] = False
            else:
                fm[key.strip()] = val
    body = text[m.end():]
    return fm, body


def _serialize_frontmatter(original_text: str, new_key: str, new_val: str) -> str:
    """Insert new_key: new_val into the existing frontmatter block."""
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", original_text, re.DOTALL)
    if not m:
        return original_text
    header = m.group(1)
    body_fm = m.group(2)
    footer = m.group(3)
    rest = original_text[m.end():]
    new_fm = body_fm.rstrip() + f"\n{new_key}: {new_val}"
    return header + new_fm + footer + rest


# ---------------------------------------------------------------------------
# Vault-user resolution
# ---------------------------------------------------------------------------

def _resolve_vault_user(vault: Path) -> set[str]:
    """Return lower-cased identifiers that represent the vault owner."""
    identifiers: set[str] = {"user", "me", "self"}
    config_path = vault / "_system" / "config.md"
    if not config_path.is_file():
        return identifiers
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        return identifiers

    fm, _ = _parse_frontmatter(text)
    for key in ("tars-user-name", "tars-user", "tars-name"):
        val = fm.get(key)
        if val and isinstance(val, str):
            identifiers.add(val.strip().lower())
            # Also add first name alone.
            first = val.strip().split()[0].lower()
            if first:
                identifiers.add(first)

    # Also scan body for "Name: ..." patterns.
    for line in text.splitlines():
        m = re.match(r"^\s*(?:name|user)\s*[:\-]\s*(.+)$", line, re.IGNORECASE)
        if m:
            name = m.group(1).strip().lower()
            identifiers.add(name)
    return identifiers


# ---------------------------------------------------------------------------
# Category assignment
# ---------------------------------------------------------------------------

def _assign_category(fm: dict, vault_user_ids: set[str]) -> str:
    owner_raw = fm.get("tars-owner") or ""
    owner = str(owner_raw).strip().lower().strip("[]").strip()
    has_due = bool(fm.get("tars-due"))
    owner_is_user = owner in vault_user_ids or not owner

    if has_due and owner_is_user:
        return "active"
    if has_due and not owner_is_user:
        return "delegated"
    return "backlog"


# ---------------------------------------------------------------------------
# Main entry point (migration contract)
# ---------------------------------------------------------------------------

def run(vault: Path, dry_run: bool = True) -> dict:
    vault = Path(vault)
    vault_user_ids = _resolve_vault_user(vault)

    changes = []
    errors = []
    skipped = 0

    # Scan all notes tagged tars/task.
    for md_file in vault.rglob("*.md"):
        if any(part.startswith(".") for part in md_file.parts):
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append({"file": str(md_file.relative_to(vault)), "error": str(exc)})
            continue

        fm, _body = _parse_frontmatter(text)
        if not fm:
            continue

        tags = fm.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]
        if "tars/task" not in tags:
            continue

        # Already has the field — skip.
        if fm.get("tars-category") is not None:
            skipped += 1
            continue

        category = _assign_category(fm, vault_user_ids)
        rel = str(md_file.relative_to(vault))
        changes.append({
            "file": rel,
            "action": "add",
            "detail": f"tars-category: {category} (owner={fm.get('tars-owner') or 'unset'}, due={bool(fm.get('tars-due'))})",
        })

        if not dry_run:
            new_text = _serialize_frontmatter(text, "tars-category", category)
            try:
                md_file.write_text(new_text, encoding="utf-8")
            except OSError as exc:
                errors.append({"file": rel, "error": str(exc)})
                changes.pop()  # Remove the optimistic change entry.

    return {
        "migration": "v3.2.0-add-tars-category",
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
