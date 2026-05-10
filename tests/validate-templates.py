#!/usr/bin/env python3
"""Validate system seed file structure and taxonomy completeness."""

import os
import re
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_DIR = os.path.join(PLUGIN_ROOT, "_system")

# Required system seed files
REQUIRED_SYSTEM_FILES = [
    "integrations.md",
    "taxonomy.md",
    "alias-registry.md",
    "kpis.md",
    "schedule.md",
    "guardrails.yaml",
    "maturity.yaml",
    "housekeeping-state.yaml",
    "schemas.yaml",
    "config.md",
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
try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


def is_valid_yaml_structure(filepath):
    """Validate YAML structure. When PyYAML is available, parse the file end-to-end
    so silent escape-sequence bugs (e.g. ``["\\']`` inside a single-quoted string)
    surface here instead of crashing health-check.py at runtime."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        return False, f"Cannot read: {e}"

    if not content.strip():
        return False, "File is empty"

    if _HAS_YAML:
        try:
            _yaml.safe_load(content)
        except _yaml.YAMLError as e:
            return False, f"YAML parse error: {e}"

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

    required_fields = ["onboarding", "deferred_setup", "hydration", "coaching"]
    for field in required_fields:
        if field not in content:
            errors.append(f"maturity.yaml: Missing required field '{field}'")


def validate_housekeeping_state(filepath, errors, warnings):
    """Validate housekeeping-state.yaml has required fields."""
    valid, err = is_valid_yaml_structure(filepath)
    if not valid:
        errors.append(f"housekeeping-state.yaml: {err}")
        return

    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read housekeeping-state.yaml: {e}")
        return

    required_fields = ["last_maintenance", "last_health_check", "last_sync", "cron_jobs", "last_run"]
    for field in required_fields:
        if field not in content:
            errors.append(f"housekeeping-state.yaml: Missing required field '{field}'")


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
    """Validate GETTING-STARTED.md exists and has reasonable content."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read GETTING-STARTED.md: {e}")
        return

    lines = [l for l in content.split("\n") if l.strip()]
    if len(lines) < 10:
        warnings.append(f"GETTING-STARTED.md seems too short ({len(lines)} non-empty lines, expected ~60)")

    content_lower = content.lower()
    if "tars" not in content_lower:
        warnings.append("GETTING-STARTED.md: Doesn't mention 'TARS'")
    if "welcome" not in content_lower and "start" not in content_lower:
        warnings.append("GETTING-STARTED.md: Missing getting started / welcome content")


def validate_alias_registry(filepath, errors, warnings):
    """Validate alias-registry.md has the canonical table shape."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Cannot read alias-registry.md: {e}")
        return

    required_headers = ["canonical", "aliases"]
    lower = content.lower()
    for header in required_headers:
        if header not in lower:
            warnings.append(f"alias-registry.md: Missing table/header text for '{header}'")


def main():
    errors = []
    warnings = []

    # --- 1. Check required system seed files exist ---
    for fname in REQUIRED_SYSTEM_FILES:
        fpath = os.path.join(SYSTEM_DIR, fname)
        if not os.path.isfile(fpath):
            errors.append(f"MISSING: _system/{fname}")

    # --- 2. Validate specific system seed files ---
    taxonomy = os.path.join(SYSTEM_DIR, "taxonomy.md")
    if os.path.isfile(taxonomy):
        validate_taxonomy(taxonomy, errors, warnings)

    guardrails = os.path.join(SYSTEM_DIR, "guardrails.yaml")
    if os.path.isfile(guardrails):
        validate_guardrails(guardrails, errors, warnings)

    maturity = os.path.join(SYSTEM_DIR, "maturity.yaml")
    if os.path.isfile(maturity):
        validate_maturity(maturity, errors, warnings)

    housekeeping = os.path.join(SYSTEM_DIR, "housekeeping-state.yaml")
    if os.path.isfile(housekeeping):
        validate_housekeeping_state(housekeeping, errors, warnings)

    integrations = os.path.join(SYSTEM_DIR, "integrations.md")
    if os.path.isfile(integrations):
        validate_integrations(integrations, errors, warnings)

    getting_started_candidates = [
        os.path.join(PLUGIN_ROOT, "docs", "GETTING-STARTED.md"),
        os.path.join(PLUGIN_ROOT, "GETTING-STARTED.md"),
    ]
    getting_started = next((p for p in getting_started_candidates if os.path.isfile(p)), None)
    if getting_started:
        validate_getting_started(getting_started, errors, warnings)
    else:
        errors.append("MISSING: GETTING-STARTED.md (expected docs/GETTING-STARTED.md)")

    alias_registry = os.path.join(SYSTEM_DIR, "alias-registry.md")
    if os.path.isfile(alias_registry):
        validate_alias_registry(alias_registry, errors, warnings)

    # --- 3. Check YAML files are parseable ---
    yaml_files = [
        "guardrails.yaml",
        "maturity.yaml",
        "housekeeping-state.yaml",
    ]
    for fname in yaml_files:
        fpath = os.path.join(SYSTEM_DIR, fname)
        if os.path.isfile(fpath):
            valid, err = is_valid_yaml_structure(fpath)
            if not valid:
                errors.append(f"_system/{fname}: Invalid YAML structure — {err}")

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
