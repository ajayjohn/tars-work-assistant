"""archive_candidates — Review-gated lifecycle archival dry-run."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .. import _common


ROOT = Path(__file__).resolve().parents[5]
VALID_CHECKS = {"all", "memory", "workflows", "inbox"}


def archive_candidates(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    if not vault:
        return _common.error("missing 'vault'")
    check = str(kwargs.get("check") or "all")
    if check not in VALID_CHECKS:
        return _common.error("check must be one of: all, memory, workflows, inbox")
    try:
        active_limit = max(1, int(kwargs.get("active_limit", 2000)))
    except (TypeError, ValueError):
        active_limit = 2000

    vault_p = _common.resolve_vault_path(vault)
    script = ROOT / "scripts" / "archive.py"
    if not script.is_file():
        return _common.error("archive.py not found")

    result = subprocess.run(
        [sys.executable, str(script), "--vault", str(vault_p), "--json", "--check", check],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        return _common.error(result.stderr.strip() or "archive candidate scan failed")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return _common.error(f"archive candidate scan returned invalid JSON: {exc}")

    active_count = sum(
        1
        for path in vault_p.rglob("*.md")
        if not str(path.relative_to(vault_p)).replace("\\", "/").startswith(("_system/", "archive/"))
    )
    payload["active_file_count"] = active_count
    payload["active_limit"] = active_limit
    payload["over_active_limit"] = active_count > active_limit
    return _common.ok(**payload)
