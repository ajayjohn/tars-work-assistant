#!/usr/bin/env python3
"""Validate TARS plugin structure for marketplace compatibility."""

import json
import sys
from pathlib import Path

def validate_plugin(plugin_dir: Path):
    """Validate plugin structure and configuration."""
    errors = []
    warnings = []

    # Check plugin.json exists
    plugin_json = plugin_dir / "plugin.json"
    if not plugin_json.exists():
        errors.append(f"Missing plugin.json at {plugin_json}")
        return errors, warnings

    # Load plugin.json
    with open(plugin_json) as f:
        plugin = json.load(f)

    # Validate required fields
    required = ["name", "version", "description", "skills", "commands"]
    for field in required:
        if field not in plugin:
            errors.append(f"Missing required field: {field}")

    # Validate skills exist
    if "skills" in plugin:
        for skill_path in plugin["skills"]:
            full_path = plugin_dir / skill_path
            if not full_path.exists():
                errors.append(f"Skill file not found: {skill_path}")

    # Validate commands exist
    if "commands" in plugin:
        for cmd_path in plugin["commands"]:
            full_path = plugin_dir / cmd_path
            if not full_path.exists():
                errors.append(f"Command file not found: {cmd_path}")

    return errors, warnings

def validate_marketplace(repo_root: Path):
    """Validate marketplace.json schema."""
    errors = []
    warnings = []

    marketplace_json = repo_root / "marketplace.json"
    if not marketplace_json.exists():
        errors.append("Missing marketplace.json")
        return errors, warnings

    with open(marketplace_json) as f:
        marketplace = json.load(f)

    # Validate root-level required fields
    required_root = ["name", "description", "owner", "plugins"]
    for field in required_root:
        if field not in marketplace:
            errors.append(f"Missing root-level field in marketplace.json: {field}")

    # Validate owner structure
    if "owner" in marketplace:
        if not isinstance(marketplace["owner"], dict):
            errors.append("'owner' must be an object with 'name' and 'url'")
        elif "name" not in marketplace["owner"]:
            errors.append("'owner' object missing 'name' field")

    # Validate plugins array
    if "plugins" not in marketplace:
        errors.append("Missing 'plugins' array")
    elif not isinstance(marketplace["plugins"], list):
        errors.append("'plugins' must be an array")
    elif len(marketplace["plugins"]) == 0:
        errors.append("'plugins' array is empty")
    else:
        # Validate first plugin
        plugin = marketplace["plugins"][0]
        if "source" in plugin:
            source = plugin["source"]
            if source.get("path") != ".claude-plugin":
                warnings.append(f"Source path is '{source.get('path')}' - should be '.claude-plugin'")

    return errors, warnings

def main():
    repo_root = Path(__file__).parent.parent
    plugin_dir = repo_root / ".claude-plugin"

    print("Validating TARS plugin structure...\n")

    # Validate plugin directory
    print("Checking .claude-plugin/ structure...")
    errors, warnings = validate_plugin(plugin_dir)

    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Plugin structure valid")

    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    # Validate marketplace configuration
    print("\nChecking marketplace.json...")
    mk_errors, mk_warnings = validate_marketplace(repo_root)

    if mk_errors:
        print("❌ ERRORS:")
        for error in mk_errors:
            print(f"  - {error}")
    else:
        print("✓ Marketplace configuration valid")

    if mk_warnings:
        print("\n⚠️  WARNINGS:")
        for warning in mk_warnings:
            print(f"  - {warning}")

    # Summary
    total_errors = len(errors) + len(mk_errors)
    total_warnings = len(warnings) + len(mk_warnings)

    print(f"\n{'='*60}")
    if total_errors == 0:
        print(f"✓ Plugin ready for marketplace ({total_warnings} warnings)")
        sys.exit(0)
    else:
        print(f"❌ Plugin has {total_errors} error(s) - fix before release")
        sys.exit(1)

if __name__ == "__main__":
    main()
