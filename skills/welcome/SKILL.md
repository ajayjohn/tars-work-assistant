---
name: welcome
description: Deterministic first-run setup contract for the TARS Markdown workspace, with optional Obsidian mode and deferred setup continuation
user-invocable: true
triggers:
  - first run
  - "setup"
  - "onboarding"
  - "welcome"
  - "initialize TARS"
  - "bootstrap"
  - "continue TARS setup"
help:
  purpose: |-
    Create or update the user's portable TARS workspace. The first-run path
    asks only essential questions, uses the local TARS helper to create the
    workspace, and verifies the canonical workspace before saying setup is complete.
  use_cases:
    - "Set up TARS"
    - "Bootstrap my workspace"
    - "Continue deferred setup: `/welcome --continue-setup`"
    - "Enable Obsidian later: `/welcome --enable-obsidian`"
    - "Disable Obsidian dependency: `/welcome --disable-obsidian`"
    - "Enable scheduled jobs: `/welcome --setup-schedules`"
    - "Relocate a moved workspace: `/welcome --relocate`"
    - "Change persona later: `/welcome --change-persona`"
  scope: setup,bootstrap,onboarding,welcome,initialize
---

# Welcome

This skill is the only first-run setup path for TARS. Setup is designed for
Sonnet or a stronger model: short prompts, deterministic tool calls, explicit
verification, and no architectural improvisation.

## Canonical Workspace Contract

TARS creates one portable Markdown workspace. All user-visible TARS state must
live inside the selected workspace folder.

Required workspace layout:

```text
_system/
memory/
journal/
contexts/
inbox/pending/
inbox/processed/
archive/
templates/
scripts/
index.md
```

Obsidian mode may also create `_views/`. It must use the same workspace folder.

Never create generic product-management folders. Never say setup is complete if
`index.md`, `_system/install.yaml`, `_system/config.md`, `memory/`, or
`inbox/pending/` is missing.

The inbox is the `inbox/pending/` folder. Do not create or tell users to edit
`INBOX.md` or `inbox.md`. Durable records must be stored in the `memory/`
subfolders, not in root files like `MEMORY.md`, `PEOPLE.md`, or
`INITIATIVES.md`.

## First-Run Setup

Use this path when `_system/config.md` or `_system/install.yaml` is missing.

### 1. Show workspace choices

Tell the user:

> "TARS stores everything in one local workspace folder. Markdown files are
> plain text files you can open in any text editor. You can zip the workspace
> later to back up your setup and data."

Show:

- Claude-selected folder: `{cwd}`
- Active TARS workspace: `{active_workspace}`
- Recommended default: `~/Documents/TARS Workspace`

Ask:

> "Where should TARS create the workspace? Choose the active folder, the
> Documents default, or provide another folder."

If the requested folder differs from the active workspace path available to the
local TARS helper and the helper cannot write there, stop. Do not create the
workspace in the wrong folder.

If the active path resolves under `~/.claude` and no existing install record is
present, warn and recommend `~/Documents/TARS Workspace`.

### 2. Ask essential personalization questions

Ask this compact prompt:

> "What should TARS know to personalize setup?
> - Your name:
> - Role/title:
> - Company or team:"

Do not skip this prompt during first-run setup.

### 3. Pick persona

Ask:

> "Which best matches your role? Pick the closest; you can change it later.
> 1. Product Leader
> 2. Sales / Customer-Facing
> 3. Delivery / Project Manager
> 4. Data Science / Analytics Lead
> 5. Architect / Staff Engineer
> 6. Support / Operations Lead
> 7. Engineering Manager
> 8. None of these match"

Store the matching persona key:

```text
product-leader
sales-customer-facing
delivery-pm
data-science-lead
architect-staff-eng
support-ops-lead
engineering-manager
```

### 4. Pick workspace mode

Ask:

> "How do you want to use this workspace now?
> 1. Claude-first Markdown workspace (recommended)
> 2. Obsidian browsing over the same workspace
>
> If you don't know what Obsidian is, leave it disabled. You can turn it on
> later. In Obsidian mode, this same TARS workspace is also an Obsidian vault."

Use `headless` for option 1 and `obsidian` for option 2.

### 5. Create workspace deterministically

Use the local TARS helper exactly once:

```text
mcp__tars_vault__scaffold_workspace(
  workspace_type="<headless|obsidian>",
  user_name="<name>",
  user_role="<role/title>",
  company="<company/team>",
  persona="<persona key>",
  overwrite=false
)
```

If the helper is unavailable, stop. Use this user-facing recovery text:

```markdown
I can't safely finish TARS setup because the local TARS helper is not connected.

This helper creates and checks the workspace in the background. This is not an
Obsidian, calendar, task, email, or Slack issue. Those integrations are optional.

Please make sure the TARS plugin is enabled, restart Claude, and run `/doctor`
or ask "check my TARS install." Then run `/welcome` again.
```

If the helper returns an error, show the reason in plain language and stop.

### 6. Verify before completing

Use the local TARS helper to read and verify:

```text
mcp__tars_vault__read_note(file="index.md")
mcp__tars_vault__read_note(file="_system/install.yaml")
mcp__tars_vault__read_note(file="_system/config.md")
```

Also verify the scaffold result reports:

```text
memory_path: "memory"
inbox_path: "inbox/pending"
index_path: "index.md"
```

If any verification fails, say setup is incomplete and explain what failed.

### 7. Final response

Keep the final response short. Use this structure:

```markdown
## Workspace Ready

TARS is set up in `{workspace_path}`.

- `index.md`: cheat sheet created
- `memory/`: durable context folders ready
- `inbox/pending/`: drop-zone ready for transcripts, PDFs, reports, email threads, decks, screenshots, exports, and rough notes

Slash commands are optional. You do not need to remember them; natural language works just as well.

| Shortcut | Natural-language example |
|---|---|
| `/maintain inbox` | "Process everything in my inbox" |
| `/meeting` | "Process this meeting transcript" |
| `/learn` | "Remember that Sarah owns onboarding" |
| `/help` | "What can TARS do?" |

### Try this now

Paste or upload a meeting transcript, PDF/report excerpt, email thread, or rough notes.
I will preview what TARS can extract into memory candidates, journal notes, and
tasks before saving anything.

Or drop files into `inbox/pending/` and say: "process inbox".

You can continue setup later with `/welcome --continue-setup` or by saying
"continue TARS setup".

TARS is ready whenever you want to process something.
```

If the user runs `/welcome --setup-schedules`, follow the **Schedule
registration** procedure further below. If no scheduler is available in the
current runtime, say: "TARS couldn't enable scheduled jobs in this session. You
can still use every command manually."

Do not include a long directory listing. Do not recommend namespaced command
syntax; use plain TARS slash commands or natural language.
Do not recommend `/briefing` as a starter action in a brand-new workspace;
briefings become useful after the workspace has memory, meetings, tasks, or
connected calendar/task integrations. Do not end with an open-ended "what's on
your mind?" question; guide the user into the first demo.

## Existing Workspace

If both `_system/config.md` and `_system/install.yaml` exist, say:

> "TARS is already set up for {user_name}. Run a health check, continue setup,
> or change settings?"

Offer:

1. Health check
2. Continue setup
3. Change persona
4. Enable or disable Obsidian
5. Cancel

Do not overwrite identity, memory, journal, integrations, or schedules unless
the user explicitly chooses a focused setup mode.

## Focused Modes

These modes do not rerun first setup.

### `/welcome --continue-setup`

Also run when the user says "continue TARS setup", "finish setup", "add
integrations", "add people", or "add initiatives".

Read `_system/maturity.yaml`. Offer one compact menu:

```text
Deferred setup still available:
1. Add key people
2. Add active initiatives
3. Connect calendar/tasks
4. Configure briefings and maintenance
5. Add brand context
6. Enable Obsidian browsing
7. Mark setup complete for now
```

Run only the selected module and update `_system/maturity.yaml`.

### `/welcome --enable-obsidian`

Use when a headless user wants Obsidian as an optional browser. Idempotent.
Accepts an optional `--keep-views` flag (preserves existing `.base` files
even if they were generated by an older plugin version).

1. Read `_system/install.yaml`.
2. Confirm the Obsidian folder. Default to `workspace_path`.
3. Verify it is the same workspace folder.
4. Refresh views via the helper script. From a Bash tool call:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/refresh-obsidian-views.py --vault <workspace_path> --apply`
   (add `--keep-views` if the user passed `--keep-views`). The script:
   - Detects views generated by an older plugin version using their
     `# generated-by: tars <version>` header line.
   - Backs up every existing `.base` to `_views/.attic/<timestamp>/` before
     regenerating.
   - Skips when `--keep-views` is set; only reports staleness.
   - Is safe to run on a workspace with no `_views/` directory yet (the
     scaffold step will have created it; this script just refreshes content).
5. Update only:

```yaml
workspace_type: obsidian
obsidian_enabled: true
obsidian_vault_path: "<workspace_path>"
last_session_at: "<now>"
```

Confirm: "Obsidian browsing is enabled for this workspace. Existing memory,
journal, schedules, and integrations were left untouched." If the script
reported stale views and regenerated them, append: " I refreshed N Obsidian
view(s); your previous views are backed up under `_views/.attic/`."

If `--keep-views` was used and stale views exist, append instead: " I left
your existing Obsidian views in place. Run `/welcome --enable-obsidian`
without `--keep-views` to refresh them when you're ready."

### `/welcome --disable-obsidian`

1. Read `_system/install.yaml`.
2. Update only:

```yaml
workspace_type: headless
obsidian_enabled: false
last_session_at: "<now>"
```

Leave `_views/` and Obsidian metadata untouched.

Confirm: "TARS is now Claude-first. Existing data remains in the same
workspace."

### `/welcome --relocate`

Use when the workspace folder moved.

1. Read `_system/install.yaml`.
2. Compare recorded `workspace_path` to the active workspace.
3. Ask for confirmation.
4. Update only `workspace_path`, backward-compatible `vault_path`, and
   `last_session_at`.

Do not re-scaffold the workspace. Do not ask onboarding questions. Do not
rewrite `_system/config.md`.

### `/welcome --change-persona`

1. Read current persona from `_system/install.yaml`.
2. Show the seven persona menu and mark the current choice.
3. Update only persona-derived config fields.
4. Append one line to `_system/changelog/YYYY-MM-DD.md`.

Confirm: "Persona changed from X to Y. Existing identity, memory, schedule, and integrations were left untouched."

Do not touch `tars-user-name`, `tars-user-title`, `tars-user-company`, memory,
journal, integrations, or scheduled jobs.

### `/welcome --setup-schedules`

Idempotent. Registers four standard scheduled jobs against whichever scheduler
is connected in the current Claude session. Re-running is safe — already-registered
jobs are skipped.

**1. Detect available scheduler.** Try, in order:

- `mcp__scheduled-tasks__create_scheduled_task` (Cowork) — preferred when both available.
- `CronCreate` (Claude Code).

If neither tool is callable in this session, stop and say: *"TARS couldn't
enable scheduled jobs in this session. You can still use every command
manually. Try `/welcome --setup-schedules` again from a session where a
scheduler is connected."* Do not write to housekeeping-state.

**2. Read current state.** Use `mcp__tars_vault__read_system_file(file="_system/housekeeping-state.yaml")`
and find the `cron_jobs` block. For each of the four jobs below, check
`status`. If already `registered` with the **same** scheduler_type, skip it.
If registered with a **different** scheduler_type, surface a one-line warning
and skip it (mutual exclusion). If `not_registered`, proceed.

**3. Register each pending job.** For each:

| Job | Default cadence | Default time | Skill the job runs |
|---|---|---|---|
| `daily_briefing` | weekdays | 08:00 local | `/briefing` |
| `weekly_briefing` | Mondays | 07:00 local | `/briefing` (weekly mode) |
| `weekly_maintenance` | Sundays | 18:00 local | `/maintain` |
| `lint` | Saturdays | 09:00 local | `/lint` |

For Cowork: call `mcp__scheduled-tasks__create_scheduled_task` with `cron`
expression, the slash-command body, and a stable name. For Claude Code's
`CronCreate`: call it with the same cron + prompt.

**4. Stamp housekeeping-state.** For each successful registration, update the
matching `cron_jobs.<job>` entry via
`mcp__tars_vault__update_frontmatter(file="_system/housekeeping-state.yaml", updates={...}, allow_protected_paths=true)`
with:

```yaml
id: <id returned by the scheduler>
scheduler_type: "mcp__scheduled-tasks"     # or "CronCreate"
schedule: "0 8 * * 1-5"                    # the cron string actually used
status: registered
cron_create_registered_at: "<ISO 8601 now, only when scheduler_type is CronCreate>"
```

**5. Stamp install.yaml.** Set `scheduler_type` at the top level of
`_system/install.yaml` so SessionStart can compare. Same `update_frontmatter`
call with `allow_protected_paths=true`.

**6. Mark notice acknowledged.** The `schedules_not_registered` notice in
`acknowledged_notices` should advance to "now" so SessionStart stops surfacing it.

**7. Output to user — plain language only.** Example:

> *"Registered 4 scheduled jobs with Cowork. Daily briefing weekdays 8am, weekly
> briefing Mondays 7am, weekly maintenance Sundays 6pm, weekly lint Saturdays
> 9am. Run `/welcome --setup-schedules` again to refresh, or edit the times in
> _system/housekeeping-state.yaml."*

If any registrations failed, list them by friendly name (e.g. "weekly lint")
and propose `/welcome --setup-schedules` for a retry. **Never** print MCP tool
names or shell commands in the user-visible summary.

**8. Edge case: `--skip-schedules`.** If the user passed `--skip-schedules`
instead, do not register anything; just write
`acknowledged_notices.schedules_not_registered: "<now>"` so the SessionStart
notice stays suppressed for 7 days. Tell the user: *"Skipped scheduled jobs.
Run `/welcome --setup-schedules` whenever you want to enable them."*

## Safety Rules

- Ask when path confidence is below 80%.
- Never create workspace files outside the selected workspace.
- Never create generic product-management folders.
- Never create root index-like files named `INBOX.md`, `MEMORY.md`,
  `PEOPLE.md`, or `INITIATIVES.md`.
- Never auto-persist memory or tasks during the first demo.
- Always offer the first demo after setup.
- Always treat slash commands as shortcuts, not requirements.
