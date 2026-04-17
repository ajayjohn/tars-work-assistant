---
name: tasks
description: Extract tasks from text or manage existing tasks with accountability testing and duplicate checking
triggers: ["extract tasks from", "what's on my plate", "show tasks", "mark done", "task review"]
---

# Tasks skill

Extract commitments into actionable, accountable tasks from any input source, or manage existing tasks with review, prioritization, completion, and pruning.

All vault writes go through `mcp__tars_vault__*` tools (see `skills/core/SKILL.md` → "Write interface"). External task-system integration (Apple Reminders, Microsoft 365 Tasks, Todoist, etc.) resolves through `mcp__tars_vault__resolve_capability(capability="tasks")` — never hard-code specific server names. All names use canonical forms from the alias registry. Task creation always requires user confirmation via the numbered review list.

---

## Mode detection

| Signal | Mode |
|--------|------|
| User provides text with action items, "extract tasks from..." | Extract mode |
| Called from meeting processing pipeline (Step 10) | Extract mode |
| "What's on my plate?", "show tasks", "task review" | Manage mode |
| "Mark X as done", "complete [task]" | Manage mode |
| "Reprioritize", "move to backlog" | Manage mode |

---

# EXTRACT MODE

Convert loose commitments from any input source into actionable tasks with accountability validation, duplicate checking, and user-confirmed creation.

Input can be: meeting transcript excerpt, email, conversation, freeform notes, or a call from the meeting processing pipeline.

---

## Step 1: Alias registry (server-cached)

Alias resolution runs via `mcp__tars_vault__resolve_alias(name="…")`. The server keeps the registry in memory and invalidates on file-mtime change — no explicit load is required. Every task owner is normalized to their canonical name before presentation or creation.

---

## Step 2: Scan for commitment patterns

Scan the input text for language that signals a commitment or action item:

### Pattern categories

| Pattern | Examples |
|---------|----------|
| Direct commitment | "I will...", "I'll...", "I need to..." |
| Assignment | "Can you...", "Please...", "[Name] will..." |
| Deadline signal | "By [date]...", "Before the end of...", "Due [date]..." |
| Explicit markers | "Action item:", "TODO:", "Follow up:", "Next step:" |
| Conditional commitment | "If X, then I'll...", "Once Y is done, we need to..." |
| Implicit obligation | "We agreed to...", "The plan is to...", "We decided..." |

Extract every candidate. Do not filter at this stage.

---

## Step 3: Apply accountability test

For each candidate, test ALL three criteria:

| Criterion | Question | Pass | Fail |
|-----------|----------|------|------|
| Concrete | Is it a specific deliverable or action? | "Review hiring plan" | "Think about Q4" |
| Owned | Does it have a clear single owner? | "Bob will send the report" | "The team needs to align" |
| Verifiable | Will we know when it's done? | "Share report by Friday" | "Stay on top of things" |

All three must pass for a task to be marked `[KEEP]`.

**Failure reasons to cite:**
- "No owner" -- commitment uses "we", "the team", "someone" without naming a lead
- "Not concrete" -- uses vague language like "think about", "look into", "keep an eye on"
- "Not verifiable" -- no clear completion state, ongoing/monitoring language
- "Not actionable" -- observation or wish, not a commitment

---

## Step 4: Resolve metadata

For each task passing the accountability test, resolve all metadata fields:

### Owner normalization

Map the raw name to canonical form using the alias registry. If ambiguous or unknown, apply the name resolution cascade:
1. Alias registry exact match
2. Vault search: `mcp__tars_vault__search_by_tag(tag="tars/person", query="<name>", limit=5)`
3. Context clues (role references, team mentions)
4. Ask the user (batch all unresolved names in one question)

### Date resolution

| User says | Resolution |
|-----------|------------|
| "today" | Current date YYYY-MM-DD |
| "tomorrow" | Current date + 1 day |
| "this week" | Thursday of current week |
| "next week" | Monday of next week |
| "Friday" / "next Friday" | First occurrence of that day after today |
| "end of month" | Last day of current month |
| "end of quarter" | Last day of current quarter |
| "later" / no date | Backlog (no due date) |

NEVER use relative dates in output. Always resolve to YYYY-MM-DD.

### Source

| Context | Source value |
|---------|------------|
| From meeting pipeline | `[[YYYY-MM-DD Meeting Title]]` (journal entry wikilink) |
| From email | `email` with subject in notes |
| From conversation | `direct` |
| From inbox item | `[[inbox item name]]` |

### Project/initiative

If the task relates to a known initiative, link it:
```
mcp__tars_vault__search_by_tag(tag="tars/initiative", query="<keywords>", limit=3)
```
If a match is found, set `tars-initiative` to the initiative wikilink.

---

## Step 5: Check for duplicates

Search existing open tasks for potential matches:

```
mcp__tars_vault__search_by_tag(
  tag="tars/task",
  frontmatter={"tars-status": "open"},
  query="<task keywords>",
  limit=10
)
```

Compare by title similarity and owner. For each candidate:

| Match type | Action |
|-----------|--------|
| Exact duplicate (same title, same owner) | Skip, note as "Already exists" |
| Similar task, same owner | Flag: "Similar to existing task: [title]. Create anyway?" |
| Same task, different owner | Allow (different people can own similar tasks) |

---

## Step 6: Present numbered review list (MANDATORY)

Always present ALL candidates, showing both kept and filtered items. This step is never skipped, even when called from the meeting pipeline.

```
[N] potential tasks found. [M] pass the accountability test:

  1. [KEEP] Review hiring plan (you, due 2026-03-25, high)
  2. [KEEP] Share migration report (Bob Chen, due 2026-03-24, medium)
  3. [KEEP] Update API documentation (you, due 2026-03-28, medium)
  4. [KEEP] Schedule vendor demo (Sarah Lopez, due 2026-03-26, low)
  5. [KEEP] Draft budget proposal (you, due 2026-03-31, high)

  -- Filtered out --
  6. "We should think about Q4" -- no owner, not concrete
  7. "The team needs to align on priorities" -- no specific owner
  8. "Keep an eye on the timeline" -- not verifiable

  -- Duplicates --
  9. "Review hiring plan" -- already exists (task from 2026-03-18)

Which to create?
  - "all" to create 1-5
  - "1, 3" to keep specific ones
  - "all except 4" to exclude specific ones
  - "move 7 to keep" to override a filter (you'll be asked for an owner)
  - "none" to skip all
```

### Selection syntax

| Input | Behavior |
|-------|----------|
| `all` | Create all `[KEEP]` items |
| `1, 3, 5` | Create only those numbered items |
| `all except 2` | Create all `[KEEP]` items except #2 |
| `move 7 to keep` | Override a filtered item. If it failed for missing owner, ask for owner. If not concrete, ask user to rephrase. |
| `none` | Skip all task creation |

NEVER create tasks without this review step. NEVER auto-create.

---

## Step 7: Create confirmed tasks

For each task the user selected, create a note in the vault:

```
mcp__tars_vault__create_note(
  name="Task Title",
  path="tasks/YYYY-MM-DD-task-slug.md",
  template="task",
  frontmatter={
    "tags": ["tars/task"],
    "tars-status": "open",
    "tars-owner": "[[Owner Name]]",
    "tars-due": "YYYY-MM-DD",
    "tars-priority": "high | medium | low",
    "tars-source": "[[Source]]",
    "tars-initiative": "[[Initiative Name]]",
    "tars-category": "active | delegated | backlog",
    "tars-created": "YYYY-MM-DD"
  }
)
```

Phase 5 adds optional fields `tars-blocked-by`, `tars-age-days`, `tars-escalation-level` per §9.1 — backward-compatible; the server's schema validator accepts notes without them.

### Task placement logic

| Condition | Category |
|-----------|----------|
| Has due date, owner is user | `active` |
| Has due date, owner is someone else | `delegated` |
| No due date | `backlog` |

### Priority assignment

| Signal | Priority |
|--------|----------|
| Explicit urgency ("ASAP", "critical", "urgent") | `high` |
| Near-term deadline (within 3 business days) | `high` |
| Standard deadline (within 2 weeks) | `medium` |
| Distant deadline or backlog | `low` |
| Explicit de-prioritization ("when you get a chance", "low priority") | `low` |

---

## Step 8: Daily-note log (handled by PostToolUse hook)

The `PostToolUse` hook appends a tasks-extracted summary line to the daily note after the last `create_note` call completes. Emit telemetry events `task_proposed` (count, accountability_pass_count) and `task_persisted` (count).

---

## Extract mode output

```markdown
---
## Task extraction complete

### Created ([N] tasks)
| # | Task | Owner | Due | Category | Priority | Source |
|---|------|-------|-----|----------|----------|--------|
| 1 | Review hiring plan | You | 2026-03-25 | Active | High | [[2026-03-21 Platform Review]] |
| 2 | Share migration report | Bob Chen | 2026-03-24 | Delegated | Medium | [[2026-03-21 Platform Review]] |

### Duplicates skipped
| Task | Reason |
|------|--------|
| Review hiring plan | Already exists as open task from 2026-03-18 |

### Filtered out
| Item | Reason |
|------|--------|
| "We should think about Q4" | No owner, not concrete |
| "The team needs to align" | No specific owner |

### User skipped
| Item | Reason |
|------|--------|
| Schedule vendor demo | User excluded from selection |
```

---

---

# MANAGE MODE

Review, complete, reprioritize, and prune existing tasks.

---

## Step 1: Load task state

Query all open tasks from the vault:

```
mcp__tars_vault__search_by_tag(
  tag="tars/task",
  frontmatter={"tars-status": "open"},
  limit=100
)
```

For each task found, read its properties to build the full task state.

### Categorize tasks

Group by `tars-category`:
- **Active**: Owner is user, has due date
- **Delegated**: Owner is someone else, has due date
- **Backlog**: No due date

Within each group, sort by:
1. Overdue tasks first (due date < today)
2. Then by due date ascending
3. Then by priority (high > medium > low)

---

## Step 2: Present current state

```markdown
## Current task state

### Overdue ([N] tasks)
| # | Task | Owner | Due | Days overdue | Priority | Source |
|---|------|-------|-----|-------------|----------|--------|
| 1 | Review hiring plan | You | 2026-03-18 | 3 | High | [[2026-03-15 Team Sync]] |

### Active ([N] tasks)
| # | Task | Owner | Due | Priority | Source |
|---|------|-------|-----|----------|--------|
| 2 | Draft budget proposal | You | 2026-03-25 | High | [[2026-03-21 Platform Review]] |
| 3 | Update API docs | You | 2026-03-28 | Medium | Direct |

### Delegated ([N] tasks)
| # | Task | Owner | Due | Priority | Source |
|---|------|-------|-----|----------|--------|
| 4 | Share migration report | Bob Chen | 2026-03-24 | Medium | [[2026-03-21 Platform Review]] |

### Backlog ([N] tasks, [M] stale)
| # | Task | Owner | Age | Priority | Source |
|---|------|-------|-----|----------|--------|
| 5 | Evaluate new vendor | You | 45 days | Low | Direct |
| 6 | Research competitors | You | 102 days | Low | [[2025-12-10 Strategy]] |
```

Flag tasks older than 90 days as stale. Flag overdue tasks prominently.

---

## Step 3: Handle user actions

### Complete a task

Triggered by: "mark 1 as done", "complete [task name]", "done with [task]"

**Always confirm before completing:**
```
Mark "Review hiring plan" as done? [Y/N]
```

After confirmation:
```
mcp__tars_vault__update_frontmatter(file="Review hiring plan", property="tars-status",       value="done")
mcp__tars_vault__update_frontmatter(file="Review hiring plan", property="tars-completed",    value="YYYY-MM-DD")
mcp__tars_vault__update_frontmatter(file="Review hiring plan", property="tars-completed-by", value="[[User Name]]")
```
The PostToolUse hook writes the daily-note "task completed" line. Emit telemetry `task_completed`.

### Reprioritize a task

Triggered by: "move 5 to active", "set due date on 6", "make 3 high priority"

```
mcp__tars_vault__update_frontmatter(file="Task Title", property="tars-priority", value="high")
mcp__tars_vault__update_frontmatter(file="Task Title", property="tars-due",      value="YYYY-MM-DD")
mcp__tars_vault__update_frontmatter(file="Task Title", property="tars-category", value="active")
mcp__tars_vault__update_frontmatter(file="Task Title", property="tars-modified", value="YYYY-MM-DD")
```

### Bulk operations

Users can act on multiple tasks:
- "complete 1, 3, 5" -- mark multiple as done (confirm each)
- "move 5, 6 to active with due date next Friday" -- bulk reprioritize
- "deprioritize 2, 4 to backlog" -- bulk move to backlog

---

## Step 4: Prune stale tasks

Triggered by: "prune backlog", "clean up tasks", or proactively during task review when stale items exist.

### Identify stale tasks

Tasks are stale when:
- `tars-category` is `backlog` AND age > 90 days
- `tars-status` is `open` AND `tars-due` is more than 30 days overdue
- `tars-category` is `delegated` AND `tars-due` is more than 14 days overdue

### Present pruning recommendations

```
Stale task review:

  1. [102 days] "Research competitors" (backlog, low)
     Recommendation: Archive or delete
  2. [95 days] "Evaluate new vendor" (backlog, low)
     Recommendation: Set due date or archive
  3. [32 days overdue] "Follow up with vendor" (delegated, medium)
     Recommendation: Re-delegate or complete

Actions:
  - "archive 1" to mark archived
  - "delete 1" to remove
  - "keep 2, set due next Friday" to revive with deadline
  - "re-delegate 3 to [name]" to reassign
  - "skip" to leave all as-is
```

### Archive a task

```
mcp__tars_vault__archive_note(file="Task Title")
```
The server adds `tars/archived` tag, sets `tars-status: archived`, updates `tars-modified`, and moves to `archive/tasks/YYYY-MM/` only if guardrails pass (no backlinks in last 90d, no active-task references). If blocked, surface the reason to the user.

NEVER delete tasks without explicit user instruction. Default to archiving.

---

## Step 5: Opportunistic duplicate detection

While displaying tasks in manage mode, scan for potential duplicates:

```
# Look for tasks with similar titles
mcp__tars_vault__search_by_tag(tag="tars/task", query="<keywords from each task>", limit=5)
```

Flag when found:
```
Note: Tasks #2 and #7 may be duplicates:
  - #2: "Draft budget proposal" (active, due 2026-03-25)
  - #7: "Write budget document" (backlog, no due date)
Merge into one? [Keep #2 / Keep #7 / Keep both]
```

Suggest consolidation but let the user decide.

---

## Manage mode output

```markdown
---
## Task management update

### Completed
| Task | Owner | Was due | Completed |
|------|-------|---------|-----------|
| Review hiring plan | You | 2026-03-18 | 2026-03-21 |

### Reprioritized
| Task | From | To | Change |
|------|------|----|--------|
| Evaluate vendor | Backlog | Active | Due date set: 2026-03-28 |

### Archived
| Task | Age | Reason |
|------|-----|--------|
| Research competitors | 102 days | Stale backlog item |

### Current summary
- Active: [N] tasks ([M] overdue)
- Delegated: [N] tasks ([M] overdue)
- Backlog: [N] tasks ([M] stale >90 days)
- Total open: [N]
```

---

---

# Shared protocols

These apply to both extract and manage modes.

## Wikilink mandate

All entity references in task properties and body content must use `[[Entity Name]]` wikilink syntax. The MCP server runs the auto-wikilink pass (§3.3) before write; ambiguous names are returned for batched review. Explicit verification when drafting a wikilink to an entity:

```
mcp__tars_vault__search_by_tag(tag="tars/<type>", query="<entity>", limit=1)
```

If the entity does not exist, write the name as plain text and note it as unverified. Do not fabricate wikilinks to nonexistent notes.

## Context budget

| Resource | Budget |
|----------|--------|
| Alias registry | Full read (Step 1 of either mode) |
| Task search | Up to 3 queries for duplicate checking |
| Vault search | Up to 5 queries for entity verification |
| Memory reads | Up to 5 targeted reads for owner resolution |

## Absolute constraints

1. NEVER create tasks without the numbered review list and user confirmation
2. NEVER mark tasks as done without user confirmation
3. NEVER delete tasks without explicit user instruction. Archive instead.
4. NEVER create tasks for "Team" or "We" without a specific lead identified
5. NEVER use relative dates in output. Always resolve to YYYY-MM-DD.
6. NEVER skip the accountability test, even for items explicitly labeled "Action item"
7. NEVER skip duplicate checking before creation
8. ALWAYS apply canonical names from the alias registry to all owners and references
9. ALWAYS log task operations to the daily note
10. ALWAYS preserve `tars-source` when editing tasks
