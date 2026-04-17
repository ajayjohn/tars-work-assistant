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
