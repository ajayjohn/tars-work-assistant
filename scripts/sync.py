#!/usr/bin/env python3
"""TARS sync script.

Checks schedule.md for due items, scans for orphan tasks,
and identifies memory gaps. Designed to be invoked by the
/update skill which handles task tool queries separately.

Output: JSON report with due_items, orphan_tasks, and gaps.
Uses only Python standard library.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_schedule(workspace):
    """Parse reference/schedule.md for due items."""
    schedule_path = workspace / 'reference' / 'schedule.md'
    if not schedule_path.exists():
        return [], []

    try:
        with open(schedule_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return [], []

    today = datetime.now().strftime('%Y-%m-%d')
    recurring_due = []
    onetime_due = []

    # Parse recurring items: look for [RECURRING] markers
    recurring_pattern = re.compile(
        r'\[RECURRING\].*?next-due:\s*(\d{4}-\d{2}-\d{2}).*?(?:title|name|description):\s*(.+?)(?:\n|$)',
        re.IGNORECASE | re.DOTALL
    )
    # Simpler pattern: table rows or list items with dates
    line_pattern = re.compile(
        r'(?:\||\-)\s*(?:\[RECURRING\]|\[ONCE\])?\s*(.*?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|?'
    )

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Check for recurring items
        if '[RECURRING]' in line.upper():
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if date_match:
                due_date = date_match.group(1)
                if due_date <= today:
                    # Extract description (everything that's not the date or tag)
                    desc = re.sub(r'\[RECURRING\]', '', line, flags=re.IGNORECASE)
                    desc = re.sub(r'\d{4}-\d{2}-\d{2}', '', desc)
                    desc = re.sub(r'[|*\-]', ' ', desc).strip()
                    recurring_due.append({
                        'type': 'recurring',
                        'description': desc or 'Recurring item',
                        'due_date': due_date,
                    })

        # Check for one-time items
        elif '[ONCE]' in line.upper():
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if date_match:
                due_date = date_match.group(1)
                if due_date <= today:
                    desc = re.sub(r'\[ONCE\]', '', line, flags=re.IGNORECASE)
                    desc = re.sub(r'\d{4}-\d{2}-\d{2}', '', desc)
                    desc = re.sub(r'[|*\-]', ' ', desc).strip()
                    onetime_due.append({
                        'type': 'once',
                        'description': desc or 'One-time item',
                        'due_date': due_date,
                    })

    return recurring_due, onetime_due


def scan_journal_for_entities(workspace):
    """Scan recent journal entries for entity references."""
    journal_dir = workspace / 'journal'
    if not journal_dir.exists():
        return set(), set(), set()

    cutoff = datetime.now() - timedelta(days=30)
    people_refs = set()
    initiative_refs = set()
    term_refs = set()

    wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')
    name_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')

    for root, dirs, files in os.walk(journal_dir):
        for fname in files:
            if not fname.endswith('.md') or fname.startswith('_'):
                continue
            filepath = Path(root) / fname
            try:
                stat = filepath.stat()
                if datetime.fromtimestamp(stat.st_mtime) < cutoff:
                    continue
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            for match in wikilink_pattern.finditer(content):
                entity = match.group(1)
                # Simple heuristic: if it looks like a person name, add to people
                if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', entity):
                    people_refs.add(entity)
                else:
                    initiative_refs.add(entity)

            for match in name_pattern.finditer(content):
                people_refs.add(match.group(1))

    return people_refs, initiative_refs, term_refs


def load_known_entities(workspace):
    """Load known entities from memory indexes."""
    known_people = set()
    known_initiatives = set()

    # Load people
    people_index = workspace / 'memory' / 'people' / '_index.md'
    if people_index.exists():
        try:
            with open(people_index, 'r', encoding='utf-8') as f:
                for line in f:
                    # Extract names from table rows
                    match = re.match(r'\|\s*([^|]+?)\s*\|', line)
                    if match:
                        name = match.group(1).strip()
                        if name and name != 'Name' and not name.startswith('-'):
                            known_people.add(name)
        except (OSError, UnicodeDecodeError):
            pass

    # Load initiatives
    init_index = workspace / 'memory' / 'initiatives' / '_index.md'
    if init_index.exists():
        try:
            with open(init_index, 'r', encoding='utf-8') as f:
                for line in f:
                    match = re.match(r'\|\s*([^|]+?)\s*\|', line)
                    if match:
                        name = match.group(1).strip()
                        if name and name != 'Name' and not name.startswith('-'):
                            known_initiatives.add(name)
        except (OSError, UnicodeDecodeError):
            pass

    return known_people, known_initiatives


def detect_gaps(workspace):
    """Find entities referenced in journal but not in memory."""
    people_refs, initiative_refs, _ = scan_journal_for_entities(workspace)
    known_people, known_initiatives = load_known_entities(workspace)

    unknown_people = []
    for name in sorted(people_refs - known_people):
        unknown_people.append({'name': name, 'source': 'journal'})

    unknown_initiatives = []
    for name in sorted(initiative_refs - known_initiatives):
        if name not in known_people:  # Don't flag people as initiatives
            unknown_initiatives.append({'name': name, 'source': 'journal'})

    return unknown_people, unknown_initiatives


def main():
    if len(sys.argv) > 1:
        workspace = Path(sys.argv[1])
    else:
        workspace = Path('.')

    if not workspace.exists():
        print(json.dumps({'error': f'Workspace not found: {workspace}'}))
        sys.exit(1)

    # Check schedule
    recurring_due, onetime_due = parse_schedule(workspace)

    # Detect memory gaps
    unknown_people, unknown_initiatives = detect_gaps(workspace)

    report = {
        'workspace': str(workspace),
        'timestamp': datetime.now().isoformat(),
        'schedule': {
            'recurring_due': recurring_due,
            'onetime_due': onetime_due,
            'total_due': len(recurring_due) + len(onetime_due),
        },
        'memory_gaps': {
            'unknown_people': unknown_people,
            'unknown_initiatives': unknown_initiatives,
            'total_gaps': len(unknown_people) + len(unknown_initiatives),
        },
    }

    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
