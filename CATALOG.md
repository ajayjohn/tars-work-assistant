<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS Catalog

TARS is a persistent executive assistant framework built around an Obsidian vault. It is designed for senior knowledge workers who need continuity across meetings, decisions, tasks, stakeholder context, and long-running initiatives.

## Executive summary

TARS addresses three chronic problems in modern knowledge work:
- context decays faster than people can rehydrate it
- meeting follow-through is inconsistent and hard to audit
- strategic work is often detached from the evidence trail that produced it

TARS solves those problems by treating the vault as a structured operating system rather than a pile of notes. It combines durable memory, transcript-backed retrieval, task review gates, live views, and maintenance workflows so the assistant stays useful over time instead of becoming another capture layer that drifts out of date.

## What makes TARS different

TARS is intentionally opinionated about how a long-lived assistant should work:
- Obsidian is the native runtime, not a secondary destination
- `obsidian-cli` is the write path for managed vault changes
- `.base` files replace manual `_index.md` maintenance
- transcript archives are first-class retrieval assets
- tasks and memory go through explicit review before persistence
- schemas, guardrails, aliasing, and maintenance state live in `_system/`

The result is a framework that is stable for months-long use, especially when the vault accumulates hundreds of journal entries, transcripts, and memory notes.

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

TARS supports structured strategic analysis, stakeholder-aware drafting, initiative planning, and artifact creation while grounding those outputs in what the vault already knows.

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
