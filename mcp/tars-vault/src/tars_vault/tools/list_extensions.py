"""list_extensions — Inventory workspace-installed TARS extensions."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import _common
from . import extension_common as ext


def list_extensions(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    if not vault:
        return _common.error("missing 'vault'")
    try:
        vault_p = _common.resolve_vault_path(vault)
    except ValueError as exc:
        return _common.error(str(exc))

    registry = ext.load_registry(vault_p)
    registered = ext.registry_entries(vault_p)
    scanned = ext.scan_extension_dirs(vault_p)
    items: list[dict[str, Any]] = []

    seen: set[str] = set()
    for extension_id, entry in sorted(registered.items()):
        if not isinstance(entry, dict):
            continue
        seen.add(extension_id)
        target = None
        path_error = None
        if entry.get("path"):
            target, path_error = ext.safe_workspace_relative_path(vault_p, str(entry.get("path")))
        manifest = ext.load_manifest(target) if target and target.is_dir() else {}
        _manifest, errors, warnings = (
            ext.validate_manifest(vault_p, target) if target and target.is_dir() else ({}, ["extension path is missing"], [])
        )
        if path_error:
            errors = [path_error]
        items.append(
            {
                "id": extension_id,
                "enabled": bool(entry.get("enabled", False)),
                "source": entry.get("source", "unknown"),
                "root": entry.get("root", "workspace"),
                "path": entry.get("path"),
                "version": manifest.get("version") or entry.get("installed_version"),
                "type": manifest.get("type"),
                "capabilities": manifest.get("capabilities", []),
                "valid": not errors,
                "errors": errors,
                "warnings": warnings,
                "registered": True,
            }
        )

    for extension_id, target in sorted(scanned.items()):
        if extension_id in seen:
            continue
        manifest, errors, warnings = ext.validate_manifest(vault_p, target)
        items.append(
            {
                "id": extension_id,
                "enabled": False,
                "source": "unregistered",
                "root": "workspace",
                "path": target.relative_to(vault_p).as_posix(),
                "version": manifest.get("version"),
                "type": manifest.get("type"),
                "capabilities": manifest.get("capabilities", []),
                "valid": not errors,
                "errors": errors,
                "warnings": warnings,
                "registered": False,
            }
        )

    return _common.ok(
        registry_version=registry.get("version"),
        extension_root=ext.EXTENSION_ROOT,
        registry=ext.REGISTRY_PATH,
        extensions=items,
    )

