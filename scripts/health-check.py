#!/usr/bin/env python3
"""
TARS v3 Health Check
Comprehensive vault health scan: schemas, links, aliases, staleness.
Outputs JSON for agent consumption.

Usage: python3 scripts/health-check.py [vault_path]
"""

import sys
import os
import json
import re
import argparse
import shutil
from pathlib import Path
from datetime import datetime, date

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

KEY_MAP = {
    "title": None,
    "pm": "tars-owner",
    "owner": "tars-owner",
    "status": "tars-status",
    "state": "tars-status",
    "start": "tars-start-date",
    "end": "tars-target-date",
    "target": "tars-target-date",
    "due": "tars-due",
    "priority": "tars-priority",
    "category": "tars-category",
    "summary": "tars-summary",
    "description": "tars-summary",
    "created": "tars-created",
    "modified": "tars-modified",
    "updated": "tars-modified",
    "health": "tars-health",
}

TAG_NAMESPACE_MAP = {
    "initiative": "tars/initiative",
    "person": "tars/person",
    "decision": "tars/decision",
    "meeting": "tars/meeting",
    "task": "tars/task",
    "wisdom": "tars/wisdom",
    "vendor": "tars/vendor",
    "competitor": "tars/competitor",
    "product": "tars/product",
    "company": "tars/company",
    "journal": "tars/journal",
}

RESERVED_NON_PREFIX = {"tags", "aliases"}
POLLUTION_SKIP_PREFIXES = ("_system/", "_views/", "archive/")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def load_yaml_file(filepath):
    """Load a YAML file. Returns None on missing or unparseable input so callers
    degrade instead of crashing the whole health-check run."""
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r") as f:
            if HAS_YAML:
                return yaml.safe_load(f)
            return {}
    except Exception:
        return None


def parse_frontmatter(file_path):
    """Extract YAML frontmatter from a markdown file."""
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
            # Simple fallback parser
            fm = {}
            for line in match.group(1).split("\n"):
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    key, _, val = line.partition(":")
                    val = val.strip().strip("'\"")
                    if val.startswith("[") and val.endswith("]"):
                        val = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
                    fm[key.strip()] = val

        body = content[match.end():]
        return fm if isinstance(fm, dict) else None, body
    except Exception:
        return None, content


def extract_wikilinks(text):
    """Extract all wikilinks from text."""
    if not text:
        return []
    return [m.group(1) for m in re.finditer(r'\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]', text)]


def check_broken_links(vault_path):
    """Find wikilinks that don't resolve to any file."""
    vault = Path(vault_path)
    all_notes = set()
    all_aliases = set()

    for md_file in vault.rglob("*.md"):
        if md_file.name.startswith(".") or "/.obsidian/" in str(md_file):
            continue
        all_notes.add(md_file.stem.lower())

        fm, _ = parse_frontmatter(md_file)
        if fm and "aliases" in fm:
            aliases = fm["aliases"]
            if isinstance(aliases, list):
                for alias in aliases:
                    if isinstance(alias, str):
                        all_aliases.add(alias.lower())

    broken = []
    scan_dirs = ["memory", "journal", "contexts", "_system/backlog"]

    for scan_dir in scan_dirs:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue

        for md_file in dir_path.rglob("*.md"):
            fm, body = parse_frontmatter(md_file)

            # Check body links
            links = extract_wikilinks(body) if body else []

            # Check frontmatter wikilinks
            if fm:
                for key, val in fm.items():
                    if isinstance(val, str):
                        links.extend(extract_wikilinks(val))
                    elif isinstance(val, list):
                        for item in val:
                            if isinstance(item, str):
                                links.extend(extract_wikilinks(item))

            for link in links:
                link_lower = link.lower()
                if link_lower not in all_notes and link_lower not in all_aliases:
                    broken.append({
                        "source": str(md_file.relative_to(vault)),
                        "target": link,
                    })

    # Deduplicate
    seen = set()
    deduped = []
    for b in broken:
        key = (b["source"], b["target"])
        if key not in seen:
            seen.add(key)
            deduped.append(b)

    return deduped


def check_staleness(vault_path):
    """Check for stale content based on staleness tiers."""
    vault = Path(vault_path)
    stale = []
    today = date.today()

    thresholds = {"durable": None, "seasonal": 180, "transient": 90, "ephemeral": 30}

    memory_dir = vault / "memory"
    if not memory_dir.exists():
        return stale

    for md_file in memory_dir.rglob("*.md"):
        if md_file.name.startswith("_") or md_file.name.startswith("."):
            continue

        fm, _ = parse_frontmatter(md_file)
        if not fm:
            continue

        staleness = fm.get("tars-staleness", "seasonal")
        threshold = thresholds.get(staleness)
        if threshold is None:
            continue

        modified = fm.get("tars-modified")
        if not modified:
            stale.append({
                "file": str(md_file.relative_to(vault)),
                "reason": "No tars-modified date",
                "staleness": staleness,
            })
            continue

        try:
            if isinstance(modified, str):
                mod_date = datetime.strptime(modified, "%Y-%m-%d").date()
            elif isinstance(modified, date):
                mod_date = modified
            else:
                continue

            age_days = (today - mod_date).days
            if age_days > threshold:
                stale.append({
                    "file": str(md_file.relative_to(vault)),
                    "staleness": staleness,
                    "threshold_days": threshold,
                    "age_days": age_days,
                    "last_modified": str(modified),
                })
        except (ValueError, TypeError):
            stale.append({
                "file": str(md_file.relative_to(vault)),
                "reason": f"Invalid tars-modified date: {modified}",
            })

    return stale


def check_duplicate_aliases(vault_path):
    """Find aliases that map to multiple notes."""
    vault = Path(vault_path)
    alias_map = {}

    for md_file in vault.rglob("*.md"):
        if md_file.name.startswith(".") or "/.obsidian/" in str(md_file):
            continue

        fm, _ = parse_frontmatter(md_file)
        if not fm or "aliases" not in fm:
            continue

        aliases = fm["aliases"]
        if not isinstance(aliases, list):
            continue

        for alias in aliases:
            if not isinstance(alias, str):
                continue
            alias_lower = alias.lower()
            if alias_lower not in alias_map:
                alias_map[alias_lower] = []
            alias_map[alias_lower].append(md_file.stem)

    return [
        {"alias": alias, "notes": notes}
        for alias, notes in alias_map.items()
        if len(notes) > 1
    ]


def check_missing_frontmatter(vault_path):
    """Find TARS-tagged notes missing required frontmatter."""
    vault = Path(vault_path)
    schemas = load_yaml_file(vault / "_system" / "schemas.yaml") or {}
    issues = []

    scan_dirs = ["memory", "journal", "_system/backlog"]
    for scan_dir in scan_dirs:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue

        for md_file in dir_path.rglob("*.md"):
            if md_file.name.startswith("_") or md_file.name.startswith("."):
                continue

            fm, _ = parse_frontmatter(md_file)
            if not fm:
                continue

            tags = fm.get("tags", [])
            if not isinstance(tags, list):
                tags = [tags] if tags else []

            # Find matching schema
            for type_name, schema in schemas.items():
                required_tags = schema.get("required_tags", [])
                if all(t in tags for t in required_tags):
                    for prop in schema.get("required_properties", []):
                        if prop not in fm or fm[prop] is None or fm[prop] == "":
                            issues.append({
                                "file": str(md_file.relative_to(vault)),
                                "schema": type_name,
                                "missing_property": prop,
                            })
                    break

    return issues


def scan_flagged_markers(body):
    """Find <!-- tars-flag:negative YYYY-MM-DD --> markers and their content.

    Merged in from the retired scripts/scan-flagged.py (PRD §7.4).
    """
    findings = []
    pattern = re.compile(
        r'<!--\s*tars-flag:negative\s+(\d{4}-\d{2}-\d{2})\s*-->\s*\n?(.*?)(?=\n<!--|\n##|\n\n|\Z)',
        re.DOTALL,
    )
    for match in pattern.finditer(body):
        flag_date = match.group(1)
        flagged_text = match.group(2).strip()
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
    for pat_def in patterns or []:
        try:
            pattern = re.compile(pat_def["pattern"])
        except (re.error, KeyError, TypeError):
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


def check_flagged_content(vault_path):
    """Scan memory/people/ for negative sentiment markers and patterns.

    Returns a list of per-person finding records. Safe to call when
    guardrails.yaml is missing — returns [] in that case.
    """
    vault = Path(vault_path)
    guardrails = load_yaml_file(vault / "_system" / "guardrails.yaml") or {}
    neg_patterns = guardrails.get("negative_sentiment_patterns", []) or []

    people_dir = vault / "memory" / "people"
    if not people_dir.exists():
        return []

    results = []
    for md_file in people_dir.rglob("*.md"):
        frontmatter, body = parse_frontmatter(md_file)
        if body is None:
            continue

        relative = str(md_file.relative_to(vault))
        person_name = md_file.stem
        marker_findings = scan_flagged_markers(body)
        sentiment_findings = scan_sentiment_patterns(body, neg_patterns)
        has_flag_property = (
            frontmatter is not None
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


def pollution_skip(rel_path):
    rel = rel_path.as_posix()
    return any(rel.startswith(prefix) for prefix in POLLUTION_SKIP_PREFIXES)


def check_frontmatter_pollution(vault_path):
    """Find notes with non-TARS frontmatter keys."""
    vault = Path(vault_path)
    offenders = []
    for md_file in vault.rglob("*.md"):
        rel = md_file.relative_to(vault)
        if pollution_skip(rel):
            continue
        fm, _ = parse_frontmatter(md_file)
        if not fm:
            continue
        bad_keys = [
            key for key in fm
            if key not in RESERVED_NON_PREFIX and not key.startswith("tars-")
        ]
        if bad_keys:
            offenders.append({
                "path": rel.as_posix(),
                "bad_keys": bad_keys,
                "tags": fm.get("tags") or [],
            })
    return offenders


def split_frontmatter(text):
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    return match.group(1), text[match.end():]


def parse_frontmatter_block(block):
    entries = []
    in_list = None
    for raw in block.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            entries.append((f"__raw__{len(entries)}", raw))
            continue
        if raw.startswith("  -") and in_list is not None:
            in_list.append(stripped[1:].strip().strip('"').strip("'"))
            continue
        in_list = None
        if ":" not in raw:
            entries.append((f"__raw__{len(entries)}", raw))
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip()
        if not val:
            in_list = []
            entries.append((key, in_list))
            continue
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            entries.append((
                key,
                [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()],
            ))
            continue
        entries.append((key, val.strip('"').strip("'")))
    return entries


def quote_frontmatter_value(value):
    if value is None or value == "":
        return '""'
    if any(char in value for char in (":", "#", "[", "]", "'")) or " " in value:
        if '"' not in value:
            return f'"{value}"'
    return value


def emit_frontmatter_block(entries):
    lines = []
    for key, value in entries:
        if key.startswith("__raw__"):
            lines.append(value if isinstance(value, str) else "")
        elif isinstance(value, list):
            if value:
                rendered = ", ".join(quote_frontmatter_value(item) for item in value)
                lines.append(f"{key}: [{rendered}]")
            else:
                lines.append(f"{key}:")
        else:
            lines.append(f"{key}: {quote_frontmatter_value(value)}")
    return "\n".join(lines)


def migrate_frontmatter_entries(entries):
    report = {"renamed": [], "dropped": [], "unmapped": [], "tags_namespaced": []}
    migrated = []
    seen_keys = set()

    for key, value in entries:
        if key.startswith("__raw__"):
            migrated.append((key, value))
            continue
        if key in RESERVED_NON_PREFIX or key.startswith("tars-"):
            if key == "tags" and isinstance(value, list):
                new_tags = []
                for tag in value:
                    if tag in TAG_NAMESPACE_MAP:
                        replacement = TAG_NAMESPACE_MAP[tag]
                        report["tags_namespaced"].append({"from": tag, "to": replacement})
                        new_tags.append(replacement)
                    else:
                        new_tags.append(tag)
                deduped = []
                seen_tags = set()
                for tag in new_tags:
                    if tag not in seen_tags:
                        seen_tags.add(tag)
                        deduped.append(tag)
                migrated.append((key, deduped))
                seen_keys.add(key)
                continue
            migrated.append((key, value))
            seen_keys.add(key)
            continue
        if key in KEY_MAP:
            target = KEY_MAP[key]
            if target is None:
                report["dropped"].append(key)
                continue
            if target in seen_keys:
                report["dropped"].append(f"{key} (duplicate of existing {target})")
                continue
            migrated.append((target, value))
            report["renamed"].append({"from": key, "to": target})
            seen_keys.add(target)
            continue
        report["unmapped"].append(key)
        migrated.append((key, value))

    return migrated, report


def fix_frontmatter_prefixes(vault_path, apply=False):
    """Dry-run or apply canonical tars-* frontmatter prefix fixes."""
    vault = Path(vault_path)
    summary = {"scanned": 0, "changed": 0, "files": [], "unmapped_keys": set()}

    for md_file in vault.rglob("*.md"):
        rel = md_file.relative_to(vault)
        if pollution_skip(rel):
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        block, body = split_frontmatter(text)
        if block is None:
            continue
        summary["scanned"] += 1
        entries = parse_frontmatter_block(block)
        migrated, report = migrate_frontmatter_entries(entries)
        if not (report["renamed"] or report["dropped"] or report["tags_namespaced"]):
            if report["unmapped"]:
                summary["unmapped_keys"].update(report["unmapped"])
            continue
        summary["changed"] += 1
        summary["files"].append({"path": rel.as_posix(), **report})
        summary["unmapped_keys"].update(report["unmapped"])
        if apply:
            backup = md_file.with_suffix(md_file.suffix + ".pre-migration")
            if not backup.exists():
                shutil.copy2(md_file, backup)
            md_file.write_text(
                "---\n" + emit_frontmatter_block(migrated) + "\n---\n" + body,
                encoding="utf-8",
            )

    summary["unmapped_keys"] = sorted(summary["unmapped_keys"])
    return summary


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run TARS workspace health checks.")
    parser.add_argument("vault_path", nargs="?", default=None)
    parser.add_argument("--vault", dest="vault", default=None)
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--fix-prefixes", action="store_true",
                        help="Dry-run canonical tars-* frontmatter prefix fixes.")
    parser.add_argument("--apply", action="store_true",
                        help="Apply fixes for --fix-prefixes.")
    return parser.parse_args(argv)


def main():
    args = parse_args(sys.argv[1:])
    vault_path = args.vault or args.vault_path or "."

    if args.fix_prefixes:
        summary = fix_frontmatter_prefixes(vault_path, apply=args.apply)
        print(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "mode": "frontmatter_prefixes",
            "apply": args.apply,
            "frontmatter_prefixes": summary,
        }, indent=2))
        return 0

    broken_links = check_broken_links(vault_path)
    stale_content = check_staleness(vault_path)
    duplicate_aliases = check_duplicate_aliases(vault_path)
    missing_fm = check_missing_frontmatter(vault_path)
    flagged = check_flagged_content(vault_path)
    polluted = check_frontmatter_pollution(vault_path)

    flagged_total = sum(r["total_flags"] for r in flagged)
    flagged_stale = sum(r["stale_flags"] for r in flagged)
    critical = len(broken_links) + len(missing_fm)
    warnings = len(stale_content) + len(duplicate_aliases) + flagged_stale + len(polluted)

    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "critical": critical,
            "warnings": warnings,
            "total": critical + warnings,
        },
        "broken_links": broken_links[:50],
        "broken_links_total": len(broken_links),
        "missing_frontmatter": missing_fm[:30],
        "missing_frontmatter_total": len(missing_fm),
        "stale_content": stale_content[:30],
        "stale_content_total": len(stale_content),
        "duplicate_aliases": duplicate_aliases,
        "flagged_content": {
            "people_with_flags": len(flagged),
            "total_flags": flagged_total,
            "stale_flags": flagged_stale,
            "results": flagged,
        },
        "frontmatter_pollution": {
            "count": len(polluted),
            "offenders": polluted,
            "fix_command": "scripts/health-check.py --vault <workspace> --fix-prefixes --apply",
        },
    }

    print(json.dumps(output, indent=2))
    return 0 if critical == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
