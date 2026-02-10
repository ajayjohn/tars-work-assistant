#!/usr/bin/env python3
"""Validate YAML frontmatter on all TARS skills and commands."""

import os
import re
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Regex to extract YAML frontmatter between --- delimiters
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

# Simple YAML key extractor (stdlib-only, no PyYAML dependency)
# Handles top-level keys and one level of nesting
def parse_simple_yaml(text):
    """Parse simple YAML into a dict of top-level keys with string values.
    Handles nested keys one level deep (returns nested dict)."""
    result = {}
    current_key = None
    current_indent = 0

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Detect indentation level
        indent = len(line) - len(line.lstrip())

        # Top-level key
        if indent == 0 and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                result[key] = value
            else:
                result[key] = {}
                current_key = key
                current_indent = indent
            continue

        # Nested key (simple one-level nesting)
        if indent > 0 and current_key and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
            if isinstance(result.get(current_key), dict):
                result[current_key][key] = value if value else True

    return result


def extract_frontmatter(filepath):
    """Extract and parse YAML frontmatter from a markdown file."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        return None, f"Cannot read file: {e}"

    match = FRONTMATTER_RE.match(content)
    if not match:
        return None, "No YAML frontmatter found (expected --- delimiters)"

    yaml_text = match.group(1)
    try:
        parsed = parse_simple_yaml(yaml_text)
        return parsed, None
    except Exception as e:
        return None, f"Failed to parse YAML frontmatter: {e}"


def validate_skill_frontmatter(filepath, rel_path, errors, warnings):
    """Validate frontmatter for a SKILL.md file."""
    fm, err = extract_frontmatter(filepath)
    if err:
        errors.append(f"{rel_path}: {err}")
        return

    # Required fields
    if "name" not in fm:
        errors.append(f"{rel_path}: Missing required field 'name'")
    if "description" not in fm:
        errors.append(f"{rel_path}: Missing required field 'description'")

    # user-invocable field
    if "user-invocable" not in fm:
        errors.append(f"{rel_path}: Missing required field 'user-invocable'")
    else:
        val = str(fm["user-invocable"]).lower()
        if val not in ("true", "false"):
            errors.append(f"{rel_path}: 'user-invocable' must be true or false, got: {fm['user-invocable']}")

    # Help section (v2.0 requirement)
    if "help" not in fm:
        warnings.append(f"{rel_path}: Missing 'help' section (required for v2.0)")
    else:
        help_val = fm["help"]
        # help can be a string (inline) or a dict (structured)
        if isinstance(help_val, dict):
            # Check for recommended sub-fields
            recommended = ["purpose", "use_cases", "invoke_examples", "common_questions", "related_skills"]
            for field in recommended:
                if field not in help_val:
                    warnings.append(f"{rel_path}: help section missing recommended field '{field}'")

    # Name should match directory name
    skill_name = fm.get("name", "")
    dir_name = os.path.basename(os.path.dirname(filepath))
    if skill_name and skill_name != dir_name:
        warnings.append(f"{rel_path}: name '{skill_name}' doesn't match directory '{dir_name}'")

    # Description should not be empty
    desc = fm.get("description", "")
    if isinstance(desc, str) and len(desc.strip()) < 10:
        warnings.append(f"{rel_path}: Description seems too short ({len(desc.strip())} chars)")


def validate_command_frontmatter(filepath, rel_path, errors, warnings):
    """Validate frontmatter for a command .md file."""
    fm, err = extract_frontmatter(filepath)
    if err:
        errors.append(f"{rel_path}: {err}")
        return

    # Required field
    if "description" not in fm:
        errors.append(f"{rel_path}: Missing required field 'description'")
    else:
        desc = fm.get("description", "")
        if isinstance(desc, str) and len(desc.strip()) < 5:
            warnings.append(f"{rel_path}: Description seems too short")


def main():
    errors = []
    warnings = []

    # --- Validate all skill SKILL.md files ---
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    if os.path.isdir(skills_dir):
        for entry in sorted(os.listdir(skills_dir)):
            skill_dir = os.path.join(skills_dir, entry)
            if os.path.isdir(skill_dir):
                skill_md = os.path.join(skill_dir, "SKILL.md")
                if os.path.isfile(skill_md):
                    rel_path = f"skills/{entry}/SKILL.md"
                    validate_skill_frontmatter(skill_md, rel_path, errors, warnings)
                else:
                    errors.append(f"skills/{entry}/: SKILL.md not found")

    # --- Validate all command .md files ---
    commands_dir = os.path.join(PLUGIN_ROOT, "commands")
    if os.path.isdir(commands_dir):
        for entry in sorted(os.listdir(commands_dir)):
            if entry.endswith(".md"):
                cmd_path = os.path.join(commands_dir, entry)
                rel_path = f"commands/{entry}"
                validate_command_frontmatter(cmd_path, rel_path, errors, warnings)

    print_results(errors, warnings)
    return 1 if errors else 0


def print_results(errors, warnings):
    print("=" * 60)
    print("TARS Frontmatter Validation")
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
        print("\n  ✓ All frontmatter checks passed")

    print()
    print(f"Result: {len(errors)} errors, {len(warnings)} warnings")
    if not errors:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


if __name__ == "__main__":
    sys.exit(main())
