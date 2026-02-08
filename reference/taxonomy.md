# Framework taxonomy

Standardized vocabulary for tags, types, categories, staleness tiers, and relationships. Use consistently for search and retrieval.

---

## Memory types

| Type | Folder | Description |
|------|--------|-------------|
| `person` | `memory/people/` | Internal or key external stakeholders |
| `vendor` | `memory/vendors/` | Vendors, contractors with relationships |
| `competitor` | `memory/competitors/` | Competitive intelligence |
| `product` | `memory/products/` | Our products and offerings |
| `initiative` | `memory/initiatives/` | Projects, programs, efforts |
| `decision` | `memory/decisions/` | Key decisions and rationale |
| `context` | `memory/organizational-context/` | Team dynamics, processes |
| `product-spec` | `contexts/products/` | Deep product documentation and specifications |

---

## Staleness tiers

Every memory file has a `staleness` field in frontmatter that determines archival behavior.

| Tier | Threshold | Behavior |
|------|-----------|----------|
| `durable` | Never | Never auto-archives. Core reference data (org charts, key decisions). |
| `seasonal` | 180 days | Archives if `updated` field is >180 days old. Quarterly review cadence. |
| `transient` | 90 days | Archives if `updated` field is >90 days old. Tactical or time-bound content. |
| `ephemeral` | Date-tagged | Individual lines with `[expires: YYYY-MM-DD]` tags are removed on expiry. |

Default tier if omitted: `seasonal`.

Archive destination: `archive/YYYY-MM/{category}/` with manifest in `archive/_archive_index.yaml`.
Unarchive: Available for non-ephemeral content via the maintain skill.
Search scope: Normal searches never touch archive. Use "search archive" for archived content.

### Tier assignment guidelines

- **Durable**: Org structure, key stakeholders, strategic decisions, product definitions
- **Seasonal**: Active initiative details, vendor relationships, competitor intelligence
- **Transient**: Meeting-specific context, temporary project details, time-bound tasks
- **Ephemeral**: Travel schedules, temporary contact info, event-specific details (use `[expires:]` tags)

---

## Standard tags

### People
- `stakeholder` -- Key decision-maker
- `executive` -- C-level or VP
- `team-member` -- Direct or indirect reports
- `external` -- Outside the organization

### Vendors
- `vendor` -- Provides products or services
- `consultant` -- Advisory services
- `active` -- Current relationship
- `former` -- Past relationship

### Competitors
- `direct` -- Head-to-head competition
- `adjacent` -- Overlapping market
- `emerging` -- Potential future threat
- `intelligence` -- Competitive info

### Initiatives
- `priority` -- High-priority effort
- `active` -- Currently in progress
- `planned` -- Future effort
- `completed` -- Finished

### Decisions

| Status | Definition |
|--------|------------|
| `proposed` | Under consideration |
| `decided` | Decision made, pending implementation |
| `implemented` | In effect |
| `superseded` | Replaced by newer decision |
| `rejected` | Considered but not adopted |

### Products
- `internal` -- Internal tool
- `external` -- Customer-facing
- `data` -- Data-related product
- `ai` -- AI-powered product

---

## Relationship types

Typed relationships make the knowledge graph queryable. Use in frontmatter `relationships` section and `[[Entity Name]]` wikilinks in body text.

| Relation | Direction | Example |
|----------|-----------|---------|
| `works_with` | Person <-> Person | Peer collaboration |
| `reports_to` | Person -> Person | Manager relationship |
| `member_of` | Person -> Team/Group | Team membership |
| `manages` | Person -> Team/Group | Management relationship |
| `owned_by` | Initiative -> Person | Initiative ownership |
| `works_on` | Person -> Initiative | Contributor relationship |
| `depends_on` | Initiative -> Initiative | Dependency chain |
| `relates_to` | Any -> Any | General association |
| `competes_with` | Competitor -> Product | Competitive overlap |
| `provides_to` | Vendor -> Product/Team | Vendor relationship |
| `key_contact` | Vendor -> Person | Primary contact |
| `decided_by` | Decision -> Person | Decision authority |
| `affects` | Decision -> Initiative | Impact relationship |

---

## Task metadata

| Field | Format | Required |
|-------|--------|----------|
| `due` | ISO date (YYYY-MM-DD) or `backlog` | Yes |
| `source` | `journal/YYYY-MM/YYYY-MM-DD-slug.md`, `direct`, `email` | Yes |
| `created` | ISO date (YYYY-MM-DD) | Yes |
| `initiative` | Initiative name as wikilink | If applicable |
| `owner` | Canonical person name | Yes |
| `status` | `open`, `blocked`, `completed` | Yes |

---

## Frontmatter templates

### Base memory template

Every memory entry must include:

```yaml
---
title: Full Name or Title
type: person | vendor | competitor | product | initiative | decision | context
staleness: durable | seasonal | transient
tags: [from standard tags above]
aliases: [alternate names, abbreviations]
summary: One-line description for index scanning
relationships:
  - type: relation_type
    target: "[[Entity Name]]"
    context: Optional one-line context
related: [linked entities]
updated: YYYY-MM-DD
---
```

### Person template

```yaml
---
title: Full Name
type: person
staleness: durable
tags: [stakeholder, executive, team-member, or external]
aliases: [First Name, nickname, abbreviations]
summary: Role and primary context
relationships:
  - type: reports_to
    target: "[[Manager Name]]"
  - type: member_of
    target: "[[Team Name]]"
  - type: works_on
    target: "[[Initiative Name]]"
related: [linked entities]
updated: YYYY-MM-DD
---

## Role and context
[Durable facts about this person's role, preferences, communication style]

## Ephemeral facts
[Time-bound information with expiry tags]
- Current focus: Q1 planning for data platform [expires: 2026-04-01]
- Out of office Feb 10-14 [expires: 2026-02-15]
- Prefers async updates until March [expires: 2026-03-01]
```

### Journal frontmatter

```yaml
---
date: YYYY-MM-DD
title: Entry Title
type: meeting | briefing-daily | briefing-weekly | wisdom | performance
participants: [Name1, Name2]
topics: [topic1, topic2]
initiatives: [Initiative1, Initiative2]
---
```

### Decision frontmatter

Standard naming convention: `YYYY-MM-DD-{slug}.md`
- Date is decision date (from frontmatter `date` field)
- Slug is kebab-case topic identifier

```yaml
---
date: YYYY-MM-DD
title: Decision Title
type: decision
staleness: durable
status: proposed | decided | implemented | superseded | rejected
decision_maker: "[[Person Name]]"
stakeholders: ["[[Person 1]]", "[[Person 2]]"]
affects: ["[[Initiative 1]]", "[[Product 1]]"]
supersedes: decision-file.md  # If replacing an earlier decision
summary: One-line description for index scanning
relationships:
  - type: decided_by
    target: "[[Person Name]]"
  - type: affects
    target: "[[Initiative Name]]"
updated: YYYY-MM-DD
---
```

### Product specification frontmatter

For deep product documentation in `contexts/products/`:

```yaml
---
title: Product Full Name
type: product-spec
staleness: seasonal
status: active | planned | deprecated
owner: "[[Person Name]]"
summary: One-line description for index
tags: [product-category, feature-tags]
relationships:
  - type: owned_by
    target: "[[Person Name]]"
related_initiatives: ["[[Initiative 1]]", "[[Initiative 2]]"]
related_decisions: ["[[Decision 1]]"]
updated: YYYY-MM-DD
version: "1.0"
---
```

---

## YAML-based index format

All `_index.md` files use YAML format for parseability and editability. Tags and staleness tiers are visible at the index level for filtering without opening individual files.

### Category index format (`memory/{category}/_index.md`)

```yaml
---
type: index
category: people
updated: YYYY-MM-DD
count: 5
---
entries:
  - name: "Jane Smith"
    file: jane-smith.md
    aliases: [Jane, JS]
    summary: "VP Engineering, leads platform team"
    tags: [executive, stakeholder]
    staleness: durable
    updated: 2026-02-07
  - name: "Bob Chen"
    file: bob-chen.md
    aliases: [Bob]
    summary: "Senior PM, data products"
    tags: [team-member]
    staleness: seasonal
    updated: 2026-01-15
```

### Master index format (`memory/_index.md`)

Consolidated view of every entity across all categories:

```yaml
---
type: master-index
updated: YYYY-MM-DD
total_entities: 25
---
categories:
  - name: people
    path: memory/people/
    count: 12
  - name: initiatives
    path: memory/initiatives/
    count: 5
  - name: decisions
    path: memory/decisions/
    count: 3
  - name: products
    path: memory/products/
    count: 2
  - name: vendors
    path: memory/vendors/
    count: 1
  - name: competitors
    path: memory/competitors/
    count: 1
  - name: organizational-context
    path: memory/organizational-context/
    count: 1
```

### Journal index format (`journal/YYYY-MM/_index.md`)

```yaml
---
type: journal-index
period: YYYY-MM
updated: YYYY-MM-DD
count: 8
---
entries:
  - date: 2026-02-07
    type: meeting
    title: "Q1 Planning Sync"
    file: 2026-02-07-q1-planning-sync.md
    participants: [Jane Smith, Bob Chen]
    initiatives: [Platform Rewrite]
```

### Product spec index format (`contexts/products/_index.md`)

```yaml
---
type: product-index
updated: YYYY-MM-DD
count: 2
---
entries:
  - name: "Data Platform"
    file: data-platform.md
    status: active
    owner: "Jane Smith"
    summary: "Core data processing and analytics platform"
    updated: 2026-02-01
```

---

## Folder structure

### Core folders

| Folder | Purpose |
|--------|---------|
| `memory/` | Persistent knowledge base with category subfolders |
| `journal/` | Chronological entries organized by `YYYY-MM/` |
| `contexts/` | Deep product documentation (`contexts/products/`) |
| `reference/` | Templates, configuration, and reference materials |
| `archive/` | Archived memory files organized by `YYYY-MM/{category}/` |
| `inbox/` | Content awaiting processing |
| `scripts/` | Automation scripts (Python/bash, stdlib-only) |

### Archive folder (`archive/`)

```
archive/
  _archive_index.yaml    # Manifest of all archived files
  2026-01/
    people/              # Archived person files from January
    initiatives/         # Archived initiative files from January
  2026-02/
    ...
```

Managed by `scripts/archive.py`. Supports `--dry-run` for preview.

### Inbox folder (`inbox/`)

```
inbox/
  pending/               # Files waiting for processing
  processing/            # Currently being processed
  completed/             # Successfully processed items
  failed/                # Failed items with companion .error files
```

Drop any content into `inbox/pending/`: meeting transcripts, articles, emails, notes. TARS auto-detects content type and routes to the appropriate skill. Each item is processed by an isolated sub-agent. Failed items get a companion `.error` file explaining what went wrong.

Daily briefing checks inbox and offers to process pending items.

---

## Integration registry

Skills reference integrations by **category** (calendar, tasks, project_tracker, etc.), not by specific tool name. The registry at `reference/integrations.md` defines each integration's provider, type, operations, and constraints.

### Integration categories

| Category | Required | Description |
|----------|----------|-------------|
| `calendar` | Yes | Schedule, events, availability |
| `tasks` | Yes | Task creation, editing, completion |
| `project_tracker` | No | Issues, sprints, backlog |
| `documentation` | No | Wiki, docs, knowledge base |
| `data_warehouse` | No | Data queries, schemas |
| `analytics` | No | Metrics, dashboards |
| `time_tracking` | No | Utilization, capacity |
| `monitoring` | No | Infrastructure health, alerts |

### Provider types

| Type | Interface | Example |
|------|-----------|---------|
| `http-api` | Local HTTP server, invoked via curl | Eventlink (Apple Calendar) |
| `cli` | Command-line tool, invoked via bash | remindctl (Apple Reminders) |
| `mcp` | MCP server, detected from `<mcp_servers>` at runtime | Todoist, Jira, Confluence |

### How skills use integrations

1. Read `reference/integrations.md`, find the relevant category section
2. Check `status` field: `configured` → proceed, `not_configured` → skip and note gap
3. Execute operations using the provider's type-specific interface
4. If a configured integration fails at runtime, fall back to workspace-only data and report the gap

Health check: `scripts/verify-integrations.py` validates all configured integrations.

---

## Core concepts

### Durability test (memory gate)

Every memory addition must pass ALL four criteria:

| Criterion | Question |
|-----------|----------|
| **Lookup value** | Will this be useful for lookup next week or next month? |
| **Signal** | Is this high-signal and broadly applicable? |
| **Durability** | Is this durable (not transient or tactical)? |
| **Behavior change** | Does this change how I should interact in the future? |

If ANY answer is "No", do not persist to memory.

### Accountability test (task gate)

Every task must meet ALL three criteria:

| Criterion | Question |
|-----------|----------|
| **Concrete** | Is it a specific deliverable (not "think about", "consider")? |
| **Owned** | Is there a clear owner? |
| **Verifiable** | Will we know objectively when it's done? |

Pass: "Send Q3 roadmap draft to Sarah by Friday"
Fail: "Synergize on the roadmap"

### Index-first pattern

**Mandatory for all searches.** Every folder query reads `_index.md` first, then opens only the specific files needed. This prevents context window blowout when memory grows to hundreds of entries.

Never scan all files in a folder. Always use the index.

### Ephemeral facts

Time-bound information in person files uses `[expires: YYYY-MM-DD]` tags. These lines are automatically removed by `scripts/archive.py` when the date passes.

Use for: travel schedules, temporary preferences, time-bound project focus, out-of-office periods. Place in a clearly marked "Ephemeral facts" section within the person file.
