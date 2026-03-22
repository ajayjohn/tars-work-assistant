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

## Source priority — with transcript fallback (Issue 6)

| Priority | Source | Contains | Confidence |
|----------|--------|----------|------------|
| 1 (first) | **Memory files** (`memory/`) | Durable facts, relationships, decisions, preferences | High |
| 2 | **Task notes** (via task integration) | Action items, deadlines, assignments, follow-ups | High |
| 3 | **Journal entries** (`journal/`) | Meeting summaries, briefings, wisdom extractions | High |
| 4 | **Transcript archives** (`archive/transcripts/`) | Verbatim meeting records — when summaries lack detail | High (verbatim) |
| 5 | **Integration sources** (calendar, project tracker) | Schedule, events, project data | High |
| 6 (last) | **Web search** | External, current information | Medium-Low — flag explicitly |

**Key rule**: Never answer internal questions from web search alone. Exhaust internal sources first. If answering from LLM knowledge with no source, confidence is **Low** — flag explicitly.

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

1. Check `<mcp_servers>` context for calendar MCP server (preferred)
2. If found, use MCP tools (`list_events`, `get_event`)
3. If not found, check `_system/integrations.md` for legacy provider
4. Resolve target date to `YYYY-MM-DD` format
5. Execute `list_events` for the target date(s)

**TARS has calendar access via configured integration.** Never respond that calendar access is unavailable without checking integration status. If the integration is unreachable, state the specific connection error.

After calendar data, enrich with:
- Memory profiles for meeting attendees
- Task integration for related tasks due on the same day

### Person lookup

```
obsidian search query="tag:tars/person [name]" limit=5
```

If no exact match, check aliases:
```
obsidian read file="alias-registry"
```
Search for alternate names, nicknames, last names.

Then read the full profile:
```
obsidian read file="[canonical name]"
```

If the person has meeting history, optionally scan recent journal entries:
```
obsidian search query="tag:tars/meeting [person name]" limit=5
```

### Meeting history

```
obsidian search query="tag:tars/meeting [topic or person]" limit=10
```

Read matching journal entries. If the user asks about a specific detail discussed in a meeting, and the journal summary doesn't contain it, proceed to transcript fallback (Step 3).

### Task queries

1. Check `<mcp_servers>` context for tasks/reminders MCP server (preferred)
2. If found, use MCP tools (`list_reminders`)
3. If not found, check `_system/integrations.md` for legacy provider
4. Filter by: owner, due date, initiative, keyword, status

For "what's overdue":
```
obsidian search query="tag:tars/task tars-status:open" limit=50
```
Filter results where `tars-due` < today.

### Initiative status

```
obsidian search query="tag:tars/initiative [name]" limit=5
obsidian read file="[initiative name]"
```

Cross-reference with:
- Recent journal entries mentioning the initiative
- Tasks linked to the initiative
- People involved in the initiative

### Decision recall

```
obsidian search query="tag:tars/decision [topic]" limit=10
```

If not found in decisions, search journal entries:
```
obsidian search query="tag:tars/meeting [topic]" limit=10
```

Look for "Decisions" sections in meeting summaries.

### General knowledge

Follow the full hierarchy:
1. Memory: `obsidian search query="[keywords]" limit=10`
2. Tasks: check task integration
3. Journal: `obsidian search query="tag:tars/journal [keywords]" limit=10`
4. Contexts: `obsidian search query="path:contexts [keywords]" limit=5`
5. Transcripts: if none of the above has the answer (see Step 3)
6. Web: only if explicitly external information

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
   obsidian search query="tag:tars/meeting [criteria]" limit=5
   ```

2. **Read the journal entry** and check for a transcript link:
   ```
   obsidian read file="[journal entry name]"
   ```
   Look for the `tars-transcript` property in frontmatter.

3. **If transcript exists**, read it:
   ```
   obsidian read file="[transcript name]"
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

For vault searches, always use obsidian search with tags and property filters rather than scanning folders:

```
obsidian search query="tag:tars/person [name]" limit=5
obsidian search query="tag:tars/meeting tars-date:>=2026-03-01" limit=10
obsidian search query="tag:tars/decision [topic]" limit=5
```

Never scan all files in a folder. Always use tags and properties to narrow results.

## Alias resolution

If an entity is not found by its primary name:

1. Check `_system/alias-registry.md` for alternate names
2. Try partial name matching: `obsidian search query="[last name]" limit=5`
3. Try related entities: search by initiative or team that person belongs to

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
- ALWAYS use obsidian search with tags rather than folder scanning
