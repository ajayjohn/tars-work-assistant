<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS

TARS turns a local Markdown workspace into a persistent Claude assistant for meetings, memory, tasks, briefings, strategic thinking, and stakeholder communication.

TARS is built around a few core ideas:
- The local Markdown workspace is the data model. Obsidian is optional and can be enabled later as a visual browser.
- A `tars-vault` MCP server is the write interface; skills call `mcp__tars_vault__*` tools and hooks enforce write discipline.
- TARS-managed notes use schema-validated `tars-` frontmatter properties.
- Live Obsidian Bases are available in Obsidian mode; headless users can query the same files through Claude.
- Retrieval combines SQLite FTS5 over structured memory with a local FastEmbed + sqlite-vec semantic layer over prose (journal, transcripts, contexts).
- Meetings run a nuance-capture pass after summarization — contrarian views, quotes, numbers, unusual terms are preserved verbatim.
- The inbox is a first-class intake path: drop transcripts, PDFs, decks, docs, screenshots, exports, or rough notes into `inbox/pending/` and ask TARS to process the inbox in bulk.
- Integrations are provider-agnostic: skills resolve a capability (calendar, tasks, meeting-recording, data-warehouse, analytics, design, documentation, project-tracker, etc.) and the registry picks the active server.
- Office output (`.pptx`, `.docx`, `.xlsx`, `.pdf`, HTML) delegates to Anthropic's first-party rendering skills; TARS owns content structuring, brand application, companion notes, and workspace filing.
- Tasks and durable memory always go through review before persistence.
- Cold-start friction is addressed by `/start`, progressive `/welcome`, seven onboarding personas, and graceful degradation when integrations are missing.
- Wikilink hygiene is centralized: every `[[…]]` flows through `format_wikilink`; smart-quote and Obsidian-illegal links are rejected at the write side; legacy broken links can be repaired in bulk.
- Periodic work runs only via cron jobs registered during `/welcome` — Claude does not run in the background, so every staleness, drift, and rollup feature is bound to a single `tars-weekly-maintenance` job that opens a session and writes a numbered review queue for next time.

## Try it in 90 seconds

After installing the plugin, run `/start` and paste your own content. No setup, integrations, or Obsidian required.

```text
/start
Paste a meeting transcript and extract decisions, risks, and follow-up items.

/start
Paste a sales discovery call and draft a follow-up email.

/start
Paste a design discussion and identify decisions, open questions, risks, and tasks.
```

No transcript handy? Try one of `examples/`.

## What you get over time

- **Day 1**: useful structure from pasted meetings, emails, calls, and docs.
- **Day 7**: inbox files, memory, people, decisions, and tasks start showing up in `/answer` and `/briefing`.
- **Day 30**: TARS becomes an operating layer for recurring work, follow-through, and organizational context.

## What ships in the framework

The framework ships with 14 skills, 15 commands, note templates, office content outlines, seven personas, live views for Obsidian mode, and deterministic maintenance scripts.

Core user-facing capabilities:
- Daily and weekly briefings with calendar, task, people, and initiative context (plus a Monday telemetry footer)
- Meeting processing that links transcripts, journal notes, decisions, and follow-through — with nuance-capture pass
- Inbox processing for bulk transcripts, PDFs, decks, docs, screenshots, exports, and raw notes
- Task extraction with accountability testing, duplicate checks, age / escalation tracking
- Durable memory capture for people, initiatives, decisions, products, vendors, competitors, and organizational context
- Hybrid fast lookup — FTS5 over memory, semantic over journal + transcripts + contexts, plus integrations
- Strategic analysis (five modes), communications drafting (RASCI + brand-aware), initiative planning
- `/lint --actions` materialized review queue (subsets: wikilinks, patterns, curator) + `/maintain --weekly` cron-fired pipeline
- `/learn --review-patterns` for observed-preference learning (user model + workflow-alias proposals)
- `/create` office output orchestration via Anthropic's first-party skills

## Architecture at a glance

The framework uses this high-level structure:

```text
skills/           Behavioral and workflow protocols (14 skills)
commands/         Thin slash-command wrappers into the skills
hooks/            SessionStart / PreToolUse / PostToolUse / PreCompact / SessionEnd
mcp/tars-vault/   Write-interface MCP server + retrieval + organization tools
_system/          Runtime configuration, schemas, guardrails, telemetry, registries
_views/           Optional Obsidian `.base` files for live queries
templates/        Canonical TARS note templates (+ office content outlines)
scripts/          Deterministic stdlib-only validators and maintenance utilities
.claude/skills/   Obsidian-specific helper skills used by the agent
```

A deployed TARS workspace uses this runtime layout. These directories live in your **workspace**, not in this repository. The plugin scaffolds them on first `/welcome`:

```text
memory/                 Durable knowledge graph
journal/YYYY-MM/        Skill outputs and dated notes
contexts/               Deep reference material and generated artifacts
inbox/pending/          Raw intake waiting for processing (incl. weekly review queues)
inbox/processed/        Processed intake awaiting later maintenance
archive/transcripts/    Preserved transcript notes with journal backlinks
```

Put raw files in `inbox/pending/` and say "process inbox" or run `/maintain inbox`. TARS inventories the folder, classifies each item, routes it to the right workflow, proposes memory/tasks for review, writes durable context, and moves processed items to `inbox/processed/`.

The plugin/workspace boundary is strict: plugin-shipped skills are read-only from a user's perspective, and any auto-created or user-tunable behavior lives in the workspace (`_system/install.yaml`, `_system/user-model.md`, `_system/workflows.yaml`).

## Quick start

1. Install the framework from the marketplace or from a local checkout.
2. Point TARS at a local folder for your Markdown workspace.
3. Run `/start` to preview what TARS does with pasted content.
4. Run `/welcome` to scaffold the workspace, pick a persona, and set your identity.
5. Continue deeper setup later with `/welcome --continue-setup`; enable Obsidian with `/welcome --enable-obsidian` if you want live views.

Examples:

```text
/start
/welcome
/briefing
/meeting
/tasks
/maintain inbox
/answer What do I know about the platform rewrite?
/think Stress-test this roadmap decision.
```

Slash commands are shortcuts. Natural-language requests work too: "process everything in my inbox", "what should I focus on today", "remember Sarah owns onboarding", or "stress-test this roadmap".

## How TARS behaves

TARS is designed to preserve signal and avoid silent drift:
- It checks the workspace before writing and classifies findings as NEW, UPDATE, REDUNDANT, or CONTRADICTS.
- It uses the durability test before proposing memory persistence.
- It uses the accountability test before proposing tasks.
- It preserves transcript text so later queries can inspect what was actually said.
- It records framework issues and user improvement ideas in `_system/backlog/`.
- It performs scheduled or session-start maintenance to keep schemas, links, and archival state healthy.
- It coaches lightly through Daily Digest suggestions, milestone moments, and `/help`, with controls to show fewer tips or turn coaching off.

## Documentation map

Start here depending on what you need:
- [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) for setup and first workflows
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the current system model
- [docs/BUILD.md](docs/BUILD.md) for packaging and release mechanics
- [CONTRIBUTING.md](CONTRIBUTING.md) for maintenance and change hygiene
- [CHANGELOG.md](CHANGELOG.md) for release history
- [docs/CATALOG.md](docs/CATALOG.md) for the product and adoption overview
- [docs/MIGRATION-v3.0-to-v3.1.md](docs/MIGRATION-v3.0-to-v3.1.md) for legacy vault migration (v3.0 → v3.1; v3.1 → v3.3 handled via automated hook)
- [docs/MOBILE-USAGE.md](docs/MOBILE-USAGE.md) for Claude Remote Control on mobile

## License

This repository is licensed under PolyForm Noncommercial 1.0.0. See [LICENSE](LICENSE).
