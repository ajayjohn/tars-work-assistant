---
name: briefing
description: Daily and weekly briefings with calendar, tasks, people context, and system status
triggers: ["daily briefing", "what's my day look like", "weekly briefing", "plan my week", "weekly planning"]
user-invocable: true
help:
  purpose: |-
    Daily and weekly briefings combining calendar, tasks, people context, initiative status, and system health into actionable intelligence.
  use_cases:
    - "Daily briefing"
    - "What's my day look like?"
    - "Weekly briefing"
    - "Plan my week"
  scope: briefing,calendar,tasks,planning,initiatives
---

# Briefing Protocol

Unified protocol for daily and weekly briefings. Mode is determined by the request signal.

All integration calls (calendar, tasks) resolve through `mcp__tars_vault__resolve_capability(capability=…)` — never hard-code `mcp__apple_calendar__*` or `mcp__microsoft_365_*`. Vault reads/writes use `mcp__tars_vault__*` tools. See `skills/core/SKILL.md` → "Write interface" for the full tool list.

| Signal | Mode |
|--------|------|
| "daily briefing", "what's my day look like?", "morning briefing" | Daily |
| "weekly briefing", "plan my week", "weekly planning", "what's my week" | Weekly |
| Ambiguous | Default to daily unless the user mentions "week" |

**Parallelization**: Data gathering (calendar, tasks, memory) runs as **three parallel sub-agents** using the Task tool. This reduces wall-clock time since calendar queries, task queries, and memory lookups are independent operations. Launch all three in a single message.

---

# Daily Briefing

Generate a focused morning briefing for clarity and prioritization.

---

## Step 1: Determine date and load configuration

- Determine target date: if current time is after 5 PM, brief for tomorrow. Otherwise, brief for today.
- Resolve target date to `YYYY-MM-DD` format.
- Output folder: `journal/YYYY-MM/`

---

## Steps 2-4: Parallel data gathering (sub-agents)

Spawn **three parallel sub-agents** using the Task tool. **Launch all three in a single message** using multiple Task tool calls.

### Sub-agent A: Fetch calendar

```
cap = mcp__tars_vault__resolve_capability(capability="calendar")
If cap.status == "unavailable": return {"status": "not_configured"}.

Resolve {target_date} to YYYY-MM-DD.
Call cap.tools[0].name (typically a list_events-style tool) for {target_date} with offset=1.
For each event extract: time, title, duration, attendee names.

Return JSON:
{
  "status": "ok" | "not_configured" | "error",
  "events": [{"time": "HH:MM", "end_time": "HH:MM", "title": "...", "attendees": ["..."], "location": "..."}],
  "error": null | "description"
}
```

### Sub-agent B: Fetch tasks

```
cap = mcp__tars_vault__resolve_capability(capability="tasks")
If cap.status == "unavailable": return {"status": "not_configured"}.

Use cap.tools[*] to list primary task list (default: Active).
Identify tasks due {target_date} or highest priority.
Run overdue check for tasks past due date.

Return JSON:
{
  "status": "ok" | "not_configured" | "error",
  "tasks_due_today": [{"title": "...", "due": "...", "list": "...", "priority": "high|medium|low"}],
  "overdue": [{"title": "...", "due": "...", "list": "...", "days_overdue": 0}],
  "top_priority": [{"title": "...", "due": "...", "list": "..."}],
  "error": null | "description"
}
```

### Sub-agent C: Query memory and context

```
People:       mcp__tars_vault__search_by_tag(tag="tars/person", limit=100)
  Build a people lookup table: name → summary, open items.

Initiatives:  mcp__tars_vault__search_by_tag(tag="tars/initiative", frontmatter={"tars-status": "active"}, limit=20)
  Extract: initiative name, status, upcoming milestones.

Read _system/schedule.md if it exists:
  Identify [RECURRING] and [ONCE] items due {target_date}.

Inbox:        mcp__tars_vault__search_by_tag(tag="tars/inbox", limit=1)
  (Result count indicates pending items.)

Schedule:     mcp__tars_vault__read_note(file="schedule")      (skip if absent)
Housekeeping: mcp__tars_vault__read_note(file="housekeeping-state")

Live hydration counts (replaces the old "Level 1" artifact — read from disk,
don't trust `_system/maturity.yaml` which drifts):
  Bash: python3 scripts/sync.py --hydration <TARS_VAULT_PATH>
  → JSON: {"hydration": {"people_count": N, "initiative_count": N,
                         "decision_count": N, "journal_count": N,
                         "task_count": N, "last_checked": "YYYY-MM-DD"}}

Return JSON:
{
  "people_context": [{"name": "...", "summary": "...", "open_items": ["..."]}],
  "initiative_context": [{"name": "...", "status": "...", "next_milestone": "..."}],
  "scheduled_items": [{"type": "recurring|once", "description": "...", "due": "..."}],
  "inbox_count": 0,
  "housekeeping_last_run": "YYYY-MM-DD",
  "hydration": {"people_count": N, "initiative_count": N, "decision_count": N,
                "journal_count": N, "task_count": N}
}
```

### Sub-agent contracts (daily)

| Sub-agent | Input | Output | Failure mode |
|-----------|-------|--------|-------------|
| Calendar | MCP server or integrations.md, target date | JSON: events with times, titles, attendees | Return `status: error`, briefing proceeds without calendar |
| Tasks | MCP server or integrations.md, target date | JSON: due today, overdue, top priority | Return `status: error`, briefing proceeds without tasks |
| Memory | People search, initiatives search, schedule, inbox, system state | JSON: people context, initiatives, scheduled items, system status | Return partial data, briefing uses what is available |

**Attendee note**: Calendar data may not be available when spawning the memory sub-agent. Spawn without attendee names. After calendar sub-agent returns, do a quick targeted lookup for any attendees not covered by the initial people search.

---

## Step 5: Cross-reference and enrich

After all three sub-agents complete:

1. **Match attendees to memory**: For each person in today's calendar events, find their memory profile. Extract: summary, recent interactions, open items, responses owed.
2. **Targeted lookups**: For attendees not covered by the initial search, do targeted reads:
   ```
   mcp__tars_vault__read_note(file="<person name>")
   ```
3. **Link tasks to meetings**: Match tasks to meetings by initiative, person, or topic overlap.
4. **Flag unrecognized people**: Calendar attendees with no memory profile get flagged:
   ```
   "3 people not in memory: [names]. Add profiles? [Y/N]"
   ```
5. **Identify focus opportunities**: Find calendar gaps of 30+ minutes for deep work.

---

## Step 6: Generate briefing

```markdown
# Daily Briefing — YYYY-MM-DD

## Today's schedule
| Time | Meeting | Key attendees | Prep needed |
|------|---------|---------------|-------------|
| 9:00 | Q1 Planning | [[Jane Smith]], [[Bob Chen]] | Review Q1 metrics |
| 11:00 | 1:1 with Sarah | [[Sarah Park]] | Discuss hiring plan |
| 2:00 | — Open — | | *Focus block: 2 hours* |

## Scheduled items due today
- [RECURRING] Weekly report submission
- [ONCE] Submit vendor evaluation by EOD

## Priority tasks
1. **[OVERDUE]** Review hiring plan — due Mar 19 (2 days overdue)
2. Share migration report with [[Bob Chen]] — due today
3. Follow up with [[Sarah Park]] on API contract — due today

> Tasks linked to meetings: #2 relates to Q1 Planning at 9:00

## People I'm meeting
### [[Jane Smith]] — VP Engineering
- **Context**: Leading [[Platform Rewrite]], approved 2 backend hires
- **Open items**: Waiting on Q3 timeline estimate
- **Ask about**: Mobile team staffing decision

### [[Sarah Park]] — Engineering Manager
- **Context**: New hire, started Jan 2026
- **Response owed**: She asked about API vendor shortlist on Mar 18

## Initiative pulse
| Initiative | Health | Today's relevance |
|------------|--------|-------------------|
| [[Platform Rewrite]] | On track | Discussed in Q1 Planning |
| [[API Migration]] | At risk | Follow-up with Sarah |

## Focus opportunities
- 2:00-4:00 PM: 2-hour open block → Suggested: Review hiring plan (overdue)

## Unrecognized people
- john.doe@external.com (in Q1 Planning) — not in memory

## System status
- Vault hydration: 106 people, 7 initiatives, 50 decisions, 195 tasks, 123 journal entries
- Inbox: 3 items pending
- Last housekeeping: 2026-03-18

---
*Data freshness: 4 meetings, 8 tasks, 12 memory files queried.*
*Stale: [[Tom Richards]] not updated in 65 days.*
```

**Note on hydration**: the System status line reports **live** counts from the latest
`scripts/sync.py --hydration` run, not from `_system/maturity.yaml` (which drifts
and is repaired by `/lint`'s framework-self-state check — §5.2). The numbers above
are illustrative; the skill always pulls actual counts at briefing generation time.

---

## Step 7: Save and display

```
mcp__tars_vault__create_note(
  name="YYYY-MM-DD Daily Briefing",
  path="journal/YYYY-MM/YYYY-MM-DD-daily-briefing.md",
  template="briefing",
  frontmatter={
    "tags": ["tars/journal", "tars/briefing"],
    "tars-date": "YYYY-MM-DD",
    "tars-briefing-type": "daily",
    "tars-created": "YYYY-MM-DD"
  },
  body="<generated briefing markdown>"
)
```

Display the full briefing directly to the user.

---

## Step 8: Cron self-check — Issue 10

After generating the briefing, verify scheduled automation:

1. Execute `CronList` to check all registered cron jobs
2. Verify expected jobs are active:
   - Daily briefing (if configured)
   - Weekly briefing (if configured)
   - Maintenance/housekeeping (if configured)
3. If any scheduled jobs have expired or are missing:
   - Re-register via `CronCreate`
   - Update `_system/housekeeping-state.yaml` with new cron job IDs
   - Note in briefing: "Re-registered expired cron job: [description]"

---

## Step 9: Daily-note log (handled by PostToolUse hook)

The `PostToolUse` hook appends the briefing-generation line to the daily note after `create_note` succeeds. No explicit append call is required. Emit telemetry event `briefing_generated` with `{meetings, tasks_due_today, overdue, unrecognized_people}` counts for the skill-activity view.

---

# Weekly Briefing

Generate a comprehensive weekly briefing for strategic planning and review.

---

## Step 1: Determine date range and load configuration

- Current week: Monday through Sunday of the current week
- Last week: Previous Monday through Sunday
- Resolve all dates to `YYYY-MM-DD` format
- Output folder: `journal/YYYY-MM/`

---

## Steps 2-4: Parallel data gathering (sub-agents)

Spawn **three parallel sub-agents** using the Task tool. **Launch all three in a single message.**

### Sub-agent A: Fetch calendar (weekly)

```
cap = mcp__tars_vault__resolve_capability(capability="calendar")
If cap.status == "unavailable": return {"status": "not_configured"}.

Resolve {monday_date} to YYYY-MM-DD format.
Call cap.tools[*] (list_events-style) with {monday_date} and offset=7.
Identify high-priority meetings (executives, leadership, clients, key stakeholders).
Identify open time slots of 60+ minutes.

Return JSON:
{
  "status": "ok" | "not_configured" | "error",
  "events": [{"date": "...", "time": "...", "end_time": "...", "title": "...", "attendees": ["..."], "priority": "high|normal"}],
  "open_slots": [{"date": "...", "start": "...", "end": "...", "duration_minutes": 0}],
  "error": null | "description"
}
```

### Sub-agent B: Fetch tasks (weekly)

```
cap = mcp__tars_vault__resolve_capability(capability="tasks")
If cap.status == "unavailable": return {"status": "not_configured"}.

Using cap.tools[*], list ALL configured lists (default: Active, Delegated, Backlog).
Execute overdue check.
Identify tasks due this week ({monday_date} through {sunday_date}).
Identify backlog items older than 90 days (flag as stale).
Identify tasks completed last week (if integration supports it).

Return JSON:
{
  "status": "ok" | "not_configured" | "error",
  "tasks_due_this_week": [{"title": "...", "due": "...", "list": "...", "owner": "..."}],
  "overdue": [{"title": "...", "due": "...", "list": "...", "days_overdue": 0}],
  "backlog_stale": [{"title": "...", "created": "...", "days_old": 0}],
  "completed_last_week": [{"title": "...", "completed": "..."}],
  "error": null | "description"
}
```

### Sub-agent C: Query memory and context (weekly)

```
People:       mcp__tars_vault__search_by_tag(tag="tars/person", limit=100)
  For frequent meeting attendees, read full profiles.
  Identify responses owed and follow-ups needed across all people.

Initiatives:  mcp__tars_vault__search_by_tag(tag="tars/initiative", frontmatter={"tars-status": "active"}, limit=20)
  Extract: name, status, milestones due this week, health indicators.

Journal:      mcp__tars_vault__search_by_tag(tag="tars/journal",
                 frontmatter={"tars-date__gte": "{last_monday}"}, limit=50)
  Summarize: meetings held, decisions made, tasks completed.

Schedule:     mcp__tars_vault__read_note(file="schedule")         (skip if absent)
Inbox:        mcp__tars_vault__search_by_tag(tag="tars/inbox", limit=1)
Housekeeping: mcp__tars_vault__read_note(file="housekeeping-state")

Live hydration counts:
  Bash: python3 scripts/sync.py --hydration <TARS_VAULT_PATH>
  → JSON: {"hydration": {"people_count": N, "initiative_count": N,
                         "decision_count": N, "journal_count": N,
                         "task_count": N, "last_checked": "YYYY-MM-DD"}}

Return JSON:
{
  "people_context": [{"name": "...", "summary": "...", "responses_owed": ["..."], "follow_ups": ["..."]}],
  "initiatives": [{"name": "...", "status": "...", "health": "on_track|at_risk|blocked", "milestones_this_week": ["..."]}],
  "last_week_entries": [{"date": "...", "type": "meeting|briefing|wisdom", "title": "...", "key_outcomes": ["..."]}],
  "scheduled_items": [{"type": "recurring|once", "description": "...", "due": "..."}],
  "inbox_count": 0,
  "housekeeping_last_run": "YYYY-MM-DD",
  "last_index_rebuild": "YYYY-MM-DD",
  "hydration": {"people_count": N, "initiative_count": N, "decision_count": N,
                "journal_count": N, "task_count": N}
}
```

### Sub-agent contracts (weekly)

| Sub-agent | Input | Output | Failure mode |
|-----------|-------|--------|-------------|
| Calendar | MCP server or integrations.md, monday date, offset=7 | JSON: events, open slots, priority flags | Return `status: error`, briefing proceeds without calendar |
| Tasks | MCP server or integrations.md, date range | JSON: due this week, overdue, stale backlog, completed last week | Return `status: error`, briefing proceeds without tasks |
| Memory/Context | People search, initiatives search, journal entries, schedule, inbox, system state | JSON: people context, initiatives, last week summary, system status | Return partial data, briefing uses what is available |

---

## Step 5: Cross-reference and enrich

After all three sub-agents complete:

1. **Match attendees to memory**: For all people appearing in this week's meetings, find memory profiles.
2. **Targeted lookups**: Read full profiles for high-priority meeting attendees.
3. **Link tasks to meetings**: Match tasks to meeting topics and initiatives.
4. **Identify preparation needs**: Flag meetings that require advance preparation (docs, reports, decisions).
5. **Match focus time to priorities**: Pair open calendar slots with highest-priority tasks.
6. **Flag responses owed**: People who are owed a response and appear in this week's meetings.
7. **Review last week**: Cross-reference completed tasks against planned tasks for gap analysis.

---

## Step 6: Generate briefing

```markdown
# Weekly Briefing — Week of YYYY-MM-DD

## Last week summary
### Completed
- Processed 5 meetings, created 12 tasks
- Completed: Review hiring plan, Share migration report, 3 others
- Decision made: REST over GraphQL for public API

### Incomplete
- Vendor evaluation — carried over (blocked on pricing data)
- API contract review — pushed to this week

---

## This week's meetings

### High-priority (flag)
| Date | Time | Meeting | Attendees | Prep needed |
|------|------|---------|-----------|-------------|
| Mon | 10:00 | Board Update | [[CEO]], [[CFO]] | Prepare Q1 summary deck |
| Thu | 14:00 | Client Review | [[Client PM]] | Review deliverables status |

### Full schedule
| Date | Time | Meeting | Attendees |
|------|------|---------|-----------|
| Mon | 10:00 | Board Update | [[CEO]], [[CFO]] |
| Mon | 14:00 | Team Standup | Engineering team |
| Tue | 09:00 | 1:1 with [[Sarah Park]] | |
| ... | ... | ... | ... |

---

## Open tasks

### Due this week
| Task | Due | Owner | Related meeting |
|------|-----|-------|----------------|
| Vendor evaluation | Mon | You | Board Update |
| API contract review | Wed | You | Client Review |

### Overdue
| Task | Due | Days overdue |
|------|-----|-------------|
| Review hiring plan | Mar 19 | 5 days |

### Meeting preparation
- **Board Update (Mon)**: Prepare Q1 summary deck, review initiative health
- **Client Review (Thu)**: Collect deliverables status from [[Bob Chen]]

---

## Milestones and initiatives
| Initiative | Health | This week | Next milestone |
|------------|--------|-----------|----------------|
| [[Platform Rewrite]] | On track | Sprint review Wed | Beta launch Apr 15 |
| [[API Migration]] | At risk | Client review Thu | Contract sign-off Mar 30 |
| [[Hiring Push]] | On track | 2 interviews this week | Offers by Apr 1 |

---

## People context

### Responses owed
| Person | What | When promised | Meeting this week |
|--------|------|--------------|-------------------|
| [[Sarah Park]] | API vendor shortlist | Mar 18 | 1:1 Tuesday |
| [[Bob Chen]] | Migration timeline | Mar 20 | Team standup Mon |

### Questions to ask
- [[Jane Smith]]: Q3 timeline estimate (open since Mar 15)
- [[Client PM]]: Budget approval status

---

## Recommended focus time
| Date | Slot | Duration | Suggested task |
|------|------|----------|----------------|
| Tue | 13:00-16:00 | 3 hours | Vendor evaluation (due Mon — overdue!) |
| Wed | 10:00-12:00 | 2 hours | API contract review (due Wed) |
| Fri | 09:00-17:00 | Full day | Deep work on Q2 planning |

---

## Backlog review (>90 days stale)
| Task | Created | Days old | Recommendation |
|------|---------|----------|----------------|
| Research cloud migration options | Dec 2025 | 95 days | Reprioritize or remove |
| Draft team handbook | Nov 2025 | 120 days | Remove — superseded by wiki |

---

## System status
- Vault hydration: 106 people, 7 initiatives, 50 decisions, 195 tasks, 123 journal entries (live)
- Inbox: 3 items pending
- Last housekeeping: 2026-03-18
- Last schema validation: 2026-03-20
- Cron jobs: 3 active (daily briefing, weekly briefing, housekeeping)

---
*Data freshness: 12 meetings this week, 24 tasks across 3 lists, 15 memory profiles queried.*
*Stale memory: [[Tom Richards]] (65 days), [[Vendor X]] (90 days).*
```

---

## Step 7: Save and display

```
mcp__tars_vault__create_note(
  name="YYYY-MM-DD Weekly Briefing",
  path="journal/YYYY-MM/YYYY-MM-DD-weekly-briefing.md",
  template="briefing",
  frontmatter={
    "tags": ["tars/journal", "tars/briefing"],
    "tars-date": "YYYY-MM-DD",
    "tars-briefing-type": "weekly",
    "tars-week-start": "YYYY-MM-DD",
    "tars-week-end": "YYYY-MM-DD",
    "tars-created": "YYYY-MM-DD"
  },
  body="<generated briefing markdown>"
)
```

Display key highlights to the user (full briefing is saved to journal).

---

## Step 8: Cron self-check — Issue 10

Same as daily briefing Step 8. Verify all scheduled cron jobs are active, re-register any that expired.

---

## Step 9: Daily-note log (handled by PostToolUse hook)

The `PostToolUse` hook writes the daily-note line after the briefing create_note succeeds. Emit telemetry event `briefing_generated` with `{briefing_type: "weekly", meetings, tasks_due, overdue, stale_backlog, initiatives}` counts.

---

# Progress tracking

Use the `TodoWrite` tool to give the user real-time visibility into briefing generation. Create the todo list at the start and update as steps complete.

**Daily mode:**
```
1. Determine date and load configuration              [in_progress → completed]
2. Fetch calendar data (parallel sub-agent)            [pending → in_progress → completed]
3. Fetch task data (parallel sub-agent)                [pending → in_progress → completed]
4. Query memory and context (parallel sub-agent)       [pending → in_progress → completed]
5. Cross-reference and enrich data                     [pending → in_progress → completed]
6. Generate and save briefing                          [pending → in_progress → completed]
7. Cron self-check                                     [pending → completed]
```

**Weekly mode:**
```
1. Determine date range and load configuration         [in_progress → completed]
2. Fetch calendar data (parallel sub-agent)            [pending → in_progress → completed]
3. Fetch task data (parallel sub-agent)                [pending → in_progress → completed]
4. Query memory and context (parallel sub-agent)       [pending → in_progress → completed]
5. Cross-reference and enrich data                     [pending → in_progress → completed]
6. Generate and save briefing                          [pending → in_progress → completed]
7. Cron self-check                                     [pending → completed]
```

**Parallelization note**: Steps 2, 3, and 4 run concurrently as sub-agents. Mark ALL THREE as `in_progress` when spawning them. Mark each `completed` as its sub-agent returns. Do not wait for all three before updating individual statuses.

---

# Frontmatter (both modes)

```yaml
---
tags: [tars/journal, tars/briefing]
tars-date: YYYY-MM-DD
tars-briefing-type: daily | weekly
tars-created: YYYY-MM-DD
---
```

Weekly mode adds:
```yaml
tars-week-start: YYYY-MM-DD
tars-week-end: YYYY-MM-DD
```

---

# Context budgets

| Source | Daily | Weekly |
|--------|-------|--------|
| Calendar | list_events for 1 day | list_events for 7 days |
| Tasks | Active list only | Active + Delegated + Backlog lists |
| People | Search + up to 5 targeted reads | Search + up to 10 targeted reads |
| Initiatives | Active initiatives only | Active initiatives + health details |
| Journal | — | Last week's entries via search |
| Schedule | `_system/schedule.md` | `_system/schedule.md` |
| Inbox | Count only | Count only |
| System | housekeeping-state.yaml + live hydration (via `sync.py --hydration`) | same |

---

# Self-evaluation — Issue 9

If any errors occur during briefing generation:

1. Check `_system/backlog/issues/` for existing issue with same error signature
2. If exists: increment `tars-occurrence-count`, update `tars-last-seen`
3. If new: create issue note with context via the issue template
4. Continue generating briefing with available data — never fail silently

---

# Absolute constraints

- NEVER skip calendar lookup — fall back to tasks-only if calendar is unreachable, but always attempt
- NEVER output a briefing without saving to journal
- ALWAYS resolve dates to `YYYY-MM-DD` format before any calendar query
- ALWAYS look up memory profiles for meeting attendees
- ALWAYS flag overdue tasks prominently
- ALWAYS check calendar integration constraints before querying
- ALWAYS include the data freshness footer with sources used and stale memory flagged
- ALWAYS verify cron jobs during the self-check step (Issue 10)
- NEVER fabricate meetings, tasks, or people context — only report what is found
- NEVER skip the cross-reference step — attendees must be matched to memory
- ALWAYS include system status section with live vault hydration counts (from `sync.py --hydration`), inbox count, and last housekeeping date — never hardcoded "Level N" labels
