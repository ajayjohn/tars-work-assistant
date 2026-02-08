#!/usr/bin/env python3
"""Validate routing completeness: every workflow skill has signals, no orphaned signals."""

import json
import os
import re
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_JSON = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")
CORE_SKILL = os.path.join(PLUGIN_ROOT, "skills", "core", "SKILL.md")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def get_user_invocable_skills():
    """Return set of skill directory names that are user-invocable: true."""
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    invocable = set()
    if not os.path.isdir(skills_dir):
        return invocable

    for entry in os.listdir(skills_dir):
        skill_md = os.path.join(skills_dir, entry, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        try:
            with open(skill_md) as f:
                content = f.read()
        except Exception:
            continue

        match = FRONTMATTER_RE.match(content)
        if not match:
            continue

        fm_text = match.group(1)
        # Check user-invocable field
        for line in fm_text.split("\n"):
            line = line.strip()
            if line.startswith("user-invocable:"):
                val = line.split(":", 1)[1].strip().lower()
                if val == "true":
                    invocable.add(entry)
                break

    return invocable


def get_all_skill_dirs():
    """Return set of all skill directory names on disk."""
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    if not os.path.isdir(skills_dir):
        return set()
    return {
        entry for entry in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, entry))
        and os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md"))
    }


def extract_signal_table(core_path):
    """Extract routing signal entries from the core skill.
    Returns list of (signal_text, target_skill_name) tuples."""
    try:
        with open(core_path) as f:
            content = f.read()
    except Exception:
        return []

    entries = []

    # Find markdown table rows in signal table section
    # Look for the signal table section
    in_signal_table = False
    table_header_seen = False

    for line in content.split("\n"):
        stripped = line.strip()

        # Detect signal table start (must be a markdown heading, not inline text)
        if stripped.startswith("#") and "signal table" in stripped.lower():
            in_signal_table = True
            continue

        # Detect next section (end of signal table)
        if in_signal_table and stripped.startswith("##") and "signal table" not in stripped.lower():
            # Check if this is a subsection within the signal table area
            if stripped.startswith("### "):
                # Could be routing rules subsection - keep scanning
                in_signal_table = False
                break
            in_signal_table = False
            break

        if not in_signal_table:
            continue

        # Skip table header and separator
        if stripped.startswith("| Signal") or stripped.startswith("|---"):
            table_header_seen = True
            continue

        # Parse table rows
        if table_header_seen and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")]
            # cols[0] is empty (before first |), cols[1] is signal, cols[2] is route
            if len(cols) >= 3:
                signal = cols[1]
                route = cols[2]

                # Extract skill name from route like `skills/meeting/` or skills/think/ (analyze mode)
                skill_match = re.search(r"skills/([a-z][a-z0-9-]+)/", route)
                if skill_match:
                    entries.append((signal, skill_match.group(1)))

    # Also check the help routing table if present
    in_help_table = False
    for line in content.split("\n"):
        stripped = line.strip()
        if "help routing" in stripped.lower() or ("help" in stripped.lower() and "signal" in stripped.lower()):
            in_help_table = True
            continue
        if in_help_table and stripped.startswith("##"):
            break
        if in_help_table and stripped.startswith("|") and "Signal" not in stripped and "---" not in stripped:
            cols = [c.strip() for c in stripped.split("|")]
            if len(cols) >= 3:
                route = cols[2]
                skill_match = re.search(r"skills/([a-z][a-z0-9-]+)/", route)
                if skill_match:
                    entries.append((cols[1], skill_match.group(1)))

    return entries


def main():
    errors = []
    warnings = []

    # --- 1. Get all user-invocable skills ---
    invocable_skills = get_user_invocable_skills()
    all_skills = get_all_skill_dirs()

    if not invocable_skills:
        errors.append("No user-invocable skills found")
        print_results(errors, warnings)
        return 1

    # --- 2. Extract signal table ---
    if not os.path.isfile(CORE_SKILL):
        errors.append("Core skill (skills/core/SKILL.md) not found — cannot validate routing")
        print_results(errors, warnings)
        return 1

    signal_entries = extract_signal_table(CORE_SKILL)
    if not signal_entries:
        errors.append("No signal entries found in core skill routing table")
        print_results(errors, warnings)
        return 1

    # Build set of skills referenced in routing table
    routed_skills = set()
    for signal, target in signal_entries:
        routed_skills.add(target)

    # --- 3. Every user-invocable skill should have at least one signal ---
    for skill in sorted(invocable_skills):
        if skill not in routed_skills:
            errors.append(f"User-invocable skill '{skill}' has NO signals in routing table")

    # --- 4. No orphaned signals (pointing to non-existent skills) ---
    for signal, target in signal_entries:
        if target not in all_skills:
            errors.append(f"Routing signal points to non-existent skill: skills/{target}/ (signal: '{signal}')")

    # --- 5. Report coverage statistics ---
    print()
    print(f"  User-invocable skills: {len(invocable_skills)}")
    print(f"  Skills with routing signals: {len(routed_skills & invocable_skills)}")
    print(f"  Total signal entries: {len(signal_entries)}")
    print(f"  Unique routed skill targets: {len(routed_skills)}")

    # --- 6. Check for duplicate signals (same signal text mapping to different skills) ---
    signal_map = {}
    for signal, target in signal_entries:
        if signal in signal_map and signal_map[signal] != target:
            warnings.append(
                f"Signal '{signal}' maps to multiple skills: "
                f"{signal_map[signal]} and {target}"
            )
        signal_map[signal] = target

    print_results(errors, warnings)
    return 1 if errors else 0


def print_results(errors, warnings):
    print("=" * 60)
    print("TARS Routing Completeness Validation")
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
        print("\n  ✓ All routing checks passed")

    print()
    print(f"Result: {len(errors)} errors, {len(warnings)} warnings")
    if not errors:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


if __name__ == "__main__":
    sys.exit(main())
