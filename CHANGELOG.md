# Changelog

## v3.1.0-dev — WIP

### Phase 5 — Backlog fixes + state self-healing (§5)
- **Brand auto-load (§5.1)**: new `templates/brand-guidelines.md` with `tars-brand: true` flag. `/communicate` gains a mandatory Step 0 that resolves the active brand (via `_system/config.md`.`tars-active-brand` or a `search_by_tag(tag="tars/brand")` filtered on the frontmatter flag) and caches the chosen file for future sessions. `/create` Step 2 performs the same resolution and forwards the brand-file path to the render skill.
- **Framework self-state (§5.2)**: `scripts/sync.py` grows a `compute_hydration()` helper and a `--hydration` flag that returns live counts of people / initiatives / decisions / journal / task notes. `/briefing` (daily + weekly) now sources its System-status line from the live count rather than the drifting `_system/maturity.yaml`. The "Level 2 (15 people, 42 meetings)" artifact is gone; `/lint` owns the `maturity.yaml` repair per the updated check-table row.
- **Task lifecycle (§5.3)**: `_system/schemas.yaml` gains optional fields `tars-blocked-by`, `tars-age-days`, `tars-escalation-level` on the task schema (plus `tars-category`, `tars-completed`, `tars-completed-by`) and `tars-brand` / `tars-draft-status` on a new `context-artifact` schema. `/tasks` manage-mode sort is now escalation-aware (level 3 → 2 → 1 → 0, then overdue, then due-date, then priority). `/lint` owns the computation of `tars-age-days` / `tars-escalation-level` on its nightly pass with 30d / 60d / 90d thresholds.
- **Telemetry + reflection (§5.4)**: `hooks/_common.py` gains `append_telemetry()`. `hooks/post-tool-use.py` emits `vault_write` events for successful `mcp__tars_vault__*` mutations. `hooks/instructions-loaded.py` emits `skill_loaded`. New `_views/skill-activity.base` queries `tars/telemetry-rollup` notes; `/maintain sync` now produces the 14-day rollup note that populates the view. New `/lint` rules: memories-saved-but-never-re-read and tasks-created-but-never-transitioned.

### Phase 6 — /create office-productivity upgrade (§8.10)
- **Orchestrator rewrite**: `skills/create/SKILL.md` rewritten as a 9-step orchestrator — capability probe → intake → brand auto-load → context gathering → format selection → content-first markdown draft → review → delegate render → verify + companion + telemetry. Renders delegate exclusively to Anthropic's first-party `pptx`, `docx`, `xlsx`, `pdf`, `web-artifacts-builder` skills. TARS ships zero office-format libraries.
- **Structural templates**: new `templates/office/` with content-outline templates (`deck-executive`, `deck-narrative`, `deck-technical-review`, `spreadsheet-kpi-dashboard`, `spreadsheet-roadmap`, `doc-decision-memo`, `doc-project-status`, `html-board-update`) plus a README documenting the delegation split. Each template is plain markdown with `{{placeholder}}` fields.
- **Companion-note contract (§26.13)**: `/create` Step 8 writes the per-artifact `.md` companion under `contexts/artifacts/YYYY-MM/<slug>.md` with `tars-companion-of`, `tars-generated-by`, `tars-brand-applied`, `tars-source-data`, SHA-256, etc. Schema updated (`companion` in `_system/schemas.yaml`) to cover all office companion fields and the `html` original-type value.
- **`/welcome` pre-flight addition**: the onboarding flow now probes which Anthropic first-party skills are available in the host Claude Code install and persists the result in `_system/config.md.tars-anthropic-skills`. `/create` reads this at session start instead of reprobing per invocation. `/welcome` also offers to scaffold the first brand file from `templates/brand-guidelines.md`.
- **New validator**: `tests/validate-phase5-6.py` asserts brand-auto-load plumbing, hydration flag, task-lifecycle fields, telemetry hook wiring, office templates presence, `/create` step markers, and the absence of any reintroduction of a custom office MCP.

### Phase 4 — Hybrid retrieval + meeting nuance pass (§6)
- **Hybrid retrieval index**: `scripts/build-search-index.py` now builds FTS5 (Tier A: `memory/**`; Tier B: `journal/**`, `archive/transcripts/**`, `contexts/**`) plus a `sqlite-vec` vector layer over Tier B with `BAAI/bge-small-en-v1.5` (384-dim) embeddings via FastEmbed. Incremental SHA-256 state at `_system/search-index-state.json`; bounded 10-minute runs; graceful FTS-only fallback when FastEmbed or sqlite-vec is unavailable.
- **MCP search tools implemented**: `mcp__tars_vault__fts_search` (keyword, tier+source filters), `mcp__tars_vault__semantic_search` (hybrid 0.7 semantic + 0.3 FTS, scope by journal/transcripts/contexts/all, optional date filter), `mcp__tars_vault__rerank` (deterministic score-based rerank with recency + source boosts).
- **Meeting nuance pass (Step 7b)**: new sub-step inserted in `skills/meeting/SKILL.md` between summary and persistence. Spawns a Haiku sub-agent with the verbatim PRD §26.8 prompt to capture notable phrases, contrarian views, specific quotes, unusual terms, strong emotional statements, and missed numbers/dates. Rendered as `## Notable phrases & perspectives` in the journal entry. Telemetry: `meeting_nuance_captured` or `meeting_nuance_failed`. Never blocks the pipeline.
- **Test surface**: `mcp/tars-vault/tests/test_search_index.py` — 18 stdlib-only unit tests covering tier classification, chunking, FTS round-trip, tool contracts (no-index / missing args / fallback), and rerank ordering + boosts.
- **Dependency guard**: `tests/validate-scripts.py` now recognizes the PRD §26.2 approved deps (`mcp`, `fastembed`, `sqlite_vec`, `tars_vault`) alongside stdlib.

## v3.0.0 (2026-03-22)

**TARS 3.0: Obsidian-native rebuild — complete architecture redesign**

### Architecture
- **Obsidian-native**: All vault mutations via `obsidian-cli` (create, append, property:set, search). No direct filesystem writes for content.
- **Bases replace indexes**: 15 live `.base` query files replace all hand-maintained `_index.md` files. Zero drift, always accurate.
- **Schema-validated frontmatter**: All TARS notes use `tars-` prefixed properties validated against `_system/schemas.yaml` (14 entity types).
- **Vault-first runtime**: The deployed Obsidian vault is the runtime source of truth. The repository is the framework source and packaging surface.
- **Tag-driven filterability**: Hierarchical `tars/` tags on all managed notes for reliable search and base filtering.

### New capabilities (10 real-world issues addressed)
- **Transcript format detection + mandatory calendar check** (Issue 1): Meeting processing always queries calendar even when transcript provides a date. Multiple-choice confirmation for ambiguous matches.
- **Task review UX** (Issue 2): All task extraction presents numbered lists with selection syntax (`all`, `1,3,7`, `all except 4`, `none`). No silent task creation.
- **Ask don't assume** (Issue 3): Core principle — multiple-choice questions, max 3-4 per round, always check vault first, always include skip option.
- **File organization + companion files** (Issue 4): Non-markdown files get companion `.md` notes with metadata. Maintenance auto-organizes user-added files by date.
- **Quick capture / screenshot processing** (Issue 5): Multimodal image analysis with calendar context inference for screenshots captured during meetings.
- **Transcript-linked fallback lookup** (Issue 6): Transcripts archived with bidirectional journal links. Answer skill falls back to raw transcript when summaries lack detail.
- **Check before writing** (Issue 7): Knowledge inventory before all extraction — NEW/UPDATE/REDUNDANT/CONTRADICTS classification prevents stale overwrites.
- **Negative statement capture + cleanup** (Issue 8): Sentiment detection with inline flags. Periodic maintenance review with numbered removal. `flagged-content.base` view.
- **Self-evaluation backlog** (Issue 9): Auto-detected framework errors logged to `_system/backlog/issues/` (deduplicated). User ideas captured separately. `backlog.base` view.
- **Scheduled execution** (Issue 10): CronCreate for daily briefings, weekly briefings, and maintenance. Cron self-check at every session start.

### Added
- `_system/` directory: config, integrations, alias-registry, taxonomy, kpis, schedule, guardrails.yaml, maturity.yaml, housekeeping-state.yaml, schemas.yaml, changelog/, backlog/
- `_views/` directory: 15 `.base` files (all-people, all-initiatives, all-decisions, all-products, all-vendors, all-competitors, recent-journal, active-tasks, overdue-tasks, stale-memory, inbox-pending, all-documents, all-transcripts, flagged-content, backlog)
- `templates/` directory: 15 Obsidian templates (person, vendor, competitor, product, initiative, decision, org-context, meeting-journal, daily-briefing, weekly-briefing, wisdom-journal, companion, transcript, issue, idea)
- `commands/` thin wrappers retained for explicit slash-command invocation in the v3 framework
- `scripts/validate-schema.py`: Schema validation against schemas.yaml with PyYAML fallback
- `scripts/scan-flagged.py`: Negative sentiment scanner for people notes
- `scripts/health-check.py`: Rewritten for v3 schema, broken links, alias consistency, staleness
- `scripts/scan-secrets.py`: Rewritten for v3 guardrails.yaml format
- `scripts/sync.py`: Rewritten for v3 meeting journals, memory freshness, task drift
- `scripts/archive.py`: Rewritten with guardrails (never archive backlinked or task-referenced notes)
- `tests/smoke-tests.py`: 13-point verification suite
- `tests/fixtures/`: 6 schema validation fixtures (valid + invalid examples)
- `CLAUDE.md`: Vault-level agent configuration for v3
- Architectural decisions and deviation notes recorded during the rebuild
- `.claude/skills/`: obsidian-cli, obsidian-bases, obsidian-markdown, json-canvas, defuddle skill references

### Changed
- **All 12 skills rewritten** for Obsidian-native operation (core, welcome, learn, tasks, meeting, briefing, answer, maintain, think, communicate, initiative, create)
- **Name resolution**: 3-layer system (Obsidian aliases → context-aware registry → search fallback) replaces flat `replacements.md`
- **Inbox processing**: Simplified to pending/processed (no processing/failed intermediate states)
- **Think modes**: All 5 modes (A-E) check existing vault knowledge before analyzing
- **Communication drafting**: Loads stakeholder memory, checks for flagged negative content
- **Documentation set refreshed**: README, GETTING-STARTED, ARCHITECTURE, BUILD, CATALOG, and contribution docs now describe the actual v3 runtime model and release flow
- **Repository cleanup**: Removed duplicate legacy `.claude-plugin` payload trees, obsolete helper scripts, and stale release artifacts that were not part of the active v3 plugin

### Retired from the active runtime architecture
- `_index.md` files: Replaced by `.base` live queries
- `reference/` as runtime control plane: Replaced by `_system/`
- Manual index rebuilding as the primary query model: Replaced by live views and schema-driven note structure

## v2.2.0 (2026-02-19)

**Framework audit: efficiency, consistency, and automated validation**

### Added
- **Documentation consistency validator** (`tests/validate-docs.py`): 5-check validator catching stale skill references, provider-name leaks, count drift, archival tier terminology, and empty changelogs. Prevents semantic drift between docs and implementation.
- **CI integration for doc validation**: `validate-docs.py` added to `.github/workflows/validate.yml` with change detection for documentation files (ARCHITECTURE.md, README.md, GETTING-STARTED.md, CHANGELOG.md, CATALOG.md, reference/**, skills/**, commands/**, scripts/**).
- **Universal constraints in core skill**: 9 cross-cutting rules (date resolution, wikilink mandate, name normalization, task verification, integration constraints, index-first pattern, no-deletion, journal persistence, frontmatter compliance) now defined once in core and referenced by all skills.
- **Maintain skill developer reference**: Internal procedures for health-check.py, rebuild-indexes.py, and archive.py documented in ARCHITECTURE.md for maintainers without inflating the active skill.
- **CONTRIBUTING.md**: Consistency checklist for skill/script/protocol/integration/version changes, plus local validator run instructions.
- **Maintenance breadcrumbs**: HTML comments in core and maintain skills pointing to validate-docs.py and CONTRIBUTING.md.
- **Help metadata**: Added `purpose`, `use_cases`, `scope` help metadata to all 8 skills that were missing it (core, learn, think, maintain, welcome, initiative, create, communicate).
- **Name resolution protocol** (core skill): Cascading resolution for ambiguous and unknown names. Uses calendar attendees, transcript context, and memory files before asking the user. Batch clarification minimizes interruptions.
- **Health mode auto-fix** (maintain skill): Deterministic issues (decision file renames, index orphan removal, index rebuilds) are now auto-fixed instead of only suggested. Non-deterministic issues still presented to user.
- **Inbox name pre-resolution** (maintain skill): Names across all pending transcript files are resolved in a single pass before sub-agents spawn, ensuring consistency and preventing redundant user queries.

### Changed
- **Skill efficiency (~400 lines reduced)**: Deduplicated shared protocols across skills by referencing core definitions. Consolidated 3 inbox sub-agent templates into shared pipeline + type-specific processing. Streamlined maintain skill health/rebuild modes to script invocation with fallback references. Trimmed per-skill absolute constraints to unique-only (universal constraints in core).
- **workflows.md**: Rewrote all 8 workflow entries to use v2.2 skill names and reflect current pipeline architecture (was using v1.x names like `process-meeting`, `extract-tasks`).
- **ARCHITECTURE.md**: Fixed sub-agent descriptions to match actual implementations, corrected token baseline count, fixed script count (10→11), removed duplicate lines in workspace structure, corrected runner.sh reference.
- **README.md**: Fixed archival tier names from "active/warm/cool/archived" to canonical "durable/seasonal/transient/ephemeral".
- **welcome skill**: Updated command references (`/daily-briefing`→`/briefing`, `/process-meeting`→`/meeting`), replaced nonexistent `create-shortcut` skill reference with Cowork shortcut mechanism.
- **shortcuts.md**: Replaced `create-shortcut` skill reference with manual setup instructions.
- **answer skill**: Replaced hardcoded provider names (`eventlink`, `remindctl`) with generic language per provider-agnostic principle.
- **CHANGELOG.md**: Fixed wrong file path for getting-started guide (was `reference/getting-started.md`, corrected to `GETTING-STARTED.md`).
- **ARCHITECTURE.md help schema**: Aligned documented schema with actual implementation (`purpose`, `use_cases`, `scope`).
- **Script count**: 10→11 (added update-reference.py in v2.1.0, corrected in docs).
- **Meeting skill pipeline reorder**: Calendar lookup now runs before speaker name resolution so attendee lists inform the resolution cascade.
- **Meeting skill name resolution**: Enhanced from assumption-based inference to the core name resolution protocol with user clarification for remaining ambiguities.
- **Learn skill**: Both memory and wisdom modes now check for name ambiguity before processing. Unresolved names block extraction to prevent incorrect memory entries.
- **Health mode output**: Split into "Auto-fixed" and "Manual action required" sections. Deterministic fixes executed automatically, ambiguous issues presented to user.
- **Health mode constraint**: Expanded auto-fix scope from "only replacements" to include deterministic file renames, index orphan removal, and index rebuilds.
- **Version**: 2.1.0 → 2.2.0

---

## v2.1.0 (2026-02-19)

> Bumped from v2.0.1


## v2.0.1 (2026-02-10)

> Bumped from v2.0.0

### Added
- **Task creation verification**: All task creation paths (meeting, inbox, tasks skills) now include mandatory post-creation verification via `list_reminders`. Prevents silent failures where tasks are reported as created but never appear in the task manager.
- **Reference file update mechanism**: New `scripts/update-reference.py` surgically updates workspace reference files when the plugin is updated, preserving user customizations (name replacements, KPI definitions, schedule items). Three merge strategies: `full_replace`, `section_merge`, `additive_merge`.
- **Maintain update mode**: New `/maintain update` mode checks workspace reference files against the installed plugin version and applies updates with user confirmation.
- **Plugin version tracking**: `scaffold.sh` now writes `plugin_version` to `.housekeeping-state.yaml` at install time. Used by update-reference.py to detect stale workspaces.
- **Wikilink validation**: Inbox sub-agent templates now read memory indexes before creating wikilinks. Unverified names are flagged and added to replacements.md with placeholders.

### Changed
- **Inbox sub-agent templates**: Expanded from thin bullet-point templates to structured 6-step pipelines with memory index reads, speaker resolution, calendar lookup, structured report sections, wikilink validation, and task verification.
- **Inbox result collection**: Three-way handling (ok/partial/error) replaces binary ok/error. Partial status captures items where the journal was saved but task creation or memory extraction had issues.
- **Inbox file-move ordering**: Files are now moved from pending to processing as a batch before any sub-agents are spawned (prevents race conditions).
- **Task skill Step 6**: Now requires checking each `create_reminder` tool response before counting a task as created. New Step 7 calls `list_reminders` for post-creation verification.
- **Meeting skill Sub-agent A**: Task extraction template now includes response checking and `list_reminders` verification with `creation_unverified` tracking.
- **Integrations.md Tasks section**: Added verification requirement constraint.
- **Script count**: 9 → 10 (added update-reference.py)

---

All notable changes to the TARS framework are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). Version numbers follow [Semantic Versioning](https://semver.org/).

---

## v2.0.0 (2026-02-08)

**Architecture overhaul: skill consolidation, integration abstraction, automated housekeeping, and enterprise distribution**

### Breaking changes
- Consolidated 28 skills into 12 (7 background skills merged into single core skill, workflow skills merged by domain, 2 composite skills absorbed)
- Reduced 23 commands to 11 thin wrappers matching consolidated skills
- Renamed `/setup` to `/welcome` with progressive onboarding
- Replaced pipe-delimited index tables with YAML format
- Replaced hardcoded Eventlink/remindctl references with provider-agnostic integration registry
- Skill help metadata changed from flat string to structured object (purpose, use_cases, invoke_examples, common_questions, related_skills)

### Added
- **Skill consolidation**: core (7→1), meeting (2→1), tasks (2→1), learn (2→1), think (5→1), initiative (2→1), maintain (3→1)
- **9 automation scripts**: health-check.py, rebuild-indexes.py, scaffold.sh, sync.py, archive.py, verify-integrations.py, scan-secrets.py, bump-version.py (all Python stdlib only)
- **Provider-agnostic integration registry**: category-based design supporting http-api, cli, and mcp provider types
- **Progressive welcome flow**: 3-phase onboarding (instant setup, first win, background learning) replacing 4-round interrogation
- **YAML-based indexes**: improved editability and parseability over pipe tables
- **4-tier content archival**: durable/seasonal/transient/ephemeral with automatic expiry
- **Batch processing inbox**: inbox/pending → processing → completed/failed with isolated sub-agent processing
- **Sub-agent parallelization**: meeting (task extraction || memory extraction), think deep mode (validation || executive council), briefing (calendar || tasks || memory)
- **Automated daily housekeeping**: session-start check triggers maintenance scripts if not run today
- **Inline help metadata**: structured help objects in all skill YAML frontmatter
- **Sensitive data guardrails**: script-based scanning (scan-secrets.py) with configurable patterns in reference/guardrails.yaml
- **CI/CD pipeline**: GitHub Actions for PR validation (validate.yml) and auto-release (release.yml)
- **Test suite**: 6 validation scripts + test runner with dynamic test selection
- **CATALOG.md**: leadership adoption document for enterprise distribution
- **Maturity model**: reference/maturity.yaml tracking onboarding progress
- **Getting started guide**: GETTING-STARTED.md for new users
- **Workflow patterns**: reference/workflows.md documenting multi-skill patterns
- **Communication rules go global**: BLUF, anti-sycophancy, banned phrases now apply to ALL TARS outputs
- **AskUserQuestion integration**: structured UI clarification in Cowork mode
- **TodoWrite progress tracking**: real-time visibility during long-running operations
- **Context management directive**: intermediate results offloaded to files
- **Proactive learning triggers**: TARS suggests memory extraction when user corrects facts or shares context
- **Help routing**: core skill handles "how do I", "what can you do" queries via inline help metadata
- **Cowork shortcut support**: scheduled daily housekeeping via create-shortcut skill

### Changed
- Session baseline: ~115 tokens → ~48 tokens (12 skills × ~4 tokens vs 28 × ~4)
- Version: 1.5.0 → 2.0.0
- Plugin name: lowercase "tars" in manifest
- Skill descriptions: optimized with trigger keywords for better auto-routing accuracy
- Index format: pipe-delimited markdown tables → YAML entries
- Welcome flow: 4-round interrogation (10+ min) → 2 questions + auto-discovery (5 min)
- Integration references: hardcoded tool names → category-based ("query calendar integration")

### Removed
- 7 individual background skill directories (identity, communication, memory-management, task-management, decision-frameworks, clarification, routing) — merged into core
- 2 composite skill directories (meeting-processor, deep-analysis) — absorbed into meeting and think
- 8 individual workflow skill directories (process-meeting, extract-tasks, manage-tasks, extract-memory, extract-wisdom, housekeeping, rebuild-index, update, setup, quick-answer, strategic-analysis, executive-council, validation-council, discovery-mode, performance-report, create-artifact) — consolidated into domain skills
- 12 command files — consolidated to match 11 merged skills

---

## v1.5.0 (2026-02-07)

**Structural compliance rebuild: spec-compliant Claude Cowork plugin**

### Breaking changes
- **Removed**: `agents/` directory -- converted to composite skills
- **Removed**: `data/` directory tree -- workspace template created at runtime by `/setup`
- **Removed**: `reference/executive-council-manifesto.md` -- duplicate of `skills/executive-council/manifesto.md`
- **Removed**: `reference/migrate-tasks.sh` -- one-time v1.3 migration utility
- **Removed**: `.claude/settings.local.json` -- malformed permissions, plugins should not ship local settings
- **Changed**: Plugin name `"tars"` → `"TARS"` in plugin.json

### Added
- **2 composite skills**: `skills/meeting-processor/SKILL.md` and `skills/deep-analysis/SKILL.md` (converted from agents)
- **2 new commands**: `commands/meeting-processor.md` and `commands/deep-analysis.md`
- **YAML frontmatter** on all 23 commands (`description` + optional `argument-hint`)
- **`reference/schedule.md`**: Template for recurring and one-time scheduled items (heartbeat)
- **Heartbeat integration**: `/update` checks schedule (Step 1.5), `/daily-briefing` surfaces due items, `/setup` creates schedule template
- **Source attribution**: Confidence tiering added to `quick-answer`, `strategic-analysis`, `executive-council`, `validation-council`
- **`author` field** in plugin.json: `{"name": "Ajay John"}`
- **Filesystem MCP server** configured in `.mcp.json`
- **Routing entries** for composite skills (deep-analysis, meeting-processor)
- **Expanded plugin.json**: Added `author.url`, `repository`, `homepage`, `bugs`, `keywords`, `contributors` fields
- **`NOTICE` file**: Apache 2.0 attribution file at plugin root
- **Copyright headers**: Added to ARCHITECTURE.md and README.md
- **`.claude-plugin/marketplace.json`**: Marketplace catalog entry for distribution

### Changed
- Plugin version: `1.4.0` → `1.5.0`
- 3 thick commands (setup, update, rebuild-index) thinned to standard skill redirects
- Counts: 26 → 28 skills, 21 → 23 commands, 4 → 5 reference templates
- Version numbering corrected: what was previously labeled v2.0.0 is now v1.5.0 (the current state is a structural compliance rebuild, not the full architecture overhaul)

### Fixed
- All `data/` and `data/data/` path prefixes in `reference/taxonomy.md`
- Stale `protocols/meeting-processor.md` reference in `skills/extract-wisdom/SKILL.md`
- Stale `data/journal/` paths in `skills/process-meeting/meeting-context-query.md`
- Routing signal table now references `skills/deep-analysis/` instead of inline chain

---

## v1.4.0 (2026-02-06)

**Major architecture migration: protocols → native Claude plugin skills**

### Breaking changes
- **Removed**: protocols/ directory - all logic now in skills/
- **Removed**: install.sh - replaced by /setup skill
- **Removed**: build-plugins.sh and modular plugin system
- **Removed**: .claude/rules/ and .claude/commands/ - framework reads from plugin directly
- **Removed**: .agent/ Antigravity compatibility layer
- **Path change**: `data/` prefix removed from all workspace paths (data/memory/ → memory/)

### New architecture
- **26 skills** (7 background + 19 workflow): All with YAML frontmatter, user-invocable flag
- **21 commands**: Thin wrappers passing modes to skills
- **2 sub-agents**: meeting-processor, deep-analysis (orchestrate skill chains)
- **3-level loading**: L1 metadata (~105 tokens), L2 full skill, L3 supporting files
- **Provider-based integrations**: reference/integrations.md supports eventlink|mcp|none

### Token efficiency
- Session baseline: ~4,000 tokens saved (was ~4,200 for all behavioral skills, now ~105 for metadata only)
- L2 (full skill) loads on-demand, same cost as v1.3 protocol loading
- Net result: Significantly improved token efficiency with no functionality loss

### New skills (user-invocable workflow skills)
- process-meeting, extract-tasks, manage-tasks, extract-memory, extract-wisdom
- briefing (daily/weekly modes), communicate, strategic-analysis
- executive-council, validation-council, discovery-mode
- create-artifact, performance-report, initiative (planning/status modes)
- quick-answer, housekeeping, rebuild-index, setup, update

### Migration from v1.3.0
- Protocols merged into skills, behavioral constraints preserved
- All path references updated (removed data/ prefix)
- setup skill replaces install.sh + bootstrap command
- Signal table in routing skill now references skills/ not protocols/
- Reference files moved from data/reference/ to reference/ at plugin root

---

## [1.3.0] — 2026-02-04

### Added
- `/housekeeping` command and `protocols/housekeeping.md` for workspace maintenance and cleanup
- MCP discovery section in routing skill for detecting available integrations
- Decision status values in taxonomy (proposed, decided, implemented, superseded, rejected)
- Product specification frontmatter template in taxonomy
- Core concepts section in taxonomy (durability test, accountability test, index-first pattern)
- Auto-add unknown names to replacements.md with placeholder during meeting processing
- Calendar title priority hierarchy for meeting filename generation
- Contexts/products indexing in rebuild-index command
- Decision file naming validation in rebuild-index command
- MCP detection patterns and fallback hierarchy in CONNECTORS.md
- Migration scripts: `scripts/migrate-decisions.sh` and `scripts/add-product-frontmatter.sh`
- Bootstrap now creates `contexts/products/_index.md` and `contexts/artifacts/_index.md`
- Plugin decomposition: 6 modular plugins (core, memory, productivity, journal, analysis, comms)
- Plugin manifest: `plugins/manifest.json` with dependencies and presets
- `--plugins` flag for install.sh to select which plugins to install
- `.tars-plugins` marker file to track installed plugins
- `build-plugins.sh` script to package each plugin as a versioned zip file

### Changed
- **BREAKING**: Replaced `--no-antigravity` flag with `--platform <name>` flag in install.sh. Default is now Claude Code only (no `.agent/` generation). Use `--platform antigravity` to enable Antigravity shims. This prepares for future platform support.
- **BREAKING**: Consolidated user data under `data/` folder. Old paths (`memory/`, `journal/`, `contexts/`, `reference/`) are now `data/memory/`, `data/journal/`, `data/contexts/`, `data/reference/`. Existing workspaces need manual migration.
- Deprecated `tasks/` folder removed from scaffolding (tasks migrated to Apple Reminders via remindctl)
- Meeting processor Step 0.5 upgraded from RECOMMENDED to MANDATORY WHEN AVAILABLE
- Meeting frontmatter now includes `calendar_title`, `organizer`, and `source` fields
- Merged `reference/mcp-guide.md` into `reference/integrations.md` (token efficiency)
- Simplified 18 command files to routing stubs (reduced ~600 tokens per session)
- Routing table now lives only in `.claude/rules/07-routing.md`, removed from CLAUDE.md
- CLAUDE.md now references 21 commands and 17 protocols
- Install.sh now copies routing skill as `07-routing.md`
- Reference files reduced from 6 to 5

### Removed
- `reference/mcp-guide.md` (content merged into integrations.md)
- Routing table duplication in generated CLAUDE.md

---

## [1.2.0] — 2026-02-02

### Changed
- Antigravity workflows now contain inlined command content instead of redirect shims
- All 20 commands generate workflows automatically (was 13 manually-configured)
- `.agent/` generation loop auto-discovers commands (zero maintenance for new commands)

### Removed
- `.agent/skills/` directory and all 7 skill shims (consolidated into workflows)
- `generate_workflow()` and `generate_skill()` functions from install.sh
- Manual workflow/skill mapping in install.sh

---

## [1.1.0] — 2026-02-02

### Added
- `ARCHITECTURE.md` — comprehensive framework documentation (architecture, design decisions, maintenance guide)
- `CHANGELOG.md` — version history tracking
- `AGENTS.md` symlink — Antigravity reads `AGENTS.md` instead of `CLAUDE.md`; symlink ensures both clients share the same root config

### Fixed
- Antigravity workflow shims now include YAML `description` frontmatter (previously started with `# Title`, which Antigravity silently ignored)
- Antigravity skill shims now use folder/SKILL.md structure (`.agent/skills/<name>/SKILL.md`) instead of flat files (`.agent/skills/<name>.md`)
- Antigravity rules shim now concatenates full content of all 6 rule files instead of containing redirect pointers that Antigravity doesn't follow

---

## [1.0.0] — Initial release

### Added
- 7 skills: routing, identity, communication, memory management, task management, decision frameworks, clarification
- 20 commands: bootstrap, update, process-meeting, extract-memory, extract-tasks, extract-wisdom, daily-briefing, weekly-briefing, initiative-status, manage-tasks, quick-answer, communicate, strategic-analysis, executive-council, validation-council, discovery-mode, initiative-planning, create-artifact, performance-report, rebuild-index
- 16 protocols: meeting-processor, meeting-context, briefing-protocol, extract-wisdom, extract-memory, extract-tasks, initiative-planning, artifact-generation, search-protocol, stakeholder-comms, strategic-analysis, performance-report, executive-council, validation-council, text-refinement, discovery-mode
- 5 reference files: executive-council-manifesto, mcp-guide, taxonomy, replacements, kpis
- 8 connector categories with `~~placeholder` abstraction
- `install.sh` workspace expander for cowork and Antigravity compatibility
- `CLAUDE.md` generation with user block preservation, intelligent router, file map, cowork protocol
- `.agent/` shim layer for Antigravity (rules, workflows, skills)
- Plugin manifest (`plugin.json`) with skills, commands, and connectors
