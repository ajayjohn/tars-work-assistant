---
name: answer
description: Fast lookup and answer skill for schedule, people, meetings, tasks, initiatives, and general knowledge queries
triggers: ["when did I", "what's my schedule", "what do I know about", "who is", "am I free", "what meetings", "what's on my calendar"]
user-invocable: true
help:
  purpose: |-
    Fast factual lookups across calendar, memory, tasks, journal, transcripts, and integrations.
    Answers questions with source citations and confidence tiers.
  use_cases:
    - "When did I last meet Jane?"
    - "What's my schedule tomorrow?"
    - "Am I free Friday afternoon?"
    - "What do I know about the Platform Rewrite?"
    - "Who is Bob Chen?"
    - "What did we decide about the API?"
  scope: calendar,schedule,tasks,people,context,lookup
---

# Answer: Fast Lookup Protocol

Answer questions by searching across TARS information sources in priority order. Provide answers in BLUF (Bottom Line Up Front) format with source citations.

---

## Source priority — hybrid retrieval (v3.1)

| Priority | Source / tool | Contains | Confidence |
|----------|---------------|----------|------------|
| 1 | **Memory files** — `mcp__tars_vault__search_by_tag(tag="tars/<type>", …)` + `read_note` | Durable facts, relationships, decisions, preferences | High |
| 2 | **Tier-A FTS5** — `mcp__tars_vault__fts_search(scope="memory", query=…)` (Phase 4) | Keyword/BM25 over short structured notes | High |
| 3 | **Task notes** — `mcp__tars_vault__search_by_tag(tag="tars/task", …)` + task integration (`resolve_capability(capability="tasks")`) | Action items, deadlines, assignments | High |
| 4 | **Journal entries** — `mcp__tars_vault__search_by_tag(tag="tars/journal", …)` + semantic | Meeting summaries, briefings, wisdom | High |
| 5 | **Tier-B semantic** — `mcp__tars_vault__semantic_search(scope="journal\|transcripts\|contexts", …)` (Phase 4) | Paraphrase/quote recall over prose | Medium-High |
| 6 | **Transcript archives** — full-read fallback when semantic returned low scores | Verbatim quotes | High (verbatim) |
| 7 | **Integration sources** — `resolve_capability(capability="calendar\|tasks\|project-tracker\|…")` | Schedule, live data from provider MCPs | High |
| 8 (last) | **Web search** | External information | Medium-Low — flag explicitly |

**Key rules**:
- Never answer internal questions from web search alone. Exhaust internal sources first.
- If answering from LLM knowledge with no source, confidence is **Low** — flag explicitly.
- Cite with wikilinks + chunk indices for Tier-B hits (e.g., `[[2026-03-10 CSI Onsite Day 1]]#chunk-14`).
- Emit telemetry `answer_delivered` with `source_hit_tier` array covering which priorities contributed.

---

## Step 1: Parse query intent

Analyze the user's question to determine:

| Dimension | Examples |
|-----------|---------|
| **Intent type** | Schedule question, person lookup, meeting history, task query, initiative status, decision recall, general knowledge |
| **Entities** | People, products, initiatives, vendors, competitors |
| **Topics** | What the query is specifically about |
| **Timeframe** | Today, tomorrow, this week, last meeting, a specific date, "ever" |
| **Depth** | Quick fact (one-liner) vs. full context (detailed history) |

### Intent routing table

| Intent | Primary source | Fallback chain |
|--------|---------------|----------------|
| Schedule / "am I free" / "what's on my calendar" | Calendar integration | Journal → Memory |
| Person lookup / "who is" | Memory (`tars/person`) | Journal → Transcripts |
| Meeting history / "when did I meet" | Journal (`tars/meeting`) | Calendar → Transcripts |
| Task query / "what do I need to do" | Task integration | Journal (task extraction sections) |
| Initiative status / "how is X going" | Memory (`tars/initiative`) | Journal → Tasks |
| Decision recall / "what did we decide" | Memory (`tars/decision`) | Journal → Transcripts |
| General knowledge / "what do I know about" | Memory (all types) | Journal → Contexts → Transcripts |

---

## Step 2: Route to appropriate search

### Schedule queries (calendar, agenda, meetings, availability, "am I free")

Start with the calendar integration FIRST.

```
cap = mcp__tars_vault__resolve_capability(capability="calendar")
```

1. If `cap.status == "connected"`, call `cap.tools[*]` dynamically (never hard-code `mcp__apple_calendar__*` or `mcp__microsoft_365_*`).
2. If `cap.status == "unavailable"` and calendar is marked `required: true` in `_system/integrations.md`, state the specific connection error.
3. Always resolve the target date to `YYYY-MM-DD` before querying.

After calendar data, enrich via:
- Memory profiles for meeting attendees.
- Task integration via `resolve_capability(capability="tasks")` for items due same day.

### Person lookup

```
mcp__tars_vault__search_by_tag(tag="tars/person", query="<name>", limit=5)
```

If no exact match, resolve through the alias registry:
```
mcp__tars_vault__resolve_alias(name="<name>")
```

Then read the full profile:
```
mcp__tars_vault__read_note(file="<canonical name>")
```

If the person has meeting history, scan recent journal entries:
```
mcp__tars_vault__search_by_tag(tag="tars/meeting", query="<person name>", limit=5)
```

### Meeting history

```
mcp__tars_vault__search_by_tag(tag="tars/meeting", query="<topic or person>", limit=10)
```

Read matching journal entries. If the user asks about a specific detail discussed in a meeting and the journal summary lacks it, call `mcp__tars_vault__semantic_search(scope="transcripts", query=…)` (Phase 4) or proceed to transcript fallback (Step 3).

### Task queries

```
cap = mcp__tars_vault__resolve_capability(capability="tasks")
# use cap.tools[*] dynamically for list/filter by owner, due date, status
```

For "what's overdue" on TARS-managed task notes:
```
mcp__tars_vault__search_by_tag(
  tag="tars/task",
  frontmatter={"tars-status": "open"},
  limit=50
)
```
Filter results where `tars-due` < today.

### Initiative status

```
mcp__tars_vault__search_by_tag(tag="tars/initiative", query="<name>", limit=5)
mcp__tars_vault__read_note(file="<initiative name>")
```

Cross-reference with:
- Recent journal entries mentioning the initiative.
- Tasks linked to the initiative.
- People involved.

### Decision recall

```
mcp__tars_vault__search_by_tag(tag="tars/decision", query="<topic>", limit=10)
```

If not found in decisions, search journal entries:
```
mcp__tars_vault__search_by_tag(tag="tars/meeting", query="<topic>", limit=10)
```

Look for "Decisions" sections in meeting summaries.

### General knowledge

Follow the full hierarchy:
1. Memory: `mcp__tars_vault__fts_search(scope="memory", query="<keywords>", limit=10)` (Phase 4; until then `search_by_tag`).
2. Tasks: `resolve_capability(capability="tasks")` + `search_by_tag(tag="tars/task", …)`.
3. Journal: `mcp__tars_vault__semantic_search(scope="journal", query="<keywords>", limit=10)` (Phase 4).
4. Contexts: `mcp__tars_vault__semantic_search(scope="contexts", query="<keywords>", limit=5)` (Phase 4).
5. Transcripts: if none of the above has the answer (see Step 3).
6. Web: only if explicitly external information.

---

## Step 3: Transcript fallback — Issue 6

When memory, journal summaries, and other sources do not have enough detail to answer the question, fall back to archived transcripts.

### When to use transcript fallback

- User asks about a specific quote: "What exactly did Jane say about the timeline?"
- User asks about a minor detail not in summaries: "Did anyone mention the budget number?"
- User asks about meeting tone or dynamics: "Was there pushback on the proposal?"
- Journal entry exists but lacks the specific detail requested

### Transcript fallback pipeline

1. **Find relevant journal entries** by date, person, or topic:
   ```
   mcp__tars_vault__search_by_tag(tag="tars/meeting", query="<criteria>", limit=5)
   ```

2. **Read the journal entry** and check for a transcript link:
   ```
   mcp__tars_vault__read_note(file="<journal entry name>")
   ```
   Look for the `tars-transcript` property in frontmatter.

3. **If transcript exists**, read it:
   ```
   mcp__tars_vault__read_note(file="<transcript name>")
   ```

4. **Search the transcript** for the specific topic, quote, or detail the user is asking about.

5. **Return with citation**:
   ```
   From the raw transcript of [[2026-03-21 Platform Review]]:
   Jane said at 2:15pm: "The timeline is aggressive but doable if we get
   the two backend hires by end of month."
   ```

### Transcript search tips

- Search by speaker name to find what a specific person said
- Search by topic keywords to find relevant discussion segments
- Use timestamps to locate specific moments
- If the transcript is long (>15,000 words), search by section rather than reading the entire file

### When transcripts don't exist

If the journal entry has no `tars-transcript` link, or the transcript was not archived:
- Note: "No transcript archived for this meeting. Answer based on journal summary only."
- Do NOT fabricate transcript content.

---

## Step 4: Present answer in BLUF format

**BLUF (Bottom Line Up Front)**: Lead with the direct answer, then provide supporting detail.

### Format

```markdown
**[Direct answer to the question]**

[Supporting detail with context]

---
Sources:
- [[memory/people/jane-smith.md]] — person profile
- [[journal/2026-03/2026-03-21-platform-review.md]] — meeting summary
- Calendar: Mar 21 event "Platform Review" at 2:00 PM
```

### Examples

**Query**: "When did I last meet Jane?"

```markdown
**You last met Jane Smith on March 21, 2026** at the Platform Review meeting (2:00-3:00 PM).

Topics discussed: Q3 timeline, backend hiring, mobile team staffing.
Key outcome: Jane approved 2 backend hires for Platform Rewrite.
Next meeting: Not yet scheduled.

---
Sources:
- [[journal/2026-03/2026-03-21-platform-review.md]]
- Calendar: Mar 21, 2:00 PM "Platform Review"
```

**Query**: "What did we decide about the API?"

```markdown
**Decision: REST over GraphQL for the public API**, made on March 19, 2026.

Rationale: Broader ecosystem compatibility, lower barrier for external developers,
and alignment with existing internal tooling. GraphQL will remain for internal
services only.

Decided by: [[Jane Smith]] and [[Bob Chen]] during the API Architecture Review.

---
Sources:
- [[memory/decisions/api-architecture.md]]
- [[journal/2026-03/2026-03-19-api-architecture-review.md]]
```

**Query**: "What exactly did Bob say about the migration risk?"

```markdown
**Bob Chen expressed concern about Q3 timeline risk** during the Platform Review
on March 21.

From the raw transcript of [[2026-03-21 Platform Review]]:
Bob said at 2:32pm: "I'm worried about the Q3 deadline. If we don't get the
database migration done by June, we're looking at a 6-week slip minimum.
The team is already stretched thin with the API work."

---
Sources:
- [[archive/transcripts/2026-03/2026-03-21-platform-review-transcript.md]] — verbatim
- [[journal/2026-03/2026-03-21-platform-review.md]] — summary
```

---

## Step 5: Cite sources with wikilinks

Every piece of information in the answer must be traceable to a source. Use `[[wikilinks]]` for vault files and explicit labels for integration sources.

### Citation format

| Source type | Citation format |
|-------------|----------------|
| Memory file | `[[memory/people/jane-smith.md]]` |
| Journal entry | `[[journal/2026-03/2026-03-21-platform-review.md]]` |
| Transcript | `[[archive/transcripts/2026-03/...]]` with "verbatim" label |
| Calendar | `Calendar: [date] [event title]` |
| Task integration | `Tasks: [list name] — [task title]` |
| Web search | `Web: [URL or search query]` — flag as external |
| LLM knowledge | `Note: This is from general knowledge, not TARS memory` — flag as low confidence |

---

## Step 6: Handle gaps honestly

If the answer cannot be found in any source:

```markdown
**I don't have this information in memory, journal, or transcripts.**

Suggestions:
- Check your email for messages about [topic]
- This may have been discussed before TARS was active
- Would you like me to search the web for external information?
- If you know when this was discussed, I can check specific transcripts
```

Never fabricate an answer. Never hallucinate memory that doesn't exist. Never claim certainty when the source is ambiguous.

### Partial answers

If some parts of the question can be answered but others cannot:

```markdown
**Partial answer**: [what is known]

**Unknown**: [what could not be found]
I checked: [list of sources searched]. The [specific detail] was not captured.
```

---

# Search mechanics

## Index-first pattern (MANDATORY)

For vault searches, always use `mcp__tars_vault__search_by_tag` (tag + frontmatter filter) or the Phase-4 `fts_search` / `semantic_search` — never scan folders:

```
mcp__tars_vault__search_by_tag(tag="tars/person", query="<name>", limit=5)
mcp__tars_vault__search_by_tag(tag="tars/meeting", frontmatter={"tars-date__gte": "2026-03-01"}, limit=10)
mcp__tars_vault__search_by_tag(tag="tars/decision", query="<topic>", limit=5)
```

## Alias resolution

If an entity is not found by its primary name:

1. Call `mcp__tars_vault__resolve_alias(name="<name>")`.
2. Try partial name matching: `mcp__tars_vault__search_by_tag(tag="tars/person", query="<last name>", limit=5)`.
3. Try related entities: search by initiative or team the person belongs to.

## Date resolution

Always resolve dates before querying:

| User says | Resolve to |
|-----------|------------|
| "today" | Current date YYYY-MM-DD |
| "tomorrow" | Current date + 1 |
| "yesterday" | Current date - 1 |
| "this week" | Monday to Sunday of current week |
| "last week" | Monday to Sunday of previous week |
| "last meeting with X" | Search journal by person, sort by date desc |
| "March" | 2026-03-01 to 2026-03-31 |

---

# Source attribution

Tag each piece of information with its confidence tier:

| Source | Confidence | Display |
|--------|------------|---------|
| Memory files | High | No special label needed |
| User input (this session) | High | No special label needed |
| Calendar/task integration | High | No special label needed |
| Journal entries | High | No special label needed |
| Transcript archives | High | Label as "verbatim" |
| Web search | Medium-Low | **Flag explicitly**: "From web search:" |
| LLM general knowledge | Low | **Flag explicitly**: "Note: from general knowledge, not TARS memory" |

---

# Context budget

| Source | Limit |
|--------|-------|
| Memory | Search results + up to 5 targeted file reads |
| Journal | Search results + up to 3 full entry reads |
| Transcripts | Up to 2 transcript reads (only when journal insufficient) |
| Tasks | Active list by default (other lists only if explicitly needed) |
| Calendar | Target date(s) only |
| Contexts | Up to 2 reads (only for deep-detail questions) |

---

# Self-evaluation — Issue 9

If any errors occur during lookup:

1. Check `_system/backlog/issues/` for existing issue with same error signature
2. If exists: increment `tars-occurrence-count`, update `tars-last-seen`
3. If new: create issue note with context
4. Continue answering with available data — note the error to the user

---

# Absolute constraints

- NEVER answer internal questions from web search alone — exhaust internal sources first
- NEVER hallucinate or fabricate memory, journal entries, or transcript content
- NEVER claim calendar access is unavailable — TARS has calendar access. If integration fails, report the specific error.
- NEVER skip alias checking when an entity is not found by primary name
- NEVER present information without source citation
- NEVER present LLM general knowledge as vault-sourced fact — always flag confidence level
- ALWAYS query calendar integration for any question about schedule, agenda, meetings, availability, or "am I free"
- ALWAYS resolve dates to `YYYY-MM-DD` format before any query
- ALWAYS use BLUF format — lead with the direct answer
- ALWAYS cite sources using `[[wikilinks]]` for vault files
- ALWAYS attempt transcript fallback (Issue 6) before saying "I don't know" for meeting-related questions
- ALWAYS handle gaps honestly — say what was searched and what was not found
- ALWAYS use `mcp__tars_vault__search_by_tag` (or Phase-4 fts_search / semantic_search) rather than folder scanning
