#!/usr/bin/env python3
"""Validate TARS plugin structure: plugin.json validity, file existence, directory layout."""

import json
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_JSON = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")

REQUIRED_ROOT_FILES = [
    "LICENSE",
    "NOTICE",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "README.md",
]

REQUIRED_ROOT_DIRS = [
    "skills",
    "commands",
    "scripts",
    "reference",
    ".claude-plugin",
]

REQUIRED_PLUGIN_JSON_FIELDS = [
    "name",
    "description",
    "author",
]

REQUIRED_AUTHOR_FIELDS = ["name", "email"]


def main():
    errors = []
    warnings = []

    # --- 1. plugin.json exists and is valid JSON ---
    if not os.path.isfile(PLUGIN_JSON):
        errors.append(f"MISSING: {PLUGIN_JSON}")
        print_results(errors, warnings)
        return 1

    try:
        with open(PLUGIN_JSON) as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"INVALID JSON in plugin.json: {e}")
        print_results(errors, warnings)
        return 1

    # --- 2. Required fields in plugin.json ---
    for field in REQUIRED_PLUGIN_JSON_FIELDS:
        if field not in manifest:
            errors.append(f"MISSING FIELD in plugin.json: '{field}'")

    # Author sub-fields
    author = manifest.get("author", {})
    if isinstance(author, dict):
        for field in REQUIRED_AUTHOR_FIELDS:
            if field not in author:
                errors.append(f"MISSING FIELD in plugin.json author: '{field}'")
        if "url" in author:
            warnings.append("plugin.json author contains 'url' field (should be omitted per spec)")
    else:
        errors.append("plugin.json 'author' should be an object with 'name' and 'url'")

    # Version format check (optional)
    version = manifest.get("version", "")
    if version:
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            errors.append(f"plugin.json version '{version}' is not valid semver (expected X.Y.Z)")

    # Skills check (optional)
    skills = manifest.get("skills", [])
    if "skills" in manifest and (not isinstance(skills, list) or len(skills) == 0):
        warnings.append("plugin.json 'skills' is present but empty or invalid")

    # Commands check (optional)
    commands = manifest.get("commands", [])
    if "commands" in manifest and (not isinstance(commands, list) or len(commands) == 0):
        warnings.append("plugin.json 'commands' is present but empty or invalid")

    # --- 3. All referenced skill files exist on disk ---
    for skill_path in skills:
        full_path = os.path.join(PLUGIN_ROOT, skill_path)
        if not os.path.isfile(full_path):
            errors.append(f"MISSING SKILL FILE: {skill_path} (referenced in plugin.json)")

    # --- 4. All referenced command files exist on disk ---
    for cmd_path in commands:
        full_path = os.path.join(PLUGIN_ROOT, cmd_path)
        if not os.path.isfile(full_path):
            errors.append(f"MISSING COMMAND FILE: {cmd_path} (referenced in plugin.json)")

    # --- 5. Required root files exist ---
    for fname in REQUIRED_ROOT_FILES:
        if not os.path.isfile(os.path.join(PLUGIN_ROOT, fname)):
            errors.append(f"MISSING ROOT FILE: {fname}")

    # --- 6. Required root directories exist ---
    for dname in REQUIRED_ROOT_DIRS:
        if not os.path.isdir(os.path.join(PLUGIN_ROOT, dname)):
            errors.append(f"MISSING ROOT DIRECTORY: {dname}/")

    # --- 7. Optional but expected directories ---
    optional_dirs = ["memory", "journal", "inbox", "archive", "tests"]
    for dname in optional_dirs:
        if not os.path.isdir(os.path.join(PLUGIN_ROOT, dname)):
            warnings.append(f"OPTIONAL DIRECTORY MISSING: {dname}/")

    # --- 8. Skills directory structure: each skill dir has SKILL.md ---
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    if os.path.isdir(skills_dir):
        for entry in sorted(os.listdir(skills_dir)):
            skill_dir = os.path.join(skills_dir, entry)
            if os.path.isdir(skill_dir):
                skill_md = os.path.join(skill_dir, "SKILL.md")
                if not os.path.isfile(skill_md):
                    errors.append(f"MISSING SKILL.md in skills/{entry}/")

    # --- 9. No unexpected files in skills/ root (should only have directories) ---
    if os.path.isdir(skills_dir):
        for entry in os.listdir(skills_dir):
            full = os.path.join(skills_dir, entry)
            if os.path.isfile(full):
                warnings.append(f"UNEXPECTED FILE in skills/: {entry} (expected only directories)")

    # --- 10. Verify .mcp.json exists ---
    mcp_json = os.path.join(PLUGIN_ROOT, ".mcp.json")
    if not os.path.isfile(mcp_json):
        warnings.append("MISSING: .mcp.json (MCP server configuration)")

    print_results(errors, warnings)
    return 1 if errors else 0


def print_results(errors, warnings):
    print("=" * 60)
    print("TARS Plugin Structure Validation")
    print("=" * 60)

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")

    if not errors and not warnings:
        print("\n  ✓ All structure checks passed")

    print()
    total = len(errors) + len(warnings)
    print(f"Result: {len(errors)} errors, {len(warnings)} warnings")
    if not errors:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


if __name__ == "__main__":
    sys.exit(main())
