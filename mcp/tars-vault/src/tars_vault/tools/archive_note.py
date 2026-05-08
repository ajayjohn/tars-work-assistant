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

import re
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Any

from .. import _common
from ..telemetry import append_event
from .move_note import move_note
from .update_frontmatter import update_frontmatter


DURABLE_TAGS = {"tars/decision", "tars/org-context"}
SKIP_DIRS = {".git", ".obsidian", ".claude", "_system/embedding-cache"}


def _tags(fm: dict[str, Any]) -> list[str]:
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    if not isinstance(tags, list):
        return []
    return [str(t) for t in tags]


def _note_targets(note_p: Path, fm: dict[str, Any], vault_p: Path) -> set[str]:
    rel_no_ext = str(note_p.relative_to(vault_p).with_suffix("")).replace("\\", "/")
    targets = {note_p.stem, rel_no_ext}
    for alias in fm.get("aliases") or []:
        targets.add(str(alias))
    title = fm.get("title")
    if title:
        targets.add(str(title))
    return {t for t in targets if t}


def _contains_wikilink(text: str, targets: set[str]) -> bool:
    for target in targets:
        escaped = re.escape(target)
        if re.search(r"\[\[" + escaped + r"(?:[#|\]]|\]\])", text):
            return True
    return False


def _scan_guardrails(vault_p: Path, note_p: Path, fm: dict[str, Any]) -> list[dict[str, Any]]:
    targets = _note_targets(note_p, fm, vault_p)
    cutoff = datetime.now().astimezone() - timedelta(days=90)
    findings: list[dict[str, Any]] = []
    for md in vault_p.rglob("*.md"):
        rel = md.relative_to(vault_p)
        if md == note_p or any(str(rel).startswith(s) for s in SKIP_DIRS):
            continue
        try:
            text = md.read_text(encoding="utf-8")
            other_fm, _other_body = _common.split_frontmatter(text)
        except (OSError, UnicodeDecodeError):
            continue
        if not _contains_wikilink(text, targets):
            continue
        try:
            modified_at = datetime.fromtimestamp(md.stat().st_mtime).astimezone()
        except OSError:
            modified_at = datetime.now().astimezone()
        if modified_at >= cutoff:
            findings.append({
                "type": "recent_backlink",
                "file": str(rel),
                "modified": modified_at.date().isoformat(),
            })
        other_tags = _tags(other_fm or {})
        other_status = str((other_fm or {}).get("tars-status", "")).lower()
        if "tars/task" in other_tags and other_status in ("", "open", "active"):
            findings.append({
                "type": "active_task_reference",
                "file": str(rel),
                "status": other_status or "open",
            })
    return findings


def archive_note(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    file_ = kwargs.get("file")
    reason = kwargs.get("reason", "")
    force = bool(kwargs.get("force", False))
    dry_run = bool(kwargs.get("dry_run", False))
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
    if _common.is_protected_path(vault_p, note_p):
        return _common.error(_common.protected_path_reason(vault_p, note_p))

    fm, _body = _common.split_frontmatter(_common.read_note_text(note_p))
    fm = fm or {}
    if fm.get("tars-archive-exempt") is True and not force:
        return _common.error("note has tars-archive-exempt=true (pass force=true to override)")
    tags = _tags(fm)
    if any(t in DURABLE_TAGS for t in tags) and not force:
        return _common.error(
            f"note has durable tag {[t for t in tags if t in DURABLE_TAGS]}; "
            "refuse to archive (pass force=true to override)"
        )
    guardrail_findings = _scan_guardrails(vault_p, note_p, fm)
    if guardrail_findings and not force:
        return _common.error(
            "archive guardrail blocked: "
            + "; ".join(f"{f['type']} in {f['file']}" for f in guardrail_findings),
            blocked=True,
            guardrails=guardrail_findings,
        )

    # Determine target path: archive/YYYY-MM/<filename>
    today = date.today()
    bucket = f"archive/{today.year:04d}-{today.month:02d}"
    target_rel = f"{bucket}/{note_p.name}"
    target_abs = vault_p / target_rel
    if target_abs.exists() and not force:
        return _common.error(f"archive target already exists: {target_rel}")

    if dry_run:
        return _common.ok(
            from_path=str(note_p.relative_to(vault_p)),
            to_path=target_rel,
            blocked=False,
            guardrails=[],
            dry_run=True,
        )

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
        allow_protected_paths=True,
    )
    if upd_result.get("status") != "ok":
        return _common.error(f"tag-update failed: {upd_result.get('reason')}")

    # Use move_note so wikilinks are rewritten.
    mv_result = move_note(
        vault=str(vault_p),
        src=str(note_p.relative_to(vault_p)),
        dst=target_rel,
        allow_protected_paths=True,
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
