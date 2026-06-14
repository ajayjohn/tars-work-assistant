<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS

TARS turns a local Markdown workspace into a persistent Claude assistant for meetings, memory, tasks, briefings, strategic thinking, and stakeholder communication.

TARS is built around a few core ideas:
- The local Markdown workspace is the data model. Obsidian is optional and can be enabled later as a visual browser.
- The local TARS helper (`tars-vault`) is the required guardrail layer for workspace writes. It ships with the plugin and runs locally.
- The AI harness is treated as product code: lean always-loaded instructions, mode-specific references, hooks, validators, and review-gated improvements.
- TARS-managed notes use schema-validated `tars-` frontmatter properties.
- Live Obsidian Bases are available in Obsidian mode; headless users can query the same files through Claude.
- Retrieval combines SQLite FTS5 over structured memory with a local FastEmbed + sqlite-vec semantic layer over prose (journal, transcripts, contexts).
- Briefing is adaptive by default: daily, weekly, re-entry, sparse-context, and drift-aware orientation all route through `/briefing` or natural language.
- Meetings run a nuance-capture pass after summarization — contrarian views, quotes, numbers, unusual terms are preserved verbatim.
- The inbox is a first-class intake path: drop transcripts, PDFs, decks, docs, screenshots, exports, or rough notes into `inbox/pending/` and ask TARS to process the inbox in bulk.
- Integrations are provider-agnostic: skills resolve a capability (calendar, tasks, meeting-recording, data-warehouse, analytics, design, documentation, project-tracker, etc.) and the registry picks the active server.
- Extensions are workspace-installed modules for provider adapters, workflow playbooks, template packs, retrieval packs, and validators; even curated catalog extensions are copied into the user's workspace before use.
- Office output (`.pptx`, `.docx`, `.xlsx`, `.pdf`, HTML) delegates to Anthropic's first-party rendering skills; TARS owns content structuring, brand application, companion notes, and workspace filing.
- Tasks and durable memory always go through review before persistence.
- Cold-start friction is addressed by progressive `/welcome`, seven onboarding personas, and graceful degradation when integrations are missing.
- Wikilink hygiene is centralized: every `[[…]]` flows through `format_wikilink`; smart-quote and Obsidian-illegal links are rejected at the write side; legacy broken links can be repaired in bulk.
- Startup context is time-aware instead of scan-heavy: a tiny `_system/activity-ledger.yaml` capsule tracks last use, intake gaps, stale initiatives, overdue tasks, and active-set pressure.
- Scheduled work is optional and registered through `/welcome --setup-schedules` when a scheduler is available. Claude does not run in the background by itself, so weekly staleness, drift, and rollup work is surfaced through scheduled jobs or manual `/maintain --weekly`.

## First run

After installing the plugin, run `/welcome`. It creates a local Markdown workspace, records your identity and persona, and then guides you into a first paste-or-upload workflow before anything is saved.

```text
/welcome
```

## What you get over time

- **Day 1**: useful structure from pasted meetings, emails, calls, and docs.
- **Day 7**: inbox files, memory, people, decisions, and tasks start showing up in `/answer` and `/briefing`.
- **Day 30**: TARS becomes an operating layer for recurring work, follow-through, and organizational context.

## What ships in the framework

The framework ships with 15 skills, 15 slash-command wrappers, note templates, office content outlines, seven personas, live views for Obsidian mode, and deterministic maintenance scripts.

Core user-facing capabilities:
- Adaptive briefings for day-start, week planning, re-entry after time away, sparse intake, and drift
- Meeting processing that links transcripts, journal notes, decisions, and follow-through — with nuance-capture pass
- Inbox processing for bulk transcripts, PDFs, decks, docs, screenshots, exports, and raw notes
- Task extraction with accountability testing, duplicate checks, age / escalation tracking
- Durable memory capture for people, initiatives, decisions, products, vendors, competitors, and organizational context
- Hybrid fast lookup — FTS5 over memory, semantic over journal + transcripts + contexts, plus integrations
- Workspace navigation helpers that build bounded context from Markdown: activity gaps, entity timelines, context bundles, and archive candidate review
- Strategic analysis (five modes), communications drafting (RASCI + brand-aware), initiative planning
- `/lint --actions` materialized review queue (subsets: wikilinks, patterns, curator) + `/maintain --weekly` scheduled pipeline
- `/learn --review-patterns` for observed-preference learning (user model + workflow-alias proposals)
- `/create` office output orchestration via Anthropic's first-party skills

## Architecture at a glance

The framework uses this high-level structure:

```text
skills/           Behavioral and workflow protocols (15 skills)
commands/         Thin slash-command wrappers into the skills
hooks/            SessionStart / PreToolUse / PostToolUse / PreCompact / SessionEnd
mcp/tars-vault/   Local TARS helper + retrieval + organization tools
_system/          Source defaults for scaffolded runtime config and schemas
_views/           Source templates for optional Obsidian `.base` views
templates/        Canonical TARS note templates (+ office content outlines)
scripts/          Deterministic stdlib-only validators and maintenance utilities
.claude/skills/   Obsidian-specific helper skills used by the agent
```

A deployed TARS workspace uses this runtime layout. These directories live in your **workspace**, not in this repository. The plugin scaffolds them on first `/welcome`:

```text
_system/               Runtime config, install state, maturity, schemas, guardrails
memory/                Durable knowledge graph
journal/               Skill outputs and dated notes
contexts/              Deep reference material and generated artifacts
extensions/            Workspace-installed TARS extensions
inbox/pending/         Raw intake waiting for processing (incl. weekly review queues)
inbox/processed/       Processed intake awaiting later maintenance
tasks/                 Current task-note location
archive/               Preserved transcripts and archived material, grouped by type
templates/             User-visible templates copied for portability
scripts/               Workspace-local helper scripts
index.md               Cheat sheet and natural-language workflow guide
```

Put raw files in `inbox/pending/` and say "process inbox" or run `/maintain inbox`. TARS inventories the folder, classifies each item, routes it to the right workflow, proposes memory/tasks for review, writes durable context, and moves processed items to `inbox/processed/`.

The plugin/workspace boundary is strict: plugin-shipped skills are read-only from a user's perspective, and any auto-created or user-tunable behavior lives in the workspace (`_system/install.yaml`, `_system/extensions.yaml`, `_system/user-model.md`, `_system/workflows.yaml`, `extensions/`).

Existing workspaces do not need a manual migration for `3.7.0`. The first `/briefing` or `/lint` rebuilds the derived activity ledger; legacy `memory/tasks/` notes remain readable while new task workflows continue to use `tasks/`. Workspace extensions are installed under `extensions/` when first used.

## Quick start

1. Install the framework from the marketplace or from a local checkout.
2. Point TARS at a local folder for your Markdown workspace.
3. Run `/welcome` to scaffold the workspace, pick a persona, and set your identity.
4. Paste or upload a meeting transcript, PDF/report excerpt, email thread, or rough notes when welcome offers the first guided workflow.
5. Continue deeper setup later with `/welcome --continue-setup`; enable Obsidian with `/welcome --enable-obsidian` if you want live views.

Examples:

```text
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
- It refuses workspace writes when the local helper cannot resolve a real TARS workspace or when the install record points at a different folder.
- It validates managed note frontmatter against workspace schemas before create-time writes.
- It uses the durability test before proposing memory persistence.
- It uses the accountability test before proposing tasks.
- It keeps startup context lean by rebuilding a small derived activity ledger instead of re-scanning the whole workspace on every session.
- It preserves transcript text so later queries can inspect what was actually said.
- It records framework issues and user improvement ideas in `_system/backlog/`.
- It performs scheduled or session-start maintenance to keep schemas, links, integration indexes, and archival state healthy.
- It coaches lightly through Daily Digest suggestions, milestone moments, and `/help`, with controls to show fewer tips or turn coaching off.

## Documentation map

Start here depending on what you need:
- [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) for setup and first workflows
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the current system model
- [docs/BUILD.md](docs/BUILD.md) for packaging and release mechanics
- [CONTRIBUTING.md](CONTRIBUTING.md) for maintenance and change hygiene
- [CHANGELOG.md](CHANGELOG.md) for release history
- [docs/CATALOG.md](docs/CATALOG.md) for the product and adoption overview
- [docs/MOBILE-USAGE.md](docs/MOBILE-USAGE.md) for Claude Remote Control on mobile

## License

This repository is licensed under PolyForm Noncommercial 1.0.0. See [LICENSE](LICENSE).
