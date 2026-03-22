# TARS 3.0 Rebuild Handoff

Read this file and execute the rebuild. Do not ask for a broad summary first. Start by reading the required documents below, then follow the phased build sequence and environment checks exactly.

## Mission

Rebuild the current TARS framework into **TARS 3.0**, an Obsidian-native persistent executive assistant framework, on a **new branch** without modifying the current 2.x implementation on `main`.

You are working in this repository:

`/Users/ajayjohn/Sync/Applications/Library/tars/`

You must:

- create branch `tars-3.0` from `main`
- leave `main` untouched
- implement the v3 rebuild according to the reference plans
- incorporate the ten real-world issue themes captured in `Temp.md`
- document justified deviations in `DECISIONS.md`

## Required Reads

Read these in this order before making any changes:

1. [REBUILD_HANDOFF.md](/Users/ajayjohn/Sync/Applications/Library/tars/REBUILD_HANDOFF.md)
2. [Temp.md](/Users/ajayjohn/Sync/Applications/Library/tars/Temp.md)
3. [TARS_V3_REBUILD_PLAN.md](/Users/ajayjohn/Sync/Applications/Library/tars/TARS_V3_REBUILD_PLAN.md)
4. [TARS_V2_REBUILD_PLAN.md](/Users/ajayjohn/Sync/Applications/Library/tars/TARS_V2_REBUILD_PLAN.md)
5. [TARS_REBUILD_FOUNDATION.md](/Users/ajayjohn/Sync/Applications/Library/tars/TARS_REBUILD_FOUNDATION.md)

Also inspect the current framework source under:

- [skills/](/Users/ajayjohn/Sync/Applications/Library/tars/skills)
- [reference/](/Users/ajayjohn/Sync/Applications/Library/tars/reference)
- [scripts/](/Users/ajayjohn/Sync/Applications/Library/tars/scripts)
- [tests/](/Users/ajayjohn/Sync/Applications/Library/tars/tests)
- [CLAUDE.md](/Users/ajayjohn/Sync/Applications/Library/tars/CLAUDE.md)

## Authority Order

When the docs differ, prefer:

1. `REBUILD_HANDOFF.md` for execution prerequisites and branch/packaging rules
2. `TARS_V3_REBUILD_PLAN.md` for the target architecture and build sequence
3. `Temp.md` for issue-driven requirements and user outcomes that must be covered
4. `TARS_V2_REBUILD_PLAN.md` for technical detail the v3 plan explicitly references
5. `TARS_REBUILD_FOUNDATION.md` for rationale, product lessons, and what should be preserved vs redesigned

## Branch and Repo Rules

1. Create branch `tars-3.0` from `main` before any implementation work.
2. Do not modify `main`.
3. Do not overwrite the current 2.x implementation in place.
4. If you discover a better approach than the plan specifies, use it only if you document the reason in `DECISIONS.md`.
5. Do not revert unrelated user changes.

## What The Rebuild Must Achieve

This rebuild is not a mechanical port. It must produce a usable TARS 3.0 system that:

- uses Obsidian as the durable operating surface
- uses `obsidian-cli` as the write interface
- uses schemas and `.base` files instead of hand-maintained indexes
- preserves the TARS operating model while redesigning brittle mechanics
- fully addresses the real-world issues described in `Temp.md`

## The Ten Issue Themes From Temp.md Must Be Explicitly Covered

Your implementation must clearly address all of these:

1. Transcript format variability and mandatory calendar/date resolution
2. Review-before-create task UX for meeting processing and bulk inbox work
3. Ask-don’t-assume behavior for names and other ambiguous cases
4. Automatic organization and metadata/companion handling for user-added files
5. Quick-capture screenshot/image processing with contextual inference
6. Transcript-linked fallback lookup when summaries omit details
7. Check-before-writing knowledge discipline across the framework
8. Negative-statement capture with later cleanup/reporting workflow
9. Self-evaluation backlog for repeated issues and user ideas
10. Scheduled briefings and maintenance using reliable scheduling tools when available

Do not merely preserve the “how” described in `Temp.md`. Preserve the “why” and the intended user outcome.

## Hard Requirements Already Derived From Temp.md

These are mandatory design constraints for the rebuild:

1. Meeting processing must always check calendar context before finalizing transcript interpretation, even if the transcript itself contains a date.
2. Meeting task extraction must always present a low-friction review surface before durable task creation.
3. Ambiguity must trigger bounded questions instead of silent assumptions.
4. Human-added files must be organized and made queryable through metadata or companion notes.
5. Screenshot/image quick capture must be a first-class supported path, not an afterthought.
6. Journal entries must link back to archived transcripts so answer workflows can fall back to the raw record.
7. The system must check what it already knows before persisting new memory/tasks/decisions.
8. Negative statements about people must be reviewable and removable later.
9. The framework must maintain its own backlog of repeated failures and user-requested ideas without flooding duplicates.
10. Briefings and maintenance should support scheduled execution, not only manual invocation.

## Environment Prerequisites

These are required for a fully working rebuild.

### A. Obsidian skills package

The rebuild assumes the agent has access to the `obsidian-skills` command references, including:

- `obsidian-cli/SKILL.md`
- `obsidian-bases/SKILL.md`
- `obsidian-markdown/SKILL.md`
- `json-canvas/SKILL.md`
- `defuddle/SKILL.md`

The current repo does **not** have these installed in `.claude/skills/`.

Current observed state:

- local `.claude/skills/` in this repo: missing
- user-level `.claude/skills/`: missing

So before implementing vault-interaction logic, do one of:

1. Install/provide the Obsidian skills into `.claude/skills/` in the working tree, or
2. Stop and report that the API reference is missing

Do not guess command syntax if the skills are unavailable.

### B. Obsidian CLI / running Obsidian

The rebuild assumes a working `obsidian-cli`/Obsidian environment.

Current observed shell state:

- `obsidian` command: missing

Before running integration or end-to-end vault tests, do one of:

1. Install/configure the required Obsidian CLI environment and connect it to a running Obsidian vault, or
2. Stop and report the blocker precisely

Do not claim integration readiness without this.

### C. Scheduler capability

The rebuild plan expects scheduled tasks support for briefings and maintenance. If the execution environment exposes `CronCreate`/`CronList`/`CronDelete` or equivalent scheduling, use it. If not, implement the integration points and document the missing runtime scheduler as a blocker or deferred dependency.

## Preflight Checks

Before writing code, verify:

1. Git repo is available and on `main`
2. Branch `tars-3.0` is created
3. Required reference docs are readable
4. Obsidian skills are available or explicitly missing
5. Obsidian CLI/runtime is available or explicitly missing
6. You understand the phased build sequence in Part G of the v3 plan

If prerequisites 4 or 5 are missing, document them immediately in `DECISIONS.md` or a blocker note before proceeding with assumptions.

## Current Repo Context You Should Preserve/Use

The current repo already contains the legacy TARS framework implementation, including:

- skill definitions in `skills/`
- reference files in `reference/`
- scripts in `scripts/`
- existing `CLAUDE.md`

Use the existing repo to understand:

- what capabilities already exist
- what operational logic should survive
- what naming, workflow, and structure problems the rebuild must avoid copying

Do not blindly carry forward:

- duplicate distribution trees
- index-note maintenance as a primary architecture
- brittle assumptions from legacy integrations
- prompt-only guarantees that need deterministic enforcement

## Build Sequence

Follow Part G of [TARS_V3_REBUILD_PLAN.md](/Users/ajayjohn/Sync/Applications/Library/tars/TARS_V3_REBUILD_PLAN.md) in order.

At a high level:

1. Pre-build branch creation
2. Phase 1 foundation
3. Phase 2 high-value expansion
4. Phase 3 advanced capabilities

Do not jump ahead and implement advanced features before the foundation is structurally complete and tested.

## Phase 1 Must-Have Areas

These must be complete before moving on:

- vault scaffolding
- `_system/` files
- templates
- `.base` views
- schema validation
- secret scanning
- flagged-content scanner
- core skill and vault `CLAUDE.md`
- alias registry and name resolution
- onboarding flow
- memory save
- task extraction
- meeting processing
- daily briefing
- fast lookup
- health check and maintenance
- activity logging
- smoke tests

## Phase 2 High-Value Areas

- weekly briefing
- inbox processing
- strategic analysis modes A and B
- communication drafting
- sync
- archive management

## Phase 3 Advanced Areas

- executive council
- deep analysis chain
- discovery mode
- initiative planning and status
- wisdom extraction
- artifact creation
- canvas generation

## Implementation Rules

1. Use the V3 plan’s architectural choices even when the current repo uses older patterns.
2. Use the V2 plan for exact schema detail and `.base` details where the V3 plan says to do so.
3. Preserve the memory model, durability test, accountability test, journal-first persistence, and provider-agnostic integration model.
4. Turn prompt-level guarantees into deterministic validation or script-backed enforcement wherever feasible.
5. When you discover under-specified gaps, document them in `DECISIONS.md` and choose the least brittle option.

## Testing Requirements

You must test as you go.

### Minimum expectations

1. Run smoke tests after scaffolding
2. Run schema validation when schemas and templates exist
3. Run integration tests if and only if Obsidian CLI/runtime is actually available
4. Run end-to-end tests on the critical path before declaring the rebuild complete

### If environment is blocked

If Obsidian CLI/runtime or scheduling tools are unavailable:

- still complete all static/code/documentation work you can
- clearly separate “implemented but not integration-tested” from “fully verified”
- report the precise blocker in the final output

## Required Deliverables

At minimum, produce:

- branch `tars-3.0`
- all files required by the V3 phased build sequence
- `DECISIONS.md` documenting justified deviations and prerequisite blockers
- updated `CLAUDE.md` for the v3 system
- tests/smoke coverage as specified by the plan

If you add scaffolding helpers, fixtures, or migration placeholders needed for correctness, include them and document why.

## Definition Of Done

The rebuild is complete only when:

1. The v3 structure exists and matches the plan materially
2. The ten Temp.md issue themes are clearly covered in the resulting implementation
3. Foundation, workflows, schemas, and views are in place
4. Validation and smoke tests pass, or blocked tests are precisely documented
5. The system is on `tars-3.0`, not `main`
6. The current 2.x implementation remains untouched on `main`

## Failure Conditions

Stop and report rather than bluffing if:

- Obsidian skills are unavailable and command syntax would need guessing
- Obsidian CLI/runtime is unavailable and a claimed integration test would be fake
- branch creation from `main` fails
- a required V3/V2 reference document is missing

## Final Response Requirements

When done, report:

- whether the rebuild completed fully or partially
- current branch
- which phases were completed
- what was tested
- what remains blocked by environment prerequisites
- any major deviations from the plan
- where `DECISIONS.md` lives

## One-Line User Prompt

If invoked conversationally, the intended instruction is:

“Read [REBUILD_HANDOFF.md](/Users/ajayjohn/Sync/Applications/Library/tars/REBUILD_HANDOFF.md) and execute the rebuild exactly as specified.”
