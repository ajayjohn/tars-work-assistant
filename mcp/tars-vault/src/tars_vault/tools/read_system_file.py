"""read_system_file — Read a managed system file with structured YAML parsing."""
from __future__ import annotations

from typing import Any

from .. import _common


ALLOWED_SUFFIXES = {".md", ".yaml", ".yml"}


def read_system_file(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    file_ = kwargs.get("file") or kwargs.get("path")
    if not vault:
        return _common.error("missing 'vault' path")
    if not file_:
        return _common.error("missing 'file' argument")
    try:
        vault_p = _common.resolve_vault_path(vault)
        raw = str(file_).lstrip("/")
        if raw.startswith("_system/"):
            raw = raw[len("_system/"):]
        target = (vault_p / "_system" / raw).resolve()
        target.relative_to(vault_p / "_system")
    except ValueError:
        return _common.error(f"path escapes system folder: {file_}")
    if target.suffix not in ALLOWED_SUFFIXES:
        return _common.error("unsupported system file type")
    if not target.is_file():
        return _common.error(f"system file not found: {raw}")
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return _common.error(f"read failed: {exc}")
    rel = str(target.relative_to(vault_p)).replace("\\", "/")
    if target.suffix in {".yaml", ".yml"}:
        return _common.ok(path=rel, data=_common.parse_simple_yaml(text), raw=text)
    payload = _common.note_payload(text)
    return _common.ok(path=rel, **payload)
