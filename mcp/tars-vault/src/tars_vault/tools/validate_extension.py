"""validate_extension — Validate a workspace-installed TARS extension."""
from __future__ import annotations

from typing import Any

from .. import _common
from . import extension_common as ext


def validate_extension(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    extension_id = kwargs.get("extension_id") or kwargs.get("id")
    path = kwargs.get("path")
    if not vault:
        return _common.error("missing 'vault'")
    if not extension_id and not path:
        return _common.error("provide extension_id or path")
    vault_p = _common.resolve_vault_path(vault)

    target = None
    if extension_id:
        target = ext.registered_extension_dirs(vault_p).get(str(extension_id))
        if target is None:
            target = ext.scan_extension_dirs(vault_p).get(str(extension_id))
    if target is None and path:
        target, path_error = ext.safe_workspace_relative_path(vault_p, str(path))
        if path_error:
            return _common.error(path_error)
    if target is None:
        return _common.error("extension not found")

    manifest, errors, warnings = ext.validate_manifest(vault_p, target)
    return _common.ok(
        valid=not errors,
        id=manifest.get("id"),
        path=target.relative_to(vault_p).as_posix(),
        manifest=manifest,
        errors=errors,
        warnings=warnings,
    )

