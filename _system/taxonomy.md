---
tags:
  - tars/system
tars-created: 2026-03-21
---

# Taxonomy

## Entity Types

| Type | Tag | Storage | Template | Staleness Tiers |
|------|-----|---------|----------|----------------|
| Person | `tars/person` | `memory/people/` | `person` | durable, seasonal, transient |
| Vendor | `tars/vendor` | `memory/vendors/` | `vendor` | durable, seasonal, transient |
| Competitor | `tars/competitor` | `memory/competitors/` | `competitor` | durable, seasonal, transient |
| Product | `tars/product` | `memory/products/` | `product` | durable, seasonal, transient |
| Initiative | `tars/initiative` | `memory/initiatives/` | `initiative` | — (status-driven) |
| Decision | `tars/decision` | `memory/decisions/` | `decision` | — (status-driven) |
| Org Context | `tars/org-context` | `memory/org-context/` | `org-context` | durable, seasonal, transient |

## Journal Types

| Type | Tags | Storage | Template |
|------|------|---------|----------|
| Meeting | `tars/journal`, `tars/meeting` | `journal/YYYY-MM/` | `meeting-journal` |
| Daily Briefing | `tars/journal`, `tars/briefing` | `journal/YYYY-MM/` | `daily-briefing` |
| Weekly Briefing | `tars/journal`, `tars/briefing` | `journal/YYYY-MM/` | `weekly-briefing` |
| Wisdom | `tars/journal`, `tars/wisdom` | `journal/YYYY-MM/` | `wisdom-journal` |
| Analysis | `tars/journal`, `tars/analysis` | `journal/YYYY-MM/` | — |

## Operational Types

| Type | Tags | Storage | Template |
|------|------|---------|----------|
| Task | `tars/task` | `memory/tasks/` or inline | — |
| Transcript | `tars/transcript` | `archive/transcripts/YYYY-MM/` | `transcript` |
| Companion | `tars/companion` | alongside original file | `companion` |
| Issue | `tars/backlog`, `tars/issue` | `_system/backlog/issues/` | `issue` |
| Idea | `tars/backlog`, `tars/idea` | `_system/backlog/ideas/` | `idea` |
| Inbox Item | `tars/inbox` | `inbox/pending/` | — |

## Staleness Tiers

| Tier | Archive Threshold | Description |
|------|------------------|-------------|
| durable | Never auto-archive | Core organizational knowledge, key relationships |
| seasonal | 180 days without update | Quarterly relevance: vendor contracts, project phases |
| transient | 90 days without update | Tactical: meeting series, short-term projects |
| ephemeral | 30 days without update | One-time events, temporary context |

## Relationship Types

Used in note body as inline fields:
- `reports_to::` — person reports to person
- `works_on::` — person works on initiative
- `member_of::` — person member of team/group
- `depends_on::` — initiative depends on initiative
- `supersedes::` — decision supersedes decision
- `affects::` — decision affects initiative
