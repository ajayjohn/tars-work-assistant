---
name: learn
description: Capture durable memory, wisdom, and reviewable preference or workflow patterns
triggers: ["remember that", "save to memory", "learn from this", "extract wisdom", "this changed", "note that"]
user-invocable: true
help:
  purpose: |-
    Extract durable facts, wisdom, and observed preference patterns from user
    input while preventing memory bloat and silent persistence.
  use_cases:
    - "Remember that Jane prefers email."
    - "Save this decision."
    - "Learn from this article."
    - "This changed since last week..."
  scope: memory,wisdom,learning,patterns
---

# Learn

Use Learn when the user provides a durable fact, correction, preference,
decision, relationship, or learning source. Treat short context crumbs as valid
input. Busy users should not need a full transcript to make TARS smarter.

## Modes

| Mode | Use when |
|---|---|
| Memory | Durable fact, correction, preference, relationship, decision |
| Wisdom | Article, podcast, book, video, reference content |
| Patterns | Review telemetry-derived user-model and workflow proposals |

## Required behavior

- Check existing workspace knowledge before proposing persistence.
- Apply durability criteria to memory candidates.
- Show `NEW`, `UPDATE`, `REDUNDANT`, or `CONTRADICTS`.
- Persist only after explicit review.
- Negative or sensitive person content must be flagged or rephrased.

## References

- `references/memory.md`
- `references/wisdom.md`
- `references/patterns.md`
- `references/legacy-full-protocol.md`
