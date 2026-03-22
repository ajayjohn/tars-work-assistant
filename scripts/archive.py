#!/usr/bin/env python3
"""
TARS v3 Archive Script
Identifies content past its staleness threshold for archival.
Does NOT perform archival directly — outputs JSON candidates for agent review.
Agent applies changes via obsidian-cli after user approval.

Usage: python3 scripts/archive.py [vault_path]
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime, date

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_frontmatter(file_path):
    """Extract YAML frontmatter."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return None, None

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


def extract_wikilinks(text):
    """Extract all wikilinks."""
    if not text:
        return []
    return [m.group(1) for m in re.finditer(r'\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]', text)]


def find_active_task_references(vault_path):
    """Find all entities referenced by active tasks."""
    vault = Path(vault_path)
    referenced = set()

    for scan_dir in ["memory"]:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue

        for md_file in dir_path.rglob("*.md"):
            fm, body = parse_frontmatter(md_file)
            if not fm:
                continue

            tags = fm.get("tags", [])
            if not isinstance(tags, list):
                tags = [tags] if tags else []

            if "tars/task" not in tags:
                continue

            status = fm.get("tars-status", "")
            if status in ("done", "cancelled"):
                continue

            # This task is active — collect all its references
            if body:
                for link in extract_wikilinks(body):
                    referenced.add(link.lower())

            # Also check frontmatter references
            for key in ("tars-owner", "tars-project", "tars-source"):
                val = fm.get(key, "")
                if isinstance(val, str):
                    for link in extract_wikilinks(val):
                        referenced.add(link.lower())

    return referenced


def find_recent_backlinks(vault_path, days=90):
    """Find entities that have incoming links from recent notes."""
    vault = Path(vault_path)
    today = date.today()
    cutoff = today - __import__("datetime").timedelta(days=days)
    linked = set()

    for scan_dir in ["journal", "memory"]:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue

        for md_file in dir_path.rglob("*.md"):
            # Check if file is recent
            try:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime).date()
                if mtime < cutoff:
                    continue
            except OSError:
                continue

            _, body = parse_frontmatter(md_file)
            if body:
                for link in extract_wikilinks(body):
                    linked.add(link.lower())

    return linked


def find_archive_candidates(vault_path):
    """Find memory notes past their staleness threshold."""
    vault = Path(vault_path)
    today = date.today()
    candidates = []

    thresholds = {
        "durable": None,
        "seasonal": 180,
        "transient": 90,
        "ephemeral": 30,
    }

    # Get protection sets
    active_refs = find_active_task_references(vault_path)
    recent_links = find_recent_backlinks(vault_path, days=90)

    memory_dir = vault / "memory"
    if not memory_dir.exists():
        return candidates

    for md_file in memory_dir.rglob("*.md"):
        if md_file.name.startswith("_") or md_file.name.startswith("."):
            continue

        fm, _ = parse_frontmatter(md_file)
        if not fm:
            continue

        tags = fm.get("tags", [])
        if not isinstance(tags, list):
            tags = [tags] if tags else []

        # Skip already archived
        if "tars/archived" in tags:
            continue

        staleness = fm.get("tars-staleness", "seasonal")
        threshold = thresholds.get(staleness)
        if threshold is None:
            continue  # Durable, never auto-archive

        modified = fm.get("tars-modified")
        if not modified:
            continue

        try:
            if isinstance(modified, str):
                mod_date = datetime.strptime(modified, "%Y-%m-%d").date()
            elif isinstance(modified, date):
                mod_date = modified
            else:
                continue

            age_days = (today - mod_date).days
            if age_days <= threshold:
                continue

            # Check guardrails
            note_name = md_file.stem.lower()
            protected_by = []

            if note_name in active_refs:
                protected_by.append("referenced by active task")
            if note_name in recent_links:
                protected_by.append("has recent backlinks (< 90 days)")

            candidates.append({
                "file": str(md_file.relative_to(vault)),
                "name": md_file.stem,
                "staleness": staleness,
                "threshold_days": threshold,
                "age_days": age_days,
                "last_modified": str(modified),
                "protected": len(protected_by) > 0,
                "protection_reasons": protected_by,
            })
        except (ValueError, TypeError):
            continue

    # Sort by age descending
    candidates.sort(key=lambda c: c["age_days"], reverse=True)
    return candidates


def find_processed_inbox_items(vault_path, days_old=7):
    """Find processed inbox items older than N days for cleanup."""
    vault = Path(vault_path)
    processed_dir = vault / "inbox" / "processed"
    candidates = []
    today = date.today()

    if not processed_dir.exists():
        return candidates

    for f in processed_dir.iterdir():
        if f.name.startswith("."):
            continue

        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).date()
            age = (today - mtime).days
            if age >= days_old:
                candidates.append({
                    "file": str(f.relative_to(vault)),
                    "age_days": age,
                })
        except OSError:
            continue

    return candidates


def main():
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "."

    archive_candidates = find_archive_candidates(vault_path)
    inbox_cleanup = find_processed_inbox_items(vault_path)

    archivable = [c for c in archive_candidates if not c["protected"]]
    protected = [c for c in archive_candidates if c["protected"]]

    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "archive_candidates": len(archivable),
            "protected_from_archive": len(protected),
            "inbox_cleanup_candidates": len(inbox_cleanup),
        },
        "archive_candidates": archivable,
        "protected": protected,
        "inbox_cleanup": inbox_cleanup,
    }

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
