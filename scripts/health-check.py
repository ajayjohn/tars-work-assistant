#!/usr/bin/env python3
"""TARS workspace health check.

Performs deterministic validation of workspace structure:
- File naming validation (decisions must be YYYY-MM-DD-slug.md)
- YAML frontmatter checks (required fields per type)
- Index-vs-file synchronization (orphan entries, missing entries)
- Wikilink validation (broken [[Entity]] references)
- Replacements coverage (names in journal not in replacements.md)

Output: JSON report with issues array, auto-fixes array, and summary stats.
Uses only Python standard library.
"""

import json
import os
import re
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

    # Simple YAML parser for flat key-value pairs
    fm = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.match(r'^(\w[\w-]*)\s*:\s*(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            # Handle YAML lists like [tag1, tag2]
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(',') if v.strip()]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            fm[key] = value

    return fm, body


def check_naming(workspace):
    """Validate decision file naming: YYYY-MM-DD-slug.md."""
    issues = []
    decisions_dir = workspace / 'memory' / 'decisions'
    if not decisions_dir.exists():
        return issues

    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.md$')

    for f in sorted(decisions_dir.iterdir()):
        if f.name.startswith('_') or f.name.startswith('.') or not f.name.endswith('.md'):
            continue
        if not pattern.match(f.name):
            fm, _ = parse_frontmatter(f)
            date_str = fm.get('date', fm.get('updated', '')) if fm else ''
            suggestion = ''
            if date_str and re.match(r'\d{4}-\d{2}-\d{2}', str(date_str)):
                slug = re.sub(r'^\d{4}-\d{2}-\d{2}-?', '', f.stem)
                if not slug:
                    slug = f.stem
                suggestion = f"{str(date_str)[:10]}-{slug}.md"

            issues.append({
                'category': 'naming',
                'file': str(f.relative_to(workspace)),
                'issue': 'Decision file does not match YYYY-MM-DD-slug.md pattern',
                'suggested_fix': f'Rename to {suggestion}' if suggestion else 'Add date prefix from frontmatter'
            })

    return issues


def check_frontmatter(workspace):
    """Validate required frontmatter fields per memory type."""
    issues = []
    required_base = ['title', 'type', 'summary', 'updated']
    required_extra = {
        'person': ['tags', 'aliases'],
        'decision': ['status'],
        'product-spec': ['status', 'owner'],
    }
    valid_decision_statuses = {'proposed', 'decided', 'implemented', 'superseded', 'rejected'}
    valid_product_statuses = {'active', 'planned', 'deprecated'}

    memory_dir = workspace / 'memory'
    if not memory_dir.exists():
        return issues

    for root, dirs, files in os.walk(memory_dir):
        # Skip index files
        for fname in sorted(files):
            if fname.startswith('_') or fname.startswith('.') or not fname.endswith('.md'):
                continue
            filepath = Path(root) / fname
            fm, _ = parse_frontmatter(filepath)
            rel_path = str(filepath.relative_to(workspace))

            if fm is None:
                issues.append({
                    'category': 'frontmatter',
                    'file': rel_path,
                    'issue': 'No YAML frontmatter found',
                    'suggested_fix': 'Add standard frontmatter template'
                })
                continue

            # Check base required fields
            for field in required_base:
                if field not in fm:
                    issues.append({
                        'category': 'frontmatter',
                        'file': rel_path,
                        'issue': f'Missing required field: {field}',
                        'suggested_fix': f'Add {field} to frontmatter'
                    })

            # Check type-specific fields
            ftype = fm.get('type', '')
            if ftype in required_extra:
                for field in required_extra[ftype]:
                    if field not in fm:
                        issues.append({
                            'category': 'frontmatter',
                            'file': rel_path,
                            'issue': f'Missing required field for {ftype}: {field}',
                            'suggested_fix': f'Add {field} to frontmatter'
                        })

            # Validate status values
            status = fm.get('status', '')
            if ftype == 'decision' and status and status not in valid_decision_statuses:
                issues.append({
                    'category': 'frontmatter',
                    'file': rel_path,
                    'issue': f'Invalid decision status: "{status}"',
                    'suggested_fix': f'Change to one of: {", ".join(sorted(valid_decision_statuses))}'
                })
            if ftype in ('product', 'product-spec') and status and status not in valid_product_statuses:
                issues.append({
                    'category': 'frontmatter',
                    'file': rel_path,
                    'issue': f'Invalid product status: "{status}"',
                    'suggested_fix': f'Change to one of: {", ".join(sorted(valid_product_statuses))}'
                })

    return issues


def check_index_sync(workspace):
    """Check for orphaned index entries and files missing from indexes."""
    issues = []
    memory_dir = workspace / 'memory'
    if not memory_dir.exists():
        return issues

    categories = ['people', 'initiatives', 'decisions', 'products', 'vendors', 'competitors', 'organizational-context']

    for cat in categories:
        cat_dir = memory_dir / cat
        if not cat_dir.exists():
            continue

        index_path = cat_dir / '_index.md'
        # Get actual files
        actual_files = set()
        for f in cat_dir.iterdir():
            if f.name.endswith('.md') and not f.name.startswith('_') and not f.name.startswith('.'):
                actual_files.add(f.name)

        # Parse index entries (look for filenames in the index)
        indexed_files = set()
        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_content = f.read()
                # Match filenames in table rows or YAML entries
                for match in re.finditer(r'[\|:]\s*(\S+\.md)\s*[\|]?', index_content):
                    indexed_files.add(match.group(1))
                # Also try YAML-style: file: something.md
                for match in re.finditer(r'file:\s*(\S+\.md)', index_content):
                    indexed_files.add(match.group(1))
            except (OSError, UnicodeDecodeError):
                pass

        # Orphaned index entries (in index but no file)
        for fname in sorted(indexed_files - actual_files):
            issues.append({
                'category': 'index',
                'file': f'memory/{cat}/_index.md',
                'issue': f'Orphan entry: "{fname}" in index but file does not exist',
                'suggested_fix': f'Remove "{fname}" from index'
            })

        # Missing from index (file exists but not in index)
        for fname in sorted(actual_files - indexed_files):
            if indexed_files:  # Only flag if index has content (not empty template)
                issues.append({
                    'category': 'index',
                    'file': f'memory/{cat}/{fname}',
                    'issue': f'File not in index: memory/{cat}/_index.md',
                    'suggested_fix': f'Add to memory/{cat}/_index.md or run /rebuild-index'
                })

    return issues


def check_wikilinks(workspace):
    """Find broken [[Entity]] references."""
    issues = []

    # Build entity registry from all memory indexes
    known_entities = set()
    memory_dir = workspace / 'memory'
    if not memory_dir.exists():
        return issues

    for root, dirs, files in os.walk(memory_dir):
        for fname in files:
            if fname.startswith('_') or fname.startswith('.') or not fname.endswith('.md'):
                continue
            filepath = Path(root) / fname
            fm, _ = parse_frontmatter(filepath)
            if fm:
                title = fm.get('title', '')
                if title:
                    known_entities.add(title.lower())
                aliases = fm.get('aliases', [])
                if isinstance(aliases, list):
                    for a in aliases:
                        known_entities.add(str(a).lower())

    # Scan for wikilinks in memory, journal, contexts
    scan_dirs = ['memory', 'journal', 'contexts']
    wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')

    for scan_dir in scan_dirs:
        target = workspace / scan_dir
        if not target.exists():
            continue
        for root, dirs, files in os.walk(target):
            for fname in files:
                if not fname.endswith('.md') or fname.startswith('_'):
                    continue
                filepath = Path(root) / fname
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError):
                    continue

                for match in wikilink_pattern.finditer(content):
                    entity = match.group(1)
                    if entity.lower() not in known_entities:
                        rel_path = str(filepath.relative_to(workspace))
                        issues.append({
                            'category': 'wikilink',
                            'file': rel_path,
                            'issue': f'Broken wikilink: [[{entity}]]',
                            'suggested_fix': f'Create memory entry for "{entity}" or fix the reference'
                        })

    # Deduplicate (same broken link may appear many times)
    seen = set()
    deduped = []
    for issue in issues:
        key = (issue['file'], issue['issue'])
        if key not in seen:
            seen.add(key)
            deduped.append(issue)

    return deduped


def check_replacements_coverage(workspace):
    """Find names in recent journal entries not in replacements.md."""
    issues = []
    auto_fixes = []

    # Load replacements
    replacements_path = workspace / 'reference' / 'replacements.md'
    known_names = set()
    if replacements_path.exists():
        try:
            with open(replacements_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Extract names from table rows: | Name | Canonical |
            for match in re.finditer(r'\|\s*([^|]+?)\s*\|', content):
                name = match.group(1).strip()
                if name and name != 'Name' and name != '---' and not name.startswith('-'):
                    known_names.add(name.lower())
        except (OSError, UnicodeDecodeError):
            pass

    # Scan recent journal entries (last 30 days)
    journal_dir = workspace / 'journal'
    if not journal_dir.exists():
        return issues, auto_fixes

    cutoff = datetime.now() - timedelta(days=30)
    name_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
    acronym_pattern = re.compile(r'\b([A-Z]{2,5})\b')

    name_counts = {}
    acronym_counts = {}

    for root, dirs, files in os.walk(journal_dir):
        for fname in files:
            if not fname.endswith('.md') or fname.startswith('_'):
                continue
            filepath = Path(root) / fname
            # Check if file is recent enough
            try:
                stat = filepath.stat()
                if datetime.fromtimestamp(stat.st_mtime) < cutoff:
                    continue
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            for match in name_pattern.finditer(content):
                name = match.group(1)
                if name.lower() not in known_names:
                    name_counts[name] = name_counts.get(name, 0) + 1

            for match in acronym_pattern.finditer(content):
                acr = match.group(1)
                # Skip common words that look like acronyms
                skip = {'THE', 'AND', 'FOR', 'NOT', 'BUT', 'ARE', 'WAS', 'HAS', 'HAD', 'GET',
                        'SET', 'PUT', 'NEW', 'OLD', 'ALL', 'ANY', 'FEW', 'HOW', 'WHO', 'OUR',
                        'OUT', 'NOW', 'WAY', 'MAY', 'SAY', 'SHE', 'TWO', 'ITS', 'LET', 'TOP',
                        'USE', 'HER', 'HIM', 'SEE', 'TRY', 'RUN', 'ADD', 'END', 'KEY', 'BIG',
                        'JSON', 'YAML', 'HTML', 'HTTP', 'HTTPS', 'URL', 'API', 'CLI', 'MCP',
                        'README', 'TODO', 'NOTE', 'TARS'}
                if acr in skip or acr.lower() in known_names:
                    continue
                acronym_counts[acr] = acronym_counts.get(acr, 0) + 1

    # Flag names appearing 2+ times
    for name, count in sorted(name_counts.items(), key=lambda x: -x[1]):
        if count >= 2:
            issues.append({
                'category': 'replacements',
                'file': 'journal/',
                'issue': f'"{name}" appears {count} times but is not in replacements.md',
                'suggested_fix': f'Add to reference/replacements.md'
            })
            auto_fixes.append({
                'action': 'add_replacement',
                'name': name,
                'count': count
            })

    for acr, count in sorted(acronym_counts.items(), key=lambda x: -x[1]):
        if count >= 2:
            issues.append({
                'category': 'replacements',
                'file': 'journal/',
                'issue': f'Acronym "{acr}" appears {count} times but is not in replacements.md',
                'suggested_fix': f'Add to reference/replacements.md'
            })

    return issues, auto_fixes


def main():
    if len(sys.argv) > 1:
        workspace = Path(sys.argv[1])
    else:
        workspace = Path('.')

    if not workspace.exists():
        print(json.dumps({'error': f'Workspace not found: {workspace}'}))
        sys.exit(1)

    all_issues = []
    auto_fixes = []

    # Run all checks
    all_issues.extend(check_naming(workspace))
    all_issues.extend(check_frontmatter(workspace))
    all_issues.extend(check_index_sync(workspace))
    all_issues.extend(check_wikilinks(workspace))

    replacement_issues, replacement_fixes = check_replacements_coverage(workspace)
    all_issues.extend(replacement_issues)
    auto_fixes.extend(replacement_fixes)

    # Build summary
    categories = {}
    for issue in all_issues:
        cat = issue['category']
        categories[cat] = categories.get(cat, 0) + 1

    report = {
        'workspace': str(workspace),
        'timestamp': datetime.now().isoformat(),
        'total_issues': len(all_issues),
        'issues_by_category': categories,
        'issues': all_issues,
        'auto_fixes': auto_fixes,
        'summary': {
            'naming_issues': categories.get('naming', 0),
            'frontmatter_issues': categories.get('frontmatter', 0),
            'index_issues': categories.get('index', 0),
            'wikilink_issues': categories.get('wikilink', 0),
            'replacement_issues': categories.get('replacements', 0),
        }
    }

    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
