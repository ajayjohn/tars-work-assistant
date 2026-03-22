# TARS 3.0 Build and Release

This document describes the supported packaging path for the rebuilt framework.

## Build model

TARS 3.0 is maintained from the repository root and packaged into a distributable plugin directory. The active packaging entrypoint is [build-plugin.sh](/Users/ajayjohn/Sync/Applications/Library/tars/build-plugin.sh).

The build model is:
- repository source is the maintainer-facing truth
- `.claude-plugin/plugin.json` is the metadata source of truth
- `build-plugin.sh` assembles the distributable plugin tree
- the packaged plugin is meant for installation, not for authoring

## What the root build script packages

The root build script currently creates `tars-cowork-plugin/` and copies:
- `skills/`
- Python scripts from `scripts/`
- `templates/`
- `_system/`
- `_views/`
- `.claude/skills/`
- `LICENSE`
- `CLAUDE.md`
- `.mcp.json` when present

It also:
- generates a minimal distribution `plugin.json`
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

The repository remains the place where framework source, tests, and documentation live.

## Supported maintainer workflow

Use this sequence for release preparation:

1. Update framework source files.
2. Update public docs and changelog.
3. Update `.claude-plugin/plugin.json` if version or release metadata changed.
4. Run validators from `tests/`.
5. Run `./build-plugin.sh`.
6. Verify the packaged plugin contents and packaged README.
7. Tag and publish the GitHub release artifact.

## Repository versus distribution

Repository source includes:
- documentation
- tests
- migration and rebuild handoff documents
- helper and compatibility files not required in the install artifact

Distribution output includes only what the installed framework needs to run.

## Versioning

The version source of truth is `.claude-plugin/plugin.json`.

Helpful utilities:

```bash
python3 scripts/bump-version.py 3.0.0
./build-plugin.sh
python3 tests/validate-plugin.py
```

## Marketplace metadata

Marketplace metadata lives in `.claude-plugin/marketplace.json`. The build script keeps the packaged version aligned with the source manifest so the GitHub release artifact and marketplace entry describe the same version of TARS.

## Legacy packaging note

Only the repository-root `build-plugin.sh` is part of the supported v3 release flow.
