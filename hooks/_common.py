"""Shared helpers for TARS hooks.

Stdlib-only. Imported by every hook script. Keep this surface minimal — hooks
must stay fast (sub-second) so heavy work belongs in detached subprocesses.
"""
import json
import os
import re
import sys
from fnmatch import fnmatch
from datetime import datetime, timezone
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
# Workspace-path resolution
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


def read_acknowledged_notices(vault: Path) -> dict[str, datetime]:
    target = Path(vault) / "_system" / "install.yaml"
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    notices: dict[str, datetime] = {}
    in_block = False
    for raw in text.splitlines():
        if re.match(r"^acknowledged_notices\s*:\s*$", raw):
            in_block = True
            continue
        if in_block and raw and not raw[0].isspace():
            break
        if not in_block:
            continue
        m = re.match(r"^\s+([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$", raw)
        if not m:
            continue
        value = m.group(2).strip().strip('"').strip("'")
        if not value:
            continue
        try:
            notices[m.group(1)] = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
    return notices


def is_notice_suppressed(vault: Path, notice_id: str, ttl_days: int = 7) -> bool:
    seen = read_acknowledged_notices(vault).get(notice_id)
    if not seen:
        return False
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - seen).days < ttl_days


def mark_notice_acknowledged(vault: Path, notice_id: str, when: datetime | None = None) -> None:
    target = Path(vault) / "_system" / "install.yaml"
    when = when or datetime.now(timezone.utc)
    stamp = when.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        text = target.read_text(encoding="utf-8") if target.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return
    lines = text.splitlines()
    out: list[str] = []
    in_block = False
    wrote = False
    found_block = False
    for raw in lines:
        if re.match(r"^acknowledged_notices\s*:\s*$", raw):
            found_block = True
            in_block = True
            out.append(raw)
            continue
        if in_block and raw and not raw[0].isspace():
            if not wrote:
                out.append(f"  {notice_id}: \"{stamp}\"")
                wrote = True
            in_block = False
        if in_block:
            m = re.match(r"^(\s+)([A-Za-z0-9_-]+)\s*:", raw)
            if m and m.group(2) == notice_id:
                out.append(f"{m.group(1)}{notice_id}: \"{stamp}\"")
                wrote = True
                continue
        out.append(raw)
    if in_block and not wrote:
        out.append(f"  {notice_id}: \"{stamp}\"")
    if not found_block:
        if out and out[-1].strip():
            out.append("")
        out.append("acknowledged_notices:")
        out.append(f"  {notice_id}: \"{stamp}\"")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(out) + "\n", encoding="utf-8")
    except OSError:
        return


def _is_unexpanded_var(value: str) -> bool:
    """Return True if value looks like an unexpanded shell variable.

    Claude Code's MCP runtime does not perform shell variable expansion, so a
    config entry like ``"TARS_VAULT_PATH": "${TARS_VAULT_PATH}"`` passes the
    literal string through.  Detect both ``${VAR}`` and ``$VAR`` forms.
    """
    return bool(re.search(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*", value))


def resolve_vault() -> tuple[Path | None, dict[str, Any]]:
    """Resolve the vault path with diagnostic status.

    Resolution order:
      1. ``TARS_VAULT_PATH`` env var (explicit override always wins).
         If the value contains an unexpanded shell variable (e.g. ``${TARS_VAULT_PATH}``),
         the env var is rejected and resolution continues to step 2 — the unexpanded
         literal would create a mis-named directory and silently misroute writes.
      2. CWD if it contains ``_system/install.yaml``.
      3. CWD if it contains ``_system/config.md`` (legacy vault without
         install.yaml — works, but flagged so /welcome can offer to upgrade).
      4. install.yaml.workspace_path / vault_path on a previously known install if reachable.
      5. None.

    Returns (path_or_none, status). ``status`` includes:
      * ``source``: which step matched (env|cwd-install|cwd-config|install-file|none)
      * ``mismatch``: True if install.yaml.vault_path disagrees with CWD
      * ``install``: parsed install.yaml when one was located
      * ``unexpanded_env``: True when TARS_VAULT_PATH contained an unexpanded variable
    """
    status: dict[str, Any] = {
        "source": "none",
        "mismatch": False,
        "install": None,
        "unexpanded_env": False,
    }

    env_value = os.environ.get("TARS_VAULT_PATH")
    if env_value:
        if _is_unexpanded_var(env_value):
            # Record the problem but do NOT use this value — fall through to CWD.
            status["unexpanded_env"] = True
            status["raw_env_value"] = env_value
        else:
            env_path = Path(env_value).expanduser()
            status["source"] = "env"
            install = read_install_config(env_path)
            if install:
                status["install"] = install
                stored = install.get("workspace_path") or install.get("vault_path")
                if stored and Path(str(stored)).expanduser().resolve() != env_path.resolve():
                    status["mismatch"] = True
            return env_path, status

    cwd = Path.cwd()
    if _candidate_has_install(cwd):
        install = read_install_config(cwd)
        status["source"] = "cwd-install"
        status["install"] = install
        stored = (install.get("workspace_path") or install.get("vault_path")) if install else None
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


# ---------------------------------------------------------------------------
# Extension runtime state and policy helpers
# ---------------------------------------------------------------------------

EXTENSION_RUNTIME = "_system/extension-runtime.json"


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    lowered = value.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"null", "~", "none"}:
        return None
    return value


def _parse_yaml_mapping(lines: list[str], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    i = index
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        current = len(raw) - len(raw.lstrip(" "))
        if current < indent:
            break
        if current > indent:
            i += 1
            continue
        match = re.match(r"^\s*([^:\s][^:]*):\s*(.*?)\s*$", raw)
        if not match:
            i += 1
            continue
        key = match.group(1).strip()
        inline = match.group(2).strip()
        if inline:
            result[key] = _parse_scalar(inline)
            i += 1
            continue
        next_i = _next_yaml_content(lines, i + 1)
        if next_i is None:
            result[key] = {}
            i += 1
            continue
        next_raw = lines[next_i]
        next_indent = len(next_raw) - len(next_raw.lstrip(" "))
        if next_indent <= current:
            result[key] = {}
            i += 1
            continue
        if next_raw.lstrip().startswith("- "):
            result[key], i = _parse_yaml_list(lines, next_i, next_indent)
        else:
            result[key], i = _parse_yaml_mapping(lines, next_i, next_indent)
    return result, i


def _parse_yaml_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    i = index
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        current = len(raw) - len(raw.lstrip(" "))
        if current < indent:
            break
        if current > indent:
            i += 1
            continue
        match = re.match(r"^\s*-\s*(.*?)\s*$", raw)
        if not match:
            break
        result.append(_parse_scalar(match.group(1)))
        i += 1
    return result, i


def _next_yaml_content(lines: list[str], index: int) -> int | None:
    for i in range(index, len(lines)):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            return i
    return None


def read_yaml_subset(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    parsed, _ = _parse_yaml_mapping(text.splitlines(), 0, 0)
    return parsed


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if value in (None, ""):
        return []
    return [str(value)]


def load_extension_runtime(vault: Path) -> dict[str, Any]:
    target = Path(vault) / EXTENSION_RUNTIME
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_extension_runtime(vault: Path, state: dict[str, Any]) -> None:
    target = Path(vault) / EXTENSION_RUNTIME
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        return


def _session_state(state: dict[str, Any], session_id: str) -> dict[str, Any]:
    sessions = state.setdefault("sessions", {})
    if not isinstance(sessions, dict):
        state["sessions"] = sessions = {}
    session = sessions.setdefault(session_id or "unknown", {})
    if not isinstance(session, dict):
        sessions[session_id or "unknown"] = session = {}
    return session


def record_skill_loaded(vault: Path, session_id: str, skill: str) -> None:
    state = load_extension_runtime(vault)
    session = _session_state(state, session_id)
    session["last_skill"] = skill
    session["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_extension_runtime(vault, state)


def record_extension_loaded(vault: Path, session_id: str, extension_id: str) -> None:
    state = load_extension_runtime(vault)
    session = _session_state(state, session_id)
    loaded = session.setdefault("loaded_extensions", {})
    if not isinstance(loaded, dict):
        session["loaded_extensions"] = loaded = {}
    loaded[extension_id] = datetime.now(timezone.utc).isoformat()
    session["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_extension_runtime(vault, state)


def extension_loaded(vault: Path, session_id: str, extension_id: str) -> bool:
    session = (load_extension_runtime(vault).get("sessions") or {}).get(session_id or "unknown") or {}
    loaded = session.get("loaded_extensions") or {}
    return isinstance(loaded, dict) and extension_id in loaded


def last_loaded_skill(vault: Path, session_id: str) -> str:
    session = (load_extension_runtime(vault).get("sessions") or {}).get(session_id or "unknown") or {}
    return str(session.get("last_skill") or "")


def enabled_extension_policies(vault: Path) -> list[dict[str, Any]]:
    registry = read_yaml_subset(Path(vault) / "_system" / "extensions.yaml")
    entries = registry.get("extensions") if isinstance(registry.get("extensions"), dict) else {}
    policies: list[dict[str, Any]] = []
    for extension_id, entry in sorted(entries.items()):
        if not isinstance(entry, dict) or not entry.get("enabled", False):
            continue
        rel = str(entry.get("path") or "")
        if not rel or Path(rel).is_absolute() or not rel.replace("\\", "/").startswith("extensions/"):
            continue
        ext_dir = (Path(vault) / rel).resolve()
        try:
            ext_dir.relative_to((Path(vault) / "extensions").resolve())
        except ValueError:
            continue
        manifest = read_yaml_subset(ext_dir / "extension.yaml")
        owns = manifest.get("owns") if isinstance(manifest.get("owns"), dict) else {}
        provider = manifest.get("provider") if isinstance(manifest.get("provider"), dict) else {}
        detection = provider.get("detection") if isinstance(provider.get("detection"), dict) else {}
        applies_to = manifest.get("applies_to") if isinstance(manifest.get("applies_to"), dict) else {}
        provider_tools = _list(owns.get("provider_tools"))
        provider_tools.extend(_list(detection.get("tool_name_patterns")))
        if not provider_tools:
            continue
        policies.append(
            {
                "extension_id": str(extension_id),
                "name": str(manifest.get("name") or extension_id),
                "provider_tools": provider_tools,
                "enforcement": str(owns.get("enforcement") or "advisory"),
                "applies_to_skills": _list(applies_to.get("skills")),
                "tool_contract": (manifest.get("entrypoints") or {}).get("tool_contract", "")
                if isinstance(manifest.get("entrypoints"), dict)
                else "",
            }
        )
    return policies


def provider_tool_matches(pattern: str, tool_name: str) -> bool:
    if fnmatch(tool_name, pattern):
        return True
    try:
        return bool(re.search(pattern, tool_name, re.IGNORECASE))
    except re.error:
        return pattern.lower() in tool_name.lower()


def normalized_tool_name(tool_name: str) -> str:
    return str(tool_name or "").strip().lower().replace("-", "_")


def tool_action(tool_name: str) -> str:
    normalized = normalized_tool_name(tool_name)
    if "__" in normalized:
        return normalized.rsplit("__", 1)[-1]
    return normalized.rsplit(".", 1)[-1]


def is_tars_vault_tool(tool_name: str) -> bool:
    normalized = normalized_tool_name(tool_name)
    if not normalized.startswith("mcp__"):
        return False
    parts = [part for part in normalized.split("__")[1:] if part]
    return any("tars" in part for part in parts) and any("vault" in part for part in parts)


def is_tars_vault_action(tool_name: str, action: str) -> bool:
    return is_tars_vault_tool(tool_name) and tool_action(tool_name) == normalized_tool_name(action)
