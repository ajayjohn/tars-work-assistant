<!-- Copyright 2026 Ajay John. Licensed under Apache 2.0. See LICENSE. -->

# TARS v2.0.0 Architecture

> **Read this first.** This document gives any AI session (or human contributor) enough context to understand, modify, and extend the TARS v2.0.0 framework without re-analyzing every file.

**Version**: 2.0.0
**Release**: 2026-02-08
**Architecture**: Native Claude plugin with consolidated skills, provider-agnostic integrations, and scripted operations

---

## What TARS is

TARS is a **knowledge work assistant plugin** for Claude Code and Claude Cowork. It turns Claude into a persistent, context-aware executive assistant with memory, task management, meeting processing, strategic analysis, and stakeholder communications.

Target users: executives, senior ICs, and knowledge workers who need structured thinking support across recurring workflows.

**v2.0.0 key improvement**: Architecture consolidation. Skills reduced from 28→12 (~50%), commands from 23→11, and session baseline tokens drop to ~60 (from ~115 in v1.5.0). Deterministic operations extracted to 9 Python/shell scripts. Integration patterns provider-agnostic. Welcome flow simplified to 3 phases.

---

## Directory structure

### Plugin source

```
tars/
├── .claude-plugin/
│   ├── plugin.json                      # v2.0.0 manifest (12 skills, 11 commands)
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
│   ├── maintain/SKILL.md                # Workflow: health-check, sync, rebuild, inbox
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
│   └── runner.sh                        # Script orchestration (called by maintain skill)
├── reference/                           # 11 configuration files (copied to workspace by /welcome)
│   ├── integrations.md                  # Provider-agnostic registry (category/status/provider/type)
│   ├── taxonomy.md                      # Memory types, tags, frontmatter templates
│   ├── replacements.md                  # Name normalization (empty template)
│   ├── kpis.md                          # KPI definitions (empty template)
│   ├── schedule.md                      # Recurring/one-time scheduled items
│   ├── guardrails.yaml                  # Sensitive data patterns for scan-secrets.py
│   ├── maturity.yaml                    # Onboarding progress (updated by welcome phases)
│   ├── .housekeeping-state.yaml         # Auto-maintenance state (updated by maintain skill)
│   ├── getting-started.md               # New user guide
│   ├── workflows.md                     # Multi-skill patterns and orchestration
│   └── shortcuts.md                     # Quick reference of all commands
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

**Total**: 12 skills (1 background + 11 workflow), 11 commands, 11 reference templates, 9 scripts, 8 validation tests

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
│   ├── getting-started.md       # New user guide
│   ├── workflows.md             # Multi-skill patterns
│   └── shortcuts.md             # Command reference
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
- v2.0.0: ~60 tokens (metadata from 12 skills, plus housekeeping state check)
- **Net savings**: ~55 tokens per session, ~50% skill reduction

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
| **meeting** | Meeting transcript processing (full pipeline) | Speaker identification • Emotion analysis • Action item extraction |
| **tasks** | Extract + manage tasks | Priority classification • Dependency mapping |
| **learn** | Memory persistence + wisdom extraction | Source extraction • Relevance scoring |
| **think** | Strategic analysis, debate, stress-test, deep analysis, discovery | Strategic analysis (Tree of Thoughts) • Executive council (CPO/CTO personas) • Validation council (adversarial stress-test) • Discovery mode (no-solution deep) |
| **briefing** | Daily + weekly briefings | Agenda assembly • Insight synthesis |
| **initiative** | Initiative planning, status, performance | Plan (structure, timeline, risks) • Status (progress, blockers, adjustments) • Performance (KPI analysis) |
| **maintain** | Health-check, sync, rebuild, inbox processing | Health checks • Script orchestration via runner.sh/runner.py |
| **welcome** | Progressive onboarding (3 phases) | Phase 1: Instant setup (directories + CLAUDE.md) • Phase 2: First win (sample memory, journal entry) • Phase 3: Background learning (system walkthrough) |
| **communicate** | Stakeholder communications | Text refinement (tone, structure, clarity) |
| **create** | Decks, narratives, speeches | Outline generation • Content assembly • Visual notes |
| **answer** | Fast factual lookups | Query parsing • Source routing • Confidence tiering |

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
**Provider**: cli
**Implementation**: remindctl
**Operations**: list-tasks, create-task, complete-task, update-task
```

Skills reference **categories** (calendar, tasks, email, documents, etc.), not specific tools. This allows users to swap providers without skill modifications:

- **http-api**: REST endpoints (Zapier, custom APIs)
- **cli**: Command-line tools (remindctl, curl)
- **mcp**: Model Context Protocol servers

The `/welcome` skill auto-detects providers via `verify-integrations.py` and updates status.

---

## Key v2.0.0 innovations

### 1. Skill consolidation
28 skills → 12 skills (~50% reduction). Related workflow skills merged (e.g., strategic-analysis + executive-council + validation-council + discovery-mode → think). All 7 background skills → core.

### 2. Script extraction
9 Python/shell scripts handle deterministic operations:
- `health-check.py`: Workspace scan
- `rebuild-indexes.py`: Index regeneration
- `scaffold.sh`: Directory initialization
- `sync.py`: Task + inbox triage
- `archive.py`: 4-tier content archival (durable/seasonal/transient/ephemeral)
- `verify-integrations.py`: Provider auto-detection
- `scan-secrets.py`: Sensitive data pattern detection (via guardrails.yaml)
- `bump-version.py`: Version management
- `runner.sh`: Script orchestration

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
Skills invoke sub-agents for specific tasks (e.g., meeting skill spawns agents for speaker ID, emotion analysis, action extraction). Reduces latency.

### 9. Automated daily housekeeping
`maintain` skill runs at session start (via housekeeping check in core routing). Calls `runner.sh` to orchestrate:
- Health check
- Sync pending tasks + inbox
- Archive stale content
- Scan for sensitive data leaks

State tracked in `.housekeeping-state.yaml` (last run, detected issues).

### 10. Inline help metadata
YAML frontmatter in all skills includes:
```yaml
---
name: meeting
description: Process meeting transcripts
user-invocable: true
help:
  purpose: "Extract actions, decisions, and insights from meeting transcripts"
  use_cases:
    - "Turn recorded call into actionable task list"
    - "Capture decisions with context for memory"
  invoke_examples:
    - "Process this Zoom transcript"
    - "/meeting"
  common_questions:
    - "How do you handle side conversations?"
    - "Can you identify speakers automatically?"
  related_skills: [tasks, learn, communicate]
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

---

## Help system

Inline help metadata in YAML frontmatter enables contextual help without loading full skill content:

```yaml
help:
  purpose: "High-level description of what this skill does"
  use_cases:
    - "Specific user scenario 1"
    - "Specific user scenario 2"
  invoke_examples:
    - "Example voice command"
    - "/command syntax"
  common_questions:
    - "FAQ question 1"
    - "FAQ question 2"
  related_skills: [skill_name1, skill_name2]
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

**Problem**: Loading 7 separate behavioral skills at session start costs ~28 tokens.
**Solution**: Consolidate into one core skill with internal sections (Identity, Communication, Routing, etc.).
**Result**: Token savings (~24 tokens/session), single source of truth for behavioral constraints, easier to maintain.

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
**Solution**: Maintain skill runs at session start (via housekeeping check in core routing). Calls runner.sh to execute health-check.py, sync.py, archive.py, scan-secrets.py.
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
     invoke_examples: [...]
     common_questions: [...]
     related_skills: [...]
   ---
   ```
2. Add to `.claude-plugin/plugin.json` skills array
3. Create `commands/new-skill.md` with YAML frontmatter (`description`, optional `argument-hint`)
4. Add to `.claude-plugin/plugin.json` commands array
5. Update `skills/core/SKILL.md` signal table if the skill handles new signal types

### Adding a new script

1. Create `scripts/new-script.py` or `scripts/new-script.sh`
2. Add to `scripts/runner.sh` or `scripts/runner.py` orchestration
3. Add test file in `tests/validate-new-script.py`
4. Add to `.github/workflows/validate.yml`

### Adding a new integration category

1. Document in `reference/integrations.md` with category, provider options, operations
2. Update `scripts/verify-integrations.py` to auto-detect (if applicable)
3. Add validation to `tests/validate-integrations.py`
4. Skills reference category name (calendar, tasks, etc.), not provider

---

## Performance characteristics

| Metric | v1.5.0 | v2.0.0 | Change |
|--------|--------|--------|--------|
| Session baseline tokens | ~115 | ~60 | -47% |
| Skill count | 28 | 12 | -57% |
| Command count | 23 | 11 | -52% |
| Workflow skills | 19 | 11 | -42% |
| Background skills | 7 | 1 | -86% |
| Scripts | 0 | 9 | +9 new |
| Integration coupling | Hardcoded tool names | Provider-agnostic registry | **Decoupled** |
| Workspace token baseline (at session start) | ~300 tokens (core files) | ~240 tokens (core + state) | -20% |

---

## Version history

- **v2.0.0** (2026-02-08): Architecture overhaul (skill consolidation, script extraction, provider-agnostic integrations, progressive welcome, 4-tier archival, housekeeping automation)
- **v1.5.0** (2026-02-07): Structural compliance, composite skills, heartbeat, source attribution
- **v1.4.0** (2026-02-06): Protocol-to-skill migration, 3-level loading, provider abstraction
- **v1.3.0** (2026-02-04): Plugin decomposition, data/ consolidation
- **v1.2.0** (2026-02-02): Antigravity workflow inlining
- **v1.1.0** (2026-02-02): Architecture documentation
- **v1.0.0**: Initial release

---

## Migration from v1.5.0

### What changed

| v1.5.0 | v2.0.0 | Reason |
|--------|--------|--------|
| 7 background skills | 1 core skill | Token efficiency, behavioral consolidation |
| 19 workflow skills | 11 workflow skills | Merge related workflows (e.g., strategic-analysis + councils → think) |
| 2 composite skills | 0 composite skills (merged into single skills) | Simplification (think skill handles all analysis modes) |
| 0 scripts | 9 scripts | Deterministic ops (health checks, archival, index rebuild) moved to Python/shell |
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
