#!/usr/bin/env python3
"""TARS archival sweep script.

Scans memory files for staleness, moves expired content to archive/,
expires ephemeral lines with [expires: YYYY-MM-DD] tags, and maintains
the archive index.

Staleness tiers:
  - durable:   Never auto-archives
  - seasonal:  180 days without update
  - transient: 90 days without access
  - ephemeral: Date-based expiry via [expires:] tags

Output: JSON report of archived files, expired lines, and stats.
Uses only Python standard library.
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None, ""

    if not content.startswith('---'):
        return None, content

    end = content.find('---', 3)
    if end == -1:
        return None, content

    fm_text = content[3:end].strip()
    body = content[end + 3:]

    fm = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.match(r'^(\w[\w-]*)\s*:\s*(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(',') if v.strip()]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            fm[key] = value

    return fm, body


def get_staleness_tier(fm):
    """Determine staleness tier from frontmatter."""
    staleness = fm.get('staleness', 'seasonal')
    if isinstance(staleness, str):
        staleness = staleness.lower().strip()
    if staleness in ('durable', 'seasonal', 'transient', 'ephemeral'):
        return staleness
    return 'seasonal'  # default


def check_staleness(filepath, fm, today):
    """Check if a file should be archived based on its staleness tier."""
    tier = get_staleness_tier(fm)

    if tier == 'durable':
        return False, tier

    updated_str = fm.get('updated', '')
    if not updated_str:
        return False, tier

    try:
        updated = datetime.strptime(str(updated_str)[:10], '%Y-%m-%d')
    except (ValueError, TypeError):
        return False, tier

    if tier == 'seasonal' and (today - updated).days > 180:
        return True, tier
    elif tier == 'transient' and (today - updated).days > 90:
        return True, tier

    return False, tier


def expire_ephemeral_lines(filepath, today_str):
    """Remove lines with expired [expires: YYYY-MM-DD] tags."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return 0

    expires_pattern = re.compile(r'\[expires:\s*(\d{4}-\d{2}-\d{2})\]')
    expired_count = 0
    new_lines = []

    for line in lines:
        match = expires_pattern.search(line)
        if match:
            expire_date = match.group(1)
            if expire_date <= today_str:
                expired_count += 1
                continue  # Skip this line (expired)
        new_lines.append(line)

    if expired_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return expired_count


def archive_file(filepath, workspace, archive_dir, today):
    """Move a file to the archive directory."""
    rel_path = filepath.relative_to(workspace)
    month_str = today.strftime('%Y-%m')

    # Determine category from path
    parts = rel_path.parts
    if len(parts) >= 2:
        category = parts[1]  # e.g., 'people' from 'memory/people/file.md'
    else:
        category = 'uncategorized'

    target_dir = archive_dir / month_str / category
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / filepath.name
    # Avoid overwriting existing archived files
    if target_path.exists():
        stem = filepath.stem
        suffix = filepath.suffix
        counter = 1
        while target_path.exists():
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    shutil.move(str(filepath), str(target_path))
    return str(target_path.relative_to(workspace))


def update_archive_index(archive_dir, archived_files):
    """Update or create the archive index."""
    index_path = archive_dir / '_archive_index.yaml'

    existing_entries = []
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Simple parse: each entry is a "- " line
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    existing_entries.append(line[2:])
        except (OSError, UnicodeDecodeError):
            pass

    # Add new entries
    for entry in archived_files:
        line = f"file: {entry['archive_path']} | original: {entry['original_path']} | date: {entry['date']} | reason: {entry['reason']}"
        existing_entries.append(line)

    # Write index
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('# Archive index\n\n')
        for entry in existing_entries:
            f.write(f'- {entry}\n')


def main():
    if len(sys.argv) > 1:
        workspace = Path(sys.argv[1])
    else:
        workspace = Path('.')

    dry_run = '--dry-run' in sys.argv

    if not workspace.exists():
        print(json.dumps({'error': f'Workspace not found: {workspace}'}))
        sys.exit(1)

    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    archive_dir = workspace / 'archive'

    archived_files = []
    expired_lines_total = 0
    skipped_durable = 0
    scanned = 0

    memory_dir = workspace / 'memory'
    if memory_dir.exists():
        for root, dirs, files in os.walk(memory_dir):
            for fname in files:
                if fname.startswith('_') or fname.startswith('.') or not fname.endswith('.md'):
                    continue

                filepath = Path(root) / fname
                scanned += 1
                fm, body = parse_frontmatter(filepath)

                if fm is None:
                    continue

                # Check ephemeral lines
                expired = expire_ephemeral_lines(filepath, today_str)
                expired_lines_total += expired

                # Check staleness
                should_archive, tier = check_staleness(filepath, fm, today)

                if tier == 'durable':
                    skipped_durable += 1
                    continue

                if should_archive:
                    original_path = str(filepath.relative_to(workspace))
                    if dry_run:
                        archived_files.append({
                            'original_path': original_path,
                            'archive_path': f'(dry run)',
                            'reason': f'{tier} staleness threshold exceeded',
                            'date': today_str,
                        })
                    else:
                        archive_path = archive_file(filepath, workspace, archive_dir, today)
                        archived_files.append({
                            'original_path': original_path,
                            'archive_path': archive_path,
                            'reason': f'{tier} staleness threshold exceeded',
                            'date': today_str,
                        })

    # Update archive index if we archived anything
    if archived_files and not dry_run:
        archive_dir.mkdir(parents=True, exist_ok=True)
        update_archive_index(archive_dir, archived_files)

    report = {
        'workspace': str(workspace),
        'timestamp': today.isoformat(),
        'dry_run': dry_run,
        'files_scanned': scanned,
        'files_archived': len(archived_files),
        'expired_lines_removed': expired_lines_total,
        'durable_skipped': skipped_durable,
        'archived_files': archived_files,
    }

    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
