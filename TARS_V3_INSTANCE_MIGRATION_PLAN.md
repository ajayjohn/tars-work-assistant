# TARS 3.0 Legacy Instance Migration Plan

**Date:** 2026-03-21  
**Status:** Ready for agent execution after preflight decisions  
**Source instance verified:** `/Users/ajayjohn/Sync/Applications/TARS-Work/`  
**Target:** TARS v3 Obsidian vault built from `TARS_V3_REBUILD_PLAN.md`

## Purpose

This plan tells an AI agent how to migrate an already-used legacy TARS workspace into TARS v3 without losing working knowledge, creating invalid V3 notes, or silently dropping edge-case data. It is based on:

- Full review of `TARS_V3_REBUILD_PLAN.md`
- Full review of `TARS_V2_REBUILD_PLAN.md`
- Full review of `TARS_REBUILD_FOUNDATION.md`
- Direct inspection of the live source instance at `/Users/ajayjohn/Sync/Applications/TARS-Work/`

This is a **content migration plan**, not a greenfield onboarding flow.

## Non-Negotiable Migration Rules

1. The migration must be **non-destructive**. Never edit the source instance in place.
2. The migration must be **idempotent**. Re-running it must not duplicate notes or tasks.
3. The migration must be **schema-safe**. Never force a legacy file into the wrong V3 schema.
4. The migration must preserve **provenance**. Every migrated note must retain a link back to its legacy source path.
5. The migration must preserve **retrievability**. Raw transcripts and raw documents must remain accessible after migration.
6. The migration must prefer **explicit unresolved states** over guesses.
7. The migration must produce a **migration report** and a **file mapping manifest**.

## Source Instance Snapshot

These observations come from the live source instance, not from the design docs:

- Total files: `397`
- Markdown files: `312`
- Text transcripts: `44`
- PowerPoints: `6`
- PDFs: `5`
- CSVs: `1`
- YAML files: `2`

### Top-level source layout

- `memory/` contains `165` Markdown notes
- `journal/` contains `95` Markdown notes
- `inbox/` contains `43` completed transcript-like `.txt` files and `1` pending placeholder
- `contexts/` contains `33` Markdown files plus `10` non-Markdown artifacts
- `archive/` contains `8` Markdown files with no frontmatter
- `reference/` contains `9` legacy config docs/files
- Hidden operational state exists in `.agent/` and `.claude/`
- Root-level user artifacts exist outside the formal TARS folders

### Memory inventory

- `people/`: `70` files including `_index.md`
- `decisions/`: `51` files including `_index.md`
- `initiatives/`: `24` files including `_index.md`
- `vendors/`: `7` files including `_index.md`
- `products/`: `6` files including `_index.md`
- `organizational-context/`: `5` files including `_index.md`
- `competitors/`: `1` file (`_index.md` only)
- `memory/_index.md` exists and is stale

### Journal inventory

- `2026-01/`: `22` files
- `2026-02/`: `48` files
- `2026-03/`: `25` files

### Current journal type drift

Observed `type:` values:

- `meeting`: `51`
- `briefing-weekly`: `5`
- `briefing-daily`: `3`
- `journal`: `3`
- `1:1`: `3`
- `journal-index`: `2`
- `briefing`: `1`
- `wisdom`: `1`
- `team-meeting`: `1`
- `planning-meeting`: `1`
- `strategic-review`: `1`
- no frontmatter at all: `2`
- frontmatter present but no `type`: `21`

### Other source realities the migration must handle

- There is **no git repository** in the source instance.
- The source still uses legacy `reference/` rather than V3 `_system/`.
- The source still uses legacy `_index.md` files and some are already stale:
  - `memory/_index.md` says `40` decisions; actual decision notes are `50`
  - `memory/people/_index.md` says `68`; actual people notes are `69`
  - `memory/initiatives/_index.md` says `22`; actual initiative notes are `23`
- There are `43` completed raw transcript `.txt` files in `inbox/completed/`.
- In this legacy instance, `inbox/completed/` functions as a de facto raw transcript store, not as disposable cleanup residue.
- Only a minority of journal notes directly reference inbox transcript paths in frontmatter.
- There are `231` unchecked checkbox tasks across `journal/`, `memory/`, `contexts/`, and `archive/`.
- There are no dedicated V3-style task notes in the source instance.
- `contexts/` contains both structured `product-spec` notes and many unstructured Markdown artifacts.
- `archive/` contains valuable Markdown documents with no frontmatter.
- Hidden compatibility/config files exist:
  - `.agent/.tars-compat.json`
  - `.agent/rules/*`
  - `.agent/workflows/*`
  - `.claude/settings.json`
  - `.claude/settings.local.json`
- Source quality issues already exist:
  - malformed wikilinks such as `[Justin Mclure]]` and `[Duc Le]]`
  - unresolved alias placeholders in `reference/replacements.md`
  - stale maturity/housekeeping metadata
  - mislabeled source references, e.g. `source_file: "inbox/completed/Keith + AJ 1-1.txt"` on a Hilary 1:1 journal

## Critical V3 Spec Gaps To Resolve Before Migration

The migration agent must pause and document these in `DECISIONS.md` before the first real write batch:

### 1. Tasks folder gap

V3 defines `tars/task` notes, task bases, and task workflows, but Part B does not define a physical `tasks/` folder.  
**Required decision:** create `/tasks/` in the target vault and store all task notes there.

### 2. Markdown context file gap

V3 cleanly defines schemas for memory, journal, transcript, companion, issue, and idea notes, but not for legacy Markdown context documents such as:

- `contexts/products/*.md`
- `contexts/artifacts/*.md`
- unstructured root/context Markdown working docs
- legacy archive Markdown analyses

**Required decision:** do not force these into the wrong schema. Preserve them as content files, and create wrapper/bridge notes only when needed.

### 3. Transcript schema strictness

V3 transcript notes require `tars-journal-entry`. Some source transcripts have no reliable linked journal entry.  
**Required decision:** for unmatched transcripts, create a minimal legacy-import journal note first, then attach the transcript to that note.

## Migration Strategy

The migration should happen into a **new v3 vault**, never inside the legacy workspace. The old workspace remains frozen as the rollback source of truth.

The migration has four layers:

1. **Vault scaffolding and migration workspace**
2. **Strictly-typed TARS-managed content**
3. **Legacy content preserved as plain content or wrapped content**
4. **Validation, reconciliation, and cutover**

## Phase 0: Preflight and Freeze

1. Verify read access to `/Users/ajayjohn/Sync/Applications/TARS-Work/`.
2. Create a timestamped full backup copy of the source instance.
3. Create the new v3 vault from the authoritative V3 build plan.
4. Add a migration workspace in the target vault:
   - `_system/migration/`
   - `_system/migration/manifests/`
   - `_system/migration/reports/`
5. Generate immutable source manifests before transforming anything:
   - `source-file-inventory.csv`
   - `source-frontmatter-audit.csv`
   - `source-task-extract.csv`
   - `source-transcript-map.csv`
   - `source-alias-map.csv`
6. Write a `DECISIONS.md` capturing the three spec gaps above and any later migration-only rules.
7. Explicitly mark `inbox/completed/*.txt` as **preserve-and-link assets** so no cleanup, archive, or dedupe step treats them as deletion candidates.

## Phase 1: Build the Target V3 Vault First

Do not start content migration until the target vault already has:

- Full V3 folder structure
- `_system/*.md|yaml`
- `_views/*.base`
- `templates/*.md`
- `scripts/*.py`
- `skills/*`
- `CLAUDE.md`
- `tasks/` folder added by migration decision

Then run V3 smoke tests before importing legacy content.

## Phase 2: Migrate Legacy System/Reference State

### Direct mappings

| Source | Target | Notes |
|---|---|---|
| `reference/integrations.md` | `_system/integrations.md` | Preserve provider notes, then normalize wording for V3 |
| `reference/taxonomy.md` | `_system/taxonomy.md` | Replace with V3 version, but preserve legacy-only concepts in migration report |
| `reference/kpis.md` | `_system/kpis.md` | Copy content, normalize headings only |
| `reference/schedule.md` | `_system/schedule.md` | Preserve even if empty |
| `reference/guardrails.yaml` | `_system/guardrails.yaml` | Merge carefully with V3 guardrail schema |
| `reference/maturity.yaml` | `_system/maturity.yaml` | Preserve as historical state, then normalize counters |
| `reference/.housekeeping-state.yaml` | `_system/housekeeping-state.yaml` | Preserve history but mark as imported-from-legacy |
| `reference/replacements.md` | `_system/alias-registry.md` | Transform, do not copy verbatim |

### Legacy reference docs that should not become active V3 system files

These should be copied into `_system/migration/legacy-reference/` for audit only:

- `reference/shortcuts.md`
- `reference/workflows.md`

### Alias registry transformation rules

Transform `reference/replacements.md` into `_system/alias-registry.md` as follows:

1. Split entries into:
   - ambiguous names
   - people aliases
   - team abbreviations
   - product abbreviations
   - vendor abbreviations
2. Convert flat replacements into canonical mappings.
3. Preserve unresolved entries like `??` under a `Needs Verification` section.
4. Deduplicate repeated entries such as duplicate `Michel`.
5. Add migration provenance note for every unresolved or suspect mapping.

## Phase 3: Migrate Memory Notes

### Folder mappings

| Source | Target |
|---|---|
| `memory/people/` | `memory/people/` |
| `memory/vendors/` | `memory/vendors/` |
| `memory/competitors/` | `memory/competitors/` |
| `memory/products/` | `memory/products/` |
| `memory/initiatives/` | `memory/initiatives/` |
| `memory/decisions/` | `memory/decisions/` |
| `memory/organizational-context/` | `memory/org-context/` |

### General memory transform rules

For every source memory note that is not an `_index.md`:

1. Preserve the filename slug unless it conflicts with an existing canonical entity slug.
2. Convert source frontmatter to V3 frontmatter.
3. Preserve the original legacy frontmatter block inside a `## Legacy Metadata` section or HTML comment in the body.
4. Preserve the original body content unless it contains blocked secrets.
5. Add provenance fields in body text:
   - legacy source path
   - imported date
6. Normalize wikilinks where the target canonical note is known.
7. If a field is malformed or missing, infer only when confidence is high; otherwise flag for review.

### Memory field mapping

| Legacy field | V3 field |
|---|---|
| `summary` | `tars-summary` |
| `staleness` | `tars-staleness` |
| `updated` | `tars-modified` |
| `date` | `tars-date` where appropriate by type |
| `status` | `tars-status` |
| `owner` / `owned_by` | `tars-owner` |
| `decision_maker` | `tars-decided-by` |
| `participants` on decisions | `tars-stakeholders` |
| `related_initiatives` / `initiatives` | `tars-affects` or `tars-initiatives` depending on note type |

### Type-specific rules

#### People

- Required tag: `tars/person`
- `aliases` stays as native `aliases`
- Convert plain relationship bullets into body links; do not invent unsupported frontmatter properties
- Set:
  - `tars-summary`
  - `tars-staleness`
  - `tars-created` = best known original date or imported date if unknown
  - `tars-modified` = legacy `updated`

#### Initiatives

- Required tag: `tars/initiative`
- Map legacy `status` values:
  - `active` -> `active`
  - `at-risk` -> `active` plus `tars-health: red` or `yellow` based on body language
  - `planned` -> `planning`
  - if unclear, preserve as `active` and note ambiguity in migration report
- If owner exists only in body, infer cautiously and flag if not explicit

#### Decisions

- Required tag: `tars/decision`
- Use legacy filename date as fallback for missing decision date
- Map:
  - `status` -> `tars-status`
  - `decision_maker` -> `tars-decided-by`
  - `participants` or `stakeholders` -> `tars-stakeholders`
  - `initiatives` / `affects` -> `tars-affects`
- If `summary` is missing, derive it from the title
- Files missing `type` or `summary` must be repaired during import

#### Products

- Required tag: `tars/product`
- Use product summary note only for durable product identity
- Detailed specs stay in `contexts/products/` and should be linked from the product note body

#### Org context

- Source folder name changes from `organizational-context` to `org-context`
- Required tag: `tars/org-context`
- Preserve body content as durable organizational context

### Memory files to exclude from direct migration

Do not migrate these as real entity notes:

- `memory/_index.md`
- `memory/*/_index.md`

Instead:

- record them in the migration report
- compare their counts to reality
- delete them from the target
- rely on `.base` files in v3

## Phase 4: Migrate Journal Notes

### Journal type normalization

| Legacy type | V3 destination | V3 tag pattern |
|---|---|---|
| `meeting` | Meeting journal | `tars/journal`, `tars/meeting` |
| `1:1` | Meeting journal | `tars/journal`, `tars/meeting` |
| `team-meeting` | Meeting journal | `tars/journal`, `tars/meeting` |
| `planning-meeting` | Meeting journal | `tars/journal`, `tars/meeting` |
| `strategic-review` | Meeting journal | `tars/journal`, `tars/meeting` |
| `journal` | Usually meeting journal; review body before import |
| `briefing-daily` | Daily briefing | `tars/journal`, `tars/briefing` |
| `briefing-weekly` | Weekly briefing | `tars/journal`, `tars/briefing` |
| `briefing` | Determine daily vs weekly from title/body |
| `wisdom` | Wisdom journal | `tars/journal`, `tars/wisdom` |
| missing type | classify from title/body sections |

### Journal classification heuristics for missing/invalid types

Classify as meeting if the note contains most of:

- `## Topics`
- `## Updates`
- `## Concerns`
- `## Decisions`
- `## Action Items`
- participants or organizer metadata

Classify as briefing if it contains:

- schedule table
- priority tasks
- people context
- system status

Classify as wisdom if it is source-analysis oriented and not tied to a specific meeting.

If confidence is below 80%, create a migration review entry instead of guessing.

### Journal frontmatter transform rules

Map legacy fields to V3:

| Legacy field | V3 field |
|---|---|
| `date` | `tars-date` |
| `time` + `date` | `tars-meeting-datetime` if parseable |
| `participants` | `tars-participants` as wikilinks |
| `organizer` | `tars-organizer` |
| `topics` | `tars-topics` |
| `initiatives` | `tars-initiatives` |
| `source` | `tars-source` |
| `calendar_title` | `tars-calendar-title` |
| `duration` | body-only unless target schema is extended |

### Body preservation rules

Keep all substantive sections exactly as narrative body content, including:

- Topics
- Updates
- Concerns
- Decisions
- Action Items
- Notes
- Unverified/uncertain sections

Do not flatten or summarize away useful narrative detail.

### Journal files that need special handling

- `journal/*/_index.md` are legacy indexes and must not migrate as journal notes
- the two journal files with no frontmatter must be reconstructed from filename/body before import
- any journal note with mismatched `source_file` must keep a migration warning

## Phase 5: Extract and Create V3 Task Notes

The source instance does not have a trustworthy local task note system. Tasks live as inline checkboxes and action tables across content.

### Task extraction sources

Extract tasks from:

- journal checkbox lists
- `## Action Items` tables
- explicit owner/action rows
- action bullets in memory/context/archive files

### Task migration principle

Preserve all unresolved tasks, but do not leave them buried in bodies only. V3 needs actual `tars/task` notes.

### Task creation rules

For each extracted task:

1. Create a deterministic import key from:
   - source file path
   - task text
   - source line number
2. Use that import key to guarantee idempotency.
3. Set `tags: [tars/task]`
4. Set `tars-status`:
   - unchecked -> `open`
   - checked -> `done`
5. Resolve `tars-owner` from explicit owner text or default to the named person if the bullet starts with a person.
6. Set `tars-source` to the migrated journal note link.
7. Parse due dates from:
   - explicit ISO dates
   - embedded relative references already resolved in the journal text
8. Set `tars-project` when an initiative is clearly associated.
9. Preserve original task wording in the body.
10. Add a legacy provenance block with source path and line number.

### Task review tiers

Because the source contains `231` open checkboxes, the migration should split them into:

- `high-confidence tasks`: create automatically
- `needs-review tasks`: create in a migration review note first if owner/due/source are ambiguous

High-confidence means:

- concrete wording
- identifiable owner
- identifiable source note

If owner is unclear, use the review queue rather than guessing.

## Phase 6: Migrate Raw Transcripts From Inbox

### Source reality

The source still has `43` completed transcript `.txt` files in `inbox/completed/`. For this legacy instance, those files are not trash and they are not normal inbox residue. They are the raw transcript corpus that v3 is supposed to keep searchable and linkable.

### Transcript preservation rule

`inbox/completed/*.txt` files are **never deletion candidates** during migration. They must be reorganized into the v3 transcript system so detailed lookup can point back to the transcript itself.

### Transcript migration rules

1. Every `.txt` transcript in `inbox/completed/` becomes a preserved transcript artifact.
2. Convert each legacy transcript into a V3 transcript note in `archive/transcripts/YYYY-MM/`.
3. The **body of the transcript note must contain the raw transcript text** so V3 detailed search and transcript fallback can read the actual conversation.
4. Preserve original provenance in the transcript note body:
   - original legacy path
   - original filename
   - import batch id
5. If desired, also preserve the original raw `.txt` as a sidecar file under `_system/migration/raw-transcripts/`, but the searchable V3 source of truth must be the transcript note.
6. Link each transcript note to a migrated journal note via `tars-journal-entry`.
7. Do not leave migrated transcripts in `inbox/processed/`; transcripts belong in `archive/transcripts/`.

### Matching order for transcript -> journal association

1. Exact frontmatter `source` or `source_file` match in a journal note
2. Filename/title similarity
3. Date extracted from transcript header
4. Participant overlap between transcript text and journal note
5. Calendar title/body correlation

### If no journal match exists

Create a minimal legacy-import journal note:

- title: `YYYY-MM-DD Legacy Transcript Import - <slug>`
- tags: meeting journal tags
- `tars-source: transcript`
- body: note that the transcript was imported from legacy inbox without a confirmed processed journal

Then attach the transcript note to that journal stub so the transcript schema remains valid.

### Relationship to V3 inbox cleanup

Do not apply the normal v3 maintenance rule for processed inbox items to these legacy transcript imports. Once imported, they are no longer inbox items at all; they are permanent transcript records in `archive/transcripts/`.

### Transcript format classification

Classify each transcript as one of:

- `raw_text`
- `unknown`
- or specific vendor format if reliably detected

Do not guess Otter/Zoom/etc. without evidence.

## Phase 7: Migrate Context Files and User Documents

### Important rule

Do not force all context documents into memory schemas. Many are working docs, specs, drafts, or artifacts, not memory entities.

### Context classes

#### A. Product specification notes

Source: `contexts/products/*.md`

Plan:

- keep them in `contexts/products/`
- preserve content largely as-is
- normalize filenames only if needed
- ensure each has a linked `memory/products/*.md` summary note where a product entity exists
- add provenance header in body if frontmatter is not standardized

#### B. Working markdown artifacts

Source:

- `contexts/*.md`
- `contexts/artifacts/*.md`
- root Markdown docs that are user content rather than framework files

Plan:

- move into `contexts/YYYY-MM/` or `contexts/artifacts/` based on content
- preserve as plain Markdown content if no native V3 schema fits
- create bridge notes only where the artifact should appear in journal or memory retrieval

#### C. Non-Markdown artifacts

Source:

- PDFs
- PPTX files
- CSV
- text dumps that are reference docs rather than transcripts
- root-level PDFs/PPTX files

Plan:

1. Place files in date-organized `contexts/YYYY-MM/` or `contexts/artifacts/`
2. Create a `tars/companion` note for each non-Markdown file
3. Populate:
   - `tars-original-file`
   - `tars-original-type`
   - `tars-file-size`
   - `tars-added-date`
   - `tars-source: legacy-import`
   - `tars-summary`
4. Link companions to any relevant memory/journal notes

### Files to exclude as noise

Do not migrate these as meaningful artifacts:

- `.DS_Store`
- Office lock temp files such as `~$CX26-DES-Data-Intelligence-Presentation.pptx`

Record exclusions in the migration report.

## Phase 8: Migrate Archive Content

The source `archive/` contains Markdown documents with no frontmatter. These are preserved knowledge artifacts, not disposable clutter.

### Archive migration rules

1. Do not discard them.
2. Do not force them into invalid TARS schemas.
3. Move them into `archive/legacy/` or `archive/YYYY-MM/legacy/` in the new vault.
4. Preserve filenames and content.
5. Create an archive manifest note listing:
   - original path
   - new path
   - inferred content class
   - linked entities if known

### Optional uplift

If an archive file clearly maps to a V3 journal analysis or wisdom entry, the agent may create a new V3 note that links to the preserved legacy archive file. The preserved raw file remains the source artifact.

## Phase 9: Hidden Operational State

### `.agent/`

Preserve for audit only under `_system/migration/legacy-agent/` or external backup:

- `.tars-compat.json`
- rules
- workflow definitions

Do not activate these in v3.

### `.claude/`

Preserve as historical config only:

- `settings.json`
- `settings.local.json`

Do not treat these as active Obsidian configuration.

### Root framework docs

These root files are framework docs, not user knowledge:

- `TARS_REBUILD_FOUNDATION.md`
- `TARS_V2_REBUILD_PLAN.md`
- `TARS_V3_REBUILD_PLAN.md`
- `AGENTS.md`
- `CLAUDE.md`

Migration behavior:

- do not import them as user journal/memory/context content
- preserve copies under `_system/migration/legacy-framework-docs/` if desired
- create the new v3 `CLAUDE.md` from the authoritative rebuild plan, not from the source instance

## Phase 10: Validation and Reconciliation

After migration, run all of the following:

### Schema validation

- every TARS-managed note validates against `_system/schemas.yaml`
- no migrated TARS-managed note uses legacy unprefixed fields as active frontmatter

### Link validation

- all `tars-participants`, `tars-owner`, `tars-decided-by`, `tars-affects`, `tars-project`, and transcript backlinks resolve
- malformed links repaired where possible
- unresolved names logged in alias registry and migration report

### Count reconciliation

Produce a report comparing source vs target counts:

- people
- initiatives
- decisions
- products
- vendors
- org-context notes
- journal notes by class
- transcripts preserved
- task notes created
- context artifacts preserved
- excluded noise files

### Provenance validation

Every migrated TARS-managed note must include or be traceable to:

- source legacy path
- import batch id
- import timestamp

### Transcript validation

- every imported transcript note links to a journal note
- every imported transcript note contains the raw transcript body text, not just a summary
- every journal note created from transcript import either links to a transcript or explicitly states none exists

## Phase 11: Migration Report Outputs

The agent must generate:

- `_system/migration/reports/migration-summary.md`
- `_system/migration/reports/schema-exceptions.md`
- `_system/migration/reports/unresolved-aliases.md`
- `_system/migration/reports/task-review-queue.md`
- `_system/migration/reports/transcript-match-report.md`
- `_system/migration/manifests/file-map.csv`
- `_system/migration/manifests/exclusions.csv`

`migration-summary.md` should include:

- what was migrated
- what was preserved but not schema-upgraded
- what was excluded
- what needs human review
- what V3 design gaps were patched for migration

## Recommended Execution Order

1. Freeze and back up source instance.
2. Create new v3 vault and run pre-migration smoke tests.
3. Record source manifests.
4. Resolve migration-only design decisions.
5. Migrate `_system`-equivalent reference/config state.
6. Migrate memory entities.
7. Migrate journal notes.
8. Extract and create task notes.
9. Migrate transcripts and attach them to journals.
10. Migrate contexts and non-Markdown artifacts.
11. Migrate legacy archive content.
12. Preserve hidden operational state for audit.
13. Run validation suite.
14. Generate reports.
15. Review unresolved items.
16. Only then switch active use to the v3 vault.

## Hard Failure Conditions

The migration agent must stop and report instead of continuing when:

- a target write would create invalid V3 frontmatter
- two canonical entities collide and cannot be safely merged
- a transcript cannot be matched and the agent also cannot create a safe journal stub
- secret scan finds blocked secrets in content being converted into TARS-managed notes
- more than 5% of migrated TARS-managed notes fail schema validation

## Acceptance Criteria

The migration is successful only if all are true:

1. No source content is lost.
2. All source memory entities exist in valid V3 form or are explicitly reported as exceptions.
3. All journal entries exist in valid V3 form or are explicitly reported as exceptions.
4. All legacy transcripts are preserved and retrievable.
5. No legacy completed-inbox transcript was treated as a deletion candidate.
6. All non-Markdown artifacts are preserved and discoverable via companion notes.
7. Inline legacy tasks are no longer trapped only inside bodies; they exist as task notes or in a review queue.
8. All legacy index files are removed from active use.
9. Alias normalization is preserved in `_system/alias-registry.md`.
10. The target vault passes V3 smoke tests and schema validation.
11. A human can answer:
   - what moved
   - what changed
   - what was left alone
   - what still needs review

## Source-Specific Red Flags To Call Out In The Final Report

- Source is not under git; backup is mandatory.
- Legacy indexes are stale and cannot be trusted as ground truth.
- Source transcript-to-journal linkage is incomplete.
- The source task system is implicit, not note-based.
- Some context/archive content has no schema and must remain preserved legacy content.
- Some journal notes have missing `type`, missing frontmatter, or mislabeled sources.
- Some memory notes use `name:` instead of `title:` and some are missing `summary:`.
- There are malformed wikilinks and unresolved aliases already present in the source.

## Bottom Line

The right migration is **not** a blind frontmatter rewrite. It is a staged import that:

- upgrades true TARS-managed knowledge into strict v3 schemas
- preserves raw operational evidence like transcripts and documents
- extracts actionable tasks into first-class task notes
- carries forward alias intelligence and provenance
- refuses to invent false certainty where the legacy instance is incomplete

That is the only way to make the migrated TARS v3 vault fully usable without schema drift, broken history, or lost context.
