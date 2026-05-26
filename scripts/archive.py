#!/usr/bin/env python3
"""archive — staleness-based archival candidate finder (Phase 7 curator).

Identifies content past its staleness threshold for archival. Does NOT
perform archival directly — outputs JSON candidates for /lint --actions
curator and /maintain --weekly to surface for user review. The vault-side
curator never deletes; archival happens via mcp__tars_vault__archive_note
after explicit approval.

Three check classes (default: all):
  memory     — memory/* notes with tars-staleness tier elapsed since
               tars-modified / tars-updated, gated by guardrails (active-task
               references across tasks/ and legacy memory/tasks/, recent backlinks)
               and never auto-proposing tars-pinned: true
               or already-archived notes.
  workflows  — _system/workflows.yaml entries whose last_used is null AND
               created is older than 60 days, OR last_used is older than
               60 days. Respects pinned: true.
  inbox      — inbox/processed/* items older than --inbox-days (default 7)
               for routine sweep.

Contract:
  --vault <path>          required
  --json                  emit machine-readable output (default: human text)
  --check {all,memory,workflows,inbox}   limit to one class (default: all)
  --memory-stale-days N   override memory-tier-elapsed cutoff (informational
                          override; the tars-staleness tier is still the
                          primary signal)
  --workflow-stale-days N default 60
  --inbox-days N          default 7
Exit codes: 0 OK, 2 error, 3 invalid state.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_frontmatter(file_path: Path) -> tuple[dict | None, str]:
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None, ""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None, content
    try:
        if HAS_YAML:
            fm = yaml.safe_load(match.group(1))
        else:
            fm = {}
            for line in match.group(1).split("\n"):
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    key, _, val = line.partition(":")
                    val = val.strip().strip("'\"")
                    fm[key.strip()] = val
        body = content[match.end():]
        return fm if isinstance(fm, dict) else None, body
    except Exception:
        return None, content


def extract_wikilinks(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(1) for m in re.finditer(r'\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]', text)]


def _tags(fm: dict | None) -> list[str]:
    if not fm:
        return []
    tags = fm.get("tags", []) or []
    if isinstance(tags, str):
        tags = [tags]
    if not isinstance(tags, list):
        return []
    return [str(t).lstrip("#") for t in tags]


def _parse_date(value: Any) -> date | None:
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


def note_activity_date(path: Path, fm: dict | None) -> date | None:
    fm = fm or {}
    for key in (
        "tars-modified",
        "tars-updated",
        "tars-inbox-processed",
        "tars-date",
        "tars-created",
        "updated",
        "created",
    ):
        parsed = _parse_date(fm.get(key))
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


def note_reference_keys(vault: Path, md: Path, fm: dict | None) -> set[str]:
    fm = fm or {}
    keys = {md.stem.lower(), str(md.relative_to(vault).with_suffix("")).replace("\\", "/").lower()}
    for alias in fm.get("aliases") or []:
        keys.add(str(alias).lower())
    for key in ("title", "tars-name"):
        value = fm.get(key)
        if value:
            keys.add(str(value).lower())
    return {key for key in keys if key}


# ---------------------------------------------------------------------------
# Memory check
# ---------------------------------------------------------------------------


def find_active_task_references(vault: Path) -> set[str]:
    referenced: set[str] = set()
    for root in (vault / "tasks", vault / "memory" / "tasks"):
        if not root.is_dir():
            continue
        for md in root.rglob("*.md"):
            fm, body = parse_frontmatter(md)
            if not fm:
                continue
            if "tars/task" not in _tags(fm):
                continue
            if str(fm.get("tars-status", "")).lower() in ("done", "completed", "cancelled", "canceled", "archived"):
                continue
            if body:
                for link in extract_wikilinks(body):
                    referenced.add(link.lower())
            for key in ("tars-owner", "tars-project", "tars-source"):
                val = fm.get(key, "")
                if isinstance(val, str):
                    for link in extract_wikilinks(val):
                        referenced.add(link.lower())
    return referenced


def find_recent_backlinks(vault: Path, days: int = 90) -> set[str]:
    cutoff = date.today() - timedelta(days=days)
    linked: set[str] = set()
    for scan_dir in ("journal", "memory", "contexts", "tasks"):
        d = vault / scan_dir
        if not d.is_dir():
            continue
        for md in d.rglob("*.md"):
            fm, body = parse_frontmatter(md)
            activity = note_activity_date(md, fm)
            if not activity:
                continue
            if activity < cutoff:
                continue
            if body:
                for link in extract_wikilinks(body):
                    linked.add(link.lower())
    return linked


def find_memory_candidates(vault: Path, override_days: int | None = None) -> dict[str, Any]:
    today = date.today()
    thresholds = {"durable": None, "seasonal": 180, "transient": 90, "ephemeral": 30}
    active_refs = find_active_task_references(vault)
    recent_links = find_recent_backlinks(vault, days=90)
    archivable: list[dict[str, Any]] = []
    protected: list[dict[str, Any]] = []
    pinned_skipped = 0

    mem = vault / "memory"
    if not mem.is_dir():
        return {"archivable": archivable, "protected": protected, "pinned_skipped": pinned_skipped}

    for md in mem.rglob("*.md"):
        if md.name.startswith(("_", ".")):
            continue
        fm, _ = parse_frontmatter(md)
        if not fm:
            continue
        tags = _tags(fm)
        if "tars/archived" in tags:
            continue
        # Phase 7: respect pinned notes regardless of staleness
        if fm.get("tars-pinned") is True or fm.get("tars-pinned") in ("true", "yes"):
            pinned_skipped += 1
            continue
        staleness = fm.get("tars-staleness", "seasonal")
        threshold = override_days if override_days else thresholds.get(staleness)
        if threshold is None:
            continue
        modified_date = note_activity_date(md, fm)
        if not modified_date:
            continue
        age_days = (today - modified_date).days
        if age_days <= threshold:
            continue
        note_keys = note_reference_keys(vault, md, fm)
        protection: list[str] = []
        if tags and any(t in {"tars/decision", "tars/org-context"} for t in tags):
            protection.append("durable decision/org context")
        if "tars/initiative" in tags and str(fm.get("tars-status", "")).lower() in ("active", "planned", "in-progress"):
            protection.append("active initiative")
        if note_keys & active_refs:
            protection.append("referenced by active task")
        if note_keys & recent_links:
            protection.append("has recent backlinks (< 90 days)")
        record = {
            "file": str(md.relative_to(vault)),
            "name": md.stem,
            "staleness": staleness,
            "threshold_days": threshold,
            "age_days": age_days,
            "last_modified": modified_date.isoformat(),
            "protection_reasons": protection,
        }
        if protection:
            protected.append(record)
        else:
            archivable.append(record)
    archivable.sort(key=lambda c: c["age_days"], reverse=True)
    return {"archivable": archivable, "protected": protected, "pinned_skipped": pinned_skipped}


# ---------------------------------------------------------------------------
# Workflow check
# ---------------------------------------------------------------------------


def _read_workflows(vault: Path) -> list[dict]:
    """Return the list of workflow entries from _system/workflows.yaml.

    Handles the schema-documented shape `workflows: [...]`. Stdlib parser
    fallback covers the subset our template uses.
    """
    target = vault / "_system" / "workflows.yaml"
    if not target.is_file():
        return []
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    if HAS_YAML:
        try:
            data = yaml.safe_load(text) or {}
            wf = data.get("workflows", [])
            return wf if isinstance(wf, list) else []
        except Exception:
            return []
    # Stdlib fallback: parse a minimal subset (entries are bullet items
    # `- key: value` blocks). Returns best-effort result; full parsing
    # uses PyYAML when available.
    out: list[dict] = []
    cur: dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s*-\s+(\S[^:]*):\s*(.*)$", line)
        if m:
            if cur:
                out.append(cur)
            cur = {m.group(1).strip(): m.group(2).strip().strip('"').strip("'")}
            continue
        m = re.match(r"^\s+(\S[^:]*):\s*(.*)$", line)
        if m and cur is not None:
            cur[m.group(1).strip()] = m.group(2).strip().strip('"').strip("'")
    if cur:
        out.append(cur)
    return out


def find_workflow_candidates(vault: Path, stale_days: int = 60) -> dict[str, Any]:
    today = date.today()
    cutoff = today - timedelta(days=stale_days)
    candidates: list[dict[str, Any]] = []
    pinned_skipped = 0
    for wf in _read_workflows(vault):
        if not isinstance(wf, dict):
            continue
        wid = wf.get("id") or ""
        if wf.get("pinned") is True or wf.get("pinned") in ("true", "yes"):
            pinned_skipped += 1
            continue
        last_used = wf.get("last_used")
        created = wf.get("created")
        # Determine the most-recent activity date for this workflow
        ref_date: date | None = None
        for value in (last_used, created):
            if not value or value in ("null", "~", "None"):
                continue
            try:
                if isinstance(value, str):
                    ref_date = datetime.strptime(value, "%Y-%m-%d").date()
                elif isinstance(value, date):
                    ref_date = value
                break
            except (ValueError, TypeError):
                continue
        if ref_date is None:
            continue
        if ref_date >= cutoff:
            continue
        age = (today - ref_date).days
        candidates.append({
            "id": wid,
            "name": wf.get("name", ""),
            "trigger": wf.get("trigger", ""),
            "last_used": last_used,
            "created": created,
            "age_days": age,
            "use_count": wf.get("use_count", 0),
        })
    candidates.sort(key=lambda c: c["age_days"], reverse=True)
    return {"candidates": candidates, "pinned_skipped": pinned_skipped}


# ---------------------------------------------------------------------------
# Inbox sweep (uses tars-inbox-processed/tars dates before filesystem mtime)
# ---------------------------------------------------------------------------


def find_processed_inbox_items(vault: Path, days_old: int = 7) -> list[dict]:
    out: list[dict] = []
    target = vault / "inbox" / "processed"
    if not target.is_dir():
        return out
    today = date.today()
    for f in target.iterdir():
        if f.name.startswith("."):
            continue
        fm, _body = parse_frontmatter(f) if f.suffix == ".md" else ({}, "")
        activity = note_activity_date(f, fm)
        if not activity:
            continue
        age = (today - activity).days
        if age >= days_old:
            out.append({"file": str(f.relative_to(vault)), "age_days": age})
    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="archive")
    parser.add_argument("--vault", default=None, help="Vault path (defaults to first positional or CWD).")
    parser.add_argument("vault_positional", nargs="?", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help="Emit JSON (default).")
    parser.add_argument("--check", choices=["all", "memory", "workflows", "inbox"], default="all")
    parser.add_argument("--memory-stale-days", type=int, default=None)
    parser.add_argument("--workflow-stale-days", type=int, default=60)
    parser.add_argument("--inbox-days", type=int, default=7)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    vault_str = args.vault or args.vault_positional or "."
    vault = Path(vault_str).expanduser().resolve()
    if not vault.is_dir():
        print(f"error: vault path not a directory: {vault}", file=sys.stderr)
        return 3

    output: dict[str, Any] = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "vault": str(vault),
        "checks": [],
        "summary": {},
    }

    if args.check in ("all", "memory"):
        mem = find_memory_candidates(vault, override_days=args.memory_stale_days)
        output["checks"].append("memory")
        output["memory"] = mem
        output["summary"]["memory_archivable"] = len(mem["archivable"])
        output["summary"]["memory_protected"] = len(mem["protected"])
        output["summary"]["memory_pinned_skipped"] = mem["pinned_skipped"]

    if args.check in ("all", "workflows"):
        wf = find_workflow_candidates(vault, stale_days=args.workflow_stale_days)
        output["checks"].append("workflows")
        output["workflows"] = wf
        output["summary"]["workflow_candidates"] = len(wf["candidates"])
        output["summary"]["workflow_pinned_skipped"] = wf["pinned_skipped"]

    if args.check in ("all", "inbox"):
        inbox = find_processed_inbox_items(vault, days_old=args.inbox_days)
        output["checks"].append("inbox")
        output["inbox"] = inbox
        output["summary"]["inbox_cleanup_candidates"] = len(inbox)

    print(json.dumps(output, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
