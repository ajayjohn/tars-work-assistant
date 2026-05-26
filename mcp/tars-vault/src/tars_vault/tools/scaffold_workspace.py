"""scaffold_workspace — deterministic first-run TARS workspace bootstrap.

Creates the empty directories and starter files that /welcome depends on.
This keeps first-run setup out of model-only "remember to mkdir" territory.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid

from .. import _common


ROOT = Path(__file__).resolve().parents[5]


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
    "tasks",
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
    "archive/inbox",
    "archive/tasks",
    "archive/people",
    "archive/initiatives",
    "archive/notes",
    "templates",
    "scripts",
    "skills",
]

OBSIDIAN_DIRECTORIES = [
    "_views",
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

Markdown files are plain text files. You can open them in any text editor. If you enable Obsidian later, this same workspace also becomes your Obsidian vault.

Slash commands are optional shortcuts. You can type natural-language requests and TARS will route them.

| What you want | Shortcut | Natural-language example |
|---|---|---|
| Try TARS with a paste | `/meeting` | "Process this meeting transcript" |
| Process raw files | `/maintain inbox` | "Process everything in my inbox" |
| Process a meeting | `/meeting` | "Process this meeting transcript" |
| Save durable context | `/learn` | "Remember Sarah owns onboarding" |
| Look something up | `/answer` | "What do we know about the platform rewrite?" |
| Get oriented after adding context | `/briefing` | "What should I focus on today?" |
| Extract or manage tasks | `/tasks` | "Extract the action items from this" |
| Think through a decision | `/think` | "Stress-test this roadmap decision" |
| Draft communication | `/communicate` | "Draft a follow-up email from this call" |
| Create an artifact | `/create` | "Turn this into an exec-ready narrative" |
| Plan or check initiatives | `/initiative` | "Check the health of the onboarding initiative" |
| Check workspace health | `/lint` | "Check for stale or broken items" |
| Check TARS install | `/doctor` | "Check my TARS install" |
| Continue setup | `/welcome --continue-setup` | "Continue TARS setup" |
| See help | `/help` | "What can TARS do?" |

## Inbox

The inbox is a folder workflow, not a single `INBOX.md` note. Drop transcripts, PDFs, decks, docs, screenshots, exports, or rough notes into `inbox/pending/`, then say "process inbox". TARS can process the pending folder in bulk and will ask before persisting memory or tasks.

## First demo

Paste a meeting transcript, PDF/report excerpt, email thread, or rough notes and say "show me what TARS can do with this." TARS will preview memory candidates, journal notes, and tasks first, then ask before saving anything durable.
"""


def _obsidian_view_files() -> dict[str, str]:
    """Return Obsidian `.base` templates available from source or package."""
    repo_or_plugin_root = Path(__file__).resolve().parents[5]
    candidates = [
        repo_or_plugin_root / "templates" / "views",
        repo_or_plugin_root / "_views",
    ]
    for directory in candidates:
        if not directory.is_dir():
            continue
        files: dict[str, str] = {}
        for path in sorted(directory.glob("*.base")):
            try:
                files[path.name] = _stamp_view(path.read_text(encoding="utf-8"))
            except OSError:
                continue
        if files:
            return files

    return {
        "inbox-pending.base": _stamp_view('filters:\n  file.inFolder("inbox/pending")\n\nviews:\n  - type: table\n    name: "Pending Items"\n'),
        "all-people.base": _stamp_view('filters:\n  file.hasTag("tars/person")\n\nviews:\n  - type: table\n    name: "All People"\n'),
        "all-initiatives.base": _stamp_view('filters:\n  file.hasTag("tars/initiative")\n\nviews:\n  - type: table\n    name: "All Initiatives"\n'),
    }


def _stamp_view(text: str) -> str:
    if text.startswith("# generated-by: tars "):
        return text
    return f"# generated-by: tars {_plugin_version()}\n{text}"


def _install_yaml(
    workspace: Path,
    workspace_type: str,
    obsidian_enabled: bool,
    persona: str,
    now: str,
) -> str:
    plugin_version = _plugin_version()
    return f"""workspace_type: {workspace_type}
workspace_path: "{workspace}"
vault_path: "{workspace}"
obsidian_enabled: {"true" if obsidian_enabled else "false"}
obsidian_vault_path: "{workspace if obsidian_enabled else ""}"
installation_id: "{uuid.uuid4()}"
persona: "{persona}"
plugin_version: "{plugin_version}"
created: "{now}"
last_session_at: "{now}"
acknowledged_notices:
"""


def _plugin_version() -> str:
    try:
        data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        return str(data.get("version") or "")
    except Exception:
        return ""


def _repo_seed(rel: str, fallback: str) -> str:
    try:
        return (ROOT / rel).read_text(encoding="utf-8")
    except OSError:
        return fallback


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


def _activity_ledger_yaml() -> str:
    return """# Derived state capsule for SessionStart and adaptive briefing.
# Rebuilt from Markdown by tars-vault workspace_map/context_gaps and /lint.
generated_at: null
source: derived-from-markdown
active_file_count: 0
archive_file_count: 0
last:
  session_at: null
  briefing_at: null
  transcript_at: null
  inbox_process_at: null
  successful_sync_at: null
  archive_sweep_at: null
stale_active_initiatives:
  count: 0
  oldest_days: 0
overdue_tasks:
  count: 0
  oldest_days: 0
inbox:
  pending_count: 0
frontmatter_pollution_count: 0
context_gaps: []
"""


def scaffold_workspace(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    if not vault:
        return _common.error("missing 'vault' path")
    workspace_type = str(kwargs.get("workspace_type") or "headless").strip()
    if workspace_type not in {"headless", "obsidian"}:
        return _common.error("workspace_type must be 'headless' or 'obsidian'")
    obsidian_enabled = workspace_type == "obsidian"
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
        directories = DIRECTORIES + (OBSIDIAN_DIRECTORIES if obsidian_enabled else [])
        for rel in directories:
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
        "_system/guardrails.yaml": _repo_seed("_system/guardrails.yaml", "block_patterns: []\nwarn_patterns: []\n"),
        "_system/housekeeping-state.yaml": _repo_seed("_system/housekeeping-state.yaml", f'plugin_version: "{_plugin_version()}"\n').replace('plugin_version: ""', f'plugin_version: "{_plugin_version()}"'),
        "_system/activity-ledger.yaml": _repo_seed("_system/activity-ledger.yaml", _activity_ledger_yaml()),
        "index.md": _index_md(),
    }

    if obsidian_enabled:
        files.update({f"_views/{name}": text for name, text in _obsidian_view_files().items()})

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
        views_path="_views" if obsidian_enabled else None,
    )
