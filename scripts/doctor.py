#!/usr/bin/env python3
"""Fast runtime preflight for TARS workspaces.

Checks only deterministic local state: Python version, dependency imports,
workspace path resolution, basic write permission, and install-record
consistency. It does not create, move, or edit workspace files.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MCP_SRC = ROOT / "mcp" / "tars-vault" / "src"
RECOMMENDED_WORKSPACE = "~/Documents/TARS Workspace"


def _record(status: str, check: str, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": status, "check": check, "message": message}
    payload.update(extra)
    return payload


def _is_unexpanded(value: str) -> bool:
    return bool(re.search(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*", value))


def _parse_flat_yaml(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value.lower() in ("true", "yes"):
            out[key] = True
        elif value.lower() in ("false", "no"):
            out[key] = False
        elif value.lower() in ("null", "~"):
            out[key] = None
        else:
            out[key] = value
    return out


def _workspace_from_args(args: argparse.Namespace) -> tuple[Path | None, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    raw = args.workspace or os.environ.get("TARS_VAULT_PATH") or ""
    if raw and _is_unexpanded(raw):
        checks.append(_record("error", "workspace_path", f"Unexpanded workspace variable: {raw}"))
        return None, checks
    if raw:
        return Path(raw).expanduser(), checks
    cwd = Path.cwd()
    if (cwd / "_system" / "install.yaml").is_file() or (cwd / "_system" / "config.md").is_file():
        return cwd, checks
    checks.append(
        _record(
            "warning",
            "workspace_path",
            "No workspace path supplied. Use --workspace or TARS_VAULT_PATH.",
            recommended=RECOMMENDED_WORKSPACE,
        )
    )
    return None, checks


def _under_claude_home(path: Path) -> bool:
    try:
        home_claude = (Path.home() / ".claude").resolve()
        return path.expanduser().resolve().is_relative_to(home_claude)
    except Exception:
        return False


def run(args: argparse.Namespace) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    if sys.version_info >= (3, 10):
        checks.append(_record("ok", "python", f"Python {sys.version.split()[0]}"))
    else:
        checks.append(_record("error", "python", "Python 3.10+ is required", found=sys.version.split()[0]))

    sys.path.insert(0, str(MCP_SRC))
    for module in ("tars_vault.server", "mcp.server", "mcp.server.stdio", "fastembed", "sqlite_vec"):
        try:
            importlib.import_module(module)
            checks.append(_record("ok", f"import:{module}", "Import succeeded"))
        except Exception as exc:
            severity = "error" if module in ("tars_vault.server", "mcp.server", "mcp.server.stdio") else "warning"
            checks.append(_record(severity, f"import:{module}", f"Import failed: {exc}"))

    workspace, path_checks = _workspace_from_args(args)
    checks.extend(path_checks)

    if workspace is not None:
        expanded = workspace.expanduser()
        checks.append(_record("ok", "workspace_path", str(expanded), recommended=RECOMMENDED_WORKSPACE))
        install_path = expanded / "_system" / "install.yaml"

        if _under_claude_home(expanded) and not install_path.is_file():
            checks.append(
                _record(
                    "error",
                    "claude_home_workspace",
                    "Workspace resolves under ~/.claude without an existing install record. Use a transparent folder such as ~/Documents/TARS Workspace.",
                )
            )

        permission_target = expanded if expanded.exists() else expanded.parent
        if permission_target.exists() and os.access(permission_target, os.W_OK):
            checks.append(_record("ok", "write_permission", f"Writable: {permission_target}"))
        else:
            checks.append(_record("error", "write_permission", f"Not writable or missing: {permission_target}"))

        if install_path.is_file():
            install = _parse_flat_yaml(install_path)
            stored = install.get("workspace_path") or install.get("vault_path")
            if stored:
                try:
                    if Path(str(stored)).expanduser().resolve() == expanded.resolve():
                        checks.append(_record("ok", "install_record", "install.yaml matches workspace_path"))
                    else:
                        checks.append(
                            _record(
                                "error",
                                "install_record",
                                "install.yaml workspace_path does not match the active workspace",
                                stored=str(stored),
                                active=str(expanded),
                            )
                        )
                except OSError as exc:
                    checks.append(_record("error", "install_record", f"Could not resolve install path: {exc}"))
            else:
                checks.append(_record("warning", "install_record", "install.yaml exists but has no workspace_path"))
        else:
            checks.append(_record("warning", "install_record", "No _system/install.yaml found yet"))

    errors = [c for c in checks if c["status"] == "error"]
    warnings = [c for c in checks if c["status"] == "warning"]
    return {
        "status": "error" if errors else "ok",
        "errors": len(errors),
        "warnings": len(warnings),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fast TARS runtime preflight checks.")
    parser.add_argument("--workspace", help="Path to the TARS workspace. Defaults to TARS_VAULT_PATH or CWD.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    result = run(args)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for check in result["checks"]:
            label = check["status"].upper()
            print(f"{label:7} {check['check']}: {check['message']}")
        if result["status"] == "ok":
            print("\nTARS runtime preflight passed. The local TARS helper can be used.")
        else:
            print("\nTARS runtime preflight found blocking issues with the local TARS helper.")
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
