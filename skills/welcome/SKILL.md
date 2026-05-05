---
name: welcome
description: Onboarding wizard that scaffolds the vault structure, installs obsidian-skills, configures integrations, gathers user context, registers scheduled jobs, and initializes git
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
    Interactive first-run workspace setup. Creates vault scaffolding, installs obsidian-skills,
    configures integrations, gathers user context progressively, registers cron jobs for
    briefings and maintenance, and initializes git.
  use_cases:
    - "Set up TARS"
    - "Bootstrap my workspace"
    - "Initialize TARS"
    - "Run onboarding"
  scope: setup,bootstrap,onboarding,welcome,initialize
---

# Welcome: onboarding wizard

Interactive first-run setup for TARS v3. Creates the full vault structure, installs obsidian-skills,
configures integrations, gathers user context progressively, registers scheduled jobs, and
initializes git. This skill replaces both `install.sh` and the legacy `/welcome` command.

### v3.1 pre-flight additions

- Verify `tars-vault` MCP server is reachable (`mcp__tars_vault__read_note(file="schemas")` should succeed). If not, guide user through `.mcp.json` entry: `{"tars-vault": {"type": "stdio", "command": "python3", "args": ["-m", "tars_vault"]}}`.
- Confirm plugin hooks (`session-start.py`, `pre-tool-use.py`, `post-tool-use.py`, `pre-compact.py`, `session-end.py`, `instructions-loaded.py`) are registered.
- Run `scripts/githooks/install-githooks.sh` to enforce authorship rules locally.
- **Anthropic first-party skills probe (§8.10.1)**: detect which of `pptx`, `docx`, `xlsx`, `pdf`, `web-artifacts-builder` are available in the host Claude Code install. Read the user-invocable skills list surfaced in `<system-reminder>` blocks; do not programmatically load or inspect third-party skill packages. Persist the result in `_system/config.md` frontmatter as `tars-anthropic-skills: [pptx, docx, xlsx, pdf, web-artifacts-builder]` (include only those available). `/create` reads this at session start instead of reprobing.
- Integration discovery: `mcp__tars_vault__refresh_integrations()` writes `_system/tools-registry.yaml` so `resolve_capability` works from the first session.
- **Brand-guidelines scaffold (§5.1)**: if the user plans to use `/create` or `/communicate` for branded artifacts, offer to scaffold a brand file from `templates/brand-guidelines.md` → `contexts/brand/<brand-name>-brand-guidelines.md` (tagged `tars/brand`, frontmatter `tars-brand: true`). Cache the active brand as `tars-active-brand: <filename>` in `_system/config.md`.

---

## Pipeline overview

| Step | Name | Purpose |
|------|------|---------|
| 1 | Pre-flight check | Detect existing vault, offer resume or fresh start |
| 1.5 | Pick a persona | Seed role-appropriate defaults for briefings and analysis |
| 2 | Create vault structure | All folders, _system files (incl. `install.yaml` with persona), templates, _views, scripts |
| 3 | Install obsidian-skills | Copy/verify skills into .claude/skills/ |
| 4 | Configure integrations | Calendar provider, task manager selection |
| 5 | Initial context gathering | Progressive user profiling (4 rounds) |
| 6 | Configure schedule | Briefing times and maintenance window |
| 7 | Register cron jobs | Daily briefing, weekly briefing, weekly maintenance |
| 8 | Initialize git | Repo init, .gitignore, initial commit |
| 9 | Welcome summary | Report, next steps, maturity update |

---

## Step 1: Pre-flight check

Check whether the vault has already been set up.

**Detection**: Read `_system/config.md`. If it exists and contains a filled `tars-user-name` property:

> "TARS is already set up for {user_name}. Run health check? [Y/N]"

- **Y**: Route to `skills/maintain/` health check mode. Exit this skill.
- **N**: Ask: "Start fresh (overwrites config) or cancel?"
  - **Fresh**: Continue to Step 2. Existing memory/journal content is preserved.
  - **Cancel**: Exit.

If `_system/config.md` does not exist or has no user profile, proceed to Step 1.5.

---

## Step 1.5: Pick a persona

Before scaffolding the vault, one short question seeds sensible defaults so day 1 produces a useful briefing instead of an empty one. The answer is recorded in `_system/install.yaml` (written in Step 2b).

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

If the user picked option 8 ("None of these match"), skip persona-defaults application. The vault scaffolds with stock defaults.

---

## Step 2: Create vault structure

Create the complete vault directory tree. Use `mcp__tars_vault__create_note` for all note creation (the server wraps obsidian-cli). Use filesystem tools only for creating empty directories.

### 2a: Directories

Create every directory in the vault structure:

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

For each directory, check if it already exists before creating. Report skipped directories.

### 2b: _system files

Create the following system files with default content:

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

**_system/taxonomy.md** -- Tag taxonomy and entity type definitions per the tag taxonomy table in the vault structure spec.

**_system/kpis.md** -- Empty KPI template with instructions for adding metrics per team and initiative.

**_system/schedule.md** -- Empty schedule template with sections for recurring and one-time items.

**_system/guardrails.yaml** -- Default guardrails with block patterns (SSN, credit card, API key) and warn patterns (salary, compensation, performance rating).

**_system/maturity.yaml**
```yaml
onboarding:
  vault_structure: false
  obsidian_skills: false
  integrations: false
  user_profile: false
  schedule: false
  cron_jobs: false
  git_initialized: false
  completed: false
  completed_date: null
last_updated: null
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

**_system/install.yaml** -- Vault-specific install record. Use the `templates/install.yaml` shape and fill in:
- `vault_path`: the absolute path to this vault (the folder we just scaffolded). Hooks use this on every session start to detect a moved/duplicated vault and refuse silent writes from a stale folder.
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

Create `.base` files in `_views/`. Each .base file is a YAML-formatted Obsidian Bases live query.

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
- Accept the vault path as first argument
- Output JSON to stdout
- Exit 0 on success, 1 on error
- Read configuration from `_system/` files
- Never modify files directly (output recommendations for the agent to apply via obsidian-cli)

After creating all structure, update `_system/maturity.yaml`:
```yaml
onboarding:
  vault_structure: true
```

---

## Step 3: Install obsidian-skills

Copy or verify the following obsidian-skills are present in `.claude/skills/`:

| Skill | Path | Contents |
|-------|------|----------|
| obsidian-cli | `.claude/skills/obsidian-cli/SKILL.md` | CLI tool for all vault writes |
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

Present integration choices using multiple-choice questions. Ask both in a single interaction round.

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

### Round 3: Key people

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

### Round 4: Active initiatives

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
1. Surface a notice: "N pending migration(s) need to run to bring your vault up to plugin version X.X.X."
2. Offer to run them now: "Run migrations now? [Y/n — recommended for fresh onboarding]"
3. If accepted: run `python3 scripts/run-migrations.py --vault $TARS_VAULT_PATH --dry-run`, show the plan, then confirm before `--apply`.
4. On success, `plugin_version` in housekeeping-state.yaml advances automatically.
5. If declined: remind user they can run `/maintain migrations` at any time.

For an existing vault being re-onboarded (user ran /welcome --relocate or upgrade):
- Always run the migration check — the vault may be multiple versions behind.
- Apply migrations before completing onboarding so the vault is schema-current before first use.

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
git commit -m "Initialize TARS v3 vault structure

Created by TARS onboarding wizard.
Includes: vault structure, templates, _views, scripts, _system config, obsidian-skills."
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
## TARS v3 setup complete

### Vault structure
- _system/: {N} config files created
- _views/: {N} base queries created
- templates/: {N} templates created
- scripts/: {N} validation scripts created
- memory/: {N} entity folders ready
- journal/: ready
- contexts/: ready (products, artifacts)
- inbox/: ready (pending, processed)
- archive/: ready

### Obsidian skills
- obsidian-cli: {installed | verified | missing}
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
1. Run "daily briefing" to see your first morning briefing
2. Drop a meeting transcript into inbox/pending/ and run "process inbox"
3. Ask "help" to see all available TARS capabilities
4. Edit _system/kpis.md to define your team metrics
5. Add more people and context as you use TARS -- it learns as you go
```

Update `_system/maturity.yaml`:
```yaml
onboarding:
  completed: true
  completed_date: YYYY-MM-DD
last_updated: YYYY-MM-DD
```

---

## Error handling

| Failure | Recovery |
|---------|----------|
| Directory creation fails | Log error, continue with remaining directories, report at end |
| obsidian-cli not available | Fall back to direct file creation with warning that Obsidian cache may be stale |
| MCP server not responding | Mark integration as "error", continue setup, user can re-run later |
| CronCreate unavailable | Skip cron registration, rely on session-start fallback |
| Git init fails | Log error, continue, user can initialize manually |
| User cancels mid-setup | Save progress to _system/maturity.yaml, user can resume with "setup" |

### Resume capability

If the user runs "setup" after a partial completion:
1. Read `_system/maturity.yaml`
2. Skip steps marked `true`
3. Resume from the first `false` step
4. Report: "Resuming setup from Step {N}: {step_name}"

---

## Absolute constraints

- NEVER skip the pre-flight check (Step 1)
- NEVER overwrite existing memory, journal, or context files during setup
- NEVER persist user data without confirmation
- NEVER create task integration entries without verified connectivity
- NEVER commit sensitive data (.env, API keys) to git
- ALWAYS use obsidian-cli for note creation when available
- ALWAYS validate integration connectivity before marking as "connected"
- ALWAYS save progress to maturity.yaml after each step
- ALWAYS use bounded questions (multiple-choice, max 3-4 per round)
- ALWAYS include a skip/escape option for optional configuration

---

## Context budget

- _system/ files: Read all during pre-flight check
- Templates: Write-only during creation (no reads needed)
- Memory: Write-only during person/initiative creation
- obsidian-skills: Read SKILL.md header only to verify installation
- No journal, contexts, or archive reads during onboarding
