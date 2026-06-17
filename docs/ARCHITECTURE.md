<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS 3.7.3 Architecture

This document describes the current framework architecture as of v3.7.3, which makes the local Markdown workspace authoritative, keeps Obsidian optional, and treats the AI harness as first-class product code.

**Version**: 3.7.3
**Release**: 2026-06-16 — see `CHANGELOG.md`

**Model**: Framework repository plus deployed Markdown workspace runtime, with optional Obsidian views

## Three operations (Karpathy framing)

TARS v3.2 makes the three-operations pattern explicit:

- **Ingest** — meetings, transcripts, inbox items, manual learning. Skills: `/meeting`, `/learn`, `/maintain`, SessionEnd / PreCompact hooks.
- **Query** — retrieval from workspace memory + journal + transcripts + integrations. Skills: `/answer`, `/briefing`, `/think`, `/initiative`.
- **Lint** — deterministic and LLM-assisted consistency checks over the workspace and its own telemetry. Skill: `/lint`. Runs nightly.

## System model

TARS operates directly on a local Markdown workspace and treats that workspace as the persistent runtime state. Obsidian can be enabled as an enhanced browser over the same files.

At a high level:
- the repository is the framework source, packaging logic, and documentation
- the workspace is the live operating environment where memory, journal entries, transcripts, and context live
- the local TARS helper (`tars-vault`) is the canonical write interface for workspace mutations; skills call its internal `mcp__tars_vault__*` tools and never raw file writes
- TARS-managed notes use schema-validated `tars-` properties and `tars/` tags
- Obsidian Bases provide optional live query surfaces instead of hand-maintained index notes
- Hooks (`SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `SessionEnd`) enforce write discipline, capture telemetry, and route Claude Code session transcripts into `inbox/pending/` for later `/meeting`-style review

Only skill metadata loads eagerly at session start. With 15 skills, the lightweight baseline stays small before deeper instructions are loaded on demand.

## Repository layout

The current framework source is centered on these directories:

```text
tars/
├── .claude-plugin/           Manifest and marketplace metadata
├── .claude/skills/           Obsidian helper skills used by the agent
├── .mcp.json                 Project defaults for MCP servers (incl. tars-vault)
├── mcp/tars-vault/           Local TARS helper (Python)
├── hooks/                    SessionStart / *ToolUse / PreCompact / SessionEnd scripts
├── skills/                   TARS protocol skills (14)
├── commands/                 Slash-command wrappers + README mapping
├── _system/                  Canonical v3.1 system files and defaults
├── _views/                   Obsidian `.base` query definitions
├── templates/                Canonical note templates (+ office outlines)
├── scripts/                  Deterministic stdlib-only maintenance and validation utilities
├── tests/                    Validators and regression tests
├── docs/                     User and developer guides (architecture, build, mobile)
├── build-plugin.sh           Supported packaging entrypoint
├── requirements.txt          No required third-party deps for first setup
├── requirements-search.txt   Optional semantic-search deps: fastembed, sqlite-vec
├── CLAUDE.md                 Live agent operating rules
├── README.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

The framework currently ships 15 skills, 15 slash-command wrappers, and deterministic scripts.

## Deployed workspace layout

`/welcome` produces a workspace with this shape:

```text
_system/
  config.md
  integrations.md
  alias-registry.md
  taxonomy.md
  kpis.md
  schedule.md
  extensions.yaml
  guardrails.yaml
  maturity.yaml
  housekeeping-state.yaml
  activity-ledger.yaml
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
extensions/
inbox/pending/
inbox/processed/
archive/transcripts/YYYY-MM/
archive/inbox/YYYY-MM/
archive/tasks/YYYY-MM/
tasks/
templates/
scripts/
```

Key runtime notes:
- `memory/` stores durable entity knowledge
- `journal/` stores dated outputs such as meeting notes and briefings
- `contexts/` stores deep reference material and generated artifacts
- `extensions/` stores workspace-installed provider adapters, workflow playbooks,
  template packs, retrieval packs, and validation packs
- `inbox/` is raw intake, not durable knowledge by itself
- `archive/transcripts/` preserves transcript text for future lookup and verification
- `_system/activity-ledger.yaml` is a tiny derived state capsule for startup and adaptive briefing
- `tasks/` is the current task-note location; legacy `memory/tasks/` remains readable

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

The framework uses one core skill and thirteen user-invocable skills. Resource files such as `skills/think/manifesto.md`, `skills/meeting/resources/nuance-pass-prompt.md`, and `skills/communicate/text-refinement.md` load only when a workflow needs them.

### Write interface layer

The `mcp/tars-vault/` Python local helper sits between every skill and the workspace. It exposes internal `mcp__tars_vault__*` tools that:
- enforce the `tars-` frontmatter prefix and `_system/schemas.yaml` validation on every write
- reject unknown tool arguments before dispatch, so misshaped calls fail visibly instead of silently dropping data
- fail closed when no real workspace can be resolved, and block writes when `_system/install.yaml` records a different workspace path
- protect managed system paths (`_system/`, `_views/`, `archive/`, root `index.md`) from direct create/update/move/archive calls outside internal maintenance flows
- chunk appends at 40KB so large transcripts land cleanly
- maintain an in-process alias-registry cache with mtime invalidation
- validate wikilinks before writes
- move notes while preserving wikilinks (Organization Engine primitive)
- wrap `scripts/scan-secrets.py` for pre-write secret classification
- read system files through `read_system_file`, with YAML parsed into structured data and traversal blocked
- classify files and detect near-duplicates for the Organization Engine
- resolve capabilities against `_system/tools-registry.yaml` (populated by `SessionStart`)
- resolve and read workspace-installed extensions from `extensions/` through
  `_system/extensions.yaml`
- enforce fail-closed extension ownership for workspace paths and tags before
  mutating notes, preventing externalized capabilities from silently falling
  back to local Markdown
- expose FTS5 + semantic retrieval + deterministic rerank
- expose navigation tools (`workspace_map`, `context_gaps`, `entity_timeline`, `context_bundle`, `archive_candidates`) for bounded context packs without making a database mandatory

### Hooks layer

Hooks under `hooks/` are stdlib-only Python scripts wired via `hooks/hooks.json` and `.claude/settings.json`:
- `SessionStart` — refresh the integrations index, read `_system/activity-ledger.yaml` for concise workspace-state guidance, and suppress repeated housekeeping notices through `_system/install.yaml.acknowledged_notices`
- `PreToolUse` — block unsafe helper writes and direct provider MCP calls
  governed by required/fail-closed extensions until the extension contract has
  been loaded
- `PostToolUse` — emit workspace-write telemetry events and record successful
  extension loads for provider-bypass enforcement
- `PreCompact` + `SessionEnd` — drop the Claude Code session transcript into `inbox/pending/` so `/meeting` can ingest it later
- `InstructionsLoaded` — telemetry on skill load plus active-skill state for
  extension enforcement

Hook implementation errors exit 0, but successful `PreToolUse` policy checks can
deny unsafe tool calls with a plain reason.

### Retrieval layer

Hybrid retrieval, built by `scripts/build-search-index.py` and served from `mcp/tars-vault/src/tars_vault/search_index.py`:
- Tier A: SQLite FTS5 over `memory/**` — keyword / BM25 on structured entity notes
- Tier B: FTS5 + `sqlite-vec` vector search over `journal/**`, `archive/transcripts/**`, `contexts/**` using `BAAI/bge-small-en-v1.5` (384-dim) via FastEmbed
- The `rerank` tool applies deterministic score normalization plus recency + source boosts
- Index is incremental (SHA-256 content hash in `_system/search-index-state.json`) and bounded to a 10-minute run

### Integration layer (provider-agnostic)

`_system/integrations.md` is a capability-preference map (calendar / tasks / email / meeting-recording / office-docs / file-storage / design / data-warehouse / analytics / project-tracker / documentation / monitoring / communication). `_system/tools-registry.yaml` is auto-discovered state with a 24-hour TTL, refreshed silently by the SessionStart hook via `scripts/discover-mcp-tools.py` + `scripts/capability-classifier.py`. Users only see a plain `/doctor` hint if that refresh fails.

Every skill resolves integrations through `mcp__tars_vault__resolve_capability(capability=…)` and uses whatever MCP tool the registry returns. No hardcoded server names anywhere.

### Extension layer

TARS supports provider adapters, workflow extensions, template packs, retrieval
packs, and validation packs as subordinate modules loaded by canonical core
skills at explicit extension points. The design keeps plugin skills and
framework code in the dynamic plugin root, while all installed extensions live
under the recorded workspace root. Curated extensions hosted in the TARS GitHub
repository are installed into the workspace before use.

Extensions can also declare ownership of capabilities, workspace paths, tags,
and provider tools. Advisory ownership only informs routing; required ownership
blocks provider bypasses until the extension is loaded; fail-closed ownership
also blocks local workspace writes to owned paths/tags. This lets default
commands use third-party tools without turning TARS itself into a
vendor-specific framework or mixing plugin and workspace paths. See
[EXTENSIONS.md](EXTENSIONS.md) for the path model, manifest contract, registry,
resolver tools, and enforcement rules.

### Office output layer

`/create` orchestrates office output but does NOT render. Rendering delegates to Anthropic's first-party skills — `pptx`, `docx`, `xlsx`, `pdf`, `web-artifacts-builder`. `/create`'s responsibilities:
1. content structuring as reviewable markdown first
2. brand pointer passing (path to a `tars-brand: true` note)
3. data-source resolution via integrations
4. companion-note creation (`mcp__tars_vault__create_note` after render completes)
5. workspace filing under `contexts/artifacts/YYYY-MM/`
6. telemetry (`artifact_generated`)

TARS ships zero office-rendering Python libraries. The `templates/office/` folder holds structural outlines only.

### State and schema layer

`_system/` is the canonical runtime control plane:
- `schemas.yaml` defines allowed TARS note shapes (v3.1 adds `tars-blocked-by`, `tars-age-days`, `tars-escalation-level` on tasks; `tars-brand` / `tars-draft-status` on context-artifacts; full companion-note super-set)
- `alias-registry.md` resolves names and alternate forms
- `integrations.md` records capability preferences (v3.1 format, `tars-config-version: "2.0"`)
- `extensions.yaml` records enabled workspace-installed extensions and their
  workspace-relative paths
- `tools-registry.yaml` is the auto-discovered live tool roster (24h TTL)
- `guardrails.yaml` drives secret and negative-sentiment scans, including common Slack, GitHub, Stripe, Twilio, SendGrid, Google, OpenAI, and Anthropic token patterns
- `housekeeping-state.yaml` + `maturity.yaml` track maintenance cadence and live hydration counts
- `activity-ledger.yaml` caches last-use, intake, stale-initiative, overdue-task, active-set, and gap signals derived from Markdown
- `install.yaml` stores workspace identity, plugin version, scheduler preference, and notice acknowledgments
- `telemetry/YYYY-MM-DD.jsonl` captures skill invocations, workspace writes, retrieval hits, durability / accountability signals
- `backlog/` stores framework issues and user improvement ideas
- `search-index-state.json` + `search.db` hold the hybrid retrieval state

These files are part of the workspace state, not separate background documentation.

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
- `office/` — 8 structural content outlines for `/create`

### Script layer

`scripts/` holds deterministic utilities that support the skills and release workflow. The active set is stdlib-only (optional deps wrapped in `try/except ImportError` with fallback parsers per PRD §26.2): schema validation, secret scanning, health checks (including flagged-content and frontmatter-prefix sub-checks), archival (memory + workflow staleness, v3.2), sync / hydration, search-index builder, wikilink fixers, telemetry rollup (v3.2), MCP tool discovery, capability classifier, version bump, plugin validation, and packaging.

## Critical behavior changes in v3

The TARS v3 rebuild introduced the most important architectural changes in the framework:
- live bases replace `_index.md` files when Obsidian mode is enabled
- raw transcript text is preserved as part of the searchable system
- tasks and durable memory are reviewed before persistence
- name resolution uses aliases, workspace search, and user confirmation instead of flat replacements only
- maintenance state, schemas, and guardrails live in `_system/`
- the active runtime structure is centered on the workspace and `_system/` seeds

## What's new in v3.7.3

- **Plugin mount compatibility.** Extension load acknowledgements recognize
  plugin-namespaced and hyphenated TARS vault `read_extension` tool names, so
  legitimate extension provider calls are not blocked on installs where Claude
  mounts the helper under a different MCP name.

## What was new in v3.7.2

- **Extension enforcement layer.** Extensions can declare ownership of
  capabilities, workspace paths, tags, and provider tools. `tars-vault` blocks
  fail-closed local writes to owned state, while hooks block direct provider
  MCP calls until the governing extension has been loaded.
- **Direct command pre-flight.** Slash-command wrappers now name the extension
  pre-flight before skill handoff so direct commands do not rely solely on core
  routing to discover extensions.

## What was new in v3.7.1

- **Mandatory extension pre-flight.** Core routing resolves enabled extensions
  for the selected skill/mode before the target workflow runs. Matched
  extensions declare the capabilities that must be resolved before a workflow
  decides no provider work is needed.

## What was new in v3.7

- **Workspace extension layer.** Provider adapters, workflow playbooks, template
  packs, retrieval packs, and validation packs now have a workspace-only runtime
  model. Installed extensions live under `extensions/` and are registered in
  `_system/extensions.yaml`; plugin-root extension loading is intentionally not
  supported.
- **Extension resolver tools.** The local helper exposes `list_extensions`,
  `validate_extension`, `resolve_extension`, `read_extension`,
  `scaffold_extension`, and `install_extension` so core skills can load
  extension instructions through a path-safe boundary.
- **Extension path invariants.** Catalog extensions from the TARS repository are
  copied into the workspace before use. Registry entries store
  workspace-relative paths only, and tests reject absolute or plugin-root
  extension paths.

## What was new in v3.6

- **Harness-first prompt architecture.** Core, briefing, meeting, maintain, learn, think, and ideate now use compact router cards plus mode-specific references instead of loading long workflow manuals by default. A harness-budget validator prevents those always-loaded cards from growing back into mega-prompts.
- **Natural-language-first routing.** Slash commands remain compatibility shortcuts, but help and core routing now frame work as workflows: prepare my day, catch me up, process a meeting, remember this, draft a message, create an artifact, and clean up the workspace.
- **Adaptive briefing by default.** `/briefing` infers daily, weekly, re-entry, context-gap, or drift-aware posture from workspace state. No new briefing flags are required.
- **Dynamic activity ledger.** `_system/activity-ledger.yaml` gives SessionStart and briefing a tiny derived state capsule: last session, last briefing, last transcript, inbox pressure, stale initiatives, overdue tasks, active file count, and context gaps.
- **Workspace navigation tools.** The local helper now exposes `workspace_map`, `context_gaps`, `entity_timeline`, `context_bundle`, and `archive_candidates` so Claude can build bounded context packs over a Markdown workspace without broad startup scans or a required database runtime.
- **Lifecycle-aware archive guardrails.** Archival uses `tars-modified` / `tars-updated` dates, reads both `tasks/` and legacy `memory/tasks/`, protects durable and pinned notes, and moves reviewed items into typed destinations such as `archive/inbox/YYYY-MM/` and `archive/tasks/YYYY-MM/`.
- **Self-improvement stays review-gated.** Weekly maintenance references now include a harness-review section for repeated failures, routing misses, bloated skill cards, unused aliases, and contradictions between instructions and implementation. TARS proposes changes; it does not auto-edit its own harness.

## What was new in v3.5

- **MCP helper safety moved into the server.** Unknown tool arguments are rejected, write tools fail when the install record points at another workspace, and auto-resolution no longer treats the current directory as a vault unless it is actually a TARS workspace.
- **Runtime schema validation.** `create_note` and `write_note_from_content` validate managed notes against `_system/schemas.yaml` before writing. Intentional partial stubs must opt out with `validate=false`.
- **Plain SessionStart notices.** SessionStart silently refreshes integration metadata, deduplicates housekeeping notices through `acknowledged_notices`, and surfaces empty-workspace, welcome-back, version-drift, inbox, overdue-task, stale-initiative, and frontmatter-pollution guidance as short action-oriented lines.
- **Freeform note writes are safe.** `write_note_from_content` accepts either split `frontmatter` + `body` or a single full-Markdown `content` blob, and never reports success for unknown arguments or empty accidental writes.
- **Managed paths are protected.** Direct writes to system files, generated views, archive destinations, and the root cheat sheet are blocked unless an internal maintenance flow opts in.
- **System-file reads are explicit.** `read_system_file` reads `_system/*.yaml|*.yml|*.md`, parses YAML into structured data, and rejects traversal.
- **Expanded secret scanning.** Guardrails now block common provider tokens including Slack, GitHub, Stripe, Twilio, SendGrid, Google, OpenAI, and Anthropic.
- **Version-stamped generated views.** Obsidian `.base` views scaffold with a generated-by TARS version marker so stale generated views can be detected.

## What was new in v3.2

- **Persistent install record (`_system/install.yaml`)** — workspace-specific record carrying `workspace_type`, `workspace_path`, backward-compatible `vault_path`, `obsidian_enabled`, `obsidian_vault_path`, `installation_id`, `persona`, `plugin_version`, and timestamps. Hooks consult it on every session start; the local helper enforces install/workspace alignment for writes.
- **Persona-driven cold start** — seven onboarding personas (`templates/personas/`) seed `_system/config.md` defaults, `_system/taxonomy.md` starter tags, and `_system/briefing-sections` so day-1 briefings are role-aware.
- **Workspace modes (`headless` | `obsidian`)** — headless mode uses the Markdown workspace through Claude. Obsidian mode uses the same files plus `.base` views and helper skills. This is a view/storage adapter, not a separate data model.
- **Wikilink discipline (forward + retroactive)** — new `mcp__tars_vault__format_wikilink(text, kind)` tool resolves raw text to an Obsidian-safe link via the alias registry + workspace file lookup. Write tools and the pre-tool-use hook reject content with smart quotes or Obsidian-illegal characters. `scripts/fix-wikilinks.py --repair-broken` classifies broken legacy links into `auto_safe` / `needs_review` / `unresolvable`, with apply-only-on-safe semantics.
- **40 KB body cap + `tars-` prefix enforcement** at the hook layer for non-chunking write tools.
- **SessionStart banner** — now a concise, state-aware context summary rather than a persistent wall of internal notices.
- **Active `/lint --actions`** — materializes fixable findings as a numbered review queue. Two surfaces: inline for interactive users, `inbox/pending/weekly-review-YYYY-MM-DD.md` for scheduled maintenance callers. Subsets: `wikilinks`, `patterns`, `curator`.
- **Weekly maintenance job (`/maintain --weekly`)** — scheduled Sunday 18:00 when the user enables schedules through `/welcome --setup-schedules`, or run manually. Pipeline: telemetry rollup → `_system/changelog/`, backlog grouping, `/lint --actions`, `/learn --review-patterns` proposals, curator + persona-drift proposals, materialize the weekly review file, update housekeeping cooling-off timestamps. Single trigger that backstops every staleness/drift/rollup feature; Claude does not run in the background.
- **Telemetry rollup script (`scripts/telemetry-rollup.py`)** — stdlib aggregator over `_system/telemetry/*.jsonl`. Same source feeds `/briefing` weekly footer (Mondays) and `/maintain --weekly`.
- **Observed-preference user model (`_system/user-model.md`)** — single living note (~5 KB cap) capturing BLUF tolerance, decision speed, default skill, meeting cadence, recurring concerns, vendor sentiment, observed skill mix. Updated passively by `/learn` Mode C when patterns repeat ≥3× in 14 days.
- **Workflows registry (`_system/workflows.yaml`)** — workspace-owned saved multi-step routing aliases. Created only on user approval. `core` consults the registry before default routing.
- **Workspace-side staleness curator** — workflow-staleness (60 days unused) and memory-staleness (90 days, honoring `tars-pinned: true`) checks in `scripts/archive.py --check workflows`. Always archive, never delete.
- **Persona-drift detection** — runs inside `/maintain --weekly` only when ≥30 days of telemetry exist and the 14-day cooling-off has elapsed. Compares observed skill-mix against persona expectations.

## What was new in v3.1

- **Hook-based enforcement** replaces duplicated prompt-level reminders. SessionStart, PreCompact, SessionEnd, PreToolUse, PostToolUse all go through stdlib-only Python scripts under `hooks/`.
- **Local TARS helper (`tars-vault`)** centralizes filesystem writes, validation, chunking, alias resolution, and secret scanning. Skills call internal `mcp__tars_vault__*` tools.
- **Bundled stdlib MCP transport** lets marketplace installs expose `tars-vault` tools without requiring users to install the Python `mcp` package first. The official SDK remains an optional transport when available.
- **Integration Registry 2.0** — capability-preference map (`_system/integrations.md` v2) plus auto-discovered `_system/tools-registry.yaml` with a 24h TTL. Skills resolve via `resolve_capability` and work interchangeably across Apple, Microsoft 365, Minutes.app, Figma, Snowflake, Pendo, etc.
- **Hybrid retrieval** — FTS5 for structured memory + FastEmbed + sqlite-vec semantic search for prose. Directly fixes the retrieval-nuance pain point from v3.0 feedback.
- **Meeting nuance pass** — a Haiku sub-step after summarization preserves contrarian views, notable phrases, specific quotes, unusual terms, missed numbers and dates. Lands in the journal as `## Notable phrases & perspectives`.
- **`/lint` skill** — first-class daily workspace lint; `/maintain` slims down to inbox + sync + archive sweep.
- **`/create` office-output orchestration** — delegates rendering to Anthropic's first-party `pptx` / `docx` / `xlsx` / `pdf` / `web-artifacts-builder` skills. Zero office-rendering code or dependencies in TARS.
- **Cross-session continuity** — PreCompact and SessionEnd hooks route Claude Code session transcripts into `inbox/pending/` for `/meeting`-style review, without violating review gates.
- **Telemetry + reflection** — every skill invocation, workspace write, durability decision, accountability decision, and retrieval hit appends to `_system/telemetry/YYYY-MM-DD.jsonl`. `/lint` uses the log to surface memories saved but never re-read, tasks created but never transitioned, etc.
- **Archival policy** — scale target is 3× current (600 journal, 360 people). Notes unreferenced for 90+ days archive unless durable.
- **Self-state fixes** — `scripts/sync.py --hydration` computes live counts; `/briefing` stops inventing "Level N" artifacts; `/lint` reconciles `maturity.yaml` drift.

## Core workflows

### Onboarding

`/welcome` scaffolds the workspace, optionally enables Obsidian views, writes system files, captures user context, and configures schedules.

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
2. FTS5 over workspace (Tier A)
3. tasks
4. journal + transcripts — semantic + FTS hybrid (`mcp__tars_vault__semantic_search`)
5. transcript archive fallback (raw transcript text when summaries lack detail)
6. integrations (via capability resolution)
7. external search only when necessary

The hybrid retrieval layer means TARS can answer paraphrased questions against journal and transcript prose without relying on exact keyword matches, while keyword search still dominates on structured entity notes where FTS wins.

## Release and packaging model

The supported release packaging path is the repository-root [build-plugin.sh](build-plugin.sh). It packages the v3 framework, helper skills, templates, system files, and scripts into `tars-cowork-plugin/`.

The packaged plugin is intentionally slimmer than the repository, but it should describe the same architecture and behaviors. Release documentation must stay aligned with the repository source, the packaged README, and `.claude-plugin/plugin.json`.
