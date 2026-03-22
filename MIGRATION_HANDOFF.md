# TARS V3 Migration Handoff

Read this file and execute the migration. Do not ask for a broader overview first. Start work after reading the required documents below.

## Mission

Migrate the legacy TARS instance at:

`/Users/ajayjohn/Sync/Applications/TARS-Work/`

into a new TARS v3 Obsidian vault at:

`/Users/ajayjohn/Sync/Applications/TARS-V3-Vault/`

The migration must preserve all usable legacy content, make all TARS-managed notes valid for TARS v3, preserve transcript-level lookup, and produce a complete migration report plus review queues for anything ambiguous.

## Required Reads

Read these in this order before making any changes:

1. [MIGRATION_HANDOFF.md](/Users/ajayjohn/Sync/Applications/Library/tars/MIGRATION_HANDOFF.md)
2. [TARS_V3_INSTANCE_MIGRATION_PLAN.md](/Users/ajayjohn/Sync/Applications/Library/tars/TARS_V3_INSTANCE_MIGRATION_PLAN.md)
3. [TARS_V3_REBUILD_PLAN.md](/Users/ajayjohn/Sync/Applications/Library/tars/TARS_V3_REBUILD_PLAN.md)
4. [TARS_V2_REBUILD_PLAN.md](/Users/ajayjohn/Sync/Applications/Library/tars/TARS_V2_REBUILD_PLAN.md)
5. [TARS_REBUILD_FOUNDATION.md](/Users/ajayjohn/Sync/Applications/Library/tars/TARS_REBUILD_FOUNDATION.md)

Treat `TARS_V3_INSTANCE_MIGRATION_PLAN.md` as the migration authority and `TARS_V3_REBUILD_PLAN.md` as the target-vault authority.

## Source and Target

- Source legacy instance: `/Users/ajayjohn/Sync/Applications/TARS-Work/`
- Target v3 vault: `/Users/ajayjohn/Sync/Applications/TARS-V3-Vault/`
- Build/migration planning docs live in: `/Users/ajayjohn/Sync/Applications/Library/tars/`

## Core Execution Rules

1. Never migrate in place. The source instance is read-only except for optional backup copying.
2. If the target vault does not exist, create it and scaffold it according to the V3 rebuild plan before migrating content.
3. The migration must be non-destructive and idempotent.
4. Do not silently drop files.
5. Do not force legacy content into the wrong V3 schema.
6. Prefer explicit unresolved states and review queues over guessing.
7. Produce durable manifests and reports as part of the migration.

## Critical Instance-Specific Decisions Already Made

These are not optional. Follow them exactly.

1. Create a real `/tasks/` folder in the target vault even though the V3 plan under-specifies the physical task-note location.
2. Treat `inbox/completed/*.txt` in the legacy instance as preserved transcript assets, not cleanup residue and not deletion candidates.
3. Every migrated transcript must end up as a V3 transcript note in `archive/transcripts/YYYY-MM/`.
4. Every migrated transcript note must contain the raw transcript text in its body so detailed lookup can search the transcript itself.
5. If useful, you may also preserve original transcript `.txt` files under `_system/migration/raw-transcripts/`, but the searchable v3 source of truth must be the transcript note.
6. Legacy Markdown context and archive documents that do not cleanly fit a V3 schema must be preserved as content, not forced into memory/journal schemas.
7. Legacy `_index.md` files are not authoritative, must not be migrated as active notes, and should be replaced by V3 `.base` views.
8. For unmatched transcripts, create a minimal legacy-import journal note first, then link the transcript note to it so the transcript schema remains valid.

## Known Realities Of The Source Instance

Plan around these facts:

- The source is a real used instance with months of data.
- The source is not a git repository.
- The source contains hidden agent/config state in `.agent/` and `.claude/`.
- The source contains stale legacy indexes.
- The source contains inline checkbox tasks rather than a trustworthy local task-note system.
- The source contains raw transcripts in `inbox/completed/`.
- The source contains many context/archive documents with no frontmatter.
- The source contains malformed links, missing frontmatter on some notes, missing `type:` on many journal notes, and some mislabeled source references.

## Success Criteria

The migration is successful only if all are true:

1. No meaningful source content is lost.
2. All migrated TARS-managed notes validate against v3 schemas.
3. All legacy transcripts are preserved, linked, and searchable.
4. All non-Markdown artifacts are preserved and discoverable.
5. Legacy inline tasks are no longer trapped only inside note bodies; they exist as task notes or explicit review-queue items.
6. Alias normalization is preserved in `_system/alias-registry.md`.
7. The target vault passes v3 smoke tests and validation.
8. A human can review what changed, what was preserved as-is, and what still needs attention.

## Required Final Outputs

Create these outputs in the target vault:

- `_system/migration/reports/migration-summary.md`
- `_system/migration/reports/schema-exceptions.md`
- `_system/migration/reports/unresolved-aliases.md`
- `_system/migration/reports/task-review-queue.md`
- `_system/migration/reports/transcript-match-report.md`
- `_system/migration/manifests/file-map.csv`
- `_system/migration/manifests/exclusions.csv`
- `_system/migration/manifests/source-file-inventory.csv`
- `_system/migration/manifests/source-frontmatter-audit.csv`
- `_system/migration/manifests/source-task-extract.csv`
- `_system/migration/manifests/source-transcript-map.csv`
- `_system/migration/manifests/source-alias-map.csv`
- `DECISIONS.md`

## Execution Sequence

Follow this order:

1. Verify the source path is readable.
2. Create a full timestamped backup copy of the source instance.
3. Create the target v3 vault if it does not yet exist.
4. Scaffold the target vault per the V3 rebuild plan.
5. Add `/tasks/` and `_system/migration/` to the target vault.
6. Run v3 smoke checks on the empty/scaffolded target.
7. Generate source manifests before transforming content.
8. Write `DECISIONS.md` capturing migration-only implementation choices and any deviations.
9. Migrate legacy `reference/` state into `_system/` according to the migration plan.
10. Transform `reference/replacements.md` into `_system/alias-registry.md`.
11. Migrate memory entities.
12. Migrate journal notes.
13. Extract inline legacy tasks and create task notes in `/tasks/`.
14. Migrate transcripts from legacy `inbox/completed/` into `archive/transcripts/YYYY-MM/` and link them to journals.
15. Migrate context files and non-Markdown artifacts, creating companion notes where appropriate.
16. Migrate legacy archive content as preserved content.
17. Preserve hidden operational state for audit only.
18. Run full validation and reconciliation.
19. Generate reports and review queues.

## Important Content Handling Rules

### Transcripts

- Never delete or treat legacy `inbox/completed/*.txt` transcripts as disposable.
- Convert each one into a V3 transcript note.
- Ensure the transcript note body contains the raw transcript text.
- Ensure the transcript note links to a journal note via `tars-journal-entry`.
- If no clean journal match exists, create a minimal legacy-import journal stub and attach the transcript to it.

### Tasks

- Extract tasks from checkbox lists, action tables, and explicit action sections.
- Create deterministic import keys so re-runs do not duplicate tasks.
- Put migrated task notes in `/tasks/`.
- If owner, due date, or source is too ambiguous, create a review-queue entry instead of inventing facts.

### Contexts and artifacts

- Preserve structured `contexts/products/*.md` as product-context content.
- Preserve unstructured working docs as content even if they do not map cleanly to a TARS schema.
- Create companion notes for non-Markdown files like PDFs, PPTX files, CSVs, and similar artifacts.

### Legacy indexes

- Do not import `memory/_index.md`, `memory/*/_index.md`, or `journal/*/_index.md` as active content.
- Record them in the migration report and rely on v3 bases instead.

## Validation Requirements

At the end, verify:

1. All TARS-managed notes use v3 frontmatter and tags.
2. All critical links resolve.
3. Transcript backlinks resolve.
4. All migrated transcripts contain raw text in the body.
5. Count reconciliation is documented.
6. Exceptions are documented, not hidden.

## Failure Conditions

Stop and report instead of continuing if:

- a write would produce invalid v3 frontmatter
- a canonical entity collision cannot be resolved safely
- a transcript cannot be matched and you also cannot create a safe journal stub
- blocked secret patterns would be persisted into TARS-managed notes
- more than 5% of migrated TARS-managed notes fail schema validation

## Working Style

- Be proactive and execute the migration end-to-end.
- Do not stop at analysis.
- Only pause to ask the user if you hit a real blocker or a decision with meaningful destructive risk.
- If the V3 plan and the migration plan conflict, prefer:
  - `TARS_V3_INSTANCE_MIGRATION_PLAN.md` for migration mechanics
  - `TARS_V3_REBUILD_PLAN.md` for target-vault structure and workflow expectations
- If you deviate, document the reason in `DECISIONS.md`.

## Final Response Requirements

When done, report:

- whether the migration completed
- target vault path
- backup path
- counts migrated by content type
- transcripts preserved count
- task notes created count
- files preserved as legacy content count
- unresolved review items count
- validation status
- any remaining risks

## One-Line User Prompt

If invoked conversationally, the intended instruction is:

“Read [MIGRATION_HANDOFF.md](/Users/ajayjohn/Sync/Applications/Library/tars/MIGRATION_HANDOFF.md) and execute the migration exactly as specified.”
