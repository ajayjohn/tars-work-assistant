#!/usr/bin/env python3
"""
TARS v3 Secret Scanner
Scans content against _system/guardrails.yaml patterns.
Detects blocked secrets (must redact) and warn-level sensitive data.
Outputs JSON for agent consumption.

Usage:
  python3 scripts/scan-secrets.py [vault_path]           # Scan full vault
  python3 scripts/scan-secrets.py --content "text"        # Scan a string
  python3 scripts/scan-secrets.py --file path/to/file.md  # Scan single file
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

# Use yaml if available, otherwise simple parser
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def simple_yaml_load(filepath):
    """Minimal YAML parser for guardrails format when PyYAML is unavailable."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = {"block_patterns": [], "warn_patterns": [], "negative_sentiment_patterns": []}
    current_section = None
    current_item = {}

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped.startswith("block_patterns:"):
            current_section = "block_patterns"
            continue
        elif stripped.startswith("warn_patterns:"):
            current_section = "warn_patterns"
            continue
        elif stripped.startswith("negative_sentiment_patterns:"):
            current_section = "negative_sentiment_patterns"
            continue

        if current_section and stripped.startswith("- name:"):
            if current_item and "pattern" in current_item:
                result[current_section].append(current_item)
            current_item = {"name": stripped.split(":", 1)[1].strip()}
        elif current_section and stripped.startswith("- pattern:"):
            if current_item and "pattern" in current_item:
                result[current_section].append(current_item)
            pat = stripped.split(":", 1)[1].strip().strip("'\"")
            current_item = {"pattern": pat}
        elif stripped.startswith("pattern:") and current_item:
            pat = stripped.split(":", 1)[1].strip().strip("'\"")
            current_item["pattern"] = pat
        elif stripped.startswith("description:") and current_item:
            current_item["description"] = stripped.split(":", 1)[1].strip().strip("'\"")
        elif stripped.startswith("category:") and current_item:
            current_item["category"] = stripped.split(":", 1)[1].strip().strip("'\"")

    if current_item and "pattern" in current_item and current_section:
        result[current_section].append(current_item)

    return result


def load_guardrails(vault_path):
    """Load guardrails configuration."""
    guardrails_path = Path(vault_path) / "_system" / "guardrails.yaml"
    if not guardrails_path.exists():
        return None, f"Guardrails file not found: {guardrails_path}"
    if HAS_YAML:
        with open(guardrails_path, "r") as f:
            return yaml.safe_load(f), None
    else:
        return simple_yaml_load(guardrails_path), None


def compile_patterns(guardrails):
    """Compile regex patterns from guardrails config."""
    compiled = {"block": [], "warn": []}

    for pattern_def in guardrails.get("block_patterns", []):
        try:
            compiled["block"].append({
                "name": pattern_def.get("name", "unknown"),
                "pattern": re.compile(pattern_def["pattern"]),
                "description": pattern_def.get("description", ""),
            })
        except (re.error, KeyError):
            pass

    for pattern_def in guardrails.get("warn_patterns", []):
        try:
            compiled["warn"].append({
                "name": pattern_def.get("name", "unknown"),
                "pattern": re.compile(pattern_def["pattern"]),
                "description": pattern_def.get("description", ""),
            })
        except (re.error, KeyError):
            pass

    return compiled


def scan_content(content, patterns, source="inline"):
    """Scan text content against compiled patterns."""
    findings = []

    for level in ["block", "warn"]:
        for pat in patterns[level]:
            for match in pat["pattern"].finditer(content):
                line_start = content.rfind("\n", 0, match.start()) + 1
                line_num = content[:match.start()].count("\n") + 1
                line_end = content.find("\n", match.end())
                if line_end == -1:
                    line_end = len(content)
                context_line = content[line_start:line_end].strip()
                redacted = context_line.replace(
                    match.group(), f"[REDACTED:{pat['name']}]"
                )

                findings.append({
                    "level": level,
                    "pattern_name": pat["name"],
                    "description": pat["description"],
                    "source": source,
                    "line": line_num,
                    "context": redacted,
                })

    return findings


def scan_file(file_path, patterns, vault_path=None):
    """Scan a single file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return []

    relative = str(file_path)
    if vault_path:
        try:
            relative = str(Path(file_path).relative_to(vault_path))
        except ValueError:
            pass

    return scan_content(content, patterns, source=relative)


def scan_vault(vault_path, patterns):
    """Scan all relevant vault directories."""
    vault = Path(vault_path)
    all_findings = []

    scan_dirs = ["memory", "journal", "contexts", "inbox", "archive"]

    for scan_dir in scan_dirs:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue

        for md_file in dir_path.rglob("*.md"):
            if md_file.name.startswith("."):
                continue
            findings = scan_file(md_file, patterns, vault_path)
            all_findings.extend(findings)

    return all_findings


def main():
    vault_path = "."
    scan_mode = "vault"
    target = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--content" and i + 1 < len(sys.argv):
            scan_mode = "content"
            target = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--file" and i + 1 < len(sys.argv):
            scan_mode = "file"
            target = sys.argv[i + 1]
            i += 2
        else:
            vault_path = sys.argv[i]
            i += 1

    guardrails, error = load_guardrails(vault_path)
    if error:
        print(json.dumps({"error": error}))
        sys.exit(1)

    patterns = compile_patterns(guardrails)

    if scan_mode == "content":
        findings = scan_content(target, patterns)
    elif scan_mode == "file":
        findings = scan_file(target, patterns, vault_path)
    else:
        findings = scan_vault(vault_path, patterns)

    blocked = [f for f in findings if f["level"] == "block"]
    warned = [f for f in findings if f["level"] == "warn"]

    output = {
        "timestamp": datetime.now().isoformat(),
        "scan_mode": scan_mode,
        "summary": {
            "total_findings": len(findings),
            "blocked": len(blocked),
            "warned": len(warned),
        },
        "blocked": blocked,
        "warned": warned,
        "safe": len(blocked) == 0,
    }

    print(json.dumps(output, indent=2))
    sys.exit(0 if len(blocked) == 0 else 1)


if __name__ == "__main__":
    main()
