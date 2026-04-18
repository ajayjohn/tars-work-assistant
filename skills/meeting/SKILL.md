---
name: meeting
description: Process meeting transcripts into journal entries, tasks, and memory updates
triggers: ["process this meeting", "meeting transcript", "meeting notes"]
---

# Meeting processing pipeline

The highest-value workflow in TARS. Transforms raw meeting transcripts into structured journal entries, actionable tasks, and durable memory updates through a 14-step pipeline (plus a 7b nuance-capture sub-step) with mandatory user review gates.

All vault writes go through `mcp__tars_vault__*` tools (see `skills/core/SKILL.md` → "Write interface"). All integration calls resolve via `mcp__tars_vault__resolve_capability` — never hard-code `mcp__apple_*` or `mcp__microsoft_365_*`. All names use canonical forms from the alias registry. All persistence requires user confirmation.

**Hooks now enforce** `tars-` prefix, content chunking, alias-registry load, changelog writes, and telemetry. The pipeline body below describes intent; the MCP server handles validation and logging. Legacy `obsidian-cli` examples map 1:1 to the `mcp__tars_vault__*` tools in the core skill's write-interface table.

---

## Pipeline overview

```
Steps 1-6:   Preparation (load context, detect format, resolve calendar/participants, check knowledge, scan secrets)
Step 7:      Processing (LLM analysis of transcript)
Step 7b:     Nuance capture (second Haiku pass over raw transcript — safety net)
Steps 8-9:   Persistence (journal entry + transcript archive)
Steps 10-11: Extraction with review (tasks + memory, user confirms each)
Steps 12-14: Cleanup (unresolved names, daily note, self-evaluation)
```

---

## Step 1: Load alias registry (handled by server)

The `tars-vault` MCP server holds the alias registry in-process (invalidated on file-mtime change). Name-resolution calls (`mcp__tars_vault__resolve_alias`) use the cache. If the SessionStart hook has run this session, the canonical-names head is already in additionalContext. No explicit load is required — call `mcp__tars_vault__resolve_alias(name="…")` whenever a speaker label, attendee, or entity reference needs canonicalization.

---

## Step 2: Detect transcript format (Issue 1)

Inspect the raw transcript and classify its format and available metadata.

### Format classification

| Format | Identifying signals |
|--------|-------------------|
| `otter` | "Otter.ai" header, `Speaker N` labels, MM:SS timestamps |
| `fireflies` | "Fireflies.ai" header, structured JSON with `SPEAKER`/`LINE_TEXT` fields |
| `zoom` | "WEBVTT" header or Zoom chat export format |
| `teams` | Microsoft Teams transcript format, `<v>` tags or Teams metadata |
| `raw_text` | Speaker labels present but no platform markers |
| `unknown` | No recognizable structure |

### Metadata inventory

Produce a checklist of what the transcript provides:

```
Format: [detected format]
Has date:             yes/no
Has duration:         yes/no
Has attendees header: yes/no
Has speaker labels:   yes/no
Has timestamps:       yes/no
```

Fill in whatever the transcript provides. Missing fields will be resolved in subsequent steps. Do not guess missing values.

---

## Step 3: MANDATORY calendar check (Issue 1)

ALWAYS query the calendar, even when the transcript provides a date. Calendar data is authoritative for meeting title, full attendee list (including silent participants), organizer, and precise time.

### Resolve the calendar provider first

```
cap = mcp__tars_vault__resolve_capability(capability="calendar")
# use cap.tools[*].name dynamically — never hard-code mcp__apple_calendar__* or mcp__microsoft_365_*
```

If `cap.status == "unavailable"` and `calendar.required: true` in `_system/integrations.md`, halt with a clear message. Otherwise degrade to transcript-provided date + user confirmation.

### Step 3b: Meeting-recording check (optional)

If `resolve_capability(capability="meeting-recording")` returns a connected provider and the user did not paste a transcript, propose:
```
Import transcript from "<recording title>" (<recording URL>)?
```
Uses whichever tool the resolver returns (Minutes.app, Otter, Fireflies, etc.).

### Query logic

**a. Transcript has a date:**
Use the transcript date to define a narrow calendar query window (that day, +/- 1 day).

**b. Transcript lacks a date:**
Query the past 3 business days from today.

**c. Match criteria:**
Score each calendar event against the transcript using:
- Title keyword overlap with transcript topics/header
- Attendee name overlap with transcript speakers
- Time window alignment with any timestamps in transcript
- Duration alignment if transcript has duration metadata

### Resolution flow

**d. Single strong match:**
Present for confirmation with a binary question.
```
This appears to be the "Q1 Planning Sync" from Mon 2026-03-16 at 10:00am. Correct? [Y/N]
```

**e. Multiple matches (Issue 3):**
Present as a multiple-choice list.
```
Which meeting is this transcript from?
  1. Mon 2026-03-16, 10:00am -- "Q1 Planning" with Jane Smith, Bob Chen
  2. Tue 2026-03-17, 2:00pm -- "Platform Review" with Sarah Lopez
  3. None of these -- I'll specify
```

**f. No match and calendar unavailable:**
Ask the user directly.
```
When did this meeting happen? (e.g., "yesterday at 2pm" or "2026-03-19")
```

**g. NEVER proceed without a resolved date and time.** The pipeline halts here until date/time is confirmed.

### Extract from calendar

Once matched, extract and carry forward:
- Complete attendee list (for participant resolution in Step 4)
- Meeting time (for `tars-meeting-datetime` frontmatter)
- Organizer name
- Calendar meeting title (authoritative source for filename and journal title)

---

## Step 4: Resolve participants (Issue 3)

Merge two participant sources into one canonical list:
1. Speaker labels from the transcript
2. Attendee list from the calendar event (Step 3)

### Resolution cascade for each name

**Pass 1: Alias registry**
Check the alias registry loaded in Step 1 for an exact match or known variation. If found, map to canonical form.

**Pass 2: Vault search**
```
mcp__tars_vault__search_by_tag(tag="tars/person", query="<name>", limit=5)
```
If the name matches exactly one person note, use it.

**Pass 3: Contextual disambiguation**
If ambiguous (multiple candidates), use context clues:
- Calendar attendees narrow the pool to people actually present
- Transcript context: role references ("the PM said"), team mentions, topic expertise
- Memory files: recent interactions, team membership

**Pass 4: Ask the user**
If any names remain unresolved after passes 1-3, batch ALL unresolved names into a single interaction.

For ambiguous names, present multiple-choice:
```
Who is "Dan" in this meeting?
  1. Dan Rivera (Engineering)
  2. Dan Chen (Infrastructure)
  3. Someone new -- I'll provide details
```

For unknown names, ask directly:
```
Who is "Mick"? Please provide their full name.
```

### Confirm participant list

Present the final resolved participant list for confirmation before proceeding:
```
Participants resolved:
  - Jane Smith (from calendar + transcript)
  - Bob Chen (from calendar + transcript)
  - Sarah Lopez (from calendar only, silent in transcript)
  - You

Correct? [Y / Edit]
```

NEVER use generic speaker labels ("Speaker 1", "Unknown") in any output.

---

## Step 5: Knowledge inventory (Issue 7)

Before extracting anything, check what the vault already knows about the entities and topics in this transcript.

### Vault scan

For each person, initiative, decision, or topic identified in the transcript:

```
mcp__tars_vault__search_by_tag(tag="tars/person",     query="<entity>", limit=5)
mcp__tars_vault__search_by_tag(tag="tars/initiative", query="<entity>", limit=5)
mcp__tars_vault__search_by_tag(tag="tars/decision",   query="<entity>", limit=5)
```

Phase 4 adds `mcp__tars_vault__fts_search` and `mcp__tars_vault__semantic_search` for paraphrase/prose matching over journal + transcripts + contexts.

### Classification

Classify each piece of information from the transcript against existing vault knowledge:

| Classification | Meaning | Action |
|---------------|---------|--------|
| `NEW` | Not in the vault at all | Include in extraction |
| `UPDATE` | Exists but transcript has newer/additional info | Show diff in Step 11 |
| `REDUNDANT` | Already captured with same detail | Skip silently |
| `CONTRADICTS` | Transcript says X, vault says Y | Flag for user resolution in Step 11 |

### Report to user

```
Knowledge check:
  - Jane Smith: 12 entries in memory. Last updated 2026-03-15.
  - Platform Rewrite: active initiative, 8 related entries.
  - "REST vs GraphQL": decision already recorded (2026-02-28).
  Will focus on what's new or changed.
```

If processing a batch of transcripts chronologically, note the position:
```
This is transcript 2 of 5. Later transcripts will supersede earlier ones on overlapping topics.
```

---

## Step 6: Secret scan

Run the secrets scanner against transcript content BEFORE any vault writes.

```
mcp__tars_vault__scan_secrets(content="<transcript_content>")
```

Returns JSON: `{block: [...], warn: [...], negative_sentiment: [...]}`. The MCP server also runs `scan_secrets` internally before every write via `PreToolUse` hook; the pre-write call here is belt-and-braces so redaction happens before the transcript is echoed back to the user.

### Block patterns (halt and redact)
- Social Security numbers
- API keys and tokens
- Passwords and credentials
- Connection strings
- Credit card numbers

### Warn patterns (flag for review)
- Dates of birth
- Salary and compensation figures
- PIP (performance improvement plan) references
- Termination details
- Medical diagnoses

**If blocked:** Redact the sensitive content and notify the user. Do not proceed with the redacted content without confirmation.

**If warned:** Flag the content for user review. Present the flagged items and ask whether to include, redact, or rephrase before proceeding.

---

## Step 7: Process transcript (LLM reasoning)

Analyze the transcript and produce structured output for ALL of the following sections. Do not skip any section. If a section has no content, state "None identified."

### Topics
- Discussion points as bullet points
- Infer the meeting type but do NOT state it explicitly

### Updates
- Status updates from anyone OTHER than the user
- Be specific: names, projects, dates, deliverables

### Concerns
- Risks raised, formatted as WHO / ISSUE / DEADLINE
- Include both explicit risks and implied risks from context

### Decisions
- What was decided, who made the call, and rationale if stated
- Distinguish firm decisions from tentative agreements

### Action items
Classify into:
- **For me**: Tasks the user committed to
- **For others**: Tasks assigned to specific people
- **Unassigned**: Tasks that need doing but have no clear owner

Format: **"Owner"** -- Task description (deadline if stated)

### Unresolved items
- Topics discussed without reaching a conclusion
- Questions raised but not answered
- Items explicitly deferred ("let's revisit next week")

### Key quotes
- Notable statements attributed to specific speakers
- Include approximate timestamp if available
- Focus on statements that carry weight: commitments, concerns, strategic direction

---

## Step 7b: Nuance capture pass (PRD §6.8)

Directly addresses the top-declared retrieval pain: summaries miss nuance,
contrarian views, specific phrases, and quantitative claims. Runs AFTER
Step 7 and BEFORE Step 8 so the nuance section lands in the same journal
entry as the main summary.

### When to run

- Always, when the raw transcript is available.
- Skip with a telemetry note (`meeting_nuance_skipped`, reason) only if the
  transcript was unavailable (e.g., meeting-recording import produced summary
  only) or was <500 words total. The nuance pass is cheap enough (~1 extra
  Haiku call) that it should run by default.

### How to run

Spawn a sub-agent with `subagent_type="general-purpose"`, model Haiku,
`max_turns=1`, temperature `0.2`. Feed it the verbatim prompt from
`skills/meeting/reference/nuance-pass-prompt.md`, substituting
`{{TRANSCRIPT_TEXT}}` with the full raw transcript (before any archival
chunking). The prompt requires a single JSON object back.

### What the JSON contains

Six arrays, any of which may be empty:

| Key | Content |
|-----|---------|
| `notable_phrases` | Verbatim phrases the summary dropped. Speaker + quote + nearby text for grep. |
| `contrarian_views` | Statements contradicting the dominant summary sentiment. |
| `specific_quotes` | Quotes worth preserving verbatim with rationale. |
| `unusual_technical_terms` | Jargon worth indexing with speaker + context sentence. |
| `emotional_strong_statements` | Strong emotional statements with emotion type. |
| `numbers_and_dates_missed` | Quantitative claims absent from the summary. |

Never apply durability / accountability filtering here — those gates run on
persistence, not capture. Over-capture is the design intent.

### How it lands in the journal

The nuance JSON is rendered beneath the main summary as a `## Notable phrases & perspectives` section. Suggested layout (omit empty sub-headings):

```markdown
## Notable phrases & perspectives

### Notable phrases
- **Jane Smith** (~12:14): "we've been papering over this for six months"
- **Bob Chen** (~23:02): "that's technically a rewrite, not a refactor"

### Contrarian views
- **Sarah Lopez**: pushed back on the REST-over-GraphQL decision — "we'll regret this when the mobile team gets here"
  > Quote: "we'll regret this when the mobile team gets here"

### Specific quotes worth preserving
- **Jane Smith**: "the whole reason we did the Q1 rewrite was to avoid exactly this conversation" — captures the frustration behind the roadmap reset

### Unusual technical terms
- **idempotency fences** (Bob Chen): raised in the context of the retry-queue redesign

### Strong emotional statements
- **Sarah Lopez** (frustration): "I've been asking for this for eight months"

### Numbers & dates missed
- 2026-06-30 — vendor contract renewal (mentioned once by Jane, absent from summary)
- $340k — projected savings from consolidation (Bob's estimate)
```

Nothing in this section is persisted to memory automatically. It lives in the
journal as a searchable reading of the room. Memory extraction (Step 11) still
runs its own durability gate on any item the user later promotes.

### Failure handling

Failure here **must not** block the pipeline:

- JSON parse error, non-JSON response, or sub-agent error → skip the nuance
  section and emit telemetry event `meeting_nuance_failed` with the error
  string. Proceed to Step 8 as if 7b never ran.
- Empty JSON (all arrays empty) → still append the section heading with "No
  nuance flagged." so the user can see the pass ran. Emit
  `meeting_nuance_captured` with counts (all zero).

### Telemetry

On success emit `meeting_nuance_captured` with counts per category:

```json
{
  "event": "meeting_nuance_captured",
  "counts": {
    "notable_phrases": 4,
    "contrarian_views": 1,
    "specific_quotes": 2,
    "unusual_technical_terms": 3,
    "emotional_strong_statements": 1,
    "numbers_and_dates_missed": 2
  }
}
```

`/lint` can later surface meetings where the nuance pass returned all-zero
counts — often a symptom of a malformed transcript rather than a thin meeting.

---

## Step 8: Create journal entry (Issue 6)

```
mcp__tars_vault__create_note(
  name="YYYY-MM-DD Meeting Title",
  path="journal/YYYY-MM/YYYY-MM-DD-meeting-slug.md",
  template="meeting-journal",
  frontmatter={...},
  body="..."
)
```

If `template=` is not available for the meeting-journal template in the user's vault, the server falls back to `mcp__tars_vault__write_note_from_content` automatically. Auto-chunking applies when body >40KB.

### Frontmatter properties

The `create_note` call takes the full frontmatter inline. Values:

```yaml
---
tags: [tars/journal, tars/meeting]
tars-date: YYYY-MM-DD
tars-meeting-datetime: YYYY-MM-DDTHH:MM:SS
tars-participants: ["[[Jane Smith]]", "[[Bob Chen]]"]
tars-organizer: "[[Jane Smith]]"
tars-topics: [topic-slug-1, topic-slug-2]
tars-initiatives: ["[[Platform Rewrite]]"]
tars-source: calendar | transcript
tars-calendar-title: "Original Calendar Title"
tars-transcript: "[[YYYY-MM-DD-meeting-slug-transcript]]"
tars-transcript-format: otter | fireflies | zoom | teams | raw_text
tars-created: YYYY-MM-DD
---
```

### Body content

Append the structured report from Step 7 to the journal entry body:

```markdown
# Meeting Title
**Date:** YYYY-MM-DD | **Time:** HH:MM | **Participants:** [[Jane Smith]], [[Bob Chen]]
**Initiatives:** [[Platform Rewrite]]

## Topics
[From Step 7]

## Updates
[From Step 7]

## Concerns
[From Step 7]

## Decisions
[From Step 7]

## Action items
[From Step 7]

## Unresolved items
[From Step 7]

## Key quotes
[From Step 7]

## Notable phrases & perspectives
[From Step 7b — omit if the nuance pass was skipped; keep heading if pass ran with zero findings]

## Associated captures
[Screenshots and images related to this meeting, if any]
```

### Title and slug generation

**Title priority:**
1. Calendar meeting title (authoritative when available)
2. Transcript header/title (fallback)
3. Context-inferred title (last resort)

**Slug rules:**
- Lowercase, hyphenated
- Remove filler words (the, a, an, and, or, for, to, in, on, at, of)
- Example: "MCP Planning Session" becomes `mcp-planning`

When the calendar title differs from the transcript header, keep `tars-calendar-title` in frontmatter for reference.

---

## Step 9: Archive transcript (Issue 6)

Move the original transcript to the archive with a standardized filename and bidirectional links.

### Create archived transcript

```
mcp__tars_vault__create_note(
  name="YYYY-MM-DD-meeting-slug-transcript",
  path="archive/transcripts/YYYY-MM/YYYY-MM-DD-meeting-slug-transcript.md",
  template="transcript",
  frontmatter={
    "tags": ["tars/transcript"],
    "tars-journal-entry": "[[YYYY-MM-DD Meeting Title]]",
    "tars-date": "YYYY-MM-DD",
    "tars-meeting-datetime": "YYYY-MM-DDTHH:MM:SS",
    "tars-participants": ["[[Jane Smith]]", "[[Bob Chen]]"],
    "tars-format": "otter",
    "tars-created": "YYYY-MM-DD"
  }
)
```

### Append raw transcript content

```
mcp__tars_vault__append_note(
  file="YYYY-MM-DD-meeting-slug-transcript",
  content="<full raw transcript text>"
)
```
The server auto-chunks at 40KB boundaries so arbitrarily large transcripts persist cleanly.

### Bidirectional links

- The journal entry's `tars-transcript` property points to the archived transcript
- The archived transcript's `tars-journal-entry` property points back to the journal entry

**NEVER delete the original transcript.** Archive it, link it, preserve it.

---

## Step 10: Extract tasks with review (Issue 2)

Every task candidate goes through the accountability test. The user always sees and selects which tasks to create.

### Accountability test

For each potential action item from Step 7, test ALL three criteria:

| Criterion | Question | Pass example | Fail example |
|-----------|----------|-------------|-------------|
| Concrete | Is it a specific deliverable? | "Review hiring plan" | "Think about Q4" |
| Owned | Does it have a clear single owner? | "Bob will send the report" | "The team needs to align" |
| Verifiable | Will we know when it's done? | "Share migration report by Friday" | "Stay on top of things" |

All three must pass. If any criterion fails, the item is filtered out.

### Present numbered review list

Always present ALL candidates, showing both kept and filtered items:

```
15 potential tasks found. 8 pass the accountability test:

  1. [KEEP] Review hiring plan (you, due 2026-03-25, high)
  2. [KEEP] Share migration report (Bob Chen, due 2026-03-24, medium)
  3. [KEEP] Update API documentation (you, due 2026-03-28, medium)
  4. [KEEP] Schedule vendor demo (Sarah Lopez, due 2026-03-26, low)
  5. [KEEP] Draft budget proposal (you, due 2026-03-31, high)
  6. [KEEP] Send test results to QA (Bob Chen, due 2026-03-25, medium)
  7. [KEEP] Review platform architecture doc (you, due 2026-03-28, low)
  8. [KEEP] Follow up with Sarah on API timeline (you, due 2026-03-28, low)

  -- Filtered out --
   9. "We should think about Q4" -- no owner, not concrete
  10. "The team needs to align on priorities" -- no specific owner
  11. "Keep an eye on the timeline" -- not verifiable
  12. "Stay on top of vendor responses" -- not concrete
  13. "Someone should look into that" -- no owner
  14. "We need to be more proactive" -- not concrete, not verifiable
  15. "Let's circle back on that" -- not concrete

Which to create?
  - "all" to create 1-8
  - "1, 3, 7" to keep specific ones
  - "all except 4" to exclude specific ones
  - "move 10 to keep" to override a filter decision
  - "none" to skip all
```

### Create selected tasks

After the user responds, create ONLY the selected tasks using the tasks skill protocol:

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
    "tars-priority": "high",
    "tars-source": "[[YYYY-MM-DD Meeting Title]]",
    "tars-created": "YYYY-MM-DD"
  }
)
```

### Task placement logic

| Condition | Category |
|-----------|----------|
| Has due date, owner is user | Active |
| Has due date, owner is someone else | Delegated |
| No due date | Backlog |

### Date resolution

| User says | Resolution |
|-----------|------------|
| "today" | Current date YYYY-MM-DD |
| "tomorrow" | Current date + 1 day |
| "this week" | Thursday of current week |
| "next week" | Monday of next week |
| "Friday" / "next Friday" | First occurrence of that day after today |
| "end of month" | Last day of current month |
| "later" / no date | Backlog (no due date) |

NEVER use relative dates in output. Always resolve to YYYY-MM-DD.

---

## Step 11: Extract memory with review (Issues 7, 8)

Memory persistence requires passing the durability test, checking against existing knowledge, handling negative sentiment, and getting user confirmation.

### Durability test

All 4 criteria must pass:

| Criterion | Question |
|-----------|----------|
| Lookup value | Will this be useful for lookup next week or next month? |
| Signal | Is this high-signal and broadly applicable? |
| Durability | Is this durable, not transient or tactical? |
| Behavior change | Does this change how TARS should interact in the future? |

**Pass examples:** "Jane now leads both platform and mobile teams." / "Vendor contract renews June 2026." / "Decision: REST over GraphQL for public API."

**Fail examples:** "Meeting rescheduled to Thursday." / "Bob will send the report by Friday." / "We discussed the timeline."

### Knowledge check (Issue 7)

For each item passing the durability test, compare against the vault inventory from Step 5:

| Classification | Action |
|---------------|--------|
| `NEW` | Include in the review list |
| `UPDATE` | Show diff: "Current: 'Jane leads platform.' Update to: 'Jane leads platform and mobile.' Save update?" |
| `REDUNDANT` | Skip: "Already in memory. Skipping." |
| `CONTRADICTS` | Ask: "Memory says REST. Transcript says GraphQL. Which is current?" |

### Negative sentiment detection (Issue 8)

Scan proposed memory updates for negative patterns:
- Performance concerns: slow, underperforming, missing deadlines, unreliable
- Interpersonal: difficult, political, confrontational, unresponsive
- Capability: struggling, not up to speed, out of depth

When negative sentiment is detected, present with options:

```
This about Steve has negative sentiment: "Steve has been slow to deliver on infrastructure commitments."
Save with flag for periodic review? [Y / Rephrase / Skip]
```

**If saved with flag:**
- Wrap the content in markers: `<!-- tars-flag:negative YYYY-MM-DD -->content<!-- end-tars-flag -->`
- Set `tars-has-flagged-content: true` on the person's note via `obsidian property:set`
- Flagged content appears in the `_views/flagged-content.base` for periodic cleanup

**If rephrase:** Ask user for alternative wording and save the rephrased version without a flag.

**If skip:** Do not persist.

### Present review list with selection syntax

```
Proposed memory updates:
  1. [[Jane Smith]]: Now leads both platform and mobile teams (UPDATE -- was platform only)
  2. [[Bob Chen]]: Concerned about Q3 timeline, may need additional hires (NEW)
  3. [[Platform Rewrite]]: Decision to use REST over GraphQL for public API (NEW decision)
  4. [[Steve Park]]: Slow to deliver on infrastructure [FLAGGED -- negative sentiment]

  -- Skipped --
  5. "We discussed the roadmap" -- failed durability test (no specific insight)
  6. "Jane mentioned the Q1 results" -- redundant (already in memory from 2026-03-15)

Save? [all / 1, 3 / none / edit #2]
```

### Persist confirmed updates

For each confirmed memory update:

**New person/entity notes:**
```
mcp__tars_vault__create_note(
  name="Entity Name",
  path="memory/<type>/entity-name.md",
  template="<type>",
  frontmatter={"tags": ["tars/<type>"], "tars-created": "YYYY-MM-DD"}
)
```

**Updates to existing notes:**
```
mcp__tars_vault__append_note(
  file="Entity Name",
  content="## Update YYYY-MM-DD\n[New information from meeting]\nSource: [[YYYY-MM-DD Meeting Title]]"
)
mcp__tars_vault__update_frontmatter(file="Entity Name", property="tars-modified", value="YYYY-MM-DD")
```

**New decisions:**
```
mcp__tars_vault__create_note(
  name="Decision Title",
  path="memory/decisions/decision-slug.md",
  template="decision",
  frontmatter={"tags": ["tars/decision"], "tars-date": "YYYY-MM-DD", "tars-created": "YYYY-MM-DD"}
)
```

### Memory folder mapping

| Type | Folder |
|------|--------|
| Person | `memory/people/` |
| Vendor | `memory/vendors/` |
| Competitor | `memory/competitors/` |
| Product | `memory/products/` |
| Initiative | `memory/initiatives/` |
| Decision | `memory/decisions/` |
| Org context | `memory/org-context/` |

---

## Step 12: Scan for unresolved names

After all writes are complete, scan every wikilink in the journal entry and any newly created/updated notes.

For any wikilink that does not resolve to an existing note:

```
mcp__tars_vault__append_note(
  file="alias-registry",
  content="| <Unresolved Name> | ?? (needs full name) |"
)
```

The `mcp__tars_vault__create_note` / `append_note` tools also run the auto-wikilink pass (§3.3) — ambiguous name candidates are returned for batched user review, never auto-linked silently.

Report all unresolved names in the output summary.

---

## Step 13: Daily-note + changelog (handled by PostToolUse hook)

The `PostToolUse` hook appends a structured entry to `_system/changelog/YYYY-MM-DD.md` on every successful vault mutation (skill, tool, file, batch_id, timestamp). Daily-note appends are batched by the same hook.

Skills no longer emit per-workflow changelog entries. If richer batch context is needed (e.g., "this was meeting processing for transcript X"), emit a telemetry event via the MCP server rather than writing to the changelog directly.

Emit at minimum: `meeting_processed`, `tasks_proposed`, `memory_proposed`.

---

## Step 14: Self-evaluation (Issue 9)

If any errors occurred during the pipeline (failed calendar lookup, obsidian-cli error, script failure, unresolved ambiguity):

### Check for existing issue

```
mcp__tars_vault__search_by_tag(tag="tars/issue", query="<error-signature-keywords>", limit=5)
```

### If existing issue found

```
mcp__tars_vault__update_frontmatter(file="<issue-note>", property="tars-occurrence-count", value="<n+1>")
mcp__tars_vault__update_frontmatter(file="<issue-note>", property="tars-last-seen",       value="YYYY-MM-DD")
mcp__tars_vault__append_note(file="<issue-note>",
  content="## Occurrence YYYY-MM-DD\n<Error context from this run>")
```

Note: the `PostToolUse` hook also auto-dedupes framework-level MCP failures into `_system/backlog/issues/`. This step is for pipeline-level errors (missed calendar match, unresolved attendee, secret-scan block) that the hook wouldn't see.

### If new issue

```
mcp__tars_vault__create_note(
  name="Issue: <Brief Description>",
  path="_system/backlog/issues/issue-slug.md",
  template="issue",
  frontmatter={
    "tags": ["tars/backlog", "tars/issue"],
    "tars-issue-type": "cli-error",
    "tars-severity": "warning",
    "tars-occurrence-count": 1,
    "tars-first-seen": "YYYY-MM-DD",
    "tars-last-seen": "YYYY-MM-DD",
    "tars-status": "open",
    "tars-context": "Meeting processing, <step where error occurred>",
    "tars-created": "YYYY-MM-DD"
  }
)
```

---

## Output summary

End every meeting processing run with this summary, regardless of whether all steps succeeded:

```markdown
---
## Meeting processed

**Journal:** `journal/YYYY-MM/YYYY-MM-DD-meeting-slug.md`
**Transcript:** `archive/transcripts/YYYY-MM/YYYY-MM-DD-meeting-slug-transcript.md`

## Task extraction
| # | Task | Owner | Due | Category | Status |
|---|------|-------|-----|----------|--------|
| 1 | Review hiring plan | You | 2026-03-25 | Active | Created |
| 2 | Share migration report | Bob Chen | 2026-03-24 | Delegated | Created |

## Memory updates
| Action | Entity | Summary |
|--------|--------|---------|
| Updated | [[Jane Smith]] | Now leads platform and mobile |
| Created | REST vs GraphQL | New decision record |

## Summary
- Journal entry created
- Transcript archived with bidirectional links
- Tasks: N created (M candidates, K filtered, J skipped by user)
- Memory: N updates (X new, Y updated, Z skipped)
- Unresolved names: N (added to alias registry)
- Errors: [any errors, or "None"]
```

---

## Context budget

| Resource | Budget |
|----------|--------|
| Alias registry | Full read (Step 1) |
| Calendar | 1 query for event matching (Step 3) |
| Vault search | Up to 5 queries per entity/topic (Step 5) |
| Scripts | 1 scan-secrets.py invocation (Step 6) |
| Memory reads | Up to 10 targeted file reads for knowledge inventory |
| Backlog search | 1 query for existing issues (Step 14) |

---

## Absolute constraints

1. NEVER skip any of the 14 pipeline steps
2. NEVER proceed past Step 3 without a confirmed date and time
3. NEVER use generic speaker labels ("Speaker 1") in any output
4. NEVER create tasks without presenting the numbered review list and waiting for user selection
5. NEVER persist memory without presenting the review list and waiting for user confirmation
6. NEVER delete the original transcript
7. NEVER write to the vault before the secret scan (Step 6) completes
8. NEVER guess when a name is ambiguous. Ask the user.
9. NEVER skip the knowledge inventory. Redundant information wastes vault space and creates contradictions.
10. NEVER persist negative sentiment without flagging it and getting explicit user consent
11. NEVER use relative dates in output. Always resolve to YYYY-MM-DD.
12. ALWAYS apply canonical names from the alias registry to all output
13. ALWAYS save a summary to the daily note and changelog
14. ALWAYS report errors in the output summary even if processing completed partially
15. Step 7b failure NEVER blocks the pipeline — skip the nuance section, log `meeting_nuance_failed`, and continue to Step 8
