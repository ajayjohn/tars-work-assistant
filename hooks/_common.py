"""Shared helpers for TARS hooks.

Stdlib-only. Imported by every hook script. Keep this surface minimal — hooks
must stay fast (sub-second) so heavy work belongs in detached subprocesses.
"""
import json
import os
import re
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


# ---------------------------------------------------------------------------
# Vault-path resolution (Phase 1, plan R2)
# ---------------------------------------------------------------------------

def _candidate_has_install(path: Path) -> bool:
    return (path / "_system" / "install.yaml").is_file()


def _candidate_has_config(path: Path) -> bool:
    return (path / "_system" / "config.md").is_file()


def _read_install_yaml(path: Path) -> dict[str, Any] | None:
    """Parse a flat install.yaml file. Stdlib-only mini parser.

    Supports `key: value` lines with string/bool scalars and `# comments`.
    Returns None if the file is missing or unreadable.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    out: dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$", line)
        if not m:
            continue
        key = m.group(1)
        value = m.group(2)
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if value.lower() in ("true", "yes"):
            out[key] = True
        elif value.lower() in ("false", "no"):
            out[key] = False
        elif value.lower() in ("null", "~", ""):
            out[key] = None if value else ""
        else:
            out[key] = value
    return out


def read_install_config(vault: Path | None = None) -> dict[str, Any] | None:
    """Return the parsed _system/install.yaml for ``vault`` (or the CWD)."""
    base = Path(vault) if vault else Path.cwd()
    target = base / "_system" / "install.yaml"
    if not target.is_file():
        return None
    return _read_install_yaml(target)


def install_mode(vault: Path | None = None) -> str:
    """Return the engagement mode ('casual' or 'standard').

    Defaults to 'standard' when install.yaml is missing or the field is unset.
    Anything other than the two known values normalizes to 'standard' — we
    never block on a typo.
    """
    config = read_install_config(vault)
    if not config:
        return "standard"
    value = str(config.get("mode") or "standard").strip().lower()
    return "casual" if value == "casual" else "standard"


def resolve_vault() -> tuple[Path | None, dict[str, Any]]:
    """Resolve the vault path with diagnostic status.

    Resolution order:
      1. ``TARS_VAULT_PATH`` env var (explicit override always wins).
      2. CWD if it contains ``_system/install.yaml``.
      3. CWD if it contains ``_system/config.md`` (legacy vault without
         install.yaml — works, but flagged so /welcome can offer to upgrade).
      4. install.yaml.vault_path on a previously known install if reachable.
      5. None.

    Returns (path_or_none, status). ``status`` includes:
      * ``source``: which step matched (env|cwd-install|cwd-config|install-file|none)
      * ``mismatch``: True if install.yaml.vault_path disagrees with CWD
      * ``install``: parsed install.yaml when one was located
    """
    status: dict[str, Any] = {"source": "none", "mismatch": False, "install": None}

    env_value = os.environ.get("TARS_VAULT_PATH")
    if env_value:
        env_path = Path(env_value).expanduser()
        status["source"] = "env"
        install = read_install_config(env_path)
        if install:
            status["install"] = install
            stored = install.get("vault_path")
            if stored and Path(str(stored)).expanduser().resolve() != env_path.resolve():
                status["mismatch"] = True
        return env_path, status

    cwd = Path.cwd()
    if _candidate_has_install(cwd):
        install = read_install_config(cwd)
        status["source"] = "cwd-install"
        status["install"] = install
        stored = install.get("vault_path") if install else None
        if stored:
            stored_path = Path(str(stored)).expanduser().resolve()
            if stored_path != cwd.resolve():
                status["mismatch"] = True
        return cwd, status

    if _candidate_has_config(cwd):
        status["source"] = "cwd-config"
        return cwd, status

    return None, status


def vault_path() -> Path | None:
    """Return the active vault path, or None.

    Backwards-compatible signature: callers that only need a path get one.
    Use ``resolve_vault()`` when diagnostics matter (e.g., SessionStart).
    """
    path, _status = resolve_vault()
    return path


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
