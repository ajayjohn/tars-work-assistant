"""Frontmatter / schema / content validators."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .sanitize import find_bad_wikilinks


TARS_PREFIX = "tars-"


def is_tars_managed_property(name: str) -> bool:
    """Return True if ``name`` is a tars-managed frontmatter key."""
    return name.startswith(TARS_PREFIX)


def validate_frontmatter_shape(frontmatter: dict[str, Any]) -> list[str]:
    """Return a list of human-readable errors; empty list means OK."""
    errors: list[str] = []
    if not isinstance(frontmatter, dict):
        errors.append("frontmatter must be a mapping")
    return errors


def validate_no_bad_wikilinks(content: str) -> list[str]:
    """Return error messages for any wikilink with smart quotes / illegal chars.

    Pure: takes text, returns one human-readable message per offender. Empty
    list means the content is clean. The pre-tool-use hook calls the same
    helper for defense-in-depth.
    """
    if not isinstance(content, str) or not content:
        return []
    findings = find_bad_wikilinks(content)
    if not findings:
        return []
    out: list[str] = []
    for item in findings:
        raw = item.get("raw", "")
        issue = item.get("issue", "")
        if issue == "smart_quote":
            out.append(
                f"wikilink [[{raw}]] contains smart quotes — normalize to straight "
                "quotes (use mcp__tars_vault__format_wikilink)"
            )
        elif issue == "illegal_char":
            out.append(
                f"wikilink [[{raw}]] contains characters Obsidian forbids in "
                'filenames (\\ / : * ? " < > |) — sanitize the basename'
            )
        elif issue == "empty":
            out.append(f"wikilink [[{raw}]] has an empty target")
        else:
            out.append(f"wikilink [[{raw}]] failed validation ({issue})")
    return out


_SCHEMA_CACHE: dict[Path, tuple[float, dict[str, Any]]] = {}


def load_schemas(vault: str | Path) -> dict[str, Any]:
    """Load _system/schemas.yaml with a small schema-specific parser."""
    path = Path(vault) / "_system" / "schemas.yaml"
    if not path.is_file():
        return {}
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {}
    cached = _SCHEMA_CACHE.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        schemas = _parse_schemas_yaml(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}
    _SCHEMA_CACHE[path] = (mtime, schemas)
    return schemas


def _parse_flow_list(value: str) -> list[Any]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return [value.strip('"').strip("'")] if value else []
    inner = value[1:-1].strip()
    if not inner:
        return []
    out: list[Any] = []
    for raw in inner.split(","):
        item = raw.strip().strip('"').strip("'")
        if item.isdigit():
            out.append(int(item))
        else:
            out.append(item)
    return out


def _parse_schemas_yaml(text: str) -> dict[str, Any]:
    schemas: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    current_name: str | None = None
    list_key: str | None = None
    in_rules = False
    rule_name: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0 and stripped.endswith(":"):
            current_name = stripped[:-1]
            current = {}
            schemas[current_name] = current
            list_key = None
            in_rules = False
            rule_name = None
            continue
        if current is None:
            continue
        if indent == 2:
            in_rules = False
            rule_name = None
            if stripped.startswith("required_tags:"):
                current["required_tags"] = _parse_flow_list(stripped.split(":", 1)[1])
                list_key = None
            elif stripped in {"required_properties:", "optional_properties:"}:
                list_key = stripped[:-1]
                current[list_key] = []
            elif stripped == "property_rules:":
                current["property_rules"] = {}
                list_key = None
                in_rules = True
            else:
                list_key = None
            continue
        if indent == 4 and list_key and stripped.startswith("- "):
            current[list_key].append(stripped[2:].split("#", 1)[0].strip())
            continue
        if indent == 4 and "property_rules" in current and stripped.endswith(":"):
            in_rules = True
            rule_name = stripped[:-1]
            current["property_rules"].setdefault(rule_name, {})
            continue
        if indent == 6 and in_rules and rule_name and ":" in stripped:
            key, _, value = stripped.partition(":")
            value = value.strip()
            current["property_rules"][rule_name][key.strip()] = (
                _parse_flow_list(value) if value.startswith("[") else value.strip('"').strip("'")
            )
    return schemas


def _tags_from_frontmatter(frontmatter: dict[str, Any]) -> list[str]:
    tags = frontmatter.get("tags") or []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, list):
        return [str(t) for t in tags]
    return []


def _infer_schema(tags: list[str], schemas: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    tag_set = set(tags)
    best_name: str | None = None
    best_schema: dict[str, Any] | None = None
    best_score = -1
    for name, schema in schemas.items():
        if not isinstance(schema, dict):
            continue
        required_tags = schema.get("required_tags") or []
        if isinstance(required_tags, str):
            required_tags = [required_tags]
        required_set = {str(t) for t in required_tags}
        if required_set and required_set.issubset(tag_set) and len(required_set) > best_score:
            best_name = str(name)
            best_schema = schema
            best_score = len(required_set)
    if best_schema:
        return best_name, best_schema
    for tag in tags:
        if not tag.startswith("tars/"):
            continue
        candidate = tag.split("/", 1)[1]
        schema = schemas.get(candidate)
        if isinstance(schema, dict):
            return candidate, schema
    return None, None


def validate_against_schema(frontmatter: dict[str, Any], schemas: dict[str, Any]) -> list[str]:
    """Validate create-time frontmatter against the inferred TARS schema.

    Per PRD-07: when no `tars/<type>` tag is present, validation is best-effort
    and returns no errors — freeform notes (used by `write_note_from_content`
    for genuinely templateless content) are intentionally schema-agnostic.
    Once an entity type is inferable, all schema rules apply.
    """
    if not isinstance(frontmatter, dict):
        return ["frontmatter must be a mapping"]
    tags = _tags_from_frontmatter(frontmatter)
    if not tags:
        return []
    _name, schema = _infer_schema(tags, schemas)
    if not schema:
        return []

    errors: list[str] = []
    required_tags = schema.get("required_tags") or []
    if isinstance(required_tags, str):
        required_tags = [required_tags]
    for tag in required_tags:
        if str(tag) not in tags:
            errors.append(f"missing required tag: {tag}")

    required_props = schema.get("required_properties") or []
    if isinstance(required_props, str):
        required_props = [required_props]
    for prop in required_props:
        if prop not in frontmatter or frontmatter.get(prop) in (None, ""):
            errors.append(f"missing required property: {prop}")

    rules = schema.get("property_rules") or {}
    if isinstance(rules, dict):
        for prop, rule in rules.items():
            if prop not in frontmatter or not isinstance(rule, dict):
                continue
            allowed = rule.get("enum")
            if allowed is not None and frontmatter.get(prop) not in allowed:
                errors.append(
                    f"property {prop!r} value {frontmatter.get(prop)!r} is not in allowed set {allowed}"
                )
    return errors
