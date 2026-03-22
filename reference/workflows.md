# Common workflows

This file remains as a lightweight workflow map. In TARS 3.0, the active runtime instructions live in `skills/` and `CLAUDE.md`.

## Daily operating loop

Trigger:
- `/briefing`
- “What does my day look like?”

Flow:
1. TARS checks maintenance state and runs scheduled upkeep when needed.
2. Calendar, tasks, and memory context are gathered in parallel when available.
3. The briefing surfaces meetings, deadlines, people context, and important initiative signals.

Output:
- Daily or weekly journal briefing with operational context

## Meeting to execution

Trigger:
- `/meeting`
- “Process this transcript”

Flow:
1. TARS matches the meeting against date and calendar context.
2. A meeting journal entry is drafted.
3. Tasks are proposed only if they pass the accountability test.
4. Durable memory is proposed only if it passes the durability test.
5. Transcript text is archived in a searchable transcript note linked to the journal entry.

Output:
- Meeting journal entry
- Reviewed tasks
- Reviewed memory updates
- Archived transcript note

## Ask and retrieve

Trigger:
- `/answer`
- “What do I know about X?”
- “When did we decide Y?”

Flow:
1. Search memory.
2. Search tasks and recent journal entries.
3. Search transcript archives for missing detail.
4. Check integrations when the question depends on external state.

Output:
- Source-backed answer with confidence anchored in the vault

## Initiative tracking

Trigger:
- `/initiative`
- “Set up a new initiative”
- “How is this initiative going?”

Flow:
1. TARS checks whether the initiative already exists.
2. It creates or updates the initiative note.
3. It links decisions, tasks, KPIs, and related stakeholders.

Output:
- Initiative note updates and supporting context

## Strategic analysis

Trigger:
- `/think`
- “Stress-test this decision”

Flow:
1. TARS reviews what the vault already knows.
2. It runs the appropriate analysis mode.
3. It produces a recommendation, risks, assumptions, and failure conditions.

Output:
- Structured strategic analysis grounded in current context
