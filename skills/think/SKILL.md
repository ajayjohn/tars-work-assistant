---
name: think
description: Strategic analysis, validation, executive council, and discovery routing
user-invocable: true
help:
  purpose: |-
    Help the user reason through strategy, tradeoffs, risks, and ambiguous
    decisions using bounded workspace context and explicit analytical modes.
  use_cases:
    - "Analyze this strategy"
    - "Stress-test this decision"
    - "Launch the council"
    - "Help me think through this"
  scope: strategy,analysis,validation,council,discovery
---

# Think

Use Think for high-stakes reasoning. Use workspace context, but do not flood the
main session. Subagents may explore alternatives or objections and must return
bounded summaries.

## Modes

| Mode | Use when |
|---|---|
| Strategic analysis | The user asks for analysis, tradeoffs, or recommendation |
| Validation | The user asks what could go wrong or to stress-test |
| Executive council | The user wants multi-perspective debate |
| Discovery | The problem is ambiguous or needs non-obvious angles |
| Deep analysis | The user explicitly needs a full chain of analysis |

If discovery requires a dedicated bisociation engine, route to `skills/ideate/`.

## Rules

- State the framework and why it fits.
- Separate evidence, assumptions, risks, and recommendation.
- Use internal context when relevant, but cite uncertainty.
- Do not persist analysis unless the user asks or the workflow requires a saved
  artifact.

## References

- `manifesto.md`
- `references/analyze.md`
- `references/council.md`
- `references/legacy-full-protocol.md`
