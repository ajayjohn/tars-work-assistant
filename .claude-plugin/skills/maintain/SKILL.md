---
name: maintain
description: Workspace maintenance with health checks, index rebuilding, task sync, memory gap detection, and archival
user-invocable: true
---

# Maintain skill: health, sync, rebuild, and inbox

Comprehensive workspace maintenance with four distinct modes: running health checks, syncing tasks and detecting gaps, rebuilding all index files, and batch-processing inbox items with parallel sub-agents.

---

## Automatic vs user-initiated operations

### Automatic (daily, session-start triggered)

These operations run silently at the start of the first session each day via the core skill's session-start housekeeping check. They require no user interaction and produce no output unless critical issues are found.

| Operation | Script | What it does | Failure behavior |
|-----------|--------|-------------|-----------------|
| Archival sweep | `scripts/archive.py --auto` | Expire ephemeral lines past their `[expires:]` date, check staleness thresholds, move qualifying files to `archive/` | Log failure, continue session |
| Health check | `scripts/health-check.py` | Validate indexes vs files on disk, check for broken wikilinks, flag naming violations | Log failure, continue session |
| Task sync | `scripts/sync.py` | Check `reference/schedule.md` for due recurring/one-time items, scan for orphan tasks | Log failure, continue session |
| Inbox count | (directory listing) | Count files in `inbox/pending/` and update `.housekeeping-state.yaml` | Non-critical, skip on error |

**Triggering:** The core skill reads `reference/.housekeeping-state.yaml` at session start. If `last_run` is not today, it runs the above scripts in sequence, updates the state file, and proceeds to the user's request.

### User-initiated (explicit command only)

These operations are more expensive, require user judgment, or have side-effects that need confirmation. They are invoked via `/maintain <mode>` or natural language ("rebuild indexes", "process inbox", "deep sync").

| Operation | Command | Why not automatic |
|-----------|---------|------------------|
| Full index rebuild | `/maintain rebuild` | Rewrites all `_index.md` files. Expensive for large workspaces. Only needed when indexes are known to be stale or corrupted. |
| Inbox processing | `/maintain inbox` | Spawns sub-agents that create tasks and memory entries. Requires user to review and confirm the processing plan before execution. |
| Comprehensive sync | `/maintain sync --comprehensive` | Queries MCP sources (project tracker, calendar), scans last 90 days of journal. Higher cost. Surfaces items that need user triage. |
| Unarchive content | (manual) | Requires user to select specific archived files to restore. No bulk unarchive. |
| Manual health fixes | `/maintain health` | Script-detected issues that require human judgment (file renames, broken wikilink resolution, frontmatter corrections). |

### Cowork scheduled shortcut

If the user's environment supports Cowork shortcuts with schedules, a `daily-housekeeping` shortcut can run maintenance on a cron schedule (e.g., 8 AM daily) instead of relying on session-start detection. This is the preferred approach when available, as it runs even on days the user doesn't start a session. See the shortcut definition in the plugin's shortcut registry.

The session-start check in the core skill serves as a fallback: if the scheduled shortcut already ran today, `last_run` will be current and the session-start check will be a no-op.

---

## Health mode

Scan for workspace issues, auto-fix where safe, and report problems requiring manual intervention.

### Step 1: Load workspace state

Read the following indexes:
- `memory/_index.md` (master memory index)
- `memory/decisions/_index.md`
- `memory/people/_index.md`
- `memory/initiatives/_index.md`
- `contexts/products/_index.md` (if exists)
- `reference/replacements.md`

### Step 2: Naming pattern validation

#### Decision files

Scan `memory/decisions/` for naming violations:

**Standard pattern:** `YYYY-MM-DD-{slug}.md`

| Violation | Example | Suggested fix |
|-----------|---------|---------------|
| Missing date prefix | `ba-role-definition.md` | Extract date from frontmatter, rename |
| Context-first | `ai-strategy-2026-01-20.md` | Reorder to `2026-01-20-ai-strategy.md` |
| No date anywhere | `legacy-decision.md` | Check frontmatter `date` field, rename |

**Auto-fix (safe):** If frontmatter contains `date` field, suggest rename command.

### Step 3: Frontmatter validation

Scan all memory files for required fields:

| Type | Required fields |
|------|-----------------|
| All memory | `title`, `type`, `summary`, `updated` |
| person | + `tags`, `aliases` |
| decision | + `status`, `decision_maker` |
| product-spec | + `status`, `owner` |

#### Status value validation

For decisions, verify `status` is one of: `proposed`, `decided`, `implemented`, `superseded`, `rejected`

For products/product-specs, verify `status` is one of: `active`, `planned`, `deprecated`

Report invalid values.

### Step 4: Index synchronization

#### Check for orphaned entries

For each category index:
1. List entries in `_index.md`
2. List actual `.md` files in folder
3. Flag entries in index that don't have corresponding files
4. Flag files that aren't in the index

#### Check for stale summaries

For each file in memory:
1. Compare file `updated` date with index entry
2. Flag if file was modified more recently than index was regenerated

**Auto-fix (safe):** Run `/rebuild-index` to resync all indexes.

### Step 5: Broken wikilink detection

Scan all files in `memory/`, `journal/`, and `contexts/` for wikilinks:

Pattern: `[[Entity Name]]`

For each wikilink:
1. Check if entity exists in `memory/people/_index.md`
2. Check if entity exists in `memory/initiatives/_index.md`
3. Check if entity exists in `memory/products/_index.md`
4. Check if entity exists in `memory/decisions/_index.md`

Flag broken wikilinks (reference to non-existent entity).

### Step 6: Replacements coverage

Scan all journal files from the last 30 days for names:

1. Extract all capitalized multi-word names (potential person names)
2. Extract all acronyms (2-4 capital letters)
3. Cross-reference against `reference/replacements.md`

Flag names/acronyms that appear multiple times but aren't in replacements.

**Auto-fix (safe):** Add flagged items to `reference/replacements.md` with placeholder:
```markdown
| NewName | ?? (needs canonical form) |
```

### Step 7: Information redundancy check

#### Duplicate detection

Scan for potential duplicates:
1. Same entity name in different folders (e.g., person also exists as initiative)
2. Very similar file names in same folder (edit distance < 3)
3. Same `aliases` values across different files

#### Cross-reference check

For each person in `memory/people/`:
1. Check if they're referenced in any task (via task integration notes)
2. Check if they're referenced in any journal entry
3. Flag people with zero references in last 90 days as potentially stale

### Health mode output

Generate report in this format:

```markdown
## Housekeeping report (YYYY-MM-DD)

### Issues found

| Category | File | Issue | Suggested fix |
|----------|------|-------|---------------|
| naming | decisions/ba-role-definition.md | Missing date prefix | Rename to 2026-01-15-ba-role-definition.md |
| frontmatter | contexts/products/dbi.md | Missing frontmatter | Add standard product-spec template |
| frontmatter | memory/decisions/old.md | Invalid status "pending" | Change to "proposed" |
| index | memory/people/_index.md | Orphan entry "Jane Doe" | Entry has no file, remove from index |
| index | memory/initiatives/new-project.md | Not in index | Add to initiatives/_index.md |
| wikilink | journal/2026-01/meeting.md | Broken link [[Unknown Person]] | Create memory entry or fix reference |
| replacements | journal/ | "JT" appears 5 times | Add to reference/replacements.md |

### Auto-fixed

- Added 2 unknown names to reference/replacements.md with placeholders
- (List other auto-fixes)

### Manual action required

- 5 files need frontmatter review (see table above)
- 2 broken wikilinks need resolution
- 3 decision files need renaming

### Recommendations

- Run `/rebuild-index` to regenerate all indexes
- Review stale memory entries (not referenced in 90+ days)
- Complete placeholder entries in reference/replacements.md
```

---

## Sync mode

Sync tasks from integration, detect memory gaps, and triage stale items. Optional flag: `--comprehensive` for deep scan mode.

### Step 1: Load current state

Query task integration (read `reference/integrations.md` Tasks section for provider details):
- Execute `list` operation for all configured lists (default: Active, Delegated, Backlog)
- Execute `overdue` operation

Read:
- `memory/people/_index.md`
- `memory/initiatives/_index.md`

### Step 1.5: Check scheduled items and memory gaps

Run the automated sync script:

```bash
python3 scripts/sync.py {workspace_path}
```

This script checks `reference/schedule.md` for due items (recurring and one-time) and scans recent journal entries for memory gaps (people and initiatives referenced but not in memory). Parse the JSON output:

- `schedule.recurring_due`: Recurring items past their next-due date. After completion, advance `next-due` to the next occurrence in schedule.md.
- `schedule.onetime_due`: One-time items past their due date. After completion, remove the entry from schedule.md.
- `memory_gaps.unknown_people`: People referenced in journal but not in memory/people/. Present to user.
- `memory_gaps.unknown_initiatives`: Initiatives referenced but not in memory/initiatives/. Present to user.

Surface due items in the report under "Scheduled items." Merge memory gaps with Step 4 output.

If `scripts/sync.py` is not available, fall back to manual schedule checking:
Read `reference/schedule.md` if it exists. For each entry:
- **[RECURRING]**: Check if `next-due` is today or past. If due, add to triage output as "Scheduled item due."
- **[ONCE]**: Check if `due` is today or past. If due, surface it.

### Step 2: Sync from project tracker (if available)

If project tracker integration is configured:
1. Query for items assigned to user that are not in Active/Delegated tasks
2. Query for items recently completed that are still open as tasks
3. Present deltas: "Found {N} new items in project tracker not in your tasks. Add them?"
4. If accepted, create tasks via the task integration `add` operation in the appropriate list

### Step 3: Triage

Scan all reminders/tasks and flag:

| Condition | Flag |
|-----------|------|
| Past due date (from task integration `overdue` operation) | OVERDUE |
| Created >30 days ago without update (from notes field) | STALE |
| No initiative in notes field | ORPHAN |
| Owner in notes not in memory/people/ | UNKNOWN OWNER |

Present flagged items grouped by category. For each:
- OVERDUE: "Update due date, complete, or remove?"
- STALE: "Still relevant? Update, move to backlog, or remove?"
- ORPHAN: "Link to an initiative or keep as standalone?"
- UNKNOWN OWNER: "Add this person to memory?"

### Step 4: Memory gap detection

Decode all entities referenced in tasks:

1. **People**: Extract all owner names and mentioned people from notes fields. Cross-reference against `memory/people/_index.md`. List undefined people.
2. **Initiatives**: Extract all `[[Initiative]]` references from notes fields. Cross-reference against `memory/initiatives/_index.md`. List undefined initiatives.
3. **Terms**: Scan task titles for capitalized terms, acronyms, and project names not in `reference/replacements.md` or memory indexes. List undefined terms.

Present gaps:
```
## Memory gaps detected

### Undefined people (referenced in tasks but not in memory)
- "Sarah Chen" (owner of 3 tasks) -- Create memory entry?
- "Mike R." (mentioned in 1 task) -- Add to replacements?

### Undefined initiatives
- "Project Phoenix" (linked to 2 tasks) -- Create initiative entry?

### Undefined terms
- "RBAC" (used in 2 task descriptions) -- Add to replacements?
```

For each gap, ask user to provide brief context, then create the memory entry or replacement.

### Sync mode output (default)

```markdown
## Update complete

| Category | Count |
|----------|-------|
| Tasks synced from project tracker | N |
| Overdue tasks flagged | N |
| Stale tasks flagged | N |
| Orphan tasks flagged | N |
| Memory gaps found | N |
| Memory entries created | N |
| Replacements added | N |
```

### Comprehensive mode (`--comprehensive`)

All of default mode, PLUS:

#### Step 5: MCP source scan

If project tracker is configured:
- Query recent items (last 14 days) for action items not captured
- Surface items assigned to user's team members

Query the calendar integration for last 7 days of meetings (see `reference/integrations.md` Calendar section):
- Resolve the start date (7 days ago) to `YYYY-MM-DD` format, execute `list_events` operation with offset=7
- Cross-reference against journal entries
- Flag meetings that occurred but have no journal entry: "You had '{Meeting Title}' on {date} but no meeting notes. Process it?"

If calendar integration is not reachable, skip calendar scan and note the gap.

#### Step 6: Stale memory cleanup

Scan memory for staleness:
- Initiatives tagged `completed` that still have open reminders -> flag
- People not referenced in any reminder or journal entry in last 90 days -> flag for review
- Decisions older than 6 months -> flag for relevance check

Present:
```
## Stale memory candidates

- memory/initiatives/old-project.md -- Tagged completed, 2 open tasks reference it
- memory/people/former-vendor.md -- Not referenced in 90+ days
- memory/decisions/q3-decision.md -- 6+ months old, verify still relevant
```

#### Step 7: Entity discovery

From MCP sources scanned in Step 5:
- Surface new people names not in memory
- Surface new project/initiative names not in memory
- Offer to create entries

#### Comprehensive report

Append to default report:

```markdown
### Comprehensive scan results
| Category | Count |
|----------|-------|
| Unprocessed meetings found | N |
| New entities from MCP sources | N |
| Stale memory candidates | N |
```

---

## Rebuild mode

Regenerate all _index.md files from current file contents and frontmatter.

### Step 1: Memory indexes

For each category in `memory/` (people, initiatives, decisions, products, vendors, competitors, organizational-context):

1. Scan all `.md` files in the folder (excluding `_index.md` and `_template.md`)
2. Read frontmatter from each file: `title`, `aliases`, `tags`, `summary`, `updated`
3. Generate `_index.md` with format:

```markdown
# [Category] index

| Name | Aliases | File | Summary | Updated |
|------|---------|------|---------|---------|
| Entity Name | alias1, alias2 | filename.md | One-line summary | YYYY-MM-DD |
```

For initiatives, separate into Active and Completed sections based on tags.

### Step 2: Master memory index

Generate `memory/_index.md`:

```markdown
# Memory index

| Category | Path | Count |
|----------|------|-------|
| People | memory/people/ | N |
| Initiatives | memory/initiatives/ | N |
| Decisions | memory/decisions/ | N |
| Products | memory/products/ | N |
| Vendors | memory/vendors/ | N |
| Competitors | memory/competitors/ | N |
| Organizational context | memory/organizational-context/ | N |
```

### Step 3: Journal indexes

For each month folder in `journal/`:

1. Scan all `.md` files (excluding `_index.md`)
2. Read frontmatter: `date`, `type`, `title`, `participants`, `initiatives`
3. Generate `journal/YYYY-MM/_index.md`:

```markdown
# [Month Year] journal index

| Date | Type | Title | Participants | Initiatives |
|------|------|-------|-------------|-------------|
| YYYY-MM-DD | meeting | Title | Names | Initiatives |
```

### Step 4: Contexts/products index

Scan `contexts/products/` for product specification files:

1. Scan all `.md` files in the folder (excluding `_index.md`)
2. Read frontmatter: `title`, `type`, `status`, `owner`, `summary`, `updated`
3. Generate `contexts/products/_index.md`:

```markdown
# Product specifications index

| Name | Status | Owner | Summary | Updated |
|------|--------|-------|---------|---------|
| Product Name | active | [[Owner Name]] | One-line summary | YYYY-MM-DD |
```

### Step 5: Decision file validation

For files in `memory/decisions/`:

1. Check naming convention: should be `YYYY-MM-DD-{slug}.md`
2. Flag files that don't match the pattern:
   - Missing date prefix
   - Non-standard date format
   - Context-first naming (e.g., `topic-YYYY-MM-DD.md`)
3. Report suggested renames

### Step 6: Annual rollup (if applicable)

For completed years, generate `journal/YYYY-annual-index.md` consolidating all month indexes.

### Rebuild mode output

Report what was regenerated and any issues found:

```markdown
## Rebuild complete

### Indexes regenerated
| Area | Count |
|------|-------|
| Memory categories | N |
| Journal months | N |
| Contexts/products | N |

### Issues found
| Type | File | Issue | Suggested fix |
|------|------|-------|---------------|
| missing-frontmatter | path/file.md | No frontmatter | Add required fields |
| naming-violation | decisions/file.md | Missing date prefix | Rename to YYYY-MM-DD-slug.md |
| missing-required | path/file.md | Missing `summary` field | Add summary for index |
```

### Script invocation

Run the automated rebuild script for deterministic index generation:

```bash
python3 scripts/rebuild-indexes.py {workspace_path}
```

This script performs Steps 1-5 deterministically (memory indexes, master index, journal indexes, contexts index, decision naming validation). Parse the JSON output and use it to populate the rebuild report.

#### Interpreting script output

The script returns JSON with:
- `stats`: counts of memory categories, journal months, context products, and total entries rebuilt
- `issues`: array of problems found (missing-frontmatter, naming-violation, missing-required fields)
- `total_issues`: count of all issues

Present the `stats` as the "Indexes regenerated" table. Present `issues` as the "Issues found" table. The script handles all file I/O — do not duplicate its work by manually reading and rewriting index files.

#### When to skip the script

If `scripts/rebuild-indexes.py` is not available (e.g., workspace predates script extraction), fall back to the manual procedure above.

### Post-execution checklist
- [ ] All memory category indexes regenerated
- [ ] Master memory index regenerated
- [ ] All journal month indexes regenerated
- [ ] Contexts/products index regenerated
- [ ] Decision naming validated
- [ ] Any missing frontmatter flagged to user
- [ ] Suggested fixes presented

---

## Inbox mode

Batch-process all pending items in the inbox using **isolated parallel sub-agents**. Each item is processed by an independent sub-agent with its own context, ensuring no cross-contamination between items.

### Step 1: Scan inbox

List all files in `inbox/pending/`. For each file:
1. Read the first 50 lines to determine content type
2. Classify as one of: `transcript`, `article`, `email`, `notes`, `unknown`
3. Build processing queue with file path, detected type, and file size

If no pending items, report "Inbox is empty" and exit.

### Step 2: Present processing plan

Before spawning sub-agents, present the plan to the user:

```markdown
## Inbox processing plan

| # | File | Detected type | Proposed action |
|---|------|---------------|-----------------|
| 1 | meeting-2026-02-05.txt | transcript | Process as meeting (tasks + memory) |
| 2 | article-ai-strategy.md | article | Extract wisdom |
| 3 | notes-from-call.txt | notes | Extract tasks + memory |
| 4 | unknown-file.txt | unknown | Skip (manual review needed) |

Process all items? (Confirm before proceeding)
```

Wait for user confirmation before spawning sub-agents. Allow the user to exclude specific items or change detected types.

### Step 3: Parallel sub-agent processing

After user confirmation, spawn **one sub-agent per inbox item** using the Task tool. **Launch all sub-agents in a single message** for maximum parallelism.

For each item, move the file from `inbox/pending/` to `inbox/processing/` before spawning the sub-agent.

##### Sub-agent template by content type

**Transcript items:**
```
You are processing a meeting transcript from the inbox.

Move file from: inbox/processing/{filename}
Read the transcript file.
Read reference/replacements.md and apply canonical names.
Read reference/integrations.md for calendar and task integration details.

Execute the meeting processing pipeline:
1. Process transcript and generate structured report
2. Save to journal/YYYY-MM/YYYY-MM-DD-{slug}.md
3. Extract tasks and create via task integration
4. Extract memory and update knowledge graph

After completion, move the source file to inbox/completed/{filename}.

Return JSON:
{
  "status": "ok" | "error",
  "source_file": "{filename}",
  "content_type": "transcript",
  "journal_path": "journal/YYYY-MM/...",
  "tasks_created": 0,
  "memory_updates": 0,
  "errors": []
}
```

**Article/wisdom items:**
```
You are extracting wisdom from an article in the inbox.

Read the article file at: inbox/processing/{filename}
Read reference/replacements.md and apply canonical names.

Execute the wisdom extraction pipeline:
1. Identify key insights, frameworks, and actionable takeaways
2. Apply durability test to each insight
3. Persist durable insights to appropriate memory locations
4. Save extraction report to journal/YYYY-MM/YYYY-MM-DD-wisdom-{slug}.md
5. Extract any tasks or action items

After completion, move the source file to inbox/completed/{filename}.

Return JSON:
{
  "status": "ok" | "error",
  "source_file": "{filename}",
  "content_type": "article",
  "journal_path": "journal/YYYY-MM/...",
  "insights_persisted": 0,
  "tasks_created": 0,
  "errors": []
}
```

**Notes items:**
```
You are processing notes from the inbox.

Read the notes file at: inbox/processing/{filename}
Read reference/replacements.md and apply canonical names.
Read reference/integrations.md Tasks section for task creation.

Execute:
1. Extract tasks (apply accountability test, check duplicates, create via task integration)
2. Extract durable memory (apply durability test, persist to memory/)
3. Save summary to journal/YYYY-MM/YYYY-MM-DD-notes-{slug}.md

After completion, move the source file to inbox/completed/{filename}.

Return JSON:
{
  "status": "ok" | "error",
  "source_file": "{filename}",
  "content_type": "notes",
  "journal_path": "journal/YYYY-MM/...",
  "tasks_created": 0,
  "memory_updates": 0,
  "errors": []
}
```

### Step 4: Collect results and handle failures

After all sub-agents complete:
1. Collect JSON results from each sub-agent
2. For any sub-agent that failed, move its file from `inbox/processing/` to `inbox/failed/` and create a companion `.error` file with the error details
3. Generate consolidated report

### Sub-agent input/output contracts (inbox mode)

| Content type | Input | Output | Failure mode |
|-------------|-------|--------|-------------|
| Transcript | Source file, replacements.md, integrations.md | JSON: journal path, tasks created, memory updates | Move to inbox/failed/, create .error file |
| Article | Source file, replacements.md | JSON: journal path, insights persisted, tasks created | Move to inbox/failed/, create .error file |
| Notes | Source file, replacements.md, integrations.md | JSON: journal path, tasks created, memory updates | Move to inbox/failed/, create .error file |

**Shared constraints for all inbox sub-agents:**
- Each sub-agent operates with fully isolated context
- Each sub-agent reads its own copy of reference files (no shared state)
- Memory writes must use `.lock` files (see core skill cowork protocol)
- Task creation checks for duplicates independently per sub-agent
- If a sub-agent fails, other sub-agents continue unaffected

### Inbox mode output

```markdown
## Inbox processing complete

### Processed items
| # | File | Type | Journal | Tasks | Memory | Status |
|---|------|------|---------|-------|--------|--------|
| 1 | meeting-2026-02-05.txt | transcript | journal/2026-02/... | 3 | 2 | ok |
| 2 | article-ai-strategy.md | article | journal/2026-02/... | 1 | 4 | ok |
| 3 | notes-from-call.txt | notes | journal/2026-02/... | 2 | 1 | ok |

### Failed items
| File | Error |
|------|-------|
| (none) | |

### Summary
- Items processed: N
- Items failed: N
- Tasks created: N (total across all items)
- Memory updates: N (total across all items)
- Journal entries created: N
```

### Progress tracking (TodoWrite) for inbox mode

```
1. Scan inbox and classify items                   [in_progress → completed]
2. Present processing plan for approval            [pending → completed]
3. Process item: {filename1} (parallel)            [pending → completed]
4. Process item: {filename2} (parallel)            [pending → completed]
5. Process item: {filename3} (parallel)            [pending → completed]
6. Collect results and generate report             [pending → completed]
```

Mark all item-processing todos as `in_progress` simultaneously when spawning sub-agents. Mark each `completed` as its sub-agent returns.

---

## Script invocation for health mode

Before performing manual checks, run the automated scripts for deterministic validation:

### Step 0: Run health-check.py

```bash
python3 scripts/health-check.py {workspace_path}
```

This script performs Steps 2-6 deterministically (naming validation, frontmatter checks, index sync, wikilink detection, replacements coverage). Parse the JSON output and use it to populate the issues table in the report. Only manually investigate items the script cannot assess (Step 7: information redundancy, cross-reference depth).

### Step 0b: Run archive.py (optional)

```bash
python3 scripts/archive.py {workspace_path}
```

or for preview only:

```bash
python3 scripts/archive.py {workspace_path} --dry-run
```

This script scans memory files for staleness and archives expired content. Run with `--dry-run` first to preview, then confirm with the user before running without the flag. Parse the JSON output and include archived file counts in the report.

### Interpreting script output

The scripts return JSON. Key fields:
- `health-check.py`: `issues` array (each with category, file, issue, suggested_fix), `auto_fixes` array, `summary` stats
- `archive.py`: `files_archived`, `expired_lines_removed`, `archived_files` array with paths and reasons

Present the findings using the output format above. For auto-fixes, apply them and note what was done. For manual-fix items, present to the user for confirmation.

---

## Context budget

**Health mode:**
- Memory indexes: Read all `_index.md` files
- Memory files: Scan frontmatter only (not full content) unless checking wikilinks
- Journal: Scan last 30 days of entries
- Reference: Read `replacements.md`

**Sync mode:**
- Task integration: Up to 3 queries per list
- Memory indexes: Read people and initiatives indexes
- Schedule: Read `reference/schedule.md` if exists
- Project tracker: Up to 3 queries per team
- Calendar: Last 7 days of events (comprehensive mode)
- Journal: Scan last 90 days for staleness and entity discovery (comprehensive mode)

**Rebuild mode:**
- Memory: Scan all files in all categories
- Journal: Scan all month folders
- Contexts: Scan products folder (if exists)
- Reference: None required

**Inbox mode:**
- Main agent: Read `inbox/pending/` file list + first 50 lines of each file for classification
- Each sub-agent: Read its assigned source file + `reference/replacements.md` + `reference/integrations.md` + relevant memory indexes
- Sub-agents have isolated context; budget is per-item, not cumulative

---

## Absolute constraints

**Health mode:**
- NEVER delete files (only suggest deletions with user confirmation)
- NEVER modify content (only metadata like replacements)
- NEVER change wikilink targets without user approval
- **Auto-fix safety:** Only add to replacements, only suggest renames (don't execute)

**Sync mode:**
- NEVER create tasks without user approval
- NEVER fabricate data from missing integrations (report gaps)
- NEVER modify tasks without user confirmation
- ALWAYS use provider-agnostic language (no hardcoded Jira/Asana terminology)
- NEVER skip memory gap detection

**Rebuild mode:**
- NEVER modify file content (only regenerate indexes)
- NEVER delete files
- ALWAYS validate decision naming patterns
- ALWAYS report missing frontmatter
- NEVER skip any category

**Inbox mode:**
- NEVER process items without user confirmation of the processing plan
- NEVER delete source files (move to completed/ or failed/, never remove)
- ALWAYS create .error companion files for failed items
- ALWAYS use `.lock` files for memory writes from parallel sub-agents
- NEVER spawn sub-agents for items classified as `unknown` (require manual review)
- ALWAYS move files to `inbox/processing/` before spawning sub-agents (prevents double-processing)

---

## Documentation note

When building future functionality, consider whether the housekeeping script should be updated to include relevant validation elements.
