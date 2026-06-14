"""Shared helpers for workspace-installed TARS extensions.

Extensions are always loaded from ``<workspace>/extensions``. The plugin root is
not an extension runtime location; catalog extensions must be installed into the
workspace before use.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from .. import _common


EXTENSION_SCHEMA_VERSION = "1"
EXTENSION_ROOT = "extensions"
REGISTRY_PATH = "_system/extensions.yaml"
ALLOWED_TYPES = {
    "provider-adapter",
    "workflow",
    "template-pack",
    "retrieval-pack",
    "validation-pack",
}


def extension_root(vault: Path) -> Path:
    return (vault / EXTENSION_ROOT).resolve()


def registry_path(vault: Path) -> Path:
    return (vault / REGISTRY_PATH).resolve()


def parse_yaml_subset(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    parsed, _ = _parse_mapping(lines, 0, 0)
    return parsed


def _parse_mapping(lines: list[str], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    i = index
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        current_indent = len(raw) - len(raw.lstrip(" "))
        if current_indent < indent:
            break
        if current_indent > indent:
            i += 1
            continue
        match = re.match(r"^\s*([^:\s][^:]*):\s*(.*?)\s*$", raw)
        if not match:
            i += 1
            continue
        key = match.group(1).strip()
        inline = match.group(2).strip()
        if inline:
            result[key] = _parse_scalar_or_flow(inline)
            i += 1
            continue

        next_i = _next_content_index(lines, i + 1)
        if next_i is None:
            result[key] = {}
            i += 1
            continue
        next_raw = lines[next_i]
        next_indent = len(next_raw) - len(next_raw.lstrip(" "))
        if next_indent <= current_indent:
            result[key] = {}
            i += 1
            continue
        if next_raw.lstrip().startswith("- "):
            result[key], i = _parse_list(lines, next_i, next_indent)
        else:
            result[key], i = _parse_mapping(lines, next_i, next_indent)
    return result, i


def _parse_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    i = index
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        current_indent = len(raw) - len(raw.lstrip(" "))
        if current_indent < indent:
            break
        if current_indent > indent:
            i += 1
            continue
        match = re.match(r"^\s*-\s*(.*?)\s*$", raw)
        if not match:
            break
        result.append(_parse_scalar_or_flow(match.group(1).strip()))
        i += 1
    return result, i


def _next_content_index(lines: list[str], index: int) -> int | None:
    for i in range(index, len(lines)):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            return i
    return None


def _parse_scalar_or_flow(value: str) -> Any:
    if value == "":
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in _split_commas(inner)]
    return _parse_scalar(value)


def _parse_scalar(value: str) -> Any:
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"null", "~", "none"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _split_commas(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for ch in value:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            current.append(ch)
            continue
        if ch == ",":
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return parts


def dump_yaml(data: dict[str, Any]) -> str:
    return _dump_mapping(data, 0)


def _dump_mapping(data: dict[str, Any], indent: int) -> str:
    lines: list[str] = []
    pad = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            lines.append(_dump_mapping(value, indent + 2).rstrip())
        elif isinstance(value, list):
            if not value:
                lines.append(f"{pad}{key}: []")
            else:
                lines.append(f"{pad}{key}:")
                for item in value:
                    lines.append(f"{pad}  - {_dump_scalar(item)}")
        else:
            lines.append(f"{pad}{key}: {_dump_scalar(value)}")
    return "\n".join(lines) + "\n"


def _dump_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if not text or text != text.strip() or re.search(r"[:#\n{}\[\],]", text):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def load_yaml_file(path: Path) -> dict[str, Any]:
    try:
        return parse_yaml_subset(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def default_registry() -> dict[str, Any]:
    return {"version": EXTENSION_SCHEMA_VERSION, "extensions": {}}


def load_registry(vault: Path) -> dict[str, Any]:
    path = registry_path(vault)
    if not path.is_file():
        return default_registry()
    data = load_yaml_file(path)
    if not isinstance(data.get("extensions"), dict):
        data["extensions"] = {}
    if not data.get("version"):
        data["version"] = EXTENSION_SCHEMA_VERSION
    return data


def write_registry(vault: Path, registry: dict[str, Any]) -> None:
    registry.setdefault("version", EXTENSION_SCHEMA_VERSION)
    registry.setdefault("extensions", {})
    _common.write_note_text(registry_path(vault), dump_yaml(registry), backup=True)


def safe_workspace_relative_path(vault: Path, relpath: str) -> tuple[Path | None, str | None]:
    raw = Path(str(relpath))
    if raw.is_absolute():
        return None, "extension path must be workspace-relative"
    if raw.parts and raw.parts[0] != EXTENSION_ROOT:
        return None, "extension path must live under extensions/"
    target = (vault / raw).resolve()
    try:
        target.relative_to(extension_root(vault))
    except ValueError:
        return None, "extension path escapes workspace extensions/"
    return target, None


def extension_dir_from_id(vault: Path, extension_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", extension_id).strip(".-") or "extension"
    return (extension_root(vault) / safe).resolve()


def load_manifest(ext_dir: Path) -> dict[str, Any]:
    manifest_path = ext_dir / "extension.yaml"
    manifest = load_yaml_file(manifest_path)
    if "entrypoints" not in manifest:
        entrypoints: dict[str, Any] = {}
        if manifest.get("instructions"):
            entrypoints["instructions"] = manifest.get("instructions")
        if manifest.get("tool_contract"):
            entrypoints["tool_contract"] = manifest.get("tool_contract")
        if manifest.get("review_schema"):
            entrypoints["review_schema"] = manifest.get("review_schema")
        if entrypoints:
            manifest["entrypoints"] = entrypoints
    return manifest


def validate_manifest(vault: Path, ext_dir: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        ext_dir.relative_to(extension_root(vault))
    except ValueError:
        errors.append("extension directory must be under workspace extensions/")
    manifest_path = ext_dir / "extension.yaml"
    if not manifest_path.is_file():
        return {}, ["missing extension.yaml"], warnings
    manifest = load_manifest(ext_dir)
    for field in (
        "id",
        "name",
        "version",
        "tars_extension_version",
        "type",
        "capabilities",
        "applies_to",
        "entrypoints",
        "safety",
    ):
        if field not in manifest:
            errors.append(f"missing required field: {field}")
    if str(manifest.get("tars_extension_version")) != EXTENSION_SCHEMA_VERSION:
        errors.append("unsupported tars_extension_version")
    ext_type = manifest.get("type")
    if ext_type and ext_type not in ALLOWED_TYPES:
        errors.append(f"unsupported extension type: {ext_type}")
    if not isinstance(manifest.get("capabilities"), list):
        errors.append("capabilities must be a list")
    applies_to = manifest.get("applies_to")
    if not isinstance(applies_to, dict):
        errors.append("applies_to must be a mapping")
    entrypoints = manifest.get("entrypoints")
    instructions = entrypoints.get("instructions") if isinstance(entrypoints, dict) else None
    if not instructions:
        errors.append("entrypoints.instructions is required")
    elif _safe_entrypoint(ext_dir, str(instructions)) is None:
        errors.append("entrypoints.instructions escapes extension directory")
    elif not _safe_entrypoint(ext_dir, str(instructions)).is_file():
        errors.append("entrypoints.instructions file is missing")
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        errors.append("safety must be a mapping")
    elif safety.get("requires_review") is not True:
        errors.append("safety.requires_review must be true")
    for key in ("may_write_workspace", "may_mutate_external_provider"):
        if isinstance(safety, dict) and safety.get(key) is True:
            warnings.append(f"{key}=true requires parent skill approval at runtime")
    return manifest, errors, warnings


def _safe_entrypoint(ext_dir: Path, relpath: str) -> Path | None:
    raw = Path(relpath)
    if raw.is_absolute():
        return None
    target = (ext_dir / raw).resolve()
    try:
        target.relative_to(ext_dir.resolve())
    except ValueError:
        return None
    return target


def registry_entries(vault: Path) -> dict[str, dict[str, Any]]:
    registry = load_registry(vault)
    entries = registry.get("extensions", {})
    return entries if isinstance(entries, dict) else {}


def registered_extension_dirs(vault: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for extension_id, entry in registry_entries(vault).items():
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not path:
            continue
        target, error = safe_workspace_relative_path(vault, str(path))
        if error or target is None:
            continue
        out[str(extension_id)] = target
    return out


def scan_extension_dirs(vault: Path) -> dict[str, Path]:
    root = extension_root(vault)
    out: dict[str, Path] = {}
    if not root.is_dir():
        return out
    for manifest_path in root.rglob("extension.yaml"):
        ext_dir = manifest_path.parent.resolve()
        try:
            ext_dir.relative_to(root)
        except ValueError:
            continue
        manifest = load_manifest(ext_dir)
        extension_id = str(manifest.get("id") or "")
        if extension_id:
            out[extension_id] = ext_dir
    return out


def read_entrypoint(vault: Path, extension_id: str, file: str | None = None) -> tuple[dict[str, Any], Path | None, str | None]:
    ext_dir = registered_extension_dirs(vault).get(extension_id)
    if ext_dir is None:
        return {}, None, "extension is not registered"
    manifest, errors, _warnings = validate_manifest(vault, ext_dir)
    if errors:
        return manifest, None, "; ".join(errors)
    entrypoints = manifest.get("entrypoints") if isinstance(manifest.get("entrypoints"), dict) else {}
    rel = file or entrypoints.get("instructions")
    if not rel:
        return manifest, None, "no file requested and extension has no instructions entrypoint"
    target = _safe_entrypoint(ext_dir, str(rel))
    if target is None:
        return manifest, None, "requested extension file escapes extension directory"
    if not target.is_file():
        return manifest, None, "requested extension file is missing"
    return manifest, target, None


def install_from_source(vault: Path, source: Path, enable: bool, source_label: str) -> tuple[dict[str, Any], list[str], list[str]]:
    if not source.is_dir():
        return {}, ["source_path must be an extension directory"], []
    source_manifest = load_manifest(source)
    extension_id = str(source_manifest.get("id") or "").strip()
    if not extension_id:
        return {}, ["source extension.yaml is missing id"], []
    target = extension_dir_from_id(vault, extension_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    manifest, errors, warnings = validate_manifest(vault, target)
    if errors:
        shutil.rmtree(target, ignore_errors=True)
        return manifest, errors, warnings
    registry = load_registry(vault)
    entries = registry.setdefault("extensions", {})
    rel = target.relative_to(vault).as_posix()
    entries[extension_id] = {
        "enabled": bool(enable),
        "source": source_label,
        "root": "workspace",
        "path": rel,
        "installed_version": str(manifest.get("version") or ""),
    }
    write_registry(vault, registry)
    return manifest, errors, warnings


def match_extension(manifest: dict[str, Any], *, skill: str | None, mode: str | None, capability: str | None, provider: str | None, tool_names: list[str]) -> tuple[bool, int, list[str]]:
    reasons: list[str] = []
    score = 0
    if capability:
        capabilities = [str(c) for c in manifest.get("capabilities", []) if c]
        if capability not in capabilities:
            return False, 0, []
        score += 40
        reasons.append(f"capability:{capability}")
    applies_to = manifest.get("applies_to") if isinstance(manifest.get("applies_to"), dict) else {}
    if skill:
        skills = [str(s) for s in applies_to.get("skills", [])] if isinstance(applies_to.get("skills"), list) else []
        if skills and skill not in skills:
            return False, 0, []
        if skills:
            score += 20
            reasons.append(f"skill:{skill}")
    if mode:
        modes = [str(m) for m in applies_to.get("modes", [])] if isinstance(applies_to.get("modes"), list) else []
        if modes and mode not in modes:
            return False, 0, []
        if modes:
            score += 10
            reasons.append(f"mode:{mode}")
    provider_meta = manifest.get("provider") if isinstance(manifest.get("provider"), dict) else {}
    if provider:
        declared = str(provider_meta.get("name") or "")
        if declared and declared.lower() != provider.lower():
            return False, 0, []
        if declared:
            score += 20
            reasons.append(f"provider:{provider}")
    detection = provider_meta.get("detection") if isinstance(provider_meta.get("detection"), dict) else {}
    patterns = detection.get("tool_name_patterns") if isinstance(detection, dict) else []
    if patterns and tool_names:
        haystack = "\n".join(tool_names)
        matched = [str(p) for p in patterns if re.search(str(p), haystack, re.IGNORECASE)]
        if matched:
            score += min(10, len(matched) * 3)
            reasons.append("tool-pattern")
    return True, score, reasons
