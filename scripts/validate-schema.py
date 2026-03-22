#!/usr/bin/env python3
"""
TARS Schema Validator
Validates frontmatter in vault notes against _system/schemas.yaml definitions.
Outputs JSON for agent consumption.

Usage: python3 scripts/validate-schema.py [vault_path] [--fix] [--type TYPE]
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def simple_yaml_load(filepath):
    """Minimal YAML parser for schemas format when PyYAML unavailable."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    schemas = {}
    current_type = None
    current_section = None
    current_rule_prop = None

    for line in content.split("\n"):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if stripped.startswith("#") or not stripped:
            continue

        if indent == 0 and stripped.endswith(":") and not stripped.startswith("-"):
            current_type = stripped[:-1]
            schemas[current_type] = {
                "required_tags": [],
                "required_properties": [],
                "optional_properties": [],
                "property_rules": {},
            }
            current_section = None
            current_rule_prop = None
        elif current_type and indent == 2:
            if stripped.startswith("required_tags:"):
                val = stripped.split(":", 1)[1].strip()
                if val.startswith("[") and val.endswith("]"):
                    schemas[current_type]["required_tags"] = [
                        v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()
                    ]
                else:
                    current_section = "required_tags"
            elif stripped.startswith("required_properties:"):
                current_section = "required_properties"
            elif stripped.startswith("optional_properties:"):
                current_section = "optional_properties"
            elif stripped.startswith("property_rules:"):
                current_section = "property_rules"
                current_rule_prop = None
        elif current_type and indent == 4:
            if current_section in ("required_tags", "required_properties", "optional_properties"):
                if stripped.startswith("- "):
                    val = stripped[2:].strip().strip("'\"")
                    schemas[current_type][current_section].append(val)
            elif current_section == "property_rules":
                if stripped.endswith(":") and not stripped.startswith("-"):
                    current_rule_prop = stripped[:-1]
                    schemas[current_type]["property_rules"][current_rule_prop] = {}
        elif current_type and indent == 6 and current_rule_prop:
            if stripped.startswith("enum:"):
                val = stripped.split(":", 1)[1].strip()
                if val.startswith("[") and val.endswith("]"):
                    schemas[current_type]["property_rules"][current_rule_prop]["enum"] = [
                        v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()
                    ]
            elif stripped.startswith("type:"):
                schemas[current_type]["property_rules"][current_rule_prop]["type"] = (
                    stripped.split(":", 1)[1].strip()
                )

    return schemas


def load_schemas(vault_path):
    """Load schema definitions from _system/schemas.yaml."""
    schema_path = Path(vault_path) / "_system" / "schemas.yaml"
    if not schema_path.exists():
        return None, f"Schema file not found: {schema_path}"
    with open(schema_path, "r") as f:
        if HAS_YAML:
            return yaml.safe_load(f), None
        else:
            pass
    return simple_yaml_load(schema_path), None


def parse_frontmatter(file_path):
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return None, f"Cannot read file: {file_path}"

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None, None  # No frontmatter, not an error for non-TARS files

    try:
        if HAS_YAML:
            fm = yaml.safe_load(match.group(1))
        else:
            fm = {}
            current_list_key = None
            for line in match.group(1).split("\n"):
                stripped = line.strip()
                indent = len(line) - len(line.lstrip())
                if not stripped or stripped.startswith("#"):
                    current_list_key = None
                    continue
                if stripped.startswith("- ") and current_list_key:
                    val = stripped[2:].strip().strip("'\"")
                    if isinstance(fm.get(current_list_key), list):
                        fm[current_list_key].append(val)
                    else:
                        fm[current_list_key] = [val]
                elif ":" in stripped:
                    key, _, val = stripped.partition(":")
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if val == "" or val == "[]":
                        fm[key] = []
                        current_list_key = key
                    elif val.startswith("[") and val.endswith("]"):
                        fm[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
                        current_list_key = None
                    elif val.lower() == "true":
                        fm[key] = True
                        current_list_key = None
                    elif val.lower() == "false":
                        fm[key] = False
                        current_list_key = None
                    else:
                        fm[key] = val
                        current_list_key = None
        return fm if isinstance(fm, dict) else None, None
    except Exception as e:
        return None, f"Parse error in {file_path}: {e}"


def detect_schema_type(frontmatter, schemas):
    """Determine which schema type applies based on tags."""
    tags = frontmatter.get("tags", [])
    if not isinstance(tags, list):
        tags = [tags] if tags else []

    matched_types = []
    for type_name, schema in schemas.items():
        required_tags = schema.get("required_tags", [])
        if all(t in tags for t in required_tags):
            matched_types.append((type_name, len(required_tags)))

    if not matched_types:
        return None

    # Return the most specific match (most required tags)
    matched_types.sort(key=lambda x: x[1], reverse=True)
    return matched_types[0][0]


def validate_note(file_path, frontmatter, schema_type, schema):
    """Validate a single note against its schema."""
    errors = []
    warnings = []

    # Check required tags
    tags = frontmatter.get("tags", [])
    if not isinstance(tags, list):
        tags = [tags] if tags else []

    for tag in schema.get("required_tags", []):
        if tag not in tags:
            errors.append(f"Missing required tag: {tag}")

    # Check required properties
    for prop in schema.get("required_properties", []):
        if prop not in frontmatter or frontmatter[prop] is None or frontmatter[prop] == "":
            errors.append(f"Missing or empty required property: {prop}")

    # Check property rules
    for prop, rules in schema.get("property_rules", {}).items():
        if prop in frontmatter and frontmatter[prop] is not None:
            value = frontmatter[prop]

            # Enum validation
            if "enum" in rules:
                valid_values = rules["enum"]
                if isinstance(value, list):
                    for v in value:
                        if v not in valid_values:
                            errors.append(
                                f"Invalid value '{v}' for {prop}. "
                                f"Valid: {valid_values}"
                            )
                elif value not in valid_values:
                    errors.append(
                        f"Invalid value '{value}' for {prop}. "
                        f"Valid: {valid_values}"
                    )

            # Type validation
            if "type" in rules:
                expected = rules["type"]
                if expected == "checkbox" and not isinstance(value, bool):
                    errors.append(f"Property {prop} must be boolean (checkbox)")
                elif expected == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Property {prop} must be a number")

    return {
        "file": str(file_path),
        "schema_type": schema_type,
        "errors": errors,
        "warnings": warnings,
        "valid": len(errors) == 0,
    }


def scan_vault(vault_path, schemas, target_type=None):
    """Scan all markdown files in the vault and validate against schemas."""
    results = []
    vault = Path(vault_path)

    # Directories to scan
    scan_dirs = [
        "memory", "journal", "contexts", "inbox", "archive",
        "_system/backlog"
    ]

    for scan_dir in scan_dirs:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue

        for md_file in dir_path.rglob("*.md"):
            # Skip index files
            if md_file.name == "_index.md":
                continue

            frontmatter, error = parse_frontmatter(md_file)

            if error:
                results.append({
                    "file": str(md_file.relative_to(vault)),
                    "schema_type": None,
                    "errors": [error],
                    "warnings": [],
                    "valid": False,
                })
                continue

            if frontmatter is None:
                continue  # No frontmatter, skip

            schema_type = detect_schema_type(frontmatter, schemas)
            if schema_type is None:
                continue  # Not a TARS-managed note

            if target_type and schema_type != target_type:
                continue

            result = validate_note(
                md_file.relative_to(vault), frontmatter, schema_type, schemas[schema_type]
            )
            results.append(result)

    return results


def validate_fixtures(vault_path, schemas):
    """Validate test fixture files."""
    fixtures_dir = Path(vault_path) / "tests" / "fixtures"
    if not fixtures_dir.exists():
        return []

    results = []
    for fixture_file in fixtures_dir.rglob("*.md"):
        frontmatter, error = parse_frontmatter(fixture_file)

        if error:
            results.append({
                "file": str(fixture_file.relative_to(Path(vault_path))),
                "errors": [error],
                "valid": False,
            })
            continue

        if frontmatter is None:
            continue

        schema_type = detect_schema_type(frontmatter, schemas)
        if schema_type is None:
            continue

        # Check if fixture name indicates expected validity
        expect_valid = "invalid" not in fixture_file.stem.lower()
        result = validate_note(
            fixture_file.relative_to(Path(vault_path)),
            frontmatter,
            schema_type,
            schemas[schema_type],
        )

        if expect_valid and not result["valid"]:
            result["warnings"].append(
                f"Valid fixture has validation errors: {result['errors']}"
            )
        elif not expect_valid and result["valid"]:
            result["warnings"].append(
                "Invalid fixture passes validation — update schema or fixture"
            )

        results.append(result)
    return results


def main():
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "."
    target_type = None

    for arg in sys.argv[2:]:
        if arg.startswith("--type="):
            target_type = arg.split("=", 1)[1]

    schemas, error = load_schemas(vault_path)
    if error:
        print(json.dumps({"error": error}))
        sys.exit(1)

    results = scan_vault(vault_path, schemas, target_type)
    fixture_results = validate_fixtures(vault_path, schemas)

    total = len(results)
    valid = sum(1 for r in results if r["valid"])
    invalid = total - valid

    output = {
        "timestamp": datetime.now().isoformat(),
        "vault_path": str(vault_path),
        "summary": {
            "total_notes_scanned": total,
            "valid": valid,
            "invalid": invalid,
        },
        "errors": [r for r in results if not r["valid"]],
        "fixture_results": fixture_results,
    }

    print(json.dumps(output, indent=2, default=str))
    sys.exit(0 if invalid == 0 else 1)


if __name__ == "__main__":
    main()
