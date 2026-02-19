# Contributing to TARS

## Consistency checklist

When making changes to the TARS framework, use this checklist to ensure everything stays in sync.

### If you add, rename, or remove a skill:
- [ ] Update `plugin.json` skills array
- [ ] Update or create `commands/{name}.md`
- [ ] Update core skill routing/signal table
- [ ] Update `ARCHITECTURE.md` skill tables and counts
- [ ] Update `README.md` skills and commands tables
- [ ] Update `reference/workflows.md` if the skill participates in any workflow
- [ ] Update `CHANGELOG.md` with the change
- [ ] Run `python3 tests/validate-docs.py` to catch stale references

### If you add, rename, or remove a script:
- [ ] Update `ARCHITECTURE.md` scripts list and count
- [ ] Update any skill that invokes the script
- [ ] Update `reference/shortcuts.md` if the script is used in scheduled tasks
- [ ] Run `python3 tests/validate-docs.py`

### If you change a protocol (durability test, accountability test, etc.):
- [ ] Update the authoritative definition in core skill
- [ ] Check all skills that reference the protocol (grep for the protocol name)
- [ ] Update sub-agent templates that inline the protocol
- [ ] The durability test and accountability test examples in core MUST be preserved

### If you change integration patterns:
- [ ] Update `reference/integrations.md` (the single source of truth for providers)
- [ ] NEVER add provider-specific names to skill files
- [ ] Run `python3 tests/validate-docs.py` (Check 2: provider compliance)

### If you change version numbers or counts:
- [ ] Update `plugin.json` version
- [ ] Update `ARCHITECTURE.md` counts and version references
- [ ] Update `CHANGELOG.md` with a non-empty entry for the new version
- [ ] Run `python3 tests/validate-docs.py` (Check 3: count consistency)

## Running validators locally

```bash
python3 tests/validate-structure.py    # Plugin structure
python3 tests/validate-frontmatter.py  # YAML frontmatter
python3 tests/validate-references.py   # Cross-references
python3 tests/validate-routing.py      # Routing completeness
python3 tests/validate-templates.py    # Reference files
python3 tests/validate-scripts.py      # Script syntax
python3 tests/validate-docs.py         # Documentation consistency
```

Run all validators before committing changes to skills, commands, or documentation.
