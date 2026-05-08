# Changelog

## v3.5.0 (2026-05-08)

### Added

- **Session start now uses plain, state-aware guidance.** TARS avoids the old wall of setup jargon, suppresses repeated schedule and integration notices, shows empty-folder and welcome-back hints, and surfaces stale initiatives, overdue tasks, inbox items, version drift, and non-TARS frontmatter in user-facing language.
- **The local helper can read managed system files.** `read_system_file` returns parsed YAML for system settings while keeping traversal and unsupported file types blocked.

### Fixed

- **Migration runs no longer end with a traceback.** The migration journal handles older result shapes safely, stamps successful runs, and unexpected failures are converted into a one-line error with a telemetry log.
- **Fresh seeds no longer claim to be on an old plugin version.** New workspaces stamp the live plugin version during setup instead of inheriting a stale migration state.
- **Workspace writes now fail closed.** MCP writes are blocked when the install record points at another workspace, unknown tool arguments are rejected, and automatic vault resolution no longer falls back to an arbitrary current directory.
- **Freeform note writes no longer create empty files.** `write_note_from_content` accepts full Markdown content or split frontmatter/body, rejects mixed shapes, and shares create-time schema validation.
- **Created notes are validated against workspace schemas.** Managed notes with missing required fields or invalid enum values now fail before anything is written, with `validate=false` available for intentional partial stubs.
- **Managed paths are protected.** Direct writes, moves, archives, and frontmatter updates are blocked for TARS system areas and generated views unless an internal maintenance flow opts in.
- **Secret scanning catches more common tokens.** Slack, GitHub, Stripe, Twilio, SendGrid, Google, OpenAI, and Anthropic key patterns are now blocked.
- **Obsidian views carry a generated-by version stamp.** Newly scaffolded views include the plugin version so stale generated views can be detected later.

## v3.4.4 (2026-05-07)

### Fixed

- **Installed `/welcome` no longer exposes missing skill-file lookups.** The command wrapper now tells Claude not to read packaged skill files from the user's workspace, so a fresh workspace does not show `note not found: skills/welcome/SKILL.md`.
- **Fresh setup closeout now gives a concrete first demo.** The welcome fallback and full skill both ask the user to paste or upload a meeting transcript, PDF/report excerpt, email thread, or rough notes so TARS can preview memory, journal, and task extraction before saving anything.
- **Slash commands are explained as optional shortcuts.** The welcome closeout now includes natural-language examples next to the most useful starter commands instead of leaving users to memorize command names.
- **Empty workspaces no longer get briefing as a starter suggestion.** Welcome now avoids recommending `/briefing` until the workspace has useful context, tasks, meetings, or integrations.

## v3.4.3 (2026-05-06)

### Fixed

- **Packaged helper registration now uses Claude's plugin manifest path.** The install artifact declares `tars-vault` directly in packaged `plugin.json` and ships a plugin-root `.mcp.json`, so Claude can register `mcp__tars_vault__runtime_info`, `mcp__tars_vault__scaffold_workspace`, and the rest of the local helper tools after marketplace install.
- **The local helper no longer requires a pip-installed MCP SDK.** `tars-vault` now falls back to a bundled stdlib MCP transport when the Python `mcp` package is unavailable, so marketplace users only need Python for first setup.
- **Installed plugin now includes command wrappers and MCP metadata.** The release package now ships `commands/` and `.claude-plugin/mcp-servers.json` so `/welcome`, `/start`, and the rest of the command surface route into TARS reliably after marketplace-style install.
- **Fresh setup is deterministic for Sonnet or stronger models.** `/welcome` is now a short setup contract that asks essential personalization questions, calls the deterministic scaffold tool, verifies `index.md`, `_system/install.yaml`, `_system/config.md`, `memory/`, and `inbox/pending/`, then offers an immediate demo with a transcript, report, email thread, or notes.
- **Setup failures now explain the local TARS helper, not raw tool plumbing.** `/welcome` and `/doctor` describe `tars-vault` as the one required local helper, keep Obsidian/calendar/tasks/email/Slack clearly optional, and give nontechnical recovery steps before technical details.
- **The first-run closeout now prescribes a concrete demo.** After setup, TARS asks the user to paste or upload a meeting transcript, PDF/report excerpt, email thread, or rough notes so it can preview memory candidates, journal notes, and tasks.
- **The installed runtime contract no longer carries stale Obsidian assumptions.** Shipped `CLAUDE.md` now states that the Markdown workspace is authoritative, Obsidian is optional, writes go through `tars-vault`, and uninitialized workspaces must route to `/welcome`.
- **Obsidian mode scaffolds views without changing the data model.** Headless setup creates the canonical portable workspace only; Obsidian setup creates the same workspace plus `_views/*.base`.
- **Release validation now tests the artifact users install.** New artifact validation extracts the built zip, verifies required packaged files, starts the packaged local helper over stdio, fails unless required tools are visible, runs scaffold from the extracted helper, rejects generic `knowledge/`, `projects/`, or `research/` setup folders, and checks the generated `index.md` for natural-language and inbox guidance.
- **Helper/tool contract gaps are closed.** `resolve_alias` and `runtime_info` are now real helper tools, semantic search accepts `limit` as well as `top_k`, and single-property `update_frontmatter` examples are supported.
- **Semantic-search dependencies are optional.** `requirements.txt` has no third-party requirement for first setup; `fastembed` and `sqlite-vec` live in `requirements-search.txt` and degrade to FTS-only when absent.

## v3.4.2 (2026-05-06)

### Fixed

- **Fresh setup now creates the real workspace.** `/welcome` now calls a deterministic MCP scaffold tool so `inbox/`, `memory/`, `journal/`, `archive/`, `_system/`, and root `index.md` are created in the selected workspace instead of relying on model-only folder creation.
- **First-run onboarding asks essential questions again.** The welcome flow captures name, role/title, company/team, first use case, persona, and workspace type before scaffolding, then offers a guided first demo with a transcript, report, email thread, or inbox file.
- **Plugin installs without an explicit `TARS_VAULT_PATH` no longer drift silently.** The MCP server now falls back to the Claude-selected working folder when the env var is unset or passed through as a literal shell variable.
- **Install records can be verified through MCP.** `_system/install.yaml` and other explicit non-Markdown system files can now be read through the shared MCP path resolver.
- **TARS path-qualified wikilinks work again.** The wikilink validator now allows TARS links such as `[[memory/people/alex]]` while still rejecting illegal characters inside each path segment.

### Added

- **Real-world smoke tests.** `tests/test_real_world_smoke.py` now validates fresh headless setup, Obsidian-mode setup, inbox/memory/index creation, MCP read/write/search, task references, archive guardrails, duplicate detection, secret scanning, FTS indexing, and semantic-search fallback behavior.

## v3.4.1 (2026-05-05)

### Added

- **Inbox-first onboarding.** Welcome, help, README, Getting Started, and Catalog now explain that users can drop transcripts, PDFs, decks, docs, screenshots, exports, and notes into `inbox/pending/` and ask TARS to process the inbox in bulk.
- **Deferred setup continuation.** `/welcome --continue-setup` and the natural-language request "continue TARS setup" resume people, initiative, integration, schedule, brand, maintenance, and Obsidian setup after the one-minute path.
- **Runtime doctor.** `scripts/doctor.py` checks Python, MCP importability, workspace path resolution, write permissions, and install-record consistency with cheap deterministic output.

### Changed

- **Natural-language-first cheat sheet.** The generated workspace `index.md` now states that slash commands are shortcuts and includes natural-language examples for every workflow.
- **Workspace terminology.** User-facing setup and docs consistently call the working folder a workspace, with a clear note that an Obsidian-enabled workspace is also an Obsidian vault.
- **Safer setup defaults.** Fresh setup now recommends `~/Documents/TARS Workspace`, shows the Claude-selected folder and active TARS workspace before scaffolding, and stops when the requested folder cannot be honored by the active MCP session.

### Fixed

- **Accidental `.claude` workspaces.** Hooks and doctor checks now warn or block fresh writes when the active workspace resolves under `~/.claude` without an explicit existing install record.
- **Self-learning documentation.** Getting Started now describes the supported observed-preference review loop without implying that proposals are auto-applied.
- **Stale index references.** Remaining user-facing `_index.md` guidance now points to search, `.base` views, or targeted workspace reads.

## v3.4.0 (2026-05-05)

### Added

- **Local Markdown workspace mode.** `_system/install.yaml` now records `workspace_type`, `workspace_path`, `obsidian_enabled`, and `obsidian_vault_path`, while preserving `vault_path` as a backward-compatible alias.
- **`/start` and `/help`.** New first-time demo and grouped help commands make TARS useful before integrations or Obsidian setup.
- **Coaching state.** `_system/maturity.yaml` now tracks restrained coaching, dismissed tips, milestone counters, and Daily Digest "Next useful thing" suggestions.
- **Example inputs.** Product, Engineering, and Sales paste targets support zero-setup evaluation.
- **Workspace validation.** `tests/validate-workspace.sh` provides a fast cross-cutting regression check.
- **Existing-user backfill script.** `scripts/migrate-install-record.py` adds local-workspace install fields to existing Obsidian installs without moving data.

### Changed

- **Progressive `/welcome`.** Setup now starts with folder, identity, persona, and workspace type, then defers integrations, people, initiatives, schedules, and Obsidian helper skills.
- **Obsidian is optional.** `/welcome --enable-obsidian` and `/welcome --disable-obsidian` switch the view layer without moving or rewriting existing data.
- **Docs and plugin metadata.** README, Getting Started, Architecture, Catalog, MCP README, and marketplace metadata now describe the Markdown workspace as the primary data model.

### Fixed

- **`search_by_tag` implementation gap.** The MCP tool now supports the `query` and `frontmatter` filters already used by skills.
- **Archive guardrails.** `archive_note` now checks recent backlinks and active task references, and supports `dry_run`.
- **Dead MCP modules removed.** Unused skeleton modules were deleted so the source tree no longer advertises incomplete paths.
- **FastEmbed first-run warning.** `/answer` now warns before the one-time embedding model download.

## v3.3.0 (2026-05-05)

**Design-efficiency release: doc-code alignment, token trimming, and mode removal.**

This release resolves documentation-implementation mismatches, removes the casual/standard engagement-mode bifurcation, consolidates redundant always-on token surface, and adds data-integrity safeguards for the alias registry and session stubs.

### Removed

- **Engagement modes (`standard` | `casual`).** The `mode:` field in `_system/install.yaml` is removed. All vaults now run the full pipeline and TARS adjusts automatically based on connected integrations. Migration `v3.3.0-remove-casual-mode.py` strips the obsolete field.

### Fixed

- **PostToolUse doc-code mismatch.** 18 incorrect claims across 8 skill files and the hooks README incorrectly stated that the `PostToolUse` hook writes to the daily note, changelog, or deduplicates backlog issues. In reality, it only emits `vault_write` telemetry events. All skills now explicitly write daily-note summaries and changelog entries via `mcp__tars_vault__append_note`.
- **Session-stub coalescing.** `pre-compact.py` and `session-end.py` now check for existing stubs with matching `(session_id, calendar_day)` before writing, preventing duplicate stubs when both hooks fire for the same session.

### Added

- **Alias registry rebuild migration (`v3.3.0-rebuild-alias-registry.py`).** Recomputes `_system/alias-registry.md` from entity-note `aliases:` frontmatter. Existing manual-only entries are preserved in a `## Manual entries` section for user review.
- **Lint empty-review skip gate.** Scheduled lint runs that find zero Critical, Warning, or Auto-fixable findings skip writing the review file entirely and emit a `lint_clean` telemetry event. Prevents inbox clutter from clean-vault nightly runs.

### Changed

- **CLAUDE.md token reduction (~1,190 tokens, ~13%).** The duplicated MCP tools table, key constraints enumeration, and routing table were replaced with compact pointers to canonical definitions in `skills/core/SKILL.md`.
- **Decision frameworks catalog relocated.** The full framework catalog (12 frameworks) moved from `skills/core/SKILL.md` (always-loaded, ~260 tokens) to `skills/think/manifesto.md` (loaded on demand when `/think` is invoked). Core retains a one-line pointer.
- **Banned phrases table compacted.** 12-row table replaced with grouped-by-category format (~100 tokens saved).
- **Session self-evaluation rewritten (Phase 5).** Session-end self-evaluation now uses structured criteria instead of freeform reflection.
- **ARCHITECTURE.md, GETTING-STARTED.md, CATALOG.md** updated to reflect casual-mode removal and v3.3 version.

### Migration

Existing v3.2 vaults: run `python3 scripts/run-migrations.py --vault <path> --apply` to apply `v3.3.0-remove-casual-mode` and `v3.3.0-rebuild-alias-registry`. Both migrations are safe and reversible.

---

## v3.2.1 (2026-05-04)

**Patch — fix hook and MCP server paths that break on spaces in directory names.**

Paths containing spaces (e.g. `Library/Application Support/`) caused all six plugin hooks to fail at launch because `${CLAUDE_PLUGIN_ROOT}` was not quoted in the shell command strings inside `hooks/hooks.json`. The unquoted expansion split the path into multiple shell arguments, breaking the `python3` invocation.

### Fixed

- **`hooks/hooks.json` — quote `${CLAUDE_PLUGIN_ROOT}` in all hook commands.** All six hook entries (`SessionStart`, `InstructionsLoaded`, `PreToolUse`, `PostToolUse`, `PreCompact`, `SessionEnd`) now wrap the expanded path in double quotes so paths with spaces are treated as a single argument.
- **`.claude-plugin/mcp-servers.json` — updated comment to v3.2.1.**

## v3.2.0 (2026-05-03)

**Persistence, cold-start, wikilink hygiene, and self-improvement plumbing.**

A round of foundational work: every onboarded user can produce a useful day-1 briefing, broken backlinks stop accumulating and existing ones get repaired, the cron-fired weekly job actually has work to do, and observed preferences accrue without manual restating. Casual users who only use TARS for occasional decks/drafts/brainstorms are explicitly supported via a `mode: casual` toggle that gates review queues and weekly cron registration.

### Added

- **Persistent install record (`_system/install.yaml`).** Vault-specific record carrying `vault_path`, `installation_id`, `persona`, `mode`, `plugin_version`, and timestamps. Hooks consult it on every session start to detect a moved or duplicated vault and refuse silent writes.
- **Persona templates (`templates/personas/`).** Seven starter profiles — product-leader, sales-customer-facing, delivery-pm, data-science-lead, architect-staff-eng, support-ops-lead, engineering-manager — each ~1.5 KB with `tars-config-defaults`, `tars-taxonomy-tags`, `tars-briefing-sections`, `tars-default-mode`. The wizard reads the chosen persona and applies its defaults to `_system/config.md` and `_system/taxonomy.md`.
- **Engagement modes (`standard` | `casual`).** Casual mode skips Step 5 rounds 3-4 in welcome, registers only the daily-briefing cron (opt-in), and suppresses staleness/drift/curator proposals on session start. Power-user behavior is the default.
- **Wikilink discipline (forward correctness).** New MCP tool `mcp__tars_vault__format_wikilink(text, kind)` resolves raw text into an Obsidian-safe wikilink via the alias registry and vault file lookup. Status taxonomy: `resolved`, `disambiguation_needed`, `new_entity`, `error`. Skills MUST use this instead of hand-forming `[[...]]`.
- **Wikilink discipline (write-side rejection).** `create_note`, `append_note`, `write_note_from_content` reject content payloads containing wikilinks with smart quotes or Obsidian-illegal characters. The `pre-tool-use` hook runs the same scan as defense-in-depth.
- **Wikilink retroactive repair.** `scripts/fix-wikilinks.py --repair-broken` scans every wikilink, classifies into `auto_safe` / `needs_review` / `unresolvable` buckets, and `--apply` only acts on `auto_safe`. The other two buckets surface via `/lint --actions wikilinks`. The four-pattern bracket repair from v3.1 is preserved.
- **`_views/broken-links.base`** — Bases view over notes with broken-link counts.
- **40 KB body cap + `tars-` prefix enforcement at the hook layer.** `pre-tool-use` rejects oversized bodies on non-chunking write tools (pointing the caller at `append_note`) and rejects non-prefixed frontmatter keys outside the reserved set (`tags`, `aliases`) unless `allow_user_properties=true`.
- **SessionStart banner.** Composes install-mismatch warning, legacy-vault notice, stale `tools-registry.yaml` notice (24h TTL), and unregistered-cron notice (parses `_system/housekeeping-state.yaml` cron_jobs block).
- **Session-summary stubs.** `pre-compact` and `session-end` write `inbox/pending/claude-session-<ts>.md` with frontmatter so `/maintain inbox` surfaces sessions next time.
- **Telemetry rollup script (`scripts/telemetry-rollup.py`).** Stdlib aggregator over `_system/telemetry/*.jsonl`. `--days N` (default 7), `--format text|json`, `--since`/`--until` window overrides. Aggregates events-by-type, skills loaded, vault writes by destination, retrieval source-tier mix, miss signals, daily totals. Single source feeds `/briefing` weekly footer + `/maintain --weekly`.
- **Active `/lint --actions` mode.** Materializes fixable findings as a numbered queue. Two surfaces: inline for interactive users, `inbox/pending/weekly-review-YYYY-MM-DD.md` for cron-fired callers. Subsets: `wikilinks`, `patterns`, `curator`.
- **Weekly maintenance job (`/maintain --weekly`).** Cron-fired Sunday 18:00 (registered by `welcome` Step 7 in standard mode). Pipeline: telemetry rollup → `_system/changelog/`, backlog auto-grouping, `/lint --actions`, `/learn --review-patterns` proposals, curator + persona-drift proposals, materialize the weekly review file, update housekeeping-state cooling-off timestamps.
- **Briefing weekly-rollup footer.** `/briefing` calls the rollup script in text mode on the configured weekday (default Monday) and appends the output. Degrades silently on script error or zero-event windows.
- **User model (`templates/user-model.md`).** Single living note (~5 KB cap) capturing observed preferences distinct from declared config: BLUF tolerance, decision speed, default skill, meeting cadence, recurring concerns, vendor sentiment, observed skill mix. Updated passively by `/learn` Mode C when patterns repeat ≥3× in 14 days.
- **Workflows (`templates/workflows.yaml`).** Vault-owned saved multi-step routing aliases. Created only on user approval of pattern proposals from `/maintain --weekly`. `core` consults the registry before default routing.
- **`/learn --review-patterns` (Mode C).** Detects candidate patterns from telemetry, returns proposals to either an inline numbered list or to `/maintain --weekly`'s review queue. Honors `tars-pinned-fields` and `pinned: true`.
- **Vault-side staleness curator (`scripts/archive.py --check workflows`).** Workflow-staleness check (60 days unused) and memory-staleness check honoring `tars-pinned: true`. Always archive, never delete. Surfaced via `/lint --actions curator` and `/maintain --weekly`.
- **Persona-drift detection.** Inside `/maintain --weekly`, runs only when ≥30 days of telemetry exist and the cooling-off window (14 days) has elapsed. Compares observed skill-mix signature against persona expectations and proposes a switch when drift exceeds threshold.

### Changed

- **Routing rules.** `core` now consults `_system/workflows.yaml` (workflow-alias expansion) and `_system/user-model.md` (observed-preference soft defaults) before default fallthrough. Declared config in `_system/config.md` always wins on conflict.
- **Wikilink discipline paragraph in `core`.** New mandatory subsection. One-line pointers added to `meeting`, `learn`, `communicate`, `briefing`, `initiative`, `answer`, `tasks`.
- **Welcome wizard restructured.** New Step 1.5 (persona + mode pick), Step 2b writes `install.yaml`, Step 5 skips rounds 3-4 in casual mode, Step 6 skips weekly-schedule prompts in casual mode, Step 7 registers `tars-weekly-maintenance` cron in standard mode.
- **Lint check table.** New rows: install-record health, observed-vs-declared drift, user-model staleness, workflows registry health.
- **Maintain weekly mode** is now a real pipeline; the v3.1 Step 4 telemetry-rollup-as-journal-note was removed in favor of `scripts/telemetry-rollup.py` and `/lint` ownership of telemetry-derived findings.
- **Stdlib YAML parser** in `tars_vault/_common.py` now correctly recognizes nested-mapping keys that contain hyphens (e.g. `tars-bluf-level:`).

### Removed

- **`.claude/skills/defuddle/`.** Not central to any of the seven personas; URL ingestion (rare) falls back to `WebFetch`. References in `welcome`, `CLAUDE.md`, `maintain`, and `tests/smoke-tests.py` were also removed.
- **Two legacy `obsidian-cli` direct examples** in `core` and `meeting` replaced with `mcp__tars_vault__*` equivalents.

## v3.1.1 (2026-04-18)

**Patch — make the `tars-vault` MCP server actually work.**

The v3.1.0 release shipped the Python MCP harness as a Phase-1a skeleton: `run_stdio()` instantiated a `Server` object but never entered the request loop, so the process exited immediately on launch and Claude Code reported the server as failed to connect. 13 of 17 tool handlers raised `NotImplementedError`. This release lands real, minimal-but-correct implementations so `/tars:*` skills can function end-to-end.

### Changed — `mcp/tars-vault/`

- **`server.py` — real request loop.** `run_stdio()` now wires `list_tools` and `call_tool` handlers against the MCP Python SDK's `Server` + `stdio_server`, returns `InitializationOptions(server_name="tars-vault", server_version="3.1.1", ...)`, and blocks on `server.run(read, write, init_opts)`. Tool dispatch runs synchronous handlers via `asyncio.to_thread` and wraps all exceptions so a bad handler can't kill the server.
- **`_common.py` (new).** Stdlib-only frontmatter parser + serializer supporting scalars, flow/block lists, and one-level nested mappings — the subset TARS frontmatter actually uses. No PyYAML runtime dependency.
- **`tools/read_note.py`** — reads a note, returns parsed frontmatter + body + path.
- **`tools/create_note.py`** — writes a new note with schema-light validation; rejects non-tars-prefixed keys unless `allow_user_properties=true`; refuses to overwrite unless `overwrite=true`.
- **`tools/write_note_from_content.py`** — alias of `create_note` (template-free path, resolves issue-obsidian-template-not-configured).
- **`tools/append_note.py`** — appends with automatic 40KB chunking (resolves issue-obsidian-append-large-content).
- **`tools/update_frontmatter.py`** — upserts or deletes frontmatter keys; same prefix-enforcement as `create_note`.
- **`tools/search_by_tag.py`** — walks the vault, parses frontmatter, matches exact tag or (with `prefix_match=true`) tag prefix.
- **`tools/archive_note.py`** — archives into `archive/YYYY-MM/` with guardrails: refuses if note carries a durable tag (`tars/decision`, `tars/org-context`) or `tars-archive-exempt: true`, unless `force=true`. Uses `move_note` internally so wikilink refs follow.
- **`tools/move_note.py`** — moves a note and rewrites path-qualified wikilinks (`[[folder/old]]` and `[[folder/old|alias]]`) across the vault.
- **`tools/classify_file.py`** — path-based classifier for the Organization Engine. Rule set covers resumes, walkthroughs, meeting prep, DBI/data-hub, research/strategy/roadmap, and screening-interview-CV docs; falls through to `contexts/misc/` at low confidence.
- **`tools/detect_near_duplicates.py`** — three similarity signals (content SHA-256, normalized filename, body-prefix hash) with cluster reporting.
- **`tools/resolve_capability.py`** — reads `_system/integrations.md` preferences + `_system/tools-registry.yaml` discovered state; prefers connected servers, falls back to declared, returns `unresolved` with reason when nothing covers a capability.
- **`tools/refresh_integrations.py`** — shells out to `scripts/discover-mcp-tools.py` and returns the updated registry path.
- **`tools/scan_secrets.py`** — stdlib-only guardrail loader + matcher; classifies content as `clean`/`warn`/`block` against `_system/guardrails.yaml`.

### Changed — `scripts/`

- **`fix-wikilinks.py` — real implementation.** Applies the four regex transforms documented in the v3.0 → v3.1 migration runbook (`[[[[X]]|X]]` → `[[X]]`, `[[[[X]]|Y]]` → `[[X|Y]]`, `[[[X|Y]]` → `[[X|Y]]`, defensive `[[[[X]]` → `[[X]]`). Writes per-file `.pre-v3.1-wiki-backup`. `--skip-dirs` defaults to `.git,.claude,.obsidian,archive`. Honors the PRD §26.15 migration-script contract (clean-worktree check before `--apply`).
- **`discover-mcp-tools.py` — real implementation.** Reads `.mcp.json`, classifies servers via a short-name hint table + command/URL regex, probes `claude mcp list` status when available, and emits a `_system/tools-registry.yaml` with capability coverage, transport, and ttl.

### Added — tests

- **`mcp/tars-vault/tests/test_tools.py`** — 14 stdlib-only unit tests covering the write path (create/read/append/update), search, classify, dedupe, move+wikilink-rewrite, archive guardrails, capability resolution, and secret classification. All pass.

### Known remaining gaps (v3.2 candidates)

- No dedicated `resolve_alias` tool; alias lookups still route through `search_by_tag` + direct read of the alias-registry markdown. Adequate for v3.1.1 skill prose, but a single-call tool would tighten the read path.
- `discover-mcp-tools.py` only probes `claude mcp list` for connection status — it does not invoke each server's `tools/list` to enumerate tool names. The `tools:` arrays in the generated registry are empty; capability coverage comes from the short-name hint table alone.
- `fix-wikilinks.py` is regex-only; it does not consult the alias registry to propose canonical targets for unresolved links. The ~247 broken links surfaced after the v3.0 → v3.1 wikilink repair remain broken until v3.2 adds auto-stub creation.

## v3.1.0 (2026-04-17)

**TARS 3.1: Harden, simplify, and extend — hooks, MCP wrappers, hybrid retrieval, office productivity**

### Phase 8 — Docs (§8)
- **CLAUDE.md**: version bump to v3.1. New "Write interface: `tars-vault` MCP tools" section documents all `mcp__tars_vault__*` tools. Skill roster adds `/lint`. Startup checks re-ordered around the SessionStart hook + integration-registry refresh + Anthropic-skills probe. Key constraints expanded: `mcp__tars_vault__*` mandate, provider-agnostic resolve_capability rule, office-delegation rule, nuance-capture rule. Vault structure block updated (telemetry, search-index, embedding-cache, tools-registry, search.db). Template + script blocks reflect the Phase 7 consolidation.
- **README.md**: version-agnostic intro broadened with retrieval, integrations, office-delegation, nuance-capture bullets. Architecture-at-a-glance adds `hooks/` and `mcp/tars-vault/`. Documentation map links to the new Migration / Release / Mobile guides.
- **ARCHITECTURE.md**: renamed to "TARS 3.1 Architecture". New "Three operations" framing paragraph. Repo-layout block adds `.mcp.json`, `mcp/tars-vault/`, `hooks/`, `scripts/githooks/`, `archive/historical/`, `docs/`, `requirements.txt`. Runtime-layers section gains explicit "Write interface", "Hooks", "Retrieval", "Integration (provider-agnostic)", and "Office output" sub-sections. State/schema layer documents the v3.1 additions (`tools-registry.yaml`, `telemetry/*.jsonl`, `search-index-state.json`, `search.db`). Template layer lists the consolidated `briefing.md` and `backlog-item.md`. Added "What's new in v3.1" section covering all 10 strategic bets. Retrieval section rewritten with the hybrid tier-A / tier-B priority.
- **GETTING-STARTED.md**: prerequisites add Python 3.10+ and `tars-vault` MCP server. Installation section adds the `pip install -r requirements.txt` step and sets the zero-office-libs expectation. Integrations section rewritten around the capability-preference map and `resolve_capability`. New "First semantic search — FastEmbed model download" and "Office output prerequisites" subsections. `/lint` added to "Your first workflows".
- **New `docs/MIGRATION-v3.0-to-v3.1.md`**: 9-step user-executed migration runbook (backup → integrations-v2 migration → wikilink fixes → search-index build → githooks install → `/welcome` refresh → `/lint` pass → cron registration → verification). Rollback, duration, known-issues sections included.
- **New `docs/RELEASE-v3.1.0.md`**: user-executed release runbook (authorship guards, pre-release verification, retroactive tag backfill, version bump, CHANGELOG finalization, commit, build, tag, merge, push). Zero-Claude-attribution enforced via the installed git hooks.
- **New `docs/MOBILE-USAGE.md`**: Claude Remote Control setup + daily use + troubleshooting + security for iOS / Android. Matches §26.14 outline — Pro/Max plan + launchd keepalive + mobile mic-first workflow.

### Phase 7 — Consolidation and cleanup (§7)
- **Repo cleanup (§7.1)**: 6 legacy rebuild docs (`TARS_REBUILD_FOUNDATION.md`, `TARS_V2_REBUILD_PLAN.md`, `TARS_V3_REBUILD_PLAN.md`, `TARS_V3_INSTANCE_MIGRATION_PLAN.md`, `MIGRATION_HANDOFF.md`, `REBUILD_HANDOFF.md` — ~197 KB) moved from the repo root into `archive/historical/`. They were already untracked via `.git/info/exclude`, so no git history was rewritten.
- **Template consolidation (§7.2)**: `templates/daily-briefing.md` + `templates/weekly-briefing.md` → single `templates/briefing.md` with `tars-briefing-type: daily|weekly`. `templates/issue.md` + `templates/idea.md` → single `templates/backlog-item.md` with `tars-backlog-type: issue|idea`. Skills (`briefing`, `learn`, `meeting`) and `_system/taxonomy.md` updated to reference the merged templates. Net: 17 templates → 15.
- **Script consolidation (§7.4)**: `scripts/scan-flagged.py` merged into `scripts/health-check.py` as a `flagged_content` sub-block (markers, unmarked sentiment, stale-flag count). `_system/guardrails.yaml` header, `tests/smoke-tests.py` required-scripts list, `skills/lint/SKILL.md`, and `skills/welcome/SKILL.md` updated to point at the consolidated script. Net: 13 scripts → 12.
- **Validator hardening**: `tests/validate-scripts.py` now treats imports wrapped in `try/except ImportError|ModuleNotFoundError` as optional (§26.2 "graceful degrade path"), which unblocks the 6 pre-existing YAML-fallback scripts without loosening the pinned-deps allowlist.
- **Commands readme (§7.5)**: new `commands/README.md` documents the 12 command-to-skill mappings; the thin wrappers remain in place pending end-to-end verification of Claude Code skill auto-registration (narrow-path per §26.18 — retirement deferred).
- **`.mcp.json` project defaults (§7.6)**: repo-root `.mcp.json` now declares the `tars-vault` MCP server entry (stdio transport, `python3 -m tars_vault`, `PYTHONPATH=mcp/tars-vault/src`), alongside the existing `filesystem` server.
- **Doc counts synced**: `README.md` and `ARCHITECTURE.md` framework-inventory summary sentences updated to reflect 13 commands / 12 scripts / 15 templates.
- **Deferred (documented in `docs/HANDOFF-NOTES.md`)**: deep skill-body trimming to the ≤300-line target (meeting, welcome, think, learn, briefing), retirement of the 12 thin command wrappers, shared-validator extraction into `scripts/lib/validators.py`.

### Phase 5 — Backlog fixes + state self-healing (§5)
- **Brand auto-load (§5.1)**: new `templates/brand-guidelines.md` with `tars-brand: true` flag. `/communicate` gains a mandatory Step 0 that resolves the active brand (via `_system/config.md`.`tars-active-brand` or a `search_by_tag(tag="tars/brand")` filtered on the frontmatter flag) and caches the chosen file for future sessions. `/create` Step 2 performs the same resolution and forwards the brand-file path to the render skill.
- **Framework self-state (§5.2)**: `scripts/sync.py` grows a `compute_hydration()` helper and a `--hydration` flag that returns live counts of people / initiatives / decisions / journal / task notes. `/briefing` (daily + weekly) now sources its System-status line from the live count rather than the drifting `_system/maturity.yaml`. The "Level 2 (15 people, 42 meetings)" artifact is gone; `/lint` owns the `maturity.yaml` repair per the updated check-table row.
- **Task lifecycle (§5.3)**: `_system/schemas.yaml` gains optional fields `tars-blocked-by`, `tars-age-days`, `tars-escalation-level` on the task schema (plus `tars-category`, `tars-completed`, `tars-completed-by`) and `tars-brand` / `tars-draft-status` on a new `context-artifact` schema. `/tasks` manage-mode sort is now escalation-aware (level 3 → 2 → 1 → 0, then overdue, then due-date, then priority). `/lint` owns the computation of `tars-age-days` / `tars-escalation-level` on its nightly pass with 30d / 60d / 90d thresholds.
- **Telemetry + reflection (§5.4)**: `hooks/_common.py` gains `append_telemetry()`. `hooks/post-tool-use.py` emits `vault_write` events for successful `mcp__tars_vault__*` mutations. `hooks/instructions-loaded.py` emits `skill_loaded`. New `_views/skill-activity.base` queries `tars/telemetry-rollup` notes; `/maintain sync` now produces the 14-day rollup note that populates the view. New `/lint` rules: memories-saved-but-never-re-read and tasks-created-but-never-transitioned.

### Phase 6 — /create office-productivity upgrade (§8.10)
- **Orchestrator rewrite**: `skills/create/SKILL.md` rewritten as a 9-step orchestrator — capability probe → intake → brand auto-load → context gathering → format selection → content-first markdown draft → review → delegate render → verify + companion + telemetry. Renders delegate exclusively to Anthropic's first-party `pptx`, `docx`, `xlsx`, `pdf`, `web-artifacts-builder` skills. TARS ships zero office-format libraries.
- **Structural templates**: new `templates/office/` with content-outline templates (`deck-executive`, `deck-narrative`, `deck-technical-review`, `spreadsheet-kpi-dashboard`, `spreadsheet-roadmap`, `doc-decision-memo`, `doc-project-status`, `html-board-update`) plus a README documenting the delegation split. Each template is plain markdown with `{{placeholder}}` fields.
- **Companion-note contract (§26.13)**: `/create` Step 8 writes the per-artifact `.md` companion under `contexts/artifacts/YYYY-MM/<slug>.md` with `tars-companion-of`, `tars-generated-by`, `tars-brand-applied`, `tars-source-data`, SHA-256, etc. Schema updated (`companion` in `_system/schemas.yaml`) to cover all office companion fields and the `html` original-type value.
- **`/welcome` pre-flight addition**: the onboarding flow now probes which Anthropic first-party skills are available in the host Claude Code install and persists the result in `_system/config.md.tars-anthropic-skills`. `/create` reads this at session start instead of reprobing per invocation. `/welcome` also offers to scaffold the first brand file from `templates/brand-guidelines.md`.
- **New validator**: `tests/validate-phase5-6.py` asserts brand-auto-load plumbing, hydration flag, task-lifecycle fields, telemetry hook wiring, office templates presence, `/create` step markers, and the absence of any reintroduction of a custom office MCP.

### Phase 4 — Hybrid retrieval + meeting nuance pass (§6)
- **Hybrid retrieval index**: `scripts/build-search-index.py` now builds FTS5 (Tier A: `memory/**`; Tier B: `journal/**`, `archive/transcripts/**`, `contexts/**`) plus a `sqlite-vec` vector layer over Tier B with `BAAI/bge-small-en-v1.5` (384-dim) embeddings via FastEmbed. Incremental SHA-256 state at `_system/search-index-state.json`; bounded 10-minute runs; graceful FTS-only fallback when FastEmbed or sqlite-vec is unavailable.
- **MCP search tools implemented**: `mcp__tars_vault__fts_search` (keyword, tier+source filters), `mcp__tars_vault__semantic_search` (hybrid 0.7 semantic + 0.3 FTS, scope by journal/transcripts/contexts/all, optional date filter), `mcp__tars_vault__rerank` (deterministic score-based rerank with recency + source boosts).
- **Meeting nuance pass (Step 7b)**: new sub-step inserted in `skills/meeting/SKILL.md` between summary and persistence. Spawns a Haiku sub-agent with the verbatim PRD §26.8 prompt to capture notable phrases, contrarian views, specific quotes, unusual terms, strong emotional statements, and missed numbers/dates. Rendered as `## Notable phrases & perspectives` in the journal entry. Telemetry: `meeting_nuance_captured` or `meeting_nuance_failed`. Never blocks the pipeline.
- **Test surface**: `mcp/tars-vault/tests/test_search_index.py` — 18 stdlib-only unit tests covering tier classification, chunking, FTS round-trip, tool contracts (no-index / missing args / fallback), and rerank ordering + boosts.
- **Dependency guard**: `tests/validate-scripts.py` now recognizes the PRD §26.2 approved deps (`mcp`, `fastembed`, `sqlite_vec`, `tars_vault`) alongside stdlib.

### Migration

Existing v3.0 vaults migrate via the user-executed runbook at [docs/MIGRATION-v3.0-to-v3.1.md](docs/MIGRATION-v3.0-to-v3.1.md) — snapshot → integrations-v2 → wikilink cleanup → search-index build → git-hooks install → `/welcome` refresh → `/lint` pass → cron registration → verification. Schema additions are backward-compatible; no v3.0 frontmatter shapes break.

### Release runbook

User-executed release steps are documented at [docs/RELEASE-v3.1.0.md](docs/RELEASE-v3.1.0.md). Mobile access via Claude Remote Control is documented at [docs/MOBILE-USAGE.md](docs/MOBILE-USAGE.md).

## v3.0.0 (2026-03-22)

**TARS 3.0: Obsidian-native rebuild — complete architecture redesign**

### Architecture
- **Obsidian-native**: All vault mutations via `obsidian-cli` (create, append, property:set, search). No direct filesystem writes for content.
- **Bases replace indexes**: 15 live `.base` query files replace all hand-maintained `_index.md` files. Zero drift, always accurate.
- **Schema-validated frontmatter**: All TARS notes use `tars-` prefixed properties validated against `_system/schemas.yaml` (14 entity types).
- **Vault-first runtime**: The deployed Obsidian vault is the runtime source of truth. The repository is the framework source and packaging surface.
- **Tag-driven filterability**: Hierarchical `tars/` tags on all managed notes for reliable search and base filtering.

### New capabilities (10 real-world issues addressed)
- **Transcript format detection + mandatory calendar check** (Issue 1): Meeting processing always queries calendar even when transcript provides a date. Multiple-choice confirmation for ambiguous matches.
- **Task review UX** (Issue 2): All task extraction presents numbered lists with selection syntax (`all`, `1,3,7`, `all except 4`, `none`). No silent task creation.
- **Ask don't assume** (Issue 3): Core principle — multiple-choice questions, max 3-4 per round, always check vault first, always include skip option.
- **File organization + companion files** (Issue 4): Non-markdown files get companion `.md` notes with metadata. Maintenance auto-organizes user-added files by date.
- **Quick capture / screenshot processing** (Issue 5): Multimodal image analysis with calendar context inference for screenshots captured during meetings.
- **Transcript-linked fallback lookup** (Issue 6): Transcripts archived with bidirectional journal links. Answer skill falls back to raw transcript when summaries lack detail.
- **Check before writing** (Issue 7): Knowledge inventory before all extraction — NEW/UPDATE/REDUNDANT/CONTRADICTS classification prevents stale overwrites.
- **Negative statement capture + cleanup** (Issue 8): Sentiment detection with inline flags. Periodic maintenance review with numbered removal. `flagged-content.base` view.
- **Self-evaluation backlog** (Issue 9): Auto-detected framework errors logged to `_system/backlog/issues/` (deduplicated). User ideas captured separately. `backlog.base` view.
- **Scheduled execution** (Issue 10): CronCreate for daily briefings, weekly briefings, and maintenance. Cron self-check at every session start.

### Added
- `_system/` directory: config, integrations, alias-registry, taxonomy, kpis, schedule, guardrails.yaml, maturity.yaml, housekeeping-state.yaml, schemas.yaml, changelog/, backlog/
- `_views/` directory: 15 `.base` files (all-people, all-initiatives, all-decisions, all-products, all-vendors, all-competitors, recent-journal, active-tasks, overdue-tasks, stale-memory, inbox-pending, all-documents, all-transcripts, flagged-content, backlog)
- `templates/` directory: 15 Obsidian templates (person, vendor, competitor, product, initiative, decision, org-context, meeting-journal, daily-briefing, weekly-briefing, wisdom-journal, companion, transcript, issue, idea)
- `commands/` thin wrappers retained for explicit slash-command invocation in the v3 framework
- `scripts/validate-schema.py`: Schema validation against schemas.yaml with PyYAML fallback
- `scripts/scan-flagged.py`: Negative sentiment scanner for people notes
- `scripts/health-check.py`: Rewritten for v3 schema, broken links, alias consistency, staleness
- `scripts/scan-secrets.py`: Rewritten for v3 guardrails.yaml format
- `scripts/sync.py`: Rewritten for v3 meeting journals, memory freshness, task drift
- `scripts/archive.py`: Rewritten with guardrails (never archive backlinked or task-referenced notes)
- `tests/smoke-tests.py`: 13-point verification suite
- `tests/fixtures/`: 6 schema validation fixtures (valid + invalid examples)
- `CLAUDE.md`: Vault-level agent configuration for v3
- Architectural decisions and deviation notes recorded during the rebuild
- `.claude/skills/`: obsidian-cli, obsidian-bases, obsidian-markdown, json-canvas, defuddle skill references

### Changed
- **All 12 skills rewritten** for Obsidian-native operation (core, welcome, learn, tasks, meeting, briefing, answer, maintain, think, communicate, initiative, create)
- **Name resolution**: 3-layer system (Obsidian aliases → context-aware registry → search fallback) replaces flat `replacements.md`
- **Inbox processing**: Simplified to pending/processed (no processing/failed intermediate states)
- **Think modes**: All 5 modes (A-E) check existing vault knowledge before analyzing
- **Communication drafting**: Loads stakeholder memory, checks for flagged negative content
- **Documentation set refreshed**: README, GETTING-STARTED, ARCHITECTURE, BUILD, CATALOG, and contribution docs now describe the actual v3 runtime model and release flow
- **Repository cleanup**: Removed duplicate legacy `.claude-plugin` payload trees, obsolete helper scripts, and stale release artifacts that were not part of the active v3 plugin

### Retired from the active runtime architecture
- `_index.md` files: Replaced by `.base` live queries
- `reference/` as runtime control plane: Replaced by `_system/`
- Manual index rebuilding as the primary query model: Replaced by live views and schema-driven note structure

## v2.2.0 (2026-02-19)

**Framework audit: efficiency, consistency, and automated validation**

### Added
- **Documentation consistency validator** (`tests/validate-docs.py`): 5-check validator catching stale skill references, provider-name leaks, count drift, archival tier terminology, and empty changelogs. Prevents semantic drift between docs and implementation.
- **CI integration for doc validation**: `validate-docs.py` added to `.github/workflows/validate.yml` with change detection for documentation files (ARCHITECTURE.md, README.md, GETTING-STARTED.md, CHANGELOG.md, CATALOG.md, reference/**, skills/**, commands/**, scripts/**).
- **Universal constraints in core skill**: 9 cross-cutting rules (date resolution, wikilink mandate, name normalization, task verification, integration constraints, index-first pattern, no-deletion, journal persistence, frontmatter compliance) now defined once in core and referenced by all skills.
- **Maintain skill developer reference**: Internal procedures for health-check.py, rebuild-indexes.py, and archive.py documented in ARCHITECTURE.md for maintainers without inflating the active skill.
- **CONTRIBUTING.md**: Consistency checklist for skill/script/protocol/integration/version changes, plus local validator run instructions.
- **Maintenance breadcrumbs**: HTML comments in core and maintain skills pointing to validate-docs.py and CONTRIBUTING.md.
- **Help metadata**: Added `purpose`, `use_cases`, `scope` help metadata to all 8 skills that were missing it (core, learn, think, maintain, welcome, initiative, create, communicate).
- **Name resolution protocol** (core skill): Cascading resolution for ambiguous and unknown names. Uses calendar attendees, transcript context, and memory files before asking the user. Batch clarification minimizes interruptions.
- **Health mode auto-fix** (maintain skill): Deterministic issues (decision file renames, index orphan removal, index rebuilds) are now auto-fixed instead of only suggested. Non-deterministic issues still presented to user.
- **Inbox name pre-resolution** (maintain skill): Names across all pending transcript files are resolved in a single pass before sub-agents spawn, ensuring consistency and preventing redundant user queries.

### Changed
- **Skill efficiency (~400 lines reduced)**: Deduplicated shared protocols across skills by referencing core definitions. Consolidated 3 inbox sub-agent templates into shared pipeline + type-specific processing. Streamlined maintain skill health/rebuild modes to script invocation with fallback references. Trimmed per-skill absolute constraints to unique-only (universal constraints in core).
- **workflows.md**: Rewrote all 8 workflow entries to use v2.2 skill names and reflect current pipeline architecture (was using v1.x names like `process-meeting`, `extract-tasks`).
- **ARCHITECTURE.md**: Fixed sub-agent descriptions to match actual implementations, corrected token baseline count, fixed script count (10→11), removed duplicate lines in workspace structure, corrected runner.sh reference.
- **README.md**: Fixed archival tier names from "active/warm/cool/archived" to canonical "durable/seasonal/transient/ephemeral".
- **welcome skill**: Updated command references (`/daily-briefing`→`/briefing`, `/process-meeting`→`/meeting`), replaced nonexistent `create-shortcut` skill reference with Cowork shortcut mechanism.
- **shortcuts.md**: Replaced `create-shortcut` skill reference with manual setup instructions.
- **answer skill**: Replaced hardcoded provider names (`eventlink`, `remindctl`) with generic language per provider-agnostic principle.
- **CHANGELOG.md**: Fixed wrong file path for getting-started guide (was `reference/getting-started.md`, corrected to `GETTING-STARTED.md`).
- **ARCHITECTURE.md help schema**: Aligned documented schema with actual implementation (`purpose`, `use_cases`, `scope`).
- **Script count**: 10→11 (added update-reference.py in v2.1.0, corrected in docs).
- **Meeting skill pipeline reorder**: Calendar lookup now runs before speaker name resolution so attendee lists inform the resolution cascade.
- **Meeting skill name resolution**: Enhanced from assumption-based inference to the core name resolution protocol with user clarification for remaining ambiguities.
- **Learn skill**: Both memory and wisdom modes now check for name ambiguity before processing. Unresolved names block extraction to prevent incorrect memory entries.
- **Health mode output**: Split into "Auto-fixed" and "Manual action required" sections. Deterministic fixes executed automatically, ambiguous issues presented to user.
- **Health mode constraint**: Expanded auto-fix scope from "only replacements" to include deterministic file renames, index orphan removal, and index rebuilds.
- **Version**: 2.1.0 → 2.2.0

---

## v2.1.0 (2026-02-19)

> Bumped from v2.0.1


## v2.0.1 (2026-02-10)

> Bumped from v2.0.0

### Added
- **Task creation verification**: All task creation paths (meeting, inbox, tasks skills) now include mandatory post-creation verification via `list_reminders`. Prevents silent failures where tasks are reported as created but never appear in the task manager.
- **Reference file update mechanism**: New `scripts/update-reference.py` surgically updates workspace reference files when the plugin is updated, preserving user customizations (name replacements, KPI definitions, schedule items). Three merge strategies: `full_replace`, `section_merge`, `additive_merge`.
- **Maintain update mode**: New `/maintain update` mode checks workspace reference files against the installed plugin version and applies updates with user confirmation.
- **Plugin version tracking**: `scaffold.sh` now writes `plugin_version` to `.housekeeping-state.yaml` at install time. Used by update-reference.py to detect stale workspaces.
- **Wikilink validation**: Inbox sub-agent templates now read memory indexes before creating wikilinks. Unverified names are flagged and added to replacements.md with placeholders.

### Changed
- **Inbox sub-agent templates**: Expanded from thin bullet-point templates to structured 6-step pipelines with memory index reads, speaker resolution, calendar lookup, structured report sections, wikilink validation, and task verification.
- **Inbox result collection**: Three-way handling (ok/partial/error) replaces binary ok/error. Partial status captures items where the journal was saved but task creation or memory extraction had issues.
- **Inbox file-move ordering**: Files are now moved from pending to processing as a batch before any sub-agents are spawned (prevents race conditions).
- **Task skill Step 6**: Now requires checking each `create_reminder` tool response before counting a task as created. New Step 7 calls `list_reminders` for post-creation verification.
- **Meeting skill Sub-agent A**: Task extraction template now includes response checking and `list_reminders` verification with `creation_unverified` tracking.
- **Integrations.md Tasks section**: Added verification requirement constraint.
- **Script count**: 9 → 10 (added update-reference.py)

---

All notable changes to the TARS framework are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). Version numbers follow [Semantic Versioning](https://semver.org/).

---

## v2.0.0 (2026-02-08)

**Architecture overhaul: skill consolidation, integration abstraction, automated housekeeping, and enterprise distribution**

### Breaking changes
- Consolidated 28 skills into 12 (7 background skills merged into single core skill, workflow skills merged by domain, 2 composite skills absorbed)
- Reduced 23 commands to 11 thin wrappers matching consolidated skills
- Renamed `/setup` to `/welcome` with progressive onboarding
- Replaced pipe-delimited index tables with YAML format
- Replaced hardcoded Eventlink/remindctl references with provider-agnostic integration registry
- Skill help metadata changed from flat string to structured object (purpose, use_cases, invoke_examples, common_questions, related_skills)

### Added
- **Skill consolidation**: core (7→1), meeting (2→1), tasks (2→1), learn (2→1), think (5→1), initiative (2→1), maintain (3→1)
- **9 automation scripts**: health-check.py, rebuild-indexes.py, scaffold.sh, sync.py, archive.py, verify-integrations.py, scan-secrets.py, bump-version.py (all Python stdlib only)
- **Provider-agnostic integration registry**: category-based design supporting http-api, cli, and mcp provider types
- **Progressive welcome flow**: 3-phase onboarding (instant setup, first win, background learning) replacing 4-round interrogation
- **YAML-based indexes**: improved editability and parseability over pipe tables
- **4-tier content archival**: durable/seasonal/transient/ephemeral with automatic expiry
- **Batch processing inbox**: inbox/pending → processing → completed/failed with isolated sub-agent processing
- **Sub-agent parallelization**: meeting (task extraction || memory extraction), think deep mode (validation || executive council), briefing (calendar || tasks || memory)
- **Automated daily housekeeping**: session-start check triggers maintenance scripts if not run today
- **Inline help metadata**: structured help objects in all skill YAML frontmatter
- **Sensitive data guardrails**: script-based scanning (scan-secrets.py) with configurable patterns in reference/guardrails.yaml
- **CI/CD pipeline**: GitHub Actions for PR validation (validate.yml) and auto-release (release.yml)
- **Test suite**: 6 validation scripts + test runner with dynamic test selection
- **CATALOG.md**: leadership adoption document for enterprise distribution
- **Maturity model**: reference/maturity.yaml tracking onboarding progress
- **Getting started guide**: GETTING-STARTED.md for new users
- **Workflow patterns**: reference/workflows.md documenting multi-skill patterns
- **Communication rules go global**: BLUF, anti-sycophancy, banned phrases now apply to ALL TARS outputs
- **AskUserQuestion integration**: structured UI clarification in Cowork mode
- **TodoWrite progress tracking**: real-time visibility during long-running operations
- **Context management directive**: intermediate results offloaded to files
- **Proactive learning triggers**: TARS suggests memory extraction when user corrects facts or shares context
- **Help routing**: core skill handles "how do I", "what can you do" queries via inline help metadata
- **Cowork shortcut support**: scheduled daily housekeeping via create-shortcut skill

### Changed
- Session baseline: ~115 tokens → ~48 tokens (12 skills × ~4 tokens vs 28 × ~4)
- Version: 1.5.0 → 2.0.0
- Plugin name: lowercase "tars" in manifest
- Skill descriptions: optimized with trigger keywords for better auto-routing accuracy
- Index format: pipe-delimited markdown tables → YAML entries
- Welcome flow: 4-round interrogation (10+ min) → 2 questions + auto-discovery (5 min)
- Integration references: hardcoded tool names → category-based ("query calendar integration")

### Removed
- 7 individual background skill directories (identity, communication, memory-management, task-management, decision-frameworks, clarification, routing) — merged into core
- 2 composite skill directories (meeting-processor, deep-analysis) — absorbed into meeting and think
- 8 individual workflow skill directories (process-meeting, extract-tasks, manage-tasks, extract-memory, extract-wisdom, housekeeping, rebuild-index, update, setup, quick-answer, strategic-analysis, executive-council, validation-council, discovery-mode, performance-report, create-artifact) — consolidated into domain skills
- 12 command files — consolidated to match 11 merged skills

---

## v1.5.0 (2026-02-07)

**Structural compliance rebuild: spec-compliant Claude Cowork plugin**

### Breaking changes
- **Removed**: `agents/` directory -- converted to composite skills
- **Removed**: `data/` directory tree -- workspace template created at runtime by `/setup`
- **Removed**: `reference/executive-council-manifesto.md` -- duplicate of `skills/executive-council/manifesto.md`
- **Removed**: `reference/migrate-tasks.sh` -- one-time v1.3 migration utility
- **Removed**: `.claude/settings.local.json` -- malformed permissions, plugins should not ship local settings
- **Changed**: Plugin name `"tars"` → `"TARS"` in plugin.json

### Added
- **2 composite skills**: `skills/meeting-processor/SKILL.md` and `skills/deep-analysis/SKILL.md` (converted from agents)
- **2 new commands**: `commands/meeting-processor.md` and `commands/deep-analysis.md`
- **YAML frontmatter** on all 23 commands (`description` + optional `argument-hint`)
- **`reference/schedule.md`**: Template for recurring and one-time scheduled items (heartbeat)
- **Heartbeat integration**: `/update` checks schedule (Step 1.5), `/daily-briefing` surfaces due items, `/setup` creates schedule template
- **Source attribution**: Confidence tiering added to `quick-answer`, `strategic-analysis`, `executive-council`, `validation-council`
- **`author` field** in plugin.json: `{"name": "Ajay John"}`
- **Filesystem MCP server** configured in `.mcp.json`
- **Routing entries** for composite skills (deep-analysis, meeting-processor)
- **Expanded plugin.json**: Added `author.url`, `repository`, `homepage`, `bugs`, `keywords`, `contributors` fields
- **`NOTICE` file**: Apache 2.0 attribution file at plugin root
- **Copyright headers**: Added to ARCHITECTURE.md and README.md
- **`.claude-plugin/marketplace.json`**: Marketplace catalog entry for distribution

### Changed
- Plugin version: `1.4.0` → `1.5.0`
- 3 thick commands (setup, update, rebuild-index) thinned to standard skill redirects
- Counts: 26 → 28 skills, 21 → 23 commands, 4 → 5 reference templates
- Version numbering corrected: what was previously labeled v2.0.0 is now v1.5.0 (the current state is a structural compliance rebuild, not the full architecture overhaul)

### Fixed
- All `data/` and `data/data/` path prefixes in `reference/taxonomy.md`
- Stale `protocols/meeting-processor.md` reference in `skills/extract-wisdom/SKILL.md`
- Stale `data/journal/` paths in `skills/process-meeting/meeting-context-query.md`
- Routing signal table now references `skills/deep-analysis/` instead of inline chain

---

## v1.4.0 (2026-02-06)

**Major architecture migration: protocols → native Claude plugin skills**

### Breaking changes
- **Removed**: protocols/ directory - all logic now in skills/
- **Removed**: install.sh - replaced by /setup skill
- **Removed**: build-plugins.sh and modular plugin system
- **Removed**: .claude/rules/ and .claude/commands/ - framework reads from plugin directly
- **Removed**: .agent/ Antigravity compatibility layer
- **Path change**: `data/` prefix removed from all workspace paths (data/memory/ → memory/)

### New architecture
- **26 skills** (7 background + 19 workflow): All with YAML frontmatter, user-invocable flag
- **21 commands**: Thin wrappers passing modes to skills
- **2 sub-agents**: meeting-processor, deep-analysis (orchestrate skill chains)
- **3-level loading**: L1 metadata (~105 tokens), L2 full skill, L3 supporting files
- **Provider-based integrations**: reference/integrations.md supports eventlink|mcp|none

### Token efficiency
- Session baseline: ~4,000 tokens saved (was ~4,200 for all behavioral skills, now ~105 for metadata only)
- L2 (full skill) loads on-demand, same cost as v1.3 protocol loading
- Net result: Significantly improved token efficiency with no functionality loss

### New skills (user-invocable workflow skills)
- process-meeting, extract-tasks, manage-tasks, extract-memory, extract-wisdom
- briefing (daily/weekly modes), communicate, strategic-analysis
- executive-council, validation-council, discovery-mode
- create-artifact, performance-report, initiative (planning/status modes)
- quick-answer, housekeeping, rebuild-index, setup, update

### Migration from v1.3.0
- Protocols merged into skills, behavioral constraints preserved
- All path references updated (removed data/ prefix)
- setup skill replaces install.sh + bootstrap command
- Signal table in routing skill now references skills/ not protocols/
- Reference files moved from data/reference/ to reference/ at plugin root

---

## [1.3.0] — 2026-02-04

### Added
- `/housekeeping` command and `protocols/housekeeping.md` for workspace maintenance and cleanup
- MCP discovery section in routing skill for detecting available integrations
- Decision status values in taxonomy (proposed, decided, implemented, superseded, rejected)
- Product specification frontmatter template in taxonomy
- Core concepts section in taxonomy (durability test, accountability test, index-first pattern)
- Auto-add unknown names to replacements.md with placeholder during meeting processing
- Calendar title priority hierarchy for meeting filename generation
- Contexts/products indexing in rebuild-index command
- Decision file naming validation in rebuild-index command
- MCP detection patterns and fallback hierarchy in CONNECTORS.md
- Migration scripts: `scripts/migrate-decisions.sh` and `scripts/add-product-frontmatter.sh`
- Bootstrap now creates `contexts/products/_index.md` and `contexts/artifacts/_index.md`
- Plugin decomposition: 6 modular plugins (core, memory, productivity, journal, analysis, comms)
- Plugin manifest: `plugins/manifest.json` with dependencies and presets
- `--plugins` flag for install.sh to select which plugins to install
- `.tars-plugins` marker file to track installed plugins
- `build-plugins.sh` script to package each plugin as a versioned zip file

### Changed
- **BREAKING**: Replaced `--no-antigravity` flag with `--platform <name>` flag in install.sh. Default is now Claude Code only (no `.agent/` generation). Use `--platform antigravity` to enable Antigravity shims. This prepares for future platform support.
- **BREAKING**: Consolidated user data under `data/` folder. Old paths (`memory/`, `journal/`, `contexts/`, `reference/`) are now `data/memory/`, `data/journal/`, `data/contexts/`, `data/reference/`. Existing workspaces need manual migration.
- Deprecated `tasks/` folder removed from scaffolding (tasks migrated to Apple Reminders via remindctl)
- Meeting processor Step 0.5 upgraded from RECOMMENDED to MANDATORY WHEN AVAILABLE
- Meeting frontmatter now includes `calendar_title`, `organizer`, and `source` fields
- Merged `reference/mcp-guide.md` into `reference/integrations.md` (token efficiency)
- Simplified 18 command files to routing stubs (reduced ~600 tokens per session)
- Routing table now lives only in `.claude/rules/07-routing.md`, removed from CLAUDE.md
- CLAUDE.md now references 21 commands and 17 protocols
- Install.sh now copies routing skill as `07-routing.md`
- Reference files reduced from 6 to 5

### Removed
- `reference/mcp-guide.md` (content merged into integrations.md)
- Routing table duplication in generated CLAUDE.md

---

## [1.2.0] — 2026-02-02

### Changed
- Antigravity workflows now contain inlined command content instead of redirect shims
- All 20 commands generate workflows automatically (was 13 manually-configured)
- `.agent/` generation loop auto-discovers commands (zero maintenance for new commands)

### Removed
- `.agent/skills/` directory and all 7 skill shims (consolidated into workflows)
- `generate_workflow()` and `generate_skill()` functions from install.sh
- Manual workflow/skill mapping in install.sh

---

## [1.1.0] — 2026-02-02

### Added
- `ARCHITECTURE.md` — comprehensive framework documentation (architecture, design decisions, maintenance guide)
- `CHANGELOG.md` — version history tracking
- `AGENTS.md` symlink — Antigravity reads `AGENTS.md` instead of `CLAUDE.md`; symlink ensures both clients share the same root config

### Fixed
- Antigravity workflow shims now include YAML `description` frontmatter (previously started with `# Title`, which Antigravity silently ignored)
- Antigravity skill shims now use folder/SKILL.md structure (`.agent/skills/<name>/SKILL.md`) instead of flat files (`.agent/skills/<name>.md`)
- Antigravity rules shim now concatenates full content of all 6 rule files instead of containing redirect pointers that Antigravity doesn't follow

---

## [1.0.0] — Initial release

### Added
- 7 skills: routing, identity, communication, memory management, task management, decision frameworks, clarification
- 20 commands: bootstrap, update, process-meeting, extract-memory, extract-tasks, extract-wisdom, daily-briefing, weekly-briefing, initiative-status, manage-tasks, quick-answer, communicate, strategic-analysis, executive-council, validation-council, discovery-mode, initiative-planning, create-artifact, performance-report, rebuild-index
- 16 protocols: meeting-processor, meeting-context, briefing-protocol, extract-wisdom, extract-memory, extract-tasks, initiative-planning, artifact-generation, search-protocol, stakeholder-comms, strategic-analysis, performance-report, executive-council, validation-council, text-refinement, discovery-mode
- 5 reference files: executive-council-manifesto, mcp-guide, taxonomy, replacements, kpis
- 8 connector categories with `~~placeholder` abstraction
- `install.sh` workspace expander for cowork and Antigravity compatibility
- `CLAUDE.md` generation with user block preservation, intelligent router, file map, cowork protocol
- `.agent/` shim layer for Antigravity (rules, workflows, skills)
- Plugin manifest (`plugin.json`) with skills, commands, and connectors
