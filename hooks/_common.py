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
