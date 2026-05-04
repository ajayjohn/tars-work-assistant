# Persona templates

Persona templates seed onboarding defaults so a fresh vault is useful on day 1 instead of after weeks of meeting transcripts. Each persona is a markdown file under this directory whose frontmatter carries structured seed data; the body is a short prose description shown to the user during persona selection.

The `welcome` skill reads the chosen persona during Step 1 and applies its frontmatter as defaults to:

- `_system/config.md` — `tars-bluf-level`, `tars-default-analysis-mode`, `tars-review-gate-strictness`, `tars-briefing-style`
- `_system/taxonomy.md` — appends role-aware starter tags
- `_system/install.yaml` — sets `persona: <key>`

The user can override any default in the wizard before it commits, and edit the resulting files freely afterwards. Personas are seed data, not running config.

## Schema

Persona frontmatter must include:

| Field | Purpose |
|-------|---------|
| `tars-persona-key` | Stable identifier matching the filename (e.g. `product-leader`) |
| `tars-persona-name` | Human-readable label shown in the picker |
| `tars-persona-summary` | One-sentence description |
| `tars-config-defaults` | Map of `tars-*` keys → default values applied to `_system/config.md` |
| `tars-taxonomy-tags` | List of role-relevant tag suggestions appended to `_system/taxonomy.md` |
| `tars-briefing-sections` | Ordered list of sections the daily briefing should include for this role |
| `tars-default-mode` | `casual` or `standard`; the wizard still asks the user, this is just a hint |

Valid `tars-config-defaults` keys (subset; extend as needed):

- `tars-bluf-level`: `high` | `medium` | `low`
- `tars-default-analysis-mode`: `A` | `B` | `C` | `D` | `E` (per `skills/think/manifesto.md`)
- `tars-review-gate-strictness`: `strict` | `standard` | `lenient`
- `tars-briefing-style`: `executive` | `analytical` | `operational`

## Available personas

| Key | When to pick |
|-----|--------------|
| `product-leader` | Owns roadmap, customer signals, feature decisions |
| `sales-customer-facing` | Owns pipeline, accounts, relationships, deal motion |
| `delivery-pm` | Owns schedule, scope, dependencies, RAID, sprint health |
| `data-science-lead` | Owns experiments, metrics, model drift, analyses |
| `architect-staff-eng` | Owns technical decisions, ADRs, system design, RFCs |
| `support-ops-lead` | Owns incidents, SLAs, escalations, on-call, runbooks |
| `engineering-manager` | Owns 1:1s, team health, hiring, delivery, performance |

## Authoring a new persona

1. Copy the closest existing file under a new key.
2. Edit the frontmatter — keep it tight (~1–2 KB total).
3. Update this README's "Available personas" table.
4. The `welcome` skill picks up new files automatically.

Personas should not duplicate logic that lives in core skills. They only carry seed defaults.
