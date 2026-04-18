"""Shared helpers for TARS hooks.

Stdlib-only. Imported by every hook script. Keep this surface minimal — hooks
must stay fast (sub-second) so heavy work belongs in detached subprocesses.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any


def read_event() -> dict[str, Any]:
    """Read a JSON event from stdin. Returns {} if stdin is empty/invalid."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def write_output(output: dict[str, Any]) -> None:
    """Write a JSON response to stdout."""
    json.dump(output, sys.stdout)


def vault_path() -> Path | None:
    """Return the vault path from env, or None."""
    value = os.environ.get("TARS_VAULT_PATH")
    return Path(value) if value else None


def in_recursion() -> bool:
    """True when running inside a hook-spawned subprocess."""
    return bool(os.environ.get("TARS_IN_HOOK"))


def log_stderr(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")


def append_telemetry(vault: Path, event: dict[str, Any]) -> None:
    """Append one JSONL event to ``_system/telemetry/YYYY-MM-DD.jsonl``.

    Mirrors ``tars_vault.telemetry.append_event`` so hook scripts (which can't
    always import the MCP package) have a stdlib-only path. Silently no-ops if
    ``TARS_DISABLE_TELEMETRY`` is set, or on any IO failure — telemetry must
    never take the session down.
    """
    if os.environ.get("TARS_DISABLE_TELEMETRY"):
        return
    try:
        from datetime import datetime
        day = datetime.now().astimezone().strftime("%Y-%m-%d")
        target = Path(vault) / "_system" / "telemetry" / f"{day}.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(event)
        payload.setdefault("ts", datetime.now().astimezone().isoformat(timespec="seconds"))
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except Exception:
        return
