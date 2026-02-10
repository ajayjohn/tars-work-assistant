#!/usr/bin/env python3
"""TARS index rebuilder.

Parses frontmatter from all memory, journal, and context files,
then regenerates _index.md files in YAML format.

Output: JSON report of what was regenerated and any issues found.
Uses only Python standard library.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    if not content.startswith('---'):
        return None

    end = content.find('---', 3)
    if end == -1:
        return None

    fm_text = content[3:end].strip()
    fm = {}
    current_key = None
    current_list = None

    for line in fm_text.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Handle relationships as a list of dicts (skip complex nested YAML)
        if stripped == 'relationships:':
            current_key = 'relationships'
            fm['relationships'] = []
            current_list = fm['relationships']
            continue

        if current_key == 'relationships' and stripped.startswith('- type:'):
            rel = {'type': stripped.split(':', 1)[1].strip()}
            current_list.append(rel)
            continue

        if current_key == 'relationships' and stripped.startswith('target:'):
            if current_list:
                current_list[-1]['target'] = stripped.split(':', 1)[1].strip().strip('"\'')
            continue

        if current_key == 'relationships' and stripped.startswith('context:'):
            if current_list:
                current_list[-1]['context'] = stripped.split(':', 1)[1].strip().strip('"\'')
            continue

        # Standard key: value parsing
        match = re.match(r'^(\w[\w-]*)\s*:\s*(.+)$', line.strip())
        if match:
            current_key = None
            current_list = None
            key = match.group(1)
            value = match.group(2).strip()
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(',') if v.strip()]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            fm[key] = value

    return fm


def list_md_files(directory):
    """List .md files in a directory, excluding _index.md and _template.md."""
    if not directory.exists():
        return []
    files = []
    for f in sorted(directory.iterdir()):
        if f.name.endswith('.md') and not f.name.startswith('_') and not f.name.startswith('.'):
            files.append(f)
    return files


def yaml_escape(value):
    """Escape a string value for YAML output."""
    if value is None:
        return '""'
    s = str(value)
    if not s:
        return '""'
    # Quote if contains special chars or looks like a number/boolean
    needs_quote = any(c in s for c in ':#{}[]|>&*!?,\'"') or s.lower() in ('true', 'false', 'null', 'yes', 'no')
    if needs_quote:
        return '"' + s.replace('"', '\\"') + '"'
    return s


def yaml_list(items, indent=4):
    """Format a list as YAML inline array."""
    if not items:
        return '[]'
    if isinstance(items, str):
        return '[' + items + ']'
    escaped = [yaml_escape(i) for i in items]
    inline = '[' + ', '.join(escaped) + ']'
    if len(inline) < 80:
        return inline
    # Fall back to multi-line
    prefix = ' ' * indent
    return '\n'.join(f'{prefix}- {yaml_escape(i)}' for i in items)


def rebuild_memory_index(category_dir, category_name):
    """Rebuild _index.md for a memory category in YAML format."""
    files = list_md_files(category_dir)
    issues = []
    entries = []

    for filepath in files:
        fm = parse_frontmatter(filepath)
        if fm is None:
            issues.append({
                'type': 'missing-frontmatter',
                'file': str(filepath),
                'issue': 'No frontmatter',
                'suggested_fix': 'Add required fields'
            })
            continue

        title = fm.get('title', filepath.stem)
        aliases = fm.get('aliases', [])
        if isinstance(aliases, str):
            aliases = [aliases]
        summary = fm.get('summary', '')
        updated = fm.get('updated', '')
        tags = fm.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        staleness = fm.get('staleness', 'seasonal')

        if not summary:
            issues.append({
                'type': 'missing-required',
                'file': str(filepath.name),
                'issue': 'Missing summary field',
                'suggested_fix': 'Add summary for index'
            })

        entries.append({
            'name': title,
            'aliases': aliases,
            'file': filepath.name,
            'summary': summary,
            'updated': str(updated),
            'tags': tags,
            'staleness': staleness,
        })

    # Generate YAML index content
    today = datetime.now().strftime('%Y-%m-%d')
    lines = [
        '---',
        'type: index',
        f'category: {category_name}',
        f'updated: {today}',
        f'count: {len(entries)}',
        '---',
    ]

    if category_name == 'initiatives':
        # Separate active and completed
        active = [e for e in entries if 'completed' not in (e.get('tags') or [])]
        completed = [e for e in entries if 'completed' in (e.get('tags') or [])]

        if active:
            lines.append('active:')
            for e in active:
                lines.append(f'  - name: {yaml_escape(e["name"])}')
                lines.append(f'    file: {e["file"]}')
                lines.append(f'    aliases: {yaml_list(e["aliases"])}')
                lines.append(f'    summary: {yaml_escape(e["summary"])}')
                lines.append(f'    tags: {yaml_list(e["tags"])}')
                lines.append(f'    staleness: {e["staleness"]}')
                lines.append(f'    updated: {e["updated"]}')

        if completed:
            lines.append('completed:')
            for e in completed:
                lines.append(f'  - name: {yaml_escape(e["name"])}')
                lines.append(f'    file: {e["file"]}')
                lines.append(f'    aliases: {yaml_list(e["aliases"])}')
                lines.append(f'    summary: {yaml_escape(e["summary"])}')
                lines.append(f'    tags: {yaml_list(e["tags"])}')
                lines.append(f'    staleness: {e["staleness"]}')
                lines.append(f'    updated: {e["updated"]}')

        if not active and not completed:
            lines.append('active: []')
            lines.append('completed: []')
    else:
        lines.append('entries:')
        if entries:
            for e in entries:
                lines.append(f'  - name: {yaml_escape(e["name"])}')
                lines.append(f'    file: {e["file"]}')
                lines.append(f'    aliases: {yaml_list(e["aliases"])}')
                lines.append(f'    summary: {yaml_escape(e["summary"])}')
                lines.append(f'    tags: {yaml_list(e["tags"])}')
                lines.append(f'    staleness: {e["staleness"]}')
                lines.append(f'    updated: {e["updated"]}')
        else:
            lines[-1] = 'entries: []'

    index_path = category_dir / '_index.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    return len(entries), issues


def rebuild_master_index(workspace):
    """Rebuild memory/_index.md with category counts in YAML format."""
    memory_dir = workspace / 'memory'
    categories = ['people', 'initiatives', 'decisions', 'products', 'vendors', 'competitors', 'organizational-context']

    today = datetime.now().strftime('%Y-%m-%d')
    total = 0

    cat_data = []
    for cat in categories:
        cat_dir = memory_dir / cat
        count = len(list_md_files(cat_dir)) if cat_dir.exists() else 0
        total += count
        cat_data.append({'name': cat, 'path': f'memory/{cat}/', 'count': count})

    lines = [
        '---',
        'type: master-index',
        f'updated: {today}',
        f'total_entities: {total}',
        '---',
        'categories:',
    ]

    for c in cat_data:
        lines.append(f'  - name: {c["name"]}')
        lines.append(f'    path: {c["path"]}')
        lines.append(f'    count: {c["count"]}')

    index_path = memory_dir / '_index.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def rebuild_journal_indexes(workspace):
    """Rebuild _index.md for each journal month folder in YAML format."""
    journal_dir = workspace / 'journal'
    if not journal_dir.exists():
        return 0, []

    months_rebuilt = 0
    issues = []

    for month_dir in sorted(journal_dir.iterdir()):
        if not month_dir.is_dir() or month_dir.name.startswith('.'):
            continue

        files = list_md_files(month_dir)
        if not files:
            continue

        entries = []
        for filepath in files:
            fm = parse_frontmatter(filepath)
            if fm is None:
                issues.append({
                    'type': 'missing-frontmatter',
                    'file': str(filepath),
                    'issue': 'No frontmatter in journal entry',
                    'suggested_fix': 'Add date, type, title fields'
                })
                continue

            participants = fm.get('participants', [])
            if isinstance(participants, str):
                participants = [participants]
            initiatives = fm.get('initiatives', [])
            if isinstance(initiatives, str):
                initiatives = [initiatives]

            entries.append({
                'date': fm.get('date', ''),
                'type': fm.get('type', ''),
                'title': fm.get('title', filepath.stem),
                'file': filepath.name,
                'participants': participants,
                'initiatives': initiatives,
            })

        # Generate YAML index
        today = datetime.now().strftime('%Y-%m-%d')
        lines = [
            '---',
            'type: journal-index',
            f'period: {month_dir.name}',
            f'updated: {today}',
            f'count: {len(entries)}',
            '---',
            'entries:',
        ]

        if entries:
            for e in entries:
                lines.append(f'  - date: {e["date"]}')
                lines.append(f'    type: {e["type"]}')
                lines.append(f'    title: {yaml_escape(e["title"])}')
                lines.append(f'    file: {e["file"]}')
                lines.append(f'    participants: {yaml_list(e["participants"])}')
                lines.append(f'    initiatives: {yaml_list(e["initiatives"])}')
        else:
            lines[-1] = 'entries: []'

        index_path = month_dir / '_index.md'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

        months_rebuilt += 1

    return months_rebuilt, issues


def rebuild_contexts_index(workspace):
    """Rebuild contexts/products/_index.md in YAML format."""
    products_dir = workspace / 'contexts' / 'products'
    if not products_dir.exists():
        return 0, []

    files = list_md_files(products_dir)
    issues = []
    entries = []

    for filepath in files:
        fm = parse_frontmatter(filepath)
        if fm is None:
            issues.append({
                'type': 'missing-frontmatter',
                'file': str(filepath),
                'issue': 'No frontmatter',
                'suggested_fix': 'Add product-spec template'
            })
            continue

        entries.append({
            'name': fm.get('title', filepath.stem),
            'file': filepath.name,
            'status': fm.get('status', ''),
            'owner': fm.get('owner', ''),
            'summary': fm.get('summary', ''),
            'updated': fm.get('updated', ''),
        })

    today = datetime.now().strftime('%Y-%m-%d')
    lines = [
        '---',
        'type: product-index',
        f'updated: {today}',
        f'count: {len(entries)}',
        '---',
        'entries:',
    ]

    if entries:
        for e in entries:
            lines.append(f'  - name: {yaml_escape(e["name"])}')
            lines.append(f'    file: {e["file"]}')
            lines.append(f'    status: {e["status"]}')
            lines.append(f'    owner: {yaml_escape(e["owner"])}')
            lines.append(f'    summary: {yaml_escape(e["summary"])}')
            lines.append(f'    updated: {e["updated"]}')
    else:
        lines[-1] = 'entries: []'

    index_path = products_dir / '_index.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    return len(entries), issues


def check_decision_naming(workspace):
    """Validate decision file naming convention."""
    issues = []
    decisions_dir = workspace / 'memory' / 'decisions'
    if not decisions_dir.exists():
        return issues

    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.md$')

    for f in sorted(decisions_dir.iterdir()):
        if f.name.startswith('_') or f.name.startswith('.') or not f.name.endswith('.md'):
            continue
        if not pattern.match(f.name):
            fm = parse_frontmatter(f)
            date_str = fm.get('date', fm.get('updated', '')) if fm else ''
            suggestion = ''
            if date_str and re.match(r'\d{4}-\d{2}-\d{2}', str(date_str)):
                slug = re.sub(r'^\d{4}-\d{2}-\d{2}-?', '', f.stem)
                if not slug:
                    slug = f.stem
                suggestion = f"{str(date_str)[:10]}-{slug}.md"

            issues.append({
                'type': 'naming-violation',
                'file': f'memory/decisions/{f.name}',
                'issue': 'Missing date prefix',
                'suggested_fix': f'Rename to {suggestion}' if suggestion else 'Add YYYY-MM-DD prefix'
            })

    return issues


def main():
    if len(sys.argv) > 1:
        workspace = Path(sys.argv[1])
    else:
        workspace = Path('.')

    if not workspace.exists():
        print(json.dumps({'error': f'Workspace not found: {workspace}'}))
        sys.exit(1)

    memory_dir = workspace / 'memory'
    all_issues = []
    stats = {
        'memory_categories': 0,
        'journal_months': 0,
        'contexts_products': 0,
        'total_entries': 0,
    }

    # Rebuild memory category indexes
    categories = ['people', 'initiatives', 'decisions', 'products', 'vendors', 'competitors', 'organizational-context']
    for cat in categories:
        cat_dir = memory_dir / cat
        if cat_dir.exists():
            count, issues = rebuild_memory_index(cat_dir, cat)
            stats['memory_categories'] += 1
            stats['total_entries'] += count
            all_issues.extend(issues)

    # Rebuild master index
    if memory_dir.exists():
        rebuild_master_index(workspace)

    # Rebuild journal indexes
    months, journal_issues = rebuild_journal_indexes(workspace)
    stats['journal_months'] = months
    all_issues.extend(journal_issues)

    # Rebuild contexts/products index
    products_count, ctx_issues = rebuild_contexts_index(workspace)
    stats['contexts_products'] = products_count
    all_issues.extend(ctx_issues)

    # Check decision naming
    naming_issues = check_decision_naming(workspace)
    all_issues.extend(naming_issues)

    report = {
        'workspace': str(workspace),
        'timestamp': datetime.now().isoformat(),
        'format': 'yaml',
        'stats': stats,
        'issues': all_issues,
        'total_issues': len(all_issues),
    }

    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
