"""Derived workspace state for fast startup and bounded navigation tools.

The Markdown workspace remains the source of truth. This module scans it
lightly, returns structured summaries for MCP tools, and can materialize a
small `_system/activity-ledger.yaml` capsule for SessionStart.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from . import _common


SKIP_PARTS = {".git", ".obsidian", ".claude"}
SKIP_PREFIXES = ("_system/embedding-cache/",)
ACTIVE_STATUSES = {"", "active", "open", "in-progress", "planned", "todo"}
CLOSED_STATUSES = {"done", "completed", "cancelled", "canceled", "archived"}
DATE_KEYS = (
    "tars-modified",
    "tars-updated",
    "tars-inbox-processed",
    "tars-date",
    "tars-created",
    "updated",
    "created",
    "date",
)


def _rel(vault: Path, path: Path) -> str:
    return str(path.relative_to(vault)).replace("\\", "/")


def _skip_path(rel: str, *, include_archive: bool = False, include_system: bool = False) -> bool:
    parts = set(Path(rel).parts)
    if parts & SKIP_PARTS:
        return True
    if any(rel.startswith(prefix) for prefix in SKIP_PREFIXES):
        return True
    if not include_archive and rel.startswith("archive/"):
        return True
    if not include_system and rel.startswith("_system/"):
        return True
    return False


def iter_markdown(vault: Path, *, include_archive: bool = False, include_system: bool = False) -> list[Path]:
    out: list[Path] = []
    for md in vault.rglob("*.md"):
        rel = _rel(vault, md)
        if _skip_path(rel, include_archive=include_archive, include_system=include_system):
            continue
        out.append(md)
    return sorted(out)


def _read_note(path: Path) -> tuple[dict[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}, ""
    fm, body = _common.split_frontmatter(text)
    return fm or {}, body


def _tags(fm: dict[str, Any]) -> list[str]:
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    if not isinstance(tags, list):
        return []
    return [str(t).lstrip("#") for t in tags]


def _has_tag(fm: dict[str, Any], tag: str) -> bool:
    target = tag.lstrip("#")
    return target in _tags(fm)


def parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value in (None, "", "null", "~", "None"):
        return None
    raw = str(value).strip().strip('"').strip("'")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None


def note_date(path: Path, fm: dict[str, Any]) -> date | None:
    for key in DATE_KEYS:
        parsed = parse_date(fm.get(key))
        if parsed:
            return parsed
    match = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", str(path))
    if match:
        try:
            return date.fromisoformat("-".join(match.groups()))
        except ValueError:
            pass
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).date()
    except OSError:
        return None


def _install_value(vault: Path, key: str) -> str | None:
    target = vault / "_system" / "install.yaml"
    if not target.is_file():
        return None
    try:
        data = _common.parse_simple_yaml(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    value = data.get(key)
    if value in (None, "", "null", "~"):
        return None
    return str(value)


def _housekeeping(vault: Path) -> dict[str, Any]:
    target = vault / "_system" / "housekeeping-state.yaml"
    if not target.is_file():
        return {}
    try:
        return _common.parse_simple_yaml(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def _latest(items: list[dict[str, Any]]) -> str | None:
    dates = sorted(str(item["date"]) for item in items if item.get("date"))
    return dates[-1] if dates else None


def _latest_under(vault: Path, rel: str) -> str | None:
    root = vault / rel
    if not root.is_dir():
        return None
    dates: list[str] = []
    for path in root.rglob("*"):
        if path.is_dir() or path.name.startswith("."):
            continue
        fm, _body = _read_note(path) if path.suffix == ".md" else ({}, "")
        parsed = note_date(path, fm)
        if parsed:
            dates.append(parsed.isoformat())
    return sorted(dates)[-1] if dates else None


def _item(path: Path, vault: Path, fm: dict[str, Any], dt: date | None) -> dict[str, Any]:
    return {
        "path": _rel(vault, path),
        "title": str(fm.get("title") or fm.get("tars-name") or path.stem),
        "date": dt.isoformat() if dt else None,
        "status": str(fm.get("tars-status") or ""),
    }


def build_activity_ledger(
    vault: str | Path,
    *,
    stale_days: int = 30,
    transcript_gap_days: int = 30,
) -> dict[str, Any]:
    vault_p = _common.resolve_vault_path(vault)
    today = date.today()
    stale_cutoff = today - timedelta(days=stale_days)
    transcript_cutoff = today - timedelta(days=transcript_gap_days)

    active_file_count = 0
    archive_file_count = 0
    by_root: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    people: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    active_initiatives: list[dict[str, Any]] = []
    stale_active: list[dict[str, Any]] = []
    open_tasks: list[dict[str, Any]] = []
    overdue_tasks: list[dict[str, Any]] = []
    recent_journal: list[dict[str, Any]] = []
    briefings: list[dict[str, Any]] = []
    transcripts: list[dict[str, Any]] = []
    frontmatter_pollution_count = 0

    for md in iter_markdown(vault_p, include_archive=True):
        rel = _rel(vault_p, md)
        if rel.startswith("archive/"):
            archive_file_count += 1
        else:
            active_file_count += 1
            root = rel.split("/", 1)[0]
            by_root[root] = by_root.get(root, 0) + 1

        fm, _body = _read_note(md)
        if not rel.startswith("archive/") and fm:
            allowed_keys = {"tags", "aliases"}
            if any((key not in allowed_keys and not str(key).startswith("tars-")) for key in fm):
                frontmatter_pollution_count += 1
        tags = _tags(fm)
        for tag in tags:
            by_tag[tag] = by_tag.get(tag, 0) + 1
        dt = note_date(md, fm)

        if "tars/person" in tags:
            people.append(_item(md, vault_p, fm, dt))
        if "tars/decision" in tags:
            decisions.append(_item(md, vault_p, fm, dt))
        if "tars/journal" in tags or rel.startswith("journal/"):
            recent_journal.append(_item(md, vault_p, fm, dt))
        if "tars/briefing" in tags:
            briefings.append(_item(md, vault_p, fm, dt))
        if rel.startswith("archive/transcripts/") or "tars/transcript" in tags:
            transcripts.append(_item(md, vault_p, fm, dt))

        status = str(fm.get("tars-status") or "").lower()
        if "tars/initiative" in tags and status in {"", "active", "planned", "in-progress"}:
            record = _item(md, vault_p, fm, dt)
            active_initiatives.append(record)
            if dt and dt < stale_cutoff:
                record["age_days"] = (today - dt).days
                stale_active.append(record)

        if "tars/task" in tags:
            if status not in CLOSED_STATUSES:
                record = _item(md, vault_p, fm, dt)
                due = parse_date(fm.get("tars-due"))
                if due:
                    record["due"] = due.isoformat()
                open_tasks.append(record)
                if due and due < today:
                    record["age_days"] = (today - due).days
                    overdue_tasks.append(record)

    for root in ("inbox", "tasks"):
        if (vault_p / root).is_dir() and root not in by_root:
            by_root[root] = 0

    pending_inbox = 0
    inbox_pending = vault_p / "inbox" / "pending"
    if inbox_pending.is_dir():
        pending_inbox = sum(1 for p in inbox_pending.iterdir() if p.is_file() and not p.name.startswith("."))

    housekeeping = _housekeeping(vault_p)
    last_sync = housekeeping.get("last_sync") if isinstance(housekeeping.get("last_sync"), dict) else {}
    archive_state = housekeeping.get("archive") if isinstance(housekeeping.get("archive"), dict) else {}
    inbox_state = housekeeping.get("inbox") if isinstance(housekeeping.get("inbox"), dict) else {}

    last_transcript = _latest(transcripts) or _latest_under(vault_p, "archive/transcripts")
    last_session_at = _install_value(vault_p, "last_session_at")
    last_session_date = parse_date(last_session_at)
    last_transcript_date = parse_date(last_transcript)

    context_gaps: list[dict[str, Any]] = []
    if pending_inbox:
        context_gaps.append({"type": "pending_inbox", "count": pending_inbox})
    if overdue_tasks:
        context_gaps.append({"type": "overdue_tasks", "count": len(overdue_tasks)})
    if stale_active:
        context_gaps.append({"type": "stale_active_initiatives", "count": len(stale_active), "days": stale_days})
    if last_session_date and (today - last_session_date).days >= 14:
        context_gaps.append({"type": "long_disuse", "days": (today - last_session_date).days})
    if not last_transcript_date or last_transcript_date < transcript_cutoff:
        context_gaps.append({"type": "sparse_transcripts", "last_transcript_at": last_transcript})

    recent_journal.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
    active_initiatives.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
    stale_active.sort(key=lambda item: int(item.get("age_days") or 0), reverse=True)
    overdue_tasks.sort(key=lambda item: int(item.get("age_days") or 0), reverse=True)

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "derived-from-markdown",
        "active_file_count": active_file_count,
        "archive_file_count": archive_file_count,
        "by_root": dict(sorted(by_root.items())),
        "by_tag": dict(sorted(by_tag.items())),
        "last": {
            "session_at": last_session_at,
            "briefing_at": _latest(briefings),
            "transcript_at": last_transcript,
            "inbox_process_at": inbox_state.get("last_processed") or _latest_under(vault_p, "inbox/processed"),
            "successful_sync_at": last_sync.get("date") if isinstance(last_sync, dict) else None,
            "archive_sweep_at": archive_state.get("last_sweep") if isinstance(archive_state, dict) else None,
        },
        "people": {"count": len(people), "sample": people[:10]},
        "decisions": {"count": len(decisions), "sample": decisions[:10]},
        "initiatives": {
            "active_count": len(active_initiatives),
            "active": active_initiatives[:20],
            "stale_active": stale_active[:20],
        },
        "tasks": {
            "open_count": len(open_tasks),
            "overdue_count": len(overdue_tasks),
            "overdue": overdue_tasks[:20],
        },
        "inbox": {"pending_count": pending_inbox},
        "recent_journal": recent_journal[:20],
        "context_gaps": context_gaps,
        "frontmatter_pollution_count": frontmatter_pollution_count,
    }


def summarize_for_yaml(ledger: dict[str, Any]) -> dict[str, Any]:
    stale = ledger.get("initiatives", {}).get("stale_active", [])
    overdue = ledger.get("tasks", {}).get("overdue", [])
    last = ledger.get("last", {})
    return {
        "generated_at": ledger.get("generated_at"),
        "source": ledger.get("source", "derived-from-markdown"),
        "active_file_count": ledger.get("active_file_count", 0),
        "archive_file_count": ledger.get("archive_file_count", 0),
        "last":
            {
                "session_at": last.get("session_at"),
                "briefing_at": last.get("briefing_at"),
                "transcript_at": last.get("transcript_at"),
                "inbox_process_at": last.get("inbox_process_at"),
                "successful_sync_at": last.get("successful_sync_at"),
                "archive_sweep_at": last.get("archive_sweep_at"),
            },
        "stale_active_initiatives": {
            "count": len(stale),
            "oldest_days": max([int(item.get("age_days") or 0) for item in stale] or [0]),
        },
        "overdue_tasks": {
            "count": int(ledger.get("tasks", {}).get("overdue_count") or 0),
            "oldest_days": max([int(item.get("age_days") or 0) for item in overdue] or [0]),
        },
        "inbox": {"pending_count": int(ledger.get("inbox", {}).get("pending_count") or 0)},
        "frontmatter_pollution_count": int(ledger.get("frontmatter_pollution_count") or 0),
        "context_gaps": [str(item.get("type")) for item in ledger.get("context_gaps", []) if item.get("type")],
    }


def write_activity_ledger(vault: str | Path, ledger: dict[str, Any] | None = None) -> Path:
    vault_p = _common.resolve_vault_path(vault)
    ledger = ledger or build_activity_ledger(vault_p)
    payload = summarize_for_yaml(ledger)
    target = vault_p / "_system" / "activity-ledger.yaml"
    _common.write_note_text(target, _common.serialize_frontmatter(payload), backup=False)
    return target
