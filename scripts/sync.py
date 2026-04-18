#!/usr/bin/env python3
"""
TARS v3 Sync Script
Identifies gaps between calendar events and journal entries,
task system drift, and memory staleness.
Outputs JSON for agent consumption.

Usage: python3 scripts/sync.py [vault_path]
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime, date, timedelta

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_frontmatter(file_path):
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return None

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None

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
                    if val.startswith("[") and val.endswith("]"):
                        val = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
                    fm[key.strip()] = val
        return fm if isinstance(fm, dict) else None
    except Exception:
        return None


def find_meeting_journals(vault_path, days_back=7):
    """Find meeting journal entries from the past N days."""
    vault = Path(vault_path)
    journal_dir = vault / "journal"
    today = date.today()
    cutoff = today - timedelta(days=days_back)

    meetings = []
    if not journal_dir.exists():
        return meetings

    for md_file in journal_dir.rglob("*.md"):
        fm = parse_frontmatter(md_file)
        if not fm:
            continue

        tags = fm.get("tags", [])
        if not isinstance(tags, list):
            tags = [tags] if tags else []

        if "tars/meeting" not in tags:
            continue

        meeting_date = fm.get("tars-date")
        if meeting_date:
            try:
                if isinstance(meeting_date, str):
                    md = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                elif isinstance(meeting_date, date):
                    md = meeting_date
                else:
                    continue

                if md >= cutoff:
                    meetings.append({
                        "file": str(md_file.relative_to(vault)),
                        "date": str(meeting_date),
                        "title": fm.get("tars-calendar-title", md_file.stem),
                        "participants": fm.get("tars-participants", []),
                    })
            except ValueError:
                continue

    return meetings


def find_recent_people_in_meetings(vault_path, days_back=7):
    """Find people referenced in recent meetings."""
    meetings = find_meeting_journals(vault_path, days_back)
    people = set()

    for meeting in meetings:
        participants = meeting.get("participants", [])
        if isinstance(participants, list):
            for p in participants:
                # Extract name from wikilink: [[Name]] → Name
                name = re.sub(r'\[\[|\]\]', '', str(p))
                if name:
                    people.add(name)

    return people


def check_memory_freshness(vault_path, recent_people, days_stale=60):
    """Check if people in recent meetings have stale memory files."""
    vault = Path(vault_path)
    people_dir = vault / "memory" / "people"
    stale = []
    missing = []
    today = date.today()

    if not people_dir.exists():
        return stale, list(recent_people)

    existing_people = {}
    for md_file in people_dir.rglob("*.md"):
        fm = parse_frontmatter(md_file)
        if fm:
            name = md_file.stem
            existing_people[name.lower()] = {
                "file": str(md_file.relative_to(vault)),
                "modified": fm.get("tars-modified"),
            }
            # Also check aliases
            aliases = fm.get("aliases", [])
            if isinstance(aliases, list):
                for alias in aliases:
                    existing_people[str(alias).lower()] = existing_people[name.lower()]

    for person in recent_people:
        person_lower = person.lower()
        if person_lower in existing_people:
            info = existing_people[person_lower]
            modified = info.get("modified")
            if modified:
                try:
                    if isinstance(modified, str):
                        mod_date = datetime.strptime(modified, "%Y-%m-%d").date()
                    elif isinstance(modified, date):
                        mod_date = modified
                    else:
                        continue

                    age = (today - mod_date).days
                    if age > days_stale:
                        stale.append({
                            "person": person,
                            "file": info["file"],
                            "last_modified": str(modified),
                            "days_since_update": age,
                        })
                except ValueError:
                    pass
        else:
            missing.append(person)

    return stale, missing


def count_tagged_notes(vault_path, tag, subdir=None):
    """Count markdown files whose frontmatter `tags` include the given tag.

    Scans the whole vault when ``subdir`` is None; otherwise confined to that
    subdirectory. Used to rebuild hydration counters in `_system/maturity.yaml`
    so the "Level 1" briefing artifact goes away (§5.2).
    """
    vault = Path(vault_path)
    root = vault / subdir if subdir else vault
    if not root.exists():
        return 0
    count = 0
    for md_file in root.rglob("*.md"):
        # Skip system / archive / template files; they aren't content.
        rel = md_file.relative_to(vault).parts
        if rel and rel[0] in ("_system", "archive", "templates", "_views"):
            continue
        fm = parse_frontmatter(md_file)
        if not fm:
            continue
        tags = fm.get("tags", [])
        if not isinstance(tags, list):
            tags = [tags] if tags else []
        if tag in tags:
            count += 1
    return count


def compute_hydration(vault_path):
    """Return current hydration counts for _system/maturity.yaml."""
    return {
        "people_count":     count_tagged_notes(vault_path, "tars/person",     "memory/people"),
        "initiative_count": count_tagged_notes(vault_path, "tars/initiative", "memory/initiatives"),
        "decision_count":   count_tagged_notes(vault_path, "tars/decision",   "memory/decisions"),
        "journal_count":    count_tagged_notes(vault_path, "tars/journal",    "journal"),
        "task_count":       count_tagged_notes(vault_path, "tars/task"),
        "last_checked":     date.today().isoformat(),
    }


def check_task_freshness(vault_path):
    """Find tasks that may need attention."""
    vault = Path(vault_path)
    today = date.today()
    issues = []

    # Scan for task files
    for scan_dir in ["memory"]:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue

        for md_file in dir_path.rglob("*.md"):
            fm = parse_frontmatter(md_file)
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

            due = fm.get("tars-due")
            if due:
                try:
                    if isinstance(due, str):
                        due_date = datetime.strptime(due, "%Y-%m-%d").date()
                    elif isinstance(due, date):
                        due_date = due
                    else:
                        continue

                    days_overdue = (today - due_date).days
                    if days_overdue > 0:
                        issues.append({
                            "file": str(md_file.relative_to(vault)),
                            "task": md_file.stem,
                            "due": str(due),
                            "days_overdue": days_overdue,
                            "status": status,
                        })
                except ValueError:
                    pass

    return issues


def main():
    args = [a for a in sys.argv[1:] if a]
    hydration_only = "--hydration" in args
    vault_args = [a for a in args if not a.startswith("--")]
    vault_path = vault_args[0] if vault_args else "."

    if hydration_only:
        # Fast path for the briefing skill: only compute live counts, skip
        # the meeting / task / freshness scans.
        print(json.dumps({"hydration": compute_hydration(vault_path)}, indent=2))
        sys.exit(0)

    # Check for meeting-journal gaps
    recent_meetings = find_meeting_journals(vault_path, days_back=7)

    # Check memory freshness
    recent_people = find_recent_people_in_meetings(vault_path, days_back=7)
    stale_people, missing_people = check_memory_freshness(vault_path, recent_people)

    # Check task freshness
    overdue_tasks = check_task_freshness(vault_path)

    # Hydration counts for _system/maturity.yaml (closes the "Level 1" artifact
    # bug where briefings parroted zeros despite hundreds of notes on disk).
    hydration = compute_hydration(vault_path)

    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "recent_meetings": len(recent_meetings),
            "stale_people": len(stale_people),
            "missing_people": len(missing_people),
            "overdue_tasks": len(overdue_tasks),
        },
        "hydration": hydration,
        "recent_meetings": recent_meetings,
        "stale_people": stale_people,
        "missing_people": missing_people,
        "overdue_tasks": overdue_tasks,
    }

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
