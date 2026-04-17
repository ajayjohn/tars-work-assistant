#!/usr/bin/env python3
"""capability-classifier — deterministic keyword/regex classifier that maps an
MCP tool (name + description) to a TARS capability category.

Starter pattern map lives at ``scripts/capability-classifier.yaml``. User
overrides live at ``<vault>/_system/capability-overrides.yaml`` (loaded by the
runtime discovery path; not read here in the skeleton).

Phase 1a skeleton. See PRD §26.9 for the full pattern set.
"""
import argparse
import json
import re
import sys
from pathlib import Path


PATTERNS_PATH = Path(__file__).resolve().parent / "capability-classifier.yaml"


def load_patterns_text() -> str:
    """Return the raw patterns YAML text; empty string if missing."""
    if PATTERNS_PATH.exists():
        return PATTERNS_PATH.read_text(encoding="utf-8")
    return ""


def _parse_simple_yaml(text: str) -> dict[str, list[str]]:
    """Minimal YAML reader for the ``patterns:`` section only.

    Handles: top-level ``patterns:`` block, nested capability keys, list items
    as quoted strings. No external dependency.
    """
    result: dict[str, list[str]] = {}
    in_patterns = False
    current: str | None = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "patterns:":
            in_patterns = True
            continue
        if not in_patterns:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent == 2 and stripped.endswith(":"):
            current = stripped[:-1].strip()
            result[current] = []
            continue
        if current and stripped.startswith("- "):
            item = stripped[2:].strip()
            if item.startswith('"') and item.endswith('"'):
                item = item[1:-1]
            elif item.startswith("'") and item.endswith("'"):
                item = item[1:-1]
            result[current].append(item)
    return result


def classify_tool(name: str, description: str = "") -> str:
    """Return the capability key matched, or ``uncategorized``."""
    patterns = _parse_simple_yaml(load_patterns_text())
    haystack = f"{name}\n{description}"
    for capability, regex_list in patterns.items():
        for pattern in regex_list:
            try:
                if re.search(pattern, haystack, re.IGNORECASE):
                    return capability
            except re.error:
                continue
    return "uncategorized"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="capability-classifier")
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    capability = classify_tool(args.name, args.description)
    if args.json:
        print(json.dumps({"tool": args.name, "capability": capability}))
    else:
        print(capability)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)
