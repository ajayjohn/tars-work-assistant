"""create_note — Create a new vault note with frontmatter.

Arguments (all via kwargs):
  vault:         required. Absolute vault path.
  path:          required. Vault-relative target path (with or without .md).
  frontmatter:   required. dict of frontmatter keys; tars-managed keys must
                 use the `tars-` prefix. `tags` is recommended.
  body:          optional. Markdown body (default: empty).
  overwrite:     optional bool (default false). If true, allows replacing
                 an existing note (still writes a .bak).

Auto-alias behavior (v3.3):
  When the path stem matches the pattern YYYY-MM-DD-<slug>, the server
  automatically adds a space-form alias ("YYYY-MM-DD Slug Title") to the
  `aliases` list if one is not already present.  This ensures that wikilinks
  of the form [[YYYY-MM-DD Meeting Title]] resolve correctly in Obsidian
  regardless of whether the underlying file uses a hyphen-slug name.

  The auto-alias fires for notes under journal/ and archive/transcripts/ only.
  It can be suppressed by passing `auto_alias=false`.

Writes `_system/telemetry/<date>.jsonl` vault_write event on success.

Returns:
  {status: ok, path: "...", bytes: N, aliases_added: [...]}
  {status: error, reason: "..."}
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .. import _common
from ..telemetry import append_event
from ..validators import load_schemas, validate_against_schema, validate_no_bad_wikilinks


# Paths under these vault-relative prefixes receive auto-alias treatment.
_JOURNAL_PREFIXES = ("journal/", "archive/transcripts/")

# YYYY-MM-DD-<slug> filename pattern (with optional extension).
_DATE_SLUG_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+?)(?:\.md)?$")


def _derive_space_title(stem: str) -> str | None:
    """Return the space-form title from a YYYY-MM-DD-slug stem, or None.

    Example: "2026-04-06-gba-ai-panel-prep" → "2026-04-06 Gba Ai Panel Prep"

    Title-casing is intentionally simple — Obsidian's alias matching is
    case-insensitive, so "Gba Ai Panel Prep" resolves [[GBA AI Panel Prep]].
    """
    m = _DATE_SLUG_RE.match(stem)
    if not m:
        return None
    date_str = m.group(1)
    slug = m.group(2)
    words = [w.capitalize() for w in slug.split("-") if w]
    return f"{date_str} {' '.join(words)}"


def _is_journal_path(vault_relative: str) -> bool:
    norm = vault_relative.replace("\\", "/")
    return any(norm.startswith(p) for p in _JOURNAL_PREFIXES)


def _ensure_alias(frontmatter: dict[str, Any], alias: str) -> tuple[dict[str, Any], bool]:
    """Return (updated_frontmatter, was_added).

    Adds ``alias`` to the ``aliases`` list if not already present
    (case-insensitive comparison).  Mutates a copy, never the original.
    """
    fm = dict(frontmatter)
    existing = fm.get("aliases") or []
    if not isinstance(existing, list):
        existing = [str(existing)] if existing else []
    lower_existing = {str(a).lower() for a in existing}
    if alias.lower() in lower_existing:
        return fm, False
    fm["aliases"] = existing + [alias]
    return fm, True


def create_note(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    path = kwargs.get("path")
    frontmatter = kwargs.get("frontmatter")
    body = kwargs.get("body", "")
    overwrite = bool(kwargs.get("overwrite", False))
    auto_alias = kwargs.get("auto_alias", True)  # default on
    validate_schema = kwargs.get("validate", True)
    allow_protected = bool(kwargs.get("allow_protected_paths", False))

    if not vault:
        return _common.error("missing 'vault' path")
    if not path:
        return _common.error("missing 'path' argument")
    if frontmatter is None:
        frontmatter = {}
    if not isinstance(frontmatter, dict):
        return _common.error("'frontmatter' must be a mapping")
    if not isinstance(body, str):
        return _common.error("'body' must be a string")

    link_errors = validate_no_bad_wikilinks(body)
    if link_errors:
        return _common.error(
            "wikilink validation failed: " + "; ".join(link_errors)
        )

    try:
        vault_p = _common.resolve_vault_path(vault)
        note_p = _common.resolve_note_path(vault_p, path)
    except ValueError as exc:
        return _common.error(str(exc))

    if validate_schema:
        schemas = load_schemas(vault_p)
        if schemas:
            schema_errors = validate_against_schema(frontmatter, schemas)
            if schema_errors:
                return _common.error("schema validation failed: " + "; ".join(schema_errors))

    if note_p.exists() and not overwrite:
        return _common.error(
            f"note already exists: {note_p.relative_to(vault_p)} "
            "(pass overwrite=true to replace)"
        )
    if _common.is_protected_path(vault_p, note_p) and not allow_protected:
        return _common.error(_common.protected_path_reason(vault_p, note_p))

    # Validate: any managed key (prefix tars-) is OK; permit common Obsidian
    # keys (`tags`, `aliases`) without prefix; reject any other non-prefix key
    # unless the caller explicitly opts in via allow_user_properties=True.
    allow_user = bool(kwargs.get("allow_user_properties", False))
    reserved_non_prefix = {"tags", "aliases"}
    if not allow_user:
        for key in frontmatter.keys():
            if key in reserved_non_prefix:
                continue
            if key.startswith(_common.__dict__.get("TARS_PREFIX", "tars-")) or key.startswith("tars-"):
                continue
            return _common.error(
                f"frontmatter key {key!r} is not tars-prefixed and not a reserved "
                "Obsidian key; pass allow_user_properties=true to permit"
            )

    # Auto-alias: derive the space-form title and add it to aliases when the
    # note lives under journal/ or archive/transcripts/ and has a slug stem.
    aliases_added: list[str] = []
    if auto_alias:
        rel_str = str(note_p.relative_to(vault_p)).replace("\\", "/")
        if _is_journal_path(rel_str):
            space_title = _derive_space_title(note_p.stem)
            if space_title:
                frontmatter, was_added = _ensure_alias(frontmatter, space_title)
                if was_added:
                    aliases_added.append(space_title)

    text = _common.build_note_text(frontmatter, body)
    try:
        _common.write_note_text(note_p, text, backup=bool(note_p.exists()))
    except OSError as exc:
        return _common.error(f"write failed: {exc}")

    rel = str(note_p.relative_to(vault_p))
    size = len(text.encode("utf-8"))
    append_event(
        Path(vault_p),
        {
            "event": "vault_write",
            "tool": "create_note",
            "file": rel,
            "bytes": size,
            "aliases_added": aliases_added,
        },
    )
    return _common.ok(path=rel, bytes=size, aliases_added=aliases_added)
