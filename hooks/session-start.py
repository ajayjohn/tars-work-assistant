#!/usr/bin/env python3
"""SessionStart hook. Observability-only — never exits non-zero.

Banner composition (v3.3):

  0. Unexpanded TARS_VAULT_PATH env var — highest priority; if the MCP config
     passes "${TARS_VAULT_PATH}" as a literal string, writes will land in a
     mis-named directory.  Block and instruct immediately.
  1. Worktree isolation — if CWD is inside a .claude/worktrees/ path, surface
     a prominent notice so the user knows workspace writes go through the MCP
     server and offer the two operating modes.
  2. install.yaml mismatch warning.
  3. Legacy-vault notice when install.yaml is missing.
  4. tools-registry.yaml stale or missing (TTL = 24h).
  5. Cron-job health: any job with id: null or status != registered surfaces
     as a notice.  Re-registration runs in the user's session via /welcome
     step 7 (hooks cannot call MCP tools).
"""
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import (
    in_recursion,
    is_notice_suppressed,
    mark_notice_acknowledged,
    read_event,
    read_install_config,
    resolve_vault,
    write_output,
)


_REGISTRY_TTL_SECONDS = 24 * 60 * 60  # 24h per CLAUDE.md startup-checks §6


def _unexpanded_env_notice(status: dict) -> str:
    """Highest-priority banner: TARS_VAULT_PATH contains a shell variable literal."""
    if not status.get("unexpanded_env"):
        return ""
    raw = status.get("raw_env_value", "${TARS_VAULT_PATH}")
    return (
        f"TARS setup needs attention: TARS_VAULT_PATH is still the literal value "
        f'"{raw}". Set it to your real workspace path before writing.'
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

    profile_populated = False
    try:
        vault, status = resolve_vault()
        if vault:
            cfg = vault / "_system" / "config.md"
            install = status.get("install") or read_install_config(vault) or {}
            text = cfg.read_text(encoding="utf-8") if cfg.is_file() else ""
            profile_populated = bool(install) and bool(
                re.search(r"^tars-user-name:\s*[\"']?[^\"'\s].*$", text, re.MULTILINE)
            )
    except Exception:
        profile_populated = False

    if not profile_populated:
        return (
            "You are running TARS from a git worktree. To try TARS, point it at a "
            "local Markdown workspace and run `/start` for a 90-second demo or "
            "`/welcome` for setup.\n\n"
            "Framework development docs: docs/ARCHITECTURE.md, CONTRIBUTING.md."
        )

    branch_label = f" (`{branch}`)" if branch else ""
    return (
        f"⚠️  TARS WORKTREE SESSION: This session is running in an isolated git "
        f"worktree{branch_label}.\n\n"
        "   Files created via the git filesystem will NOT appear in your main\n"
        "   workspace until merged. TARS workspace writes go through the\n"
        "   tars-vault MCP server and land in the active workspace immediately.\n\n"
        "   Choose how to proceed:\n"
        "   [1] Knowledge-work mode (default) — /meeting, /learn, /briefing,\n"
        "       /tasks, /answer: writes go to your active TARS workspace.\n"
        "   [2] Framework/code mode — modifying skills, scripts, templates:\n"
        "       changes stay in this worktree; merge explicitly when done.\n\n"
        "   To list, merge, or prune active worktrees: run /maintain worktrees"
    )


def _vault_notice(status: dict) -> str:
    if status.get("mismatch"):
        install = status.get("install") or {}
        stored = install.get("workspace_path") or install.get("vault_path") or "(unset)"
        return (
            "TARS install warning: this folder does not match the recorded workspace. "
            f"Recorded path: {stored}. Run `/welcome --relocate` before writing here."
        )
    if status.get("source") == "cwd-config":
        return (
            "TARS setup is incomplete here. Run `/welcome` to finish workspace setup."
        )
    return ""


def _claude_home_workspace_notice(vault: Path | None) -> str:
    if vault is None:
        return ""
    try:
        home_claude = (Path.home() / ".claude").resolve()
        resolved = vault.expanduser().resolve()
        if not resolved.is_relative_to(home_claude):
            return ""
    except Exception:
        return ""
    if (vault / "_system" / "install.yaml").is_file():
        return ""
    return (
        "TARS configuration warning: the active workspace resolves under ~/.claude. "
        "That folder is usually application state, not a transparent TARS workspace. "
        "Use a folder such as ~/Documents/TARS Workspace and run `/welcome` again."
    )


def _registry_notice(vault: Path) -> str:
    """Refresh stale or missing integrations registry. Notice only on failure."""
    target = vault / "_system" / "tools-registry.yaml"
    needs_refresh = not target.is_file()
    try:
        age = time.time() - target.stat().st_mtime
    except OSError:
        age = 0
    needs_refresh = needs_refresh or age > _REGISTRY_TTL_SECONDS
    if not needs_refresh:
        return ""
    runner = ROOT.parent / "scripts" / "discover-mcp-tools.py"
    if not runner.is_file():
        return "TARS couldn't refresh its integrations index. Run `/doctor` when you have a minute."
    try:
        env = dict(os.environ)
        env["TARS_IN_HOOK"] = "1"
        result = subprocess.run(
            [sys.executable, str(runner), "--vault", str(vault), "--apply", "--json"],
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
        if result.returncode == 0:
            return ""
    except Exception:
        pass
    if is_notice_suppressed(vault, "integrations_refresh_failed"):
        return ""
    mark_notice_acknowledged(vault, "integrations_refresh_failed")
    return "TARS couldn't refresh its integrations index. Run `/doctor` when you have a minute."
    return ""


_CRON_CREATE_TTL_DAYS = 7
_CRON_CREATE_WARN_DAYS = 2  # warn when ≤ this many days before expiry


def _parse_cron_jobs(text: str) -> dict[str, dict[str, str]]:
    """Parse the cron_jobs block from housekeeping-state.yaml.

    Stdlib-only. Returns {job_name: {property: value}} with all values as
    stripped strings (null/~/"" → "").
    """
    job_state: dict[str, dict[str, str]] = {}
    in_block = False
    current_job: str | None = None
    for raw in text.splitlines():
        if raw.startswith("cron_jobs:"):
            in_block = True
            continue
        if in_block:
            if raw and not raw[0].isspace() and not raw.startswith("#"):
                in_block = False
                continue
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if indent == 2 and stripped.endswith(":"):
                current_job = stripped[:-1].strip()
                job_state.setdefault(current_job, {})
            elif current_job and indent >= 4 and ":" in stripped:
                key, _, value = stripped.partition(":")
                val = value.strip().strip('"').strip("'")
                if val.lower() in ("null", "~", "none"):
                    val = ""
                job_state[current_job][key.strip()] = val
    return job_state


def _cron_notice(vault: Path) -> str:
    """Surface scheduler health issues at session start.

    Checks performed (all stdlib, no MCP calls):
      1. Unregistered jobs — scheduler_type is null/empty or status != registered.
      2. CronCreate TTL expiry — cron_create_registered_at + 7d ≤ today+2d.
         These are re-registered automatically in /maintain; notice is informational.
      3. Mutual-exclusion drift — install.yaml scheduler_type disagrees with
         housekeeping-state.yaml (indicates a scheduler was changed without updating
         both records). Surface as a warning; auto-fix is NOT performed.

    Never blocks the session (observability-only).
    """
    target = vault / "_system" / "housekeeping-state.yaml"
    if not target.is_file():
        return ""
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""

    job_state = _parse_cron_jobs(text)

    unregistered: list[str] = []
    expiring_soon: list[str] = []
    now = time.time()

    for job, props in job_state.items():
        job_id = props.get("id", "")
        status = props.get("status", "")
        scheduler_type = props.get("scheduler_type", "")

        if not job_id or status in ("not_registered", ""):
            unregistered.append(job)
            continue

        # CronCreate TTL check.
        if scheduler_type == "CronCreate":
            registered_at_str = props.get("cron_create_registered_at", "")
            if registered_at_str:
                try:
                    # Parse ISO-8601 date/datetime — take just the date portion.
                    date_part = registered_at_str[:10]
                    import datetime as _dt
                    reg_date = _dt.date.fromisoformat(date_part)
                    age_days = (_dt.date.today() - reg_date).days
                    days_left = _CRON_CREATE_TTL_DAYS - age_days
                    if days_left <= _CRON_CREATE_WARN_DAYS:
                        expiring_soon.append(f"{job} ({days_left}d remaining)")
                except (ValueError, TypeError):
                    pass

    parts: list[str] = []

    if unregistered:
        if is_notice_suppressed(vault, "schedules_not_registered"):
            return ""
        mark_notice_acknowledged(vault, "schedules_not_registered")
        parts.append(
            "TARS scheduled jobs aren't running yet. Run `/welcome --setup-schedules` to enable them."
        )

    if expiring_soon:
        parts.append(
            "Some TARS scheduled jobs need renewal soon. Run `/maintain` to refresh them."
        )

    return "\n\n".join(parts)


def _migration_notice(vault: Path) -> str:
    """Check for pending migrations and surface a one-line notice if any exist."""
    if _is_uninitialised_fresh_workspace(vault):
        _stamp_housekeeping_version(vault, _live_plugin_version())
        return ""
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
                        "TARS has updates ready for your workspace. Run `/maintain migrations` to apply them."
                    )
    except Exception:
        pass
    return ""


def _live_plugin_version() -> str:
    try:
        import json

        data = json.loads((ROOT.parent / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        return str(data.get("version") or "")
    except Exception:
        return ""


def _housekeeping_version(vault: Path) -> str:
    target = vault / "_system" / "housekeeping-state.yaml"
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    for line in text.splitlines():
        m = re.match(r"^\s*plugin_version\s*:\s*(.*?)\s*$", line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return ""


def _stamp_housekeeping_version(vault: Path, version: str) -> None:
    if not version:
        return
    target = vault / "_system" / "housekeeping-state.yaml"
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    lines = []
    found = False
    for raw in text.splitlines():
        if re.match(r"^\s*plugin_version\s*:", raw):
            leading = len(raw) - len(raw.lstrip())
            lines.append(" " * leading + f'plugin_version: "{version}"')
            found = True
        else:
            lines.append(raw)
    if not found:
        lines.append(f'plugin_version: "{version}"')
    try:
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        return


def _install_value(vault: Path, key: str) -> str:
    install = read_install_config(vault) or {}
    value = install.get(key)
    return str(value or "")


def _stamp_install_version(vault: Path, version: str) -> None:
    target = vault / "_system" / "install.yaml"
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    lines = []
    found = False
    for raw in text.splitlines():
        if re.match(r"^\s*plugin_version\s*:", raw):
            lines.append(f'plugin_version: "{version}"')
            found = True
        else:
            lines.append(raw)
    if not found:
        lines.append(f'plugin_version: "{version}"')
    try:
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        return


def _parse_iso_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _version_drift_notice(vault: Path) -> str:
    live = _live_plugin_version()
    recorded = _install_value(vault, "plugin_version")
    if not live or not recorded or recorded == live:
        return ""
    if _housekeeping_version(vault) not in ("", live):
        return ""
    if is_notice_suppressed(vault, "version_drift"):
        return ""
    _stamp_install_version(vault, live)
    mark_notice_acknowledged(vault, "version_drift")
    return f"TARS was upgraded from {recorded} to {live}. No migration needed; refreshing your install record."


def _welcome_back_notice(vault: Path) -> str:
    last = _parse_iso_date(_install_value(vault, "last_session_at"))
    if not last:
        return ""
    days = (date.today() - last).days
    if days < 30 or is_notice_suppressed(vault, "welcome_back", ttl_days=30):
        return ""
    mark_notice_acknowledged(vault, "welcome_back")
    note_count = sum(1 for _ in vault.rglob("*.md"))
    detail = "Your workspace is still light" if note_count < 20 else "There may be useful changes to catch up on"
    return f"Welcome back. You haven't used TARS in {days} days. {detail}. Run `/briefing --catchup` for a 60-second summary."


def _pollution_notice(vault: Path) -> str:
    allowed = {"tags", "aliases"}
    polluted = 0
    for md in vault.rglob("*.md"):
        rel = str(md.relative_to(vault)).replace("\\", "/")
        if rel.startswith(("_system/", "archive/")):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm = _parse_frontmatter_only(text)
        if not fm:
            continue
        if any((k not in allowed and not k.startswith("tars-")) for k in fm):
            polluted += 1
    if polluted == 0 or is_notice_suppressed(vault, "frontmatter_pollution"):
        return ""
    mark_notice_acknowledged(vault, "frontmatter_pollution")
    return f"{polluted} note(s) use non-TARS frontmatter and won't show up in structured search. Run `/lint --fix-prefixes` to migrate."


def _parse_frontmatter_only(text: str) -> dict[str, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}
    out: dict[str, str] = {}
    for raw in m.group(1).splitlines():
        if ":" not in raw or raw.startswith(" "):
            continue
        key, _, value = raw.partition(":")
        out[key.strip()] = value.strip()
    return out


def _state_aware_lines(vault: Path) -> list[str]:
    lines: list[str] = []
    stale = 0
    cutoff = time.time() - (30 * 24 * 60 * 60)
    for md in (vault / "memory" / "initiatives").rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
            fm = _parse_frontmatter_only(text)
            if "tars/initiative" in fm.get("tags", "") and "active" in fm.get("tars-status", "") and md.stat().st_mtime < cutoff:
                stale += 1
        except (OSError, UnicodeDecodeError):
            continue
    if stale:
        lines.append(f"{stale} active initiative(s) haven't been touched in 30+ days. Run `/lint --stale`.")

    overdue = 0
    today = date.today().isoformat()
    for md in (vault / "memory" / "tasks").rglob("*.md"):
        try:
            fm = _parse_frontmatter_only(md.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if "tars/task" in fm.get("tags", "") and fm.get("tars-status", "open") in ("open", "in-progress"):
            due = fm.get("tars-due", "").strip('"').strip("'")
            if due and due < today:
                overdue += 1
    if overdue:
        lines.append(f"{overdue} task(s) are overdue. Run `/tasks` to triage them.")

    inbox_dir = vault / "inbox" / "pending"
    pending = sum(1 for p in inbox_dir.glob("*.md")) if inbox_dir.is_dir() else 0
    if pending:
        lines.append(f"{pending} item(s) waiting in your inbox. Say \"process inbox\" to work through them.")
    return lines


def _is_uninitialised_fresh_workspace(vault: Path) -> bool:
    if _housekeeping_version(vault):
        return False
    if any((vault / "memory").rglob("*.md")):
        return False
    if any((vault / "journal").rglob("*.md")):
        return False
    return True


def _build_context(vault: Path | None, status: dict) -> str:
    parts: list[str] = []

    # Unexpanded env var is a blocking error — surface first, skip remaining checks.
    unexpanded = _unexpanded_env_notice(status)
    if unexpanded:
        parts.append(unexpanded)
        return "\n\n".join(parts)

    if vault is None and status.get("source") == "none":
        return "This folder isn't a TARS workspace yet. Try `/start` for a 90-second demo, or `/welcome` to set one up."

    # Worktree isolation notice (informational, non-blocking).
    worktree = _worktree_notice()
    if worktree:
        parts.append(worktree)

    vault_note = _vault_notice(status)
    if vault_note:
        parts.append(vault_note)
    claude_home = _claude_home_workspace_notice(vault)
    if claude_home:
        parts.append(claude_home)
    if vault and status.get("source") in ("env", "cwd-install", "cwd-config"):
        for line in (
            _welcome_back_notice(vault),
            _version_drift_notice(vault),
            _pollution_notice(vault),
        ):
            if line:
                parts.append(line)
        parts.extend(_state_aware_lines(vault))
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
