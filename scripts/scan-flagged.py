#!/usr/bin/env python3
"""
TARS Flagged Content Scanner (Issue 8)
Scans for negative sentiment markers in memory/people/ notes.
Detects both inline HTML comment markers and pattern-based sentiment.
Outputs JSON for agent consumption.

Usage: python3 scripts/scan-flagged.py [vault_path]
"""

import sys
import os
import json
import re
import yaml
from pathlib import Path
from datetime import datetime, date


def load_guardrails(vault_path):
    """Load negative sentiment patterns from guardrails."""
    guardrails_path = Path(vault_path) / "_system" / "guardrails.yaml"
    if not guardrails_path.exists():
        return None, f"Guardrails not found: {guardrails_path}"
    with open(guardrails_path, "r") as f:
        config = yaml.safe_load(f)
    return config, None


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
        fm = yaml.safe_load(match.group(1))
        body = content[match.end():]
        return fm if isinstance(fm, dict) else None, body
    except yaml.YAMLError:
        return None, content


def scan_flagged_markers(body):
    """Find <!-- tars-flag:negative YYYY-MM-DD --> markers and their content."""
    findings = []
    # Pattern: <!-- tars-flag:negative DATE --> ... content on same or next line
    pattern = re.compile(
        r'<!--\s*tars-flag:negative\s+(\d{4}-\d{2}-\d{2})\s*-->\s*\n?(.*?)(?=\n<!--|\n##|\n\n|\Z)',
        re.DOTALL,
    )

    for match in pattern.finditer(body):
        flag_date = match.group(1)
        flagged_text = match.group(2).strip()

        # Calculate age in days
        try:
            flag_dt = datetime.strptime(flag_date, "%Y-%m-%d").date()
            age_days = (date.today() - flag_dt).days
        except ValueError:
            age_days = -1

        findings.append({
            "date": flag_date,
            "text": flagged_text,
            "age_days": age_days,
            "stale": age_days > 90,
        })

    return findings


def scan_sentiment_patterns(body, patterns):
    """Scan for negative sentiment patterns without explicit markers."""
    findings = []
    for pat_def in patterns:
        try:
            pattern = re.compile(pat_def["pattern"])
        except re.error:
            continue

        for match in pattern.finditer(body):
            line_num = body[:match.start()].count("\n") + 1
            line_start = body.rfind("\n", 0, match.start()) + 1
            line_end = body.find("\n", match.end())
            if line_end == -1:
                line_end = len(body)
            context = body[line_start:line_end].strip()

            findings.append({
                "category": pat_def.get("category", "unknown"),
                "matched_text": match.group(),
                "context": context,
                "line": line_num,
                "has_marker": False,
            })

    return findings


def scan_vault(vault_path, guardrails):
    """Scan all people notes for flagged content."""
    vault = Path(vault_path)
    people_dir = vault / "memory" / "people"
    results = []

    neg_patterns = guardrails.get("negative_sentiment_patterns", [])

    if not people_dir.exists():
        return results

    for md_file in people_dir.rglob("*.md"):
        frontmatter, body = parse_frontmatter(md_file)
        if body is None:
            continue

        relative = str(md_file.relative_to(vault))
        person_name = md_file.stem

        # Check for explicit flag markers
        marker_findings = scan_flagged_markers(body)

        # Check for unmarked sentiment
        sentiment_findings = scan_sentiment_patterns(body, neg_patterns)

        # Check frontmatter flag
        has_flag_property = (
            frontmatter
            and frontmatter.get("tars-has-flagged-content") is True
        )

        if marker_findings or sentiment_findings:
            results.append({
                "file": relative,
                "person": person_name,
                "has_flag_property": has_flag_property,
                "marked_flags": marker_findings,
                "unmarked_sentiment": sentiment_findings,
                "total_flags": len(marker_findings) + len(sentiment_findings),
                "stale_flags": sum(
                    1 for f in marker_findings if f.get("stale", False)
                ),
            })

    return results


def main():
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "."

    guardrails, error = load_guardrails(vault_path)
    if error:
        print(json.dumps({"error": error}))
        sys.exit(1)

    results = scan_vault(vault_path, guardrails)

    total_flags = sum(r["total_flags"] for r in results)
    stale_flags = sum(r["stale_flags"] for r in results)
    people_affected = len(results)

    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "people_with_flags": people_affected,
            "total_flags": total_flags,
            "stale_flags": stale_flags,
        },
        "results": results,
    }

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
