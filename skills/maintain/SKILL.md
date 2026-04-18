---
name: maintain
description: Inbox processing, calendar/task sync, archive sweep, and scheduled housekeeping for the TARS vault
user-invocable: true
triggers:
  - "run maintenance"
  - "housekeeping"
  - "process inbox"
  - "check inbox"
  - "sync"
  - "check for gaps"
  - "archive sweep"
help:
  purpose: |-
    Vault maintenance scoped to ingest-adjacent workflows: inbox processing, calendar/task sync,
    and archive sweep. Hygiene checks (broken links, orphans, schema violations, staleness,
    contradictions, framework state drift) moved to `/lint` in v3.1.
  use_cases:
    - "Process my inbox"
    - "Sync tasks and calendar"
    - "Check for gaps"
    - "Archive stale notes"
    - "Run maintenance"
  scope: maintenance,inbox,sync,archive,housekeeping
---

# Maintain skill: inbox, sync, and archive

Three modes: **inbox** (classify and route pending items), **sync** (drift detection between vault and external systems), **archive** (staleness-based sweep with guardrails). A fourth "maintenance" trigger runs all three in sequence.

Hygiene — broken wikilinks, orphans, schema violations, staleness banners, contradictions, framework self-state drift — moved to `/lint` in v3.1. Reference-update mode was retired (v2.1 artifact).

All vault writes go through `mcp__tars_vault__*` tools. External integrations resolve via `mcp__tars_vault__resolve_capability(capability=…)` — never hard-code provider names.

| Mode | Trigger | Purpose |
|------|---------|---------|
| Inbox | "process inbox" | Classify and route pending inbox items (multimodal) |
| Sync | "sync", "check for gaps" | Calendar gaps, task drift, memory freshness |
| Archive | "archive sweep" | Staleness archival with 90d backlink + active-task guardrails |
| Maintenance | "run maintenance", "housekeeping", cron | Archive + sync; inbox only if non-empty |

**Automatic** (SessionStart): if `_system/housekeeping-state.yaml.last_run` is not today, the hook runs `archive --auto` + `sync --light` silently (surface-only; never applies without review). **Cron**: Friday 17:00 local by default (`_system/schedule.md`, registered via CronCreate in `/welcome`).

---

## Inbox processing mode

Triggered by: "process inbox", "check inbox".

Classify and process all pending inbox items. Supports text, transcripts, images, PDFs, and mixed content.

### Step 1: Scan inbox

```
mcp__tars_vault__search_by_tag(tag="tars/inbox", limit=50)
```

Fall back to directory listing of `inbox/pending/` if the search returns empty.

For each file, read the first 50 lines (or full content for images) to determine content type.

### Step 2: Classify each item

| Content type | Detection signals | Processing route |
|-------------|-------------------|-----------------|
| Transcript/meeting notes | Speaker labels, timestamp patterns, "Meeting:", Otter/Fireflies/Teams/Zoom format | `/meeting` pipeline |
| Screenshot/image | .png, .jpg, .jpeg, .gif, .webp | Multimodal analysis + context inference |
| Article/link | URL, "http", article structure, byline | `/learn` wisdom mode |
| PDF/document | .pdf, .docx, .xlsx | Companion file + text extraction |
| Task-like items | Checkbox patterns, "TODO", "Action item" | `/tasks` extract mode |
| Facts/memory items | Declarative statements, "Remember:", "Note:" | `/learn` memory mode |
| Claude-session capture | `tars-source-type: claude-session` frontmatter (dropped by PreCompact / SessionEnd hooks) | Review + route to `/meeting`, `/learn`, or `/tasks` |
| Mixed | Multiple types detected in one file | Split into components |

### Step 3: Present inventory with classification

```
N items in inbox:
  1. ClientCo-sync-notes.txt         — meeting transcript (Otter format)
  2. IMG_2847.png                    — screenshot, Slack message from Sarah about API deadline
  3. api-patterns.pdf                — research paper on API design
  4. quick-notes.md                  — mixed (2 tasks + 3 facts)
  5. claude-session-2026-04-17.md    — Claude session summary (pre-compact capture)

Process all? [all / pick specific / reclassify any]
```

Allow user to override classification, exclude items, or reorder priority.

### Step 4: Process each item

Route each selected item to the appropriate skill. Between items, report progress.

- **Transcript** → invoke `/meeting` pipeline with the file content (steps 2–14).
- **Image** → multimodal read, calendar correlation for timestamp, companion note via `mcp__tars_vault__create_note(template="companion", path="contexts/YYYY-MM/…")` with the §26.13 frontmatter contract, extracted tasks/facts routed through `/tasks` / `/learn`.
- **Article/link** → `defuddle` extraction, then `/learn` wisdom mode.
- **PDF** → text extraction, companion note, filed in `contexts/YYYY-MM/`.
- **Tasks-only** → `/tasks` extract mode (accountability test + numbered review).
- **Facts-only** → `/learn` memory mode (durability test + numbered review).
- **Claude-session** → surface decisions/commitments/questions to user, then route to appropriate skill(s). Never silently persist.

### Step 5: Mark processed

```
mcp__tars_vault__update_frontmatter(file="<inbox-item>", property="tars-inbox-processed", value="YYYY-MM-DD")
mcp__tars_vault__move_note(src="inbox/pending/<file>", dst="inbox/processed/<file>")
```

NEVER delete source files. The subsequent archive-sweep step (§below) moves `inbox/processed/` items older than 7 days to long-term archive.

### Step 6: Summary

Emit `inbox_processed` telemetry. PostToolUse hook writes the daily-note summary.

---

## Sync mode

Triggered by: "sync", "check for gaps".

### Step 1: Calendar gaps

```
cap = mcp__tars_vault__resolve_capability(capability="calendar")
events = cap.tools[list_events-style](start=today-7, end=today)
```

Cross-reference each meeting against journal entries:
1. `mcp__tars_vault__search_by_tag(tag="tars/meeting", frontmatter={"tars-date": "<date>"}, limit=5)`.
2. Match on title or participants.
3. Flag meetings without journal entries as "unprocessed meeting".

Offer the user to route each gap to `/meeting` (if a transcript is available in inbox) or to create a placeholder journal entry.

### Step 2: Task drift

```
cap = mcp__tars_vault__resolve_capability(capability="tasks")
external_tasks = cap.tools[list-style](...)
vault_tasks    = mcp__tars_vault__search_by_tag(tag="tars/task", frontmatter={"tars-status": "open"}, limit=500)
```

Compare and surface:
- **Vault-only**: tasks in vault not in external system.
- **External-only**: tasks in external system not in vault.
- **Status mismatch**: completed in one, open in the other.
- **Date mismatch**: different due dates.

Never auto-resolve. Present each drift for user decision (`/tasks manage` runs the actual update).

### Step 3: Memory freshness

Check people who appeared in recent meetings (last 14 days) but whose memory notes haven't been touched in 30+ days.

```
recent_journals = mcp__tars_vault__search_by_tag(
  tag="tars/meeting",
  frontmatter={"tars-date__gte": "<today-14>"},
  limit=50
)
# Extract participants, check tars-modified on each memory/people/<name>.md
```

Surface for user decision: update profile with recent insights (routes to `/learn`) or accept staleness.

### Step 4: Telemetry rollup

Read today's and the prior 13 days' `_system/telemetry/YYYY-MM-DD.jsonl` files and compute a 14-day per-skill rollup. Persist as a markdown note for `_views/skill-activity.base`:

```
mcp__tars_vault__create_note(
  path="journal/YYYY-MM/skill-activity-rollup.md",
  name="skill-activity-rollup",
  frontmatter={
    "tags": ["tars/telemetry-rollup"],
    "tars-rollup-window": "14d",
    "tars-skill-invocations": {"meeting": N, "answer": N, …},
    "tars-vault-writes": N,
    "tars-memory-accepted": N,
    "tars-tasks-persisted": N,
    "tars-answer-hit-tiers": {"tier1": N, "tier2": N, "tier3": N},
    "tars-lint-findings": {"critical": N, "warnings": N, "auto_fixable": N},
    "tars-created": "YYYY-MM-DD",
    "tars-modified": "YYYY-MM-DD"
  },
  body="<narrative summary of trends>"
)
```

One rollup per month; overwrite in place on each sync. Retention of the source `.jsonl` files is 90 days rolling — older files move to `_system/telemetry/archive/YYYY-MM.jsonl.gz` on the Friday 17:00 maintenance run.

### Step 5: Report + telemetry

Emit `sync_completed` with `{calendar_gaps, task_drift, stale_profiles, rollup_written}` counts. PostToolUse hook writes the daily-note summary.

---

## Archive mode

Triggered by: "archive sweep". Also runs automatically under maintenance (see `--auto` flag used by SessionStart).

### Guardrails (hard constraints)

Every archive candidate must pass BOTH:
1. No backlinks from notes modified in the last 90 days.
2. No references from any open task.

`mcp__tars_vault__archive_note` enforces these server-side — the tool returns `{blocked: true, reason: …}` if either guardrail trips.

### Pipeline

1. Run `scripts/archive.py --vault <TARS_VAULT_PATH> --dry-run --json` to enumerate candidates past staleness thresholds (tiers defined in `_system/schemas.yaml`).
2. For each candidate, call `mcp__tars_vault__archive_note(file=…, dry_run=true)` — collect the guardrail verdicts.
3. Present surviving candidates for user approval:

```
N archive candidates:
  1. memory/people/former-contractor.md    — 180d stale, 0 recent backlinks
  2. memory/decisions/2025-06-old-decision.md — 270d stale, 0 recent backlinks

Archive all / select specific / skip
```

4. For approved items: `mcp__tars_vault__archive_note(file=…)`. The server applies the `tars/archived` tag, moves to `archive/<entity-type>/YYYY-MM/`, and logs.
5. Also sweep `inbox/processed/`: items older than 7 days (by `tars-inbox-processed` date) move to `archive/inbox/YYYY-MM/`. Never deletes originals.

---

## Combined maintenance flow

Triggered by: "run maintenance", "housekeeping", or cron.

1. Check `_system/housekeeping-state.yaml.last_run`. If today and not a manual invocation, ask "Maintenance already ran today. Force re-run?"
2. Run **archive** mode.
3. Run **sync** mode (light — calendar gaps + task drift; skip memory freshness unless comprehensive flag set).
4. If inbox has pending items, prompt: "N items in inbox. Process now? [Y/N]". Do NOT auto-process.
5. Update `_system/housekeeping-state.yaml`:
   ```
   mcp__tars_vault__update_frontmatter(file="housekeeping-state", property="last_run",     value="YYYY-MM-DD")
   mcp__tars_vault__update_frontmatter(file="housekeeping-state", property="last_success", value=true)
   ```
6. Emit `maintenance_run` telemetry. PostToolUse hook writes daily-note summary.

---

## Absolute constraints

### Inbox
- NEVER process items without user confirmation of classification.
- NEVER delete source files (move to `inbox/processed/`).
- NEVER skip multimodal analysis for images.
- ALWAYS route to the owning skill (`/meeting`, `/learn`, `/tasks`) — inbox is classification, not ingestion.
- ALWAYS preserve originals through archive.

### Sync
- NEVER auto-resolve task drift — every mismatch requires user decision.
- NEVER fabricate journal entries for missed meetings (propose placeholder + flag).
- NEVER update memory profiles without showing the diff.
- ALWAYS report gaps even if no action is taken.

### Archive
- NEVER archive notes with backlinks from the last 90 days.
- NEVER archive notes referenced by any open task.
- NEVER delete files — always move via `mcp__tars_vault__archive_note`.
- ALWAYS present candidates for user approval (except `--auto` mode runs under SessionStart, which only surfaces proposals rather than applying them).
- ALWAYS log archivals through the MCP server so the changelog captures the batch.

### Universal
- ALWAYS emit telemetry for every mode run (`inbox_processed`, `sync_completed`, `archive_swept`, `maintenance_run`).
- ALWAYS use `mcp__tars_vault__*` tools for vault writes; PostToolUse hook handles changelog.
- NEVER use direct file I/O for vault content.
