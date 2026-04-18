<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS

TARS is an Obsidian-native persistent executive assistant for senior knowledge workers. It turns an Obsidian vault into a long-lived operating system for meetings, memory, tasks, briefings, strategic thinking, and stakeholder communication.

TARS is built around a few core ideas:
- Obsidian is the runtime workspace, not an export target.
- A `tars-vault` MCP server is the write interface; skills call `mcp__tars_vault__*` tools and hooks enforce write discipline.
- TARS-managed notes use schema-validated `tars-` frontmatter properties.
- Live Obsidian Bases replace hand-maintained `_index.md` files.
- Retrieval combines SQLite FTS5 over structured memory with a local FastEmbed + sqlite-vec semantic layer over prose (journal, transcripts, contexts).
- Meetings run a nuance-capture pass after summarization — contrarian views, quotes, numbers, unusual terms are preserved verbatim.
- Integrations are provider-agnostic: skills resolve a capability (calendar, tasks, meeting-recording, data-warehouse, analytics, design, documentation, project-tracker, etc.) and the registry picks the active server.
- Office output (`.pptx`, `.docx`, `.xlsx`, `.pdf`, HTML) delegates to Anthropic's first-party rendering skills; TARS owns content structuring, brand application, companion notes, and vault filing.
- Tasks and durable memory always go through review before persistence.

## What ships in the framework

The framework ships with 13 skills, 13 commands, 15 templates (plus 9 office content outlines), 16 live views, and 12 deterministic scripts.

Core user-facing capabilities:
- Daily and weekly briefings with calendar, task, people, and initiative context
- Meeting processing that links transcripts, journal notes, decisions, and follow-through — with nuance-capture pass
- Task extraction with accountability testing, duplicate checks, age / escalation tracking
- Durable memory capture for people, initiatives, decisions, products, vendors, competitors, and organizational context
- Hybrid fast lookup — FTS5 over memory, semantic over journal + transcripts + contexts, plus integrations
- Strategic analysis (five modes), communications drafting (RASCI + brand-aware), initiative planning
- `/lint` vault health pass + `/maintain` inbox / sync / archive sweep
- `/create` office output orchestration via Anthropic's first-party skills

## Architecture at a glance

The framework uses this high-level structure:

```text
skills/           Behavioral and workflow protocols (13 skills)
commands/         Thin slash-command wrappers into the skills
hooks/            SessionStart / PreToolUse / PostToolUse / PreCompact / SessionEnd
mcp/tars-vault/   Write-interface MCP server + retrieval + organization tools
_system/          Runtime configuration, schemas, guardrails, telemetry, registries
_views/           Obsidian `.base` files for live queries
templates/        Canonical TARS note templates (+ office content outlines)
scripts/          Deterministic stdlib-only validators and maintenance utilities
.claude/skills/   Obsidian-specific helper skills used by the agent
```

A deployed TARS vault uses this runtime layout:

```text
memory/                 Durable knowledge graph
journal/YYYY-MM/        Skill outputs and dated notes
contexts/               Deep reference material and generated artifacts
inbox/pending/          Raw intake waiting for processing
inbox/processed/        Processed intake awaiting later maintenance
archive/transcripts/    Preserved transcript notes with journal backlinks
```

Legacy directories or compatibility files may still exist in some checkouts for migration context, but the active runtime source of truth lives in the current system files and workflow definitions.

## Quick start

1. Install the framework from the marketplace or from a local checkout.
2. Make sure Obsidian Desktop is running and `obsidian-cli` is installed.
3. Point TARS at an Obsidian vault dedicated to your TARS workspace.
4. Run `/welcome` to scaffold the vault, configure integrations, and initialize system files.
5. Start with `/briefing`, `/meeting`, `/tasks`, `/answer`, or natural-language requests.

Examples:

```text
/welcome
/briefing
/meeting
/tasks
/answer What do I know about the platform rewrite?
/think Stress-test this roadmap decision.
```

## How TARS behaves

TARS is designed to preserve signal and avoid silent drift:
- It checks the vault before writing and classifies findings as NEW, UPDATE, REDUNDANT, or CONTRADICTS.
- It uses the durability test before proposing memory persistence.
- It uses the accountability test before proposing tasks.
- It preserves transcript text so later queries can inspect what was actually said.
- It records framework issues and user improvement ideas in `_system/backlog/`.
- It performs scheduled or session-start maintenance to keep schemas, links, and archival state healthy.

## Documentation map

Start here depending on what you need:
- [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) for setup and first workflows
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the current system model
- [docs/BUILD.md](docs/BUILD.md) for packaging and release mechanics
- [CONTRIBUTING.md](CONTRIBUTING.md) for maintenance and change hygiene
- [CHANGELOG.md](CHANGELOG.md) for release history
- [docs/CATALOG.md](docs/CATALOG.md) for the product and adoption overview
- [docs/MIGRATION-v3.0-to-v3.1.md](docs/MIGRATION-v3.0-to-v3.1.md) for vault migration
- [docs/MOBILE-USAGE.md](docs/MOBILE-USAGE.md) for Claude Remote Control on mobile

## License

This repository is licensed under PolyForm Noncommercial 1.0.0. See [LICENSE](LICENSE).
