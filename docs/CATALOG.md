<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS Catalog

TARS is a persistent executive assistant framework built around a local Markdown workspace. Obsidian is optional as a richer viewer. It is designed for senior knowledge workers who need continuity across meetings, decisions, tasks, stakeholder context, and long-running initiatives.

## Executive summary

TARS addresses three chronic problems in modern knowledge work:
- context decays faster than people can rehydrate it
- meeting follow-through is inconsistent and hard to audit
- strategic work is often detached from the evidence trail that produced it

TARS solves those problems by treating the workspace as a structured operating system rather than a pile of notes. It combines durable memory, transcript-backed retrieval, task review gates, optional live views, and maintenance workflows so the assistant stays useful over time instead of becoming another capture layer that drifts out of date.

For Obsidian users, the same workspace can be opened as a vault. The product term remains workspace because headless and Obsidian users share the same files and data model.

## What makes TARS different

TARS is intentionally opinionated about how a long-lived assistant should work:
- Markdown files and YAML frontmatter are the native runtime
- the local TARS helper (`tars-vault`) is the write path for managed workspace changes
- `.base` files are optional Obsidian views over the same workspace
- transcript archives are first-class retrieval assets
- `inbox/pending/` is the bulk intake surface for transcripts, PDFs, decks, docs, screenshots, exports, and rough notes
- tasks and memory go through explicit review before persistence
- schemas, guardrails, aliasing, and maintenance state live in `_system/`

The result is a framework that is stable for months-long use, especially when the workspace accumulates hundreds of journal entries, transcripts, and memory notes.

## Core capabilities

### Daily operating loop

TARS can assemble a daily or weekly briefing from:
- calendar context
- tasks and deadlines
- people context
- initiatives and decisions
- inbox backlog
- system health signals

### Meeting-to-execution pipeline

TARS turns a meeting transcript into:
- a meeting journal entry
- proposed tasks with clear ownership
- proposed durable memory updates
- preserved transcript notes linked to the journal record

### Inbox-to-memory pipeline

TARS also works when the input is not a clean meeting transcript. Users can drop many files into `inbox/pending/` and say "process inbox" or run `/maintain inbox`. TARS inventories the folder, classifies each item, routes transcripts to meeting processing, routes docs and articles to wisdom/context extraction, routes task-heavy notes to task review, and keeps source records in `inbox/processed/` or archive paths. If the active Claude environment cannot read a file type directly, TARS keeps a companion note and asks for extracted text instead of pretending the file was processed.

### Persistent memory

TARS maintains structured notes for:
- people
- products
- initiatives
- decisions
- vendors
- competitors
- organizational context

### Retrieval with evidence

The answer workflow searches memory first, then journal, then transcript archives, then integrations. This lets TARS answer both summary questions and detailed “what exactly was said?” questions without collapsing everything into prose summaries.

### Strategic and communication workflows

TARS supports structured strategic analysis, stakeholder-aware drafting, initiative planning, and artifact creation while grounding those outputs in what the workspace already knows.

### Persona-driven cold start (v3.2)

Onboarding is built around seven role personas — Product Leader, Sales / Customer-Facing, Delivery / PM, Data Science Lead, Architect / Staff Engineer, Support / Ops Lead, Engineering Manager. Each persona seeds role-aware briefing layout, BLUF level, default analysis mode, review-gate strictness, and starter taxonomy tags so the day-1 briefing is useful instead of empty.

Fast setup captures only the essentials. Deferred setup can be resumed with `/welcome --continue-setup` or "continue TARS setup" and is also suggested in the Daily Digest/help until completed or dismissed.

### Wikilink discipline (v3.2)

Every wikilink TARS writes is formed via the local helper’s `format_wikilink` tool, which normalizes smart quotes, sanitizes Obsidian-illegal characters, and resolves canonical names through the alias registry + workspace file lookup. Write tools and a pre-write hook reject any `[[…]]` containing forbidden characters. A retroactive `fix-wikilinks --repair-broken` mode classifies broken legacy links into `auto_safe` / `needs_review` / `unresolvable`, with apply-only-on-safe semantics.

### Self-improvement loop (v3.2)

A single weekly cron job (`tars-weekly-maintenance`, Sunday evening) opens a Claude session, rolls up telemetry, groups backlog issues, runs `/lint --actions`, surfaces user-model and workflow-alias proposals from `/learn --review-patterns`, runs the workspace-side curator (memory staleness 90d, workflow staleness 60d, persona-drift 30d with cooling-off windows), and writes everything to a numbered review queue at `inbox/pending/weekly-review-YYYY-MM-DD.md`. Nothing is auto-applied. The user reviews on next session.

## Who it is for

TARS is best suited to:
- executives with meeting-heavy schedules
- product and operations leaders managing many parallel initiatives
- chiefs of staff and strategic operators
- senior ICs who need continuity across decisions, context, and follow-through

It is less useful if you want a generic note-taking plugin without disciplined structure or if you do not want the assistant to maintain long-lived context.

## Why teams adopt it

The practical value usually shows up in four places:
- shorter time-to-context before meetings
- higher action-item accountability after meetings
- better recall of why decisions were made
- less duplication when answering recurring internal questions

The framework is opinionated on purpose. It prefers reliable persistence and auditable retrieval over frictionless but sloppy capture.

## Packaging and release shape

The public framework includes:
- skill protocols
- slash-command wrappers
- canonical templates
- system defaults
- live views
- deterministic maintenance scripts
- documentation for setup, architecture, release, and contribution

For release and packaging details, see [BUILD.md](BUILD.md).
