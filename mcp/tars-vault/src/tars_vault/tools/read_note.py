"""read_note — Read a note and return parsed frontmatter + body.

Arguments:
  vault:  required. Absolute vault path.
  file:   required. Vault-relative path (with or without .md).

Returns:
  {status: ok, frontmatter: {...}, body: "...", has_frontmatter: bool, path: "..."}
  {status: error, reason: "..."}
"""
from __future__ import annotations

from typing import Any

from .. import _common


def read_note(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    file_ = kwargs.get("file")
    if not vault:
        return _common.error("missing 'vault' path")
    if not file_:
        return _common.error("missing 'file' argument")
    try:
        vault_p = _common.resolve_vault_path(vault)
        note_p = _common.resolve_note_path(vault_p, file_)
    except ValueError as exc:
        return _common.error(str(exc))
    if not note_p.is_file():
        return _common.error(f"note not found: {note_p.relative_to(vault_p)}")
    try:
        text = _common.read_note_text(note_p)
    except (OSError, UnicodeDecodeError) as exc:
        return _common.error(f"read failed: {exc}")
    payload = _common.note_payload(text)
    return _common.ok(
        path=str(note_p.relative_to(vault_p)),
        **payload,
    )
