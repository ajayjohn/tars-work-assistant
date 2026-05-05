#!/usr/bin/env python3
"""SessionStart hook. Observability-only — never exits non-zero.

Banner composition (v3.3):

  0. Unexpanded TARS_VAULT_PATH env var — highest priority; if the MCP config
     passes "${TARS_VAULT_PATH}" as a literal string, writes will land in a
     mis-named directory.  Block and instruct immediately.
  1. Worktree isolation — if CWD is inside a .claude/worktrees/ path, surface
     a prominent notice so the user knows vault writes go through obsidian-cli
     (bypassing the worktree boundary) and offer the two operating modes.
  2. install.yaml mismatch warning.
  3. Legacy-vault notice when install.yaml is missing.
  4. tools-registry.yaml stale or missing (TTL = 24h).
  5. Cron-job health: any job with id: null or status != registered surfaces
     as a notice.  Re-registration runs in the user's session via /welcome
     step 7 (hooks cannot call MCP tools).
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import in_recursion, read_event, resolve_vault, write_output


_REGISTRY_TTL_SECONDS = 24 * 60 * 60  # 24h per CLAUDE.md startup-checks §6


def _unexpanded_env_notice(status: dict) -> str:
    """Highest-priority banner: TARS_VAULT_PATH contains a shell variable literal."""
    if not status.get("unexpanded_env"):
        return ""
    raw = status.get("raw_env_value", "${TARS_VAULT_PATH}")
    return (
        "⚠️  TARS CONFIGURATION ERROR: TARS_VAULT_PATH is not resolved.\n"
        f"   The MCP server received the literal string \"{raw}\" instead of an\n"
        "   absolute path. Claude Code does not expand shell variables in .mcp.json\n"
        "   env blocks — writes will land in a mis-named directory and be invisible\n"
        "   to Obsidian.\n\n"
        "   Fix: open your .mcp.json (or the root ~/.claude/.mcp.json) and replace\n"
        f"   \"{raw}\" with the absolute path to your vault, e.g.\n"
        "   \"/Users/you/Notes/TARS-Work\".\n\n"
        "   To relocate files already written to the wrong directory, run:\n"
        "     python3 scripts/migrate-stranded-vault-files.py --vault /path/to/vault --dry-run\n"
        "   then re-run with --apply after reviewing the plan.\n\n"
        "   Vault writes are BLOCKED until TARS_VAULT_PATH is corrected."
    )


def _worktree_notice() -> str:
    """Surface a clear notice when the session is running inside a git worktree."""
    cwd = os.getcwd()
    # Both .claude/worktrees/ (standard Claude Code path) and any path that
    # has /.git/worktrees/ ancestry indicate worktree isolation.
    in_worktree = ".claude/worktrees/" in cwd or "/.git/worktrees/" in cwd
    if not in_worktree:
        # Also check via git — the working directory may be a detached worktree
        # without the canonical path substring.
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                toplevel = result.stdout.strip()
                worktree_result = subprocess.run(
                    ["git", "worktree", "list", "--porcelain"],
                    capture_output=True, text=True, cwd=toplevel, timeout=3
                )
                if worktree_result.returncode == 0:
                    worktrees = [
                        line.split(" ", 1)[1]
                        for line in worktree_result.stdout.splitlines()
                        if line.startswith("worktree ")
                    ]
                    # If there are multiple worktrees and CWD is not the main one
                    if len(worktrees) > 1 and worktrees and cwd != worktrees[0]:
                        in_worktree = True
        except Exception:
            pass

    if not in_worktree:
        return ""

    # Extract branch name from CWD or git
    branch = ""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
    except Exception:
        pass

    branch_label = f" (`{branch}`)" if branch else ""
    return (
        f"⚠️  TARS WORKTREE SESSION: This session is running in an isolated git "
        f"worktree{branch_label}.\n\n"
        "   Files created via the git filesystem will NOT appear in your Obsidian\n"
        "   vault until merged to main. However, TARS vault writes go through\n"
        "   obsidian-cli, which communicates with the running Obsidian app directly\n"
        "   and bypasses the worktree boundary — knowledge-work outputs land in\n"
        "   your live vault immediately.\n\n"
        "   Choose how to proceed:\n"
        "   [1] Knowledge-work mode (default) — /meeting, /learn, /briefing,\n"
        "       /tasks, /answer: vault writes go to your live Obsidian vault.\n"
        "   [2] Framework/code mode — modifying skills, scripts, templates:\n"
        "       changes stay in this worktree; merge explicitly when done.\n\n"
        "   To list, merge, or prune active worktrees: run /maintain worktrees"
    )


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


def _migration_notice(vault: Path) -> str:
    """Check for pending migrations and surface a one-line notice if any exist."""
    runner = ROOT.parent / "scripts" / "run-migrations.py"
    if not runner.is_file():
        return ""
    try:
        result = subprocess.run(
            [sys.executable, str(runner), "--vault", str(vault), "--list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return ""
        # Parse output for "Pending (N):" line.
        for line in result.stdout.splitlines():
            m = __import__("re").match(r"Pending \((\d+)\):", line.strip())
            if m:
                n = int(m.group(1))
                if n > 0:
                    return (
                        f"TARS notice: {n} pending migration(s) detected. "
                        "Run /maintain migrations (or `python3 scripts/run-migrations.py "
                        f"--vault {vault} --dry-run`) to review and apply."
                    )
    except Exception:
        pass
    return ""


def _build_context(vault: Path | None, status: dict) -> str:
    parts: list[str] = []

    # Unexpanded env var is a blocking error — surface first, skip remaining checks.
    unexpanded = _unexpanded_env_notice(status)
    if unexpanded:
        parts.append(unexpanded)
        return "\n\n".join(parts)

    # Worktree isolation notice (informational, non-blocking).
    worktree = _worktree_notice()
    if worktree:
        parts.append(worktree)

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
        migration = _migration_notice(vault)
        if migration:
            parts.append(migration)
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
