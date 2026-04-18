<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS 3.1 Architecture

This document describes the current framework architecture after the v3.1 "harden, simplify, and extend" release.

**Version**: 3.1.0  
**Release**: (v3.1.0-dev, see `CHANGELOG.md`)  
**Model**: Framework repository plus deployed Obsidian vault runtime

## Three operations (Karpathy framing)

TARS v3.1 makes the three-operations pattern explicit:

- **Ingest** — meetings, transcripts, inbox items, manual learning. Skills: `/meeting`, `/learn`, `/maintain`, SessionEnd / PreCompact hooks.
- **Query** — retrieval from vault memory + journal + transcripts + integrations. Skills: `/answer`, `/briefing`, `/think`, `/initiative`.
- **Lint** — deterministic and LLM-assisted consistency checks over the vault and its own telemetry. Skill: `/lint`. Runs nightly.

## System model

TARS 3.1 operates directly on an Obsidian vault and treats that vault as the persistent runtime state.

At a high level:
- the repository is the framework source, packaging logic, and documentation
- the vault is the live operating environment where memory, journal entries, transcripts, and context live
- the `tars-vault` MCP server is the canonical write interface for vault mutations; skills call `mcp__tars_vault__*` tools and never raw `obsidian-cli`
- TARS-managed notes use schema-validated `tars-` properties and `tars/` tags
- Obsidian Bases provide live query surfaces instead of hand-maintained index notes
- Hooks (`SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `SessionEnd`) enforce write discipline, capture telemetry, and route Claude Code session transcripts into `inbox/pending/` for later `/meeting`-style review

Only skill metadata loads eagerly at session start. With 13 skills, the lightweight baseline is roughly 52 tokens before deeper instructions are loaded on demand.

## Repository layout

The current framework source is centered on these directories:

```text
tars/
├── .claude-plugin/           Manifest and marketplace metadata
├── .claude/skills/           Obsidian helper skills used by the agent
├── .mcp.json                 Project defaults for MCP servers (incl. tars-vault)
├── mcp/tars-vault/           Write-interface MCP server (Python)
├── hooks/                    SessionStart / *ToolUse / PreCompact / SessionEnd scripts
├── skills/                   TARS protocol skills (13)
├── commands/                 Slash-command wrappers + README mapping
├── _system/                  Canonical v3.1 system files and defaults
├── _views/                   Obsidian `.base` query definitions
├── templates/                Canonical note templates (+ office outlines)
├── scripts/                  Deterministic stdlib-only maintenance and validation utilities
├── scripts/githooks/         prepare-commit-msg + pre-push authorship guards
├── tests/                    Validators, fixtures, and smoke tests
├── archive/historical/       Retired legacy rebuild docs (pre-v3.0)
├── docs/                     HANDOFF notes + v3.1 migration/release/mobile guides
├── build-plugin.sh           Supported packaging entrypoint
├── requirements.txt          Pinned runtime deps: mcp, fastembed, sqlite-vec
├── CLAUDE.md                 Live agent operating rules
├── README.md
├── GETTING-STARTED.md
├── ARCHITECTURE.md
├── BUILD.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

The framework currently ships 13 skills, 13 commands, and 12 scripts.

Some older directories remain in the repository for compatibility, migration context, or packaging history. They should not be treated as the active TARS 3.0 runtime architecture unless a specific document says otherwise.

## Deployed vault layout

`/welcome` or a migration process should produce a vault with this shape:

```text
_system/
  config.md
  integrations.md
  alias-registry.md
  taxonomy.md
  kpis.md
  schedule.md
  guardrails.yaml
  maturity.yaml
  housekeeping-state.yaml
  schemas.yaml
  changelog/
  backlog/issues/
  backlog/ideas/

_views/
  *.base

memory/
  people/
  vendors/
  competitors/
  products/
  initiatives/
  decisions/
  org-context/

journal/YYYY-MM/
contexts/
  products/
  artifacts/
  YYYY-MM/
inbox/pending/
inbox/processed/
archive/transcripts/YYYY-MM/
templates/
scripts/
```

Key runtime notes:
- `memory/` stores durable entity knowledge
- `journal/` stores dated outputs such as meeting notes and briefings
- `contexts/` stores deep reference material and generated artifacts
- `inbox/` is raw intake, not durable knowledge by itself
- `archive/transcripts/` preserves transcript text for future lookup and verification

## Runtime layers

### Interface layer

Users can work through natural language or explicit commands. The command layer remains intentionally thin:
- `/welcome`
- `/briefing`
- `/meeting`
- `/tasks`
- `/learn`
- `/answer`
- `/think`
- `/communicate`
- `/initiative`
- `/create`
- `/lint`
- `/maintain`

Each command simply routes into the corresponding skill protocol.

### Protocol layer

The `skills/` directory is the behavioral core of the framework:
- `core` defines routing, write discipline, review gates, and persistence rules
- `meeting` handles transcript processing, matching, journaling, nuance capture, and follow-through
- `briefing`, `tasks`, `learn`, `answer`, `think`, `communicate`, `initiative`, `create`, `lint`, `maintain`, and `welcome` cover the rest of the user-facing workflows

The framework uses one core skill and twelve user-invocable skills (the `/lint` skill is new in v3.1, split out of `/maintain`). Resource files such as `skills/think/manifesto.md`, `skills/meeting/reference/nuance-pass-prompt.md`, and `skills/communicate/text-refinement.md` load only when a workflow needs them.

### Write interface layer

The `mcp/tars-vault/` Python MCP server sits between every skill and the vault. It exposes `mcp__tars_vault__*` tools that:
- enforce the `tars-` frontmatter prefix and `_system/schemas.yaml` validation on every write
- chunk appends at 40KB so large transcripts land cleanly
- maintain an in-process alias-registry cache with mtime invalidation
- run the auto-wikilink pass before writes
- move notes while preserving wikilinks (Organization Engine primitive)
- wrap `scripts/scan-secrets.py` for pre-write secret classification
- classify files and detect near-duplicates for the Organization Engine
- resolve capabilities against `_system/tools-registry.yaml` (populated by `SessionStart`)
- expose FTS5 + semantic retrieval + deterministic rerank

### Hooks layer

Hooks under `hooks/` are stdlib-only Python scripts wired via `hooks/hooks.json` and `.claude/settings.json`:
- `SessionStart` — load housekeeping state, refresh `_system/tools-registry.yaml`, inject vault-state summary into the session
- `PreToolUse` — observability for MCP writes (frontmatter prefix enforcement is owned by the MCP server; this hook captures shape)
- `PostToolUse` — emit `vault_write` telemetry events
- `PreCompact` + `SessionEnd` — drop the Claude Code session transcript into `inbox/pending/` so `/meeting` can ingest it later
- `InstructionsLoaded` — telemetry on skill load

All hook errors exit 0 — they never block a tool call.

### Retrieval layer

Hybrid retrieval, built by `scripts/build-search-index.py` and served from `mcp/tars-vault/src/tars_vault/search_index.py`:
- Tier A: SQLite FTS5 over `memory/**` — keyword / BM25 on structured entity notes
- Tier B: FTS5 + `sqlite-vec` vector search over `journal/**`, `archive/transcripts/**`, `contexts/**` using `BAAI/bge-small-en-v1.5` (384-dim) via FastEmbed
- The `rerank` tool applies deterministic score normalization plus recency + source boosts
- Index is incremental (SHA-256 content hash in `_system/search-index-state.json`) and bounded to a 10-minute run

### Integration layer (provider-agnostic)

`_system/integrations.md` is a capability-preference map (calendar / tasks / email / meeting-recording / office-docs / file-storage / design / data-warehouse / analytics / project-tracker / documentation / monitoring / communication). `_system/tools-registry.yaml` is auto-discovered state with a 24-hour TTL, written by the SessionStart hook via `scripts/discover-mcp-tools.py` + `scripts/capability-classifier.py`.

Every skill resolves integrations through `mcp__tars_vault__resolve_capability(capability=…)` and uses whatever MCP tool the registry returns. No hardcoded server names anywhere.

### Office output layer

`/create` orchestrates office output but does NOT render. Rendering delegates to Anthropic's first-party skills — `pptx`, `docx`, `xlsx`, `pdf`, `web-artifacts-builder`. `/create`'s responsibilities:
1. content structuring as reviewable markdown first
2. brand pointer passing (path to a `tars-brand: true` note)
3. data-source resolution via integrations
4. companion-note creation (`mcp__tars_vault__create_note` after render completes)
5. vault filing under `contexts/artifacts/YYYY-MM/`
6. telemetry (`artifact_generated`)

TARS ships zero office-rendering Python libraries. The `templates/office/` folder holds structural outlines only.

### State and schema layer

`_system/` is the canonical runtime control plane:
- `schemas.yaml` defines allowed TARS note shapes (v3.1 adds `tars-blocked-by`, `tars-age-days`, `tars-escalation-level` on tasks; `tars-brand` / `tars-draft-status` on context-artifacts; full companion-note super-set)
- `alias-registry.md` resolves names and alternate forms
- `integrations.md` records capability preferences (v3.1 format, `tars-config-version: "2.0"`)
- `tools-registry.yaml` is the auto-discovered live tool roster (24h TTL)
- `guardrails.yaml` drives secret and negative-sentiment scans
- `housekeeping-state.yaml` + `maturity.yaml` track maintenance cadence and live hydration counts
- `telemetry/YYYY-MM-DD.jsonl` captures skill invocations, vault writes, retrieval hits, durability / accountability signals
- `backlog/` stores framework issues and user improvement ideas
- `search-index-state.json` + `search.db` hold the hybrid retrieval state

These files are part of the vault state, not separate background documentation.

### View layer

`_views/` contains live `.base` files for common operational questions:
- active tasks
- recent journal activity
- stale memory
- inbox backlog
- transcript archive coverage
- people, initiatives, vendors, products, competitors, and decisions

These bases replaced `_index.md` as the primary query surface. They reduce drift because they are computed from note properties rather than manually maintained.

### Template layer

`templates/` contains canonical note shapes for TARS-managed content:
- people, vendors, competitors, products
- initiatives and decisions, org-context
- meeting journals, unified `briefing.md` (daily | weekly mode), wisdom notes
- transcript and companion notes
- unified `backlog-item.md` (issue | idea mode)
- `brand-guidelines.md` with `tars-brand: true` for render-skill consumption
- `integrations-v2.md` — capability-preference starter
- `office/` — 8 structural content outlines for `/create`

### Script layer

`scripts/` holds deterministic utilities that support the skills and release workflow. The active set is stdlib-only (optional deps wrapped in `try/except ImportError` with fallback parsers per PRD §26.2): schema validation, secret scanning, health checks (including the merged-in flagged-content sub-check), archival, sync / hydration, search-index builder, wikilink fixer, integrations v2 migration, MCP tool discovery, capability classifier, version bump, plugin validation, packaging.

Not every script is a runtime dependency for end users. Some are maintainer tools used during packaging, testing, or migration support. The `scripts/githooks/` folder holds the `prepare-commit-msg` + `pre-push` authorship guards installed by `scripts/githooks/install-githooks.sh`.

## Critical behavior changes in v3

The Obsidian-native rebuild introduced the most important architectural changes in the framework:
- live bases replace `_index.md` files
- raw transcript text is preserved as part of the searchable system
- tasks and durable memory are reviewed before persistence
- name resolution uses aliases, vault search, and user confirmation instead of flat replacements only
- maintenance state, schemas, and guardrails live in `_system/`
- the active runtime structure is centered on the vault, not a copied `reference/` bundle

## What's new in v3.1

- **Hook-based enforcement** replaces duplicated prompt-level reminders. SessionStart, PreCompact, SessionEnd, PreToolUse, PostToolUse all go through stdlib-only Python scripts under `hooks/`.
- **`tars-vault` MCP server** centralizes writes, validation, chunking, alias resolution, and secret scanning. Skills call `mcp__tars_vault__*` tools; raw `obsidian-cli` is retained only for edge cases.
- **Integration Registry 2.0** — capability-preference map (`_system/integrations.md` v2) plus auto-discovered `_system/tools-registry.yaml` with a 24h TTL. Skills resolve via `resolve_capability` and work interchangeably across Apple, Microsoft 365, Minutes.app, Figma, Snowflake, Pendo, etc.
- **Hybrid retrieval** — FTS5 for structured memory + FastEmbed + sqlite-vec semantic search for prose. Directly fixes the retrieval-nuance pain point from v3.0 feedback.
- **Meeting nuance pass** — a Haiku sub-step after summarization preserves contrarian views, notable phrases, specific quotes, unusual terms, missed numbers and dates. Lands in the journal as `## Notable phrases & perspectives`.
- **`/lint` skill** — first-class daily vault lint; `/maintain` slims down to inbox + sync + archive sweep.
- **`/create` office-output orchestration** — delegates rendering to Anthropic's first-party `pptx` / `docx` / `xlsx` / `pdf` / `web-artifacts-builder` skills. Zero office-rendering code or dependencies in TARS.
- **Cross-session continuity** — PreCompact and SessionEnd hooks route Claude Code session transcripts into `inbox/pending/` for `/meeting`-style review, without violating review gates.
- **Telemetry + reflection** — every skill invocation, vault write, durability decision, accountability decision, and retrieval hit appends to `_system/telemetry/YYYY-MM-DD.jsonl`. `/lint` uses the log to surface memories saved but never re-read, tasks created but never transitioned, etc.
- **Archival policy** — scale target is 3× current (600 journal, 360 people). Notes unreferenced for 90+ days archive unless durable.
- **Self-state fixes** — `scripts/sync.py --hydration` computes live counts; `/briefing` stops inventing "Level N" artifacts; `/lint` reconciles `maturity.yaml` drift.

## Core workflows

### Onboarding

`/welcome` scaffolds the vault, checks Obsidian connectivity, installs helper skills, writes system files, captures user context, and configures schedules.

### Meeting processing

`/meeting` follows a strict sequence:
1. resolve meeting date and title, using calendar context when available
2. draft the meeting journal entry
3. propose tasks that pass the accountability gate
4. propose durable memory updates that pass the durability gate
5. archive the transcript in a queryable transcript note linked back to the journal entry

### Answer and retrieval

`/answer` searches in this order:
1. memory — keyword (`mcp__tars_vault__fts_search`) over `memory/**`
2. FTS5 over vault (Tier A)
3. tasks
4. journal + transcripts — semantic + FTS hybrid (`mcp__tars_vault__semantic_search`)
5. transcript archive fallback (raw transcript text when summaries lack detail)
6. integrations (via capability resolution)
7. external search only when necessary

The hybrid retrieval layer means TARS can answer paraphrased questions against journal and transcript prose without relying on exact keyword matches, while keyword search still dominates on structured entity notes where FTS wins.

## Release and packaging model

The supported release packaging path is the repository-root [build-plugin.sh](build-plugin.sh). It packages the v3 framework, helper skills, templates, system files, and scripts into `tars-cowork-plugin/`.

The packaged plugin is intentionally slimmer than the repository, but it should describe the same architecture and behaviors. Release documentation must stay aligned with the repository source, the packaged README, and `.claude-plugin/plugin.json`.
