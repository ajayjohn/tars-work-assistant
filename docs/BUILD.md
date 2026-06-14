# TARS Build and Release

This document describes the supported packaging path for the current framework.

## Build model

TARS is maintained from the repository root and packaged into a distributable plugin directory. The active packaging entrypoint is [build-plugin.sh](build-plugin.sh).

The build model is:
- repository source is the maintainer-facing truth
- `.claude-plugin/plugin.json` is the metadata source of truth
- `build-plugin.sh` assembles the distributable plugin tree
- the packaged plugin is meant for installation, not for authoring
- extensions are runtime workspace artifacts, not plugin-root runtime assets

## What the root build script packages

The root build script currently creates `tars-cowork-plugin/` and copies:
- `skills/`
- `commands/`
- Python scripts from `scripts/`
- `templates/`
- source Obsidian views into `templates/views/`
- `hooks/`
- `mcp/tars-vault/`
- `.claude/skills/`
- `LICENSE`
- `CLAUDE.md`
- `requirements.txt`
- `requirements-search.txt`
- `.claude-plugin/mcp-servers.json`
- `.mcp.json` when present

The build script does not package workspace-installed extensions into the plugin
root. Curated extension sources may live in the repository for catalog and
release purposes, but installation copies or syncs them into the user's
workspace under `extensions/` and records them in `_system/extensions.yaml`.

It also:
- generates a minimal distribution `plugin.json`
- writes a plugin-root `.mcp.json` from the manifest's `mcpServers`
- syncs version and description into `.claude-plugin/marketplace.json`
- writes a packaged README
- produces `tars-cowork-plugin/Archive.zip`

## Why the packaged manifest is minimal

The installable distribution relies on directory-based discovery at runtime. The packaged `plugin.json` therefore keeps only the metadata needed by the installer:
- name
- version
- description
- author
- license
- bundled `mcpServers` metadata for `tars-vault`

The repository remains the place where framework source, tests, and documentation live.

## Supported maintainer workflow

Use this sequence for release preparation:

1. Update framework source files.
2. Update public docs and changelog.
3. Update `.claude-plugin/plugin.json` if version or release metadata changed.
4. Run validators from `tests/`, including harness-budget and framework-contract checks when the harness changes.
5. Run `./build-plugin.sh`.
6. Run `python3 tests/validate-release-artifact.py` to verify the packaged plugin contents, helper startup, and scaffold behavior.
7. Tag and publish the GitHub release artifact.

## Repository versus distribution

Repository source includes:
- documentation
- tests
- helper and compatibility files not required in the install artifact
- optional extension catalog sources, when present

Distribution output includes only what the installed framework needs to run.
It must not rely on extensions being present under the plugin root.

## Versioning

The version source of truth is `.claude-plugin/plugin.json`.

Helpful utilities:

```bash
python3 scripts/bump-version.py X.Y.Z
python3 tests/validate-harness-budget.py
python3 tests/validate-framework-contracts.py
./build-plugin.sh
python3 tests/validate-plugin.py
```

## Marketplace metadata

Marketplace metadata lives in `.claude-plugin/marketplace.json`. The build script keeps the packaged version aligned with the source manifest so the GitHub release artifact and marketplace entry describe the same version of TARS.

## Legacy packaging note

Only the repository-root `build-plugin.sh` is part of the supported release flow.
