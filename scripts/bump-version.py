#!/usr/bin/env python3
"""Bump TARS plugin version using semantic versioning.

Usage:
    python scripts/bump-version.py patch   # 2.0.0 -> 2.0.1
    python scripts/bump-version.py minor   # 2.0.0 -> 2.1.0
    python scripts/bump-version.py major   # 2.0.0 -> 3.0.0
    python scripts/bump-version.py set 2.0.0  # Set exact version
"""

import datetime
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(SCRIPT_DIR)
PLUGIN_JSON = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")
CHANGELOG = os.path.join(PLUGIN_ROOT, "CHANGELOG.md")
ARCHITECTURE = os.path.join(PLUGIN_ROOT, "ARCHITECTURE.md")


def read_version():
    """Read current version from plugin.json."""
    try:
        with open(PLUGIN_JSON) as f:
            manifest = json.load(f)
        return manifest.get("version", "0.0.0")
    except Exception as e:
        print(f"Error reading plugin.json: {e}", file=sys.stderr)
        sys.exit(1)


def parse_version(version_str):
    """Parse semver string into (major, minor, patch) tuple."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str)
    if not match:
        print(f"Invalid version format: {version_str} (expected X.Y.Z)", file=sys.stderr)
        sys.exit(1)
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(current, bump_type):
    """Apply version bump and return new version string."""
    major, minor, patch = parse_version(current)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        print(f"Unknown bump type: {bump_type}", file=sys.stderr)
        sys.exit(1)


def update_plugin_json(new_version):
    """Update version in plugin.json."""
    try:
        with open(PLUGIN_JSON) as f:
            manifest = json.load(f)

        old_version = manifest.get("version", "unknown")
        manifest["version"] = new_version

        with open(PLUGIN_JSON, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")

        print(f"  plugin.json: {old_version} -> {new_version}")
    except Exception as e:
        print(f"Error updating plugin.json: {e}", file=sys.stderr)
        sys.exit(1)


def update_changelog(old_version, new_version):
    """Add new version entry to CHANGELOG.md."""
    if not os.path.isfile(CHANGELOG):
        print(f"  CHANGELOG.md: Not found (skipped)")
        return

    try:
        with open(CHANGELOG) as f:
            content = f.read()

        today = datetime.date.today().strftime("%Y-%m-%d")
        new_entry = f"\n## v{new_version} ({today})\n\n> Bumped from v{old_version}\n\n"

        # Insert after the first heading (# CHANGELOG or similar)
        lines = content.split("\n")
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("# "):
                insert_idx = i + 1
                # Skip blank lines after heading
                while insert_idx < len(lines) and not lines[insert_idx].strip():
                    insert_idx += 1
                break

        lines.insert(insert_idx, new_entry)
        with open(CHANGELOG, "w") as f:
            f.write("\n".join(lines))

        print(f"  CHANGELOG.md: Added v{new_version} entry")
    except Exception as e:
        print(f"  CHANGELOG.md: Error updating — {e}")


def update_architecture(old_version, new_version):
    """Update version references in ARCHITECTURE.md."""
    if not os.path.isfile(ARCHITECTURE):
        print(f"  ARCHITECTURE.md: Not found (skipped)")
        return

    try:
        with open(ARCHITECTURE) as f:
            content = f.read()

        # Replace version references (careful: only replace exact version strings)
        old_pattern = re.escape(old_version)
        updated = re.sub(
            rf"\bv?{old_pattern}\b",
            new_version,
            content,
        )

        if updated != content:
            with open(ARCHITECTURE, "w") as f:
                f.write(updated)
            print(f"  ARCHITECTURE.md: Updated version references")
        else:
            print(f"  ARCHITECTURE.md: No version references to update")
    except Exception as e:
        print(f"  ARCHITECTURE.md: Error updating — {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: bump-version.py <patch|minor|major|set VERSION>")
        print("")
        print("Examples:")
        print("  bump-version.py patch      # 2.0.0 -> 2.0.1")
        print("  bump-version.py minor      # 2.0.0 -> 2.1.0")
        print("  bump-version.py major      # 2.0.0 -> 3.0.0")
        print("  bump-version.py set 2.0.0  # Set exact version")
        sys.exit(1)

    bump_type = sys.argv[1].lower()
    current = read_version()

    if bump_type == "set":
        if len(sys.argv) < 3:
            print("Usage: bump-version.py set <version>", file=sys.stderr)
            sys.exit(1)
        new_version = sys.argv[2]
        # Validate format
        parse_version(new_version)
    elif bump_type in ("major", "minor", "patch"):
        new_version = bump_version(current, bump_type)
    else:
        print(f"Unknown command: {bump_type}", file=sys.stderr)
        print("Use: patch, minor, major, or set <version>")
        sys.exit(1)

    print(f"\nBumping version: {current} -> {new_version}\n")
    print("Updating files:")

    update_plugin_json(new_version)
    update_changelog(current, new_version)
    update_architecture(current, new_version)

    print(f"\nVersion bumped to {new_version}")
    print(f"Remember to review and commit the changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
