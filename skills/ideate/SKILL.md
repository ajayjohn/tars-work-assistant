---
name: ideate
description: Open Collider semantic collision engine for non-obvious idea generation
attribution: "Bisociation engine design based on Open Collider (github.com/CL-ML/open-collider)"
user-invocable: true
help:
  purpose: |-
    Generate non-obvious ideas by colliding workspace context with structurally
    distant domains, while keeping domain exploration isolated in subagents.
  use_cases:
    - "I need surprising angles for positioning this feature"
    - "Non-obvious approaches to this challenge"
    - "What haven't we thought of?"
  scope: ideation,creativity,strategy,positioning,innovation
---

# Ideate

Ideation is a specialist workflow. Most users reach it through natural-language
discovery requests or Think escalation.

## Harness rule

Subagent isolation is mandatory. Each generation subagent receives only its
brief and assigned domain set. It must not load workspace memory or external
sources. This prevents cross-domain contamination and context bloat.

## Flow

1. Build a short brief from workspace context.
2. Confirm the objective and constraints.
3. Generate structurally distant domain mechanisms.
4. Launch isolated subagents for idea generation.
5. Score, curate, and present the strongest ideas.
6. Save only approved project/session/idea notes.

## References

- `references/legacy-full-protocol.md`
- `references/discovery.md`
- `references/generation.md`
