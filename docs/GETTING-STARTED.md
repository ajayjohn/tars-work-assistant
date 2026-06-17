<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# Getting Started with TARS

TARS is a persistent work assistant for Claude. The setup goal is straightforward: point TARS at a local Markdown folder and let `/welcome` create the workspace so daily work can begin immediately. TARS includes one required local helper, `tars-vault`, that runs locally and keeps workspace writes safe. Obsidian is optional and can be enabled later.

## Before you install

You need:
- Python 3.10+ available on the path
- Claude Code or Claude Cowork with the TARS framework installed
- a local folder dedicated to your TARS workspace, recommended default: `~/Documents/TARS Workspace`
- optional: Obsidian Desktop if you want live `.base` views and visual note browsing

Markdown files are plain text files you can open in any text editor. If you do
not know what Obsidian is, leave it disabled during setup. You can turn it on later.

If you are starting fresh, create an empty folder. This branch supports fresh v3.7 workspaces; legacy v3.0-v3.3 migration tooling is no longer part of the active framework.

## Installation

Install from your preferred path:

1. Marketplace install:
   - add the repository as a marketplace source in Cowork
   - install `tars`
2. Local install:
   - clone the repository
   - install the plugin from the local checkout

After installing the plugin from a local checkout, no third-party Python package is required for first setup. `requirements.txt` is intentionally empty of runtime pins.

Semantic search enhancements are optional:

```text
pip install -r requirements-search.txt
```

If you skip the optional search packages, setup, workspace writes, inbox processing, keyword search, and daily use still work. Semantic search falls back to FTS-only retrieval and surfaces that gap in the answer.

TARS does NOT bundle any office-rendering libraries. Office output in `/create` delegates to Anthropic's first-party `pptx` / `docx` / `xlsx` / `pdf` skills.

The plugin ships the local TARS helper configuration. In code checkout flows, set `TARS_VAULT_PATH` in your shell or IDE environment to point at your workspace before starting Claude Code, so the helper knows where to operate. The helper fails closed when it cannot resolve a real TARS workspace; it will not silently use a random current directory.

The repository contains the framework source. The folder you point TARS at is the live runtime workspace. Claude exposes the current plugin package location through `${CLAUDE_PLUGIN_ROOT}` for framework hooks and helper scripts, but that path is dynamic and is not used for workspace extensions. Extensions always live under the recorded workspace path in `extensions/` and are tracked by `_system/extensions.yaml`.

If setup behaves strangely, run the lightweight doctor from the framework checkout:

```text
python3 scripts/doctor.py --workspace ~/Documents/TARS\ Workspace
```

It checks Python, the bundled local helper, the resolved workspace path, write permissions, and install-record consistency. If Python itself is missing, install Python 3.10+ first, then rerun the check.

## First-run setup

Run `/welcome` to create the workspace and start the guided first-run flow.

The welcome flow:
- shows the Claude-selected folder and active TARS workspace so files are not silently created somewhere else
- asks for a workspace folder, your name, role/title, company/team, persona, and workspace type
- asks you to **pick a persona** (Product Leader, Sales / Customer-Facing, Delivery / PM, Data Science Lead, Architect / Staff Eng, Support / Ops Lead, Engineering Manager) so day-1 briefings are role-aware instead of empty
- creates the TARS workspace structure
- writes `_system/` files (including `install.yaml`), templates, scripts, `index.md`, and optional Obsidian views only when Obsidian mode is enabled
- creates `extensions/` plus `_system/extensions.yaml` so provider adapters and other extension packs have one safe workspace-owned location
- records the live plugin version in install and housekeeping state so fresh workspaces do not see false migration prompts
- captures your initial profile
- asks you to paste or upload a meeting transcript, PDF/report excerpt, email thread, or rough notes so TARS can preview extraction into memory candidates, journal notes, and tasks

Fast setup intentionally stops there. Continue deeper setup later with:

```text
/welcome --continue-setup
```

or say "continue TARS setup." That deferred path covers key people, active initiatives, integrations, schedules, brand context, maintenance, and optional Obsidian browsing. TARS also reminds you lightly in Daily Digest/help until you finish, dismiss the reminder, or turn coaching off.

After setup, the workspace should contain:

```text
_system/
  activity-ledger.yaml
memory/
journal/
contexts/
extensions/
inbox/pending/
inbox/processed/
archive/transcripts/
archive/inbox/
archive/tasks/
tasks/
templates/
scripts/
index.md
```

Obsidian mode adds `_views/` in the same workspace folder.

## Workspace modes

TARS now supports two workspace types:

- `headless`: the default. Claude works against a local Markdown workspace.
- `obsidian`: the same workspace plus optional Obsidian `.base` views and helper skills.

Switch later with `/welcome --enable-obsidian` or `/welcome --disable-obsidian`. The switch does not move or rewrite memory, journal, schedules, or integrations. In Obsidian mode, the TARS workspace is also the Obsidian vault.

## Integrations

TARS is strongest when it has calendar and task access, but the framework treats integrations generically. Skills look for configured providers through `_system/integrations.md` (capability-preference map, v3.1 format) and `_system/tools-registry.yaml` (auto-discovered by the SessionStart hook, 24-hour TTL). SessionStart refreshes that registry silently and only asks you to run `/doctor` if refresh fails. All skill calls resolve via `mcp__tars_vault__resolve_capability(capability=…)` — no hardcoded server names.

Capabilities TARS understands out of the box: `calendar`, `tasks`, `email`, `meeting-recording`, `office-docs`, `file-storage`, `design`, `data-warehouse`, `analytics`, `project-tracker`, `documentation`, `monitoring`, `communication`.

Recommended setup rules:
- connect calendar access so briefings and meeting matching can use real events
- connect task access so reviewed tasks can sync into your external system
- connect a meeting-recording provider (Minutes.app, Microsoft 365 with recordings, etc.) so `/meeting` can import transcripts directly instead of requiring paste
- keep `.mcp.json` or equivalent integration configuration beside the workspace or repository as appropriate for your environment

If integrations are not configured, TARS still works for local memory, journal, transcripts, strategic analysis, and communication drafting. Briefings and meeting processing simply lose some automation.

### First semantic search — FastEmbed model download

The first time `/answer` or any skill triggers a semantic search, FastEmbed downloads the `BAAI/bge-small-en-v1.5` model (~80 MB). The cache lives at `_system/embedding-cache/` and is gitignored. If the download fails, TARS falls back to FTS-only retrieval and surfaces the gap in the answer.

### Office output prerequisites

`/create` delegates `.pptx`, `.docx`, `.xlsx`, `.pdf`, and HTML rendering to Anthropic's first-party skills. `/welcome` probes which are available in your Claude Code install and stores the list in `_system/config.md.tars-anthropic-skills`. If a format is missing, `/create` informs you with a one-line install hint and falls back to markdown-only for that session.

## Your first workflows

### Daily orientation

```text
/briefing
```

TARS combines calendar context, tasks, memory, initiatives, and system health into a short daily briefing.

That same workflow adapts automatically for weekly planning, re-entry after time away, sparse-input periods, and drift-aware catch-up. No extra briefing flags are required.

### Meeting processing

```text
/meeting
```

Paste a transcript or point TARS to a transcript file. TARS will:
- match the meeting to calendar context when possible
- draft a meeting journal entry
- propose tasks that pass the accountability test
- propose durable memory updates that pass the durability test
- preserve transcript text in an archived transcript note for later retrieval

### Task management

```text
/tasks
```

Use this for extraction, review, reprioritization, and completion. TARS does not silently create tasks. It presents a numbered review list first.

### Fast lookup

```text
/answer What do I know about the platform rewrite?
```

TARS answers from memory first (FTS5 over `memory/**`), then tasks, then journal + transcripts via hybrid semantic-plus-FTS retrieval, then transcript-archive fallback, then integrations. Internal questions should not depend on web search.

### Workspace lint

```text
/lint
```

Runs deterministic checks (schema, broken links, stale memory, task escalation, telemetry signals) and surfaces proposed fixes for review. It can run manually, or on a schedule after `/welcome --setup-schedules` succeeds in an environment with a scheduler.

### Strategic work

```text
/think Stress-test the Q3 roadmap.
```

Use this for deeper analysis, challenge rounds, and structured decision support.

## How persistence works

TARS is designed to avoid dirty data.

Before it writes:
- it checks what the workspace already knows
- it resolves names through aliases and search
- it asks when confidence is low
- it routes content into the proper TARS schema and folder
- the local helper rejects unknown tool arguments, protects managed system paths, and blocks writes if the install record points at a different workspace
- create-time note writes validate required TARS frontmatter fields and enum values against `_system/schemas.yaml`

Before it persists tasks or memory:
- tasks must pass the accountability test
- memory must pass the durability test
- you review proposed changes before they are written

This is intentional. TARS is meant to accumulate reliable context over months and years, not just capture whatever was said most recently.

## Inbox and transcripts

Use `inbox/pending/` for raw intake that should be processed later in batch. Typical examples:
- raw meeting transcripts
- notes exported from another system
- screenshots or captured artifacts
- PDF reports, decks, docs, spreadsheets, or other documents to turn into context or wisdom notes
- rough notes that contain a mix of facts, tasks, and decisions

Then say:

```text
process inbox
```

or run:

```text
/maintain inbox
```

TARS inventories the pending folder, classifies each item, asks what to process, routes selected items through meeting, learn, tasks, or companion-note workflows, and moves finished items to `inbox/processed/`. This works in bulk. If a file type cannot be read directly by the active Claude environment, TARS creates a companion note and asks for extracted text or a converted copy rather than silently dropping the file.

When transcripts are processed, the raw text should remain available through archived transcript notes in `archive/transcripts/YYYY-MM/`. Those notes are part of the retrieval model, not disposable temporary files.

## Upgrading an existing workspace

`3.7.2` does not require a manual migration script.

After installing the updated build:
- run `/briefing` or `/lint` once so TARS rebuilds `_system/activity-ledger.yaml`
- extension-enabled workflows will use `extensions/`, `_system/extensions.yaml`, and derived `_system/extension-runtime.json`; older workspaces can add those lazily when the first extension is installed
- keep using your existing workspace path; `install.yaml` and schedule state remain valid
- no task migration is required; legacy `memory/tasks/` notes are still readable, while active task workflows continue to use `tasks/`
- if you rely on scheduled jobs, it is worth running `/maintain` or `/welcome --setup-schedules` once so the new version is the one refreshing notices and weekly review behavior

## Self-learning

TARS has a reviewed self-learning loop. It watches lightweight telemetry and journal patterns for repeated behavior, then proposes updates to `_system/user-model.md` or `_system/workflows.yaml` through `/learn --review-patterns` and the weekly maintenance review queue. It does not auto-apply those proposals. You approve, skip, or edit them before anything changes.

## Operating habits that make TARS valuable

The framework becomes more useful as it compounds context. The highest-leverage habits are:
- run `/briefing` at the start of the day
- process important meetings soon after they happen
- use `/learn` when new durable context emerges
- use `/tasks` to keep commitments explicit and clean
- let scheduled maintenance keep links, schemas, and archival state healthy

## Where to go next

If you want to understand the system in more depth:
- read [README.md](README.md) for the product overview
- read [ARCHITECTURE.md](ARCHITECTURE.md) for the full framework model
- read [CLAUDE.md](CLAUDE.md) for the live agent operating rules
- read [docs/MOBILE-USAGE.md](docs/MOBILE-USAGE.md) to use TARS from a phone via Claude Remote Control
