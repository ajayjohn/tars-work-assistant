<!-- Copyright 2026 Ajay John. Licensed under Apache 2.0. See LICENSE. -->

# TARS 2.2.0 Architecture

> **Read this first.** This document gives any AI session (or human contributor) enough context to understand, modify, and extend the TARS framework without re-analyzing every file.

**Version**: 2.2.0
**Release**: 2026-02-19
**Architecture**: Native Claude plugin with consolidated skills, provider-agnostic integrations, and scripted operations

---

## What TARS is

TARS is a **knowledge work assistant plugin** for Claude Code and Claude Cowork. It turns Claude into a persistent, context-aware executive assistant with memory, task management, meeting processing, strategic analysis, and stakeholder communications.

Target users: executives, senior ICs, and knowledge workers who need structured thinking support across recurring workflows.

**Key improvement**: Architecture consolidation. Skills reduced from 28→12 (~50%), commands from 23→11, and session baseline tokens drop to ~48 (from ~115 in v1.5.0). Deterministic operations extracted to 11 Python/shell scripts. Integration patterns provider-agnostic. Welcome flow simplified to 3 phases.

---

## Directory structure

### Plugin source

```
tars/
├── .claude-plugin/
│   ├── plugin.json                      # Manifest (12 skills, 11 commands)
│   └── marketplace.json                 # Marketplace catalog entry
├── .mcp.json                            # Filesystem MCP server configured
├── skills/
│   ├── core/SKILL.md                    # Background: identity, communication, routing, memory, task, decision, clarification (merged)
│   ├── meeting/SKILL.md                 # Workflow: meeting transcript processing (full pipeline with sub-agents)
│   ├── tasks/SKILL.md                   # Workflow: extract + manage tasks
│   ├── learn/SKILL.md                   # Workflow: memory persistence + wisdom extraction
│   ├── think/SKILL.md                   # Workflow: strategic analysis, debate, stress-test, deep, discover (+ manifesto.md)
│   ├── briefing/SKILL.md                # Workflow: daily + weekly briefings
│   ├── initiative/SKILL.md              # Workflow: plan, status, performance
│   ├── maintain/SKILL.md                # Workflow: health-check, sync, rebuild, inbox, update
│   ├── welcome/SKILL.md                 # Workflow: progressive onboarding (3 phases)
│   ├── communicate/SKILL.md             # Workflow: stakeholder comms (+ text-refinement.md)
│   ├── create/SKILL.md                  # Workflow: decks, narratives, speeches
│   └── answer/SKILL.md                  # Workflow: fast factual lookups
├── commands/                            # 11 thin wrappers
│   ├── meeting.md, tasks.md, learn.md, think.md, briefing.md
│   ├── initiative.md, maintain.md, welcome.md, communicate.md
│   ├── create.md, answer.md
├── scripts/
│   ├── health-check.py                  # Workspace health scan
│   ├── rebuild-indexes.py               # Regenerate all indexes
│   ├── scaffold.sh                      # Workspace directory initialization
│   ├── sync.py                          # Sync tasks + triage inbox
│   ├── archive.py                       # 4-tier archival (durable/seasonal/transient/ephemeral)
│   ├── verify-integrations.py           # Auto-detect and validate provider status
│   ├── scan-secrets.py                  # Sensitive data pattern detection
│   ├── bump-version.py                  # Version management
│   ├── build-plugin.sh                  # Plugin packaging for distribution
│   ├── validate-plugin.py               # Plugin structure validation
│   └── update-reference.py              # Workspace reference file updater (preserves user data)
├── reference/                           # 11 configuration files (copied to workspace by /welcome)
│   ├── integrations.md                  # Provider-agnostic registry (category/status/provider/type)
│   ├── taxonomy.md                      # Memory types, tags, frontmatter templates
│   ├── replacements.md                  # Name normalization (empty template)
│   ├── kpis.md                          # KPI definitions (empty template)
│   ├── schedule.md                      # Recurring/one-time scheduled items
│   ├── guardrails.yaml                  # Sensitive data patterns for scan-secrets.py
│   ├── maturity.yaml                    # Onboarding progress (updated by welcome phases)
│   ├── .housekeeping-state.yaml         # Auto-maintenance state (updated by maintain skill)
│   ├── workflows.md                     # Multi-skill patterns and orchestration
│   └── shortcuts.md                     # Quick reference of all commands
<truncated 5 lines>
├── GETTING-STARTED.md                   # New user guide
├── inbox/
│   ├── pending/                         # Awaiting processing
│   ├── processing/                      # Currently being handled
│   ├── completed/                       # Successfully processed
│   └── failed/                          # Processing errors (requires manual review)
├── archive/
│   ├── durable/                         # Strategic decisions, people profiles, long-lived context
│   ├── seasonal/                        # Annual cycles, quarterly planning, project history
│   ├── transient/                       # Weekly briefings, past initiatives, 30-90 day context
│   └── ephemeral/                       # Raw transcripts, intermediate drafts, debugging logs
├── memory/
│   ├── _index.md                        # Master index
│   ├── people/
│   ├── vendors/
│   ├── competitors/
│   ├── products/
│   ├── initiatives/
│   ├── decisions/
│   └── organizational-context/
├── journal/                             # YYYY-MM/ subdirectories
│   └── YYYY-MM/                         # Timestamped entries
├── tests/
│   ├── validate-frontmatter.py          # Check YAML in all skills
│   ├── validate-references.py           # Verify all cross-links
│   ├── validate-plugin.json.py          # Check manifest integrity
│   ├── validate-integrations.py         # Provider registry structure
│   ├── validate-scripts.py              # Python/shell syntax
│   ├── validate-workspace.py            # Workspace structure after welcome
│   ├── integration-simulation.py        # Mock integration calls
│   └── runner.py                        # Test orchestration
├── .github/workflows/
│   ├── validate.yml                     # Pre-commit: syntax, references, manifest
│   └── release.yml                      # Release: bump version, tag, build
├── ARCHITECTURE.md
├── CHANGELOG.md
├── README.md
├── CATALOG.md
├── NOTICE
├── LICENSE
└── ROADMAP.md
```

**Total**: 12 skills (1 background + 11 workflow), 11 commands, 11 reference templates, 11 scripts, 8 validation tests

### Workspace (created by /welcome)

```
{workspace}/
├── CLAUDE.md                    # Generated: user profile, integration status, file map
├── reference/
│   ├── integrations.md          # Provider-agnostic registry
│   ├── taxonomy.md              # Memory types, frontmatter templates
│   ├── replacements.md          # Name normalization mappings
│   ├── kpis.md                  # Team/initiative KPI definitions
│   ├── schedule.md              # Recurring/one-time scheduled items
│   ├── guardrails.yaml          # Sensitive data patterns
│   ├── maturity.yaml            # Onboarding progress tracking
│   ├── .housekeeping-state.yaml # Auto-maintenance state
│   ├── workflows.md             # Multi-skill patterns
│   └── shortcuts.md             # Command reference
├── GETTING-STARTED.md           # New user guide
├── memory/
│   ├── _index.md                # Master index
│   ├── people/
│   │   └── _index.md
│   ├── vendors/
│   │   └── _index.md
│   ├── competitors/
│   │   └── _index.md
│   ├── products/
│   │   └── _index.md
│   ├── initiatives/
│   │   └── _index.md
│   ├── decisions/
│   │   └── _index.md
│   └── organizational-context/
│       └── _index.md
├── journal/                     # YYYY-MM/ subdirectories
│   └── YYYY-MM/
├── inbox/
│   ├── pending/
│   ├── processing/
│   ├── completed/
│   └── failed/
├── archive/
│   ├── durable/
│   ├── seasonal/
│   ├── transient/
│   └── ephemeral/
└── contexts/
    ├── products/
    └── artifacts/
```

---

## 3-level loading model

This architecture provides dramatic token savings while maintaining full feature access.

| Level | What loads | When | Token cost |
|-------|-----------|------|------------|
| **L1 (metadata)** | `name` + `description` from YAML frontmatter | Every session start, all 12 skills | ~4 tokens/skill × 12 = ~48 tokens |
| **L2 (instructions)** | Full SKILL.md body | When skill is triggered via command or signal | Same as v1.5.0 protocol loading |
| **L3 (resources)** | Supporting files in skill directory | When explicitly referenced (e.g., manifesto.md, text-refinement.md) | Same as v1.5.0 reference file loading |

**Session baseline comparison**:
- v1.5.0: ~115 tokens (metadata from 28 skills)
- v2.2.0: ~48 tokens (metadata from 12 skills at ~4 tokens each)
- **Net savings**: ~67 tokens per session, ~58% reduction

---

## Skill architecture

### Background skill (1 total, user-invocable: false)

Merged behavioral framework. Defines how TARS operates.

| Skill | Contains |
|-------|----------|
| **core** | Identity (role, truth sources, user profile) • Communication (BLUF, anti-sycophancy, banned phrases) • Memory management (durability test, wikilinks, folder mapping) • Task management (accountability test, date resolution) • Decision frameworks (framework catalog) • Clarification (bounded techniques) • Routing (signal table, auto side-effects) |

**Why merge?** Token efficiency (single ~4 token load vs. 7 separate loads) + single source of truth for behavioral constraints.

### Workflow skills (11 total, user-invocable: true)

User-invocable skills containing complete workflow logic. Sub-agents handle parallelization where needed.

| Skill | Purpose | Sub-agents |
|-------|---------|-----------|
| **meeting** | Meeting transcript processing (full pipeline) | Task extraction (parallel) • Memory extraction (parallel) |
| **tasks** | Extract + manage tasks | None (single-threaded pipeline) |
| **learn** | Memory persistence + wisdom extraction | None (single-threaded pipeline) |
| **think** | Strategic analysis, debate, stress-test, deep analysis, discovery | Deep mode: Validation council (parallel) • Executive council (parallel) |
| **briefing** | Daily + weekly briefings | Calendar fetch (parallel) • Task fetch (parallel) • Memory query (parallel) |
| **initiative** | Initiative planning, status, performance | None (modes: plan, status, performance) |
| **maintain** | Health-check, sync, rebuild, inbox processing, reference file updates | Inbox mode: one sub-agent per inbox item (parallel) |
| **welcome** | Progressive onboarding (3 phases) | None (modes: phase 1, phase 2, phase 3) |
| **communicate** | Stakeholder communications | None (uses text-refinement.md resource) |
| **create** | Decks, narratives, speeches | None (single-threaded pipeline) |
| **answer** | Fast factual lookups | None (index-first search hierarchy) |

---

## Provider-agnostic integration registry

The `reference/integrations.md` file uses a category-based structure instead of hardcoding tool names:

```yaml
## Calendar integration
**Category**: calendar
**Status**: connected / disconnected / unavailable
**Provider**: http-api | cli | mcp
**Implementation**: [provider details]
**Operations**: read-events, create-event, update-event, delete-event
**Config**: [authentication, rate limits, fields]
**Constraints**: [limitations, data format]

## Task integration
**Category**: tasks
**Status**: connected
**Provider**: mcp
**Implementation**: [provider-specific details]
**Operations**: list-tasks, create-task, complete-task, update-task
```

Skills reference **categories** (calendar, tasks, email, documents, etc.), not specific tools. This allows users to swap providers without skill modifications:

- **http-api**: REST endpoints (Zapier, custom APIs)
- **cli**: Command-line tools
- **mcp**: Model Context Protocol servers

The `/welcome` skill auto-detects providers via `verify-integrations.py` and updates status.

---

## Key 2.1.0 innovations

### 1. Skill consolidation
28 skills → 12 skills (~50% reduction). Related workflow skills merged (e.g., strategic-analysis + executive-council + validation-council + discovery-mode → think). All 7 background skills → core.

### 2. Script extraction
11 Python/shell scripts handle deterministic operations:
- `health-check.py`: Workspace scan
- `rebuild-indexes.py`: Index regeneration
- `scaffold.sh`: Directory initialization
- `sync.py`: Task + inbox triage
- `archive.py`: 4-tier content archival (durable/seasonal/transient/ephemeral)
- `verify-integrations.py`: Provider auto-detection
- `scan-secrets.py`: Sensitive data pattern detection (via guardrails.yaml)
- `bump-version.py`: Version management
- `build-plugin.sh`: Plugin packaging for distribution
- `validate-plugin.py`: Plugin structure validation
- `update-reference.py`: Workspace reference file updater (preserves user customizations)

Benefits: Cheaper (no token overhead), more reliable (no hallucination), easier to test, auditable.

### 3. Provider-agnostic integration registry
Replaces hardcoded tool references. Category-based (calendar, tasks, email, documents) supports multiple provider types (http-api, cli, mcp). Users can swap implementations without touching skills.

### 4. Progressive welcome flow
3 phases instead of 4-round interrogation:
- **Phase 1** (instant): Directory scaffold, CLAUDE.md generation, reference files copied
- **Phase 2** (first win): Sample memory entry, journal entry, inbox setup
- **Phase 3** (background): System walkthrough, decision framework intro, integration review

Friction reduced, faster time-to-value.

### 5. YAML-based indexes
Replaced pipe tables with YAML frontmatter in index files. Enables editability, parseability, extensibility.

### 6. 4-tier content archival
- **Durable**: Strategic decisions, people profiles, long-lived context (keep 3+ years)
- **Seasonal**: Annual cycles, quarterly planning, project history (keep 1-2 years)
- **Transient**: Weekly briefings, past initiatives, 30-90 day context (keep 3-6 months)
- **Ephemeral**: Raw transcripts, intermediate drafts, debugging logs (keep 1-2 weeks)

`archive.py` moves content automatically based on date + category.

### 7. Batch processing inbox
Four directories (pending/processing/completed/failed) enable asynchronous processing. Items can be queued for later processing without blocking the user.

### 8. Sub-agent parallelization
Skills invoke sub-agents for parallel execution. Meeting skill spawns parallel agents for task extraction and memory extraction. Briefing skill spawns parallel agents for calendar, tasks, and memory queries. Think skill (deep mode) spawns parallel validation and executive council agents. Maintain skill (inbox mode) spawns one agent per inbox item.

### 9. Automated daily housekeeping
`maintain` skill runs at session start (via housekeeping check in core routing). Executes scripts directly:
- `health-check.py`: Workspace health scan
- `sync.py`: Sync pending tasks + inbox
- `archive.py`: Archive stale content
- `scan-secrets.py`: Sensitive data detection

State tracked in `.housekeeping-state.yaml` (last run, detected issues).

### 10. Inline help metadata
YAML frontmatter in all skills includes:
```yaml
---
name: meeting
description: Process meeting transcripts to extract reports, tasks, and memory.
user-invocable: true
help:
  purpose: |-
    Process meeting transcripts with automatic extraction and calendar integration.
  use_cases:
    - "Process this meeting [transcript]"
    - "Extract action items from this meeting"
  scope: meetings,transcripts,action-items
---
```

`core` skill handles help routing (user asks "help think" → loads think/SKILL.md help metadata).

### 11. Sensitive data guardrails
`guardrails.yaml` defines patterns:
```yaml
patterns:
  - name: api_key
    regex: '(api[_-]?key|apikey|api_secret)\s*[=:]\s*["\']?[a-z0-9]{32,}'
    severity: critical
    action: redact
  - name: email
    regex: '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}'
    severity: low
    action: flag
```

`scan-secrets.py` runs hourly (via maintain), reports findings to failed/ inbox.

### 12. CI/CD pipeline
`.github/workflows/`:
- **validate.yml**: Pre-commit checks (frontmatter, references, manifest, scripts)
- **release.yml**: Release automation (version bump, changelog, tag, build)

### 13. Global communication rules
BLUF, anti-sycophancy, banned phrases apply to **ALL** skill outputs, not just the communication skill. Enforced by core skill.

### 14. Reference file update mechanism
`update-reference.py` surgically updates workspace reference files when the plugin is updated, preserving user customizations (name replacements, KPI definitions, schedule items). Three merge strategies: `full_replace` (files with no user data), `section_merge` (markdown files with mixed template/user sections), `additive_merge` (YAML state files). Version tracked via `plugin_version` in `.housekeeping-state.yaml`. Invoked via `/maintain update`.

### 15. Task creation verification
All task creation paths (meeting, inbox, tasks skills) include mandatory post-creation verification. After creating tasks via MCP, skills call `list_reminders` to confirm tasks actually appear in the target list. Prevents silent failures where tasks are reported as created but never reach the task manager.

---

## Help system

Inline help metadata in YAML frontmatter enables contextual help without loading full skill content:

```yaml
help:
  purpose: |-
    High-level description of what this skill does.
  use_cases:
    - "Specific user scenario 1"
    - "Specific user scenario 2"
  scope: comma,separated,keywords
```

When user asks "help think":
1. Core routing detects help request
2. Loads think/SKILL.md YAML frontmatter only (~10 tokens)
3. Returns formatted help content
4. User can invoke full skill if needed

---

## Signal-based routing

The `core` skill maps natural language signals to skills:

| Signal | Routes to | Handler |
|--------|-----------|---------|
| Meeting transcript | meeting/ | Full pipeline with sub-agents |
| Task extraction | tasks/ | Batch extraction + placement |
| Memory persistence | learn/ | Durability test + wikilinks |
| Communication draft | communicate/ | Text refinement |
| Schedule/calendar query | answer/ | Fast lookup with sources |
| Strategic analysis request | think/ | Tree of Thoughts or council |
| Plan creation | initiative/ | Scaffold, timeline, risks |
| System maintenance | maintain/ | Health check, sync, archive |
| First-time setup | welcome/ | 3-phase onboarding |
| Content creation | create/ | Deck, narrative, speech |

Commands are shortcuts. Natural language is the primary interface. Core skill detects signal and invokes appropriate skill automatically.

---

## Design decisions

### Why merge 7 background skills into core?

**Problem**: Loading 7 separate behavioral skills at session start costs ~28 tokens (7 × ~4 tokens each).
**Solution**: Consolidate into one core skill with internal sections (Identity, Communication, Routing, etc.).
**Result**: Token savings, single source of truth for behavioral constraints, easier to maintain.

### Why extract scripts?

**Problem**: Deterministic operations (health checks, archive, indexing) consume tokens and risk hallucination.
**Solution**: Move to Python/shell scripts (health-check.py, archive.py, rebuild-indexes.py, etc.).
**Result**: Cheaper execution, higher reliability, clearer intent, easier to test and audit.

### Why provider-agnostic integrations?

**Problem**: Different users have different tools (some use Google Calendar, others Outlook; some use Asana, others Jira). Hardcoding tool references creates maintenance burden and limits flexibility.
**Solution**: Category-based registry (calendar, tasks, email, documents) supporting multiple provider types (http-api, cli, mcp).
**Result**: Users can swap implementations without editing skills. New integrations don't require skill modifications.

### Why 3-phase progressive welcome?

**Problem**: v1.5.0 welcome skill uses 4-round interrogation (profile questions, integration setup, preferences, system walkthrough). High friction, slow time-to-value.
**Solution**: Phase 1 = instant setup (scaffold + CLAUDE.md). Phase 2 = first win (sample memory + journal). Phase 3 = background learning (system walkthrough).
**Result**: User productive in minutes, not interrogations. Can learn system gradually. Phases are optional (skip if confident).

### Why YAML-based indexes?

**Problem**: Pipe-delimited tables are hard to edit manually, don't parse cleanly, don't support multi-line values.
**Solution**: YAML frontmatter in index files (memory/_index.md, journal/_index.md, etc.).
**Result**: Editability (users can update by hand), parseability (skills/scripts can extract structured data), extensibility (new fields don't break parsing).

### Why 4-tier archival?

**Problem**: Single archive directory grows unbounded. Can't distinguish recent context (needed for briefings) from long-ago decisions (historical reference).
**Solution**: Tiers (durable/seasonal/transient/ephemeral) with different retention policies.
**Result**: Smart pruning without data loss. Briefing skill surfaces only recent context. Historical queries still possible.

### Why automated housekeeping?

**Problem**: Users forget to run maintenance. Indexes get stale, inbox fills up, sensitive data lingers.
**Solution**: Maintain skill runs at session start (via housekeeping check in core routing). Executes health-check.py, sync.py, archive.py, scan-secrets.py directly.
**Result**: Consistent state, automatic cleanup, proactive security scanning. State tracked in .housekeeping-state.yaml.

---

## Extending TARS

### Adding a new workflow skill

1. Create `skills/new-skill/SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: new-skill
   description: "Human-readable description"
   user-invocable: true
   help:
     purpose: "..."
     use_cases: [...]
     scope: keyword1,keyword2
   ---
   ```
2. Add to `.claude-plugin/plugin.json` skills array
3. Create `commands/new-skill.md` with YAML frontmatter (`description`, optional `argument-hint`)
4. Add to `.claude-plugin/plugin.json` commands array
5. Update `skills/core/SKILL.md` signal table if the skill handles new signal types

### Adding a new script

1. Create `scripts/new-script.py` or `scripts/new-script.sh`
2. Reference from the appropriate skill (maintain skill calls scripts directly)
3. Add test file in `tests/validate-new-script.py`
4. Add to `.github/workflows/validate.yml`
5. Update this document's script count and directory listing

### Adding a new integration category

1. Document in `reference/integrations.md` with category, provider options, operations
2. Update `scripts/verify-integrations.py` to auto-detect (if applicable)
3. Add validation to `tests/validate-integrations.py`
4. Skills reference category name (calendar, tasks, etc.), not provider

---

## Performance characteristics

| Metric | v1.5.0 | v2.2.0 | Change |
|--------|--------|--------|--------|
| Session baseline tokens | ~115 | ~48 | -58% |
| Skill count | 28 | 12 | -57% |
| Command count | 23 | 11 | -52% |
| Workflow skills | 19 | 11 | -42% |
| Background skills | 7 | 1 | -86% |
| Scripts | 0 | 11 | +11 new |
| Integration coupling | Hardcoded tool names | Provider-agnostic registry | **Decoupled** |

---

## Version history

- **v2.2.0** (2026-02-19): Framework audit — documentation consistency fixes, efficiency improvements, automated validation (validate-docs.py), CONTRIBUTING.md
- **v2.1.0** (2026-02-08): Task verification, reference file updates, inbox sub-agent expansion
- **v1.5.0** (2026-02-07): Structural compliance, composite skills, heartbeat, source attribution
- **v1.4.0** (2026-02-06): Protocol-to-skill migration, 3-level loading, provider abstraction
- **v1.3.0** (2026-02-04): Plugin decomposition, data/ consolidation
- **v1.2.0** (2026-02-02): Antigravity workflow inlining
- **v1.1.0** (2026-02-02): Architecture documentation
- **v1.0.0**: Initial release

---

## Migration from v1.5.0

### What changed

| v1.5.0 | 2.1.0 | Reason |
|--------|--------|--------|
| 7 background skills | 1 core skill | Token efficiency, behavioral consolidation |
| 19 workflow skills | 11 workflow skills | Merge related workflows (e.g., strategic-analysis + councils → think) |
| 2 composite skills | 0 composite skills (merged into single skills) | Simplification (think skill handles all analysis modes) |
| 0 scripts | 11 scripts | Deterministic ops (health checks, archival, index rebuild, reference updates) moved to Python/shell |
| Hardcoded tool references | Provider-agnostic registry | Flexibility (users can swap tools) |
| 5 reference templates | 11 reference templates | Added guardrails.yaml, maturity.yaml, .housekeeping-state.yaml, getting-started.md, workflows.md, shortcuts.md |
| Single archive/ directory | 4-tier archive (durable/seasonal/transient/ephemeral) | Smart retention, briefing relevance |
| Manual housekeeping | Automated housekeeping at session start | Health checks, sync, archival, secret scanning all automatic |
| 4-round welcome interrogation | 3-phase progressive welcome | Faster time-to-value, optional phases |

### What stayed the same

- All workflow capabilities preserved (100% feature parity for user-facing operations)
- All behavioral constraints preserved (BLUF, anti-sycophancy, decision frameworks, etc.)
- Memory durability test, task accountability test, source confidence tiering
- Index-first pattern, context budgets
- Meeting transcript → action pipeline
- Strategic analysis (Tree of Thoughts, councils, discovery)
- Briefing generation (daily/weekly)
- Task extraction and management

---

## Maintain skill: internal procedures

> **Developer reference.** These procedures describe what the automated scripts do internally. They are preserved here for maintenance and troubleshooting. The maintain skill references this section for fallback procedures when scripts are unavailable.

### Health check procedures (health-check.py)

**Naming pattern validation (decisions):**
- Standard pattern: `YYYY-MM-DD-{slug}.md`
- Violations: missing date prefix, context-first ordering (`topic-YYYY-MM-DD.md`), no date anywhere
- Auto-fix: if frontmatter contains `date` field, suggest rename command

**Frontmatter validation:**
| Type | Required fields |
|------|-----------------|
| All memory | `title`, `type`, `summary`, `updated` |
| person | + `tags`, `aliases` |
| decision | + `status` (proposed/decided/implemented/superseded/rejected), `decision_maker` |
| product-spec | + `status` (active/planned/deprecated), `owner` |

**Index synchronization:**
- Compare `_index.md` entries against actual `.md` files in each memory category folder
- Flag orphan index entries (entry without file) and unlisted files (file without index entry)
- Flag stale summaries where file `updated` date is newer than index regeneration

**Broken wikilink detection:**
- Scan all files in `memory/`, `journal/`, `contexts/` for `[[Entity Name]]` patterns
- Cross-reference against all memory category indexes (people, initiatives, products, decisions)
- Flag wikilinks referencing non-existent entities

**Replacements coverage:**
- Scan journal files from last 30 days for capitalized multi-word names and acronyms (2-4 caps)
- Cross-reference against `reference/replacements.md`
- Flag names appearing multiple times but not in replacements
- Auto-fix: add flagged items with placeholder `?? (needs canonical form)`

### Rebuild procedures (rebuild-indexes.py)

**Memory indexes:** For each category (people, initiatives, decisions, products, vendors, competitors, organizational-context): scan `.md` files excluding `_index.md`/`_template.md`, read frontmatter (`title`, `aliases`, `tags`, `summary`, `updated`), generate index table. Initiatives split into Active/Completed sections.

**Master index:** Generate `memory/_index.md` with category paths and file counts.

**Journal indexes:** For each month folder, scan `.md` files, read frontmatter (`date`, `type`, `title`, `participants`, `initiatives`), generate month index table.

**Contexts/products index:** Scan `contexts/products/`, read frontmatter (`title`, `type`, `status`, `owner`, `summary`, `updated`), generate product specs index.

**Decision naming validation:** Check all files in `memory/decisions/` match `YYYY-MM-DD-{slug}.md` pattern. Flag violations with suggested renames.

### Archive tier definitions (archive.py)

| Tier | Retention | Examples |
|------|-----------|---------|
| Durable | Indefinite | People profiles, strategic decisions, initiative docs |
| Seasonal | 6-12 months | Quarterly reports, sprint retrospectives |
| Transient | 30-90 days | Meeting notes for completed initiatives |
| Ephemeral | 7-14 days | Draft content, temporary working notes |

Lines with `[expires: YYYY-MM-DD]` markers are removed when past their date. Files matching staleness thresholds for their tier are moved to `archive/`.

---
