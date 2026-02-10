#!/usr/bin/env python3
"""Validate cross-references: plugin.json <-> disk, commands <-> skills, routing <-> skills."""

import json
import os
import re
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_JSON = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")
CORE_SKILL = os.path.join(PLUGIN_ROOT, "skills", "core", "SKILL.md")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def load_manifest():
    """Load and return plugin.json contents."""
    try:
        with open(PLUGIN_JSON) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return None


def get_skill_dirs_on_disk():
    """Return set of skill directory names that exist on disk."""
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    if not os.path.isdir(skills_dir):
        return set()
    return {
        entry for entry in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, entry))
        and os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md"))
    }


def get_command_files_on_disk():
    """Return set of command filenames that exist on disk."""
    commands_dir = os.path.join(PLUGIN_ROOT, "commands")
    if not os.path.isdir(commands_dir):
        return set()
    return {
        entry for entry in os.listdir(commands_dir)
        if entry.endswith(".md") and os.path.isfile(os.path.join(commands_dir, entry))
    }


def extract_skill_ref_from_command(filepath):
    """Extract the skill directory referenced by a command file."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception:
        return None

    # Look for pattern: Read and follow `skills/NAME/` or similar
    patterns = [
        r"Read and follow `skills/([^/`]+)/`",
        r"Read and follow `skills/([^/`]+)`",
        r"`skills/([^/`]+)/SKILL\.md`",
        r"`skills/([^/`]+)/`",
        r"skills/([a-z-]+)/",
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    return None


def extract_routing_targets(core_skill_path):
    """Extract skill paths referenced in the routing/signal table."""
    try:
        with open(core_skill_path) as f:
            content = f.read()
    except Exception:
        return []

    # Find all `skills/NAME/` references in routing table
    # Pattern matches backtick-wrapped skill paths
    targets = re.findall(r"`skills/([^/`]+)/`", content)
    # Also match without backticks in table rows
    targets += re.findall(r"skills/([a-z][a-z0-9-]+)/", content)
    # Deduplicate
    return list(set(targets))


def main():
    errors = []
    warnings = []

    # --- 1. Load manifest ---
    manifest = load_manifest()
    if manifest is None:
        errors.append("Cannot load plugin.json — skipping reference validation")
        print_results(errors, warnings)
        return 1

    # --- 2. plugin.json skills -> disk ---
    manifest_skills = manifest.get("skills", [])
    manifest_skill_names = set()
    for skill_path in manifest_skills:
        full_path = os.path.join(PLUGIN_ROOT, skill_path)
        # Extract skill name from path like "skills/meeting/SKILL.md"
        parts = skill_path.split("/")
        if len(parts) >= 2:
            manifest_skill_names.add(parts[1])
        if not os.path.isfile(full_path):
            errors.append(f"plugin.json references skill not on disk: {skill_path}")

    # --- 3. Disk skills -> plugin.json ---
    disk_skills = get_skill_dirs_on_disk()
    for skill_name in sorted(disk_skills):
        expected_path = f"skills/{skill_name}/SKILL.md"
        if expected_path not in manifest_skills:
            warnings.append(f"Skill on disk not in plugin.json: {expected_path}")

    # --- 4. plugin.json commands -> disk ---
    manifest_commands = manifest.get("commands", [])
    manifest_cmd_names = set()
    for cmd_path in manifest_commands:
        full_path = os.path.join(PLUGIN_ROOT, cmd_path)
        parts = cmd_path.split("/")
        if len(parts) >= 2:
            manifest_cmd_names.add(parts[1])
        if not os.path.isfile(full_path):
            errors.append(f"plugin.json references command not on disk: {cmd_path}")

    # --- 5. Disk commands -> plugin.json ---
    disk_commands = get_command_files_on_disk()
    for cmd_file in sorted(disk_commands):
        expected_path = f"commands/{cmd_file}"
        if expected_path not in manifest_commands:
            warnings.append(f"Command on disk not in plugin.json: {expected_path}")

    # --- 6. Commands reference valid skills ---
    commands_dir = os.path.join(PLUGIN_ROOT, "commands")
    if os.path.isdir(commands_dir):
        for cmd_file in sorted(disk_commands):
            cmd_path = os.path.join(commands_dir, cmd_file)
            skill_ref = extract_skill_ref_from_command(cmd_path)
            if skill_ref is None:
                warnings.append(f"commands/{cmd_file}: Cannot detect skill reference")
            elif skill_ref not in disk_skills:
                errors.append(f"commands/{cmd_file}: References non-existent skill '{skill_ref}'")

    # --- 7. Routing table references valid skills ---
    if os.path.isfile(CORE_SKILL):
        routing_targets = extract_routing_targets(CORE_SKILL)
        for target in sorted(set(routing_targets)):
            if target not in disk_skills:
                errors.append(f"Routing table references non-existent skill: skills/{target}/")
    else:
        warnings.append("Core skill not found — cannot validate routing references")

    # --- 8. Skill count sanity check ---
    if len(manifest_skills) < 5:
        warnings.append(f"Unusually few skills in plugin.json: {len(manifest_skills)}")
    if len(manifest_commands) < 5:
        warnings.append(f"Unusually few commands in plugin.json: {len(manifest_commands)}")

    # --- 9. Command-skill pairing check ---
    # Each command should map to a skill that exists in the manifest
    for cmd_file in sorted(disk_commands):
        cmd_name = cmd_file.replace(".md", "")
        cmd_path = os.path.join(commands_dir, cmd_file)
        skill_ref = extract_skill_ref_from_command(cmd_path)
        if skill_ref and skill_ref in disk_skills:
            # Check the skill is also in the manifest
            expected_skill_path = f"skills/{skill_ref}/SKILL.md"
            if expected_skill_path not in manifest_skills:
                warnings.append(
                    f"commands/{cmd_file} references skill '{skill_ref}' "
                    f"which exists on disk but is not in plugin.json"
                )

    print_results(errors, warnings)
    return 1 if errors else 0


def print_results(errors, warnings):
    print("=" * 60)
    print("TARS Cross-Reference Validation")
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
        print("\n  ✓ All cross-reference checks passed")

    print()
    print(f"Result: {len(errors)} errors, {len(warnings)} warnings")
    if not errors:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


if __name__ == "__main__":
    sys.exit(main())
