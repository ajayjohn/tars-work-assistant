---
name: learn
description: Extract durable memory from conversations or wisdom from learning content
triggers: ["remember that", "save to memory", "learn from this", "extract wisdom"]
user-invocable: true
help:
  purpose: |-
    Extract durable memory from conversations or wisdom from learning content.
    Two modes: Memory (persist facts) and Wisdom (extract insights from articles, podcasts, books).
  use_cases:
    - "Remember that Jane prefers email over Slack"
    - "Save to memory: we decided to use REST for the public API"
    - "Learn from this article about API design patterns"
    - "Extract wisdom from this podcast transcript"
  scope: memory,wisdom,learning,extraction
---

# Learn: Memory and Wisdom Extraction

Two complementary modes for building TARS's knowledge base. Memory mode persists durable facts from conversations. Wisdom mode extracts insights from learning content.

All vault writes use `mcp__tars_vault__*` tools (see `skills/core/SKILL.md` → "Write interface"). The server runs the auto-wikilink pass (§3.3) before every body write — ambiguous names surface for batched review, never silent link insertion.

---

## Mode detection

| Signal | Mode |
|--------|------|
| "remember that...", "save to memory", "learn that..." | Memory |
| "extract wisdom from...", "learn from this article/podcast/book" | Wisdom |
| Ambiguous | Ask: "Should I save this as a memory fact, or extract wisdom from it as learning content?" |

---

# MODE A: Memory Extraction

Persist durable, high-value facts from conversation. Be highly selective. Most inputs will NOT result in memory additions. Memory is for durable insights, not a task tracker or event log.

---

## Step 1: Alias resolution (server-cached)

Use `mcp__tars_vault__resolve_alias(name="…")` for canonicalization. The server holds the registry in memory with mtime-based invalidation. Three-layer resolution inside the tool:

1. **Alias registry**: `_system/alias-registry.md` canonical + aliases map.
2. **Obsidian aliases**: `mcp__tars_vault__search_by_tag(tag="tars/person", query="<name>", limit=5)`.
3. **Contextual**: calendar attendees, recent journal entries, role mentions.

If any name is ambiguous (multiple canonical matches) or unknown (no match), ask before proceeding:

```
"Who is 'Dan' in this context?
  1. Dan Rivera (Engineering)
  2. Dan Chen (Infrastructure)
  3. Someone new — I'll provide the full name"
```

Do NOT persist memory entries with unresolved or ambiguous names.

---

## Step 2: Analyze input for delta (MANDATORY)

Read the input completely. Identify potential delta — new information that:

1. Was not previously known (check existing memory first)
2. Contradicts existing memory (requires update)
3. Reveals deeper insight when combined with context

**STOP.** If no delta identified, output "No Action — input contains no new information." and end.

---

## Step 3: Check existing memory (MANDATORY)

For each entity or topic identified:

```
mcp__tars_vault__search_by_tag(tag="tars/<type>", query="<entity>", limit=5)
```

Phase 4 adds `mcp__tars_vault__fts_search` for paraphrase/body matching — important for REDUNDANT detection where a different phrasing captures the same fact.

Then read the specific files that match:

```
mcp__tars_vault__read_note(file="<entity name>")
```

Compare the input against what is already captured.

- If the insight is already captured identically: **STOP.** Output "Already in memory." and end.
- If partial overlap: proceed to determine if it qualifies as an UPDATE.
- If no existing knowledge: proceed as potentially NEW.

---

## Step 4: Apply durability test (MANDATORY)

For EACH potential insight, ALL four criteria must pass:

| # | Criterion | Question |
|---|-----------|----------|
| 1 | **Lookup value** | Will this be useful for lookup next week or next month? |
| 2 | **Signal** | Is this high-signal and broadly applicable? |
| 3 | **Durability** | Is this durable (not transient or tactical)? |
| 4 | **Behavior change** | Does this change how I should interact in the future? |

### Pass examples

| Insight | Why it passes |
|---------|--------------|
| "Daniel prefers data in tables, not paragraphs" | Changes all future communications with Daniel |
| "Vendor contract renews June 2026" | Contract intelligence, lookup value for months |
| "We decided to delay Phase 2 for the migration" | Lasting strategic impact on initiative planning |
| "Sarah is the new VP of Engineering" | Durable org fact, changes communication routing |

### Fail examples

| Insight | Why it fails |
|---------|-------------|
| "I have a meeting with John tomorrow" | Tactical, schedule item — not durable |
| "We discussed MCP timeline" | Vague, no specific insight |
| "Emailed Daniel about the update" | Event log, not insight |
| "The server was down for 2 hours today" | Transient incident, not a durable fact |

If ANY criterion fails, the insight FAILS. Do not persist. When in doubt, it does NOT pass.

---

## Step 5: Classify and determine folder (MANDATORY)

Map each passing insight to the correct memory folder:

| Type | Folder | Tag |
|------|--------|-----|
| Person fact | `memory/people/` | `tars/person` |
| Vendor info | `memory/vendors/` | `tars/vendor` |
| Competitor intel | `memory/competitors/` | `tars/competitor` |
| Product knowledge | `memory/products/` | `tars/product` |
| Initiative context | `memory/initiatives/` | `tars/initiative` |
| Decision record | `memory/decisions/` | `tars/decision` |
| Organizational context | `memory/org-context/` | `tars/org-context` |

### Vendor vs competitor classification

| Type | Definition | Examples |
|------|------------|----------|
| **Vendor** | Contractual/service relationship with us | Cloud providers, SaaS tools, consulting firms |
| **Competitor** | Competing for the same customers or market share | Direct and adjacent competitors |

---

## Step 6: Knowledge check — Issue 7 (MANDATORY)

For each insight that passes the durability test, classify against existing vault knowledge:

| Classification | Action |
|---------------|--------|
| **NEW** | Present for review. Will create new content. |
| **UPDATE** | Show diff to user: "Current: 'Jane leads platform.' Update to: 'Jane leads platform and mobile.' Update?" |
| **REDUNDANT** | Skip silently. Mention in summary: "Already in memory. Skipping." |
| **CONTRADICTS** | Ask user: "Memory says REST. Input says GraphQL. Which is current?" |

Never persist REDUNDANT items. Never persist CONTRADICTS items without resolution.

---

## Step 7: Negative sentiment detection — Issue 8 (MANDATORY)

Scan each insight for negative sentiment patterns:

**Patterns to detect**: slow, political, difficult, unreliable, incompetent, lazy, disorganized, hostile, passive-aggressive, underperforming, resistant, obstructionist, untrustworthy

If a statement contains negative sentiment about a person:

```
"This about Steve has negative sentiment: 'Steve has been slow to deliver.'
 Save with flag for periodic review? [Y / Rephrase / Skip]"
```

| Response | Action |
|----------|--------|
| **Y** | Save with inline flag: `<!-- tars-flag:negative YYYY-MM-DD -->`. Set `tars-has-flagged-content: true` on the person's note. |
| **Rephrase** | Ask for a neutral restatement. Re-apply durability test to rephrased version. |
| **Skip** | Do not persist this insight. |

---

## Step 8: Present for review (MANDATORY)

Present ALL proposed memory updates in a numbered list:

```
Proposed memory updates:
  1. [[Jane Smith]]: Approved 2 backend hires for [[Platform Rewrite]]     [NEW]
  2. [[Bob Chen]]: Now reports to Sarah instead of Mike                     [UPDATE]
  3. New decision: REST over GraphQL for public API                         [NEW]

Save? [all / 1, 3 / none / edit #2]
```

Selection syntax:
- `all` — save all proposed updates
- `1, 3` — save only specific items
- `all except 2` — save all but specific items
- `none` — discard all
- `edit #2` — modify a specific item before saving

**Do NOT persist anything until the user confirms.**

---

## Step 9: Write after confirmation (MANDATORY)

For each confirmed update:

### New entity

```
mcp__tars_vault__create_note(
  name="Entity Name",
  path="memory/<category>/entity-slug.md",
  template="<type>",
  frontmatter={
    "tags": ["tars/<type>"],
    "aliases": ["<alternate names>"],
    "tars-summary": "One-line description for scanning",
    "tars-related": ["[[linked entities]]"],
    "tars-created": "YYYY-MM-DD",
    "tars-updated": "YYYY-MM-DD"
  },
  body="## Key Facts\n- <insight content>"
)
```

The server enforces all required fields per `_system/schemas.yaml`; missing required fields cause the tool call to return a validation error.

### Existing entity (update)

```
mcp__tars_vault__append_note(file="Entity Name", content="\n- <new insight> (YYYY-MM-DD)")
mcp__tars_vault__update_frontmatter(file="Entity Name", property="tars-updated", value="YYYY-MM-DD")
```

ALL entity references in content use `[[Entity Name]]` wikilink syntax; the auto-wikilink pass inside the MCP server performs the canonicalization.

---

## Step 10: Alias registry (handled automatically)

On `create_note` of a new entity, the server updates the in-process alias registry cache and appends a row to `_system/alias-registry.md` if the canonical+aliases+type+path line isn't present. No explicit append call is required; after N auto-detections the server surfaces a hint suggesting the user add manual aliases.

---

## Step 11: Daily-note + changelog (handled by PostToolUse hook)

The `PostToolUse` hook appends the memory-action line to the daily note and writes the changelog entry with batch ID. Emit telemetry events `memory_proposed` (count) and `memory_persisted` (count, accepted, rejected).

---

## Output format (Memory mode)

**If insights persisted:**

```markdown
## Memory updates
| Action | File | Summary |
|--------|------|---------|
| Created | `memory/vendors/acme.md` | Contract renewal June 2026 |
| Updated | `memory/people/jane-smith.md` | Added: leads mobile team |
| Skipped | — | "Discussed timeline" — already captured |
```

**If no insights qualified:**

```markdown
## Memory updates
No Action: Input contained no durable, high-signal insights.
Reason: [specific reason — e.g., "all items were transient scheduling logistics"]
```

---

# MODE B: Wisdom Extraction

Process learning content (articles, podcasts, books, transcripts, videos, conversations) to extract insights, frameworks, and actionable knowledge. Use this when the user is **learning** rather than **collaborating**. Not for collaborative meetings — use `skills/meeting/` instead.

---

## Step 1: Identify source type (MANDATORY)

Classify the source:

### Conversational and narrative sources (Directive A)

- Podcasts, YouTube transcripts, interviews
- Panel discussions, monologues, informal talks
- Blog posts, social media threads, newsletters
- Conversation recordings, fireside chats

### Authoritative and educational sources (Directive B)

- Research papers, technical guides, textbooks
- Formal documentation with citations, whitepapers
- Standards documents, RFCs, specifications
- Course materials, structured tutorials

State the classification in output. If mixed (e.g., a podcast with a professor), default to Directive A but apply Directive B rigor to technical segments.

---

## Step 2: Resolve references (MANDATORY)

Scan source content for person names. Resolve each via `mcp__tars_vault__resolve_alias(name="…")` — the server holds the alias registry in memory. Ambiguous or unknown names must be resolved (or explicitly marked unknown) before extraction begins.

---

## Step 3: Extract key insights

### Directive A: Conversational sources (DEFAULT)

Extract wisdom, inspiration, and profound nuggets:

- **Profound statements**: Ideas that challenge norms or reframe common assumptions
- **Novel perspectives**: Unique framing of common problems
- **Key mental models**: Frameworks, analogies, and models used by speakers
- **Actionable insights**: Specific, non-obvious advice with clear application
- **Memorable quotes**: Verbatim quotes that capture the essence of an idea

### Directive B: Authoritative sources (EXCEPTION)

Extract education and simplification:

- **Core concepts**: Fundamental principles or building blocks
- **Complex methodologies**: Step-by-step breakdowns in plain language
- **Key findings**: The "so what" — implications and applications
- **Definitions**: Critical domain-specific terms explained clearly
- **Reference frameworks**: Models, taxonomies, or decision trees

### Comprehensive context requirement (BOTH directives)

Each extracted insight MUST be comprehensive and self-contained. Never output isolated statements without context.

**Weak (avoid):**
> "Bicycle for the Mind": The speaker said AI is a bicycle for the mind. (Ref: 22:15)

**Strong (required):**
> **Reframing AI as a "Bicycle for the Mind"**: The speaker challenged the "AI as replacement" narrative. Their core argument was that AI should be viewed as cognitive amplification, much like the bicycle amplified human locomotion. The insight is that AI enables an average individual to achieve world-class cognitive output in specific narrow domains. This shifts the frame from "human vs. machine" to "human with machine." (Ref: 22:15-23:45)

---

## Step 4: Apply durability test to each insight (MANDATORY)

Apply the same four-criterion durability test from Memory mode (Step 4) to each extracted insight:

1. **Lookup value** — Will I reference this insight again?
2. **Signal** — Is this broadly applicable, not niche trivia?
3. **Durability** — Will this be true/relevant in 6 months?
4. **Behavior change** — Does this change how I think, work, or decide?

Insights that pass all four become candidates for memory persistence (Step 7). Insights that fail can still appear in the wisdom journal entry but are NOT persisted to memory files.

---

## Step 5: Check existing memory for overlap (MANDATORY)

For each durable insight:

```
mcp__tars_vault__search_by_tag(tag="tars/<type>", query="<topic keywords>", limit=5)
```

Compare against existing vault knowledge. Apply the knowledge check (Issue 7):

| Classification | Action |
|---------------|--------|
| **NEW** | Include in wisdom report and propose for memory |
| **UPDATE** | Note the enhancement. Show diff if proposing memory update. |
| **REDUNDANT** | Include in report for completeness. Do NOT propose memory update. |
| **CONTRADICTS** | Flag in report. Ask user which version to keep. |

---

## Step 6: Create wisdom journal entry (MANDATORY)

**Filename**: `journal/YYYY-MM/YYYY-MM-DD-wisdom-topic-slug.md`

Note the `wisdom-` prefix to distinguish from meeting reports.

```
mcp__tars_vault__create_note(
  name="YYYY-MM-DD Wisdom: Source Title",
  path="journal/YYYY-MM/YYYY-MM-DD-wisdom-topic-slug.md",
  template="wisdom-journal",
  frontmatter={
    "tags": ["tars/journal", "tars/wisdom"],
    "tars-date": "YYYY-MM-DD",
    "tars-source-type": "podcast | article | video | paper | book | transcript | conversation",
    "tars-source-title": "Full Source Title",
    "tars-author": "Author or Speaker Name",
    "tars-topics": ["key", "topics", "extracted"],
    "tars-created": "YYYY-MM-DD"
  },
  body="<wisdom markdown>"
)
```

### Journal entry structure

```markdown
# Wisdom: [Source Title]

## Source analysis
- **Type**: [Podcast / Article / Video / Paper / Book]
- **Author/Speaker**: [Name]
- **Core topics**: [1-2 sentence overview]
- **Directive applied**: A (conversational) / B (authoritative)

## Executive insights

### 1. [Insight title]
[Comprehensive, self-contained explanation with context, implications, and reference]

### 2. [Insight title]
[...]

## Key quotes
> "[Verbatim quote]" — [Speaker], [Reference/Timestamp]

## Implications for current work
- [[Initiative Name]]: [How this applies]
- [General application]: [How this changes thinking]

## Recommended direct review
- [Section/timestamp]: [Why worth reviewing directly]

## Follow-up actions
- [ ] [Specific action identified]
- [ ] [Research item to explore]
```

---

## Step 7: Persist durable insights to memory (CONDITIONAL)

For insights that passed the durability test AND the knowledge check (NEW or UPDATE):

Present proposed memory updates using the same numbered review format as Memory mode Step 8:

```
Durable insights extracted. Proposed memory updates:
  1. New decision: "API-first design" framework from [Source]          [NEW]
  2. [[Acme Corp]]: Identified as competitor in adjacent space         [NEW]
  3. [[Platform Rewrite]]: Validates microservices approach            [UPDATE]

Save to memory? [all / 1, 2 / none]
```

Only persist after user confirms. Follow the same write protocol as Memory mode Step 9.

---

## Step 8: Extract tasks from follow-up actions (CONDITIONAL)

If the source content suggests follow-up actions:

Apply the accountability test to each:

| # | Criterion | Question |
|---|-----------|----------|
| 1 | **Concrete** | Is it a specific deliverable? |
| 2 | **Owned** | Is there a clear single owner? (Usually the user for wisdom content) |
| 3 | **Verifiable** | Will we know when it's done? |

Present candidates:

```
Follow-up actions identified:
  1. [KEEP] Research API-first design patterns (you, backlog, low)
  2. [KEEP] Share article with Sarah re: platform strategy (you, due this week, medium)

  -- Filtered out --
  3. "Should think more about this" — not concrete

Create tasks? [all / 1 / none]
```

For each confirmed task, create via the task integration. Verify creation by reading back from the task list. Report any creation failures.

---

## Step 9: Daily-note + changelog (handled by PostToolUse hook)

The `PostToolUse` hook appends the wisdom-extraction line to the daily note and writes the changelog entry after the wisdom journal `create_note` succeeds. Emit telemetry event `wisdom_extracted` with `{insights_extracted, durable_count, memory_proposed, memory_persisted, tasks_created}`.

---

## Output format (Wisdom mode)

```markdown
# Knowledge extraction report

## 1. Source analysis
- **Source type**: [Type] (Directive [A/B])
- **Core topics**: [1-2 sentence overview]
- **Date processed**: YYYY-MM-DD

## 2. Executive insights and key ideas
[For Directive A: comprehensive wisdom nuggets with full context]
[For Directive B: simplified educational content with clear explanations]

## 3. Key quotes
[Verbatim quotes with attribution and reference]

## 4. Implications for current work
[How insights connect to active initiatives and priorities]

## 5. Recommended direct review
[Selective list of sections worth reviewing in the source, with reasons]

---
## Wisdom context
Saved: `journal/YYYY-MM/YYYY-MM-DD-wisdom-topic-slug.md`

## Memory updates
| Action | File | Summary |
|--------|------|---------|
| Created | `memory/decisions/api-first.md` | API-first design framework |
| Skipped | — | Microservices pattern — already captured |

## Task updates
| Operation | Task | Details |
|-----------|------|---------|
| Created | Research API patterns | Backlog, low priority |
| Skipped | "Think about this more" | Failed accountability test |

## Creation unverified
| Task | List | Issue |
|------|------|-------|
(Tasks reported created but not confirmed via list verification)
```

---

# Shared protocols

## Context budgets

**Memory mode:**
- Alias registry: `_system/alias-registry.md` (mandatory)
- Memory: Search results + up to 3 targeted file reads for comparison
- Daily note: append only

**Wisdom mode:**
- Alias registry: `_system/alias-registry.md` (mandatory)
- Memory: Search results + up to 3 targeted file reads for overlap check
- Journal: create one entry
- Tasks: create via integration (verify after)
- Daily note: append only

## Circuit breakers

| Condition | Action |
|-----------|--------|
| >10 memory updates in a single invocation | Pause. Ask user to confirm batch. |
| Name resolution confidence <70% | Do not persist. Ask user. |
| >3 consecutive obsidian-cli errors | Stop all operations. Report status. Log to `_system/backlog/issues/`. |
| Contradicting existing memory | Do not auto-resolve. Ask user explicitly. |

## Self-evaluation — Issue 9

If any errors occur during processing:

1. Check `_system/backlog/issues/` for existing issue with same error signature
2. If exists: increment `tars-occurrence-count`, update `tars-last-seen`
3. If new: create issue note with context via `mcp__tars_vault__create_note(path="_system/backlog/issues/…", template="issue", …)`

---

# Absolute constraints

## Memory mode constraints

- NEVER persist scheduling logistics ("meeting tomorrow at 3pm")
- NEVER persist event logs ("met with", "emailed", "called")
- NEVER persist vague references ("discussed timeline", "talked about the project")
- NEVER skip the durability test — all four criteria must pass
- NEVER skip comparison against existing memory
- NEVER skip the knowledge check (Issue 7) — classify as NEW/UPDATE/REDUNDANT/CONTRADICTS
- NEVER persist without user confirmation via the numbered review list
- NEVER skip alias registry load and name resolution
- NEVER write entries with unresolved or ambiguous names
- NEVER omit the memory updates output section

## Wisdom mode constraints

- NEVER use isolated bullet points without comprehensive context
- NEVER skip source type analysis and directive selection
- NEVER output insights without self-contained explanations
- NEVER forget to apply durability test to extracted insights
- NEVER forget to check existing memory for overlap (Issue 7)
- NEVER omit the `wisdom-` prefix in journal filenames
- NEVER report tasks as created without verifying via the task integration list operation
- NEVER skip the follow-up action extraction step

## Shared constraints

- ALL entity references MUST use `[[Entity Name]]` wikilink syntax
- ALL names MUST be resolved to canonical form via the alias registry
- ALL writes MUST be logged to the daily note and changelog
- ALL frontmatter MUST conform to `_system/schemas.yaml`
- NEVER skip negative sentiment detection (Issue 8) for person-related content
- NEVER auto-resolve contradictions — always ask the user
