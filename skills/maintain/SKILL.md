---
name: maintain
description: Health check, maintenance, housekeeping, file organization, inbox processing, sync, and reference updates for the TARS vault
user-invocable: true
triggers:
  - "health check"
  - "check vault health"
  - "run maintenance"
  - "housekeeping"
  - "process inbox"
  - "check inbox"
  - "sync"
  - "check for gaps"
  - "update references"
help:
  purpose: |-
    Comprehensive vault maintenance with six distinct modes: health check, scheduled maintenance/housekeeping,
    inbox processing (with multimodal support), sync/gap detection, and reference file updates.
  use_cases:
    - "Run a health check"
    - "Run maintenance"
    - "Process my inbox"
    - "Sync tasks and calendar"
    - "Check for gaps"
    - "Update reference files"
  scope: maintenance,health,sync,housekeeping,inbox,update,organize
---

# Maintain skill: health, housekeeping, inbox, sync, and update

Comprehensive vault maintenance with six modes. Keeps the vault healthy, processes incoming content,
detects drift between systems, and manages scheduled cleanup.

---

## Mode overview

| Mode | Trigger | Purpose |
|------|---------|---------|
| Health check | "health check", "check vault health" | Schema validation, secret scan, broken links, alias consistency, staleness |
| Maintenance | "run maintenance", "housekeeping", scheduled via cron | Full housekeeping: archive, organize, flagged review, health, sync |
| Inbox processing | "process inbox", "check inbox" | Classify and process pending inbox items with multimodal support |
| Sync | "sync", "check for gaps" | Calendar gaps, task drift, memory freshness |
| Reference update | "update references", "update framework" | Migrate templates and schemas while preserving user data |

---

## Automatic vs user-initiated operations

### Automatic (session-start or cron)

These run silently via the core skill's session-start check or via CronCreate scheduled jobs. They require no user interaction and produce no output unless critical issues are found.

| Operation | Script | What it does |
|-----------|--------|-------------|
| Schema validation | `scripts/validate-schema.py` | Validate frontmatter against _system/schemas.yaml |
| Secret scan | `scripts/scan-secrets.py` | Check for blocked/warned patterns from _system/guardrails.yaml |
| Health check | `scripts/health-check.py` | Links + aliases + staleness |
| Archive sweep | `scripts/archive.py --auto` | Expire stale content past tier thresholds |
| Sync check | `scripts/sync.py` | Calendar gaps + task drift |

**Triggering**: The core skill reads `_system/housekeeping-state.yaml` at session start. If `last_run` is not today, it runs the above scripts, updates the state file, and proceeds to the user's request.

### User-initiated (explicit command only)

| Operation | Trigger | Why not automatic |
|-----------|---------|------------------|
| Full maintenance | "run maintenance" | Includes flagged content review, file organization, user approvals |
| Inbox processing | "process inbox" | Spawns processing that creates tasks and memory. Needs user confirmation. |
| Comprehensive sync | "sync" | Queries external systems, surfaces items needing triage |
| Reference update | "update references" | Structural changes that need user review |

### Cron scheduled execution

If CronCreate registered a maintenance job during onboarding (Step 7 of welcome skill), maintenance runs at the configured time (default: Friday 5:00pm). The session-start check serves as fallback: if cron already ran today, `last_run` will be current and the session-start check is a no-op.

---

## Health check mode

Triggered by: "health check", "check vault health"

Scan for vault issues, auto-fix where safe, present problems requiring manual intervention.

### Step 1: Run validation scripts

Execute scripts in sequence. Each outputs JSON.

```bash
python3 scripts/validate-schema.py {vault_path}
```

Parse output: array of schema violations (file, property, expected type, actual value).

```bash
python3 scripts/scan-secrets.py {vault_path}
```

Parse output: array of matches with severity (blocked, warned) and file locations.

### Step 2: Check broken wikilinks

Scan all files in `memory/`, `journal/`, and `contexts/` for `[[Entity Name]]` patterns.

For each wikilink:
1. Search via `obsidian search` for the target note
2. Check if the entity resolves via Obsidian aliases
3. Flag unresolved links as broken

Group broken links by target entity. Report count of references per broken target.

### Step 3: Alias consistency

Compare `_system/alias-registry.md` against actual note aliases:

1. For each entry in the alias registry, verify the target note exists and has the alias in its frontmatter `aliases` property
2. For each note with `aliases` in frontmatter, verify the alias is registered
3. Flag mismatches:
   - Registry entry pointing to missing note
   - Registry entry with alias not in note's frontmatter
   - Note alias not in registry

### Step 4: Check duplicate aliases

Scan all notes for `aliases` frontmatter. Build a reverse map: alias -> list of notes.

Flag any alias that maps to more than one note. These cause ambiguous resolution.

### Step 5: Stale content check

Check content staleness by tier thresholds:

| Tier | Entity types | Staleness threshold |
|------|-------------|-------------------|
| Active | People in recent meetings, active initiatives | 30 days |
| Reference | Products, vendors, competitors | 90 days |
| Archival | Completed initiatives, old decisions | 180 days |

For each entity past its threshold:
1. Read `tars-updated` property
2. Calculate days since last update
3. Flag with tier and days stale

### Step 6: Present report

```markdown
## Health check report (YYYY-MM-DD)

### Critical ({N})
| Category | File | Issue | Suggested fix |
|----------|------|-------|---------------|
| secret | memory/people/john.md | Contains SSN pattern | Remove line 42 immediately |
| schema | memory/decisions/old.md | Missing required tars-status | Add property |

### Warnings ({N})
| Category | File | Issue | Suggested fix |
|----------|------|-------|---------------|
| wikilink | journal/2026-03/meeting.md | Broken [[Unknown Person]] (3 refs) | Create person note or fix reference |
| alias | _system/alias-registry.md | "JC" maps to 2 notes | Disambiguate in registry |
| stale | memory/people/former-vendor.md | 95 days since update | Update or archive |

### Auto-fixable ({N})
| Category | File | Issue | Proposed fix |
|----------|------|-------|-------------|
| alias | memory/people/sarah.md | Alias "SC" not in registry | Add to _system/alias-registry.md |
| schema | memory/initiatives/proj.md | tars-updated missing | Set to file modification date |

"7 issues found (2 critical). Auto-fix all / Fix critical only / Review each?"
```

### Step 7: Apply fixes and log

Based on user choice:
- **Auto-fix all**: Apply all proposed fixes via obsidian-cli, report results
- **Fix critical only**: Apply only critical fixes
- **Review each**: Present each issue individually for approve/skip

After all fixes applied:
1. Log results to today's daily note (create if needed):
   ```
   obsidian append --path journal/YYYY-MM/YYYY-MM-DD-daily.md --content "## Health check\n{summary}"
   ```
2. Update `_system/housekeeping-state.yaml` with run timestamp

---

## Maintenance/housekeeping mode

Triggered by: "run maintenance", "housekeeping", or scheduled via cron.

Full maintenance pipeline. Runs all health operations plus archive, file organization, flagged content review, and sync.

### Step 1: Check if already run today

Read `_system/housekeeping-state.yaml`.

- If `last_run` equals today AND this is not a manual invocation: "Maintenance already ran today. Force re-run? [Y/N]"
- If manual invocation (user explicitly asked): proceed regardless

### Step 2: Archive sweep

Find notes past staleness threshold for archival.

**GUARDRAIL**: Never archive notes with backlinks from the last 90 days.
**GUARDRAIL**: Never archive notes referenced by active tasks (check via `obsidian search` and task system query).

Process:
1. Run `scripts/archive.py --dry-run {vault_path}` to get candidates
2. For each candidate, verify guardrails:
   - `obsidian search` for backlinks to the note
   - Check if any backlink source was modified in last 90 days
   - Check if note is referenced in any open task
3. Remove candidates that fail guardrails
4. Present remaining candidates for user approval:

> "{N} archive candidates:
>   1. memory/people/former-contractor.md (180 days stale, 0 recent backlinks)
>   2. memory/decisions/2025-06-old-decision.md (270 days stale, 0 recent backlinks)
>   3. memory/vendors/defunct-vendor.md (200 days stale, 0 recent backlinks)
>
> Archive all / Select specific / Skip"

5. For approved items: move to `archive/` via filesystem, add `tars/archived` tag, log to changelog

### Step 3: Organize human-added files

Scan `inbox/` and `contexts/` for files without companion `.md` files.

For each orphan file (non-markdown file without a companion note):

1. Read the file (images via multimodal, PDFs via text extraction, etc.)
2. Generate metadata: infer topic, date, source
3. Create a companion note using the companion template:
   ```
   obsidian create --template templates/companion.md --path contexts/YYYY-MM/{new-slug}.md
   obsidian property:set --property tars-original-file --value "{original_filename}"
   obsidian property:set --property tars-original-type --value "{file_type}"
   obsidian property:set --property tars-summary --value "{generated_summary}"
   ```
4. Propose date-based organization and consistent naming

Present proposals:

> "3 unorganized files. Proposed:
>   1. IMG_2847.png -> contexts/2026-03/q1-roadmap-screenshot.png + companion note
>   2. report.pdf -> contexts/2026-03/vendor-evaluation-report.pdf + companion note
>   3. notes.txt -> contexts/2026-03/meeting-rough-notes.txt + companion note
>
> Organize? [all / review each / skip]"

For approved items: move file to proposed location, create companion note, log to changelog.

### Step 4: Flagged content review

Run flagged content scanner:

```bash
python3 scripts/scan-flagged.py {vault_path}
```

Parse output: array of flagged statements with person, statement text, date, and age in days.

Present flagged items:

> "4 flagged statements:
>   1. [[Steve Chen]]: 'slow to deliver' (6 days ago)
>   2. [[Patty Kim]]: 'playing politics' (11 days ago)
>   3. [[Dan Rivera]]: 'checked out' (75 days ago) -- STALE
>
> Actions per item: remove / keep / soften
> Bulk actions: 'remove 1,3' / 'keep all' / 'soften 2' / 'remove all for Steve'"

Process user selections:
- **Remove**: Delete the flagged statement from the person's note via obsidian-cli edit
- **Keep**: No action, reset flag age counter
- **Soften**: Present the statement and ask user for replacement wording, then update

### Step 5: Run health check

Execute the full health check mode (Steps 1-7 above). Present results inline.

### Step 6: Sync check

Run lightweight sync operations:

**Calendar gaps**: Query calendar for last 7 days of events. Cross-reference against journal entries.
- For each meeting without a journal entry: flag as "unprocessed meeting"
- Report: "{N} meetings in last 7 days without journal entries"

**Task system drift**: If external task system is configured, query for:
- Tasks in vault not in external system
- Tasks in external system not in vault
- Status mismatches (completed in one, open in other)

**Memory staleness**: Check people who appeared in recent meetings (last 14 days) but whose memory notes have `tars-updated` older than 30 days.
- Report: "{N} people in recent meetings with stale memory profiles"

### Step 7: Archive processed inbox items

Move items in `inbox/processed/` older than 7 days to `archive/`:
- Check `tars-inbox-processed` property date
- If older than 7 days, move to archive
- Never delete originals

### Step 8: Update housekeeping state

```yaml
# _system/housekeeping-state.yaml
last_run: YYYY-MM-DD
last_success: true
run_count: {incremented}
last_archival: YYYY-MM-DD  # if archive sweep ran
pending_inbox_count: {current count}
```

### Step 9: Log to daily note

Append maintenance summary to today's daily note:

```
obsidian append --path journal/YYYY-MM/YYYY-MM-DD-daily.md --content "## Maintenance ({timestamp})
- Archived: {N} notes
- Organized: {N} files
- Flagged reviewed: {N} statements
- Health issues: {N} found, {N} fixed
- Calendar gaps: {N} unprocessed meetings
- Task drift: {N} mismatches
- Stale profiles: {N} people"
```

---

## Inbox processing mode

Triggered by: "process inbox", "check inbox"

Classify and process all pending inbox items. Supports text, transcripts, images, PDFs, and mixed content.

### Step 1: Scan inbox

```
obsidian search query="path:inbox/pending" limit=50
```

Or fall back to directory listing of `inbox/pending/`.

For each file, read the first 50 lines (or full content for images) to determine content type.

### Step 2: Classify each item

| Content type | Detection signals | Processing route |
|-------------|-------------------|-----------------|
| Transcript/meeting notes | Speaker labels, timestamp patterns, "Meeting:", Otter/Fireflies format | Meeting processing pipeline |
| Screenshot/image | .png, .jpg, .jpeg, .gif, .webp extension | Multimodal analysis + context inference |
| Article/link | URL, "http", article structure, byline | Wisdom extraction |
| PDF/document | .pdf, .docx, .xlsx extension | Companion file + text extraction |
| Task-like items | Checkbox patterns, "TODO", "Action item", numbered action lists | Task extraction |
| Facts/memory items | Declarative statements, "Remember:", "Note:" | Memory save |
| Mixed | Multiple types detected in one file | Split into components |

### Step 3: Present inventory with classification

> "5 items in inbox:
>   1. ClientCo-sync-notes.txt -- meeting transcript (Otter format)
>   2. IMG_2847.png -- screenshot of Slack message from Sarah about API deadline
>   3. api-patterns.pdf -- research paper on API design
>   4. quick-notes.md -- mixed (2 tasks + 3 facts)
>   5. strategy-article.md -- article on platform strategy
>
> Process all? [all / pick specific / reclassify any]"

Allow user to:
- Override classification for any item
- Exclude items from processing
- Reorder processing priority

### Step 4: Process each item

Process items sequentially (or in parallel for independent items). Between items, report progress:

> "Item 1 complete. Item 2 of 5..."

#### 4a: Transcript processing

Route to meeting skill pipeline (`skills/meeting/SKILL.md`):
1. Load reference files (alias registry, integrations, memory)
2. Resolve speaker names
3. Generate structured report (topics, updates, concerns, decisions, action items)
4. Save to journal with frontmatter
5. Extract tasks (with user review)
6. Extract durable memory
7. Archive original transcript to `archive/transcripts/YYYY-MM/`

#### 4b: Screenshot/image processing

Multimodal analysis pipeline:

1. Read image via multimodal capability
2. Detect content type:
   - Meeting slide/presentation
   - Email screenshot
   - Chat/Slack message
   - Document/whiteboard
   - Chart/diagram
   - Other
3. Check image timestamp against calendar for concurrent meetings:
   - If meeting content detected, query calendar for events at that time
   - "This appears to be from your 2pm Platform Review. Associate? [Y/N]"
4. Extract text, tasks, key information from the image
5. Create companion note with extracted content:
   ```
   obsidian create --template templates/companion.md --path contexts/YYYY-MM/{slug}.md
   obsidian property:set --property tars-original-file --value "{image_filename}"
   obsidian property:set --property tars-original-type --value "{png|jpg|etc}"
   obsidian property:set --property tars-summary --value "{extracted_summary}"
   ```
6. If meeting-associated: link companion note to the journal entry
7. Extract any tasks or facts from the image content

#### 4c: Article/link processing

Route to learn skill wisdom mode (`skills/learn/SKILL.md`):
1. Read article content (use defuddle skill for web content)
2. Extract insights, apply durability test
3. Persist durable insights to memory
4. Save wisdom journal entry
5. Extract any actionable items as tasks

#### 4d: PDF/document processing

1. Read document content (PDF via text extraction, use available tools)
2. Create companion note with metadata and summary
3. Extract key information, facts, tasks
4. If document is relevant to an initiative or person, link via wikilinks
5. Move original to organized location in `contexts/YYYY-MM/`

#### 4e: Task extraction

1. Parse task-like items from content
2. Apply accountability test (concrete, owned, verifiable)
3. Present extracted tasks for user review:
   > "3 tasks extracted:
   >   1. Review API spec by Friday -> Active (owner: you, due: 2026-03-27)
   >   2. Send Sarah the deployment plan -> Delegated (owner: Sarah, due: 2026-03-24)
   >   3. Consider new monitoring tool -> Backlog (no date)
   >
   > Create all / select / edit / skip"
4. Create approved tasks via task integration

#### 4f: Fact/memory processing

1. Parse factual statements
2. Apply durability test (lookup value, signal, durability, behavior change)
3. For passing facts, identify target memory file (person, initiative, org-context, etc.)
4. Present for user confirmation:
   > "2 durable facts extracted:
   >   1. Sarah Chen promoted to VP Engineering -> update memory/people/sarah-chen.md
   >   2. Platform Rewrite target moved to Q3 -> update memory/initiatives/platform-rewrite.md
   >
   > Save all / select / skip"
5. Persist approved facts via obsidian-cli

### Step 5: Mark processed

For each processed item:
```
obsidian property:set --path inbox/pending/{file} --property tars-inbox-processed --value true
```

Move processed files to `inbox/processed/`. NEVER delete originals.

### Step 6: Summary and log

```markdown
## Inbox processing complete

### Processed items
| # | File | Type | Journal | Tasks | Memory | Status |
|---|------|------|---------|-------|--------|--------|
| 1 | ClientCo-sync-notes.txt | transcript | journal/2026-03/... | 3 | 2 | ok |
| 2 | IMG_2847.png | image | -- | 1 | 0 | ok |
| 3 | api-patterns.pdf | document | -- | 0 | 1 | ok |
| 4 | quick-notes.md | mixed | -- | 2 | 3 | ok |
| 5 | strategy-article.md | article | journal/2026-03/... | 0 | 4 | ok |

### Summary
- Items processed: 5
- Tasks created: 6 (verified)
- Memory updates: 10
- Journal entries: 2
- Companion notes: 2
```

Log to daily note.

---

## Sync mode

Triggered by: "sync", "check for gaps"

Compare vault state against external systems and detect drift.

### Step 1: Calendar gaps

Query calendar for last 7 days of events:
```
calendar_get_events with start_date=(today - 7 days) end_date=today
```

Cross-reference each meeting against journal entries:
1. Search journal for matching date and meeting title
2. Search journal for matching participants
3. Flag meetings without journal entries

Report:
> "Calendar gaps (last 7 days):
>   1. 2026-03-17 Platform Review (45 min, 5 attendees) -- no journal entry
>   2. 2026-03-19 1:1 with Sarah (30 min) -- no journal entry
>
> Process any? [select / skip all]"

For selected meetings: create placeholder journal entries or route to meeting processing if transcript is available.

### Step 2: Task drift

If external task system is configured:

1. Query all vault tasks (via active-tasks.base and overdue-tasks.base)
2. Query external task system for user's tasks
3. Compare and flag:
   - **Vault-only**: Tasks in vault not in external system
   - **External-only**: Tasks in external system not in vault
   - **Status mismatch**: Completed in one, open in other
   - **Date mismatch**: Different due dates between systems

Report:
> "Task drift detected:
>   - 2 tasks in vault not in Reminders
>   - 1 task completed in Reminders but open in vault
>   - 1 due date mismatch
>
> Resolve? [auto-sync / review each / skip]"

### Step 3: Memory freshness

Check people who appeared in recent meetings (last 14 days) but have stale memory profiles:

1. Extract participant names from journal entries in last 14 days
2. For each person, check `tars-updated` date in their memory note
3. Flag if `tars-updated` is older than 30 days

Report:
> "3 people in recent meetings with stale profiles:
>   1. [[Sarah Chen]] -- last updated 45 days ago, appeared in 3 meetings
>   2. [[Bob Kim]] -- last updated 60 days ago, appeared in 1 meeting
>   3. [[New Person]] -- no memory profile exists
>
> Update profiles? [update all / select / skip]"

For selected people:
- Existing profiles: scan recent journal entries for new facts, apply durability test, update
- Missing profiles: create new person note with info from journal entries

### Step 4: Present consolidated report

```markdown
## Sync report (YYYY-MM-DD)

| Category | Found | Resolved |
|----------|-------|----------|
| Calendar gaps | {N} | {N} |
| Task drift | {N} | {N} |
| Stale profiles | {N} | {N} |

### Actionable items remaining
- {list of items user deferred or skipped}
```

Log to daily note.

---

## Reference update mode

For framework updates. Migrate templates, schemas, _system files while preserving user data.

### Step 1: Version check

Read `_system/housekeeping-state.yaml` for `plugin_version`.
Compare against the current TARS version in the source tree.

If versions match: "Vault is up to date (v{version})." Exit.
If no `plugin_version` field: first update, proceed.

### Step 2: Dry-run preview

Categorize files by update strategy:

**Safe to overwrite** (no user data):
- `_system/taxonomy.md`
- `_system/schemas.yaml`
- `_system/guardrails.yaml` (block/warn patterns only, not custom additions)
- `templates/*.md`
- `_views/*.base`
- `scripts/*.py`

**Requires merge** (contain user data):
- `_system/config.md` -- preserve all user properties, add new framework properties
- `_system/integrations.md` -- preserve provider config, update structure
- `_system/alias-registry.md` -- preserve all entries, update format
- `_system/kpis.md` -- preserve user KPIs, update instructions
- `_system/schedule.md` -- preserve user items, update format

**State files** (machine-managed):
- `_system/housekeeping-state.yaml` -- add new keys, keep existing values
- `_system/maturity.yaml` -- add new keys, keep existing values

Present preview:

```markdown
## Reference update preview (v{old} -> v{new})

### Files to overwrite ({N})
| File | Reason |
|------|--------|
| _system/taxonomy.md | No user data, full replace |
| templates/person.md | Template update with new properties |

### Files to merge ({N})
| File | User data preserved |
|------|-------------------|
| _system/config.md | All tars-user-* properties |
| _system/integrations.md | Provider configuration |

### New files ({N})
| File | Purpose |
|------|---------|
| templates/new-type.md | New entity template |

### Unchanged ({N})
- _system/alias-registry.md (no structural changes)

Proceed? [Y/N]
```

### Step 3: Apply update

For each file category:

1. **Overwrite**: Replace file content entirely
2. **Merge**: Read current file, extract user data sections, write new structure with user data preserved
3. **New**: Create file from template
4. **State**: Add missing keys with defaults, preserve existing values

After update:
1. Update `plugin_version` in `_system/housekeeping-state.yaml`
2. Log changes to `_system/changelog/YYYY-MM-DD.md`
3. Git commit: "Update TARS framework to v{new}"

Report:

```markdown
## Reference update complete (v{new})

| Category | Count |
|----------|-------|
| Files overwritten | {N} |
| Files merged | {N} |
| Files created | {N} |
| Files unchanged | {N} |
| User data preserved | {N} sections |
```

---

## Context budget

**Health check mode**:
- _system/ files: Read schemas.yaml, guardrails.yaml, alias-registry.md
- Memory: Scan frontmatter only (not full content) unless checking wikilinks
- Journal: Scan last 30 days of entries for wikilink validation
- Scripts: Execute validate-schema.py, scan-secrets.py

**Maintenance mode**:
- All of health check budget, plus:
- Scripts: Execute archive.py, scan-flagged.py, sync.py
- Calendar: Last 7 days of events
- Task system: Query all configured lists
- Memory: Full read for archive candidates only
- Inbox/contexts: Directory listing for file organization

**Inbox mode**:
- Inbox: Read all files in inbox/pending/ (first 50 lines for classification, full for processing)
- Reference: alias-registry.md, integrations.md
- Memory: people, initiatives, decisions (for wikilink validation)
- Calendar: Query per transcript item for meeting correlation
- Per-item budget: full file read + template writes + task/memory updates

**Sync mode**:
- Calendar: Last 7 days of events
- Task system: Query all configured lists + overdue
- Journal: Last 14 days of entries
- Memory: People notes referenced in recent journal entries

**Reference update mode**:
- _system/: Read all files for version comparison and merge
- Templates/scripts/_views: Read current versions for diff
- Source tree: Read new versions for comparison

---

## Absolute constraints

### Health check
- NEVER delete files (only suggest deletions with user confirmation)
- NEVER modify note body content without user approval
- NEVER change wikilink targets without user approval
- Auto-fix scope: deterministic fixes only (alias registry sync, schema defaults, missing properties with computable values)

### Maintenance
- NEVER archive notes with backlinks from last 90 days
- NEVER archive notes referenced by active tasks
- NEVER delete flagged content without explicit user instruction per item
- NEVER auto-process inbox during maintenance (only report count)
- ALWAYS present archive candidates for user approval before moving
- ALWAYS present flagged content actions for user selection

### Inbox processing
- NEVER process items without user confirmation of the classification and processing plan
- NEVER delete source files (move to processed/, never remove)
- NEVER skip multimodal analysis for image files
- NEVER create tasks without user review of the extracted task list
- NEVER persist memory facts without user confirmation
- ALWAYS check calendar correlation for images and transcripts
- ALWAYS preserve originals in inbox/processed/ or archive/

### Sync
- NEVER auto-resolve task drift (always present for user decision)
- NEVER fabricate journal entries for missed meetings (create placeholders only)
- NEVER update memory profiles without showing what changed
- ALWAYS report gaps even if no action is taken

### Reference update
- NEVER overwrite files containing user data without merge strategy
- NEVER lose user configuration during framework updates
- ALWAYS preview changes before applying
- ALWAYS git commit after successful update

### Universal
- ALWAYS log all maintenance actions to the daily note
- ALWAYS update _system/housekeeping-state.yaml after any maintenance run
- ALWAYS use obsidian-cli for note creation and property updates
- NEVER use direct file I/O for writes when obsidian-cli is available
