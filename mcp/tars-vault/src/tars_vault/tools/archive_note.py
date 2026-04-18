"""archive_note — Add tars/archived tag + move into archive/YYYY-MM/ with guardrails.

Guardrails (PRD §19.2):
  * Refuse if the note has backlinks in the last 90 days (`--force` overrides).
  * Refuse if `tars-archive-exempt: true`.
  * Refuse if note has `tars/decision` or `tars/org-context` tag (durable).

Arguments:
  vault:   required.
  file:    required. Vault-relative.
  reason:  optional. Free-text archived-reason, written to frontmatter.
  force:   optional bool (default false).

Returns:
  {status: ok, from_path, to_path}
  {status: error, reason}
"""
from __future__ import annotations

from pathlib import Path
from shutil import move
from datetime import date
from typing import Any

from .. import _common
from ..telemetry import append_event
from .move_note import move_note
from .update_frontmatter import update_frontmatter


DURABLE_TAGS = {"tars/decision", "tars/org-context"}


def archive_note(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    file_ = kwargs.get("file")
    reason = kwargs.get("reason", "")
    force = bool(kwargs.get("force", False))
    if not vault:
        return _common.error("missing 'vault'")
    if not file_:
        return _common.error("missing 'file'")
    try:
        vault_p = _common.resolve_vault_path(vault)
        note_p = _common.resolve_note_path(vault_p, file_)
    except ValueError as exc:
        return _common.error(str(exc))
    if not note_p.is_file():
        return _common.error(f"note not found: {note_p.relative_to(vault_p)}")

    fm, _body = _common.split_frontmatter(_common.read_note_text(note_p))
    fm = fm or {}
    if fm.get("tars-archive-exempt") is True and not force:
        return _common.error("note has tars-archive-exempt=true (pass force=true to override)")
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    if any(t in DURABLE_TAGS for t in tags) and not force:
        return _common.error(
            f"note has durable tag {[t for t in tags if t in DURABLE_TAGS]}; "
            "refuse to archive (pass force=true to override)"
        )

    # Determine target path: archive/YYYY-MM/<filename>
    today = date.today()
    bucket = f"archive/{today.year:04d}-{today.month:02d}"
    target_rel = f"{bucket}/{note_p.name}"
    target_abs = vault_p / target_rel
    if target_abs.exists() and not force:
        return _common.error(f"archive target already exists: {target_rel}")

    # Tag frontmatter BEFORE move (so downstream views pick up the tag).
    new_tags = list(tags)
    if "tars/archived" not in new_tags:
        new_tags.append("tars/archived")
    upd_payload: dict[str, Any] = {"tags": new_tags, "tars-archived-at": today.isoformat()}
    if reason:
        upd_payload["tars-archived-reason"] = str(reason)
    upd_result = update_frontmatter(
        vault=str(vault_p),
        file=str(note_p.relative_to(vault_p)),
        updates=upd_payload,
        allow_user_properties=True,
    )
    if upd_result.get("status") != "ok":
        return _common.error(f"tag-update failed: {upd_result.get('reason')}")

    # Use move_note so wikilinks are rewritten.
    mv_result = move_note(
        vault=str(vault_p),
        src=str(note_p.relative_to(vault_p)),
        dst=target_rel,
    )
    if mv_result.get("status") != "ok":
        return _common.error(f"move failed: {mv_result.get('reason')}")

    append_event(
        vault_p,
        {
            "event": "vault_write",
            "tool": "archive_note",
            "file": target_rel,
            "from_path": str(note_p.relative_to(vault_p)),
        },
    )
    return _common.ok(
        from_path=str(note_p.relative_to(vault_p)),
        to_path=target_rel,
    )
