# Migrating a TARS v3.0 vault to v3.1

This guide is for users who already have a TARS v3.0 vault in production and want to pick up the v3.1 capabilities (`tars-vault` MCP server, hooks, hybrid retrieval, meeting nuance pass, `/lint`, `/create` office orchestration, Integration Registry 2.0, telemetry).

The migration is additive. Existing notes, frontmatter, and views keep working. No v3.0 schema shape breaks in v3.1.

> **Safety first.** Migration mutates the vault. Run every step on a clone or with `--dry-run` before running `--apply`. Confirm a fresh git commit inside the vault before starting. The migration scripts refuse to run when `git status --porcelain` inside the vault is non-empty (exit code 3).

## Prerequisites

- Framework upgraded to `v3.1.0` (plugin installed / checkout at the `v3.1.0` tag).
- `python3 -m pip install -r requirements.txt` inside the framework repo (installs the pinned `mcp`, `fastembed`, `sqlite-vec` deps — nothing else).
- `TARS_VAULT_PATH` environment variable points at the vault.
- Vault is a git working tree with a clean status (`git -C "$TARS_VAULT_PATH" status --porcelain` returns empty).
- Anthropic's first-party `pptx` / `docx` / `xlsx` / `pdf` skills available in your Claude Code install (auto-bundled on most installs; `/welcome` will probe and record the result).

## Migration runbook (user-executed)

These steps mirror PRD §10 Phase 9. Run them interactively, reviewing each step before moving on.

### 1. Back up the vault

A dedicated git tag is the simplest insurance:

```bash
cd "$TARS_VAULT_PATH"
git add -A && git commit -m "pre-v3.1 snapshot" || true
git tag pre-v3.1.0 HEAD
```

### 2. Migrate `_system/integrations.md` to the v3.1 capability-preference format

```bash
python3 scripts/migrate-integrations-v2.py --vault "$TARS_VAULT_PATH" --dry-run
# review the proposed v3.1 frontmatter; if it looks right, apply:
python3 scripts/migrate-integrations-v2.py --vault "$TARS_VAULT_PATH" --apply
```

The script writes `<file>.pre-v3.1-backup` before modifying. It is idempotent — rerunning is a no-op.

### 3. Fix pre-existing wikilink artifacts (quadruple brackets, etc.)

```bash
python3 scripts/fix-wikilinks.py --vault "$TARS_VAULT_PATH" --dry-run
# review. If the proposals look correct:
python3 scripts/fix-wikilinks.py --vault "$TARS_VAULT_PATH" --apply
```

The script targets the observed artifact patterns (quadruple brackets in alias registry, stray whitespace in wikilinks, plain-text name → wikilink for known entities) with per-instance confirmation in `--apply` mode.

### 4. Build the hybrid search index

```bash
python3 scripts/build-search-index.py --vault "$TARS_VAULT_PATH"
```

This run:

- creates `_system/search.db` (SQLite with FTS5 + `sqlite-vec`)
- creates `_system/search-index-state.json` (incremental SHA-256 state)
- creates `_system/embedding-cache/` (gitignored)
- downloads the FastEmbed model `BAAI/bge-small-en-v1.5` (~80 MB) on first run
- indexes memory, journal, `archive/transcripts/`, and `contexts/`
- bounded to 10 minutes (checkpoint + resume supported on rerun)

On a vault with ~120 journal entries + ~50 transcripts, expect 5–10 minutes end-to-end.

### 5. Install git hooks (authorship enforcement)

From the framework repo (NOT the vault):

```bash
cd /path/to/framework-repo
bash scripts/githooks/install-githooks.sh
```

Adds a `prepare-commit-msg` and `pre-push` hook to `.git/hooks/` that reject any commit or push carrying Claude attribution patterns.

### 6. Re-run `/welcome` to refresh state

In Claude Code, inside the vault, run `/welcome`. This:

- probes for Anthropic's first-party rendering skills and stores the result in `_system/config.md.tars-anthropic-skills`
- optionally scaffolds `contexts/brand/<brand-name>-brand-guidelines.md` from `templates/brand-guidelines.md` and caches the choice as `tars-active-brand`
- verifies hook installation and `tars-vault` MCP reachability

### 7. Run `/lint` and apply proposed fixes

`/lint` is new in v3.1 and produces a prioritized punch-list. On a v3.0-to-v3.1 migration, expect to see:

- decision / initiative / people count drift against `_system/maturity.yaml` (`/lint` proposes an auto-fix using `scripts/sync.py --hydration`)
- loose journal files at the root of `journal/` (propose move into `YYYY-MM/` subfolders)
- wikilink artifacts in `_system/alias-registry.md` that survived step 3
- tasks with no `tars-age-days` / `tars-escalation-level` computed (auto-fixable)

Review each finding; apply via the numbered selection syntax.

### 8. Register nightly cron jobs

In Claude Code, run:

```text
/maintain register-crons
```

Registers `CronCreate` entries (in Claude Code) for:

- daily briefing — `30 7 * * *`
- weekly briefing — `0 8 * * 1`
- maintenance — `0 17 * * 5`
- lint — `0 2 * * *`

Adjust times in `_system/config.md` before running if the defaults do not match your schedule.

### 9. Verify

Run these in a fresh Claude Code session:

- `/briefing` — confirms hydration counts come from live vault state, no "Level N" artifact.
- `/meeting` on a ≥60 KB transcript — confirms chunked archival works and the nuance pass runs.
- `/answer "what did [person] say about [topic]"` — confirms hybrid retrieval returns hits from journal or transcripts.
- `/create` with a PowerPoint request — confirms the capability probe + content-first flow + delegation to Anthropic's `pptx` skill.
- Check `_system/telemetry/YYYY-MM-DD.jsonl` exists with `skill_invoked` and `vault_write` events from the above runs.

## Rollback

Every migration script writes a `.pre-v3.1-backup` for every file it touched. To roll the vault back:

```bash
cd "$TARS_VAULT_PATH"
git reset --hard pre-v3.1.0
```

Then reinstall the v3.0 framework version in Claude Code.

Hooks and the `tars-vault` MCP server live in the framework repo, not the vault, so disabling them is independent: remove the `tars-vault` entry from `.mcp.json` and the skills will fall back to `obsidian-cli`-direct behavior (reads only — writes should still route through the MCP server).

## Duration

Expect 45–90 minutes end-to-end for the migration of a vault in the 3× scale envelope (up to 600 journal entries, 360 people, 150 decisions). The longest step is typically `build-search-index.py` on first run.

## Known issues

- Pre-existing validator warnings in `tests/validate-frontmatter.py` (2 errors + 36 warnings in the framework repo) do not affect the vault — they are reference-repo baseline noise being tracked separately.
- If `/welcome`'s Anthropic-skills probe reads an empty list, confirm your Claude Code install has the skill registry surfaced in `<system-reminder>` blocks. The probe is passive and does not introspect `~/.claude/skills/`.

## Related docs

- [docs/RELEASE-v3.1.0.md](RELEASE-v3.1.0.md) — the user-run build, tag, and publish runbook (after migration validates).
- [docs/MOBILE-USAGE.md](MOBILE-USAGE.md) — using TARS from iOS / Android via Claude Remote Control.
- [ARCHITECTURE.md](../ARCHITECTURE.md) — full v3.1 system model.
