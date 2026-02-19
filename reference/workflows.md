# Common workflows

Multi-skill patterns for recurring scenarios. Each workflow describes the skills involved, typical trigger, and expected flow.

---

## Meeting processing

**Trigger**: "Process this meeting" or paste a transcript.
**Skills**: `meeting` (single unified skill with parallel sub-agents)
**Flow**:
1. Transcript analysis produces structured journal entry with attendees, topics, decisions, and action items.
2. Two sub-agents run in parallel: task extraction (creates tasks via task integration) and memory extraction (offers durable facts for persistence).
3. If attendees are unknown, TARS offers to create memory entries.
4. Task creation is verified via list operation after each creation.
**Output**: Journal entry saved to `journal/YYYY-MM/`, tasks created and verified, memory updated.

---

## Weekly review

**Trigger**: "Weekly briefing" or "What happened this week?"
**Skills**: `briefing` (weekly mode, with parallel sub-agents for calendar, tasks, and memory)
**Flow**:
1. Three sub-agents run in parallel: calendar events from the past 7 days, task list review, and memory context query.
2. Results are cross-referenced: overdue items flagged, completed items noted, stale items triaged.
3. Memory gaps are detected (people or initiatives referenced but not in memory).
4. Upcoming week preview highlights key meetings and deadlines.
**Output**: Comprehensive weekly summary with action items for the week ahead.

---

## Strategic decision

**Trigger**: "Help me think through X" or "Analyze this decision."
**Skills**: `think` (deep mode orchestrates strategic analysis, validation council, and executive council)
**Flow**:
1. Strategic analysis uses Tree of Thoughts methodology with framework selection.
2. Two sub-agents run in parallel: validation council (adversarial stress-test) and executive council (CPO/CTO brain trust debate).
3. Final synthesis combines all perspectives into actionable recommendations.
**Output**: Multi-perspective analysis with clear recommendation and dissenting views.

---

## Initiative onboarding

**Trigger**: "Set up tracking for Project X" or "New initiative: ..."
**Skills**: `initiative` (planning mode) — cascades to `learn` (memory persistence) and `tasks` (task extraction) as side effects
**Flow**:
1. Initiative scoping captures goals, stakeholders, timeline, and success metrics.
2. Memory entry created in `memory/initiatives/` with full frontmatter.
3. Initial tasks are extracted and created with initiative linkage.
4. Stakeholder entries are checked and created if missing.
**Output**: Initiative memory file, linked tasks, stakeholder profiles updated.

---

## Stakeholder communication

**Trigger**: "Draft an email to X about Y" or "Help me communicate this change."
**Skills**: `communicate` (uses `answer` internally for context lookup)
**Flow**:
1. TARS looks up the recipient in memory for communication preferences and context.
2. Draft is composed with BLUF structure, appropriate tone, and relevant background.
3. Empathy audit checks for unintended tone issues.
4. RASCI enforcement ensures the right stakeholders are included.
**Output**: Draft communication ready for review and sending.

---

## Knowledge extraction

**Trigger**: "Extract insights from this article" or share a podcast transcript.
**Skills**: `learn` (wisdom mode — extracts insights and cascades to memory persistence)
**Flow**:
1. Content is analyzed for key insights, frameworks, and actionable takeaways.
2. Insights are structured into a journal entry with proper attribution.
3. Durable facts that pass the memory durability test are offered for persistence.
**Output**: Structured wisdom entry in journal, relevant memory updates.

---

## Daily startup

**Trigger**: Start of day or "Good morning."
**Skills**: `briefing` (daily mode, with parallel sub-agents) — automatic housekeeping via `maintain` if not already run today
**Flow**:
1. Automatic housekeeping runs if not already done today (health check, archival sweep, sync).
2. Three sub-agents run in parallel: today's calendar with attendee context, task priorities, and relevant memory context.
3. Task priorities are presented: overdue first, then today's due items, then upcoming.
4. Inbox is checked for pending items requiring processing.
**Output**: Morning briefing with calendar, tasks, people context, and pending inbox items.

---

## Performance review prep

**Trigger**: "Performance report for [team/initiative]" or "How is X doing?"
**Skills**: `initiative` (performance mode) — uses `answer` internally for KPI lookup
**Flow**:
1. KPI data is gathered from memory, task completion rates, and meeting participation.
2. Trend analysis identifies improvements and regressions over the reporting period.
3. Issues and blockers are surfaced from task and initiative data.
4. Report is formatted with metrics tables and narrative assessment.
**Output**: KPI-based performance report with trends and recommendations.
