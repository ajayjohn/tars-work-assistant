# TARS v2: Obsidian-native rebuild plan

**Date**: 2026-03-21
**Status**: Comprehensive implementation plan for the AI agent building TARS v2

---

## Part 1: What this plan is

This is the complete blueprint for rebuilding TARS as an Obsidian-native knowledge-work operating system. It synthesizes:

- A deep analysis of the current TARS framework (all skills, scripts, reference files, live deployment evidence)
- A full analysis of the obsidian-skills platform (obsidian-cli, obsidian-markdown, obsidian-bases, json-canvas, defuddle)
- An architectural design for the new system
- Functional specifications for every capability
- A pressure-test analysis identifying failure modes, guardrails, and testing requirements

The agent building TARS v2 should treat this plan as authoritative but not rigid. Where implementation reveals a better approach, deviate and document why.

---

## Part 2: Design philosophy

### What TARS is

TARS is a persistent executive assistant for knowledge workers. It provides continuity, structure, follow-through, and strategic rigor across time. It is not a prompt library or a chatbot. It is an operating layer.

### What changes in v2

| Aspect | v1 (current) | v2 (rebuild) |
|--------|-------------|--------------|
| Interface | Claude Code filesystem I/O | Obsidian vault via obsidian-cli |
| Indexes | Hand-maintained `_index.md` files | Obsidian Bases (.base live queries) |
| Templates | Markdown text blobs | Obsidian templates with frontmatter |
| Metadata | Inconsistent YAML | Obsidian-native properties (typed) |
| Links | Wikilinks (manually verified) | Obsidian wikilinks (alias-resolved, graph-backed) |
| Name resolution | `replacements.md` table lookup | Obsidian aliases + registry + search |
| Locking | `.lock` file convention | Obsidian-cli serializes writes |
| Distribution | Duplicated plugin folders | Single source tree |
| Orchestration | Prompt-only sub-agents | Agent + deterministic scripts |
| Maintenance | Described in prompts | Scripts + ambient scheduled jobs |

### What does NOT change

- The memory entity model (people, initiatives, decisions, products, vendors, competitors, org-context)
- The durability test for memory persistence
- The accountability test for task creation
- Meeting processing as the highest-value pipeline
- Journal-first persistence of meaningful outputs
- Provider-agnostic integration architecture
- Strategic thinking modes
- Stakeholder-aware communication
- Guardrails for sensitive data

### Core architectural principles

1. **obsidian-cli is the write interface.** All vault mutations go through `obsidian create`, `obsidian append`, `obsidian property:set`. Never direct file I/O for writes. This keeps Obsidian's metadata cache, link graph, and .base queries current.
2. **Scripts are deterministic validators.** Python scripts read the filesystem directly for validation, scanning, and reporting. They output JSON. The agent consumes that JSON and applies fixes via obsidian-cli.
3. **Bases replace indexes.** .base files are live queries over frontmatter. They never drift. No `rebuild-indexes.py` needed.
4. **Tags drive filterability.** Every TARS note gets a hierarchical tag (`tars/person`, `tars/task`, `tars/journal`, etc.) for reliable .base filtering and obsidian-cli search.
5. **Frontmatter is the schema.** All structured data lives in YAML frontmatter with typed Obsidian properties. Body content is narrative.
6. **Review before persist.** Any workflow that creates or mutates durable state presents a review surface to the user before writing.
7. **Every write is logged.** The daily note accumulates an activity log of everything TARS did that day.
8. **Git is the safety net.** The vault is a git repository. Every write batch is followed by a commit. Rollback is always possible.

---

## Part 3: Vault structure

```
tars-vault/
├── .claude/
│   └── skills/                          # obsidian-skills installed here
│       ├── obsidian-cli/SKILL.md
│       ├── obsidian-markdown/SKILL.md
│       ├── obsidian-bases/SKILL.md
│       ├── json-canvas/SKILL.md
│       └── defuddle/SKILL.md
├── _system/
│   ├── config.md                        # User profile, preferences, core directives
│   ├── integrations.md                  # Provider-agnostic integration registry
│   ├── alias-registry.md               # Canonical name → aliases mapping
│   ├── taxonomy.md                      # Entity types, tags, relationship types
│   ├── kpis.md                          # KPI definitions per initiative
│   ├── schedule.md                      # Recurring and one-time scheduled items
│   ├── guardrails.yaml                  # Sensitive data patterns (block/warn)
│   ├── maturity.yaml                    # Onboarding progress tracking
│   ├── housekeeping-state.yaml          # Last maintenance run state
│   ├── schemas.yaml                     # Frontmatter validation schemas
│   └── changelog/                       # Per-day operation logs
│       └── 2026-03-21.md
├── _views/
│   ├── all-people.base
│   ├── all-initiatives.base
│   ├── all-decisions.base
│   ├── all-products.base
│   ├── all-vendors.base
│   ├── all-competitors.base
│   ├── recent-journal.base
│   ├── active-tasks.base
│   ├── overdue-tasks.base
│   ├── stale-memory.base
│   ├── inbox-pending.base
│   ├── initiative-map.canvas
│   └── health-dashboard.base
├── memory/
│   ├── people/
│   ├── vendors/
│   ├── competitors/
│   ├── products/
│   ├── initiatives/
│   ├── decisions/
│   └── org-context/
├── journal/
│   └── YYYY-MM/
│       ├── YYYY-MM-DD-meeting-slug.md
│       ├── YYYY-MM-DD-daily-briefing.md
│       ├── YYYY-MM-DD-weekly-briefing.md
│       └── YYYY-MM-DD-wisdom-slug.md
├── contexts/
│   ├── products/
│   └── artifacts/
├── inbox/
│   ├── pending/
│   └── processed/
├── archive/
├── templates/
│   ├── person.md
│   ├── vendor.md
│   ├── competitor.md
│   ├── product.md
│   ├── initiative.md
│   ├── decision.md
│   ├── org-context.md
│   ├── meeting-journal.md
│   ├── daily-briefing.md
│   ├── weekly-briefing.md
│   └── wisdom-journal.md
└── scripts/
    ├── health-check.py
    ├── scan-secrets.py
    ├── archive.py
    ├── sync.py
    └── validate-schema.py
```

### Key structural decisions

- **`_system/`** replaces `reference/` and `CLAUDE.md`. The underscore prefix sorts it first and signals "system, not content."
- **`_views/`** holds .base files that replace all `_index.md` files. Zero maintenance, always accurate.
- **`templates/`** holds Obsidian templates invoked via `obsidian create ... template="person"`.
- **`scripts/`** lives inside the vault so it travels with the vault. Scripts are deterministic Python with no Obsidian dependency.
- **`inbox/`** simplified to two states: `pending/` and `processed/`. Failed items stay in `pending/` with an error property. No `processing/` or `failed/` — these intermediate states added complexity without value.
- **`archive/`** is flat. Archived notes retain their `staleness` property in frontmatter. No need for tier-named subdirectories — .base views filter by staleness.
- **No duplicate distribution trees.** The vault IS the source of truth. No `.claude-plugin/`, no `tars-cowork-plugin/`.

---

## Part 4: Data model

### Tag taxonomy

Every TARS note gets a hierarchical tag for reliable filtering:

| Tag | Used on |
|-----|---------|
| `tars/person` | People memory notes |
| `tars/vendor` | Vendor memory notes |
| `tars/competitor` | Competitor memory notes |
| `tars/product` | Product memory notes |
| `tars/initiative` | Initiative notes |
| `tars/decision` | Decision records |
| `tars/org-context` | Organizational context notes |
| `tars/journal` | All journal entries |
| `tars/meeting` | Meeting journal entries (also has `tars/journal`) |
| `tars/briefing` | Briefing entries (also has `tars/journal`) |
| `tars/wisdom` | Wisdom/learning entries (also has `tars/journal`) |
| `tars/task` | Task notes |
| `tars/analysis` | Strategic analysis outputs |
| `tars/communication` | Drafted communications |
| `tars/inbox` | Inbox items |
| `tars/archived` | Additive tag on archived items |

### Frontmatter schemas

All frontmatter uses Obsidian-native property types (text, number, checkbox, date, datetime, list).

#### Person

```yaml
---
tags:
  - tars/person
aliases:
  - Jane
  - JS
tars-summary: "VP Engineering, leads platform team"
tars-staleness: durable
tars-created: 2026-03-21
tars-modified: 2026-03-21
---
```

Body structure:
```markdown
## Role and context
VP of Engineering at Acme. Reports to [[Mike Johnson]]. Leads the [[Platform Rewrite]].

## Working style
Prefers data-driven arguments. Dislikes long meetings without agendas.

## Key relationships
- reports_to:: [[Mike Johnson]]
- works_on:: [[Platform Rewrite]]
- member_of:: [[Engineering]]

## Recent context
- Approved 2 backend hires (2026-03-21)
- Concerned about Q3 timeline (2026-03-18)
```

#### Initiative

```yaml
---
tags:
  - tars/initiative
aliases:
  - Platform Rewrite
  - PR
tars-summary: "Rewrite core data platform for scalability"
tars-status: active
tars-owner: "[[Jane Smith]]"
tars-health: green
tars-target-date: 2026-06-30
tars-created: 2026-03-21
tars-modified: 2026-03-21
---
```

#### Decision

```yaml
---
tags:
  - tars/decision
tars-summary: "Adopted REST over GraphQL for public API"
tars-status: decided
tars-date: 2026-03-15
tars-decided-by: "[[Jane Smith]]"
tars-stakeholders:
  - "[[Bob Chen]]"
  - "[[Sarah Lee]]"
tars-affects:
  - "[[Platform Rewrite]]"
tars-created: 2026-03-15
tars-modified: 2026-03-15
---
```

#### Meeting journal

```yaml
---
tags:
  - tars/journal
  - tars/meeting
tars-date: 2026-03-21
tars-participants:
  - "[[Jane Smith]]"
  - "[[Bob Chen]]"
tars-organizer: "[[Jane Smith]]"
tars-topics:
  - q1-roadmap
  - hiring
tars-initiatives:
  - "[[Platform Rewrite]]"
tars-source: calendar
tars-calendar-title: "Q1 Planning Sync"
tars-created: 2026-03-21
---
```

#### Daily briefing

```yaml
---
tags:
  - tars/journal
  - tars/briefing
tars-date: 2026-03-21
tars-briefing-type: daily
tars-created: 2026-03-21
---
```

#### Weekly briefing

```yaml
---
tags:
  - tars/journal
  - tars/briefing
tars-date: 2026-03-21
tars-briefing-type: weekly
tars-week-start: 2026-03-17
tars-week-end: 2026-03-23
tars-created: 2026-03-21
---
```

#### Task

```yaml
---
tags:
  - tars/task
tars-status: open
tars-owner: "[[Bob Chen]]"
tars-due: 2026-03-24
tars-priority: high
tars-source: "[[2026-03-21 Q1 Planning Sync]]"
tars-project: "[[Platform Rewrite]]"
tars-created: 2026-03-21
tars-modified: 2026-03-21
---
```

#### Vendor

```yaml
---
tags:
  - tars/vendor
aliases:
  - SF
tars-summary: "Cloud data warehouse provider"
tars-staleness: seasonal
tars-key-contact: "[[Sarah Lee]]"
tars-contract-renewal: 2026-06-15
tars-created: 2026-03-21
tars-modified: 2026-03-21
---
```

#### Competitor

```yaml
---
tags:
  - tars/competitor
tars-summary: "Direct competitor in enterprise analytics"
tars-staleness: seasonal
tars-created: 2026-03-21
tars-modified: 2026-03-21
---
```

#### Product

```yaml
---
tags:
  - tars/product
aliases:
  - DP
tars-summary: "Core data processing platform"
tars-status: active
tars-owner: "[[Jane Smith]]"
tars-staleness: seasonal
tars-created: 2026-03-21
tars-modified: 2026-03-21
---
```

#### Org context

```yaml
---
tags:
  - tars/org-context
tars-summary: "Engineering team structure and norms"
tars-staleness: durable
tars-created: 2026-03-21
tars-modified: 2026-03-21
---
```

#### Wisdom

```yaml
---
tags:
  - tars/journal
  - tars/wisdom
tars-date: 2026-03-21
tars-source-type: article
tars-author: "Author Name"
tars-topics:
  - ai-strategy
tars-created: 2026-03-21
---
```

### Schema validation file

`_system/schemas.yaml` defines required fields and valid values per type. Scripts validate against this.

```yaml
person:
  required_tags: [tars/person]
  required_properties:
    - tars-summary
    - tars-staleness
    - tars-created
    - tars-modified
  property_rules:
    tars-staleness:
      enum: [durable, seasonal, transient]

initiative:
  required_tags: [tars/initiative]
  required_properties:
    - tars-summary
    - tars-status
    - tars-owner
    - tars-created
    - tars-modified
  property_rules:
    tars-status:
      enum: [planning, active, paused, completed, cancelled]
    tars-health:
      enum: [green, yellow, red]

decision:
  required_tags: [tars/decision]
  required_properties:
    - tars-summary
    - tars-status
    - tars-date
    - tars-decided-by
    - tars-created
  property_rules:
    tars-status:
      enum: [proposed, decided, implemented, superseded, rejected]

meeting:
  required_tags: [tars/journal, tars/meeting]
  required_properties:
    - tars-date
    - tars-participants
    - tars-source
    - tars-created
  property_rules:
    tars-source:
      enum: [calendar, transcript, notes, manual]

task:
  required_tags: [tars/task]
  required_properties:
    - tars-status
    - tars-owner
    - tars-priority
    - tars-source
    - tars-created
  property_rules:
    tars-status:
      enum: [open, in-progress, done, cancelled]
    tars-priority:
      enum: [critical, high, medium, low]

briefing:
  required_tags: [tars/journal, tars/briefing]
  required_properties:
    - tars-date
    - tars-briefing-type
    - tars-created
  property_rules:
    tars-briefing-type:
      enum: [daily, weekly]

wisdom:
  required_tags: [tars/journal, tars/wisdom]
  required_properties:
    - tars-date
    - tars-source-type
    - tars-created
  property_rules:
    tars-source-type:
      enum: [article, podcast, book, transcript, video, conversation]

vendor:
  required_tags: [tars/vendor]
  required_properties:
    - tars-summary
    - tars-staleness
    - tars-created
    - tars-modified

competitor:
  required_tags: [tars/competitor]
  required_properties:
    - tars-summary
    - tars-staleness
    - tars-created
    - tars-modified

product:
  required_tags: [tars/product]
  required_properties:
    - tars-summary
    - tars-status
    - tars-owner
    - tars-created
    - tars-modified
  property_rules:
    tars-status:
      enum: [active, planned, deprecated]
```

### Property naming convention

All TARS-managed properties are prefixed with `tars-` to avoid collisions with user properties or other plugins. This is a deliberate namespace.

---

## Part 5: Obsidian Bases (.base files)

Bases are the single most important architectural change. They replace all `_index.md` files with live queries that never drift.

### `_views/all-people.base`

```yaml
filter:
  and:
    - property: tags
      operator: contains
      value: tars/person
    - property: tags
      operator: not contains
      value: tars/archived
formulas:
  days_since_update:
    formula: 'if(prop("tars-modified"), (now() - date(prop("tars-modified"))).days, 999)'
  needs_review:
    formula: 'if(prop("days_since_update") > 90, "Yes", "No")'
views:
  - name: All People
    type: table
    properties:
      - file.name
      - tars-summary
      - tars-staleness
      - tars-modified
    order:
      - property: file.name
        direction: asc
  - name: Stale (90+ days)
    type: table
    filters:
      - formula: needs_review
        operator: is
        value: "Yes"
    properties:
      - file.name
      - tars-summary
      - tars-modified
      - days_since_update
    order:
      - property: days_since_update
        direction: desc
```

### `_views/all-initiatives.base`

```yaml
filter:
  and:
    - property: tags
      operator: contains
      value: tars/initiative
    - property: tags
      operator: not contains
      value: tars/archived
views:
  - name: Active
    type: table
    filters:
      - property: tars-status
        operator: is
        value: active
    properties:
      - file.name
      - tars-summary
      - tars-health
      - tars-owner
      - tars-target-date
      - tars-modified
    order:
      - property: tars-target-date
        direction: asc
  - name: All
    type: table
    properties:
      - file.name
      - tars-summary
      - tars-status
      - tars-health
      - tars-owner
    group:
      - property: tars-status
```

### `_views/all-decisions.base`

```yaml
filter:
  property: tags
  operator: contains
  value: tars/decision
views:
  - name: Recent Decisions
    type: table
    properties:
      - file.name
      - tars-summary
      - tars-status
      - tars-decided-by
      - tars-date
    order:
      - property: tars-date
        direction: desc
  - name: By Status
    type: table
    properties:
      - file.name
      - tars-summary
      - tars-decided-by
      - tars-date
    group:
      - property: tars-status
```

### `_views/active-tasks.base`

```yaml
filter:
  and:
    - property: tags
      operator: contains
      value: tars/task
    - property: tars-status
      operator: is not
      value: done
    - property: tars-status
      operator: is not
      value: cancelled
    - property: tags
      operator: not contains
      value: tars/archived
formulas:
  is_overdue:
    formula: 'if(prop("tars-due"), prop("tars-due") < today(), false)'
views:
  - name: By Priority
    type: table
    properties:
      - file.name
      - tars-status
      - tars-owner
      - tars-due
      - tars-priority
      - tars-project
    order:
      - property: tars-priority
        direction: asc
      - property: tars-due
        direction: asc
  - name: By Owner
    type: table
    properties:
      - file.name
      - tars-status
      - tars-due
      - tars-priority
      - tars-project
    group:
      - property: tars-owner
  - name: Overdue
    type: table
    filters:
      - formula: is_overdue
        operator: is
        value: true
    properties:
      - file.name
      - tars-owner
      - tars-due
      - tars-priority
      - tars-project
    order:
      - property: tars-due
        direction: asc
```

### `_views/recent-journal.base`

```yaml
filter:
  property: tags
  operator: contains
  value: tars/journal
views:
  - name: Last 30 Days
    type: table
    properties:
      - file.name
      - tags
      - tars-date
      - tars-participants
      - tars-initiatives
    order:
      - property: tars-date
        direction: desc
    limit: 50
  - name: By Type
    type: table
    properties:
      - file.name
      - tars-date
      - tars-participants
    group:
      - property: tags
```

### `_views/stale-memory.base`

```yaml
filter:
  and:
    - property: tags
      operator: is one of
      value: [tars/person, tars/vendor, tars/competitor, tars/product, tars/initiative, tars/org-context]
    - property: tars-staleness
      operator: is not
      value: durable
    - property: tags
      operator: not contains
      value: tars/archived
formulas:
  days_since_update:
    formula: 'if(prop("tars-modified"), (now() - date(prop("tars-modified"))).days, 999)'
  threshold:
    formula: 'if(prop("tars-staleness") == "seasonal", 180, if(prop("tars-staleness") == "transient", 90, 30))'
  overdue:
    formula: 'prop("days_since_update") > prop("threshold")'
views:
  - name: Archive Candidates
    type: table
    filters:
      - formula: overdue
        operator: is
        value: true
    properties:
      - file.name
      - tars-staleness
      - tars-modified
      - days_since_update
    order:
      - property: days_since_update
        direction: desc
```

### Why bases are better than indexes

1. **Zero maintenance.** Bases are live queries. They never drift from reality.
2. **Multiple views.** One .base file can show "Active," "Completed," "Stale," and "By Status" from the same data.
3. **Embeddable.** Any note can include `![[all-people.base#Stale (90+ days)]]` for an inline live view.
4. **Formulaic.** Computed fields like `days_since_update` and `is_overdue` enable smart filtering without scripting.
5. **Agent-readable.** `obsidian read file="all-people"` returns the base definition; the agent can also search the underlying notes directly.

### Important caveat

.base files render in Obsidian's UI but cannot be programmatically queried by obsidian-cli. The agent uses `obsidian search` with tag and property filters for programmatic access. Bases serve the human; search serves the agent.

---

## Part 6: Name resolution system

### How it works

Name normalization uses three layers:

**Layer 1: Obsidian aliases (primary).** Every entity note has an `aliases` property:
```yaml
aliases:
  - Jane
  - JS
  - J. Smith
```
When the agent writes `[[Jane]]`, Obsidian resolves it to `[[Jane Smith]]` automatically.

**Layer 2: Alias registry (disambiguation).** `_system/alias-registry.md` handles context-dependent ambiguity:

```markdown
# Alias Registry

## Ambiguous names

| Short name | Default resolution | Context override |
|-----------|-------------------|-----------------|
| Dan | [[Dan Rivera]] | infrastructure → [[Dan Chen]] |
| Sarah | [[Sarah Kim]] | — (unambiguous) |
| Mike | [[Mike Johnson]] | product → [[Mike Torres]] |

## Team abbreviations

| Abbreviation | Canonical |
|-------------|-----------|
| eng | Engineering |
| PM | Product Management |
| DS | Data Science |

## Product abbreviations

| Abbreviation | Canonical |
|-------------|-----------|
| DP | [[Data Platform]] |
| API | [[API Gateway]] |
```

**Layer 3: Search fallback.** If layers 1-2 don't resolve:
```
obsidian search query="Jane" limit=5
```
Present matches to the user. Never guess.

### Agent resolution protocol

Before processing any content (meeting transcript, inbox item, user input):

1. Read `_system/alias-registry.md`
2. For each name in the content:
   a. Check alias registry for direct match
   b. If ambiguous, use context (meeting topic, initiative) to disambiguate
   c. If still ambiguous, ask the user with a bounded menu
   d. If unknown, offer to: (i) add as alias to existing entity, (ii) create new entity, (iii) mark as `[[Name (unverified)]]`
3. After processing, scan output for any unresolved names
4. Auto-add new confirmed names to alias registry

### Why this is better than v1

v1's `replacements.md` was a flat lookup table. It could not handle:
- Context-dependent disambiguation ("Dan" in infrastructure vs. product)
- Obsidian's native alias resolution (which handles most cases automatically)
- Graceful degradation (search fallback)

---

## Part 7: Workflow specifications

### 7.1 Meeting processing (highest priority)

**Purpose:** Convert meeting transcript/notes into structured journal entry, tasks, and memory updates.

**Trigger:** User says "process this meeting" or provides transcript text.

**Pipeline:**

```
Step 1: Load alias registry
  obsidian read file="alias-registry"

Step 2: Calendar enrichment (if available)
  Call calendar MCP: list_events for inferred date
  Extract: attendees, organizer, title, time

Step 3: Resolve participants
  For each attendee/speaker:
    Check alias registry → obsidian search → ask user if ambiguous
  Present resolved participant list for user confirmation:
    "Participants: [[Jane Smith]], [[Bob Chen]], [[Unknown: Mick]]. Confirm?"

Step 4: Agent processes transcript (LLM reasoning)
  Produce structured output:
    - Topics discussed
    - Updates (from others, not the user)
    - Concerns (WHO / ISSUE / DEADLINE)
    - Decisions (what + who decided)
    - Action items (owner / task / deadline)
    - Unresolved items

Step 5: Create journal entry
  obsidian create name="YYYY-MM-DD Meeting Title" \
    path="journal/YYYY-MM/YYYY-MM-DD-meeting-slug.md" \
    template="meeting-journal" silent
  obsidian property:set [all frontmatter properties]
  obsidian append file="..." content="[structured body]"

Step 6: Extract tasks (accountability test)
  For each action item:
    a. Is it concrete? (not "think about", "consider")
    b. Is there a clear owner?
    c. Is it verifiable?
  If passes AND not duplicate (search existing tasks):
    obsidian create name="Task title" path="memory/tasks/..." template="task" silent
    [set all task properties]
  Present extracted tasks for user review before creation.

Step 7: Extract memory (durability test)
  For each insight:
    a. Lookup value? (useful next week/month?)
    b. High-signal? (broadly applicable?)
    c. Durable? (not transient?)
    d. Behavior change? (changes future interactions?)
  If passes AND is new/updated info:
    Present proposed memory updates for user review:
    "Proposed updates:
     1. [[Jane Smith]]: Approved 2 backend hires for [[Platform Rewrite]]
     2. New decision: REST over GraphQL
     Save? [Yes / Edit / Skip #N]"
  Only persist after user confirms.
    obsidian append file="Jane Smith" content="..."
    obsidian property:set name="tars-modified" value="YYYY-MM-DD" file="Jane Smith"

Step 8: Scan for unresolved names
  Check all wikilinks in output. For any unresolved:
    Add to alias registry with "?? (needs full name)" marker
    Flag in output summary

Step 9: Log to daily note
  obsidian daily:append content="## Meeting processed: [[YYYY-MM-DD Meeting Title]]
  - Tasks extracted: N
  - Memory updates: N
  - Unresolved names: N"

Step 10: Secret scan
  Run scan-secrets.py against the journal entry content BEFORE step 5.
  If blocked patterns found: redact and notify user.
  If warn patterns found: flag for user review.
```

**Resumability:** Steps 5-9 each produce durable artifacts. If the agent fails at step 7, the journal entry (step 5) and tasks (step 6) already exist. User says "continue processing" and the agent reads the saved journal to resume.

### 7.2 Daily briefing

**Purpose:** Morning orientation snapshot.

**Trigger:** User says "daily briefing" or "what's my day."

**Pipeline:**

```
Step 1: Determine date
  If after 5 PM, brief for tomorrow.

Step 2: Gather data (parallel where possible)
  a. Calendar: list_events for target date
  b. Tasks: obsidian search query="tag:tars/task tars-status:open" limit=50
     Filter for: due today, overdue, high priority
  c. People context: For each attendee in today's meetings:
     obsidian read file="[person name]"
  d. Schedule: obsidian read file="schedule"
  e. Housekeeping state: read _system/housekeeping-state.yaml
  f. Inbox count: obsidian search query="path:inbox/pending" limit=1

Step 3: Cross-reference
  Match attendees to memory entities.
  Link tasks to meetings (same initiative, same people).
  Check for unrecognized attendees.

Step 4: Generate briefing sections
  - Today's schedule (with people context per meeting)
  - Priority tasks (due today + overdue)
  - Initiative pulse (health of active initiatives)
  - Focus opportunities (gaps in calendar)
  - Unrecognized people (attendees not in memory)
  - System status (last maintenance, inbox count, maturity level)

Step 5: Save
  obsidian create name="YYYY-MM-DD Daily Briefing" \
    path="journal/YYYY-MM/YYYY-MM-DD-daily-briefing.md" \
    template="daily-briefing" silent
  [set properties, append content]

Step 6: Data freshness footer
  Include: "Data sources: N meetings, N tasks, N memory files referenced.
  Stale: [any memory files >60 days old for today's attendees]"
```

### 7.3 Weekly briefing

**Purpose:** Week-level planning and review.

**Pipeline:** Same structure as daily but:
- Calendar: 7-day window
- Tasks: all active lists
- Journal: review entries from past week
- Additional sections: Last week summary, milestones hit/missed, responses owed, backlog review (items >90 days flagged stale), recommended focus areas

### 7.4 Task extraction

**Purpose:** Extract tasks from any freeform input.

**Pipeline:**

```
Step 1: Load alias registry

Step 2: Scan for commitment patterns
  "I will...", "Can you...", "Let's...", "Action item:", "Need to...",
  "By [date]", "[Name] should...", "Follow up on..."

Step 3: Apply accountability test per item
  a. Concrete? (specific deliverable, not "think about")
  b. Owned? (clear single owner)
  c. Verifiable? (will we know when it's done?)
  Discard items that fail. Report why.

Step 4: Resolve metadata
  Owner: normalize name
  Due date: resolve relative dates to YYYY-MM-DD
    today → current date
    tomorrow → +1 day
    this week → Thursday
    next week → next Monday
    this month → 3rd Monday
    end of month → last day
    later/unknown → no date
  Source: link to originating note
  Project: link to initiative if identifiable

Step 5: Check duplicates
  obsidian search query="tag:tars/task [task title keywords]" limit=5
  If >80% title similarity with same owner: present as potential duplicate

Step 6: Present for review
  "3 tasks extracted:
   1. Review hiring plan (you, 2026-03-25, high) [Active]
   2. Share migration report (Bob Chen, 2026-03-24, medium) [Delegated]
   3. Schedule interviews (no date) [Backlog]
   Create? [Yes / Edit / Skip #N]"

Step 7: Create tasks (after user confirms)
  obsidian create name="[task title]" path="..." silent
  [set all task properties]

Step 8: Log to daily note
```

### 7.5 Memory save (learn)

**Purpose:** Save durable facts from conversation.

**Pipeline:**

```
Step 1: Load alias registry

Step 2: Analyze input for delta
  What is new? What contradicts existing memory? What deepens existing understanding?
  If no delta: STOP. "Nothing new to save."

Step 3: Check existing memory
  obsidian search query="tag:tars/[entity-type] [entity name]" limit=5
  obsidian read file="[entity name]"
  If fact already captured: STOP. "Already in memory."

Step 4: Apply durability test (all four criteria)

Step 5: Classify and route
  Person fact → memory/people/
  Initiative fact → memory/initiatives/
  Decision → memory/decisions/
  Org context → memory/org-context/

Step 6: Present for review
  "Proposed memory update:
   [[Jane Smith]]: Prefers email over Slack for status updates.
   Save? [Yes / Edit / Skip]"

Step 7: Write (after confirmation)
  Update existing: obsidian append + property:set tars-modified
  Create new: obsidian create with template + all properties

Step 8: Update alias registry if new entity
  Add aliases to _system/alias-registry.md

Step 9: Log to daily note
```

### 7.6 Inbox processing

**Purpose:** Batch process mixed raw inputs.

**Pipeline:**

```
Step 1: Scan inbox
  obsidian search query="path:inbox/pending" limit=50
  If zero: "Inbox empty." Exit.

Step 2: Present inventory
  For each item, read first ~50 lines and classify:
  - transcript/meeting notes → route to meeting processing
  - article/link → route to wisdom extraction
  - task-like items → route to task extraction
  - facts to remember → route to memory save
  - mixed → split into components

  Present classification to user:
  "4 items in inbox:
   1. ClientCo sync notes (meeting)
   2. API patterns article (wisdom)
   3. Team offsite idea (memory)
   4. Phone task dump (tasks)
   Process all? [Yes / Pick specific / Reclassify]"

Step 3: Process each item
  Route to appropriate workflow.
  Each workflow handles its own review gates.

Step 4: Mark processed
  obsidian property:set name="tars-inbox-processed" value="true" file="..."
  obsidian property:set name="tars-inbox-processed-date" value="YYYY-MM-DD" file="..."

  IMPORTANT: Never delete the original. Mark it processed. Maintenance archives later.

Step 5: Summary
  "Inbox complete: 4 items → 1 meeting, 1 wisdom, 1 memory, 3 tasks"

Step 6: Log to daily note
```

### 7.7 Strategic analysis (Think modes)

**Mode A: Strategic Analysis**

```
1. Select framework (Working Backwards, First Principles, Pre-Mortem, etc.)
   State: "Approaching via [Framework] because [Reason]"
2. Layer 1 (Hypothesis): State the obvious answer
3. Layer 2 (Tree of Thoughts): Three parallel branches:
   - Support: evidence for hypothesis
   - Challenge: what breaks it
   - Lateral: completely different approach
4. Layer 3 (Constraints): Stress-test across:
   - Regulatory/Compliance
   - Technical/Feasibility
   - Team Capacity/Timeline
   - Political/Organizational
   - Budget/ROI
5. Layer 4 (Synthesis): Hardened recommendation with confidence (High/Medium/Low),
   key assumptions, failure conditions
6. Save to journal/YYYY-MM/YYYY-MM-DD-analysis-slug.md
```

**Mode B: Validation Council**

```
1. Vulnerability scan: weakest assumption, missing data, "hope disguised as fact"
2. Persona assault:
   - CFO: ROI, burn rate, unit economics
   - CTO: debt, scale, maintenance
   - Competitor: differentiation, moats, copycat risk
   - Customer: usability, value prop, jobs-to-be-done
3. Logic audit: steel-man the idea, then destroy the steel-man
4. Verdict: kill criteria, major risks, missing data
```

**Mode C: Executive Council**

```
CPO (Strategic Pragmatist): "How do we sell this to the Board?"
CTO (Technical Realist): "Hope is not a strategy."
1. Silent context loading from vault
2. Debate where personas MUST disagree where incentives conflict
3. Synthesis with verdict, risk mitigation, next steps
```

**Mode D: Deep Analysis Chain**

```
1. Run Mode A (sequential). Save to journal.
2. Run Mode B (parallel sub-agent A) against saved analysis.
3. Run Mode C (parallel sub-agent B) against saved analysis.
4. Synthesize all three into hardened recommendation.
5. Save final synthesis to journal.
```

**Mode E: Discovery**

```
HARD RULE: "YOU DO NOT HAVE PERMISSION TO SOLVE."
1. Mirroring: restate user intent
2. Context mapping: connect to known entities
3. The unknowns: what's missing
4. Probing questions: 3-5 targeted questions
Exit: user answers questions or says "Proceed"
```

### 7.8 Health check

**Purpose:** Scan vault for structural issues.

**Pipeline:**

```
Step 1: Run validate-schema.py
  Checks all notes with tars/ tags against _system/schemas.yaml
  Reports: missing required properties, invalid enum values, type mismatches

Step 2: Run scan-secrets.py
  Scans all memory/ and journal/ content
  Reports: blocked patterns found, warned patterns found

Step 3: Check broken wikilinks
  obsidian search query="tag:tars" limit=200
  For each note, check that wikilinks in frontmatter resolve:
  obsidian read file="[linked entity]"
  Flag any that return "not found"

Step 4: Check alias consistency
  Read alias registry. For each entry:
  obsidian read file="[target]"
  Verify target exists and aliases match

Step 5: Check duplicate aliases
  Build alias → target map. Flag any alias mapping to multiple targets.

Step 6: Check stale content
  Read _views/stale-memory.base conceptually:
  obsidian search query="tag:tars/person" (etc.) and check tars-modified dates

Step 7: Present report with severity
  Critical: broken links, schema violations, duplicates
  Warning: stale content, missing optional properties
  Info: orphaned notes, tag typos

Step 8: Offer to fix
  "7 issues found (2 critical). Auto-fix all / Fix critical only / Review each?"

Step 9: Log to daily note
```

### 7.9 Maintenance/Housekeeping

**Purpose:** Ambient maintenance to prevent entropy.

**Trigger:** Automatic (when housekeeping-state shows last_run != today) or manual.

**Pipeline:**

```
Step 1: Read _system/housekeeping-state.yaml
  If last_run == today and not manual trigger: skip

Step 2: Run archive.py (deterministic script)
  Check staleness tiers. Move qualifying notes to archive/.
  GUARDRAIL: Never archive notes with incoming backlinks from last 90 days.
  GUARDRAIL: Never archive notes referenced by active tasks.
  Present archive candidates for user approval.

Step 3: Run health check (step 7.8 above)

Step 4: Run sync check
  Calendar gap analysis: meetings from last 7 days without journal entries
  Task system sync: if external task system configured, check for state drift
  Memory staleness: people seen in recent meetings but not updated recently

Step 5: Archive processed inbox items older than 7 days
  obsidian property:set name="tags" to add tars/archived

Step 6: Update housekeeping-state.yaml
  last_run: today
  last_success: true/false
  run_count: +1

Step 7: Log to daily note
  Brief summary of what maintenance found and did
```

### 7.10 Onboarding/Welcome

**Purpose:** First-run setup.

**Pipeline:**

```
Step 1: Check if vault is already set up
  obsidian search query="path:_system/config" limit=1
  If found: "TARS is already set up. Run health check instead?"

Step 2: Create vault structure
  For each folder in the structure:
    obsidian create for a placeholder if needed
  Copy templates, scripts, system files

Step 3: Configure integrations
  "Do you use a calendar? [Apple Calendar / Google Calendar / Outlook / None]"
  "Do you use a task manager? [Apple Reminders / Todoist / Linear / None]"
  Write to _system/integrations.md

Step 4: Initial context gathering
  "What's your role?" → save to _system/config.md
  "What team are you on?" → create org-context note
  "Who are the 3-5 people you work with most?" → create people notes
  "What are your main projects right now?" → create initiative notes

Step 5: Initialize maturity.yaml at level 1

Step 6: Initialize housekeeping-state.yaml

Step 7: Create initial .base files in _views/

Step 8: Initialize git repository
  git init, initial commit

Step 9: Welcome summary
  "TARS is ready. Your vault has:
   - N people, N initiatives
   - Calendar: configured / not configured
   - Tasks: configured / not configured
   Try: 'daily briefing' or 'process this meeting'"
```

### 7.11 Fast lookup (Answer)

**Purpose:** Quick retrieval of facts, schedule, context.

**Source priority:**
1. Memory files (highest confidence)
2. Task notes
3. Journal entries
4. Integration sources (calendar, project tracker)
5. Web (lowest confidence, flag explicitly)

**Pipeline:**

```
Step 1: Classify the question
  Schedule/calendar → query calendar MCP
  Task status → obsidian search tag:tars/task
  Person context → obsidian read file="[person]"
  Initiative status → obsidian read file="[initiative]"
  Decision context → obsidian search tag:tars/decision + keyword
  General → obsidian search with keywords

Step 2: Retrieve and synthesize
  Read the most relevant sources.
  Cite sources with wikilinks.

Step 3: Flag confidence
  "Based on [[Jane Smith]] memory file (updated 2026-03-15): ..."
  "Based on web search (medium-low confidence): ..."
```

### 7.12 Communication drafting

**Purpose:** Audience-aware drafting.

**Pipeline:**

```
Step 1: Identify audience
  Load stakeholder memory files for each recipient

Step 2: Determine communication type
  Email, Slack, presentation, status update

Step 3: Draft with stakeholder awareness
  Adjust tone, detail level, framing based on:
  - Recipient's role and seniority
  - Relationship history
  - Known preferences
  - RASCI role (Responsible/Accountable/Support/Consulted/Informed)

Step 4: Empathy audit
  Check: Does this land well? Is the ask clear? Is the tone right for this person?

Step 5: Present draft for user review and iteration

Step 6: Optionally save to journal
```

---

## Part 8: Integration architecture

### Provider-agnostic model

Skills reference categories, not vendors:

| Category | Operations | Example MCP servers |
|----------|-----------|-------------------|
| Calendar | list_events, create_event, get_event | apple-calendar-mcp, google-calendar-mcp |
| Tasks | list, create, complete, edit, overdue | apple-reminders-mcp, todoist-mcp |
| Project tracker | list_issues, get_issue, create_issue | jira-mcp, linear-mcp |
| Documentation | search_pages, get_page | confluence-mcp, notion-mcp |
| Web content | extract_markdown | defuddle CLI |

### Discovery flow

```
1. Check <mcp_servers> for a server matching the category
2. If found → use MCP tools directly
3. If not found → read _system/integrations.md for legacy config
4. If legacy configured → execute legacy commands
5. If neither → note gap and proceed without
```

### Adding a new provider

1. Configure its MCP server
2. Update `_system/integrations.md` with the category mapping
3. No skill changes needed — the adapter pattern handles it

---

## Part 9: Trust and safety

### Durability test (memory gate)

ALL four must pass before any memory write:

| # | Criterion | Question |
|---|-----------|----------|
| 1 | Lookup value | Will this be useful for lookup next week or next month? |
| 2 | Signal | Is this high-signal and broadly applicable? |
| 3 | Durability | Is this durable (not transient or tactical)? |
| 4 | Behavior change | Does this change how I should interact in the future? |

**Pass:** "Daniel prefers data in tables" (behavior change), "Vendor contract renews June" (lookup), "Decided to delay Phase 2" (durable signal).

**Fail:** "Meeting with John tomorrow" (transient), "Discussed MCP timeline" (vague), "Emailed Daniel" (event log).

### Accountability test (task gate)

ALL three must pass:

| # | Criterion | Question |
|---|-----------|----------|
| 1 | Concrete | Is it a specific deliverable? |
| 2 | Owned | Is there a clear single owner? |
| 3 | Verifiable | Will we know objectively when it's done? |

### Sensitive data scanning

`scripts/scan-secrets.py` runs against content BEFORE any write.

**Block patterns** (redact, never persist):
- SSN: `\b\d{3}-\d{2}-\d{4}\b`
- API keys: `(?i)(api[_-]?key|apikey)\s*[:=]\s*\S+`
- Passwords: `(?i)(password|passwd|pwd)\s*[:=]\s*\S+`
- Bearer tokens: `(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*`
- JWTs: `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`
- Private keys: `-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----`
- Connection strings: `(?i)(mongodb|postgres|mysql|redis)://\S+:\S+@`

**Warn patterns** (flag for user review):
- Date of birth: `(?i)(date\s*of\s*birth|dob|born\s*on)\s*[:=]?\s*\d`
- Sensitive keywords: salary, compensation, PIP, termination, diagnosis, lawsuit

**Allowed** (never flagged): names, company names, deal values, contract dates, meeting content.

### Review gates

| Gate | When | What user sees |
|------|------|---------------|
| Memory update | Before any write to memory/ | Proposed fact + destination entity |
| Task creation | After extraction, before write | Task list with owner/date/priority |
| Participant resolution | Start of meeting processing | Resolved name list with vault links |
| Sensitive content | Warn pattern detected | Content snippet with options |
| Archive candidates | During maintenance | List of notes proposed for archival |
| Name disambiguation | Ambiguous alias found | Bounded menu of possible matches |

### Circuit breakers

| Condition | Action |
|-----------|--------|
| >20 files modified in single workflow | Pause, ask user to confirm |
| >5 tasks from single meeting | Present for review before creating |
| Memory file would exceed 200 lines | Suggest archival/summarization first |
| >3 consecutive obsidian-cli errors | Stop all operations, report status |
| Name resolution confidence <70% | Do not proceed, ask user |

### Activity logging

Every workflow appends to the daily note:

```markdown
## TARS Activity - 14:32
- Processed: [[2026-03-21 Q1 Planning Sync]]
- Journal: [[journal/2026-03/2026-03-21-meeting-q1-planning]]
- Memory: updated [[Jane Smith]] (added: backend hires approved)
- Tasks: 3 created (see above)
- Unresolved: 1 name (Mick → added to alias registry with ??)
```

### Changelog

`_system/changelog/YYYY-MM-DD.md` records every write operation:

```markdown
# Changelog 2026-03-21

## 14:32 - Meeting processing
- batch_id: mtg-20260321-143200
- created: journal/2026-03/2026-03-21-meeting-q1-planning.md
- updated: memory/people/jane-smith.md (appended: backend hires)
- created: [3 task files]
- updated: _system/alias-registry.md (added: Mick → ??)
```

This enables rollback. With git: `git revert <batch-commit>`. Without git: read changelog and manually revert.

---

## Part 10: Failure modes and mitigations

### Transcript too large for context window

**Risk:** 90-minute meeting with 15 participants can exceed context limits. The second half is silently truncated.

**Mitigation:**
- Chunk transcripts into 15-minute segments
- Process each chunk sequentially, accumulating results
- Final synthesis step merges chunk outputs
- Explicit "coverage" metric: "Processed 100% of transcript (4 chunks)"

### Person misidentification

**Risk:** "Dan mentioned Q3 timeline" — wrong Dan gets the attribution.

**Mitigation:**
- Participant confirmation at start of processing (mandatory review gate)
- For multi-Dan situations, the agent MUST ask before proceeding
- If a name appears that is not in the confirmed participant list, flag it

### Partial writes from mid-batch failure

**Risk:** Journal entry exists but memory updates are incomplete.

**Mitigation:**
- Each write is atomic (one obsidian-cli call per file)
- Changelog records every write with batch_id
- If failure detected: report what was written, what was not, and offer to resume
- Git commit after each successful batch for rollback

### Schema drift

**Risk:** Types proliferate (meeting, 1:1, planning-meeting, team-sync...).

**Mitigation:**
- `_system/schemas.yaml` defines strict enums
- `validate-schema.py` runs on every health check
- The agent validates frontmatter against the schema BEFORE writing — hard gate, not warning
- Any new type must be added to schemas.yaml first

### Sync service conflicts

**Risk:** iCloud/Obsidian Sync/git conflicts during writes.

**Mitigation:**
- obsidian-cli writes through Obsidian's API, which handles its own sync coordination
- Warn users about iCloud being unreliable for rapid file changes
- Recommend Obsidian Sync or git (not iCloud) for vault sync
- Post-write verification: re-read file to confirm content persisted

### Memory file grows unbounded

**Risk:** Frequently-mentioned person's file reaches 500+ lines.

**Mitigation:**
- Circuit breaker at 200 lines: suggest summarization before appending
- Maintenance flags files approaching the limit
- Offer to archive older context sections to a "history" note

### Maintenance archives active content

**Risk:** Wikilinks break because a note was archived.

**Mitigation:**
- NEVER archive notes with incoming backlinks from the last 90 days
- NEVER archive notes referenced by active tasks
- ALWAYS present archive candidates for user approval
- Leave redirect stub or broken-link note when archiving

### obsidian-cli not available

**Risk:** Fatal for all workflows.

**Mitigation:**
- First action in every workflow: health check `obsidian version`
- If fails: clear error message with installation instructions, full stop
- No partial execution when the interface is down

---

## Part 11: Testing strategy

### Vault fixture tests

Create `tests/fixtures/` with a known-good test vault. Test:

- Schema validation accepts valid notes, rejects invalid ones
- Name resolution resolves unambiguous names, flags ambiguous ones
- Wikilink validation detects broken links
- Duplicate detection catches near-identical tasks
- Sensitive keyword detection fires on known patterns
- Secret scanning blocks known patterns, passes clean content

### Integration tests (require obsidian-cli)

- `create` + `read` round-trip: content matches
- `property:set` modifies frontmatter without corrupting body
- `search` returns expected results for known content
- `append` does not overwrite existing content
- Error handling: graceful failure when target note doesn't exist

### Schema validation tests

- Every type in `schemas.yaml` has valid and invalid fixture examples
- Full vault scan reports all violations
- Regression: after each modification, re-validate

### Smoke tests (every run)

```
1. obsidian version → succeeds
2. obsidian search query="tag:tars" → returns results
3. _system/schemas.yaml → exists and parses
4. _system/alias-registry.md → exists and parses
5. Daily note → accessible
```

### Critical path tests (pre-release)

1. End-to-end meeting processing: transcript in → journal + memory + tasks out, all valid, all cross-referenced
2. Briefing generation: references real vault content, includes data freshness
3. Inbox processing: item classified, routed, processed, marked complete
4. Memory update with review gate: proposed updates appear, only persist after approval
5. Failure recovery: simulate obsidian-cli failure mid-batch, verify partial state identifiable
6. Schema validation: invalid frontmatter rejected before write

---

## Part 12: Build phases

### Phase 1: Foundation (must-have)

Build order matters. Each item builds on the previous.

1. **Vault scaffolding** — Create the folder structure, templates, system files, schemas, .base files
2. **Schema validation script** — `validate-schema.py` that checks notes against `schemas.yaml`
3. **Secret scanning script** — Port `scan-secrets.py` with guardrails.yaml patterns
4. **Alias registry and name resolution** — `_system/alias-registry.md` + resolution protocol
5. **Onboarding wizard** — Interactive setup that creates config, integrations, initial entities
6. **Memory save (learn)** — Durability test + write + review gate + daily note logging
7. **Task extraction** — Accountability test + duplicate check + review gate + creation
8. **Meeting processing** — Full pipeline: transcript → journal → tasks → memory
9. **Daily briefing** — Calendar + tasks + people + schedule + system status
10. **Health check** — Schema validation + broken links + alias consistency + stale content
11. **Activity logging** — Daily note append + changelog

### Phase 2: High-value expansion

12. **Weekly briefing** — Week review + planning + initiative health
13. **Inbox processing** — Classification + routing + batch processing
14. **Fast lookup (Answer)** — Source-priority retrieval
15. **Strategic analysis (Think Mode A)** — Framework selection + tree of thoughts + synthesis
16. **Validation council (Think Mode B)** — Persona assault + logic audit
17. **Communication drafting** — Stakeholder-aware + empathy audit
18. **Maintenance/Housekeeping** — Archive + health + sync + ambient scheduling
19. **Sync** — Calendar gap analysis + task system sync + staleness detection

### Phase 3: Advanced capabilities

20. **Executive council (Think Mode C)** — CPO/CTO debate simulation
21. **Deep analysis chain (Think Mode D)** — Chained modes with intermediate artifacts
22. **Discovery mode (Think Mode E)** — Context mapping + refusal to solve
23. **Initiative planning** — Milestones + risks + RASCI + effort estimation
24. **Initiative status** — Health assessment + progress tracking + recommended actions
25. **Wisdom extraction** — Article/podcast distillation + memory/task side effects
26. **Text refinement** — Lightweight editing command
27. **Canvas generation** — Initiative maps, org charts from memory graph
28. **Migration engine** — Template and schema version upgrades

---

## Part 13: File-by-file build manifest

This is the exact list of files the agent must create, in order.

### Phase 1 files

```
# Vault structure (folders created via obsidian create with placeholder notes)
_system/config.md
_system/integrations.md
_system/alias-registry.md
_system/taxonomy.md
_system/schedule.md
_system/guardrails.yaml
_system/maturity.yaml
_system/housekeeping-state.yaml
_system/schemas.yaml

# Templates
templates/person.md
templates/vendor.md
templates/competitor.md
templates/product.md
templates/initiative.md
templates/decision.md
templates/org-context.md
templates/meeting-journal.md
templates/daily-briefing.md
templates/weekly-briefing.md
templates/wisdom-journal.md

# Base views
_views/all-people.base
_views/all-initiatives.base
_views/all-decisions.base
_views/all-products.base
_views/all-vendors.base
_views/all-competitors.base
_views/recent-journal.base
_views/active-tasks.base
_views/overdue-tasks.base
_views/stale-memory.base
_views/inbox-pending.base
_views/health-dashboard.base

# Scripts
scripts/validate-schema.py
scripts/scan-secrets.py
scripts/health-check.py

# Skills (SKILL.md files defining agent behavior)
skills/core/SKILL.md          # Core operating rules, routing, protocols
skills/welcome/SKILL.md       # Onboarding wizard
skills/learn/SKILL.md         # Memory save + wisdom extraction
skills/tasks/SKILL.md         # Task extraction + management
skills/meeting/SKILL.md       # Meeting processing pipeline
skills/briefing/SKILL.md      # Daily + weekly briefings
skills/answer/SKILL.md        # Fast lookup
skills/maintain/SKILL.md      # Health + sync + housekeeping

# CLAUDE.md (vault-level agent configuration)
CLAUDE.md
```

### Phase 2 files

```
skills/think/SKILL.md          # Strategic analysis modes A-E
skills/think/manifesto.md      # Executive council persona definitions
skills/communicate/SKILL.md    # Communication drafting
skills/communicate/text-refinement.md

scripts/archive.py
scripts/sync.py
```

### Phase 3 files

```
skills/initiative/SKILL.md     # Initiative planning + status
skills/create/SKILL.md         # Artifact creation

_views/initiative-map.canvas   # Generated from memory graph
```

---

## Part 14: Critical implementation notes

### obsidian-cli command patterns the agent will use constantly

```bash
# Read a note (wikilink resolution, respects aliases)
obsidian read file="Jane Smith"

# Create a note with template
obsidian create name="2026-03-21 Meeting Title" \
  path="journal/2026-03/2026-03-21-meeting-slug.md" \
  template="meeting-journal" silent

# Set a frontmatter property
obsidian property:set name="tars-status" value="active" file="Platform Rewrite"

# Append content to a note
obsidian append file="Jane Smith" content="## Update 2026-03-21\nApproved 2 hires."

# Search by tag and property
obsidian search query="tag:tars/task tars-status:open" limit=50

# Get backlinks (who links to this note)
obsidian backlinks file="Platform Rewrite"

# Daily note operations
obsidian daily:read
obsidian daily:append content="## TARS Activity - 14:32\n- Processed meeting..."

# List tags with counts
obsidian tags sort=count counts

# Set multiple properties on a new note
obsidian property:set name="tags" value="tars/person" file="Bob Chen"
obsidian property:set name="aliases" value="Bob, BC" file="Bob Chen"
obsidian property:set name="tars-summary" value="Senior PM" file="Bob Chen"
```

### What the CLAUDE.md should contain

The vault-level `CLAUDE.md` should:
1. Load the core skill on every session
2. Declare the vault path for scripts
3. Set the routing table for intent → skill mapping
4. Declare which MCP servers are available
5. Set core behavioral rules (BLUF, anti-sycophancy, clarification rules)

### Property naming: why `tars-` prefix

All TARS-managed frontmatter properties use the `tars-` prefix to:
- Avoid collisions with user properties
- Avoid collisions with Obsidian properties (`tags`, `aliases`, `cssclasses`)
- Make it obvious which properties are system-managed
- Enable bulk operations (find all tars- properties)

Exception: `tags` and `aliases` use Obsidian's native property names because they power native features (graph view, link suggestions, search).

### Write ordering for cross-referenced content

When a workflow creates multiple notes that reference each other:

1. Create entity notes first (people, initiatives) — these are link targets
2. Create/update memory notes — reference entities
3. Create the journal entry — references entities and memory
4. Create task notes — reference journal and entities
5. Append to daily note — references everything above

This ensures wikilinks always point to notes that already exist.

### Date resolution table

| User says | Resolves to |
|-----------|-------------|
| today | Current date |
| tomorrow | +1 day |
| this week | Thursday of current week |
| next week | Next Monday |
| this month | 3rd Monday of current month |
| end of month | Last day of current month |
| next month | 1st of next month |
| later / unknown | No date (backlog) |

Never use relative dates in output. Always resolve to YYYY-MM-DD.

---

## Part 15: What I chose NOT to carry forward from v1

These are deliberate design decisions, not oversights:

1. **No `_index.md` files anywhere.** Bases replace them entirely. The `rebuild-indexes.py` script is eliminated.

2. **No `.lock` file convention.** obsidian-cli serializes writes through Obsidian's process. No explicit locking needed.

3. **No duplicate distribution trees.** No `.claude-plugin/`, no `tars-cowork-plugin/`. The vault is the single source of truth.

4. **No `inbox/processing/` or `inbox/failed/` directories.** Two states are enough: pending and processed. Failed items stay in pending with an error property.

5. **No `archive/durable/`, `archive/seasonal/`, etc.** Archived notes retain their staleness property in frontmatter. One flat `archive/` folder. Bases filter by staleness if needed.

6. **No maturity "levels" as a gamification mechanic.** Keep maturity tracking for onboarding progress, but don't make it feel like a video game. Users care about whether the system is useful, not about reaching "Level 4."

7. **No session-start housekeeping that blocks the user.** Maintenance runs in the background or on schedule, not as a gatekeeper before the user can ask a question.

8. **No `reference/workflows.md` or `reference/shortcuts.md` as separate files.** These are documentation artifacts from v1 that add maintenance burden without proportional value. Workflow definitions live in SKILL.md files. Help is available via the agent.

9. **Simplified journal type taxonomy.** v1 allowed meeting, briefing-daily, briefing-weekly, wisdom, performance, journal, 1:1, planning-meeting, strategic-review, team-meeting. This proliferation caused real schema drift. v2 uses: meeting, briefing (with sub-type), wisdom. That's it. A 1:1 is a meeting. A strategic review is a meeting. The distinction is in the content, not the type enum.

10. **No `antigravity-wrapper/` or compatibility layers.** Clean break.

---

## Part 16: Success criteria

The rebuild succeeds when:

1. A user can process a meeting transcript and get a journal entry, tasks, and memory updates in under 3 minutes — with review gates.
2. A daily briefing correctly references today's calendar, relevant people context, and due tasks.
3. The vault can grow to 500+ entities without performance degradation in search or briefing assembly.
4. Schema drift is mechanically prevented, not just documented.
5. Name resolution handles "Dan" correctly when there are three Dans.
6. The user can always answer: "What did TARS change?" (daily note log), "Why?" (changelog), "How do I undo it?" (git revert).
7. No sensitive data is persisted without explicit user approval.
8. Maintenance runs without user intervention and surfaces actionable findings.
9. The system works with zero external integrations (calendar, tasks) — they enrich but are not required.
10. A new user can go from empty vault to first daily briefing in under 15 minutes.

