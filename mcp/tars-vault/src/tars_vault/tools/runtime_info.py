"""runtime_info — deterministic TARS local helper health check.

This tool is intentionally light: if it can be called, the TARS local helper is
connected. It reports required runtime state and optional search enhancements
without mutating the workspace.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any

from .. import _common


def _check_import(module: str, *, required: bool) -> dict[str, Any]:
    try:
        importlib.import_module(module)
        return {"check": f"import:{module}", "status": "ok", "message": "Import succeeded"}
    except Exception as exc:
        return {
            "check": f"import:{module}",
            "status": "error" if required else "warning",
            "message": f"Import failed: {exc}",
        }


def runtime_info(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    checks: list[dict[str, Any]] = []

    if sys.version_info >= (3, 10):
        checks.append({"check": "python", "status": "ok", "message": sys.version.split()[0]})
    else:
        checks.append({
            "check": "python",
            "status": "error",
            "message": f"Python 3.10+ required; found {sys.version.split()[0]}",
        })

    checks.append(_check_import("mcp.server", required=True))
    checks.append(_check_import("fastembed", required=False))
    checks.append(_check_import("sqlite_vec", required=False))

    if vault:
        workspace = _common.resolve_vault_path(vault)
        checks.append({"check": "workspace_path", "status": "ok", "message": str(workspace)})
        install_path = workspace / "_system" / "install.yaml"
        if install_path.is_file():
            checks.append({"check": "install_record", "status": "ok", "message": "_system/install.yaml found"})
        else:
            checks.append({"check": "install_record", "status": "warning", "message": "No _system/install.yaml found yet"})
        target = workspace if workspace.exists() else workspace.parent
        if target.exists() and os.access(target, os.W_OK):
            checks.append({"check": "write_permission", "status": "ok", "message": f"Writable: {target}"})
        else:
            checks.append({"check": "write_permission", "status": "error", "message": f"Not writable or missing: {target}"})
    else:
        checks.append({"check": "workspace_path", "status": "warning", "message": "No workspace path supplied"})

    errors = [c for c in checks if c["status"] == "error"]
    warnings = [c for c in checks if c["status"] == "warning"]
    return _common.ok(
        helper="connected",
        required_runtime="ok" if not errors else "error",
        optional_search="available" if not any(c["check"] in {"import:fastembed", "import:sqlite_vec"} and c["status"] != "ok" for c in checks) else "degraded",
        errors=len(errors),
        warnings=len(warnings),
        checks=checks,
    )
