# TARS v3.1.0 release runbook (user-executed)

This document is the step-by-step runbook the user follows to cut the `v3.1.0` release once the `tars-3.1.0-dev` branch is green and the deployed-vault migration (see [MIGRATION-v3.0-to-v3.1.md](MIGRATION-v3.0-to-v3.1.md)) has been verified.

Every step is executed manually by the user in a shell inside `/Users/ajayjohn/Sync/Applications/Library/tars/`. The executing agent does NOT run release steps.

## Authorship rules (non-negotiable)

All commits, tags, CHANGELOG entries, and release notes must be attributed to the user's GitHub identity. Zero Claude attribution — no `Co-Authored-By: Claude`, no `🤖`, no "Generated with Claude Code".

The `prepare-commit-msg` and `pre-push` hooks in `scripts/githooks/` reject any commit or push that carries those patterns. Install them if not already installed:

```bash
bash scripts/githooks/install-githooks.sh
```

Confirm git identity before the release:

```bash
git config user.name     # expect: Ajay John
git config user.email    # expect: 1575879+ajayjohn@users.noreply.github.com
```

Abort if either is wrong.

## Pre-release verification

From the repo root on `tars-3.1.0-dev`:

```bash
git checkout tars-3.1.0-dev
git status                                # must be clean
python3 tests/validate-structure.py
python3 tests/validate-routing.py
python3 tests/validate-templates.py
python3 tests/validate-frontmatter.py
python3 tests/validate-references.py
python3 tests/validate-scripts.py
python3 tests/validate-docs.py
python3 tests/smoke-tests.py
python3 tests/validate-phase1-skeleton.py
python3 tests/validate-phase5-6.py
python3 mcp/tars-vault/tests/test_search_index.py
```

All must return exit 0 (`STATUS: PASS`). Pre-existing baseline warnings in `validate-frontmatter.py` and `validate-templates.py` that are documented in `docs/HANDOFF-NOTES.md` are acceptable for the rc1 cut but should be driven to green before the final `v3.1.0` tag.

## Retroactive tag backfill (one-time hygiene)

Before cutting v3.1.0, backfill the missing v2.2.0 and v3.0.0 tags so release history is honest:

```bash
V220_SHA=$(git log --format=%H --grep="v2.2.0" --all | head -1)
git tag -a v2.2.0 "$V220_SHA" \
  -m "TARS v2.2.0 — framework audit, efficiency, and automated validation"

git tag -a v3.0.0 5624ea8 \
  -m "TARS v3.0.0 — Obsidian-native rebuild with schema-validated architecture"
```

Delete the duplicate non-prefixed `2.0.0` tag if it is still in place locally:

```bash
git tag -d 2.0.0 2>/dev/null || true
```

Do NOT push these tags yet — push happens after the v3.1.0 tag is cut.

## Version bump

```bash
python3 scripts/bump-version.py --target 3.1.0
```

This updates `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Review the diff.

## CHANGELOG finalization

Edit `CHANGELOG.md`: rename the `## v3.1.0-dev — WIP` heading to `## v3.1.0 (YYYY-MM-DD)` using the release date. Ensure the Phase 1a through Phase 8 entries are present. Sections to double-check:

- Architecture (hooks, MCP wrappers, integration registry, retrieval)
- New capabilities (office productivity, meeting nuance, auto-wikilink, `/lint`, automation matrix, archival policy)
- Added (files, skills, scripts, views, templates)
- Changed (skills, integrations, retrieval, maturity sync)
- Retired (legacy rebuild docs, scan-flagged.py, individual briefing templates, individual backlog templates)
- Migration pointer — link to `docs/MIGRATION-v3.0-to-v3.1.md`

No Claude attribution in the body.

## Commit finalization

```bash
git add -A
git status
git commit -m "feat: TARS v3.1.0 — hooks, MCP wrappers, hybrid retrieval, office productivity"
```

The pre-commit hook will reject the commit if any Claude-attribution pattern is present.

## Build packaged plugin

```bash
bash build-plugin.sh
```

This packages the framework into `tars-cowork-plugin/`. Inspect the output for any stale legacy-rebuild-doc inclusion or office-library imports — both should be absent. The final plugin size should be smaller than the v3.0.0 cut even with the new MCP server, because of the Phase 7 consolidation.

## Tag the release

```bash
git tag -a v3.1.0 -m "TARS v3.1.0 — harden, simplify, extend"
```

If GPG signing is configured (`git config --get commit.gpgsign` returns `true`), the tag is signed automatically. Do NOT pass `--no-gpg-sign`.

## Merge to `main`

```bash
git checkout main
git merge --no-ff tars-3.1.0-dev -m "Merge branch 'tars-3.1.0-dev' — TARS v3.1.0"
```

This is a non-fast-forward merge so the branch history stays visible.

## Push to remote

Only after all of the above succeeds locally:

```bash
git push origin main
git push origin v3.1.0
git push origin v2.2.0      # backfilled
git push origin v3.0.0      # backfilled
```

Do NOT force-push to `main`. Do NOT push tags that were not explicitly created in this runbook.

## Optional: GitHub release notes

```bash
gh release create v3.1.0 \
  --title "TARS v3.1.0 — harden, simplify, extend" \
  --notes-file CHANGELOG.md
```

(Adjust the notes body to only include the v3.1.0 section.)

## Clean up branches

Delete the dev branch locally and on the remote once the tag is in place:

```bash
git branch -d tars-3.1.0-dev
git push origin --delete tars-3.1.0-dev
```

The legacy `tars-3.0` branch can also be deleted per PRD §24.13 if not already done.

## Final state verification

```bash
git log --oneline --decorate main -5
git tag --list | sort
.claude-plugin/plugin.json                # version: 3.1.0
python3 tests/validate-structure.py       # PASS
```

All checks green. Release done.

## Post-release checklist

- Watch the Claude Code marketplace for the new version to propagate.
- Bump `tars-3.1.0-dev` handoff notes to "RELEASED" status in `docs/HANDOFF-NOTES.md`.
- Start a `tars-3.2.0-dev` branch when picking up v3.2 work.

## Rollback (if something goes wrong after push)

If a critical regression is discovered after push:

```bash
git tag -d v3.1.0
git push origin :refs/tags/v3.1.0
git revert <merge-sha>
git push origin main
```

Then issue `v3.1.1` with the fix following the same runbook.

## Duration

Expect 60–90 minutes for a clean release (pre-release verification + bump + CHANGELOG + commit + tag + merge + push + marketplace watch). The bulk of the time is reviewing the CHANGELOG and diff, not the mechanical steps.
