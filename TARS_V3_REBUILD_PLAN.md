# TARS 3.0: Complete Rebuild Plan

**Date**: 2026-03-21
**Status**: Comprehensive implementation plan — ready for agent execution
**Branch**: `tars-3.0` (created from `main`, current codebase untouched)
**Destination file**: Save this plan to workspace as `TARS_V3_REBUILD_PLAN.md` before beginning implementation.

---

## How to use this plan

This is the authoritative guide for the AI agent rebuilding TARS. It contains:

- **Part A**: Design decisions and architectural principles
- **Part B**: Complete vault structure and data model
- **Part C**: All workflow specifications with exact obsidian-cli commands
- **Part D**: Ten real-world issue solutions from production usage
- **Part E**: Trust, safety, and guardrails
- **Part F**: Testing and validation strategy
- **Part G**: Phased build sequence with file manifest
- **Part H**: Migration considerations (for future planning)

The technical reference in `TARS_V2_REBUILD_PLAN.md` remains valid for deep implementation details (frontmatter schemas, .base file YAML, script patterns). This plan supersedes it for architectural decisions, workflow design, and build sequence.

**Agent instructions**: Create branch `tars-3.0` from `main` before any work. Do not modify `main`. Follow the build sequence in Part G. When implementation reveals a better approach than what's specified here, deviate and document why in a `DECISIONS.md` file.

---

# PART A: DESIGN DECISIONS AND PRINCIPLES

## What TARS is

TARS is a persistent executive assistant for senior knowledge workers. It provides continuity, structure, follow-through, and strategic rigor across time. The user is a senior executive. Every interaction must respect their time, present information clearly, and make it easy to make decisions quickly.

TARS is NOT:
- A chatbot or prompt library
- A note-taking app (Obsidian handles notes; TARS handles the operating layer)
- A silent assistant that makes decisions on behalf of the user

## Core architectural principles

1. **obsidian-cli is the write interface.** All vault mutations go through `obsidian create`, `obsidian append`, `obsidian property:set`. Never direct file I/O for writes. This keeps Obsidian's metadata cache, link graph, and .base queries current.

2. **Scripts are deterministic validators.** Python scripts read the filesystem directly for validation, scanning, and reporting. They output JSON. The agent consumes that JSON and applies fixes via obsidian-cli.

3. **Bases replace indexes.** .base files are live queries over frontmatter. They never drift. No `rebuild-indexes.py`. No `_index.md` files anywhere.

4. **Tags drive filterability.** Every TARS note gets a hierarchical tag (`tars/person`, `tars/task`, `tars/journal`, etc.) for reliable .base filtering and obsidian-cli search.

5. **Frontmatter is the schema.** All structured data lives in YAML frontmatter with typed Obsidian properties. Body content is narrative. All TARS-managed properties use the `tars-` prefix to avoid collisions.

6. **Ask don't assume.** When confidence is below 80% on anything that would be persisted, ask the user. Prefer multiple-choice questions. Batch questions (max 3-4 per round). Always include a skip/escape option. Always check the vault before asking — never ask what TARS could find itself.

7. **Check before writing.** Before any persistence, check what the vault already knows. Skip redundant information. Flag contradictions. Show diffs for updates. Process batches chronologically so later inputs supersede earlier ones.

8. **Review before persist.** Tasks, memory updates, and sensitive content always require user confirmation via numbered lists with selection syntax.

9. **Every write is logged.** The daily note accumulates an activity log. `_system/changelog/` records every write with batch IDs for rollback.

10. **Git is the safety net.** The vault is a git repository. Every write batch gets a commit. Rollback is always possible.

11. **Transcripts are preserved.** Original transcripts are archived with bidirectional links to journal entries. When summaries don't have the answer, the agent falls back to the raw transcript.

12. **Single source tree.** No duplicate plugin folders. The vault IS the source of truth. No `.claude-plugin/`, no `tars-cowork-plugin/`.

13. **Self-awareness.** TARS detects its own repeated failures and logs them to a backlog. User suggestions are captured as ideas. The maintainer reviews both.

## What changes from v1/v2

| Aspect | v1/v2 (current) | v3 (rebuild) |
|--------|-----------------|--------------|
| Interface | Claude Code filesystem I/O | Obsidian vault via obsidian-cli |
| Indexes | Hand-maintained `_index.md` files | Obsidian Bases (.base live queries) |
| Templates | Markdown text blobs | Obsidian templates with frontmatter |
| Metadata | Inconsistent YAML | Obsidian-native properties (typed, `tars-` prefixed) |
| Links | Wikilinks (manually verified) | Obsidian wikilinks (alias-resolved, graph-backed) |
| Name resolution | `replacements.md` flat table | 3-layer: Obsidian aliases → context-aware registry → search fallback |
| Locking | `.lock` file convention | Obsidian-cli serializes writes natively |
| Distribution | Duplicated plugin folders | Single source tree |
| Orchestration | Prompt-only sub-agents | Agent + deterministic scripts |
| Maintenance | Described in prompts, manual | Scripts + CronCreate scheduled jobs |
| Task review | Auto-create after extraction | Numbered list with selection syntax, always |
| Transcript handling | Discarded after processing | Preserved with bidirectional journal links |
| Assumptions | Silent guessing | Ask with multiple-choice |
| File organization | Manual, inconsistent | Auto-organized with companion files |
| Image/screenshot handling | Not supported | Multimodal analysis + context inference |
| Negative statements | Persist indefinitely | Flagged, periodic cleanup reports |
| Self-evaluation | None | Auto-detected issues + user idea capture |
| Scheduling | Manual invocation only | CronCreate for briefings and maintenance |
| Persistence discipline | Force-extract from everything | Check existing knowledge first, be picky |

## What does NOT change

- The memory entity model (people, initiatives, decisions, products, vendors, competitors, org-context)
- The durability test for memory persistence (4 criteria, all must pass)
- The accountability test for task creation (3 criteria, all must pass)
- Meeting processing as the highest-value pipeline
- Journal-first persistence of meaningful outputs
- Provider-agnostic integration architecture (categories, not vendors)
- Strategic thinking modes (analysis, validation, executive council, deep analysis, discovery)
- Stakeholder-aware communication support
- Guardrails for sensitive data (block patterns, warn patterns)

---

# PART B: VAULT STRUCTURE AND DATA MODEL

## Folder structure

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
│   ├── config.md                        # User profile, preferences, schedule times
│   ├── integrations.md                  # Provider-agnostic integration registry
│   ├── alias-registry.md               # Name → canonical mapping with context disambiguation
│   ├── taxonomy.md                      # Entity types, tags, relationship types
│   ├── kpis.md                          # KPI definitions per initiative
│   ├── schedule.md                      # Recurring/one-time scheduled items
│   ├── guardrails.yaml                  # Sensitive data patterns + negative sentiment patterns
│   ├── maturity.yaml                    # Onboarding progress tracking
│   ├── housekeeping-state.yaml          # Maintenance state + cron job IDs
│   ├── schemas.yaml                     # Frontmatter validation schemas (all types)
│   ├── changelog/                       # Per-day operation logs with batch IDs
│   │   └── YYYY-MM-DD.md
│   └── backlog/                         # Self-evaluation (Issue 9)
│       ├── issues/                      # Auto-detected framework errors (deduplicated)
│       └── ideas/                       # User-requested improvements
├── _views/
│   ├── all-people.base                  # Live query: people (with stale detection formula)
│   ├── all-initiatives.base             # Live query: active/all initiatives by health
│   ├── all-decisions.base               # Live query: decisions by date/status
│   ├── all-products.base
│   ├── all-vendors.base
│   ├── all-competitors.base
│   ├── recent-journal.base              # Journal entries by tars-meeting-datetime, last 30d
│   ├── active-tasks.base               # Open tasks by priority/owner/due date
│   ├── overdue-tasks.base              # Formula: tars-due < today()
│   ├── stale-memory.base               # Formula: days since update > staleness threshold
│   ├── inbox-pending.base              # Pending inbox items
│   ├── all-documents.base              # Companion files for non-markdown content (Issue 4)
│   ├── all-transcripts.base            # Archived transcripts with journal links (Issue 6)
│   ├── flagged-content.base            # People with negative sentiment flags (Issue 8)
│   ├── backlog.base                    # Issues + ideas for maintainer (Issue 9)
│   └── initiative-map.canvas           # Generated visual initiative map
├── memory/
│   ├── people/
│   ├── vendors/
│   ├── competitors/
│   ├── products/
│   ├── initiatives/
│   ├── decisions/
│   └── org-context/
├── journal/
│   └── YYYY-MM/                         # Date-organized journal entries
├── contexts/
│   ├── products/
│   └── artifacts/
│   └── YYYY-MM/                         # Date-organized user-added content (Issue 4)
├── inbox/
│   ├── pending/                         # Drop zone for raw inputs
│   └── processed/                       # Marked processed (maintenance archives later)
├── archive/
│   ├── transcripts/YYYY-MM/            # Preserved transcripts with journal backlinks (Issue 6)
│   └── ...                              # Flat archive for other content
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
│   ├── wisdom-journal.md
│   ├── companion.md                     # For non-markdown files (Issue 4)
│   ├── transcript.md                    # For archived transcripts (Issue 6)
│   ├── issue.md                         # For backlog issues (Issue 9)
│   └── idea.md                          # For backlog ideas (Issue 9)
├── scripts/
│   ├── validate-schema.py              # Validates frontmatter against schemas.yaml
│   ├── scan-secrets.py                 # Blocks/warns on sensitive patterns
│   ├── scan-flagged.py                 # Finds negative sentiment markers (Issue 8)
│   ├── health-check.py                 # Schema + links + aliases + staleness
│   ├── archive.py                      # Staleness-based archival
│   └── sync.py                         # Calendar gaps + task system sync
├── skills/
│   ├── core/SKILL.md                   # Identity, routing, universal protocols
│   ├── welcome/SKILL.md                # Onboarding wizard
│   ├── learn/SKILL.md                  # Memory save + wisdom extraction
│   ├── tasks/SKILL.md                  # Task extraction + management
│   ├── meeting/SKILL.md                # Meeting processing pipeline
│   ├── briefing/SKILL.md               # Daily + weekly briefings
│   ├── answer/SKILL.md                 # Fast lookup with transcript fallback
│   ├── maintain/SKILL.md               # Health + sync + housekeeping + file org
│   ├── think/SKILL.md                  # Strategic analysis modes A-E
│   ├── think/manifesto.md              # Executive council persona definitions
│   ├── communicate/SKILL.md            # Stakeholder-aware drafting
│   ├── communicate/text-refinement.md  # Lightweight editing
│   ├── initiative/SKILL.md             # Planning + status
│   └── create/SKILL.md                 # Artifact creation
└── CLAUDE.md                            # Vault-level agent configuration
```

## Tag taxonomy

| Tag | Used on | Purpose |
|-----|---------|---------|
| `tars/person` | People memory notes | Filter in bases, search |
| `tars/vendor` | Vendor memory notes | |
| `tars/competitor` | Competitor memory notes | |
| `tars/product` | Product memory notes | |
| `tars/initiative` | Initiative notes | |
| `tars/decision` | Decision records | |
| `tars/org-context` | Organizational context | |
| `tars/journal` | All journal entries | |
| `tars/meeting` | Meeting journals (also has tars/journal) | |
| `tars/briefing` | Briefings (also has tars/journal) | |
| `tars/wisdom` | Wisdom entries (also has tars/journal) | |
| `tars/task` | Task notes | |
| `tars/transcript` | Archived transcripts | Issue 6 |
| `tars/companion` | Companion files for non-markdown | Issue 4 |
| `tars/analysis` | Strategic analysis outputs | |
| `tars/communication` | Drafted communications | |
| `tars/inbox` | Inbox items | |
| `tars/archived` | Additive tag on archived items | |
| `tars/backlog` | Backlog items (issues + ideas) | Issue 9 |
| `tars/issue` | Auto-detected framework errors | Issue 9 |
| `tars/idea` | User-requested improvements | Issue 9 |
| `tars/flagged` | Notes with negative sentiment flags | Issue 8 |

## Frontmatter schemas

All TARS properties use the `tars-` prefix. Obsidian native properties (`tags`, `aliases`, `cssclasses`) keep their standard names.

See `TARS_V2_REBUILD_PLAN.md` Part 4 for complete schema definitions per entity type.

**Additional schemas for Issue solutions:**

### Transcript (Issue 6)
```yaml
---
tags: [tars/transcript]
tars-journal-entry: "[[2026-03-21 Platform Review]]"
tars-date: 2026-03-21
tars-meeting-datetime: 2026-03-21T14:00:00
tars-participants: ["[[Jane Smith]]", "[[Bob Chen]]"]
tars-format: otter | fireflies | zoom | teams | raw_text
tars-created: 2026-03-21
---
```

### Companion (Issue 4)
```yaml
---
tags: [tars/companion]
tars-original-file: "vendor-report.pdf"
tars-original-type: pdf | docx | png | jpg | xlsx | other
tars-file-size: "2.4 MB"
tars-added-date: 2026-03-21
tars-source: user-added
tars-summary: "Q1 vendor evaluation report"
tars-topics: [vendor-evaluation]
tars-created: 2026-03-21
---
```

### Meeting journal (updated for Issue 1, 6)
```yaml
---
tags: [tars/journal, tars/meeting]
tars-date: 2026-03-21
tars-meeting-datetime: 2026-03-21T14:00:00    # Precise timestamp for chronological ordering
tars-participants: ["[[Jane Smith]]", "[[Bob Chen]]"]
tars-organizer: "[[Jane Smith]]"
tars-topics: [q1-roadmap, hiring]
tars-initiatives: ["[[Platform Rewrite]]"]
tars-source: calendar | transcript | notes | manual
tars-calendar-title: "Q1 Planning Sync"
tars-transcript: "[[2026-03-21-platform-review-transcript]]"  # Link to archived transcript
tars-transcript-format: otter | fireflies | zoom | teams | raw_text
tars-created: 2026-03-21
---
```

### Issue (Issue 9)
```yaml
---
tags: [tars/backlog, tars/issue]
tars-issue-type: mcp-error | cli-error | skill-error | data-error | other
tars-severity: critical | warning | info
tars-occurrence-count: 3
tars-first-seen: 2026-03-19
tars-last-seen: 2026-03-21
tars-status: open | acknowledged | resolved
tars-context: "Meeting processing, calendar lookup step"
tars-created: 2026-03-19
---
```

### Idea (Issue 9)
```yaml
---
tags: [tars/backlog, tars/idea]
tars-requested-by: user
tars-status: proposed | accepted | implemented | rejected
tars-created: 2026-03-21
---
```

## Schema validation file (`_system/schemas.yaml`)

See `TARS_V2_REBUILD_PLAN.md` Part 4 for the full schemas.yaml content. Add these additional type definitions:

```yaml
transcript:
  required_tags: [tars/transcript]
  required_properties:
    - tars-journal-entry
    - tars-date
    - tars-created
  property_rules:
    tars-format:
      enum: [otter, fireflies, zoom, teams, raw_text, unknown]

companion:
  required_tags: [tars/companion]
  required_properties:
    - tars-original-file
    - tars-original-type
    - tars-added-date
    - tars-created
  property_rules:
    tars-original-type:
      enum: [pdf, docx, png, jpg, xlsx, pptx, other]

issue:
  required_tags: [tars/backlog, tars/issue]
  required_properties:
    - tars-issue-type
    - tars-severity
    - tars-occurrence-count
    - tars-status
    - tars-first-seen
    - tars-created
  property_rules:
    tars-severity:
      enum: [critical, warning, info]
    tars-status:
      enum: [open, acknowledged, resolved]

idea:
  required_tags: [tars/backlog, tars/idea]
  required_properties:
    - tars-status
    - tars-created
  property_rules:
    tars-status:
      enum: [proposed, accepted, implemented, rejected]
```

## Obsidian Bases (.base files)

See `TARS_V2_REBUILD_PLAN.md` Part 5 for complete .base YAML definitions for all standard views.

**Additional bases for Issue solutions:**

### `_views/all-transcripts.base` (Issue 6)
```yaml
filter:
  property: tags
  operator: contains
  value: tars/transcript
views:
  - name: All Transcripts
    type: table
    properties:
      - file.name
      - tars-journal-entry
      - tars-date
      - tars-participants
      - tars-format
    order:
      - property: tars-date
        direction: desc
```

### `_views/all-documents.base` (Issue 4)
```yaml
filter:
  property: tags
  operator: contains
  value: tars/companion
views:
  - name: All Documents
    type: table
    properties:
      - file.name
      - tars-original-file
      - tars-original-type
      - tars-summary
      - tars-added-date
    order:
      - property: tars-added-date
        direction: desc
```

### `_views/flagged-content.base` (Issue 8)
```yaml
filter:
  property: tars-has-flagged-content
  operator: is
  value: true
views:
  - name: People with Flagged Content
    type: table
    properties:
      - file.name
      - tars-summary
      - tars-modified
    order:
      - property: tars-modified
        direction: asc
```

### `_views/backlog.base` (Issue 9)
```yaml
filter:
  property: tags
  operator: contains
  value: tars/backlog
views:
  - name: Open Issues
    type: table
    filters:
      - property: tars-status
        operator: is
        value: open
      - property: tags
        operator: contains
        value: tars/issue
    properties:
      - file.name
      - tars-severity
      - tars-occurrence-count
      - tars-last-seen
    order:
      - property: tars-occurrence-count
        direction: desc
  - name: Ideas
    type: table
    filters:
      - property: tags
        operator: contains
        value: tars/idea
    properties:
      - file.name
      - tars-status
      - tars-created
    order:
      - property: tars-created
        direction: desc
```

---

# PART C: WORKFLOW SPECIFICATIONS

## obsidian-cli command reference (used throughout)

```bash
obsidian read file="Jane Smith"                                    # Wikilink resolution, respects aliases
obsidian create name="Note" path="path/note.md" template="person" silent  # Create from template
obsidian property:set name="tars-status" value="active" file="Note"       # Set frontmatter property
obsidian append file="Note" content="## Update\nNew content."             # Append to note body
obsidian search query="tag:tars/task tars-status:open" limit=50           # Search by tag + property
obsidian backlinks file="Platform Rewrite"                                # Get all notes linking to this
obsidian daily:read                                                        # Read today's daily note
obsidian daily:append content="## TARS Activity\n- ..."                   # Append to daily note
obsidian tags sort=count counts                                            # List tags with counts
obsidian eval code="app.vault.getFiles().length"                          # Execute JS in Obsidian
```

## Write ordering (ALWAYS follow)

1. Create entity notes first (people, initiatives — link targets)
2. Update memory notes (reference entities)
3. Create journal entry (references entities and memory)
4. Create task notes (reference journal and entities)
5. Append to daily note (references everything above)
6. Write changelog entry (records everything above)

## C.1: Meeting processing pipeline

The highest-value workflow. Updated with Issues 1, 2, 3, 6, 7, 8.

```
STEP 1: Load alias registry
  obsidian read file="alias-registry"

STEP 2: Detect transcript format [Issue 1]
  Inspect the raw transcript and classify:
  - What format? (otter, fireflies, zoom, teams, raw_text, unknown)
  - Has date/time? Has duration? Has attendees header? Has speaker labels? Has timestamps?
  Produce metadata inventory. Fill in what's present.

STEP 3: MANDATORY calendar check [Issue 1]
  ALWAYS query calendar, even if transcript provides a date.
  a. If transcript has a date → use it for calendar query window
  b. If transcript lacks a date → query past 3 business days
  c. Match by: title keywords, attendee overlap, time window
  d. If single strong match → present for confirmation:
     "This appears to be the 'Q1 Planning Sync' from Mon Mar 16 at 10am. Correct? [Y/N]"
  e. If multiple matches → multiple-choice [Issue 3]:
     "Which meeting is this transcript from?
       1. Mon Mar 16, 10:00am — 'Q1 Planning' with Jane, Bob
       2. Tue Mar 17, 2:00pm — 'Platform Review' with Sarah
       3. None of these — I'll specify"
  f. If no match AND calendar unavailable → ask user:
     "When did this meeting happen? (e.g., 'yesterday at 2pm' or '2026-03-19')"
  g. NEVER proceed without a resolved date and time.

STEP 4: Resolve participants [Issue 3]
  Merge: transcript speaker labels + calendar attendees
  For each name:
    Check alias registry → obsidian search → if ambiguous, ask:
    "Who is 'Dan' in this meeting?
      1. Dan Rivera (Engineering)
      2. Dan Chen (Infrastructure)
      3. Someone new"
  Present final participant list for confirmation.

STEP 5: Knowledge inventory [Issue 7]
  Before extracting anything, check what the vault already knows:
  For each entity/topic identified in the transcript:
    obsidian search query="tag:tars/[type] [entity]" limit=5
    Compare: is this info NEW, an UPDATE, REDUNDANT, or CONTRADICTS existing?
  Report: "I already know X, Y, Z about this topic. Will focus on what's new."
  If processing a batch chronologically, note: "This is transcript 2 of 5.
  Later transcripts will supersede earlier ones on the same topics."

STEP 6: Secret scan [existing]
  Run scan-secrets.py against transcript content BEFORE writing.
  Block: SSN, API keys, passwords, tokens, connection strings.
  Warn: DOB, salary, compensation, PIP, termination, diagnosis.
  If blocked → redact and notify. If warned → flag for review.

STEP 7: Process transcript (LLM reasoning)
  Produce structured output with sections:
  - Topics discussed
  - Updates (from others, not the user)
  - Concerns (WHO / ISSUE / DEADLINE)
  - Decisions (what + who decided + rationale)
  - Action items (owner / task / deadline)
  - Unresolved items (things discussed without conclusion)
  - Key quotes (notable statements attributed to speakers)

STEP 8: Create journal entry [existing + Issue 6]
  obsidian create name="YYYY-MM-DD Meeting Title" \
    path="journal/YYYY-MM/YYYY-MM-DD-meeting-slug.md" \
    template="meeting-journal" silent
  Set all frontmatter properties including tars-meeting-datetime and tars-transcript.
  Append structured body content.
  Include "Associated captures" section for any screenshots (Issue 5).

STEP 9: Archive transcript [Issue 6]
  Move original transcript to archive/transcripts/YYYY-MM/ with standardized filename.
  Create frontmatter on archived transcript:
    tags: [tars/transcript]
    tars-journal-entry: "[[YYYY-MM-DD Meeting Title]]"
    tars-date, tars-participants, tars-format
  The journal entry's tars-transcript property points to this archived file.
  NEVER delete the original transcript.

STEP 10: Extract tasks with review [Issue 2]
  Apply accountability test to each potential task:
    a. Concrete? (specific deliverable, not "think about")
    b. Owned? (clear single owner)
    c. Verifiable? (will we know when it's done?)

  Present ALL candidates as numbered list:
  "15 potential tasks found. 8 pass the accountability test:

    1. [KEEP] Review hiring plan (you, due Mar 25, high)
    2. [KEEP] Share migration report (Bob Chen, due Mar 24, medium)
    ...
    8. [KEEP] Follow up with Sarah on API (you, due Mar 28, low)

    -- Filtered out --
    9.  'We should think about Q4' — no owner, not concrete
    10. 'The team needs to align' — no specific owner
    ...

  Which to create?
    - 'all' to create 1-8
    - '1, 3, 7' to keep specific ones
    - 'all except 4' to exclude specific ones
    - 'move 10 to keep' to override a filter
    - 'none' to skip all"

  Create ONLY selected tasks after user responds.

STEP 11: Extract memory with review [existing + Issues 7, 8]
  Apply durability test (all 4 must pass):
    a. Lookup value? (useful next week/month?)
    b. High-signal? (broadly applicable?)
    c. Durable? (not transient or tactical?)
    d. Behavior change? (changes future interactions?)

  For items passing durability test, apply knowledge check [Issue 7]:
    NEW → include in review
    UPDATE → show diff: "Current: 'Jane leads platform.' Update to: 'Jane leads platform and mobile.' Update?"
    REDUNDANT → skip: "Already in memory. Skipping."
    CONTRADICTS → ask: "Memory says REST. This transcript says GraphQL. Which is current?"

  For negative sentiment [Issue 8]:
    If statement contains negative patterns (slow, political, difficult, unreliable, etc.):
    "This about Steve has negative sentiment: 'Steve has been slow to deliver.'
     Save with flag for periodic review? [Y / Rephrase / Skip]"
    If saved: wrap in `<!-- tars-flag:negative YYYY-MM-DD -->` markers.
    Set `tars-has-flagged-content: true` on the person's note.

  Present all proposed memory updates:
  "Proposed memory updates:
    1. [[Jane Smith]]: Approved 2 backend hires for [[Platform Rewrite]]
    2. [[Bob Chen]]: Concerned about Q3 timeline
    3. New decision: REST over GraphQL for public API
  Save? [all / 1, 3 / none / edit #2]"

  Only persist after user confirms.

STEP 12: Scan for unresolved names [existing]
  Check all wikilinks in output. For any unresolved:
  Add to alias registry with "?? (needs full name)" marker.
  Report in summary.

STEP 13: Log to daily note + changelog [existing]
  obsidian daily:append content="## Meeting processed: [[YYYY-MM-DD Meeting Title]]
  - Tasks: N created (of M extracted)
  - Memory: N updates
  - Transcript: archived to [[archive/transcripts/...]]
  - Unresolved names: N"

  Write changelog entry with batch_id for rollback.

STEP 14: Self-evaluation [Issue 9]
  If any errors occurred during processing:
    Check _system/backlog/issues/ for existing issue with same error signature
    If exists: increment tars-occurrence-count, update tars-last-seen
    If new: create issue note with context
```

## C.2: Daily briefing

```
STEP 1: Determine date
  If after 5 PM, brief for tomorrow.

STEP 2: Gather data (parallel where possible)
  a. Calendar: list_events for target date
  b. Tasks: obsidian search query="tag:tars/task tars-status:open" limit=100
     Filter: due today, overdue, high priority
  c. People context: For each attendee in today's meetings:
     obsidian read file="[person name]"
  d. Schedule: obsidian read file="schedule"
  e. Housekeeping state: read _system/housekeeping-state.yaml
  f. Inbox count: obsidian search query="path:inbox/pending" limit=1

STEP 3: Cross-reference
  Match attendees to memory entities.
  Link tasks to meetings (same initiative, same people).
  Flag unrecognized attendees: "3 people not in memory: [names]"

STEP 4: Generate briefing sections
  - Today's schedule (with people context per meeting)
  - Priority tasks (due today + overdue, with source links)
  - Initiative pulse (health of active initiatives mentioned today)
  - Focus opportunities (gaps in calendar)
  - Unrecognized people (attendees not in memory)
  - System status (last maintenance, inbox count, maturity)
  - Data freshness footer: "Sources: N meetings, N tasks, N memory files.
    Stale: [person] not updated in 60+ days."

STEP 5: Save
  obsidian create name="YYYY-MM-DD Daily Briefing" \
    path="journal/YYYY-MM/YYYY-MM-DD-daily-briefing.md" \
    template="daily-briefing" silent
  Set properties. Append content.

STEP 6: Cron self-check [Issue 10]
  Verify all scheduled cron jobs are active (CronList).
  Re-register any that expired.
```

## C.3: Weekly briefing

Same structure as daily but:
- Calendar: 7-day window
- Tasks: all active lists
- Journal: review entries from past week
- Additional sections: last week summary, milestones hit/missed, responses owed, backlog review (>90 days flagged stale), recommended focus areas, initiative health summary

## C.4: Task extraction (standalone)

Same as meeting processing Step 10 but triggered independently. Input can be freeform text, email, or conversation. Always uses the numbered review list.

## C.5: Memory save (learn)

Same as meeting processing Step 11 but triggered independently. Always checks existing knowledge first. Always applies durability test. Always presents for review. Includes sentiment detection.

## C.6: Fast lookup (answer)

Source priority (updated for Issue 6):

```
1. Memory files (highest confidence)
2. Task notes
3. Journal entries (summaries)
4. Transcript archives (verbatim — for when summaries don't have the detail) [Issue 6]
5. Integration sources (calendar, project tracker)
6. Web search (lowest confidence — flag explicitly)
```

**Transcript fallback logic:**
When a question about a meeting discussion can't be answered from journal entries:
1. Identify relevant journal entries by date, person, topic
2. Read the `tars-transcript` property to find the linked transcript
3. Read the full transcript and search for the specific topic/quote
4. Return with citation: "From the raw transcript of [[2026-03-21 Platform Review]]:
   John said at 2:15pm: '...'"

## C.7: Inbox processing

```
STEP 1: Scan inbox
  obsidian search query="path:inbox/pending" limit=50
  If zero: "Inbox empty." Exit.

STEP 2: Classify each item
  For each file, read first ~50 lines (or read image if PNG/JPG via Read tool [Issue 5]):
  - Transcript/meeting notes → route to meeting processing
  - Screenshot/image → analyze content, determine context [Issue 5]
  - Article/link → route to wisdom extraction
  - PDF/document → create companion file [Issue 4], extract if possible
  - Task-like items → route to task extraction
  - Facts to remember → route to memory save
  - Mixed → split into components

STEP 3: Present inventory with classification [Issue 3]
  "5 items in inbox:
    1. ClientCo-sync-notes.txt — meeting transcript (detected: Otter format)
    2. IMG_2847.png — screenshot of Slack message from Sarah about API deadline
    3. api-patterns.pdf — research paper on API design
    4. quick-thought.md — notes about team offsite idea
    5. task-dump.md — task list from phone
  Process all? [all / pick specific / reclassify any]"

STEP 4: Process each item
  Route to appropriate workflow. Each workflow handles its own review gates.
  Between items: "Item 1 complete (2 tasks, 1 memory update). Item 2 of 5..."

STEP 5: Image processing specifics [Issue 5]
  For screenshots/images:
  a. Read image via Claude's multimodal capability
  b. Detect: meeting slide, email, chat conversation, document, whiteboard
  c. Check filesystem timestamp against calendar for concurrent meetings
  d. If meeting content → "This screenshot appears to be from your 2pm Platform Review.
     Associate with that meeting? [Y/N]"
  e. Extract text content, potential tasks, key information
  f. Create companion file with metadata

STEP 6: Mark processed
  obsidian property:set name="tars-inbox-processed" value="true" file="..."
  obsidian property:set name="tars-inbox-processed-date" value="YYYY-MM-DD" file="..."
  NEVER delete the original.

STEP 7: Summary + log to daily note
```

## C.8: Health check

```
STEP 1: Run validate-schema.py
  Check all tars-tagged notes against _system/schemas.yaml
  Report: missing properties, invalid enums, type mismatches

STEP 2: Run scan-secrets.py
  Scan memory/ and journal/ for blocked/warned patterns

STEP 3: Check broken wikilinks
  For each tars-tagged note, verify wikilinks resolve

STEP 4: Check alias consistency
  Verify registry matches actual note aliases properties

STEP 5: Check duplicate aliases
  Flag any alias mapping to multiple targets

STEP 6: Check stale content
  Query notes by staleness tier vs. last modified date

STEP 7: Present report with severity + fix options
  "7 issues (2 critical). Auto-fix all / Fix critical only / Review each?"

STEP 8: Log to daily note
```

## C.9: Maintenance/Housekeeping

```
STEP 1: Check housekeeping-state.yaml
  If last_run == today and not manual: skip

STEP 2: Archive sweep (script)
  GUARDRAIL: Never archive notes with incoming backlinks from last 90 days
  GUARDRAIL: Never archive notes referenced by active tasks
  Present archive candidates for user approval

STEP 3: Organize human-added files [Issue 4]
  Scan inbox/ and contexts/ for files without companion .md files
  For each orphan:
    Read file (image, PDF, etc.)
    Generate metadata + companion file
    Propose date-based organization and consistent naming
  Present: "3 unorganized files. Proposed:
    1. IMG_2847.png → contexts/2026-03/q1-roadmap-screenshot.png
    2. report.pdf → contexts/2026-03/vendor-evaluation-report.pdf
  Organize? [all / review each / skip]"

STEP 4: Flagged content review [Issue 8]
  Run scan-flagged.py to find all <!-- tars-flag:negative --> markers
  If any found (especially >90 days old):
  "4 flagged statements for review:
    1. [[Steve Chen]]: 'slow to deliver on migration' (flagged 2026-03-15, 6 days ago)
    2. [[Steve Chen]]: 'over-commits and under-delivers' (flagged 2026-02-28, 21 days ago) ⚠️
    3. [[Patty Kim]]: 'playing politics with reorg' (flagged 2026-03-10, 11 days ago)
    4. [[Dan Rivera]]: 'checked out since team change' (flagged 2026-01-05, 75 days ago) ⚠️ STALE
  Actions: 'remove 2, 4' / 'keep all' / 'soften 3' / 'remove all for Steve'"

STEP 5: Run health check (C.8)

STEP 6: Run sync check
  Calendar gaps: meetings in last 7 days without journal entries
  Task system: if external system configured, check for drift
  Memory staleness: people in recent meetings but not recently updated

STEP 7: Archive processed inbox items older than 7 days

STEP 8: Update housekeeping-state.yaml

STEP 9: Log to daily note
```

## C.10: Onboarding/Welcome

```
STEP 1: Check if vault is already set up
  If _system/config.md exists: "TARS is set up. Run health check?"

STEP 2: Create vault structure
  All folders, templates, system files, scripts, .base files

STEP 3: Configure integrations
  "Calendar? [Apple Calendar / Google Calendar / Outlook / None]"
  "Task manager? [Apple Reminders / Todoist / Linear / None]"

STEP 4: Initial context gathering
  "What's your role?" → _system/config.md
  "What team?" → org-context note
  "3-5 people you work with most?" → people notes
  "Main projects right now?" → initiative notes

STEP 5: Configure schedule [Issue 10]
  "Daily briefing time? [7:30am]"
  "Weekly briefing day/time? [Monday 8:00am]"
  "Maintenance time? [Friday 5:00pm]"
  Save to _system/config.md

STEP 6: Register cron jobs [Issue 10]
  CronCreate for each scheduled task
  Store job IDs in housekeeping-state.yaml

STEP 7: Initialize git repository
  git init, .gitignore, initial commit

STEP 8: Welcome summary
```

## C.11: Strategic analysis modes

See `TARS_V2_REBUILD_PLAN.md` Section 7.7 for complete Think Mode A-E specifications. No changes from Issue solutions except:
- All modes check existing vault knowledge before analyzing (Issue 7)
- All modes ask clarifying questions with multiple-choice when scope is unclear (Issue 3)
- Deep Analysis Chain (Mode D) saves intermediate artifacts to journal for resumability

## C.12: Communication drafting

See `TARS_V2_REBUILD_PLAN.md` Section 7.12. No changes except:
- Loads stakeholder memory and checks for flagged negative content (Issue 8) — does NOT surface flagged negativity in communication drafts

## C.13: Initiative planning + status

See `TARS_V2_REBUILD_PLAN.md` Functional spec #25-26. No changes except:
- Check existing initiatives before creating duplicates (Issue 7)
- Ask don't assume for stakeholder roles and priority (Issue 3)

---

# PART D: THE TEN REAL-WORLD ISSUE SOLUTIONS

This is a summary of how each issue is addressed. Implementation details are woven into the workflow specs above.

| # | Issue | Solution | Where in plan |
|---|-------|----------|--------------|
| 1 | Transcript format variability | Format detection step + MANDATORY calendar check + ask user if no match | C.1 Steps 2-3 |
| 2 | Task review UX | Numbered list with selection syntax (`all`, `1, 3, 7`, `all except 4`) for ALL meeting processing | C.1 Step 10 |
| 3 | Ask don't assume | Core principle: multiple-choice, batched, max 3-4, always check vault first | Part A principle 6, all workflows |
| 4 | File organization | Companion files + date-based dirs + consistent naming during maintenance | C.9 Step 3 |
| 5 | Quick capture (screenshots) | Multimodal image analysis + calendar context matching + inbox integration | C.7 Step 5 |
| 6 | Transcript-linked lookups | Archive transcripts + bidirectional links + fallback search in Answer skill | C.1 Steps 8-9, C.6 |
| 7 | Check before writing | Knowledge inventory step before all extraction: NEW/UPDATE/REDUNDANT/CONTRADICTS | C.1 Step 5, all write workflows |
| 8 | Negative statements cleanup | Sentiment detection + inline flags + periodic review report with numbered removal | C.1 Step 11, C.9 Step 4 |
| 9 | Self-evaluation backlog | Auto-detect errors (deduplicated) + capture user ideas + backlog base view | C.1 Step 14, _system/backlog/ |
| 10 | Scheduled tasks | CronCreate for briefings/maintenance + re-registration at session start | C.10 Steps 5-6, C.2 Step 6 |

---

# PART E: TRUST, SAFETY, AND GUARDRAILS

## Durability test (memory gate)

ALL four must pass before any memory write:

| # | Criterion | Question |
|---|-----------|----------|
| 1 | Lookup value | Will this be useful for lookup next week or next month? |
| 2 | Signal | Is this high-signal and broadly applicable? |
| 3 | Durability | Is this durable (not transient or tactical)? |
| 4 | Behavior change | Does this change how I should interact in the future? |

## Accountability test (task gate)

ALL three must pass:

| # | Criterion | Question |
|---|-----------|----------|
| 1 | Concrete | Is it a specific deliverable? (not "think about") |
| 2 | Owned | Is there a clear single owner? |
| 3 | Verifiable | Will we know objectively when it's done? |

## Knowledge check protocol (Issue 7)

Before any extraction workflow:

| Classification | Action |
|---------------|--------|
| NEW | Extract and present for review |
| UPDATE | Show diff, ask user to confirm |
| REDUNDANT | Skip silently, mention in summary |
| CONTRADICTS | Ask user which version is current |

## Sensitive data scanning

Block (redact, never persist): SSN, API keys, passwords, bearer tokens, JWTs, private keys, connection strings.
Warn (flag for review): DOB, salary, compensation, PIP, termination, diagnosis, lawsuit.
Negative sentiment (Issue 8): Flag with inline markers, periodic cleanup.

## Review gates

| Gate | When | UX |
|------|------|-----|
| Task creation | After extraction | Numbered list + selection syntax |
| Memory update | Before any write | Proposed facts + entity destinations |
| Participant resolution | Start of meeting processing | Resolved names with vault links |
| Calendar match | Meeting without date | Multiple-choice meeting list |
| Sensitive content | Warn pattern detected | Content snippet + options |
| Negative sentiment | Flagged statement | Confirm save with flag / rephrase / skip |
| Archive candidates | During maintenance | List for approval |
| Name disambiguation | Ambiguous alias | Multiple-choice people |

## Circuit breakers

| Condition | Action |
|-----------|--------|
| >20 files modified in single workflow | Pause, ask user to confirm |
| Memory file would exceed 200 lines | Suggest archival/summarization first |
| >3 consecutive obsidian-cli errors | Stop all operations, report status, log issue |
| Name resolution confidence <70% | Do not proceed, ask user |
| Transcript >15,000 words | Chunk into segments, process sequentially |

## Activity logging

Every workflow appends to daily note AND writes to `_system/changelog/YYYY-MM-DD.md` with batch_id for rollback.

---

# PART F: TESTING AND VALIDATION

## Smoke tests (every session start)

1. `obsidian version` → obsidian-cli is available
2. `obsidian search query="tag:tars" limit=1` → vault accessible and non-empty
3. `_system/schemas.yaml` → exists and parses
4. `_system/alias-registry.md` → exists and parses
5. Daily note → accessible
6. CronList → verify scheduled jobs active, re-register if expired [Issue 10]

## Schema validation tests

- Every type in `schemas.yaml` has valid and invalid fixture examples in `tests/fixtures/`
- `validate-schema.py` runs against fixtures and full vault
- After every batch of changes: re-run validation to catch drift

## Integration tests (require obsidian-cli running)

- `create` + `read` round-trip: content matches
- `property:set` modifies frontmatter without corrupting body
- `search` returns expected results for known content
- `append` does not overwrite existing content
- Error handling: graceful failure when target doesn't exist

## End-to-end tests

1. **Meeting processing**: Transcript in → format detected → calendar checked → journal + tasks (user-selected) + memory (user-approved) out, transcript archived with backlink
2. **Task review UX**: 10+ extracted tasks → numbered list → user selects subset → only selected created
3. **Transcript lookup** [Issue 6]: Ask about minor point → summary doesn't have it → agent finds it in archived transcript
4. **Knowledge check** [Issue 7]: Process transcript with redundant info → agent skips what's already known, shows UPDATE diffs
5. **Name resolution** [Issue 3]: Ambiguous "Dan" → agent asks with multiple-choice → correct Dan selected
6. **Image processing** [Issue 5]: Screenshot in inbox → agent reads image → extracts content → associates with concurrent meeting
7. **Negative statement review** [Issue 8]: Flag detected during write → periodic report → user removes selected items
8. **Self-evaluation** [Issue 9]: MCP error → auto-logs to backlog → does not duplicate on repeat
9. **Cron scheduling** [Issue 10]: CronCreate fires → briefing generated → saved to journal → cron jobs verified
10. **File organization** [Issue 4]: Orphan PDF in contexts/ → companion file created → proposed rename and reorganization
11. **Schema enforcement**: Invalid frontmatter → `validate-schema.py` catches → agent refuses to write
12. **Secret scanning**: Content with API key → scan-secrets.py blocks → content redacted before write
13. **Daily briefing**: References correct calendar, people context, due tasks, data freshness footer

## Regression tests

- After every batch: run `validate-schema.py` against full vault
- After meeting processing: verify all wikilinks resolve
- After maintenance: verify no active content was archived (check backlinks)

---

# PART G: PHASED BUILD SEQUENCE

## Pre-build

```bash
git checkout -b tars-3.0 main
```

## Phase 1: Foundation (must-have, build in this order)

| # | Item | Files to create | Issues addressed |
|---|------|----------------|-----------------|
| 1 | **Vault scaffolding** | All folders, `_system/` files (config, integrations, alias-registry, taxonomy, kpis, schedule, guardrails.yaml, maturity.yaml, housekeeping-state.yaml, schemas.yaml, changelog/) | Structure for all |
| 2 | **Templates** | All `templates/*.md` (14 templates including companion, transcript, issue, idea) | #4, #6, #9 |
| 3 | **Base views** | All `_views/*.base` (17 base files) | #4, #6, #8, #9 |
| 4 | **Schema validation script** | `scripts/validate-schema.py` | — |
| 5 | **Secret scanning script** | `scripts/scan-secrets.py`, `_system/guardrails.yaml` | — |
| 6 | **Flagged content scanner** | `scripts/scan-flagged.py` | #8 |
| 7 | **Core skill** | `skills/core/SKILL.md`, `CLAUDE.md` | #3 (ask don't assume), #7 (knowledge check), #9 (error-to-issue protocol) |
| 8 | **Alias registry + name resolution** | `_system/alias-registry.md`, resolution protocol in core skill | #3 |
| 9 | **Onboarding wizard** | `skills/welcome/SKILL.md` | #10 (cron registration) |
| 10 | **Memory save (learn)** | `skills/learn/SKILL.md` | #7 (check existing), #8 (sentiment detection) |
| 11 | **Task extraction** | `skills/tasks/SKILL.md` | #2 (numbered review UX) |
| 12 | **Meeting processing** | `skills/meeting/SKILL.md` | #1, #2, #3, #6, #7, #8 |
| 13 | **Daily briefing** | `skills/briefing/SKILL.md` | #10 (cron-triggered) |
| 14 | **Fast lookup** | `skills/answer/SKILL.md` | #6 (transcript fallback) |
| 15 | **Health check + maintenance** | `skills/maintain/SKILL.md`, `scripts/health-check.py` | #4 (file org), #5 (images), #8 (flagged review), #9 (auto-detection) |
| 16 | **Activity logging** | Changelog + daily note patterns in all skills | — |
| 17 | **Smoke test suite** | `tests/smoke-tests.py` | — |

## Phase 2: High-value expansion

| # | Item | Files |
|---|------|-------|
| 18 | Weekly briefing | `skills/briefing/SKILL.md` (weekly mode) |
| 19 | Inbox processing | `skills/maintain/SKILL.md` (inbox mode, including image pipeline) |
| 20 | Strategic analysis (Think A) | `skills/think/SKILL.md` |
| 21 | Validation council (Think B) | `skills/think/SKILL.md` |
| 22 | Communication drafting | `skills/communicate/SKILL.md`, `skills/communicate/text-refinement.md` |
| 23 | Sync | `scripts/sync.py` |
| 24 | Archive management | `scripts/archive.py` |

## Phase 3: Advanced

| # | Item | Files |
|---|------|-------|
| 25 | Executive council (Think C) | `skills/think/manifesto.md` |
| 26 | Deep analysis chain (Think D) | `skills/think/SKILL.md` |
| 27 | Discovery mode (Think E) | `skills/think/SKILL.md` |
| 28 | Initiative planning + status | `skills/initiative/SKILL.md` |
| 29 | Wisdom extraction | `skills/learn/SKILL.md` (wisdom mode) |
| 30 | Artifact creation | `skills/create/SKILL.md` |
| 31 | Canvas generation | `_views/initiative-map.canvas` |

---

# PART H: MIGRATION CONSIDERATIONS

**This section is for future planning only.** A separate migration plan will be built after TARS 3.0 is functional.

Existing TARS v2 deployments have data that needs to migrate:

| Data type | Current location | v3 destination | Migration notes |
|-----------|-----------------|----------------|-----------------|
| Memory files | `memory/{category}/` | Same structure, new frontmatter | Add `tars-` prefixed properties, add tags, remove `_index.md` files |
| Journal entries | `journal/YYYY-MM/` | Same structure, new frontmatter | Add tags, normalize type values, add `tars-transcript` links where applicable |
| Context files | `contexts/` | `contexts/YYYY-MM/` + companions | Reorganize by date, create companion files for non-markdown |
| Inbox items | `inbox/{pending,processing,completed,failed}/` | `inbox/{pending,processed}/` | Simplify folder structure |
| Archive | `archive/{tier}/` | `archive/` (flat) + `archive/transcripts/` | Flatten tiers, preserve staleness in frontmatter |
| Reference files | `reference/` | `_system/` | Rename, merge config into config.md |
| Indexes | `memory/*/_index.md`, `journal/*/_index.md` | Deleted (replaced by .base) | Remove all index files |
| Replacements | `reference/replacements.md` | `_system/alias-registry.md` | Restructure with context disambiguation |
| CLAUDE.md | Root | Root (updated) | Rewrite for v3 skill loading |
| Scripts | `scripts/` | `scripts/` | Port to new schema format |
| Tests | `tests/` | `tests/` | Rewrite for new structure |

Key migration requirements:
- Must be non-destructive (backup original vault first)
- Must validate all migrated notes against new schemas
- Must regenerate all wikilinks for renamed entities
- Must be idempotent (safe to run multiple times)
- Must produce a migration report showing what changed

---

## Appendix: Reference documents

| Document | Purpose |
|----------|---------|
| `TARS_REBUILD_FOUNDATION.md` | Original analysis of v1/v2 strengths, weaknesses, and rebuild recommendations |
| `TARS_V2_REBUILD_PLAN.md` | Detailed technical reference: all frontmatter schemas, .base YAML, script patterns, integration architecture, failure modes |
| This plan (`TARS_V3_REBUILD_PLAN.md`) | Authoritative execution guide for the agent building TARS 3.0 |

