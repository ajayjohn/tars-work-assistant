#!/usr/bin/env python3
"""SessionStart hook. Observability-only — never exits non-zero.

Phase 4 banner composition:

  1. install.yaml mismatch warning (Phase 1).
  2. Legacy-vault notice when install.yaml is missing (Phase 1).
  3. tools-registry.yaml stale or missing (TTL = 24h). Skills should call
     `mcp__tars_vault__refresh_integrations` to repopulate; the hook only
     surfaces the notice — it cannot call MCP tools itself.
  4. Cron-job health: any job in `_system/housekeeping-state.yaml` with
     `id: null` or `status != registered` surfaces as a notice. Re-
     registration runs in the user's session via /welcome step 7 logic
     (we cannot register cron jobs from a stdlib hook).
"""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import in_recursion, read_event, resolve_vault, write_output


_REGISTRY_TTL_SECONDS = 24 * 60 * 60  # 24h per CLAUDE.md startup-checks §6


def _vault_notice(status: dict) -> str:
    if status.get("mismatch"):
        install = status.get("install") or {}
        stored = install.get("vault_path") or "(unset)"
        return (
            "TARS install warning: this folder does not match the vault recorded in "
            "_system/install.yaml.\n"
            f"  Recorded vault_path: {stored}\n"
            "  If you moved or copied the vault, run /welcome --relocate to update "
            "the install record. Until then, writes are discouraged from this folder."
        )
    if status.get("source") == "cwd-config":
        return (
            "TARS notice: this vault has no _system/install.yaml. Run /welcome to "
            "create one — until then, vault-move detection is disabled."
        )
    return ""


def _registry_notice(vault: Path) -> str:
    """Stale or missing tools-registry → user-visible notice."""
    target = vault / "_system" / "tools-registry.yaml"
    if not target.is_file():
        return (
            "TARS notice: _system/tools-registry.yaml is missing. Capability "
            "resolution will fall back to defaults — call "
            "mcp__tars_vault__refresh_integrations to rebuild it."
        )
    try:
        age = time.time() - target.stat().st_mtime
    except OSError:
        return ""
    if age > _REGISTRY_TTL_SECONDS:
        hours = int(age / 3600)
        return (
            f"TARS notice: _system/tools-registry.yaml is {hours}h old (TTL is 24h). "
            "Run mcp__tars_vault__refresh_integrations to refresh capability mappings."
        )
    return ""


def _cron_notice(vault: Path) -> str:
    """Surface jobs that look unregistered.

    Stdlib-only YAML reader: we already use the same minimal parser in
    `_read_install_yaml`. For housekeeping-state.yaml we just look for the
    cron_jobs block and the per-job `id` and `status` fields one indent in.
    """
    target = vault / "_system" / "housekeeping-state.yaml"
    if not target.is_file():
        return ""
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    issues: list[str] = []
    in_block = False
    current_job: str | None = None
    job_state: dict[str, dict[str, str]] = {}
    for raw in text.splitlines():
        if raw.startswith("cron_jobs:"):
            in_block = True
            continue
        if in_block:
            # Detect the next top-level key (no leading spaces) → exit block.
            if raw and not raw[0].isspace() and not raw.startswith("#"):
                in_block = False
                continue
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Two-space indent → job name; deeper indent → property.
            indent = len(raw) - len(raw.lstrip(" "))
            if indent == 2 and stripped.endswith(":"):
                current_job = stripped[:-1].strip()
                job_state.setdefault(current_job, {})
            elif current_job and indent >= 4 and ":" in stripped:
                key, _, value = stripped.partition(":")
                job_state[current_job][key.strip()] = value.strip().strip('"').strip("'")
    for job, props in job_state.items():
        job_id = props.get("id", "").lower()
        status = props.get("status", "").lower()
        if job_id in ("", "null", "~", "none") or status in ("not_registered", ""):
            issues.append(job)
    if not issues:
        return ""
    return (
        "TARS notice: cron jobs not registered: "
        + ", ".join(issues)
        + ". Re-run /welcome step 7 to register them — Claude does not run in the "
        "background, so unregistered jobs simply never fire."
    )


def _build_context(vault: Path | None, status: dict) -> str:
    parts: list[str] = []
    vault_note = _vault_notice(status)
    if vault_note:
        parts.append(vault_note)
    if vault and status.get("source") in ("env", "cwd-install", "cwd-config"):
        reg = _registry_notice(vault)
        if reg:
            parts.append(reg)
        cron = _cron_notice(vault)
        if cron:
            parts.append(cron)
    return "\n\n".join(parts)


def main() -> int:
    _event = read_event()
    if in_recursion():
        return 0
    vault, status = resolve_vault()
    context = _build_context(vault, status)
    write_output({"hookSpecificOutput": {"additionalContext": context}})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"session-start hook error: {exc}\n")
        rc = 0  # never block the session
    sys.exit(rc)
