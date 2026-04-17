<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS

TARS is an Obsidian-native persistent executive assistant for senior knowledge workers. It turns an Obsidian vault into a long-lived operating system for meetings, memory, tasks, briefings, strategic thinking, and stakeholder communication.

TARS is built around a few core ideas:
- Obsidian is the runtime workspace, not an export target.
- `obsidian-cli` is the write interface for vault content.
- TARS-managed notes use schema-validated `tars-` frontmatter properties.
- Live Obsidian Bases replace hand-maintained `_index.md` files.
- Meeting answers can fall back to archived raw transcripts when summaries are not enough.
- Tasks and durable memory always go through review before persistence.

## What ships in the framework

The framework ships with 13 skills, 12 commands, 15 templates, 15 live views, and 13 deterministic scripts.

Core user-facing capabilities:
- Daily and weekly briefings with calendar, task, people, and initiative context
- Meeting processing that links transcripts, journal notes, decisions, and follow-through
- Task extraction with accountability testing and duplicate checks
- Durable memory capture for people, initiatives, decisions, products, vendors, competitors, and organizational context
- Fast lookup across memory, journal, transcripts, and configured integrations
- Strategic analysis, communications drafting, initiative planning, and maintenance workflows

## Architecture at a glance

The framework uses this high-level structure:

```text
skills/           Behavioral and workflow protocols
commands/         Thin slash-command wrappers into the skills
_system/          Runtime configuration, schemas, guardrails, alias registry, state
_views/           Obsidian `.base` files for live queries
templates/        Canonical TARS note templates
scripts/          Deterministic validators and maintenance utilities
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
- [GETTING-STARTED.md](GETTING-STARTED.md) for setup and first workflows
- [ARCHITECTURE.md](ARCHITECTURE.md) for the current system model
- [BUILD.md](BUILD.md) for packaging and release mechanics
- [CONTRIBUTING.md](CONTRIBUTING.md) for maintenance and change hygiene
- [CHANGELOG.md](CHANGELOG.md) for release history
- [CATALOG.md](CATALOG.md) for the product and adoption overview

## License

This repository is licensed under PolyForm Noncommercial 1.0.0. See [LICENSE](LICENSE).
