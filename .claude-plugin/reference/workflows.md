# Common workflows

Multi-skill patterns for recurring scenarios. Each workflow describes the skills involved, typical trigger, and expected flow.

---

## Meeting processing

**Trigger**: "Process this meeting" or paste a transcript.
**Skills**: process-meeting → extract-tasks → extract-memory
**Flow**:
1. Transcript analysis produces structured journal entry with attendees, topics, decisions, and action items.
2. Action items are extracted and created as tasks via the task integration.
3. New people, initiative references, and durable facts are offered for memory persistence.
4. If attendees are unknown, TARS offers to create memory entries.
**Output**: Journal entry saved to `journal/YYYY-MM/`, tasks created, memory updated.

---

## Weekly review

**Trigger**: "Weekly briefing" or "What happened this week?"
**Skills**: briefing (weekly mode) → manage-tasks → update
**Flow**:
1. Calendar events from the past 7 days are retrieved and cross-referenced with journal entries.
2. Task lists are reviewed: overdue items flagged, completed items noted, stale items triaged.
3. Memory gaps are detected (people or initiatives referenced but not in memory).
4. Upcoming week preview highlights key meetings and deadlines.
**Output**: Comprehensive weekly summary with action items for the week ahead.

---

## Strategic decision

**Trigger**: "Help me think through X" or "Analyze this decision."
**Skills**: deep-analysis (strategic-analysis → validation-council → executive-council)
**Flow**:
1. Strategic analysis uses Tree of Thoughts methodology with framework selection.
2. Validation council stress-tests the analysis with adversarial personas.
3. Executive council (CPO/CTO brain trust) debates trade-offs and priorities.
4. Final synthesis combines all perspectives into actionable recommendations.
**Output**: Multi-perspective analysis with clear recommendation and dissenting views.

---

## Initiative onboarding

**Trigger**: "Set up tracking for Project X" or "New initiative: ..."
**Skills**: initiative → extract-memory → extract-tasks
**Flow**:
1. Initiative scoping captures goals, stakeholders, timeline, and success metrics.
2. Memory entry created in `memory/initiatives/` with full frontmatter.
3. Initial tasks are extracted and created with initiative linkage.
4. Stakeholder entries are checked and created if missing.
**Output**: Initiative memory file, linked tasks, stakeholder profiles updated.

---

## Stakeholder communication

**Trigger**: "Draft an email to X about Y" or "Help me communicate this change."
**Skills**: communicate → quick-answer (for context lookup)
**Flow**:
1. TARS looks up the recipient in memory for communication preferences and context.
2. Draft is composed with BLUF structure, appropriate tone, and relevant background.
3. Empathy audit checks for unintended tone issues.
4. RASCI enforcement ensures the right stakeholders are included.
**Output**: Draft communication ready for review and sending.

---

## Knowledge extraction

**Trigger**: "Extract insights from this article" or share a podcast transcript.
**Skills**: extract-wisdom → extract-memory
**Flow**:
1. Content is analyzed for key insights, frameworks, and actionable takeaways.
2. Insights are structured into a journal entry with proper attribution.
3. Durable facts that pass the memory durability test are offered for persistence.
**Output**: Structured wisdom entry in journal, relevant memory updates.

---

## Daily startup

**Trigger**: Start of day or "Good morning."
**Skills**: briefing (daily mode) → manage-tasks → housekeeping
**Flow**:
1. Automatic housekeeping runs if not already done today (health check, archival sweep, sync).
2. Today's calendar is retrieved with attendee context from memory.
3. Task priorities are presented: overdue first, then today's due items, then upcoming.
4. Inbox is checked for pending items requiring processing.
**Output**: Morning briefing with calendar, tasks, people context, and pending inbox items.

---

## Performance review prep

**Trigger**: "Performance report for [team/initiative]" or "How is X doing?"
**Skills**: performance-report → quick-answer (for KPI lookup)
**Flow**:
1. KPI data is gathered from memory, task completion rates, and meeting participation.
2. Trend analysis identifies improvements and regressions over the reporting period.
3. Issues and blockers are surfaced from task and initiative data.
4. Report is formatted with metrics tables and narrative assessment.
**Output**: KPI-based performance report with trends and recommendations.
