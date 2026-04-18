"""refresh_integrations — Rebuild _system/tools-registry.yaml from .mcp.json.

Delegates to scripts/discover-mcp-tools.py (v3.1.1 implementation). Invoked
on SessionStart (via hook) or explicitly via /tars:maintain refresh-integrations.

Arguments:
  vault: required.
  dry_run: optional bool (default false) — emit proposed yaml without writing.

Returns:
  {status: ok, registry_path, server_count}
  {status: error, reason}
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .. import _common


def refresh_integrations(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    dry_run = bool(kwargs.get("dry_run", False))
    if not vault:
        return _common.error("missing 'vault'")
    try:
        vault_p = _common.resolve_vault_path(vault)
    except ValueError as exc:
        return _common.error(str(exc))

    # Locate the repo (script location relative to this package).
    here = Path(__file__).resolve()
    repo_root = here.parents[5]   # tools/refresh_integrations.py → tars_vault → src → tars-vault → mcp → repo
    script = repo_root / "scripts" / "discover-mcp-tools.py"
    if not script.is_file():
        return _common.error(f"discover-mcp-tools.py not found at {script}")

    args = [sys.executable, str(script), "--vault", str(vault_p), "--json"]
    if dry_run:
        args.append("--dry-run")
    else:
        args.append("--apply")

    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=120
        )
    except subprocess.TimeoutExpired:
        return _common.error("discover-mcp-tools.py timed out after 120s")
    except OSError as exc:
        return _common.error(f"failed to invoke discover-mcp-tools.py: {exc}")

    if result.returncode != 0:
        return _common.error(
            f"discover-mcp-tools.py exited {result.returncode}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )

    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return _common.error(
            f"discover-mcp-tools.py produced non-JSON output: "
            f"{result.stdout.strip()[:400]}"
        )

    return _common.ok(
        registry_path=payload.get("registry_path")
        or str(vault_p / "_system" / "tools-registry.yaml"),
        server_count=payload.get("server_count", 0),
        dry_run=dry_run,
        raw=payload,
    )
