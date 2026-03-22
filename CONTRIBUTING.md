# Contributing to TARS

Use this checklist whenever you change the framework. TARS is opinionated and the docs, schemas, skills, templates, and packaging metadata need to stay aligned.

## If you change a skill

- Update the relevant file in `skills/`
- Update or add the matching file in `commands/` if the skill is user-invocable
- Update routing or protocol references in `skills/core/SKILL.md` and affected skills
- Update [README.md](/Users/ajayjohn/Sync/Applications/Library/tars/README.md) and [ARCHITECTURE.md](/Users/ajayjohn/Sync/Applications/Library/tars/ARCHITECTURE.md) if the public surface changed
- Update [reference/workflows.md](/Users/ajayjohn/Sync/Applications/Library/tars/reference/workflows.md) if the workflow model changed
- Update [CHANGELOG.md](/Users/ajayjohn/Sync/Applications/Library/tars/CHANGELOG.md)
- Run `python3 tests/validate-routing.py`
- Run `python3 tests/validate-docs.py`

## If you change templates, schemas, or system files

- Keep `templates/`, `_system/schemas.yaml`, and the relevant skill instructions in sync
- Update `_views/` if properties or tags used in bases changed
- Update [ARCHITECTURE.md](/Users/ajayjohn/Sync/Applications/Library/tars/ARCHITECTURE.md) if folder structure or note types changed
- Update migration or compatibility references if the change affects existing vault data
- Run `python3 tests/validate-templates.py`
- Run `python3 tests/validate-frontmatter.py`

## If you change scripts or maintenance behavior

- Update the script under `scripts/`
- Update any skills that invoke or depend on that script
- Update [BUILD.md](/Users/ajayjohn/Sync/Applications/Library/tars/BUILD.md) or [reference/shortcuts.md](/Users/ajayjohn/Sync/Applications/Library/tars/reference/shortcuts.md) when packaging or scheduled behavior changes
- Update [CHANGELOG.md](/Users/ajayjohn/Sync/Applications/Library/tars/CHANGELOG.md)
- Run `python3 tests/validate-scripts.py`
- Run `python3 tests/validate-docs.py`

## If you change integrations

- Update `_system/integrations.md` defaults or related instructions
- Keep provider-specific names out of skill files unless there is a narrow documented exception
- Update [GETTING-STARTED.md](/Users/ajayjohn/Sync/Applications/Library/tars/GETTING-STARTED.md) if onboarding expectations changed
- Run `python3 tests/validate-docs.py`

## If you change release metadata or packaging

- Update `.claude-plugin/plugin.json`
- Update `.claude-plugin/marketplace.json` if the build flow no longer syncs what changed automatically
- Update [BUILD.md](/Users/ajayjohn/Sync/Applications/Library/tars/BUILD.md)
- Update [CHANGELOG.md](/Users/ajayjohn/Sync/Applications/Library/tars/CHANGELOG.md)
- Rebuild with `./build-plugin.sh`

## Local validation

Run these before publishing or merging significant framework changes:

```bash
python3 tests/validate-structure.py
python3 tests/validate-frontmatter.py
python3 tests/validate-references.py
python3 tests/validate-routing.py
python3 tests/validate-templates.py
python3 tests/validate-scripts.py
python3 tests/validate-docs.py
python3 tests/smoke-tests.py
```

If you touch packaging or release metadata, also run:

```bash
python3 scripts/validate-plugin.py
./build-plugin.sh
```
