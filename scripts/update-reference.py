#!/usr/bin/env python3
"""Update workspace reference files to match the installed plugin version.

Surgically updates template/structural sections while preserving user data.
Three merge strategies: full_replace, section_merge, additive_merge.

Usage:
    python scripts/update-reference.py <workspace_path> [plugin_path] [--dry-run]

Output: JSON report of files updated, preserved user data, and any conflicts.
"""

import json
import os
import re
import sys
from copy import deepcopy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)


# ─── File policies ────────────────────────────────────────────────

FILE_POLICIES = {
    "taxonomy.md": {"strategy": "full_replace"},
    "workflows.md": {"strategy": "full_replace"},
    "shortcuts.md": {"strategy": "full_replace"},
    "guardrails.yaml": {"strategy": "full_replace"},
    "integrations.md": {
        "strategy": "section_merge",
        # Sections whose *body* is user data (table rows, item lists)
        "user_data_sections": [],
        # Fields within template sections to preserve (matched by prefix)
        "preserve_fields": ["status:"],
    },
    "replacements.md": {
        "strategy": "section_merge",
        # These sections have user data in their table rows
        "user_data_sections": ["## People", "## Teams", "## Products and initiatives", "## Vendors"],
        "preserve_fields": [],
    },
    "schedule.md": {
        "strategy": "section_merge",
        "user_data_sections": ["## Recurring items", "## One-time items"],
        "preserve_fields": [],
    },
    "kpis.md": {
        "strategy": "section_merge",
        # All non-header, non-instruction sections are user data
        "user_data_sections": [],  # handled specially: any section NOT in plugin source is user data
        "preserve_fields": [],
    },
    ".housekeeping-state.yaml": {"strategy": "additive_merge"},
    "maturity.yaml": {"strategy": "additive_merge"},
}


# ─── Parsing helpers ──────────────────────────────────────────────

def parse_markdown_sections(content):
    """Parse markdown into sections by ## headings.

    Returns list of (heading, body) tuples.
    The first tuple has heading=None for content before the first heading.
    """
    sections = []
    current_heading = None
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("## "):
            sections.append((current_heading, "\n".join(current_lines)))
            current_heading = line
            current_lines = []
        else:
            current_lines.append(line)

    sections.append((current_heading, "\n".join(current_lines)))
    return sections


def parse_yaml_keys(content):
    """Parse simple YAML-like key: value pairs. Returns dict."""
    result = {}
    for line in content.split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("#") and not line.startswith("-"):
            key = line.split(":", 1)[0].strip()
            value = line.split(":", 1)[1].strip()
            result[key] = value
    return result


def extract_preserve_fields(content, field_prefixes):
    """Extract field values to preserve from workspace content, in order.

    Returns a dict of {prefix: [value1, value2, ...]} where values are
    ordered by their appearance in the file. Multiple occurrences of the
    same prefix are all captured (e.g., multiple 'status:' fields).
    """
    preserved = {prefix: [] for prefix in field_prefixes}
    for line in content.split("\n"):
        stripped = line.strip()
        for prefix in field_prefixes:
            if stripped.startswith(prefix):
                preserved[prefix].append(stripped)
    return preserved


def apply_preserved_fields(content, preserved):
    """Replace field lines in content with preserved values, positionally.

    Each occurrence of a prefix in the merged content is matched to the
    corresponding preserved value by position. If the merged content has
    more occurrences than were preserved (new sections added by plugin),
    the extra occurrences keep the plugin's value.
    """
    lines = content.split("\n")
    result = []
    counters = {prefix: 0 for prefix in preserved}
    for line in lines:
        stripped = line.strip()
        replaced = False
        for prefix, values in preserved.items():
            if stripped.startswith(prefix):
                idx = counters[prefix]
                if idx < len(values):
                    # Keep the original indentation
                    indent = line[:len(line) - len(line.lstrip())]
                    result.append(indent + values[idx])
                    replaced = True
                counters[prefix] += 1
                break
        if not replaced:
            result.append(line)
    return "\n".join(result)


# ─── Merge strategies ─────────────────────────────────────────────

def full_replace(plugin_content, workspace_content, policy, filename):
    """Replace workspace file entirely with plugin source."""
    if plugin_content == workspace_content:
        return workspace_content, {"action": "unchanged", "reason": "already matches plugin"}

    return plugin_content, {"action": "replaced", "reason": "full replacement (no user data)"}


def section_merge(plugin_content, workspace_content, policy, filename):
    """Merge by replacing template sections, preserving user data sections."""
    plugin_sections = parse_markdown_sections(plugin_content)
    workspace_sections = parse_markdown_sections(workspace_content)

    user_data_headings = set(policy.get("user_data_sections", []))
    preserve_fields = policy.get("preserve_fields", [])

    # Build lookup of workspace sections by heading
    ws_by_heading = {}
    for heading, body in workspace_sections:
        ws_by_heading[heading] = body

    # Extract fields to preserve from the workspace copy
    preserved_fields = {}
    if preserve_fields:
        preserved_fields = extract_preserve_fields(workspace_content, preserve_fields)

    result_sections = []
    changes = []
    preserved_data = []

    # Track which workspace-only sections exist (user-created sections not in plugin)
    plugin_headings = {h for h, _ in plugin_sections}
    workspace_only = [(h, b) for h, b in workspace_sections if h not in plugin_headings and h is not None]

    for heading, plugin_body in plugin_sections:
        if heading in user_data_headings:
            # Use workspace version if it exists, otherwise use plugin template
            if heading in ws_by_heading:
                result_sections.append((heading, ws_by_heading[heading]))
                preserved_data.append(f"{heading} (user data preserved)")
            else:
                result_sections.append((heading, plugin_body))
        else:
            # Template section: use plugin version
            ws_body = ws_by_heading.get(heading)
            if ws_body is not None and ws_body != plugin_body:
                changes.append(f"{heading or 'header'} updated from plugin")
            result_sections.append((heading, plugin_body))

    # Append workspace-only sections (user-created)
    for heading, body in workspace_only:
        result_sections.append((heading, body))
        preserved_data.append(f"{heading} (user section preserved)")

    # Reconstruct the document
    parts = []
    for heading, body in result_sections:
        if heading is not None:
            parts.append(heading)
        parts.append(body)

    merged = "\n".join(parts)

    # Re-apply preserved fields
    has_preserved = any(values for values in preserved_fields.values())
    if has_preserved:
        merged = apply_preserved_fields(merged, preserved_fields)
        for field, values in preserved_fields.items():
            if values:
                preserved_data.append(f"Field '{field}' preserved ({len(values)} occurrence(s))")

    if merged == workspace_content:
        return merged, {"action": "unchanged", "reason": "no changes needed"}

    info = {
        "action": "merged",
        "changes": changes,
        "preserved": preserved_data,
    }
    return merged, info


def additive_merge(plugin_content, workspace_content, policy, filename):
    """For YAML state files: add new keys from plugin, preserve existing values."""
    plugin_keys = parse_yaml_keys(plugin_content)
    workspace_keys = parse_yaml_keys(workspace_content)

    new_keys = []
    for key in plugin_keys:
        if key not in workspace_keys:
            new_keys.append(key)

    if not new_keys:
        return workspace_content, {"action": "unchanged", "reason": "no new keys"}

    # Append new keys to workspace content
    lines = [workspace_content.rstrip()]
    for key in new_keys:
        lines.append(f"{key}: {plugin_keys[key]}")

    merged = "\n".join(lines) + "\n"
    return merged, {
        "action": "merged",
        "new_keys": new_keys,
        "preserved": "all existing values",
    }


STRATEGIES = {
    "full_replace": full_replace,
    "section_merge": section_merge,
    "additive_merge": additive_merge,
}


# ─── Main logic ───────────────────────────────────────────────────

def update_reference_files(workspace_path, plugin_path, dry_run=False):
    """Update all reference files and return a report."""
    ref_dir_workspace = os.path.join(workspace_path, "reference")
    ref_dir_plugin = os.path.join(plugin_path, "reference")

    if not os.path.isdir(ref_dir_plugin):
        return {"error": f"Plugin reference directory not found: {ref_dir_plugin}"}

    # Read plugin version
    plugin_json_path = os.path.join(plugin_path, ".claude-plugin", "plugin.json")
    plugin_version = "unknown"
    if os.path.isfile(plugin_json_path):
        with open(plugin_json_path) as f:
            plugin_version = json.load(f).get("version", "unknown")

    # Read workspace version
    state_path = os.path.join(ref_dir_workspace, ".housekeeping-state.yaml")
    workspace_version = None
    if os.path.isfile(state_path):
        with open(state_path) as f:
            state_content = f.read()
        keys = parse_yaml_keys(state_content)
        workspace_version = keys.get("plugin_version")

    report = {
        "plugin_version": plugin_version,
        "workspace_version": workspace_version,
        "files_updated": [],
        "files_unchanged": [],
        "files_created": [],
        "user_data_preserved": {},
        "conflicts": [],
        "warnings": [],
        "dry_run": dry_run,
    }

    for filename, policy in FILE_POLICIES.items():
        plugin_file = os.path.join(ref_dir_plugin, filename)
        workspace_file = os.path.join(ref_dir_workspace, filename)

        if not os.path.isfile(plugin_file):
            report["warnings"].append(f"{filename}: not found in plugin source, skipped")
            continue

        with open(plugin_file) as f:
            plugin_content = f.read()

        if not os.path.isfile(workspace_file):
            # File doesn't exist in workspace — create it
            if not dry_run:
                with open(workspace_file, "w") as f:
                    f.write(plugin_content)
            report["files_created"].append(filename)
            continue

        with open(workspace_file) as f:
            workspace_content = f.read()

        strategy_fn = STRATEGIES[policy["strategy"]]
        merged_content, info = strategy_fn(plugin_content, workspace_content, policy, filename)

        if info["action"] == "unchanged":
            report["files_unchanged"].append(filename)
        else:
            if not dry_run:
                with open(workspace_file, "w") as f:
                    f.write(merged_content)
            report["files_updated"].append({"file": filename, "details": info})

            if "preserved" in info and info["preserved"]:
                report["user_data_preserved"][filename] = info["preserved"]

    # Update plugin_version in .housekeeping-state.yaml
    if not dry_run and os.path.isfile(state_path):
        with open(state_path) as f:
            state_content = f.read()

        if "plugin_version:" in state_content:
            state_content = re.sub(
                r"plugin_version:.*",
                f"plugin_version: {plugin_version}",
                state_content,
            )
        else:
            state_content = state_content.rstrip() + f"\nplugin_version: {plugin_version}\n"

        with open(state_path, "w") as f:
            f.write(state_content)

    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: update-reference.py <workspace_path> [plugin_path] [--dry-run]")
        print("")
        print("Updates workspace reference files to match the installed plugin version.")
        print("Preserves user customizations (name replacements, KPI definitions, etc.)")
        print("")
        print("Options:")
        print("  --dry-run    Show what would change without modifying files")
        sys.exit(1)

    workspace_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[2:] if a != "--dry-run"]
    plugin_path = args[0] if args else DEFAULT_PLUGIN_DIR

    report = update_reference_files(workspace_path, plugin_path, dry_run)
    print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
