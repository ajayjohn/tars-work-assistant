# Framework taxonomy

This file is a compatibility-oriented overview. The active runtime taxonomy for TARS 3.0 lives in `_system/taxonomy.md`, and the canonical note schemas live in `_system/schemas.yaml`.

## Managed entity areas

TARS primarily manages these note families:

| Area | Entity type | Folder |
|------|-------------|--------|
| People | person | `memory/people/` |
| Vendors | vendor | `memory/vendors/` |
| Competitors | competitor | `memory/competitors/` |
| Products | product | `memory/products/` |
| Initiatives | initiative | `memory/initiatives/` |
| Decisions | decision | `memory/decisions/` |
| Organizational context | context | `memory/org-context/` |
| Meeting journals and briefings | — | `journal/YYYY-MM/` |
| Transcript archives | — | `archive/transcripts/YYYY-MM/` |

## Tagging and schema rules

TARS 3.0 uses:
- `tars/` tags for managed notes
- `tars-` frontmatter properties for managed metadata
- wikilinks for entity references

The core rule is simple: do not invent alternate schema shapes when a template or `_system/schemas.yaml` already defines one.

## Durability model

Durability still matters in v3, but it is applied through the runtime schema and maintenance behavior rather than through old index-driven conventions.

Canonical durability tiers:
- durable
- seasonal
- transient
- ephemeral

Use them consistently when a note type supports archival or staleness handling.

## Relationships

TARS notes should express entity relationships through:
- canonical names
- wikilinks
- typed relationship metadata when the schema supports it

Common relationship concepts include:
- reporting lines
- initiative ownership
- decision impact
- collaborator and stakeholder links
- vendor and product relationships

## Practical guidance

When in doubt:
- use the matching template in `templates/`
- validate against `_system/schemas.yaml`
- prefer updating an existing canonical note over creating duplicates
