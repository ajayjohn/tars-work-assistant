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
  - "worktrees"
  - "list worktrees"
help:
  purpose: |-
    Vault maintenance scoped to ingest-adjacent workflows: inbox processing, calendar/task sync,
    archive sweep, worktree hygiene, and pending vault migrations. Hygiene checks (broken links,
    orphans, schema violations, staleness, contradictions, framework state drift) moved to
    `/lint` in v3.1.
  use_cases:
    - "Process my inbox"
    - "Sync tasks and calendar"
    - "Check for gaps"
    - "Archive stale notes"
    - "Run maintenance"
    - "List worktrees"
    - "Merge / prune worktrees"
    - "Run pending migrations"
  scope: maintenance,inbox,sync,archive,housekeeping,worktrees,migrations
---

# Maintain skill: inbox, sync, and archive

Modes: **inbox** (classify and route pending items), **sync** (drift detection between vault and external systems), **archive** (staleness-based sweep with guardrails), **worktrees** (git worktree hygiene), **migrations** (run pending schema migrations). A "maintenance" trigger runs inbox + sync + archive in sequence.

Hygiene — broken wikilinks, orphans, schema violations, staleness banners, contradictions, framework self-state drift — moved to `/lint` in v3.1. Reference-update mode was retired (v2.1 artifact).

All vault writes go through `mcp__tars_vault__*` tools. External integrations resolve via `mcp__tars_vault__resolve_capability(capability=…)` — never hard-code provider names.

| Mode | Trigger | Purpose |
|------|---------|---------|
| Inbox | "process inbox" | Classify and route pending inbox items (multimodal) |
| Sync | "sync", "check for gaps" | Calendar gaps, task drift, memory freshness |
| Archive | "archive sweep" | Staleness archival with 90d backlink + active-task guardrails |
| Worktrees | "list worktrees", `/maintain worktrees` | Discover, merge, and prune git worktrees |
| Migrations | "run migrations", `/maintain migrations` | Apply pending schema/vault-structure migrations |
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
- **Article/link** → `WebFetch` extraction, then `/learn` wisdom mode.
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

### Step 4: Report + telemetry

(Telemetry rollup moved to `/lint` per the v3.1 boundary; the rollup script `scripts/telemetry-rollup.py` is the single source of truth and is consumed by `/briefing` weekly footer + `/maintain --weekly`. Source `.jsonl` retention is 90 days rolling — older files move to `_system/telemetry/archive/YYYY-MM.jsonl.gz` on the weekly maintenance run.)

Emit `sync_completed` with `{calendar_gaps, task_drift, stale_profiles}` counts. PostToolUse hook writes the daily-note summary.

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

## Worktrees mode (`/maintain worktrees`)

Triggered by: "list worktrees", "worktree hygiene", "clean up worktrees", or explicitly `/maintain worktrees`.

When Claude Code runs sessions in isolated git worktrees, stale branches accumulate over time. This mode surfaces them and lets the user merge or prune each one.

### Step 1: Discover worktrees

```bash
git worktree list --porcelain
```

Parse the output into a list of `{path, branch, HEAD}` records. Skip the main worktree (first entry). For each non-main worktree:

- Compute `commits_ahead` vs `main`: `git rev-list --count main..<branch>`
- Check last-commit date: `git log -1 --format="%ci" <branch>`
- Check if any TARS vault files were written in this worktree (look for new/modified `.md` files relative to `main`)

### Step 2: Present inventory

```
Active worktrees (excluding main):
  1. claude/feature-xyz  (3 commits ahead, last activity: 2026-04-28)
     — 2 vault files modified (may need merge review)
  2. claude/old-task     (0 commits ahead, last activity: 2026-03-10)
     — nothing ahead of main; safe to prune

Actions: [merge N] [prune N] [merge all safe] [prune all stale] [skip]
```

A worktree is **safe to prune** when it has 0 commits ahead of main and its last activity is older than 7 days.

### Step 3: Execute user selection

- **Merge N**: run `git merge <branch>` from the main worktree checkout, then offer to run `git worktree remove <path> --force` on success.
- **Prune N**: run `git worktree remove <path> --force` (safe-to-prune only; confirm on others).
- **Prune all stale**: batch-prune all 0-commits-ahead worktrees older than 7 days without additional confirmation.
- After pruning: run `git worktree prune` to clean up stale admin files.

### Step 4: Summary

Report counts: merged, pruned, skipped. Log to `_system/changelog/YYYY-MM-DD.md` if any action was taken.

### Constraints

- NEVER merge without showing the commit delta first.
- NEVER prune a worktree that has commits ahead of main without explicit user confirmation.
- NEVER run destructive git operations (reset, force-push) — merge and worktree-remove only.

---

## Migrations mode (`/maintain migrations`)

Triggered by: "run migrations", "run pending migrations", or as part of `/maintain --realign` (Phase 5).

Applies pending schema and vault-structure migrations that ship with each plugin version. Migrations are idempotent Python scripts in `scripts/migrations/`.

### Step 1: Check pending migrations

```bash
python3 scripts/run-migrations.py --vault $TARS_VAULT_PATH --list
```

This compares `_system/housekeeping-state.yaml.plugin_version` against the available migration scripts and prints pending ones.

### Step 2: Present the list

```
Pending migrations (vault is at v3.1.x; plugin is v3.3.0):
  1. v3.2.0-add-tars-category       — backfill tars-category on 228 task notes
  2. v3.3.0-backfill-journal-aliases — add aliases to 13+ journal files with slug mismatch

Run all? [all / pick specific N,M / dry-run first / skip]
```

Always offer dry-run first. Never apply without user acknowledgement.

### Step 3: Apply

```bash
python3 scripts/run-migrations.py --vault $TARS_VAULT_PATH --apply [--migration v3.2.0-add-tars-category]
```

Each migration writes a results summary. On success, `housekeeping-state.yaml.plugin_version` advances to match the plugin.

### Constraints

- NEVER apply migrations without showing the dry-run diff first.
- Migrations are additive-only — they set missing fields, never delete or rename user content.
- A failed migration leaves a partial results file in `journal/YYYY-MM/migration-<id>-FAILED.md` and does NOT advance the version.

---

## Weekly mode (`/maintain --weekly`)

Triggered by: the `tars-weekly-maintenance` cron job (Sunday 18:00 by default; registered in `/welcome` Step 7) or by an explicit `/maintain --weekly` from the user. Casual-mode installs do NOT register this cron; the mode still works on demand if invoked manually.

Why this exists: Claude does not run in the background, so every periodic feature in TARS (telemetry rollup, backlog grouping, staleness/drift/curator proposals) needs a single trigger that opens a session and produces a persistent surface. The cron-fired session ends without a human present, so the only output is a numbered review file the user reads on their next session.

Pipeline:

1. **Telemetry rollup snapshot.** Run `scripts/telemetry-rollup.py --vault $TARS_VAULT_PATH --days 7 --format json` and capture the output. Save the rendered text version to `_system/changelog/YYYY-MM-DD.md` under a "Weekly telemetry rollup" heading so the changelog has a permanent record.

2. **Backlog auto-grouping.** Read every note under `_system/backlog/issues/` (already created by self-evaluation in /core). Group by `tars-issue-type` and the originating skill. Compute a count per group and the most-recent occurrence. Items with `tars-occurrence-count >= 3` over the last 14 days surface as "skill X is failing repeatedly" entries. Never auto-edits any skill — surfacing only.

3. **Lint review queue.** Invoke `/lint --actions` (Phase 5) — see Step 6.5 of `skills/lint/SKILL.md`. Capture the materialized numbered queue.

4. **User-model + workflow proposals (Phase 6).** Invoke `/learn --review-patterns` (Mode C in `skills/learn/SKILL.md`) with the cron-fired surface flag so the call returns proposals as structured data instead of rendering inline. Append the structured proposals under a "User-model + workflow proposals" section in the review queue. Each row labels its kind (`user-model` field update or `workflow` proposal) plus the evidence count and 14-day window. Pinned fields (`tars-pinned-fields` in user-model, `pinned: true` in workflows) are skipped silently — surface a one-line "N pinned-field matches suppressed" notice if any were filtered.

5. **Curator proposals (Phase 7).** Run three checks; each appends numbered proposals to the weekly review file under "Curator proposals". All checks honor cooling-off windows tracked in `_system/housekeeping-state.yaml`:

   a. **Memory + workflow staleness.** Bash `scripts/archive.py --vault $TARS_VAULT_PATH --json --check all`. From the JSON: `memory.archivable` rows (excluding `protected`) become `memory:<file>` proposals; `workflows.candidates` rows become `workflow:<id>` proposals. `tars-pinned: true` notes and `pinned: true` workflows are filtered by the script — surface a one-line "N pinned items skipped" notice from the `pinned_skipped` summary fields. Track `last_run.archive_check` in housekeeping-state; if last run was less than 7 days ago, skip this check (cooling-off).

   b. **Persona drift.** Only run when (i) `_system/install.yaml.persona` is set, (ii) ≥30 days of telemetry exist, (iii) `last_run.persona_drift_check` is ≥14 days old or unset. Compute the user's 30-day skill-mix signature from `scripts/telemetry-rollup.py --days 30 --format json` (`skills_loaded` map). Compare against each persona template's `tars-briefing-sections` + implied skill mix:
      - `product-leader` → expects `briefing` + `think` + `learn` weighted toward customer-signals/roadmap.
      - `sales-customer-facing` → `briefing` + `meeting` + `tasks` weighted toward accounts/follow-ups.
      - `delivery-pm` → `briefing` + `tasks` + `initiative` weighted toward blockers/RAID.
      - `data-science-lead` → `think` (mode D) + `learn` weighted toward experiments/metrics.
      - `architect-staff-eng` → `think` (mode A) + `learn` weighted toward ADRs/RFCs.
      - `support-ops-lead` → `briefing` + `tasks` weighted toward incidents/SLAs.
      - `engineering-manager` → `meeting` (1:1s) + `briefing` weighted toward team signals.
   If the observed signature matches a different persona by ≥40% margin over the current persona, append a single `persona:<current>→<proposed>` proposal with the supporting evidence (top-3 most-invoked skills, top-3 recurring concerns from user-model). Update `last_run.persona_drift_check` to today regardless of whether a proposal was emitted.

6. **Materialize the weekly review file.** Write everything to `inbox/pending/weekly-review-YYYY-MM-DD.md` via `mcp__tars_vault__write_note_from_content`:

   ```
   ---
   tags: [tars/inbox, tars/weekly-review]
   tars-source: maintain-weekly
   tars-created: YYYY-MM-DD
   tars-status: pending
   tars-window-start: <YYYY-MM-DD>
   tars-window-end:   <YYYY-MM-DD>
   ---

   # Weekly review — YYYY-MM-DD

   ## Telemetry rollup (last 7 days)
   <text from telemetry-rollup.py>

   ## Backlog signals
   <grouped issues with counts>

   ## Lint actions
   <numbered queue from /lint --actions>

   ## User-model + workflow proposals
   <numbered list of proposals from /learn --review-patterns; each labeled
    user-model:<field> or workflow:<id>. Empty section heading retained
    when no proposals so the structure stays predictable for /lint.>

   ## Curator proposals
   <numbered list of proposals from scripts/archive.py + persona-drift
    check; each labeled memory:<file>, workflow:<id>, or
    persona:<from>→<to>. Pinned-skipped count surfaces as a one-line
    notice. Empty section heading retained when no proposals.>

   ## How to act
   - Reply with `auto-fix all`, `auto-fix N,M`, `review each`, or `skip` for the lint queue.
   - Approve or dismiss curator items individually by number.
   - Approving a curator item triggers `mcp__tars_vault__archive_note` (memory),
     a `_system/workflows.yaml` edit (workflow retirement), or
     `update_frontmatter(file="install", updates={"persona": "<new>"})`
     (persona switch). Every action logs to `_system/changelog/YYYY-MM-DD.md`
     with reversibility notes.
   ```

7. **Update housekeeping state.** Set `last_weekly_run: YYYY-MM-DD` so the SessionStart hook can detect when it last ran. Persist per-check `last-run` timestamps for cooling-off windows: `last_run.archive_check` (7d), `last_run.persona_drift_check` (14d), and `last_run.pattern_scan` (any). All live under a new `last_run` block in `_system/housekeeping-state.yaml`; the SessionStart hook reads them when computing the cron-job notice (Phase 4).

8. **Telemetry.** Emit `maintain_weekly_run` with `{rollup_events, backlog_groups, lint_queue_size, curator_memory, curator_workflow, persona_drift_proposed, review_file_path}`.

The cron-fired session ends here. The user reviews `inbox/pending/weekly-review-YYYY-MM-DD.md` on their next interactive session via the existing inbox-surfacing flow in `/maintain inbox`.

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
