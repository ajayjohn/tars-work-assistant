# Changelog

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
- **Getting started guide**: reference/getting-started.md for new users
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
