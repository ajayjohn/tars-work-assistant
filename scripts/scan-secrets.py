#!/usr/bin/env python3
"""TARS sensitive data scanner.

Scans content for secrets, credentials, and PII using regex patterns
from reference/guardrails.yaml. Accepts content via stdin or file path.

Output: JSON report: {"clean": true} or {"clean": false, "matches": [...]}.
Uses only Python standard library.
"""

import json
import os
import re
import sys
from pathlib import Path


# Default patterns (used if guardrails.yaml is not found or unparseable)
DEFAULT_PATTERNS = [
    {
        'type': 'ssn',
        'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
        'label': 'Social Security Number',
        'action': 'block',
    },
    {
        'type': 'api_key',
        'pattern': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*\S+',
        'label': 'API Key',
        'action': 'block',
    },
    {
        'type': 'password',
        'pattern': r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+',
        'label': 'Password',
        'action': 'block',
    },
    {
        'type': 'bearer_token',
        'pattern': r'(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*',
        'label': 'Bearer Token',
        'action': 'block',
    },
    {
        'type': 'client_secret',
        'pattern': r'(?i)(client[_-]?secret|secret[_-]?key)\s*[:=]\s*\S+',
        'label': 'Client Secret',
        'action': 'block',
    },
    {
        'type': 'jwt',
        'pattern': r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
        'label': 'JWT Token',
        'action': 'block',
    },
    {
        'type': 'dob',
        'pattern': r'(?i)(date\s*of\s*birth|dob|born\s*on)\s*[:=]?\s*\d',
        'label': 'Date of Birth',
        'action': 'warn',
    },
    {
        'type': 'private_key',
        'pattern': r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
        'label': 'Private Key',
        'action': 'block',
    },
    {
        'type': 'connection_string',
        'pattern': r'(?i)(mongodb|postgres|mysql|redis)://\S+:\S+@',
        'label': 'Database Connection String',
        'action': 'block',
    },
]


def load_patterns(workspace):
    """Load patterns from reference/guardrails.yaml (simple parser)."""
    guardrails_path = workspace / 'reference' / 'guardrails.yaml'
    if not guardrails_path.exists():
        return DEFAULT_PATTERNS

    try:
        with open(guardrails_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return DEFAULT_PATTERNS

    # Simple YAML parser for the guardrails format
    patterns = []
    current = {}

    for line in content.split('\n'):
        stripped = line.strip()

        if stripped.startswith('- type:'):
            if current and 'pattern' in current:
                patterns.append(current)
            current = {'type': stripped.split(':', 1)[1].strip()}
        elif stripped.startswith('pattern:') and current:
            # Extract pattern, handling quotes
            pat = stripped.split(':', 1)[1].strip()
            pat = pat.strip("'\"")
            current['pattern'] = pat
        elif stripped.startswith('label:') and current:
            current['label'] = stripped.split(':', 1)[1].strip().strip('"\'')
        elif stripped.startswith('action:') and current:
            current['action'] = stripped.split(':', 1)[1].strip()

    if current and 'pattern' in current:
        patterns.append(current)

    return patterns if patterns else DEFAULT_PATTERNS


def scan_content(content, patterns):
    """Scan content against all patterns."""
    matches = []
    lines = content.split('\n')

    for pattern_def in patterns:
        try:
            regex = re.compile(pattern_def['pattern'])
        except re.error:
            continue

        for line_num, line in enumerate(lines, 1):
            for match in regex.finditer(line):
                matched_text = match.group(0)
                # Redact the match for safety (show first 4 and last 2 chars)
                if len(matched_text) > 10:
                    redacted = matched_text[:4] + '...' + matched_text[-2:]
                else:
                    redacted = matched_text[:3] + '...'

                matches.append({
                    'type': pattern_def.get('type', 'unknown'),
                    'label': pattern_def.get('label', 'Unknown'),
                    'line': line_num,
                    'action': pattern_def.get('action', 'warn'),
                    'snippet': redacted,
                })

    return matches


def main():
    # Determine workspace for loading guardrails.yaml
    workspace = Path('.')
    content = None

    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]

    # Parse --workspace flag
    for i, flag in enumerate(flags):
        if flag.startswith('--workspace='):
            workspace = Path(flag.split('=', 1)[1])
        elif flag == '--workspace' and i + 1 < len(flags):
            workspace = Path(flags[i + 1])

    # Get content from file argument or stdin
    if args:
        filepath = Path(args[0])
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError) as e:
                print(json.dumps({'error': f'Cannot read file: {e}'}))
                sys.exit(1)
        else:
            # Treat as inline content
            content = ' '.join(args)
    else:
        # Read from stdin
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print(json.dumps({'error': 'No content provided. Pass a file path or pipe content via stdin.'}))
            sys.exit(1)

    if not content:
        print(json.dumps({'clean': True, 'matches': []}))
        sys.exit(0)

    # Load patterns
    patterns = load_patterns(workspace)

    # Scan
    matches = scan_content(content, patterns)

    if matches:
        report = {
            'clean': False,
            'matches': matches,
            'summary': {
                'total': len(matches),
                'block': sum(1 for m in matches if m['action'] == 'block'),
                'warn': sum(1 for m in matches if m['action'] == 'warn'),
            }
        }
    else:
        report = {
            'clean': True,
            'matches': [],
        }

    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
