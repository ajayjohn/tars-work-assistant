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
| Broken wikilinks | `mcp__tars_vault__search_by_tag` over all `[[…]]` patterns + `resolve_alias` | No | Propose: fix via alias registry / create stub / flag unverified |
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
scripts/validate-schema.py --vault <TARS_VAULT_PATH> --json
scripts/scan-secrets.py    --vault <TARS_VAULT_PATH> --json
scripts/health-check.py    --vault <TARS_VAULT_PATH> --json   (includes flagged_content sub-block — §7.4 merge)
scripts/fix-wikilinks.py   --vault <TARS_VAULT_PATH> --json   (detect only; applies with --apply)
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
