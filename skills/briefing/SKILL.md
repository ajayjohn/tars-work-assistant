---
name: briefing
description: Adaptive daily and weekly briefings with calendar, task, memory, drift, and re-entry context
triggers: ["daily briefing", "what should I focus on", "what's my day look like", "weekly briefing", "plan my week", "catch me up", "what did I miss"]
user-invocable: true
help:
  purpose: |-
    Prepare the user for the day or week, or reorient them after disuse, by
    combining schedule, task, memory, initiative, inbox, and system-drift
    signals into one concise briefing.
  use_cases:
    - "What should I focus on today?"
    - "Brief me for the week."
    - "Catch me up."
    - "What did I miss?"
  scope: briefing,calendar,tasks,planning,catch-up,drift
---

# Briefing

Use `/briefing` or natural language. Do not introduce user-facing flags for
catch-up or drift. Infer the briefing posture from the request and workspace
state.

## Adaptive posture

Before gathering detail, read the dynamic state capsule with
`mcp__tars_vault__context_gaps` and `mcp__tars_vault__workspace_map`.

Choose one posture:

| Posture | Trigger |
|---|---|
| Daily | Current session cadence and user asks for today/focus |
| Weekly | User mentions week or planning |
| Re-entry | User asks to catch up, or last session was 14+ days ago |
| Sparse-context | Calendar/tasks exist but recent journal/transcript/intake is thin |
| Drift-aware | Active initiatives, overdue tasks, inbox, or index state is stale |

Blend postures when needed, but keep the output short. A re-entry or sparse
briefing is still just `/briefing`.

## Data gathering

Use subagents only for independent read-heavy work. Each subagent returns
bounded JSON. The main agent performs synthesis, asks any question, and saves.

Gather:

- calendar capability, if connected
- task capability, if connected
- `workspace_map` for active initiatives, people, decisions, tasks, inbox, and
  recent journal
- `context_gaps` for stale or missing signals
- targeted memory reads for key people and initiatives

Detailed daily, weekly, and adaptive protocols live in `references/`.

## Output rules

- Start with the bottom line.
- Show missing integrations or missing context as uncertainty, not failure.
- End with exactly one high-leverage low-effort ask when context is stale or
  sparse.
- Save daily and weekly briefings to journal. Re-entry-only orientation can be
  shown inline unless the user provides new context.
- Do not output generic setup nags or a long command catalog.

## References

- `references/adaptive.md`
- `references/daily.md`
- `references/weekly.md`
- `references/legacy-full-protocol.md`
