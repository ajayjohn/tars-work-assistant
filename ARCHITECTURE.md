<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS 3.0 Architecture

This document describes the current framework architecture after the Obsidian-native rebuild.

**Version**: 3.0.0  
**Release**: 2026-03-22  
**Model**: Framework repository plus deployed Obsidian vault runtime

## System model

TARS 3.0 operates directly on an Obsidian vault and treats that vault as the persistent runtime state.

At a high level:
- the repository is the framework source, packaging logic, and documentation
- the vault is the live operating environment where memory, journal entries, transcripts, and context live
- `obsidian-cli` is the canonical write interface for vault mutations
- TARS-managed notes use schema-validated `tars-` properties and `tars/` tags
- Obsidian Bases provide live query surfaces instead of hand-maintained index notes

Only skill metadata loads eagerly at session start. With 12 skills, the lightweight baseline is roughly 48 tokens before deeper instructions are loaded on demand.

## Repository layout

The current framework source is centered on these directories:

```text
tars/
├── .claude-plugin/           Manifest and marketplace metadata
├── .claude/skills/           Obsidian helper skills used by the agent
├── skills/                   TARS protocol skills
├── commands/                 Slash-command wrappers
├── _system/                  Canonical v3 system files and defaults
├── _views/                   Obsidian `.base` query definitions
├── templates/                Canonical note templates
├── scripts/                  Deterministic maintenance and validation utilities
├── tests/                    Validators, fixtures, and smoke tests
├── build-plugin.sh           Supported packaging entrypoint
├── CLAUDE.md                 Live agent operating rules
├── README.md
├── GETTING-STARTED.md
├── ARCHITECTURE.md
├── BUILD.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

The framework currently ships 12 skills, 11 commands, and 13 scripts.

Some older directories remain in the repository for compatibility, migration context, or packaging history. They should not be treated as the active TARS 3.0 runtime architecture unless a specific document says otherwise.

## Deployed vault layout

`/welcome` or a migration process should produce a vault with this shape:

```text
_system/
  config.md
  integrations.md
  alias-registry.md
  taxonomy.md
  kpis.md
  schedule.md
  guardrails.yaml
  maturity.yaml
  housekeeping-state.yaml
  schemas.yaml
  changelog/
  backlog/issues/
  backlog/ideas/

_views/
  *.base

memory/
  people/
  vendors/
  competitors/
  products/
  initiatives/
  decisions/
  org-context/

journal/YYYY-MM/
contexts/
  products/
  artifacts/
  YYYY-MM/
inbox/pending/
inbox/processed/
archive/transcripts/YYYY-MM/
templates/
scripts/
```

Key runtime notes:
- `memory/` stores durable entity knowledge
- `journal/` stores dated outputs such as meeting notes and briefings
- `contexts/` stores deep reference material and generated artifacts
- `inbox/` is raw intake, not durable knowledge by itself
- `archive/transcripts/` preserves transcript text for future lookup and verification

## Runtime layers

### Interface layer

Users can work through natural language or explicit commands. The command layer remains intentionally thin:
- `/welcome`
- `/briefing`
- `/meeting`
- `/tasks`
- `/learn`
- `/answer`
- `/think`
- `/communicate`
- `/initiative`
- `/create`
- `/maintain`

Each command simply routes into the corresponding skill protocol.

### Protocol layer

The `skills/` directory is the behavioral core of the framework:
- `core` defines routing, write discipline, review gates, and persistence rules
- `meeting` handles transcript processing, matching, journaling, and follow-through
- `briefing`, `tasks`, `learn`, `answer`, `think`, `communicate`, `initiative`, `create`, `maintain`, and `welcome` cover the rest of the user-facing workflows

The framework uses one core skill and eleven user-invocable skills. Resource files such as `skills/think/manifesto.md` load only when a workflow needs them.

### State and schema layer

`_system/` is the canonical runtime control plane:
- `schemas.yaml` defines allowed TARS note shapes
- `alias-registry.md` resolves names and alternate forms
- `integrations.md` records how calendar, tasks, and other providers are configured
- `guardrails.yaml` and maintenance state files drive scans and scheduled upkeep
- `backlog/` stores framework issues and user improvement ideas

These files are part of the vault state, not separate background documentation.

### View layer

`_views/` contains live `.base` files for common operational questions:
- active tasks
- recent journal activity
- stale memory
- inbox backlog
- transcript archive coverage
- people, initiatives, vendors, products, competitors, and decisions

These bases replaced `_index.md` as the primary query surface. They reduce drift because they are computed from note properties rather than manually maintained.

### Template layer

`templates/` contains canonical note shapes for TARS-managed content, including:
- people, vendors, competitors, products
- initiatives and decisions
- meeting journals and briefings
- wisdom notes
- transcript notes
- issue and idea backlog entries
- companion notes for non-markdown artifacts

### Script layer

`scripts/` holds deterministic utilities that support the skills and release workflow. The active set includes schema validation, secret scanning, negative-sentiment scanning, health checks, archival, sync, version bumps, packaging, and validation helpers.

Not every script is a runtime dependency for end users. Some are maintainer tools used during packaging, testing, or migration support.

## Critical behavior changes in v3

The Obsidian-native rebuild introduced the most important architectural changes in the framework:
- live bases replace `_index.md` files
- raw transcript text is preserved as part of the searchable system
- tasks and durable memory are reviewed before persistence
- name resolution uses aliases, vault search, and user confirmation instead of flat replacements only
- maintenance state, schemas, and guardrails live in `_system/`
- the active runtime structure is centered on the vault, not a copied `reference/` bundle

## Core workflows

### Onboarding

`/welcome` scaffolds the vault, checks Obsidian connectivity, installs helper skills, writes system files, captures user context, and configures schedules.

### Meeting processing

`/meeting` follows a strict sequence:
1. resolve meeting date and title, using calendar context when available
2. draft the meeting journal entry
3. propose tasks that pass the accountability gate
4. propose durable memory updates that pass the durability gate
5. archive the transcript in a queryable transcript note linked back to the journal entry

### Answer and retrieval

`/answer` searches in this order:
1. memory
2. tasks
3. journal
4. transcript archive
5. integrations
6. external search only when necessary

This transcript fallback is one of the defining v3 behaviors because it lets TARS answer detailed historical questions without flattening everything into summaries.

## Release and packaging model

The supported release packaging path is the repository-root [build-plugin.sh](build-plugin.sh). It packages the v3 framework, helper skills, templates, system files, and scripts into `tars-cowork-plugin/`.

The packaged plugin is intentionally slimmer than the repository, but it should describe the same architecture and behaviors. Release documentation must stay aligned with the repository source, the packaged README, and `.claude-plugin/plugin.json`.
