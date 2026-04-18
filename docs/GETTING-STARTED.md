<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# Getting Started with TARS

TARS is an Obsidian-native executive assistant framework. The setup goal is straightforward: connect TARS to a real Obsidian vault, install the `tars-vault` MCP server, and let `/welcome` scaffold the runtime so daily work can begin immediately.

## Before you install

You need:
- Obsidian Desktop running on the same machine
- `obsidian-cli` installed and able to reach your target vault (used as the transport below the `tars-vault` MCP server)
- Python 3.10+ available on the path
- Claude Code or Claude Cowork with the TARS framework installed
- a vault location dedicated to your TARS workspace

If you are starting fresh, create an empty vault. If you are migrating from an earlier TARS setup, migrate the old workspace into a current TARS vault first and then use this guide. If you are upgrading from v3.0 to v3.1, see [docs/MIGRATION-v3.0-to-v3.1.md](docs/MIGRATION-v3.0-to-v3.1.md).

## Installation

Install from your preferred path:

1. Marketplace install:
   - add the repository as a marketplace source in Cowork
   - install `tars`
2. Local install:
   - clone the repository
   - install the plugin from the local checkout

After installing the plugin, install the Python runtime dependencies for the `tars-vault` MCP server from the repo root:

```text
pip install -r requirements.txt
```

The pinned deps are minimal: `mcp`, `fastembed`, `sqlite-vec`. Nothing else. In particular TARS does NOT bundle any office-rendering libraries — office output in `/create` delegates to Anthropic's first-party `pptx` / `docx` / `xlsx` / `pdf` skills.

The repository root ships an `.mcp.json` declaring the `tars-vault` server. Set `TARS_VAULT_PATH` in your shell or IDE environment to point at your vault before starting Claude Code, so the MCP server knows where to operate.

The repository contains the framework source. The vault you point TARS at is the live runtime workspace.

## First-run setup

Run `/welcome`.

The welcome flow:
- creates the TARS vault structure
- writes `_system/` files, templates, and live views
- installs or verifies the Obsidian helper skills in `.claude/skills/`
- configures integration metadata
- captures your initial profile and operating context
- registers briefing and maintenance schedules when supported

After setup, the vault should contain:

```text
_system/
_views/
memory/
journal/
contexts/
inbox/pending/
inbox/processed/
archive/transcripts/
templates/
scripts/
```

## Integrations

TARS is strongest when it has calendar and task access, but the framework treats integrations generically. Skills look for configured providers through `_system/integrations.md` (capability-preference map, v3.1 format) and `_system/tools-registry.yaml` (auto-discovered by the SessionStart hook, 24-hour TTL). All skill calls resolve via `mcp__tars_vault__resolve_capability(capability=…)` — no hardcoded server names.

Capabilities TARS understands out of the box: `calendar`, `tasks`, `email`, `meeting-recording`, `office-docs`, `file-storage`, `design`, `data-warehouse`, `analytics`, `project-tracker`, `documentation`, `monitoring`, `communication`.

Recommended setup rules:
- connect calendar access so briefings and meeting matching can use real events
- connect task access so reviewed tasks can sync into your external system
- connect a meeting-recording provider (Minutes.app, Microsoft 365 with recordings, etc.) so `/meeting` can import transcripts directly instead of requiring paste
- keep `.mcp.json` or equivalent integration configuration beside the vault or repository as appropriate for your environment

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

### Vault lint

```text
/lint
```

Runs deterministic checks (schema, broken links, stale memory, task escalation, telemetry signals) and surfaces proposed fixes for review. Runs nightly as a scheduled cron job once `/maintain register-crons` has been executed.

### Strategic work

```text
/think Stress-test the Q3 roadmap.
```

Use this for deeper analysis, challenge rounds, and structured decision support.

## How persistence works

TARS is designed to avoid dirty data.

Before it writes:
- it checks what the vault already knows
- it resolves names through aliases and search
- it asks when confidence is low
- it routes content into the proper TARS schema and folder

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
- documents to turn into context or wisdom notes

When transcripts are processed, the raw text should remain available through archived transcript notes in `archive/transcripts/YYYY-MM/`. Those notes are part of the retrieval model, not disposable temporary files.

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
- read [docs/MIGRATION-v3.0-to-v3.1.md](docs/MIGRATION-v3.0-to-v3.1.md) if you are upgrading a v3.0 vault
- read [docs/MOBILE-USAGE.md](docs/MOBILE-USAGE.md) to use TARS from a phone via Claude Remote Control
