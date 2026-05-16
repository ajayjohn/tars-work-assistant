"""update_frontmatter — Set one or more frontmatter properties on an existing note.

Arguments:
  vault:       required.
  file:        required. Vault-relative path.
  updates:     preferred. Mapping of key → value. Existing keys replaced,
               missing keys added. Set value to null to DELETE a key.
  property:    compatibility alias for one-key updates.
  value:       compatibility value for property.
  allow_user_properties: optional bool (default false). Unless true, only
                         `tars-` keys or {tags, aliases} may be modified.

Returns:
  {status: ok, path, updated: [...], removed: [...]}
  {status: error, reason}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import _common
from ..telemetry import append_event


def update_frontmatter(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    file_ = kwargs.get("file")
    updates = kwargs.get("updates")
    if updates is None and kwargs.get("property"):
        updates = {kwargs.get("property"): kwargs.get("value")}
    allow_user = bool(kwargs.get("allow_user_properties", False))
    if not vault:
        return _common.error("missing 'vault'")
    if not file_:
        return _common.error("missing 'file'")
    if not isinstance(updates, dict):
        return _common.error("'updates' must be a mapping")

    try:
        vault_p = _common.resolve_vault_path(vault)
        note_p = _common.resolve_note_path(vault_p, file_)
    except ValueError as exc:
        return _common.error(str(exc))
    if not note_p.is_file():
        return _common.error(f"note not found: {note_p.relative_to(vault_p)}")
    if _common.is_protected_path(vault_p, note_p) and not kwargs.get("allow_protected_paths"):
        return _common.error(_common.protected_path_reason(vault_p, note_p))

    reserved_non_prefix = {"tags", "aliases", "title"}
    if not allow_user:
        for k in updates.keys():
            if k in reserved_non_prefix or k.startswith("tars-"):
                continue
            return _common.error(
                f"key {k!r} is not tars-prefixed; pass allow_user_properties=true"
            )

    try:
        text = _common.read_note_text(note_p)
    except OSError as exc:
        return _common.error(f"read failed: {exc}")
    fm, body = _common.split_frontmatter(text)
    if fm is None:
        fm = {}
    updated: list[str] = []
    removed: list[str] = []
    for k, v in updates.items():
        if v is None and k in fm:
            fm.pop(k)
            removed.append(k)
        else:
            fm[k] = v
            updated.append(k)

    new_text = _common.build_note_text(fm, body)
    try:
        _common.write_note_text(note_p, new_text, backup=True)
    except OSError as exc:
        return _common.error(f"write failed: {exc}")

    rel = str(note_p.relative_to(vault_p))
    append_event(
        Path(vault_p),
        {
            "event": "vault_write",
            "tool": "update_frontmatter",
            "file": rel,
            "bytes": len(new_text.encode("utf-8")),
        },
    )
    return _common.ok(path=rel, updated=updated, removed=removed)
