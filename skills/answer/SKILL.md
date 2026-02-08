---
name: answer
description: Fast factual response using full search hierarchy with index-first pattern
user-invocable: true
help:
  purpose: |
    Fast factual lookups using a full search hierarchy: memory first, then tasks, journal, contexts, MCP tools, and finally web. Uses index-first pattern for efficient searching. Handles scheduling queries via calendar integration for calendar, agenda, and availability questions.
  use_cases:
    - "When you want to quickly look up a fact or person from your memory"
    - "When you need to check your schedule or availability"
    - "When you want to find what you've decided about something in the past"
    - "When you need to search across tasks, journal, and external sources"
  invoke_examples:
    - natural: "what do I know about X?"
    - natural: "what's on my calendar?"
    - natural: "any factual question"
    - slash: "/answer <question>"
  common_questions:
    - q: "What's the search order?"
      a: "Memory (index-first), Tasks, Journal, Contexts, MCP tools, then Web. Always search internal sources before web."
    - q: "What's index-first pattern?"
      a: "Always read _index.md before opening individual files. This scales efficiently to large workspaces."
  related_skills: [briefing, learn, maintain]
---

# Search protocol

Defines how to search across information sources for answering queries, analysis, or communication.

---

## Information hierarchy

| Priority | Source | Contains |
|----------|--------|----------|
| 1 (first) | **Memory** (`memory/`) | Quick facts, relationships, decisions |
| 2 | **Tasks** (via task integration) | Action items, deadlines, assignments |
| 3 | **Journal** (`journal/`) | Meeting summaries, briefings |
| 4 | **Contexts** (`contexts/`) | Deep reference material, full docs |
| 5 | **MCP tools** | project tracker, documentation, additional integrations |
| 6 (last) | **Web** | External, current information |

---

## Index-first pattern (MANDATORY)

Every search reads an `_index.md` BEFORE opening individual files. This is the most important scalability rule.

- `memory/_index.md` routes to the correct subfolder
- `memory/{category}/_index.md` maps aliases to filenames
- `journal/YYYY-MM/_index.md` lists entries by date, type, participants, initiatives

Never scan all files in a folder. Always use the index.

---

## When to search each source

### Memory
People, initiatives, products, vendors, competitors, past decisions.

### Tasks
What needs to be done, deadlines, assignments, follow-ups.

### Journal
Recent discussions, who said what, decisions from meetings, prior briefings.
- **Optimization:** For "last week" queries, read only current month's `_index.md`
- **Optimization:** For "find all meetings about X", check recent `_index.md` files first
- **Optimization:** For "what did we decide about X", check `memory/decisions/` first

### Contexts
Deep detail beyond memory: full product docs, schemas, org charts, specs.

### Calendar (via integration registry)
Schedule, availability, agenda, meetings, "am I free", "what do I have." TARS has calendar access via the configured calendar integration. Read `reference/integrations.md` Calendar section for provider details. Always resolve dates to `YYYY-MM-DD` format before querying. Any question about schedule, agenda, meetings, or availability MUST query the calendar integration.

### Tasks (via integration registry)
What needs to be done, deadlines, assignments, follow-ups. Read `reference/integrations.md` Tasks section. Execute the `list` operation for the relevant list.

### MCP tools
- **~~project tracker:** Issue status, sprint data, initiative metrics
- **~~documentation:** Documentation, policies, technical specs

### Web
Market information, competitor news, regulatory updates, current events. External only.

---

## Search procedure

### Step 1: Parse the query

Identify:
- **Entities:** People, products, initiatives, vendors, competitors
- **Topics:** What the query is about
- **Timeframes:** Dates, deadlines, recency
- **Depth:** Summary or full detail needed?

### Step 2: Check aliases

Entities may have alternate names. Check `_index.md` alias columns.

### Step 3: Search memory (index-first)

1. Read relevant `_index.md` to find target file
2. Read the specific file
3. Follow `[[Entity]]` wikilinks for related context

### Step 4: Check tasks (if applicable)

Execute the task integration `list` operation for configured lists (default: Active, Delegated, Backlog). Filter by owner (from notes field), due date, or initiative.

### Step 5: Check journal (if applicable)

1. Read `journal/YYYY-MM/_index.md` for recent months
2. Open specific entries matching the query
3. Expand backward in time only if needed

### Step 6: Check deep contexts (if needed)

Look in `contexts/` for full documentation, product specs, schemas.

### Step 7: Cite sources

When using information from searches, cite the source:
```
[From memory/people/jane-smith.md]
Jane prefers data-driven summaries and email over Slack.

[From journal/2026-01/2026-01-18-planning-session.md]
Discussed moving the deadline to end of February.
```

---

## Quick answer mode

For fast factual lookups:

### Scheduling queries (calendar, agenda, meetings, availability, "am I free")
Start with the calendar integration FIRST. Read `reference/integrations.md` Calendar section for provider details, resolve the target date to `YYYY-MM-DD` format, then execute the `list_events` operation. TARS has calendar access via configured integration. Never respond that calendar access is unavailable without checking integration status. If the calendar integration is unreachable, state the specific connection error. Then check memory for people context, then task integration for related tasks.

### All other queries
Follow standard hierarchy: memory -> tasks -> journal -> contexts -> MCP -> web.

### Gap closure
After searching, apply clarification protocol if critical context is still missing.

---

## Context budget
- Memory: Read `_index.md` + up to 5 targeted files
- Journal: Current month `_index.md` + up to 3 entries
- Tasks: Execute task integration `list` operation for Active only (unless other lists explicitly needed)

---

## Source attribution

When answering, tag each piece of information with its confidence tier:

| Source | Confidence |
|--------|------------|
| Memory files, user input | High |
| Native tools (calendar, tasks) | High |
| MCP tools (project tracker, docs) | Medium-High |
| Web search | Medium-Low |
| LLM knowledge (no source) | Low -- flag explicitly |

---

## Absolute constraints

- NEVER answer internal questions from web search alone
- NEVER hallucinate memory that doesn't exist
- NEVER skip context search when deep detail is clearly needed
- NEVER claim calendar access is unavailable. TARS has calendar access via configured integration. If integration fails, report the specific error.
- ALWAYS query calendar integration for any question about schedule, agenda, meetings, availability, or "am I free"
- ALWAYS resolve dates to `YYYY-MM-DD` format before any calendar query
- ALWAYS check integration constraints in reference/integrations.md before querying
- ALWAYS check aliases when entity not found by primary name
- ALWAYS use index-first pattern (never scan all files)
