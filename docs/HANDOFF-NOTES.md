# TARS v3.1 — Handoff Notes

Running log of executing-agent sessions on branch `tars-3.1.0-dev`. Each session
appends to the end. Source of truth for "what the prior session did / deferred /
needs you to decide." Ordered newest-first within each session entry, oldest-first
across sessions.

---

## 2026-04-17 — Session 1 — Phase 1a + Phase 1b skeletons

### What was done

**Branch**: created `tars-3.1.0-dev` off `main` (at commit `aa6f63d`). No push, no merge.

**Git hooks installed** (PRD §24.1 authorship enforcement):
- `scripts/githooks/prepare-commit-msg` — rejects Claude attribution patterns.
- `scripts/githooks/pre-push` — belt-and-braces check on push.
- `scripts/githooks/install-githooks.sh` — idempotent installer.
- Installed into `.git/hooks/` so this session's commit is enforced.

**`mcp/tars-vault/` skeleton** (PRD §26.3):
- `pyproject.toml` (pins: `mcp>=1.0,<2.0`, `fastembed>=0.4,<1.0`, `sqlite-vec>=0.1.6,<0.2`).
- `src/tars_vault/` package with `__main__.py`, `server.py`, `validators.py`,
  `obsidian_cli.py`, `search_index.py`, `alias_registry.py`, `wikilink_pass.py`,
  `organize.py`, `telemetry.py`.
- 16 tool skeletons under `src/tars_vault/tools/`: `create_note`, `append_note`,
  `write_note_from_content`, `update_frontmatter`, `search_by_tag`, `read_note`,
  `archive_note`, `move_note`, `classify_file`, `detect_near_duplicates`,
  `resolve_capability`, `refresh_integrations`, `scan_secrets`, `fts_search`,
  `semantic_search`, `rerank`. Each raises `NotImplementedError` with a phase pointer.
- `tests/test_skeleton.py` + fixture-vault stub.

**`hooks/` scripts** (PRD §3.2, §26.5):
- `session-start.py`, `pre-tool-use.py`, `post-tool-use.py`, `pre-compact.py`,
  `session-end.py`, `instructions-loaded.py`. All fire-and-forget in Phase 1a;
  `SessionStart`/`InstructionsLoaded` never exit non-zero.
- `_common.py` helpers: `read_event`, `write_output`, `vault_path`, `in_recursion`,
  `log_stderr`.
- `hooks/hooks.json` — plugin-level Claude Code hook manifest with narrow matchers
  (`mcp__tars_vault__.*|Bash`).

**`scripts/` Phase 1a skeletons** (PRD §3.4, §3.5, §6.4):
- `discover-mcp-tools.py` — stubbed registry discovery.
- `capability-classifier.py` — working classifier keyed off
  `scripts/capability-classifier.yaml` (PRD §26.9 starter map shipped verbatim).
- `build-search-index.py` — initializes empty FTS5 schema; vec layer lands Phase 4.
- `fix-wikilinks.py` — detection-only pass (finds `[[[[Name]]|Alias]]`-style artifacts).

**Phase 1b scaffolding** (PRD §3.5):
- `scripts/migrate-integrations-v2.py` — idempotent v3.0→v3.1 migration of
  `_system/integrations.md`; backs up `.pre-v3.1-backup`; uses the template below.
- `templates/integrations-v2.md` — v3.1 capability-preference map with
  `tars-config-version: "2.0"` marker.
- `resolve_capability` / `refresh_integrations` tool skeletons landed in
  `mcp/tars-vault/` Phase 1a as planned.

**Plugin wiring**:
- `.claude-plugin/mcp-servers.json` registers `tars-vault` only (stdio, module form).
- `hooks/hooks.json` wires all six lifecycle events.

**Test surface**:
- `tests/validate-phase1-skeleton.py` — structural validator for the new surface.
- `tests/validate-scripts.py` patched to skip non-script files (e.g., sibling
  YAML data files under `scripts/`). Pre-existing non-stdlib-import errors on
  `archive.py`, `health-check.py`, `scan-flagged.py`, `scan-secrets.py`, `sync.py`,
  `validate-schema.py` are **unchanged from baseline** — not introduced by this
  phase.
- `ARCHITECTURE.md` script count updated from 8 → 13 (minimal doc edit required for
  `validate-docs.py` to pass; full docs refresh is Phase 8).

### Tests passing (exit 0)

- `tests/validate-structure.py` — PASS
- `tests/validate-routing.py` — PASS
- `tests/validate-references.py` — PASS
- `tests/validate-docs.py` — PASS
- `tests/validate-phase1-skeleton.py` — PASS (new)
- `tests/smoke-tests.py` — exits 0 (no regressions vs. baseline)

### Tests still failing (all pre-existing, not introduced this phase)

- `tests/validate-scripts.py` — 6 errors, all pre-existing yaml-import violations
  in scripts that predate v3.1 (`archive.py`, `health-check.py`, `scan-flagged.py`,
  `scan-secrets.py`, `sync.py`, `validate-schema.py`). Phase 7 consolidation merges
  `scan-flagged.py` into `health-check.py`; the others need stdlib-only rewrites
  in later phases.
- `tests/validate-frontmatter.py` — 2 errors + 33 warnings. Exit 0. Pre-existing.
- `tests/validate-templates.py` — 1 error + 6 warnings. Exit 0. Pre-existing.

### Mid-session PRD update (2026-04-18) — tars-office removed

PRD was updated 2026-04-18 to delegate office rendering (`.pptx`, `.docx`, `.xlsx`,
`.pdf`, HTML) to Anthropic's first-party `pptx`/`docx`/`xlsx`/`pdf` skills from
[anthropics/skills](https://github.com/anthropics/skills). TARS no longer ships a
custom office MCP server (see §3.1b, §8.10, §26.4).

Corrective actions taken this session (working-tree-only, no commit had landed):
- Deleted `mcp/tars-office/` in its entirety.
- Trimmed `requirements.txt` to `mcp`, `fastembed`, `sqlite-vec` only (removed
  `python-pptx`, `openpyxl`, `python-docx`, `weasyprint`, `markdown-it-py`,
  optional `matplotlib`).
- Removed `tars-office` from `.claude-plugin/mcp-servers.json`.
- Removed `tars-office` from `hooks/hooks.json` matcher.
- Removed `tars-office` from `templates/integrations-v2.md` `office-docs` entry.
- Updated `tests/validate-phase1-skeleton.py` to assert `mcp/tars-office/` does
  NOT exist and `mcp-servers.json` does NOT declare `tars-office`.

Phase 1a scope now: `tars-vault` + `hooks/` + `scripts/` + `scripts/githooks/`.
Phase 6 (`/create` upgrade) implements the delegation pattern per §8.10.

### Design choices made (narrow defaults per §26.18)

1. **`.claude/settings.json` is user-local**; I did not overwrite the existing
   `enabledPlugins` entry. Instead, the plugin-level hook wiring went to
   `hooks/hooks.json` — the Claude Code plugin convention. If the correct location
   is actually `.claude-plugin/settings.json` or a `hooks` entry inside
   `plugin.json`, a later phase can move it; the skeleton's scripts themselves
   need no change.
2. **MCP server registration** lives at `.claude-plugin/mcp-servers.json` (stdio,
   `python -m tars_vault`). If Claude Code expects these inside `plugin.json`
   under an `mcpServers` key, Phase 2 can inline them.
3. **Skeletons raise `NotImplementedError`** rather than returning silent no-ops.
   Makes phase-2 rewiring loud rather than silent.
4. **FTS5 schema init** in `build-search-index.py` creates `fts_notes(path, title,
   tags, body)` with porter+unicode61 tokenizer. Phase 4 will add vec table + meta
   bookkeeping. No rows inserted in the skeleton — only schema DDL.
5. **Classifier YAML shipped at `scripts/capability-classifier.yaml`** verbatim
   from §26.9. User-override path (`_system/capability-overrides.yaml`) is not
   read by the skeleton; Phase 1b runtime discovery will.

### Open ambiguities / needs user input

1. **Plugin hook/MCP wiring location** — see design choice 1 & 2 above. If the
   plugin format has a canonical single location, tell the next session and it's
   a file-move only.
2. **Anthropic skills availability check mechanism** — §3.1b says session-start
   verifies `skills/pptx`, `skills/docx`, `skills/xlsx`, `skills/pdf` availability.
   How the session-start hook detects these (via MCP introspection? filesystem
   probe under `~/.claude/skills/` or a bundled path?) is not specified. Phase 1a
   skeleton deliberately does not probe — Phase 1b / Phase 6 will.
3. **`_system/` directory in repo** — contains v3.0 defaults (`integrations.md`,
   etc.). Phase 1b's migration script points at the vault's `_system/` not the
   repo's. The repo-side `_system/integrations.md` still reflects v3.0; Phase 2
   or 7 should decide whether to overwrite with the v3.1 template.
4. **Tag `tars-archive-exempt` schema extension** from §9 is a Phase 5 concern;
   skeleton schema validators do not yet reference it.

### What the next session should pick up

**Phase 2 — Skill rewiring** per PRD §10 item 3:
- Update all 12 skills (+ new `/lint` added in Phase 3) to call `mcp__tars_vault__*`
  instead of raw `obsidian-cli`.
- Replace hardcoded MCP server names with `resolve_capability(capability=…)`.
- Remove now-redundant prompt-level enforcement lines (hooks enforce them).
- Keep every review gate intact (§1, §26.16 rules 10–11).

Before starting Phase 2, the next session should:
1. Read the original PRD's §3.1, §3.5, §8 per-skill changes (not re-summarized here).
2. Run `python3 tests/validate-phase1-skeleton.py` and `python3
   tests/validate-docs.py` to confirm the skeleton hasn't drifted.
3. Re-install git hooks via `scripts/githooks/install-githooks.sh` (idempotent).

### Files touched this session

Tracked (added):
- `mcp/tars-vault/**` (25 files)
- `hooks/**` (8 files: 6 scripts + `_common.py` + `hooks.json` + `README.md`)
- `scripts/discover-mcp-tools.py`
- `scripts/capability-classifier.py`
- `scripts/capability-classifier.yaml`
- `scripts/build-search-index.py`
- `scripts/fix-wikilinks.py`
- `scripts/migrate-integrations-v2.py`
- `scripts/githooks/{prepare-commit-msg,pre-push,install-githooks.sh}`
- `templates/integrations-v2.md`
- `.claude-plugin/mcp-servers.json`
- `requirements.txt`
- `tests/validate-phase1-skeleton.py`
- `docs/HANDOFF-NOTES.md` (this file)

Tracked (modified):
- `.gitignore` — added `_system/embedding-cache/` (FastEmbed cache).
- `ARCHITECTURE.md` — script count 8 → 13.
- `tests/validate-scripts.py` — skip non-script sibling data files.

Deleted pre-commit (never committed): `mcp/tars-office/**`.

---

## 2026-04-17 — Session 2 — Phase 2 + Phase 3

### What was done

**Phase 2 — skill rewiring (all 12 pre-existing skills)**. Every skill's prompt body
has been rewired to reference `mcp__tars_vault__*` tools as the vault write interface
and `mcp__tars_vault__resolve_capability(capability=…)` as the integration resolver.
No skill hard-codes `mcp__apple_*`, `mcp__microsoft_365_*`, or any provider-specific
MCP server name. Raw `obsidian-cli` examples were replaced with the equivalent MCP
tool call where the pattern appeared inline.

Per PRD §8:

- **`core/SKILL.md`**: added the "Three operations" framing (ingest / query / lint),
  the full `mcp__tars_vault__*` write-interface table, the capability-resolver
  contract, and the "hooks enforce — don't re-assert" directive. `/lint` added
  to both the signal table and help routing table. Universal-constraint #1 now
  reads "`mcp__tars_vault__*` tools for all vault mutations."
- **`meeting/SKILL.md`**: Step 1 (alias registry) now relies on
  `resolve_alias` (server-cached). Step 3 calendar check routed through
  `resolve_capability(capability="calendar")`. New Step 3b placeholder for
  `resolve_capability(capability="meeting-recording")` import prompt. Steps 8–11
  use `mcp__tars_vault__create_note / append_note / update_frontmatter`. Step 13
  daily-note + changelog delegated to PostToolUse hook per PRD §8.2. Nuance
  capture pass (§6.8 / Phase 4) is NOT added this session — Phase 4 scope.
- **`briefing/SKILL.md`**: both daily and weekly calendar + task sub-agents
  resolve via `resolve_capability`. Journal/memory searches and saves routed
  through `search_by_tag` + `create_note`. Daily-note appends delegated to hook.
- **`tasks/SKILL.md`**: duplicate checks, creation, reprioritization, and archival
  all through MCP tools. Archive route uses `archive_note` (server enforces the
  90d-backlink + active-task guardrails). Phase 5 schema additions
  (`tars-blocked-by`, `tars-age-days`, `tars-escalation-level`) referenced as
  backward-compatible; server validator accepts notes without them.
- **`learn/SKILL.md`**: name resolution via `resolve_alias`; knowledge check via
  `search_by_tag` + Phase-4 `fts_search` pointer. Entity create/update path fully
  migrated. Alias-registry auto-update noted as server-side. Wisdom journal and
  daily-note writes moved to MCP calls; hook handles changelog.
- **`answer/SKILL.md`**: source-priority table rewritten for v3.1 hybrid retrieval
  (memory → Tier-A FTS → tasks → journal → Tier-B semantic → transcripts →
  integrations → web). All obsidian-cli examples replaced. Index-first pattern
  now reads "use `mcp__tars_vault__search_by_tag` (or Phase-4 fts/semantic)".
  Integration lookups use `resolve_capability`.
- **`think/SKILL.md`**: preamble added (vault via MCP, integrations via
  resolve_capability, Mode-D sub-agents use native `subagent_type`).
- **`communicate/SKILL.md`**: preamble added; brand-guidelines auto-load
  referenced as Phase 5 (until then the skill prompts for the active brand file).
- **`initiative/SKILL.md`**: preamble; project-tracker / data-warehouse /
  analytics resolved via `resolve_capability`.
- **`create/SKILL.md`**: reframed as **orchestrator-only**. Context gathering
  switched from `_index.md` files to `search_by_tag` (bases replace indexes per
  v3). Office rendering path explicitly delegates to Anthropic's first-party
  `pptx` / `docx` / `xlsx` / `pdf` / `web-artifacts-builder` skills — full
  delegation lands in Phase 6. Phase 2 produces markdown-only if user requests
  non-markdown. Companion-note contract (§26.13) referenced.
- **`maintain/SKILL.md`**: rewired in-place as part of the Phase 3 slim (see
  below).
- **`welcome/SKILL.md`**: pre-flight additions for tars-vault reachability,
  hook installation, git-hooks installer, Anthropic-skills detection, and
  integration auto-discovery. Person/initiative creation calls migrated to
  `mcp__tars_vault__create_note`.

**Phase 3 — `/lint` as first-class skill**:

- **`skills/lint/SKILL.md`** (193 lines, ≤300 target). Implements PRD §4.1
  check-table: broken wikilinks, quadruple-bracket artifacts, orphans, missing
  backlinks, stale memory, sparse articles, schema violations, sensitive content,
  negative-sentiment queue, contradictions, unfiled journal entries, framework
  self-state drift, duplicate aliases, telemetry-lint. Pipeline: enumerate →
  deterministic scanners (via `scripts/*.py --json`) → MCP-backed checks →
  classify (critical / warning / auto-fixable / informational) → present →
  apply → emit `lint_run` telemetry. Scheduled nightly at 02:00 per §26.7.
- **`commands/lint.md`** — thin wrapper pointing at `skills/lint/`.
- **`skills/maintain/SKILL.md`** slimmed from 754 → 245 lines (≤250 target).
  Retained modes: inbox, sync, archive, combined-maintenance. Retired modes:
  health check (now `/lint`), reference update (v2.1 artifact). Inbox routes
  items to owning skills; sync surfaces drift without auto-resolving; archive
  enforces guardrails via `archive_note`; combined flow runs archive + sync
  and prompts before inbox.
- **`commands/maintain.md`** updated to reflect the new argument hint and
  cross-reference `/lint` for hygiene.

**Doc count updates** (required for validate-docs.py to pass):

- `README.md`: "12 skills, 11 commands, 8 scripts" → "13 skills, 12 commands,
  13 scripts".
- `ARCHITECTURE.md`: skill count 12 → 13, commands 11 → 12, baseline tokens
  48 → 52.

### Tests passing (exit 0)

- `tests/validate-structure.py` — PASS
- `tests/validate-routing.py` — PASS (new `/lint` signal routes to the
  new `skills/lint/` directory; every user-invocable skill has at least one
  signal)
- `tests/validate-references.py` — PASS
- `tests/validate-docs.py` — PASS (after skill/command count updates)
- `tests/validate-phase1-skeleton.py` — PASS (unchanged)
- `tests/smoke-tests.py` — exits 0 (same 3 obsidian-cli-related pre-existing
  failures as Phase 1; unrelated to this phase)

### Tests still failing (all pre-existing, unchanged)

- `tests/validate-scripts.py` — 5 yaml-import violations in pre-v3.1
  scripts. Phase 7 consolidation will clean up.
- `tests/validate-frontmatter.py` — 2 errors + 36 warnings (baseline). Exit 0.
- `tests/validate-templates.py` — 1 error + 6 warnings (baseline). Exit 0.

### Design choices made (narrow defaults per §26.18)

1. **Skill rewrites are prompt-level, not behavioral.** The MCP tool skeletons
   from Phase 1a still raise `NotImplementedError`. Phase 2 updates the skill
   prompts so that when the MCP tools become real (later phases), every skill
   calls the right tools. If a user invokes any skill before the MCP server
   is implemented further, the MCP calls will surface `NotImplementedError`
   rather than silently falling back to raw obsidian-cli — deliberate.
2. **Integration calls converted to `resolve_capability` across the board**,
   including in sub-agent prompts inside `briefing/`. When
   `resolve_capability` is called against a still-stub server, it returns a
   clear `status: "unavailable"` and the skill degrades per
   `unavailable_behavior` in `_system/integrations.md`.
3. **Legacy obsidian-cli examples kept where they appear in instructional
   prose but pattern-call sites were migrated.** Full bash-example purge is
   Phase 7 scope (skill-body trimming); Phase 2's objective was tool-call
   rewiring, not prose scrubbing.
4. **`/create` office delegation is scaffolded, not implemented.** Skill body
   says explicitly that Phase 6 wires the Anthropic-skill invocation pattern;
   Phase 2 only updates the vault-grounding plumbing so Phase 6 can plug in
   the delegation cleanly.
5. **`/lint` scheduled cadence set to 02:00 nightly** per §26.7; this session
   did not register the cron (user runs that during Phase 9 migration via
   `/maintain register-crons`).
6. **Auto-wikilink pass** is referenced in multiple skills as server-side
   (§3.3), but the actual implementation in `mcp/tars-vault/src/tars_vault/
   wikilink_pass.py` is still the Phase 1a skeleton. No behavioral change
   this session; Phase 1b-continuation or Phase 4 will wire it.
7. **Telemetry event names** used in skill bodies match §26.11 verbatim
   (`skill_invoked`, `memory_proposed`, `task_persisted`, `answer_delivered`,
   `meeting_nuance_captured`, `lint_run`, `briefing_generated`,
   `sync_completed`, `archive_swept`, `maintenance_run`, `artifact_generated`,
   `integration_resolved`).

### Open ambiguities / needs user input

1. **Brand auto-load UX (Phase 5)** — `/communicate` and `/create` currently
   prompt when multiple `tars-brand: true` notes exist. Phase 5 caches the
   selection in `_system/config.md` as `tars-active-brand`. No user input
   needed here; flagging for continuity.
2. **Nuance capture pass (§6.8)** — noted in meeting skill prose as "Phase 4"
   but the actual Step 7b is NOT inserted this session. Phase 5 session
   will add it.
3. **`scripts/capability-classifier.yaml` heuristics** — shipped verbatim
   from §26.9 in Phase 1a. If the user's actual MCP ecosystem has tools that
   don't match any pattern, they'll fall into `uncategorized`. Phase 1b
   added `_system/capability-overrides.yaml` as the user-escape hatch.

### What the next session should pick up

**Phase 4 — Hybrid retrieval + meeting nuance pass (§6)**:
- Implement `mcp__tars_vault__fts_search` and `semantic_search` tool bodies.
- Add `scripts/build-search-index.py` FastEmbed + sqlite-vec wiring.
- Insert Step 7b (nuance capture pass) into `skills/meeting/SKILL.md` with the
  verbatim prompt from PRD §26.8.
- Add the `mcp__tars_vault__rerank` tool stub promotion to a real call.

Before starting, the next session should:
1. Read PRD §6 (and §26.8, §26.12) in full.
2. Re-install git hooks via `scripts/githooks/install-githooks.sh`.
3. Run `tests/validate-*.py` to confirm the skeleton hasn't drifted.

### Files touched this session

Tracked (added):
- `skills/lint/SKILL.md` (193 lines)
- `commands/lint.md`

Tracked (modified):
- `skills/core/SKILL.md` — write-interface table, Three-operations framing,
  `/lint` in signal & help-routing tables, integration-resolver section,
  universal-constraint #1 update.
- `skills/meeting/SKILL.md` — MCP tool migration, calendar via
  `resolve_capability`, Step 13 delegated to hook.
- `skills/briefing/SKILL.md` — calendar/tasks via `resolve_capability`,
  MCP tool migration for reads/writes, daily-note step delegated to hook.
- `skills/tasks/SKILL.md` — MCP tool migration; archive via `archive_note`.
- `skills/learn/SKILL.md` — MCP tool migration; alias + knowledge check paths
  updated.
- `skills/answer/SKILL.md` — source priority table rewritten for v3.1 hybrid
  retrieval; all obsidian-cli examples converted.
- `skills/think/SKILL.md` — v3.1 preamble.
- `skills/communicate/SKILL.md` — v3.1 preamble with brand auto-load pointer.
- `skills/initiative/SKILL.md` — v3.1 preamble with integration capabilities.
- `skills/create/SKILL.md` — orchestrator framing, Anthropic-skill delegation
  pointer, `_index.md` → `search_by_tag`.
- `skills/welcome/SKILL.md` — v3.1 pre-flight, MCP tool calls in onboarding
  person/initiative creation.
- `skills/maintain/SKILL.md` — slimmed 754 → 245 lines; hygiene retired to
  `/lint`; reference-update mode retired entirely.
- `commands/maintain.md` — argument hint + cross-reference.
- `README.md` — skill/command/script counts bumped.
- `ARCHITECTURE.md` — skill/command counts bumped; baseline tokens adjusted.
- `docs/HANDOFF-NOTES.md` (this entry).

---

## 2026-04-17 — Session 3 — Phase 4 — Hybrid retrieval + meeting nuance pass

### What was done

**Search index library** (`mcp/tars-vault/src/tars_vault/search_index.py`) —
replaced the Phase 1a stub with the real access layer:
- Tier classification (A = `memory/**`; B = `journal/**`,
  `archive/transcripts/**`, `contexts/**`; everything else is skipped).
- FTS5 virtual table `fts_notes(path, title, tags, body, tier UNINDEXED,
  source_type UNINDEXED, date UNINDEXED)` with porter+unicode61 tokenizer.
- `chunks` table (id, path, chunk_index, text, source_type, date) plus a
  sqlite-vec `vec_chunks(embedding float[384])` virtual table whose rowid
  matches `chunks.id` one-to-one.
- Pure helpers for frontmatter split, title extraction, tag parsing (YAML
  block + inline form), chunk-body (~300 words w/ 60-word overlap ≈ 400/80
  token budget from §6.2), SHA-256 file hashing, and search-index state
  persistence (`_system/search-index-state.json`).
- FTS query (bm25 + snippet) and vector KNN (sqlite-vec `embedding MATCH ?
  ORDER BY distance LIMIT k`, with post-filter by source_type since vec0
  doesn't allow mixed WHERE clauses on non-indexed columns).
- Graceful degradation: `load_sqlite_vec` returns False on missing extension;
  callers treat False as "FTS-only".

**`scripts/build-search-index.py`** — promoted from stub to full incremental
builder:
- Walks the vault, SHA-256 per file gates re-chunking + re-embedding.
- Loads FastEmbed (`BAAI/bge-small-en-v1.5`, fallback
  `sentence-transformers/all-MiniLM-L6-v2`) with cache at
  `<vault>/_system/embedding-cache/`.
- Graceful fallback: if fastembed or sqlite-vec unavailable, builds FTS-only.
- 10-minute budget per run (resumable via state file).
- Honors §26.15 migration-script contract: `--vault`, `--dry-run`, `--apply`,
  `--json`; exits 3 on dirty git worktree; 1 on SIGINT; 2 on embed error.

**Three MCP tool bodies** (promoted from NotImplementedError stubs):
- `fts_search` — BM25 keyword over the built index. Supports `tier`, explicit
  `source_types`, and a `scope` convenience alias (`memory` | `journal` |
  `transcripts` | `contexts` | `all`) that expands to tier + source_types.
  Returns `{status: ok | no_index | error, results, count, reason?}`.
- `semantic_search` — hybrid Tier-B search. Lazy-loads FastEmbed, runs vector
  KNN via `search_index.semantic_query`, merges with FTS5 results using
  `0.7 × semantic + 0.3 × FTS` (min-max normalized), applies optional
  `date_range` post-filter. Returns `{status: ok | no_index | fts_only |
  error, results, fallback, count, reason?}`. `fts_only` signals the caller
  (answer skill, nuance pass) to flag the gap to the user.
- `rerank` — deterministic score-based rerank with recency boosts (same-day
  1.15×, ≤7d 1.10×, ≤30d 1.05×) and source-type boost (transcript/journal
  1.10×). Returns `{status: ok, results, count, mode: "deterministic"}`.
  LLM-backed rerank explicitly deferred (see Deferred decisions below).

**Meeting nuance pass (Step 7b)** inserted into `skills/meeting/SKILL.md`
between Step 7 (LLM summary) and Step 8 (persist journal). Contract:
- Spawn a sub-agent with Haiku, `max_turns=1`, temperature 0.2.
- Feed the verbatim prompt from `skills/meeting/reference/nuance-pass-prompt.md`
  (new file; §26.8 verbatim).
- Parse six-key JSON response (notable_phrases, contrarian_views,
  specific_quotes, unusual_technical_terms, emotional_strong_statements,
  numbers_and_dates_missed); render under `## Notable phrases & perspectives`
  in the journal entry. Empty JSON still emits the heading with "No nuance
  flagged." Failures emit `meeting_nuance_failed` telemetry and **never**
  block the pipeline.
- Skill body also updated: preamble ("14-step pipeline (plus a 7b nuance-
  capture sub-step)"), pipeline overview adds Step 7b, Step 8 frontmatter
  body adds `## Notable phrases & perspectives` placeholder, new absolute
  constraint #15 says 7b failure never blocks.

**Unit tests** — `mcp/tars-vault/tests/test_search_index.py` (19 tests,
stdlib-only):
- Tier classification, source-type mapping, frontmatter/title/tag/date
  extraction, short + long + empty chunking with overlap invariant.
- FTS round-trip + delete + re-query on an in-memory-ish tmp vault.
- Tool contracts: no_index, missing args, invalid scope, fts_only fallback
  when vec is unavailable, scope-alias end-to-end.
- rerank: hybrid-score ordering, recency boost crossover, source boost
  crossover, invalid-input rejection.

**Validator tweak** — `tests/validate-scripts.py` now recognizes the §26.2
approved runtime deps (`mcp`, `fastembed`, `sqlite_vec`, `tars_vault`)
alongside stdlib, so `build-search-index.py` no longer trips the check.

**Changelog** — first v3.1.0-dev entry added (covers Phase 4 only; prior
phases never landed their CHANGELOG entries and I left those gaps for the
next consolidation phase rather than retroactively writing them).

### Tests passing (exit 0)

- `tests/validate-structure.py` — PASS
- `tests/validate-routing.py` — PASS
- `tests/validate-references.py` — PASS
- `tests/validate-docs.py` — PASS
- `tests/validate-phase1-skeleton.py` — PASS
- `mcp/tars-vault/tests/test_search_index.py` — PASS (19/19)
- `tests/smoke-tests.py` — exits 0 (same daily-note warning as prior phases)
- End-to-end smoke of `build-search-index.py` against a two-note fixture
  vault under `/tmp`: first run indexed 2 files (1 chunk for the journal
  body), re-run skipped both as unchanged.

### Tests still failing (all pre-existing, confirmed via `git stash` baseline)

- `tests/validate-scripts.py` — 6 `yaml` imports in `archive.py`,
  `health-check.py`, `scan-flagged.py`, `scan-secrets.py`, `sync.py`,
  `validate-schema.py`. Unchanged from Phase 1a baseline; Phase 7 cleanup.
- `tests/validate-frontmatter.py` — 2 errors (meeting/tasks SKILL.md missing
  `user-invocable`), 36 warnings. Baseline; Phase 7 frontmatter sweep.
- `tests/validate-templates.py` — 1 error (`taxonomy.md` missing memory type
  def `person`), 6 warnings. Baseline.

### Design choices made (narrow defaults per §26.18)

1. **sqlite-vec KNN pattern** — used the two-step form: first query
   `vec_chunks WHERE embedding MATCH ? ORDER BY distance LIMIT k`, then look
   up metadata from `chunks` by rowid. This is the pattern sqlite-vec docs
   explicitly support; a direct JOIN with a `source_type` filter mixes
   indexed and non-indexed WHERE clauses in vec0 which is unreliable. To keep
   `limit` respected after source_type filtering, over-fetch 4× when a
   filter is present and slice after.
2. **Chunk budget approximation** — PRD §6.2 specifies 400 tokens / 80-token
   overlap but TARS scripts are stdlib-only (no tokenizer dep). Used ~300
   words / 60-word overlap which approximates the budget at bge-small's
   ~1.33 tokens/word. Deterministic and stable across runs.
3. **Rerank is deterministic, not LLM-backed** — PRD §6.5 says "Haiku,
   max_turns=1" for rerank. Invoking the Anthropic API from inside the MCP
   server requires (a) an API key provisioned to the server process and (b)
   a tight cost/latency budget we haven't agreed on. Shipped a deterministic
   score-based reranker with recency + source boosts that is correct in
   isolation; orchestrating skills (`/answer`, `/meeting`) can layer an LLM
   rerank via a sub-agent whenever they want, unchanged. See Deferred
   decisions.
4. **Scope alias on `fts_search`** — skill prose already uses
   `fts_search(scope="memory", …)` (from Phase 2 answer-skill rewrite) but
   the PRD's tool signature uses `tier` + `source_types`. Added `scope` as a
   convenience that expands to both; explicit `tier`/`source_types` still
   win. Keeps skill prose correct without forcing a re-edit.
5. **`tars_vault` path injection in build script** — the script imports
   `tars_vault.search_index` to reuse chunking / schema helpers. Because
   `mcp/tars-vault/src/tars_vault` isn't on the default PYTHONPATH when the
   script runs from `scripts/`, the script prepends `mcp/tars-vault/src` to
   `sys.path` itself. Alternative was to duplicate ~250 LOC into the script;
   avoided. Validator allowlist updated accordingly.
6. **Chunk rows without embeddings** — when vec_enabled=False (vec extension
   missing) or embedder unavailable, chunk rows still land in the `chunks`
   table so future re-indexes pick up only changed files via SHA diff, and
   so a later `--apply` with vec available can backfill. The skip-behavior
   is: `upsert_chunks(..., embeddings=None, vec_enabled=False)` inserts rows
   but no vectors; `semantic_search` returns fts_only in that state.
7. **Nuance-pass sub-agent type** — the PRD doesn't specify one. Used
   `general-purpose` which is universally available. Running Haiku is a
   model-selection decision the caller makes when spawning; the prompt file
   documents the intended config.
8. **`date` in Tier-A notes** — for memory notes without `tars-date`, fall
   back to a date found in the vault-relative path (e.g.
   `memory/YYYY-MM/...`). Most memory notes don't carry a date, which is
   fine — the rerank recency boost simply evaluates to 1.0× for them.

### Open ambiguities / needs user input

1. **LLM rerank wiring** — if/when the user wants the actual Haiku-backed
   rerank from §6.5, two things need to land:
   a. Anthropic API key flow for the MCP server process (`ANTHROPIC_API_KEY`
      env var? keychain? sibling MCP tool?).
   b. A per-invocation cost / latency cap so rerank doesn't accidentally
      dominate a budget on long result lists.
   For now the deterministic rerank covers the use case and the orchestrating
   skill can still spawn a sub-agent for LLM rerank when needed.
2. **Nuance-pass model selection in the sub-agent** — Claude Code's Agent
   tool accepts `model: "haiku"` but the skill prose leaves model selection
   implicit. If the user wants strict Haiku enforcement in the skill, add a
   line `model: haiku` to the Step 7b sub-agent invocation. Left loose per
   §26.18.
3. **`_system/embedding-cache/` provisioning** — cache dir is created on
   first apply; the ~80MB first-download is not pre-fetched in this phase.
   Phase 8 onboarding should surface a first-run message. Already gitignored
   from Session 1.
4. **Index rebuild cadence** — PRD §6.4 says rebuild via `/maintain` and a
   PostToolUse hook debounced 30s on prose-heavy mutations. The debounce
   logic is NOT wired in this phase; `scripts/build-search-index.py` just
   needs to be run manually or via `/lint`. Hook wiring is Phase 5/7.
5. **Tier-A chunking** — PRD says Tier-A is FTS-only but we still store
   chunks for Tier-B even when embeddings are unavailable. Tier-A always
   skips chunking. If the user later wants hybrid on memory notes
   (v3.2-deferred per §6.9), the schema already supports it — just expand
   `index_file` to produce chunks + embeddings for Tier A.

### What the next session should pick up

**Phase 5 — Consolidation and noise reduction (§7)**:
- Retire historical rebuild docs (6 files, ~197KB) to `archive/historical/`.
- Template consolidation, skill-body trimming (§7.3), script consolidation
  (§7.4 — scan-flagged into health-check, etc. — this also unblocks the
  yaml-import validator errors).
- `.mcp.json` project defaults (§7.6).

Before starting, the next session should:
1. Read PRD §7 in full.
2. Run `scripts/githooks/install-githooks.sh` (idempotent).
3. Run `python3 mcp/tars-vault/tests/test_search_index.py` to confirm Phase 4
   hasn't drifted.
4. Run `python3 tests/validate-phase1-skeleton.py`.

### Files touched this session

Tracked (modified):
- `mcp/tars-vault/src/tars_vault/search_index.py` — full implementation.
- `mcp/tars-vault/src/tars_vault/tools/fts_search.py` — real body.
- `mcp/tars-vault/src/tars_vault/tools/semantic_search.py` — real body.
- `mcp/tars-vault/src/tars_vault/tools/rerank.py` — real body (deterministic).
- `scripts/build-search-index.py` — full incremental builder.
- `skills/meeting/SKILL.md` — preamble, pipeline overview, Step 7b insertion,
  Step 8 body placeholder, constraint #15.
- `tests/validate-scripts.py` — approved-runtime-deps allowlist.
- `CHANGELOG.md` — new `v3.1.0-dev — WIP` section with Phase 4 entry.
- `docs/HANDOFF-NOTES.md` (this entry).

Tracked (added):
- `mcp/tars-vault/tests/test_search_index.py` — 19 unit tests.
- `skills/meeting/reference/nuance-pass-prompt.md` — verbatim §26.8 prompt.

