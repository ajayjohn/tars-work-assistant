#!/usr/bin/env python3
"""Validate documentation consistency: stale references, provider compliance, counts, terminology, changelog.

Catches semantic drift between documentation and implementation that structural
validators miss. Designed to prevent recurring issues when different agents
update the framework.

Checks:
1. Stale skill/command name references in documentation files
2. Provider-agnostic compliance (no hardcoded provider names in skills)
3. Count consistency (skill/command/script counts match reality)
4. Archival tier terminology consistency
5. Changelog completeness for current version
"""

import json
import os
import re
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files to scan for documentation consistency
DOC_FILES = [
    "ARCHITECTURE.md",
    "README.md",
    "GETTING-STARTED.md",
    "CHANGELOG.md",
    "CATALOG.md",
    "reference/workflows.md",
    "reference/shortcuts.md",
]

# Known placeholder/example skill names used in documentation templates
PLACEHOLDER_SKILL_NAMES = {"new-skill", "example-skill", "my-skill"}

# Consolidated v1.x skill names that should no longer appear as current references.
# These were consolidated in v2.0.0 and any reference to them as current skills is stale.
V1_BLOCKLIST = {
    "process-meeting",
    "extract-tasks",
    "extract-memory",
    "extract-wisdom",
    "manage-tasks",
    "housekeeping",
    "rebuild-index",
    "quick-answer",
    "strategic-analysis",
    "executive-council",
    "validation-council",
    "discovery-mode",
    "performance-report",
    "create-artifact",
    "daily-briefing",
    "weekly-briefing",
    "deep-analysis",
    "meeting-processor",
    "create-shortcut",
}

# Provider-specific terms that should only appear in integrations.md and GETTING-STARTED.md.
# Case-insensitive matching.
PROVIDER_TERMS = [
    r"\beventlink\b",
    r"\bremindctl\b",
]

# Files exempt from provider-agnostic check
PROVIDER_EXEMPT_FILES = {
    "reference/integrations.md",
    "GETTING-STARTED.md",
    "CHANGELOG.md",
    "CATALOG.md",
}

# Canonical archival tier names
CANONICAL_TIERS = {"durable", "seasonal", "transient", "ephemeral"}

# Incorrect tier name patterns (only flag when used as archival tier labels)
# We look for "warm" and "cool" specifically since "active" and "archived"
# have many legitimate non-tier uses.
WRONG_TIER_PATTERN = re.compile(
    r"\b(warm|cool)\b.*\b(tier|archiv|content\s+lifecycle|content\s+durability)",
    re.IGNORECASE,
)
WRONG_TIER_CLUSTER = re.compile(
    r"active,?\s*warm,?\s*cool,?\s*archived",
    re.IGNORECASE,
)


def get_skill_dirs():
    """Return set of skill directory names on disk."""
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    if not os.path.isdir(skills_dir):
        return set()
    return {
        entry for entry in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, entry))
        and os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md"))
    }


def get_command_names():
    """Return set of command names (without .md extension) on disk."""
    commands_dir = os.path.join(PLUGIN_ROOT, "commands")
    if not os.path.isdir(commands_dir):
        return set()
    return {
        entry.replace(".md", "")
        for entry in os.listdir(commands_dir)
        if entry.endswith(".md")
        and os.path.isfile(os.path.join(commands_dir, entry))
    }


def get_script_files():
    """Return set of script filenames on disk."""
    scripts_dir = os.path.join(PLUGIN_ROOT, "scripts")
    if not os.path.isdir(scripts_dir):
        return set()
    return {
        entry for entry in os.listdir(scripts_dir)
        if os.path.isfile(os.path.join(scripts_dir, entry))
        and (entry.endswith(".py") or entry.endswith(".sh"))
    }


def get_skill_md_files():
    """Return list of relative paths to all SKILL.md files."""
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    if not os.path.isdir(skills_dir):
        return []
    result = []
    for entry in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, entry, "SKILL.md")
        if os.path.isfile(skill_md):
            result.append(f"skills/{entry}/SKILL.md")
    return result


def read_file(relpath):
    """Read a file relative to PLUGIN_ROOT, return content or None."""
    fullpath = os.path.join(PLUGIN_ROOT, relpath)
    try:
        with open(fullpath) as f:
            return f.read()
    except (FileNotFoundError, PermissionError):
        return None


def load_plugin_json():
    """Load plugin.json and return dict, or None on error."""
    path = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# ============================================================
# Check 1: Stale skill/command name references
# ============================================================

def _is_in_historical_section(content, pos, current_version=None):
    """Check if a position in content is inside a historical changelog section.

    For CHANGELOG.md, returns True if the position is under any version header
    OTHER than the current version. For other files, returns True if the position
    is in a section about historical versions (v1.x, v0.x, etc.).
    """
    # Find the nearest preceding ## header
    preceding = content[:pos]
    # Look for version headers: ## vX.Y.Z or ## [X.Y.Z]
    headers = list(re.finditer(r"##\s+(?:v|)\[?(\d+\.\d+\.\d+)\]?", preceding))
    if not headers:
        return False
    nearest_version = headers[-1].group(1)
    # If we know the current version, anything else is historical
    if current_version:
        return nearest_version != current_version
    # Otherwise, consider v0.x and v1.x as historical
    return nearest_version.startswith("0.") or nearest_version.startswith("1.")


def check_stale_references(errors, warnings):
    """Scan documentation for references to skills or commands that don't exist."""
    valid_skills = get_skill_dirs()
    valid_commands = get_command_names()
    manifest = load_plugin_json()
    current_version = manifest.get("version", "") if manifest else ""

    # Patterns to detect skill references in docs
    skill_ref_pattern = re.compile(r"skills/([a-z][a-z0-9-]+)/")
    # Slash-command pattern: `/word` in backticks or as standalone reference
    # Matches /name but not filesystem paths like /Users/ or /path/to/
    slash_cmd_pattern = re.compile(r"(?:^|[\s`(])/((?:[a-z][a-z0-9-]*))(?=[\s`).,:;!?\]]|$)", re.MULTILINE)

    # Exclude CHANGELOG.md — changelogs inherently reference old names when
    # documenting consolidations/renames. Changelog has its own check (Check 5).
    files_to_scan = [f for f in DOC_FILES if f != "CHANGELOG.md"] + get_skill_md_files()

    for relpath in files_to_scan:
        content = read_file(relpath)
        if content is None:
            continue

        # For CHANGELOG.md, only check the current version's section
        is_changelog = relpath == "CHANGELOG.md"

        # Check for skills/{name}/ references
        for match in skill_ref_pattern.finditer(content):
            skill_name = match.group(1)
            # Skip placeholder/example names
            if skill_name in PLACEHOLDER_SKILL_NAMES:
                continue
            if skill_name not in valid_skills:
                # Skip historical changelog sections
                if is_changelog and _is_in_historical_section(content, match.start(), current_version):
                    continue
                lineno = content[:match.start()].count("\n") + 1
                errors.append(
                    f"{relpath}:{lineno}: References non-existent skill "
                    f"'skills/{skill_name}/'"
                )

        # Check for /command-name references
        for match in slash_cmd_pattern.finditer(content):
            cmd_name = match.group(1)
            # Skip common non-command paths and known false positives
            if cmd_name in ("setup", "path", "usr", "bin", "etc", "tmp",
                            "dev", "home", "var", "opt", "proc", "sys",
                            "absolute", "help", "clear", "fast"):
                continue
            if cmd_name not in valid_commands and cmd_name not in valid_skills:
                # Skip historical changelog sections
                if is_changelog and _is_in_historical_section(content, match.start(), current_version):
                    continue
                lineno = content[:match.start()].count("\n") + 1
                # Only warn for non-blocklist items (could be mode references)
                if cmd_name in V1_BLOCKLIST:
                    errors.append(
                        f"{relpath}:{lineno}: References consolidated v1.x "
                        f"command '/{cmd_name}' (no longer exists)"
                    )
                else:
                    warnings.append(
                        f"{relpath}:{lineno}: References unknown command "
                        f"'/{cmd_name}' — verify this is intentional"
                    )

        # Check for v1.x blocklist names in prose (not just as /commands)
        # Look for backtick-wrapped or skill-path references
        for old_name in V1_BLOCKLIST:
            # Match as backtick-wrapped skill reference or skills/name/ path
            blocklist_patterns = [
                re.compile(rf"`{re.escape(old_name)}`"),
                re.compile(rf"skills/{re.escape(old_name)}/"),
            ]
            for pattern in blocklist_patterns:
                for match in pattern.finditer(content):
                    lineno = content[:match.start()].count("\n") + 1
                    # Skip historical changelog sections
                    if is_changelog and _is_in_historical_section(content, match.start(), current_version):
                        continue
                    # Skip if inside a historical section in other docs
                    context_start = max(0, match.start() - 500)
                    context = content[context_start:match.start()]
                    if re.search(r"##\s+v[01]\.", context) or re.search(r"##\s+\[1\.", context):
                        continue
                    # Skip if in a "Removed" or "Breaking changes" section
                    if re.search(r"###\s+(Removed|Breaking)", context):
                        continue
                    # Skip if on a line that's clearly a historical comparison (has →)
                    line_start = content.rfind("\n", 0, match.start()) + 1
                    line_end = content.find("\n", match.end())
                    if line_end == -1:
                        line_end = len(content)
                    line = content[line_start:line_end]
                    if "→" in line or "->" in line:
                        continue
                    errors.append(
                        f"{relpath}:{lineno}: References consolidated v1.x "
                        f"skill '{old_name}'"
                    )


# ============================================================
# Check 2: Provider-agnostic compliance
# ============================================================

def check_provider_compliance(errors, warnings):
    """Scan skill files for hardcoded provider names."""
    skill_files = get_skill_md_files()

    for relpath in skill_files:
        # Skip exemptions (integrations.md etc. are checked separately)
        if relpath in PROVIDER_EXEMPT_FILES:
            continue

        content = read_file(relpath)
        if content is None:
            continue

        for term_pattern in PROVIDER_TERMS:
            for match in re.finditer(term_pattern, content, re.IGNORECASE):
                lineno = content[:match.start()].count("\n") + 1
                # Skip if inside a code comment or historical context
                line_start = content.rfind("\n", 0, match.start()) + 1
                line_end = content.find("\n", match.end())
                if line_end == -1:
                    line_end = len(content)
                line = content[line_start:line_end]
                # Allow if in HTML comment
                if "<!--" in line:
                    continue
                errors.append(
                    f"{relpath}:{lineno}: Hardcoded provider name "
                    f"'{match.group()}' — use provider-agnostic language "
                    f"(provider names belong only in reference/integrations.md)"
                )

    # Also check doc files (except exempt ones)
    for relpath in DOC_FILES:
        if relpath in PROVIDER_EXEMPT_FILES:
            continue

        content = read_file(relpath)
        if content is None:
            continue

        for term_pattern in PROVIDER_TERMS:
            for match in re.finditer(term_pattern, content, re.IGNORECASE):
                lineno = content[:match.start()].count("\n") + 1
                warnings.append(
                    f"{relpath}:{lineno}: Contains provider-specific term "
                    f"'{match.group()}' — consider using generic language"
                )


# ============================================================
# Check 3: Count consistency
# ============================================================

def check_count_consistency(errors, warnings):
    """Verify quantitative claims in docs match reality."""
    actual_skills = len(get_skill_dirs())
    actual_commands = len(get_command_names())
    actual_scripts = len(get_script_files())
    expected_token_baseline = actual_skills * 4  # ~4 tokens per skill metadata

    # Patterns to find count claims
    count_patterns = {
        "skills": re.compile(r"(\d+)\s+skills?\b", re.IGNORECASE),
        "commands": re.compile(r"(\d+)\s+commands?\b", re.IGNORECASE),
        "scripts": re.compile(r"(\d+)\s+(?:automation\s+)?scripts?\b", re.IGNORECASE),
    }

    actual_counts = {
        "skills": actual_skills,
        "commands": actual_commands,
        "scripts": actual_scripts,
    }

    # Token baseline pattern
    token_pattern = re.compile(r"~?(\d+)\s+tokens?\b", re.IGNORECASE)

    files_to_check = ["ARCHITECTURE.md", "README.md"]

    for relpath in files_to_check:
        content = read_file(relpath)
        if content is None:
            continue

        for category, pattern in count_patterns.items():
            for match in pattern.finditer(content):
                claimed = int(match.group(1))
                actual = actual_counts[category]
                lineno = content[:match.start()].count("\n") + 1

                # Get the full line for context analysis
                line_start = content.rfind("\n", 0, match.start()) + 1
                line_end = content.find("\n", match.end())
                if line_end == -1:
                    line_end = len(content)
                line = content[line_start:line_end]

                # Skip historical comparison lines (contain → or v1.x references)
                if "→" in line or "->" in line:
                    continue
                # Skip lines that start with "v1" or reference old versions
                if re.match(r"^\s*[-|]?\s*v[01]\.", line):
                    continue
                # Skip counts in comparison table cells that belong to
                # a historical version column. Detect by finding the header
                # row and checking if this match is in the old-version column.
                if "|" in line:
                    # Find the table header row (look backwards for a
                    # separator row like |---|---| then take the line above it)
                    preceding_lines = content[:line_start].rstrip().split("\n")
                    header_line = ""
                    for prev_idx in range(len(preceding_lines) - 1, -1, -1):
                        prev_line = preceding_lines[prev_idx].strip()
                        if re.match(r"\|[\s:-]+\|", prev_line) and set(prev_line.replace("|","").replace("-","").replace(":","").strip()) <= {" ", ""}:
                            # This is a separator row; header is the line before
                            if prev_idx > 0:
                                header_line = preceding_lines[prev_idx - 1]
                            break
                        elif "|" not in prev_line:
                            break  # Left the table, stop looking
                    if header_line:
                        header_cells = [c.strip() for c in header_line.split("|")]
                        data_cells = [c.strip() for c in line.split("|")]
                        # Find which cell index contains the match
                        match_pos = match.start() - line_start
                        running = 0
                        match_cell = -1
                        for ci, cell in enumerate(data_cells):
                            cell_end = running + len(cell) + 1
                            if running <= match_pos < cell_end:
                                match_cell = ci
                                break
                            running = cell_end
                        # If the corresponding header cell references a
                        # historical version (v0.x, v1.x), skip this match
                        if 0 <= match_cell < len(header_cells):
                            hdr = header_cells[match_cell].lower()
                            if re.search(r"v?[01]\.\d", hdr):
                                continue

                # Skip if inside a section about historical versions
                context_start = max(0, match.start() - 500)
                context = content[context_start:match.start()]
                # Skip "Added/Changed/Removed" changelog subsections
                if re.search(r"###\s+(Added|Changed|Removed)", context):
                    continue
                # Skip ranges like "28 to 12 skills"
                pre_text = content[max(0, match.start() - 30):match.start()]
                if re.search(r"\d+\s+(to|→|->)\s*$", pre_text):
                    continue

                if claimed != actual:
                    errors.append(
                        f"{relpath}:{lineno}: Claims {claimed} {category} "
                        f"but actual count is {actual}"
                    )

        # Token baseline check in ARCHITECTURE.md
        if relpath == "ARCHITECTURE.md":
            for match in token_pattern.finditer(content):
                claimed_tokens = int(match.group(1))
                lineno = content[:match.start()].count("\n") + 1
                # Only check lines that discuss session baseline or L1 loading
                line_start = content.rfind("\n", 0, match.start()) + 1
                line_end = content.find("\n", match.end())
                if line_end == -1:
                    line_end = len(content)
                line = content[line_start:line_end].lower()
                if "baseline" in line or "l1" in line or "session start" in line:
                    if claimed_tokens != expected_token_baseline:
                        warnings.append(
                            f"{relpath}:{lineno}: Claims ~{claimed_tokens} "
                            f"tokens baseline but {actual_skills} skills × 4 "
                            f"= {expected_token_baseline} tokens"
                        )


# ============================================================
# Check 4: Archival tier terminology
# ============================================================

def check_tier_terminology(errors, warnings):
    """Verify archival tier names are consistent across all docs."""
    all_files = list(DOC_FILES) + get_skill_md_files()

    for relpath in all_files:
        content = read_file(relpath)
        if content is None:
            continue

        # Skip changelog historical sections
        if relpath == "CHANGELOG.md":
            continue

        # Check for the specific wrong cluster: "active, warm, cool, archived"
        for match in WRONG_TIER_CLUSTER.finditer(content):
            lineno = content[:match.start()].count("\n") + 1
            errors.append(
                f"{relpath}:{lineno}: Uses incorrect archival tier names "
                f"'{match.group()}' — canonical names are: "
                f"durable, seasonal, transient, ephemeral"
            )

        # Check for "warm" or "cool" near tier/archival terminology
        for match in WRONG_TIER_PATTERN.finditer(content):
            lineno = content[:match.start()].count("\n") + 1
            # Avoid duplicate if already caught by cluster check
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.end())
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end]
            if not WRONG_TIER_CLUSTER.search(line):
                warnings.append(
                    f"{relpath}:{lineno}: Possible incorrect archival tier "
                    f"terminology — canonical names are: durable, seasonal, "
                    f"transient, ephemeral"
                )


# ============================================================
# Check 5: Changelog completeness
# ============================================================

def check_changelog_completeness(errors, warnings):
    """Verify current version has a substantive changelog entry."""
    manifest = load_plugin_json()
    if manifest is None:
        warnings.append("Cannot load plugin.json — skipping changelog check")
        return

    version = manifest.get("version", "")
    if not version:
        warnings.append("No version in plugin.json — skipping changelog check")
        return

    content = read_file("CHANGELOG.md")
    if content is None:
        errors.append("CHANGELOG.md not found")
        return

    # Find the section for the current version
    # Pattern: ## vX.Y.Z or ## [X.Y.Z]
    version_header = re.compile(
        rf"##\s+(?:v|)\[?{re.escape(version)}\]?"
    )
    match = version_header.search(content)
    if match is None:
        errors.append(
            f"CHANGELOG.md: No entry found for current version v{version}"
        )
        return

    # Extract content between this version header and the next version header
    next_header = re.search(r"\n##\s+", content[match.end():])
    if next_header:
        section = content[match.end():match.end() + next_header.start()]
    else:
        section = content[match.end():]

    # Count substantive lines (non-empty, not just "Bumped from vX.Y.Z")
    substantive_lines = [
        line for line in section.strip().split("\n")
        if line.strip()
        and not re.match(r"^>\s*Bumped from", line.strip())
        and not line.strip().startswith("---")
    ]

    if len(substantive_lines) < 3:
        warnings.append(
            f"CHANGELOG.md: Entry for v{version} appears incomplete "
            f"({len(substantive_lines)} substantive lines — expected at least 3)"
        )


# ============================================================
# Main
# ============================================================

def print_results(errors, warnings):
    print("=" * 60)
    print("TARS Documentation Consistency Validation")
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
        print("\n  ✓ All documentation consistency checks passed")

    print()
    print(f"Result: {len(errors)} errors, {len(warnings)} warnings")
    if not errors:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


def main():
    errors = []
    warnings = []

    check_stale_references(errors, warnings)
    check_provider_compliance(errors, warnings)
    check_count_consistency(errors, warnings)
    check_tier_terminology(errors, warnings)
    check_changelog_completeness(errors, warnings)

    print_results(errors, warnings)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
