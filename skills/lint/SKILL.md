---
name: lint
description: Vault hygiene — broken links, orphans, schema violations, staleness, contradictions, sparse notes, framework state drift
user-invocable: true
triggers:
  - "lint"
  - "lint vault"
  - "check hygiene"
  - "check broken links"
  - "check orphans"
  - "check staleness"
  - "contradictions"
  - "schema violations"
help:
  purpose: |-
    The third operation in the ingest/query/lint trilogy. Scans the vault for structural
    and semantic hygiene issues, proposes fixes, and applies deterministic ones after
    user confirmation. Split out of /maintain in v3.1 to make Karpathy's "lint" verb
    explicit and first-class.
  use_cases:
    - "Lint the vault"
    - "Check for broken links"
    - "Find orphan notes"
    - "Surface stale memory"
    - "Show contradictions"
    - "Validate schemas"
  scope: hygiene,validation,wikilinks,orphans,schemas,staleness,framework-state
---

# Lint: vault hygiene and consistency

Lint is one of the three core TARS operations alongside **ingest** (/meeting, /learn, /maintain inbox) and **query** (/answer, /briefing, /think). Its purpose is narrow: surface consistency, hygiene, and health problems so the vault stays trustworthy as it scales.

Vault reads and writes use `mcp__tars_vault__*` tools. Deterministic checks call Python scripts under `scripts/` via Bash; their JSON output is consumed by this skill and applied through the MCP server. Never direct file I/O for content writes.

---

## Modes

| Trigger | Mode | Default on cron |
|---------|------|----------------|
| `lint`, `lint vault`, no argument | All checks | Yes (nightly, see §26.7) |
| `lint --focus links` / `check broken links` | Broken-link + wikilink-artifact subset | No |
| `lint --actions` | Run all checks in dry-run, then materialize each fixable finding as a numbered option in a single review queue. Same surface as `lint --actions wikilinks` but spans every check. Used directly by users and as a sub-step of `/maintain --weekly` | No |
| `lint --actions wikilinks` | Subset: only wikilink remediations (auto_safe / needs_review / unresolvable buckets from `scripts/fix-wikilinks.py --repair-broken --dry-run`) | No |
| `lint --actions patterns` | Subset: user-model + workflow proposals from `/learn --review-patterns` (Phase 6) | No |
| `lint --actions curator` | Subset: memory-staleness (90d) + workflow-staleness (60d) + persona-drift proposals. Respects `tars-pinned: true`. Phase 7 finishes the wiring | No |
| `lint --focus orphans` | Orphan + sparse subset | No |
| `lint --focus schema` | Schema validation subset | No |
| `lint --focus stale` | Staleness-tier subset | No |
| `lint --focus contradictions` | Contradiction detection subset | No |
| `lint --focus framework` | Framework self-state drift | No |
| `lint --focus organize` | Organization-engine proposals (§3.7) | No (v3.1 placeholder; full wiring Phase 7) |

---

## Check table

| Check | Source | Auto-fixable | Action on fail |
|-------|--------|-------------:|----------------|
| Broken wikilinks | `scripts/health-check.py` (exact match) + `scripts/heal-wikilinks.py` (fuzzy, v3.3) | Partial (distance≤1 auto-fix; distance=2 suggest; distance>2 none) | Auto-apply distance≤1 fixes with `--apply`; surface distance=2 suggestions as numbered options; unresolvable → propose create-stub or flag |
| Quadruple-bracket artifacts (`[[[[Name]]|Alias]]`, `[[[[Name]]]]`) | regex via `scripts/fix-wikilinks.py --json` | Yes | Auto-fix with confirmation |
| Orphan notes (0 backlinks, not referenced from a `.base` view) | link graph from `search_by_tag` | No | Propose archive or tag `tars/orphan` |
| Missing backlinks (A links B; B doesn't reflect A) | graph | Partial | Informational; offer to insert a reference when source is memory |
| Stale memory (`tars-modified` vs staleness tier) | `schemas.yaml` tiers + file mtimes | No | Propose review |
| Sparse articles (<150 words on memory note) | word count | No | Suggest consolidation, retirement, or `tars-archive-exempt` |
| Schema violations | `scripts/validate-schema.py --json` | Partial (defaults / missing-required with computable values) | Batch auto-fix; others need user |
| Sensitive content leaks | `mcp__tars_vault__scan_secrets` (wraps `scripts/scan-secrets.py`) | No | Block writes upstream; surface unresolved flags |
| Negative-sentiment review queue | `scripts/health-check.py --json` → `flagged_content` block | No | Present count; route to `/maintain inbox` flagged-review flow |
| Contradictions across related notes | LLM pass over entities co-linked in last 90d | No | Flag; do NOT auto-resolve |
| Unfiled journal entries (loose `journal/YYYY-MM-DD.md` at journal root) | path check | Yes | Propose `mcp__tars_vault__move_note` into `journal/YYYY-MM/` |
| Framework self-state drift (`_system/maturity.yaml` vs actual counts; `housekeeping-state.yaml` last_run vs telemetry) | vault scan + telemetry | Yes | Propose update via `update_frontmatter` |
| Install record health + version drift (`_system/install.yaml` missing, empty `vault_path`, `vault_path` ≠ current vault root, or `plugin_version` in either `_system/install.yaml` or `_system/housekeeping-state.yaml` older than `.claude-plugin/plugin.json`) | direct read of `_system/install.yaml`, `_system/housekeeping-state.yaml`, and `.claude-plugin/plugin.json` | Partial (refresh `last_session_at` and `plugin_version`; path mismatch + pending migrations need user) | Propose `/welcome --relocate` for path mismatch; offer `/maintain migrations` for version drift; auto-refresh trivial fields |
| Observed-vs-declared drift (`_system/user-model.md` differs from `_system/config.md`: e.g. observed `tars-bluf-tolerance: low` vs declared `tars-bluf-level: high`) | direct read of both notes | No | Surface; recommend `/learn --review-patterns` or a manual config edit |
| User-model staleness (`tars-last-pattern-scan` empty or older than 14d AND there is recent telemetry) | `_system/user-model.md` frontmatter + telemetry mtimes | No | Propose `/learn --review-patterns` |
| Workflows registry health (`_system/workflows.yaml` missing, schema-invalid, or contains entries whose `last_used` is null after 60d AND not pinned) | direct read of the registry | No | Surface for review; retirement proposals come from Phase 7 curator |
| Duplicate aliases (one alias → multiple canonical notes) | alias registry reverse-map | No | Surface for manual disambiguation |
| Task age + escalation (sets `tars-age-days`, `tars-escalation-level`) | file mtime + `tars-due` vs today | Yes | Auto-update frontmatter; surface level-2 + level-3 for user review |
| Telemetry lint — memories saved 90d ago never re-read (durability miss) | `_system/telemetry/*.jsonl` → `memory_persisted` vs subsequent `vault_write`/`answer_delivered` hits | No | Surface for user review |
| Telemetry lint — tasks created >60d ago still `open` (accountability miss) | `_system/telemetry/*.jsonl` + `memory/tasks/` frontmatter | No | Surface candidates (§5.4); route to `/tasks` |
| Decision / initiative / people count drift vs `_system/maturity.yaml` hydration block | `scripts/sync.py --hydration` | Yes | Auto-update yaml via `update_frontmatter` equivalent |

---

## Pipeline

### Step 1: Enumerate checks

Determine which checks to run based on the mode trigger. For the default "all" mode, run the full table top-down, short-circuiting any check that depends on a script that fails to import (graceful degrade per §26.2).

### Step 2: Run deterministic scanners

Call Python scripts in parallel where independent, collect JSON results:

```
scripts/validate-schema.py  --vault <TARS_VAULT_PATH> --json
scripts/scan-secrets.py     --vault <TARS_VAULT_PATH> --json
scripts/health-check.py     --vault <TARS_VAULT_PATH> --json   (includes flagged_content sub-block — §7.4 merge)
scripts/fix-wikilinks.py    --vault <TARS_VAULT_PATH> --json   (detect only; applies with --apply)
scripts/fix-wikilinks.py    --vault <TARS_VAULT_PATH> --json --repair-broken
                                   # broken-link scan; classifies into
                                   # auto_safe / needs_review / unresolvable.
                                   # --apply only acts on auto_safe; the
                                   # other buckets surface as /lint actions.
scripts/heal-wikilinks.py   --vault <TARS_VAULT_PATH> --json --dry-run
                                   # fuzzy broken-link healer (v3.3).
                                   # Three-stage pipeline: slug-normalization →
                                   # alias-registry → Levenshtein ≤2.
                                   # distance ≤ 1 → auto_fix bucket (safe to apply).
                                   # distance = 2 → suggest bucket (surface to user).
                                   # distance > 2 → unresolvable.
                                   # Run AFTER fix-wikilinks.py so artifact-bracket
                                   # repairs are already applied.
```

### Step 3: Run MCP-backed checks

```
mcp__tars_vault__search_by_tag(...)            # for tag-scoped link + orphan scans
mcp__tars_vault__read_note(...)                # for targeted body inspection
mcp__tars_vault__resolve_alias(...)            # for canonical-name resolution
```

### Step 4: Classify results

Bucket every finding into one of:

| Bucket | Meaning |
|--------|---------|
| **Critical** | Blocks vault integrity: secret leaks, schema violations on required fields |
| **Warning** | Impairs trust: broken wikilinks, duplicate aliases, contradictions, stale memory |
| **Auto-fixable** | Deterministic fix available: wikilink artifacts, alias-registry sync, unfiled journal entries, framework state drift |
| **Informational** | Signal-only: missing backlinks, sparse articles, telemetry-lint surfaces |

### Step 5: Present consolidated report (BLUF)

```markdown
## Lint report — YYYY-MM-DD

### Critical (N)
| # | Category | File | Issue | Fix |
|---|----------|------|-------|-----|
| 1 | secret   | memory/people/john.md | SSN on line 42 | Redact immediately |

### Warnings (N)
| # | Category | File | Issue | Suggested fix |

### Auto-fixable (N)
| # | Category | File | Issue | Proposed fix |

### Informational (N)
| # | Category | File | Notes |

Actions:
  - "auto-fix all"  — apply every auto-fixable
  - "auto-fix 1,3"  — apply specific ones
  - "fix critical"  — apply fixes for criticals only (if any are auto)
  - "review each"   — confirm each individually
  - "skip"          — defer until next lint run
```

### Step 6: Apply fixes

For each approved auto-fix:

```
# Wikilink artifacts
mcp__tars_vault__append_note(file=…, content=…)   # only when needed; mostly edits via dedicated tool

# Framework state — hydration counters (§5.2). Source of truth is
# `scripts/sync.py --hydration`, then update the yaml block.
mcp__tars_vault__update_frontmatter(file="maturity", property="decision_count", value="<actual>")

# Task age / escalation (§5.3). Per open task: compute age, classify level,
# write both. No user prompt needed — pure derivation.
#   tars-age-days        = (today - tars-created).days
#   tars-escalation-level:
#     tars-due < today - 90d  → 3
#     tars-due < today - 60d  → 2
#     tars-due < today - 30d  → 1
#     else                    → 0
mcp__tars_vault__update_frontmatter(file=<task>, property="tars-age-days", value=<n>)
mcp__tars_vault__update_frontmatter(file=<task>, property="tars-escalation-level", value=<0-3>)

# Unfiled journal entry
mcp__tars_vault__move_note(src="journal/YYYY-MM-DD.md", dst="journal/YYYY-MM/YYYY-MM-DD.md")
```

All writes flow through the `tars-vault` MCP server, which logs to `_system/changelog/YYYY-MM-DD.md` via the PostToolUse hook.

### Step 6.5: --actions mode (queued review)

When invoked as `lint --actions` (or `lint --actions <subset>`), do not present the report inline. Instead, materialize every fixable finding as a numbered option in a single review queue and write the queue to disk for asynchronous review:

1. Run Steps 1–4 as usual; collect all findings with their classification.
2. Filter to actionable buckets: `Critical` + `Warnings` + `Auto-fixable`. Drop `Informational`.
3. Render a numbered queue with one line per item:

   ```
   N. [bucket] [check] file: short description → proposed fix
   ```

4. Caller is one of:
   - **Interactive user** — render the queue inline; accept the same selection syntax as Step 5 (`auto-fix all`, `auto-fix 1,3`, `review each`, `skip`).
   - **/maintain --weekly** — render the queue as a markdown section and append to `inbox/pending/weekly-review-YYYY-MM-DD.md`. Do not auto-apply anything. The user reviews on next session.

5. Subset selectors filter to a single check class:
   - `lint --actions wikilinks` → broken-link / artifact rows only. Sources:
     (a) `scripts/fix-wikilinks.py --repair-broken --json` — bracket-artifact repairs (auto_safe auto-applied; needs_review surfaced).
     (b) `scripts/heal-wikilinks.py --json --dry-run` — fuzzy broken-link repairs. distance≤1 rows become auto-fixable entries; distance=2 rows become suggestion entries. Apply auto-fix bucket by running `scripts/heal-wikilinks.py --apply`; apply is logged to `_system/changelog/`. Never auto-apply suggestion bucket — present to user with the ranked candidates.
   - `lint --actions patterns` → user-model + workflow proposals only. Sources its candidate list from `/learn --review-patterns` (Phase 6); no telemetry re-aggregation here. Each proposal renders as `kind=user-model field=<f> before=<v> after=<v> evidence=<count>×<window>` or `kind=workflow id=<id> trigger="…" steps=[…]`. Selection: `accept all`, `accept N`, `review each`, `skip`. (Phase 6)
   - `lint --actions curator` → memory-staleness / workflow-staleness / persona-drift rows only. Source: `scripts/archive.py --vault $TARS_VAULT_PATH --json --check all` plus the persona-drift check described in `skills/maintain/SKILL.md` weekly mode step 5. Each row labels its kind (`memory:<file>`, `workflow:<id>`, `persona:<from>→<to>`) plus age and the protection set for memory items. Selection: `archive all`, `archive N,M`, `review each`, `skip`. On "archive", call `mcp__tars_vault__archive_note(file=…)`. Workflow items become `workflows.yaml` edits via `mcp__tars_vault__write_note_from_content`. Persona-switch acceptance updates `_system/install.yaml` `persona:` field via `mcp__tars_vault__update_frontmatter`. Every action logs to `_system/changelog/YYYY-MM-DD.md` with `{action: archive|workflow-retire|persona-switch, target, reversibility: <how to undo>, batch_id}`. (Phase 7)
   - `lint --actions` (no subset) → all of the above plus schema, framework, dedupe, sparse, telemetry-lint surfaces.

6. Emit a `lint_actions_queued` telemetry event with `{count, subset, surface: "inline"|"weekly-review"}`.

### Step 7: Log and emit telemetry

Emit one `lint_run` telemetry event per invocation:

```json
{
  "event": "lint_run",
  "skill": "lint",
  "critical": <int>,
  "warnings": <int>,
  "auto_fixable": <int>,
  "informational": <int>,
  "fixes_applied": <int>,
  "fixes_deferred": <int>
}
```

The PostToolUse hook appends a lint-summary line to the daily note. No explicit daily-note append is required.

---

## Scheduled operation

`/lint` runs nightly at 02:00 local time via CronCreate (see §26.7). The scheduled run:

- Surfaces proposals only — never applies auto-fixes without user review.
- Writes its report to `journal/YYYY-MM/YYYY-MM-DD-lint.md`.
- Emits telemetry.
- Skips if `_system/housekeeping-state.yaml` shows a manual lint already ran in the last 12h.

---

## Constraints

1. Never auto-resolve contradictions — humans decide which version is current.
2. Never delete files; propose archive via `mcp__tars_vault__archive_note` (which enforces the 90-day backlink + active-task guardrails).
3. Never write to the vault without the PostToolUse hook path; bypass would skip the changelog entry.
4. Never run on stale `housekeeping-state.yaml` without refreshing it afterwards — the nightly cadence depends on that marker.
5. Auto-fix scope is narrow: wikilink artifacts, missing required schema fields with computable defaults, alias-registry sync, framework self-state drift, unfiled journal entries. Anything touching body content needs explicit review.
6. Never surface more than 50 findings in a single report — paginate or narrow with `--focus` if over-large.
7. Circuit breaker: if >3 MCP errors in a single run, stop and report status rather than push through.
