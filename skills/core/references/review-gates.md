# Review Gates Reference

## Classifications

| Classification | Meaning | Action |
|---|---|---|
| NEW | Not represented in workspace | Propose for review |
| UPDATE | Changes existing knowledge | Show current vs proposed |
| REDUNDANT | Already represented | Skip, mention briefly |
| CONTRADICTS | Conflicts with existing knowledge | Ask which version is current |

## Memory durability

Persist only when all four are true:

- Useful for lookup next week or next month
- High-signal, not narrow event log
- Durable, not tactical or transient
- Changes future interaction, decisions, routing, or recall

## Task accountability

Persist only when all three are true:

- Concrete deliverable or action
- Single owner
- Verifiable completion state

## Review syntax

Use numbered choices:

```text
Proposed memory updates:
1. Jane Smith: now owns onboarding [UPDATE]
2. New decision: REST over GraphQL for public API [NEW]

Save? all / 1 / all except 2 / none / edit 1
```

Never silently persist memory, tasks, contradictions, sensitive content, or
harness changes.

