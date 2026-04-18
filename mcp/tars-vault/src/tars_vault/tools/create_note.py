"""create_note — Create a new vault note with frontmatter.

Arguments (all via kwargs):
  vault:         required. Absolute vault path.
  path:          required. Vault-relative target path (with or without .md).
  frontmatter:   required. dict of frontmatter keys; tars-managed keys must
                 use the `tars-` prefix. `tags` is recommended.
  body:          optional. Markdown body (default: empty).
  overwrite:     optional bool (default false). If true, allows replacing
                 an existing note (still writes a .bak).

Writes `_system/telemetry/<date>.jsonl` vault_write event on success.

Returns:
  {status: ok, path: "...", bytes: N}
  {status: error, reason: "..."}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import _common
from ..telemetry import append_event


def create_note(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    path = kwargs.get("path")
    frontmatter = kwargs.get("frontmatter")
    body = kwargs.get("body", "")
    overwrite = bool(kwargs.get("overwrite", False))

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

    try:
        vault_p = _common.resolve_vault_path(vault)
        note_p = _common.resolve_note_path(vault_p, path)
    except ValueError as exc:
        return _common.error(str(exc))

    if note_p.exists() and not overwrite:
        return _common.error(
            f"note already exists: {note_p.relative_to(vault_p)} "
            "(pass overwrite=true to replace)"
        )

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

    text = _common.build_note_text(frontmatter, body)
    try:
        _common.write_note_text(note_p, text, backup=bool(note_p.exists()))
    except OSError as exc:
        return _common.error(f"write failed: {exc}")

    rel = str(note_p.relative_to(vault_p))
    size = len(text.encode("utf-8"))
    append_event(
        Path(vault_p),
        {"event": "vault_write", "tool": "create_note", "file": rel, "bytes": size},
    )
    return _common.ok(path=rel, bytes=size)
