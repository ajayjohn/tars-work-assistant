#!/usr/bin/env python3
"""Validate reference file structure and taxonomy completeness."""

import os
import re
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE_DIR = os.path.join(PLUGIN_ROOT, "reference")

# Required reference files
REQUIRED_REFERENCE_FILES = [
    "integrations.md",
    "taxonomy.md",
    "replacements.md",
    "kpis.md",
    "schedule.md",
    "guardrails.yaml",
    "maturity.yaml",
    ".housekeeping-state.yaml",
    "getting-started.md",
    "workflows.md",
]

# Memory types that should be defined in taxonomy.md
EXPECTED_MEMORY_TYPES = [
    "person",
    "vendor",
    "competitor",
    "product",
    "initiative",
    "decision",
    "context",
]

# Staleness tiers that should be documented
EXPECTED_STALENESS_TIERS = [
    "durable",
    "seasonal",
    "transient",
    "ephemeral",
]

# Simple YAML validator (checks for valid key: value structure)
def is_valid_yaml_structure(filepath):
    """Basic validation that a YAML file has valid structure.
    Returns (valid, error_message)."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        return False, f"Cannot read: {e}"

    if not content.strip():
        return False, "File is empty"

    # Check for basic YAML structure (key: value or key:\n on at least some lines)
    has_keys = False
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped:
            has_keys = True
            break

    if not has_keys:
        return False, "No YAML key-value pairs found"

    # Check for common YAML errors
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        if "\t" in line and not line.strip().startswith("#"):
            return False, f"Tab character found on line {i} (YAML requires spaces)"

    return True, None


def validate_taxonomy(filepath, errors, warnings):
    """Validate taxonomy.md contains required type definitions and staleness tiers."""
    try:
        with open(filepath) as f:
            content = f.read().lower()
    except Exception as e:
        errors.append(f"Cannot read taxonomy.md: {e}")
        return

    # Check memory types are defined
    for mtype in EXPECTED_MEMORY_TYPES:
        if mtype not in content:
            errors.append(f"taxonomy.md: Missing memory type definition for '{mtype}'")

    # Check staleness tiers are documented
    for tier in EXPECTED_STALENESS_TIERS:
        if tier not in content:
            errors.append(f"taxonomy.md: Missing staleness tier definition for '{tier}'")

    # Check for relationship types section
    if "relationship" not in content:
        warnings.append("taxonomy.md: No 'relationship' section found")

    # Check for frontmatter template section
    if "frontmatter" not in content and "template" not in content:
        warnings.append("taxonomy.md: No frontmatter template section found")

    # Check for index format documentation
    if "index" not in content:
        warnings.append("taxonomy.md: No index format documentation found")

    # Minimum length check (comprehensive taxonomy should be substantial)
    if len(content) < 500:
        warnings.append(f"taxonomy.md seems too short ({len(content)} chars) for a comprehensive taxonomy")


def validate_guardrails(filepath, errors, warnings):
    """Validate guardrails.yaml has sensitive data patterns."""
    valid, err = is_valid_yaml_structure(filepath)
    if not valid:
        errors.append(f"guardrails.yaml: {err}")
        return

    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read guardrails.yaml: {e}")
        return

    # Check for required pattern types
    required_patterns = ["ssn", "api_key", "password", "bearer_token", "jwt"]
    for pattern_type in required_patterns:
        if pattern_type not in content.lower():
            errors.append(f"guardrails.yaml: Missing pattern type '{pattern_type}'")

    # Check for allowed_data section
    if "allowed_data" not in content:
        warnings.append("guardrails.yaml: Missing 'allowed_data' section")

    # Check for action types (block, warn)
    if "block" not in content:
        warnings.append("guardrails.yaml: No 'block' action defined for any pattern")
    if "warn" not in content:
        warnings.append("guardrails.yaml: No 'warn' action defined (consider having some patterns as warnings)")


def validate_maturity(filepath, errors, warnings):
    """Validate maturity.yaml has required fields."""
    valid, err = is_valid_yaml_structure(filepath)
    if not valid:
        errors.append(f"maturity.yaml: {err}")
        return

    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read maturity.yaml: {e}")
        return

    required_fields = ["level", "stats", "milestones"]
    for field in required_fields:
        if field not in content:
            errors.append(f"maturity.yaml: Missing required field '{field}'")


def validate_housekeeping_state(filepath, errors, warnings):
    """Validate .housekeeping-state.yaml has required fields."""
    valid, err = is_valid_yaml_structure(filepath)
    if not valid:
        errors.append(f".housekeeping-state.yaml: {err}")
        return

    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read .housekeeping-state.yaml: {e}")
        return

    required_fields = ["last_run", "last_success", "run_count"]
    for field in required_fields:
        if field not in content:
            errors.append(f".housekeeping-state.yaml: Missing required field '{field}'")


def validate_integrations(filepath, errors, warnings):
    """Validate integrations.md has provider-agnostic registry format."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read integrations.md: {e}")
        return

    content_lower = content.lower()

    # Check for required integration categories
    required_categories = ["calendar", "tasks"]
    for cat in required_categories:
        if cat not in content_lower:
            errors.append(f"integrations.md: Missing required category '{cat}'")

    # Check for registry format fields
    registry_fields = ["category", "status", "provider", "type", "operations"]
    for field in registry_fields:
        if field not in content_lower:
            warnings.append(f"integrations.md: Missing registry field '{field}'")

    # Check for status values
    if "configured" not in content_lower and "not_configured" not in content_lower:
        warnings.append("integrations.md: No status values found (expected 'configured' or 'not_configured')")


def validate_getting_started(filepath, errors, warnings):
    """Validate getting-started.md exists and has reasonable content."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read getting-started.md: {e}")
        return

    lines = [l for l in content.split("\n") if l.strip()]
    if len(lines) < 10:
        warnings.append(f"getting-started.md seems too short ({len(lines)} non-empty lines, expected ~60)")

    content_lower = content.lower()
    if "tars" not in content_lower:
        warnings.append("getting-started.md: Doesn't mention 'TARS'")
    if "welcome" not in content_lower and "start" not in content_lower:
        warnings.append("getting-started.md: Missing getting started / welcome content")


def validate_workflows(filepath, errors, warnings):
    """Validate workflows.md has common workflow patterns."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read workflows.md: {e}")
        return

    lines = [l for l in content.split("\n") if l.strip()]
    if len(lines) < 15:
        warnings.append(f"workflows.md seems too short ({len(lines)} non-empty lines, expected ~80)")

    content_lower = content.lower()
    # Check for expected workflow topics
    expected_topics = ["meeting", "review", "analysis"]
    for topic in expected_topics:
        if topic not in content_lower:
            warnings.append(f"workflows.md: Missing workflow pattern for '{topic}'")


def main():
    errors = []
    warnings = []

    # --- 1. Check required reference files exist ---
    for fname in REQUIRED_REFERENCE_FILES:
        fpath = os.path.join(REFERENCE_DIR, fname)
        if not os.path.isfile(fpath):
            errors.append(f"MISSING: reference/{fname}")

    # --- 2. Validate specific reference files ---
    taxonomy = os.path.join(REFERENCE_DIR, "taxonomy.md")
    if os.path.isfile(taxonomy):
        validate_taxonomy(taxonomy, errors, warnings)

    guardrails = os.path.join(REFERENCE_DIR, "guardrails.yaml")
    if os.path.isfile(guardrails):
        validate_guardrails(guardrails, errors, warnings)

    maturity = os.path.join(REFERENCE_DIR, "maturity.yaml")
    if os.path.isfile(maturity):
        validate_maturity(maturity, errors, warnings)

    housekeeping = os.path.join(REFERENCE_DIR, ".housekeeping-state.yaml")
    if os.path.isfile(housekeeping):
        validate_housekeeping_state(housekeeping, errors, warnings)

    integrations = os.path.join(REFERENCE_DIR, "integrations.md")
    if os.path.isfile(integrations):
        validate_integrations(integrations, errors, warnings)

    getting_started = os.path.join(REFERENCE_DIR, "getting-started.md")
    if os.path.isfile(getting_started):
        validate_getting_started(getting_started, errors, warnings)

    workflows = os.path.join(REFERENCE_DIR, "workflows.md")
    if os.path.isfile(workflows):
        validate_workflows(workflows, errors, warnings)

    # --- 3. Check YAML files are parseable ---
    yaml_files = [
        "guardrails.yaml",
        "maturity.yaml",
        ".housekeeping-state.yaml",
    ]
    for fname in yaml_files:
        fpath = os.path.join(REFERENCE_DIR, fname)
        if os.path.isfile(fpath):
            valid, err = is_valid_yaml_structure(fpath)
            if not valid:
                errors.append(f"reference/{fname}: Invalid YAML structure — {err}")

    # --- 4. Check memory directory structure ---
    memory_dir = os.path.join(PLUGIN_ROOT, "memory")
    if os.path.isdir(memory_dir):
        # Check for master index
        master_index = os.path.join(memory_dir, "_index.md")
        if not os.path.isfile(master_index):
            warnings.append("memory/_index.md (master index) not found")

        # Check category subdirectories
        expected_subdirs = ["people", "competitors", "decisions", "initiatives", "organizational-context", "products", "vendors"]
        for subdir in expected_subdirs:
            subpath = os.path.join(memory_dir, subdir)
            if not os.path.isdir(subpath):
                warnings.append(f"memory/{subdir}/ directory not found")
    else:
        warnings.append("memory/ directory not found")

    # --- 5. Check inbox directory structure ---
    inbox_dir = os.path.join(PLUGIN_ROOT, "inbox")
    if os.path.isdir(inbox_dir):
        expected_inbox_subdirs = ["pending", "processing", "completed", "failed"]
        for subdir in expected_inbox_subdirs:
            subpath = os.path.join(inbox_dir, subdir)
            if not os.path.isdir(subpath):
                warnings.append(f"inbox/{subdir}/ directory not found")
    else:
        warnings.append("inbox/ directory not found")

    # --- 6. Check archive directory exists ---
    archive_dir = os.path.join(PLUGIN_ROOT, "archive")
    if not os.path.isdir(archive_dir):
        warnings.append("archive/ directory not found")

    print_results(errors, warnings)
    return 1 if errors else 0


def print_results(errors, warnings):
    print("=" * 60)
    print("TARS Template & Data Structure Validation")
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
        print("\n  ✓ All template and data structure checks passed")

    print()
    print(f"Result: {len(errors)} errors, {len(warnings)} warnings")
    if not errors:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


if __name__ == "__main__":
    sys.exit(main())
