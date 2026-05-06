---
name: welcome
description: Progressive onboarding wizard that scaffolds a local Markdown workspace, optionally enables Obsidian views, configures integrations, and supports mode switching
user-invocable: true
triggers:
  - first run (no _system/config.md)
  - "setup"
  - "onboarding"
  - "welcome"
  - "initialize TARS"
  - "bootstrap"
help:
  purpose: |-
    Interactive first-run workspace setup. Creates a local Markdown workspace, records
    user identity and persona, optionally enables Obsidian views, configures integrations
    progressively, registers cron jobs for briefings and maintenance, and initializes git.
  use_cases:
    - "Set up TARS"
    - "Bootstrap my workspace"
    - "Initialize TARS"
    - "Run onboarding"
    - "Enable Obsidian later: `/welcome --enable-obsidian`"
    - "Disable Obsidian dependency: `/welcome --disable-obsidian`"
    - "Relocate a moved workspace: `/welcome --relocate`"
    - "Change persona later: `/welcome --change-persona`"
    - "Continue deferred setup: `/welcome --continue-setup`"
  scope: setup,bootstrap,onboarding,welcome,initialize
---

# Welcome: onboarding wizard

Interactive first-run setup for TARS v3. Creates a local Markdown workspace, then
adds optional Obsidian views and deeper integrations as the user is ready. This skill
replaces both `install.sh` and the legacy `/welcome` command.

Fast setup should stay compact, but it must not feel empty. A little friction is
worth it when it gives TARS enough context to be useful on day 1:

1. Choose or confirm a local folder.
2. Capture name, role/title, company/team, and the user's main first use case.
3. Pick the closest persona.
4. Choose workspace type: `headless` or `obsidian`.
5. Create the full workspace structure and root `index.md` cheat sheet.
6. Offer a guided first demo with a transcript, document, report, or inbox file.

Deferred setup covers key people, initiatives, calendar/tasks, schedules, brand, maintenance,
and Obsidian helper skills. Do not block first value on these items.

Fast setup must always end with an explicit continuation path:

> "You can continue setup later with `/welcome --continue-setup` or by saying 'continue TARS setup'. I’ll remind you lightly in Daily Digest/help until you finish, dismiss the reminder, or turn coaching off."

### v3.1 pre-flight additions

- Verify `tars-vault` MCP server is reachable (`mcp__tars_vault__read_note(file="schemas")` should succeed). If not, guide user through `.mcp.json` entry: `{"tars-vault": {"type": "stdio", "command": "python3", "args": ["-m", "tars_vault"]}}`.
- If the MCP server is not reachable, run or suggest `python3 scripts/doctor.py --workspace <path>` before continuing. Surface missing Python, missing `mcp`, unexpanded `TARS_VAULT_PATH`, non-writable workspace, or install-record mismatch as clear setup issues instead of silently continuing.
- Confirm plugin hooks (`session-start.py`, `pre-tool-use.py`, `post-tool-use.py`, `pre-compact.py`, `session-end.py`, `instructions-loaded.py`) are registered.
- Run `scripts/githooks/install-githooks.sh` to enforce authorship rules locally.
- **Anthropic first-party skills probe (§8.10.1)**: detect which of `pptx`, `docx`, `xlsx`, `pdf`, `web-artifacts-builder` are available in the host Claude Code install. Read the user-invocable skills list surfaced in `<system-reminder>` blocks; do not programmatically load or inspect third-party skill packages. Persist the result in `_system/config.md` frontmatter as `tars-anthropic-skills: [pptx, docx, xlsx, pdf, web-artifacts-builder]` (include only those available). `/create` reads this at session start instead of reprobing.
- Integration discovery: `mcp__tars_vault__refresh_integrations()` writes `_system/tools-registry.yaml` so `resolve_capability` works from the first session.
- **Brand-guidelines scaffold (§5.1)**: if the user plans to use `/create` or `/communicate` for branded artifacts, offer to scaffold a brand file from `templates/brand-guidelines.md` → `contexts/brand/<brand-name>-brand-guidelines.md` (tagged `tars/brand`, frontmatter `tars-brand: true`). Cache the active brand as `tars-active-brand: <filename>` in `_system/config.md`.

---

## Pipeline overview

| Step | Name | Purpose |
|------|------|---------|
| 1 | Pre-flight check | Detect existing workspace, offer resume, health check, or fast setup |
| 1.5 | Pick a persona | Seed role-appropriate defaults for briefings and analysis |
| 1.6 | Choose workspace type | `headless` by default, or `obsidian` if the user wants Obsidian views now |
| 1.7 | Mode switching | `--enable-obsidian`, `--disable-obsidian`, `--relocate`, `--change-persona`, `--continue-setup` |
| 2 | Create workspace structure | Folders, _system files, workspace index cheat sheet, templates, scripts, and optional _views |
| 3 | Install Obsidian helper skills | Only in `obsidian` mode |
| 4 | Configure integrations | Deferred calendar provider and task manager selection |
| 5 | Initial context gathering | Fast identity first, optional people and initiatives later |
| 6 | Configure schedule | Briefing times and maintenance window |
| 7 | Register cron jobs | Daily briefing, weekly briefing, weekly maintenance |
| 8 | Initialize git | Repo init, .gitignore, initial commit |
| 9 | Welcome summary | Report, next steps, maturity update |

---

## Step 1: Pre-flight check

Check whether the workspace has already been set up.

**Detection**: Read `_system/config.md`. If it exists and contains a filled `tars-user-name` property:

> "TARS is already set up for {user_name}. Run health check? [Y/N]"

- **Y**: Route to `skills/maintain/` health check mode. Exit this skill.
- **N**: Ask: "Start fresh (overwrites config) or cancel?"
  - **Fresh**: Continue to Step 2. Existing memory/journal content is preserved.
  - **Cancel**: Exit.

If `_system/config.md` does not exist or has no user profile, proceed to Step 1.5.

For first-time setup, keep the first round to the essential questions only:

Before asking, determine and show:
- **Claude-selected folder**: the current working directory exposed to the session.
- **Active TARS workspace**: the path injected into the `tars-vault` MCP server, or the current folder if no explicit path is available.
- **Recommended default**: `~/Documents/TARS Workspace`.

Use "workspace" in user-facing copy. If Obsidian is enabled, add one sentence: "In Obsidian mode, this workspace is also your Obsidian vault."

> "Where should TARS store its local Markdown workspace? [active TARS workspace / ~/Documents/TARS Workspace / choose folder]"

If the user chooses a path that differs from the active MCP workspace path, do not scaffold into the wrong folder. Stop and say:

> "The active TARS MCP session is pointed at {active_path}, so I cannot safely create workspace files in {requested_path} from this session. Restart Claude with `TARS_VAULT_PATH` set to {requested_path}, or choose the active workspace for now."

If the active path is under `~/.claude` and there is no existing `_system/install.yaml`, warn and do not scaffold there by default:

> "This resolves under `~/.claude`, which is usually Claude app state, not a transparent TARS workspace. I recommend `~/Documents/TARS Workspace`."

Ask one compact identity/use-case question:

> "What should TARS know to personalize the workspace?
> - Your name:
> - Role/title:
> - Company or team:
> - First thing you want TARS to help with: meetings, inbox/documents, tasks, briefings, strategic thinking, stakeholder communication, or something else"

These fields are essential and should be captured before scaffolding. Everything
else is deferred unless the user asks for full setup now.

---

## Step 1.5: Pick a persona

Before scaffolding the workspace, one short question seeds sensible defaults so day 1 produces a useful briefing instead of an empty one. The answer is recorded in `_system/install.yaml` (written in Step 2b).

List the available personas under `templates/personas/` (use `Read` on the directory listing — do not invoke the MCP). Present them as a numbered multiple-choice question:

> "Which best matches your role? Pick the closest — you can change it later."
>
> 1. Product Leader — roadmap, customer signals, feature decisions
> 2. Sales / Customer-Facing — pipeline, accounts, deal motion
> 3. Delivery / Project Manager — schedule, scope, dependencies, RAID
> 4. Data Science / Analytics Lead — experiments, metrics, model drift
> 5. Architect / Staff Engineer — ADRs, RFCs, system design
> 6. Support / Operations Lead — incidents, SLAs, escalations
> 7. Engineering Manager — 1:1s, team health, hiring, delivery
> 8. None of these match — skip persona seeding

For the chosen persona, read the corresponding file under `templates/personas/<key>.md`. Parse the frontmatter to obtain:
- `tars-config-defaults` — applied to `_system/config.md` in Step 2b
- `tars-taxonomy-tags` — appended to `_system/taxonomy.md` in Step 2b
- `tars-briefing-sections` — written to `_system/config.md` as `tars-briefing-sections`

Cache the chosen `tars-persona-key` in skill state for use in Step 2b.

If the user picked option 8 ("None of these match"), skip persona-defaults application. The workspace scaffolds with stock defaults.

---

## Step 1.6: Choose workspace type

Ask one question:

> "How do you want to use this workspace now?
> 1. Headless Markdown workspace in Claude (recommended)
> 2. Obsidian workspace with live views"

Default to option 1. Record the result in skill state:

```yaml
workspace_type: headless | obsidian
obsidian_enabled: false | true
obsidian_vault_path: ""
```

Headless setup is fully functional for `/start`, `/meeting`, `/learn`, `/answer`, `/briefing`, `/think`, `/communicate`, `/create`, `/tasks`, `/lint`, and `/maintain`. Obsidian mode uses the same files and adds `.base` views plus optional helper skills.

---

## Step 1.7: Mode switching and focused maintenance

These modes do not run full onboarding unless explicitly stated. They do not overwrite memory, journal, context, integrations, or schedules.

### `/welcome --enable-obsidian`

Use when a headless user wants to browse the same workspace in Obsidian.

1. Read `_system/install.yaml`.
2. Confirm or collect `obsidian_vault_path`. Default to `workspace_path`.
3. Verify the path exists and contains the active workspace files.
4. Create or refresh `_views/*.base` files from the repo templates.
5. Copy or verify Obsidian helper skills in `.claude/skills/`.
6. Update `_system/install.yaml`:
   ```yaml
   workspace_type: obsidian
   obsidian_enabled: true
   obsidian_vault_path: "<confirmed path>"
   vault_path: "<workspace_path>"
   last_session_at: "<now>"
   ```
7. Exit with: "Obsidian enabled for this workspace. Existing memory, journal, schedules, and integrations were left untouched."

### `/welcome --disable-obsidian`

Use when an Obsidian user wants Claude-first operation.

1. Read `_system/install.yaml`.
2. Update only:
   ```yaml
   workspace_type: headless
   obsidian_enabled: false
   last_session_at: "<now>"
   ```
3. Leave existing `_views/*.base` files and Obsidian metadata untouched.
4. Exit with: "TARS is now headless. Existing data remains in the same workspace."

### `/welcome --relocate`

Use when the workspace folder has moved.

1. Read `_system/install.yaml`.
2. Compute the current workspace root from `TARS_VAULT_PATH`, the MCP server path, or the current folder.
3. Show old versus new `workspace_path` and `vault_path`.
4. Ask for confirmation.
5. Update only `workspace_path`, `vault_path`, and `last_session_at`. If `obsidian_enabled: true`, ask whether `obsidian_vault_path` should also be updated.
6. Run the pending migration check from the Step 7 tail.
7. Exit with a one-line success summary.

Do not re-scaffold the workspace. Do not ask onboarding questions. Do not rewrite `_system/config.md`.

### `/welcome --change-persona`

Use when the user wants a different role default.

1. Read current `persona` from `_system/install.yaml`.
2. Show the seven persona menu from Step 1.5, marking the current selection.
3. On selection, update only:
   - `_system/install.yaml` `persona`
   - `_system/config.md` persona-derived keys: `tars-bluf-level`, `tars-default-analysis-mode`, `tars-review-gate-strictness`, `tars-briefing-style`, `tars-briefing-sections`
4. Append one line to `_system/changelog/YYYY-MM-DD.md`.
5. Confirm: "Persona changed from X to Y. Existing identity, memory, schedule, and integrations were left untouched."

Do not touch `tars-user-name`, `tars-user-title`, `tars-user-company`, memory, journal, integrations, or scheduled jobs.

### `/welcome --continue-setup`

Use when the user wants to finish deferred setup after fast setup, or when they say "continue TARS setup", "finish TARS setup", "add integrations", "add people", "add initiatives", or "set up the rest".

1. Read `_system/maturity.yaml`.
2. Build a checklist from incomplete deferred modules:
   - Key people (`onboarding.steps.initial_people`)
   - Active initiatives (`onboarding.steps.initial_initiatives`)
   - Integrations (`onboarding.steps.integrations_configured`)
   - Schedule (`onboarding.steps.schedule_configured`)
   - Cron jobs (`onboarding.steps.cron_registered`)
   - Brand context (`deferred_setup.modules.brand`)
   - Maintenance preferences (`deferred_setup.modules.maintenance`)
   - Obsidian browsing (`deferred_setup.modules.obsidian_browsing`)
3. Show one compact menu:
   ```
   Deferred setup still available:
     1. Add key people
     2. Add active initiatives
     3. Connect calendar/tasks
     4. Configure briefings and maintenance
     5. Add brand context
     6. Enable Obsidian browsing
     7. Mark setup complete for now
   ```
4. Run only the selected modules. Do not rerun fast setup and do not rewrite identity, memory, journal, integrations, or schedules outside the selected module.
5. After each completed module, update `_system/maturity.yaml`.
6. If the user chooses "Mark setup complete for now", set `deferred_setup.dismissed: true`, keep `deferred_setup.completed: false`, and stop showing reminders until the user explicitly asks to continue setup again.

When all deferred modules are complete, set:
```yaml
deferred_setup:
  completed: true
  next_step: null
```
and confirm: "Deferred setup is complete. You can still change persona, integrations, schedule, or Obsidian mode later."

---

## Step 2: Create workspace structure

Create the complete workspace directory tree with the deterministic MCP scaffold
tool. Do not rely on ad hoc model-created folders.

Call:

```text
mcp__tars_vault__scaffold_workspace(
  workspace_type="<headless|obsidian>",
  user_name="<name from Step 1>",
  user_role="<role/title from Step 1>",
  company="<company/team from Step 1>",
  persona="<persona key from Step 1.5>",
  overwrite=false
)
```

The tool must return `status: ok`, `index_path: "index.md"`, `inbox_path:
"inbox/pending"`, and `memory_path: "memory"`. If it returns an error, stop and
surface the reason. Do not claim setup is complete.

After the tool succeeds, read back `index.md`, `_system/config.md`, and
`_system/install.yaml` with `mcp__tars_vault__read_note` to verify they exist.
If any read fails, stop and say setup is incomplete.

The expected full workspace structure is listed below for auditability.

### 2a: Directories

`scaffold_workspace` creates every directory in the workspace structure:

```
_system/
_system/changelog/
_system/backlog/
_system/backlog/issues/
_system/backlog/ideas/
_views/
memory/
memory/people/
memory/vendors/
memory/competitors/
memory/products/
memory/initiatives/
memory/decisions/
memory/org-context/
journal/
contexts/
contexts/products/
contexts/artifacts/
inbox/
inbox/pending/
inbox/processed/
archive/
archive/transcripts/
templates/
scripts/
skills/
.claude/
.claude/skills/
```

For each directory, the tool checks if it already exists before creating and
reports skipped directories.

### 2b: _system files

`scaffold_workspace` creates these first-run system files with default content:

**_system/config.md**
```yaml
---
tags: [tars/system]
tars-user-name: ""
tars-user-title: ""
tars-user-company: ""
tars-user-industry: ""
tars-user-org: ""
tars-calendar-provider: ""
tars-task-provider: ""
tars-daily-briefing-time: "07:30"
tars-daily-briefing-tz: "America/Chicago"
tars-weekly-briefing-day: "Monday"
tars-weekly-briefing-time: "08:00"
tars-maintenance-day: "Friday"
tars-maintenance-time: "17:00"
tars-created: YYYY-MM-DD
---

# TARS configuration

User profile and system preferences. Populated by onboarding wizard.
```

**_system/integrations.md**
```yaml
---
tags: [tars/system]
tars-created: YYYY-MM-DD
---

# Integration registry

Provider-agnostic integration configuration.

## Calendar

| Field | Value |
|-------|-------|
| Provider | (not configured) |
| MCP server | (not configured) |
| Status | pending |

## Tasks

| Field | Value |
|-------|-------|
| Provider | (not configured) |
| MCP server | (not configured) |
| Status | pending |
| Lists | Active, Delegated, Backlog |
```

**_system/alias-registry.md** -- Empty registry with header and table structure for name-to-canonical mappings.

**_system/taxonomy.md** -- Tag taxonomy and entity type definitions per the tag taxonomy table in the workspace structure spec.

**_system/kpis.md** -- Empty KPI template with instructions for adding metrics per team and initiative.

**_system/schedule.md** -- Empty schedule template with sections for recurring and one-time items.

**_system/guardrails.yaml** -- Default guardrails with block patterns (SSN, credit card, API key) and warn patterns (salary, compensation, performance rating).

**_system/maturity.yaml**
```yaml
onboarding:
  workspace_scaffold: false
  vault_structure: false
  workspace_type_selected: false
  obsidian_enabled: false
  obsidian_skills: false
  integrations: false
  user_profile: false
  schedule: false
  cron_jobs: false
  git_initialized: false
  completed: false
  completed_date: null
deferred_setup:
  available: true
  completed: false
  dismissed: false
  next_step: people
  last_reminded: null
  modules:
    people: false
    initiatives: false
    integrations: false
    schedule: false
    cron_jobs: false
    brand: false
    maintenance: false
    obsidian_browsing: false
last_updated: null
coaching:
  enabled: true
  frequency: restrained
  last_tip_shown: null
  last_tip_context: null
  dismissed_tips: []
  completed_milestones:
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
```

**index.md** -- Workspace cheat sheet created at the workspace root. It must say slash commands are shortcuts, not requirements, and include natural-language examples. Always link it in the chat summary after setup.

```markdown
# TARS workspace

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
```

**_system/housekeeping-state.yaml**
```yaml
last_run: null
last_success: null
run_count: 0
last_archival: null
pending_inbox_count: 0
cron_jobs:
  daily_briefing: null
  weekly_briefing: null
  maintenance: null
plugin_version: "3.0.0"
```

**_system/schemas.yaml** -- Frontmatter validation schemas for all entity types (person, vendor, competitor, product, initiative, decision, org-context, journal, task, transcript, companion). Each schema lists required and optional properties with types.

**_system/install.yaml** -- Workspace-specific install record. Use the `templates/install.yaml` shape and fill in:
- `workspace_type`: `headless` or `obsidian`.
- `workspace_path`: the absolute path to this workspace (the folder we just scaffolded). Hooks use this on every session start to detect a moved/duplicated workspace and refuse silent writes from a stale folder.
- `vault_path`: same value as `workspace_path` for backward compatibility.
- `obsidian_enabled`: true only when Obsidian is enabled.
- `obsidian_vault_path`: the Obsidian vault path when enabled, otherwise empty. In Obsidian mode, the TARS workspace is also the Obsidian vault.
- `installation_id`: a UUID generated once per install (use `python3 -c "import uuid; print(uuid.uuid4())"` via Bash, or any equivalent generator). Travels with telemetry events.
- `persona`: the `tars-persona-key` from Step 1.5, or empty string if the user picked "None of these match".
- `plugin_version`: read from `.claude-plugin/plugin.json` so /lint can detect stale installs that need migration.
- `created` and `last_session_at`: current ISO-8601 timestamp.

Write the file via `mcp__tars_vault__write_note_from_content(file="_system/install.yaml", content=…)`. Do not write secrets here — `install.yaml` is checked-in alongside the rest of `_system/`.

If a persona was chosen in Step 1.5a, also apply its `tars-config-defaults` to `_system/config.md` frontmatter (each key is `tars-*` so it merges cleanly), append its `tars-taxonomy-tags` under a new "Persona starter tags" subsection in `_system/taxonomy.md`, and write its `tars-briefing-sections` to `_system/config.md` as the `tars-briefing-sections` list. Stock fields the user has not yet provided (name, title, company) stay empty until Step 5.

### 2c: Templates

Create Obsidian templates in `templates/`:

| Template | Frontmatter tags | Key properties |
|----------|-----------------|----------------|
| person.md | `tars/person` | tars-role, tars-org, tars-relationship, aliases |
| vendor.md | `tars/vendor` | tars-category, tars-status, tars-contract-renewal |
| competitor.md | `tars/competitor` | tars-category, tars-threat-level |
| product.md | `tars/product` | tars-status, tars-owner |
| initiative.md | `tars/initiative` | tars-status, tars-owner, tars-health, tars-target-date |
| decision.md | `tars/decision` | tars-status, tars-decision-maker, tars-date |
| org-context.md | `tars/org-context` | tars-scope, tars-last-validated |
| meeting-journal.md | `tars/journal, tars/meeting` | tars-date, tars-meeting-datetime, tars-participants, tars-organizer, tars-topics, tars-initiatives, tars-source, tars-transcript |
| briefing.md | `tars/journal, tars/briefing` | tars-date, tars-briefing-type: daily\|weekly |
| wisdom-journal.md | `tars/journal, tars/wisdom` | tars-date, tars-source-title, tars-source-url |
| companion.md | `tars/companion` | tars-original-file, tars-original-type, tars-file-size, tars-added-date, tars-source, tars-summary |
| transcript.md | `tars/transcript` | tars-journal-entry, tars-date, tars-meeting-datetime, tars-participants, tars-format |
| backlog-item.md | `tars/backlog, tars/{issue\|idea}` | tars-backlog-type: issue\|idea, tars-status |

Each template should include the full frontmatter block with placeholder values and a minimal body structure appropriate to the entity type.

### 2d: _views base files

Create `.base` files in `_views/` only when `workspace_type: obsidian` or when running `/welcome --enable-obsidian`. In headless mode, skip this step and mark `_system/maturity.yaml` `onboarding.obsidian_enabled: false`. Each .base file is a YAML-formatted Obsidian Bases live query.

| Base file | Query filter | Columns |
|-----------|-------------|---------|
| all-people.base | `tags contains tars/person` | Name, Role, Org, Last updated, Staleness formula |
| all-initiatives.base | `tags contains tars/initiative` | Name, Status, Owner, Health, Target date |
| all-decisions.base | `tags contains tars/decision` | Name, Date, Status, Decision maker |
| all-products.base | `tags contains tars/product` | Name, Status, Owner |
| all-vendors.base | `tags contains tars/vendor` | Name, Category, Status, Contract renewal |
| all-competitors.base | `tags contains tars/competitor` | Name, Category, Threat level |
| recent-journal.base | `tags contains tars/journal` | Date, Type, Title, Participants (last 30d filter) |
| active-tasks.base | `tags contains tars/task AND tars-status = open` | Title, Owner, Due, Priority, Initiative |
| overdue-tasks.base | `tags contains tars/task AND tars-due < today()` | Title, Owner, Due, Days overdue |
| stale-memory.base | Formula: days since tars-updated > staleness threshold | Name, Type, Last updated, Days stale |
| inbox-pending.base | `tags contains tars/inbox AND tars-inbox-processed != true` | Name, Type, Added date |
| all-documents.base | `tags contains tars/companion` | Name, Original file, Type, Added date, Summary |
| all-transcripts.base | `tags contains tars/transcript` | Name, Journal entry, Date, Format |
| flagged-content.base | `tags contains tars/flagged` | Person, Statement, Date flagged, Age |
| backlog.base | `tags contains tars/backlog` | Type, Severity/Priority, Status, Description |

Refer to the obsidian-bases skill (`obsidian-bases/SKILL.md`) for exact .base YAML syntax.

### 2e: Scripts

Create the following Python scripts in `scripts/`:

| Script | Purpose |
|--------|---------|
| validate-schema.py | Validates frontmatter against _system/schemas.yaml |
| scan-secrets.py | Scans for blocked/warned patterns from _system/guardrails.yaml |
| health-check.py | Comprehensive: schema + links + aliases + staleness + flagged-content sub-check |
| archive.py | Staleness-based archival with `--auto` and `--dry-run` flags |
| sync.py | Calendar gap detection + task system drift check |

Each script should:
- Accept the workspace path as first argument
- Output JSON to stdout
- Exit 0 on success, 1 on error
- Read configuration from `_system/` files
- Never modify files directly (output recommendations for the agent to apply via `mcp__tars_vault__*`)

After creating all structure, `scaffold_workspace` updates `_system/maturity.yaml`:
```yaml
onboarding:
  workspace_scaffold: true
  vault_structure: true
  workspace_type_selected: true
```

---

## Step 3: Install Obsidian helper skills

Skip this step in `headless` mode. Copy or verify the following Obsidian helper skills are present in `.claude/skills/` only in `obsidian` mode:

| Skill | Path | Contents |
|-------|------|----------|
| obsidian-cli | `.claude/skills/obsidian-cli/SKILL.md` | Optional Obsidian administration helper |
| obsidian-bases | `.claude/skills/obsidian-bases/SKILL.md` + `references/` | .base file creation and querying |
| obsidian-markdown | `.claude/skills/obsidian-markdown/SKILL.md` + `references/` | Markdown and frontmatter conventions |
| json-canvas | `.claude/skills/json-canvas/SKILL.md` + `references/` | Canvas file creation |

### Installation procedure

1. Check if each skill directory exists and contains SKILL.md
2. If missing, copy from the TARS source tree (this repo's skill definitions)
3. If already present, verify file is not empty and report as "verified"
4. Report installation status for each skill

After installation, update `_system/maturity.yaml`:
```yaml
onboarding:
  obsidian_skills: true
```

---

## Step 4: Configure integrations

This is deferred setup. Offer it after fast setup, in Daily Digest coaching, or when the user explicitly asks for richer briefings. Present integration choices using multiple-choice questions. Ask both in a single interaction round.

### Calendar provider

> "Calendar provider?
>   1. Apple Calendar
>   2. Google Calendar
>   3. Outlook / Microsoft 365
>   4. None for now"

### Task manager

> "Task manager?
>   1. Apple Reminders
>   2. Todoist
>   3. Linear
>   4. None for now"

### Save selections

For each configured integration:

1. Update `_system/integrations.md` with provider name, expected MCP server, and status
2. Update `_system/config.md` properties: `tars-calendar-provider`, `tars-task-provider`

### Verify connectivity

For each selected integration (not "None"):

1. Attempt a test query via the expected MCP tool:
   - Calendar: list events for today
   - Tasks: list all task lists
2. Report status:
   - Connected: "Calendar: Apple Calendar (connected)"
   - Error: "Calendar: Apple Calendar (MCP server not responding). Add to .mcp.json and restart Claude."
   - Not configured: "Calendar: None selected"

### MCP setup guidance

If any integration fails connectivity or user selects "None":

> "TARS needs calendar access for briefings, meeting context, and schedule queries.
> TARS needs task manager access for action item creation and tracking.
>
> To configure later:
> 1. Add the MCP server to your .mcp.json
> 2. Restart Claude
> 3. Run 'setup' again to verify
>
> Continue with reduced functionality? [Y/N]"

- **Y**: Proceed to Step 5
- **N**: Display .mcp.json examples and exit

### .mcp.json examples

```json
{
  "mcpServers": {
    "apple-calendar": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/apple-calendar-mcp"]
    },
    "apple-reminders": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/apple-reminders-mcp"]
    }
  }
}
```

After configuration, update `_system/maturity.yaml`:
```yaml
onboarding:
  integrations: true
```

---

## Step 5: Initial context gathering

Progressive context gathering. Do not ask everything at once. Each round is a bounded set of questions (max 3 per round). Use multiple-choice where possible. Run all four rounds for every user — rounds 3-4 have a skip/escape option if the user doesn't have the information handy yet.

### Round 1: Identity

> "What's your name and role?"

Single open question. Parse response for:
- Full name
- Title/role
- Optional: company name if mentioned

Save to `_system/config.md`: `tars-user-name`, `tars-user-title`

### Round 2: Organization

> "What organization or team are you part of? And what industry?"

Parse response for:
- Company/organization name
- Team name(s)
- Industry

Save to `_system/config.md`: `tars-user-company`, `tars-user-industry`, `tars-user-org`

Create `memory/org-context/` note for the organization using the org-context template.

### Round 3: Key people (deferred)

> "Name 3-5 people you work with most. For each, give their name and role (e.g., 'Sarah Chen, VP Engineering')."

For each person mentioned:
1. Create a person note in `memory/people/` using the person template:
   ```
   mcp__tars_vault__create_note(
     name="{name}",
     path="memory/people/{slug}.md",
     template="person",
     frontmatter={"tags": ["tars/person"], "tars-role": "{role}", "tars-created": "YYYY-MM-DD"}
   )
   ```
2. Set basic properties: name, role, relationship to user (via additional `tars-` fields).
3. Add aliases if nicknames are mentioned.
4. The MCP server adds the entry to `_system/alias-registry.md` automatically on `create_note`.

### Round 4: Active initiatives (deferred)

> "What are your main projects or initiatives right now? (Name and one-line description for each)"

For each initiative mentioned:
1. Create an initiative note in `memory/initiatives/` using the initiative template:
   ```
   mcp__tars_vault__create_note(
     name="{name}",
     path="memory/initiatives/{slug}.md",
     template="initiative",
     frontmatter={
       "tags": ["tars/initiative"],
       "tars-owner": "[[{user_name}]]",
       "tars-status": "active",
       "tars-created": "YYYY-MM-DD"
     }
   )
   ```
2. Set owner (default: user), status: active.

After gathering, update `_system/maturity.yaml`:
```yaml
onboarding:
  user_profile: true
  steps:
    initial_people: true
    initial_initiatives: true
deferred_setup:
  modules:
    people: true
    initiatives: true
```

---

## Step 6: Configure schedule

Ask for schedule preferences with sensible defaults. All three questions are presented to every user — the cron jobs registered in Step 7 honor these times.

> "When would you like your daily briefing? [default: 7:30am CT]"

> "Weekly briefing day and time? [default: Monday 8:00am CT]"

> "Maintenance window? [default: Friday 5:00pm CT — note: the weekly-maintenance cron registered in Step 7 fires Sunday 18:00 by default; this field configures the on-demand `/maintain` window]"

Accept natural language time inputs. Resolve to 24-hour format and timezone.

Save to `_system/config.md`:
- `tars-daily-briefing-time`: "07:30"
- `tars-daily-briefing-tz`: "America/Chicago"
- `tars-weekly-briefing-day`: "Monday"
- `tars-weekly-briefing-time`: "08:00"
- `tars-maintenance-day`: "Friday"
- `tars-maintenance-time`: "17:00"

Update `_system/maturity.yaml`:
```yaml
onboarding:
  schedule: true
  steps:
    schedule_configured: true
deferred_setup:
  modules:
    schedule: true
```

---

## Step 7: Register cron jobs

Claude does not run in the background; cron jobs are the only path to truly proactive behavior. Offer all four jobs to every user — skipping any of them is the user's choice, not a mode gate.

### Step 7a: Detect available scheduler(s)

```
result = mcp__tars_vault__resolve_capability(capability="scheduler")
```

This returns `available` (list of schedulers present) and `preferred` (recommended pick).  Read the `note` field — it will explicitly warn when both schedulers are active on the same machine.

**Available schedulers:**
| Scheduler | Persistence | Visibility | Expiry |
|-----------|-------------|------------|--------|
| `mcp__scheduled-tasks` | Persistent MCP server | Claude Code only | None |
| `CronCreate` | Built-in Claude tool | Claude Code + Cowork | ~7 days |

**Preferred**: `mcp__scheduled-tasks` when available (no TTL, no weekly re-registration). Otherwise `CronCreate`.

### Step 7b: Mutual-exclusion check (CRITICAL)

Before registering any job, read the current `_system/housekeeping-state.yaml` `cron_jobs` block.

For each job you are about to register:
1. Read `scheduler_type` for that job.
2. If `scheduler_type` is set (not null) and `status` is `registered`:
   - **The job is already registered with that scheduler. DO NOT register with any other scheduler.**
   - If the registered scheduler is the same as the one you're about to use → proceed to re-registration check only.
   - If the registered scheduler differs from the one you're about to use → skip registration entirely for this job. Surface a notice: "Job `<name>` is already registered with `<current_scheduler>`. To switch schedulers, use `/maintain --re-register`."
3. If `scheduler_type` is null or `status` is `not_registered` → proceed to Step 7c.

This rule prevents duplicate execution on machines where both Claude Desktop (Cowork) and Claude Code are active simultaneously.

### Step 7c: Confirm-before-run preference

Before registering, ask the user about confirm-before-run behavior (one question, not per-job):

> "When a scheduled job fires, should TARS:
>   [1] Run automatically (default — no interruption)
>   [2] Ask me first — show pending jobs and let me accept, skip, or postpone each one"

Store the answer as the global default. Users can override per-job later. If the user picks option 2, set `confirm_before_run: true` for all jobs being registered now. Also ask:

> "If you don't respond within [4] hours, should TARS: [1] Run anyway  [2] Skip for today"

Store as `auto_timeout_hours` (default 4) and `auto_timeout_action` (`run` | `skip`).

The default is `confirm_before_run: false` (auto-run) — this preserves behavior for users who don't want interruptions. Recommend option 2 to users who want control over when reports land.

### Step 7d: Register each job

Register all four jobs (`tars-daily-briefing`, `tars-weekly-briefing`, `tars-weekly-maintenance`, `tars-nightly-lint`) for every user. Present each as opt-in with a single confirm (e.g. "Register daily briefing at 7:30am CT? [Y/n]") — the default is yes. Users who decline a job can register it later via `/welcome` or manually.

For each job, choose the cron command based on `confirm_before_run`:

| confirm_before_run | Command |
|--------------------|---------|
| false (auto-run) | `"Run <job_name>"` — e.g. `"Run /briefing"` |
| true (confirm first) | `"TARS scheduled: <job_name> is due. Accept, skip, or postpone?"` |

#### Daily briefing

**With `mcp__scheduled-tasks`:**
```
mcp__scheduled_tasks__create_task(
  name: "tars-daily-briefing",
  schedule: "<cron_expression>",
  prompt: "<command per confirm_before_run setting above>"
)
```

**With `CronCreate`:**
```
CronCreate:
  name: "tars-daily-briefing"
  schedule: "<cron_expression>"
  command: "<command per confirm_before_run setting above>"
  description: "TARS daily briefing"
```

#### Weekly briefing

Register with the same scheduler type as `daily_briefing`. Never mix schedulers across jobs — pick one and use it for all.

```
name: "tars-weekly-briefing"
schedule: "<Monday HH:MM cron>"
command: "<command per confirm_before_run>"
```

#### Weekly maintenance

```
name: "tars-weekly-maintenance"
schedule: "0 18 * * 0"  # Sunday 18:00 local
command: "<command per confirm_before_run>"
```

#### Nightly lint

```
name: "tars-nightly-lint"
schedule: "0 2 * * *"   # 2:00am local
command: "Run /lint --quiet"   # lint always auto-runs; confirm_before_run not applied
```

### Step 7e: Store job state

After each successful registration, write to `_system/housekeeping-state.yaml` immediately (do not batch — if a later job fails, earlier ones are preserved):

```yaml
cron_jobs:
  daily_briefing:
    id: "{returned_job_id}"
    scheduler_type: "{mcp__scheduled-tasks|CronCreate}"
    schedule: "{cron_expression}"
    status: registered
    confirm_before_run: {true|false}
    auto_timeout_hours: {N}
    auto_timeout_action: "{run|skip}"
    cron_create_registered_at: "{ISO-8601}"  # only for CronCreate
  weekly_briefing:
    ...  # same fields; null if user declined during onboarding
```

Also update `_system/schedule.md` table row for each registered job (Scheduler column, Job ID column, Registered At column).

Record the chosen scheduler type in `_system/install.yaml`:
```yaml
scheduler_type: "{mcp__scheduled-tasks|CronCreate}"
```

If no scheduler is available at all:
- Log `status: not_registered` for all jobs
- Inform user: "No scheduler available — briefings won't fire automatically. You can run them manually anytime."
- Note that session-start housekeeping serves as the only trigger

### Migration check (Step 7 tail)

After recording job IDs, check whether any migrations are pending:

```bash
python3 scripts/run-migrations.py --vault $TARS_VAULT_PATH --list
```

If pending migrations are found:
1. Surface a notice: "N pending migration(s) need to run to bring your workspace up to plugin version X.X.X."
2. Offer to run them now: "Run migrations now? [Y/n — recommended for fresh onboarding]"
3. If accepted: run `python3 scripts/run-migrations.py --vault $TARS_VAULT_PATH --dry-run`, show the plan, then confirm before `--apply`.
4. On success, `plugin_version` in housekeeping-state.yaml advances automatically.
5. If declined: remind user they can run `/maintain migrations` at any time.

For an existing workspace being re-onboarded (user ran /welcome --relocate or upgrade):
- Always run the migration check — the workspace may be multiple versions behind.
- Apply migrations before completing onboarding so the workspace is schema-current before first use.

Update `_system/maturity.yaml`:
```yaml
onboarding:
  cron_jobs: true  # or false if skipped
  migrations_applied: true  # or false if skipped/deferred
```

---

## Step 8: Initialize git

### Check existing repo

```bash
git status
```

If already a git repo, skip `git init`.

### Create .gitignore

```
# Obsidian workspace (user-specific, not shareable)
.obsidian/workspace*
.obsidian/graph.json
.obsidian/app.json

# OS files
.DS_Store
Thumbs.db

# Sensitive
.env
*.key
*.pem

# Lock files (transient)
*.lock
```

### Initial commit

```bash
git init  # if needed
git add -A
git commit -m "Initialize TARS workspace structure

Created by TARS onboarding wizard.
Includes: workspace structure, templates, _views, scripts, _system config, obsidian-skills."
```

Update `_system/maturity.yaml`:
```yaml
onboarding:
  git_initialized: true
```

---

## Step 9: Welcome summary

Display a comprehensive summary of what was configured.

```markdown
## TARS setup complete

### Workspace structure
- _system/: {N} config files created
- _views/: {N} base queries created
- templates/: {N} templates created
- scripts/: {N} validation scripts created
- memory/: {N} entity folders ready
- journal/: ready
- contexts/: ready (products, artifacts)
- inbox/: ready (pending, processed)
- archive/: ready
- index.md: workspace cheat sheet created

### Obsidian skills
- Obsidian helper skills: {installed | verified | skipped in headless mode}
- obsidian-bases: {installed | verified | missing}
- obsidian-markdown: {installed | verified | missing}
- json-canvas: {installed | verified | missing}

### Integrations
- Calendar: {provider} ({connected | error | not configured})
- Tasks: {provider} ({connected | error | not configured})

### User profile
- Name: {user_name}
- Role: {user_title}
- Organization: {company}

### Context created
- People: {N} profiles created
- Initiatives: {N} initiatives created
- Org context: {N} notes created

### Scheduled jobs
- Daily briefing: {time} {tz} ({registered | skipped})
- Weekly briefing: {day} {time} ({registered | skipped})
- Maintenance: {day} {time} ({registered | skipped})

### Git
- Repository: {initialized | already existed}
- Initial commit: {hash}

### Next steps
1. Run "daily briefing" to see your first morning briefing.
2. Drop transcripts, PDFs, decks, docs, screenshots, exports, or rough notes into `inbox/pending/`, then say "process inbox". TARS can process the folder in bulk.
3. Continue deferred setup with `/welcome --continue-setup` or say "continue TARS setup" when you want to add people, initiatives, integrations, schedule, brand, maintenance, or optional Obsidian browsing.
4. Ask "help" to see all available TARS capabilities. Slash commands are shortcuts; natural-language requests work too.
5. Add more people and context as you use TARS. Reviewed self-learning proposals appear through `/learn --review-patterns` and weekly maintenance; nothing is auto-applied.
```

After the summary, link the cheat sheet and offer a guided first demo. Do not
leave the user on their own.

> "Your cheat sheet is `index.md` in the workspace root. Slash commands are optional; you can ask in natural language."

Ask:

> "Want to see TARS do something useful right now? Paste a transcript, report,
> PDF/deck excerpt, customer call notes, email thread, or rough notes. I’ll
> preview what TARS would extract before saving anything. If you already have
> files, drop them in `inbox/pending/` and say 'process inbox'."

If the user has nothing handy, offer the three example files from `examples/`
and route them through `/start` preview-only.

Update `_system/maturity.yaml`:
```yaml
onboarding:
  completed: true  # fast setup complete
  completed_date: YYYY-MM-DD
deferred_setup:
  available: true
  completed: false  # until /welcome --continue-setup modules are complete
  next_step: people
last_updated: YYYY-MM-DD
```

---

## Error handling

| Failure | Recovery |
|---------|----------|
| Directory creation fails | Log error, continue with remaining directories, report at end |
| Obsidian not available | Continue in headless mode and offer `/welcome --enable-obsidian` later |
| MCP server not responding | Mark integration as "error", continue setup, user can re-run later |
| CronCreate unavailable | Skip cron registration, rely on session-start fallback |
| Git init fails | Log error, continue, user can initialize manually |
| User cancels mid-setup | Save progress to _system/maturity.yaml, user can resume with `/welcome --continue-setup` or "continue TARS setup" |

### Resume capability

If the user runs "setup" after a partial completion:
1. Read `_system/maturity.yaml`
2. Skip steps marked `true`
3. Resume from the first `false` step
4. Report: "Resuming setup from Step {N}: {step_name}"

If the user completed fast setup but deferred modules remain, route "setup", "continue setup", and `/welcome --continue-setup` to Step 1.7 `/welcome --continue-setup`.

---

## Absolute constraints

- NEVER skip the pre-flight check (Step 1)
- NEVER overwrite existing memory, journal, or context files during setup
- NEVER persist user data without confirmation
- NEVER create task integration entries without verified connectivity
- NEVER commit sensitive data (.env, API keys) to git
- ALWAYS use `mcp__tars_vault__*` tools for note creation
- ALWAYS validate integration connectivity before marking as "connected"
- ALWAYS save progress to maturity.yaml after each step
- ALWAYS leave an obvious path to continue deferred setup after fast setup
- ALWAYS use bounded questions (multiple-choice, max 3-4 per round)
- ALWAYS include a skip/escape option for optional configuration

---

## Context budget

- _system/ files: Read all during pre-flight check
- Templates: Write-only during creation (no reads needed)
- Memory: Write-only during person/initiative creation
- obsidian-skills: Read SKILL.md header only to verify installation
- No journal, contexts, or archive reads during onboarding
