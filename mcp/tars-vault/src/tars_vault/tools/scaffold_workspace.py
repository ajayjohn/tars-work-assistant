"""scaffold_workspace — deterministic first-run TARS workspace bootstrap.

Creates the empty directories and starter files that /welcome depends on.
This keeps first-run setup out of model-only "remember to mkdir" territory.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

from .. import _common


DIRECTORIES = [
    "_system",
    "_system/changelog",
    "_system/backlog",
    "_system/backlog/issues",
    "_system/backlog/ideas",
    "_system/telemetry",
    "memory",
    "memory/people",
    "memory/vendors",
    "memory/competitors",
    "memory/products",
    "memory/initiatives",
    "memory/decisions",
    "memory/org-context",
    "journal",
    "contexts",
    "contexts/products",
    "contexts/artifacts",
    "contexts/brand",
    "inbox",
    "inbox/pending",
    "inbox/processed",
    "archive",
    "archive/transcripts",
    "archive/tasks",
    "templates",
    "scripts",
    "skills",
]


def _is_under_claude_home(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to((Path.home() / ".claude").resolve())
    except OSError:
        return False


def _write_if_missing(path: Path, text: str, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return "skipped"
    _common.write_note_text(path, text, backup=path.exists())
    return "created" if not path.exists() else "updated"


def _frontmatter_note(frontmatter: dict[str, Any], body: str) -> str:
    return _common.build_note_text(frontmatter, body)


def _config_md(now_date: str, user_name: str, user_role: str, company: str) -> str:
    return _frontmatter_note(
        {
            "tags": ["tars/system"],
            "tars-user-name": user_name,
            "tars-user-title": user_role,
            "tars-user-company": company,
            "tars-user-industry": "",
            "tars-user-org": "",
            "tars-calendar-provider": "",
            "tars-task-provider": "",
            "tars-daily-briefing-time": "07:30",
            "tars-daily-briefing-tz": "America/Chicago",
            "tars-weekly-briefing-day": "Monday",
            "tars-weekly-briefing-time": "08:00",
            "tars-maintenance-day": "Friday",
            "tars-maintenance-time": "17:00",
            "tars-created": now_date,
        },
        "# TARS configuration\n\nUser profile and system preferences. Populated by onboarding.\n",
    )


def _index_md() -> str:
    return """# TARS workspace

This is your TARS workspace. All TARS-managed memory, journal, contexts, inbox, archive, and `_system/` files live here.

Slash commands are optional shortcuts. You can type natural-language requests and TARS will route them.

| What you want | Shortcut | Natural-language example |
|---|---|---|
| Try TARS with a paste | `/start` | "Show me what TARS can do with this transcript" |
| Process raw files | `/maintain inbox` | "Process everything in my inbox" |
| Process a meeting | `/meeting` | "Process this meeting transcript" |
| Save durable context | `/learn` | "Remember Sarah owns onboarding" |
| Look something up | `/answer` | "What do we know about the platform rewrite?" |
| Get oriented | `/briefing` | "What should I focus on today?" |
| Extract or manage tasks | `/tasks` | "Extract the action items from this" |
| Think through a decision | `/think` | "Stress-test this roadmap decision" |
| Draft communication | `/communicate` | "Draft a follow-up email from this call" |
| Create an artifact | `/create` | "Turn this into an exec-ready narrative" |
| Plan or check initiatives | `/initiative` | "Check the health of the onboarding initiative" |
| Check workspace health | `/lint` | "Check for stale or broken items" |
| Continue setup | `/welcome --continue-setup` | "Continue TARS setup" |
| See help | `/help` | "What can TARS do?" |

## Inbox

Drop transcripts, PDFs, decks, docs, screenshots, exports, or rough notes into `inbox/pending/`, then say "process inbox". TARS can process the pending folder in bulk and will ask before persisting memory or tasks.

## First demo

Paste a transcript, report, email thread, or rough notes and say "show me what TARS can do with this." TARS will preview the structure first and ask before saving durable memory or tasks.
"""


def _install_yaml(
    workspace: Path,
    workspace_type: str,
    obsidian_enabled: bool,
    persona: str,
    now: str,
) -> str:
    return f"""workspace_type: {workspace_type}
workspace_path: "{workspace}"
vault_path: "{workspace}"
obsidian_enabled: {"true" if obsidian_enabled else "false"}
obsidian_vault_path: "{workspace if obsidian_enabled else ""}"
installation_id: "{uuid.uuid4()}"
persona: "{persona}"
plugin_version: "3.4.2"
created: "{now}"
last_session_at: "{now}"
"""


def _maturity_yaml(now: str, obsidian_enabled: bool) -> str:
    return f"""onboarding:
  workspace_scaffold: true
  vault_structure: true
  workspace_type_selected: true
  obsidian_enabled: {"true" if obsidian_enabled else "false"}
  obsidian_skills: false
  integrations: false
  user_profile: true
  schedule: false
  cron_jobs: false
  git_initialized: false
  completed: false
  completed_date: null
deferred_setup:
  available: true
  completed: false
  dismissed: false
  next_step: demo
  last_reminded: null
  modules:
    demo_document: false
    people: false
    initiatives: false
    integrations: false
    schedule: false
    cron_jobs: false
    brand: false
    maintenance: false
    obsidian_browsing: false
last_updated: "{now}"
coaching:
  enabled: true
  frequency: restrained
  last_tip_shown: null
  last_tip_context: null
  dismissed_tips: []
  completed_milestones:
    first_demo_preview: false
    first_meeting_processed: false
    first_memory_saved: false
    first_answer_lookup: false
    third_briefing: false
    obsidian_prompt_seen: false
  counters:
    briefing_count: 0
    meeting_count: 0
    memory_write_count: 0
    failed_lookup_count: 0
"""


def scaffold_workspace(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    if not vault:
        return _common.error("missing 'vault' path")
    workspace_type = str(kwargs.get("workspace_type") or "headless").strip()
    if workspace_type not in {"headless", "obsidian"}:
        return _common.error("workspace_type must be 'headless' or 'obsidian'")
    overwrite = bool(kwargs.get("overwrite", False))
    allow_claude_home = bool(kwargs.get("allow_claude_home", False))
    user_name = str(kwargs.get("user_name") or "").strip()
    user_role = str(kwargs.get("user_role") or "").strip()
    company = str(kwargs.get("company") or "").strip()
    persona = str(kwargs.get("persona") or "").strip()

    workspace = _common.resolve_vault_path(vault)
    if _is_under_claude_home(workspace) and not allow_claude_home:
        return _common.error(
            "refusing to scaffold under ~/.claude; choose a transparent workspace such as ~/Documents/TARS Workspace",
            workspace=str(workspace),
        )

    created_dirs: list[str] = []
    skipped_dirs: list[str] = []
    try:
        workspace.mkdir(parents=True, exist_ok=True)
        for rel in DIRECTORIES:
            target = workspace / rel
            if target.exists():
                skipped_dirs.append(rel)
            else:
                target.mkdir(parents=True, exist_ok=True)
                created_dirs.append(rel)
    except OSError as exc:
        return _common.error(f"directory creation failed: {exc}", workspace=str(workspace))

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    now_date = now[:10]
    obsidian_enabled = workspace_type == "obsidian"

    files = {
        "_system/config.md": _config_md(now_date, user_name, user_role, company),
        "_system/install.yaml": _install_yaml(workspace, workspace_type, obsidian_enabled, persona, now),
        "_system/maturity.yaml": _maturity_yaml(now, obsidian_enabled),
        "_system/integrations.md": _frontmatter_note(
            {"tags": ["tars/system"], "tars-created": now_date},
            "# Integration registry\n\nCalendar and task integrations are not configured yet.\n",
        ),
        "_system/alias-registry.md": "# Alias registry\n\n| Alias | Canonical note | Type | Confidence |\n|---|---|---|---|\n",
        "_system/taxonomy.md": "# TARS taxonomy\n\nStarter taxonomy for people, initiatives, decisions, tasks, inbox, and journal entries.\n",
        "_system/kpis.md": "# KPIs\n\nAdd team, product, and initiative metrics here when useful.\n",
        "_system/schedule.md": "# Schedule\n\nRecurring and one-time TARS schedules.\n",
        "_system/guardrails.yaml": "blocked_patterns:\n  - ssn\n  - credit_card\n  - api_key\nwarn_patterns:\n  - salary\n  - compensation\n  - performance_rating\n",
        "_system/housekeeping-state.yaml": "last_run: null\nlast_success: null\nrun_count: 0\npending_inbox_count: 0\ncron_jobs:\n  daily_briefing: null\n  weekly_briefing: null\n  maintenance: null\nplugin_version: \"3.4.2\"\n",
        "index.md": _index_md(),
    }

    file_status: dict[str, str] = {}
    try:
        for rel, text in files.items():
            path = workspace / rel
            existed = path.exists()
            if existed and not overwrite:
                file_status[rel] = "skipped"
                continue
            _common.write_note_text(path, text, backup=existed)
            file_status[rel] = "updated" if existed else "created"
    except OSError as exc:
        return _common.error(f"file creation failed: {exc}", workspace=str(workspace))

    return _common.ok(
        workspace=str(workspace),
        created_dirs=created_dirs,
        skipped_dirs=skipped_dirs,
        files=file_status,
        index_path="index.md",
        inbox_path="inbox/pending",
        memory_path="memory",
    )
