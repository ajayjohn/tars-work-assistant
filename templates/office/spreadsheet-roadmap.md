# {{title}} — Roadmap

**Period:** {{period_start}} → {{period_end}}
**Teams:** {{team_list}}

---

## Sheet 1: Swimlane grid

Columns: `initiative`, `owner`, `phase`, `{{period_start}}`, …, `{{period_end}}`.

Each row represents one initiative. Each period column carries one of:
- `planned`
- `in-progress`
- `done`
- `at-risk`
- blank

| initiative | owner | phase | {{period_1}} | {{period_2}} | {{period_3}} | {{period_4}} |
|-----------|-------|-------|--------------|--------------|--------------|--------------|
| {{initiative_1}} | {{owner_1}} | {{phase_1}} | planned | in-progress | in-progress | done |
| {{initiative_2}} | {{owner_2}} | {{phase_2}} | — | planned | in-progress | in-progress |

Render hints:
- Conditional formatting: `planned` (grey), `in-progress` (blue), `done` (green), `at-risk` (red).
- Freeze the left three columns.

## Sheet 2: Dependencies

| Initiative | Depends on | Type | Resolved? |
|-----------|-----------|------|-----------|
| {{initiative_1}} | {{dep_1}} | {{dep_type_1}} | {{resolved_1}} |

## Sheet 3: Milestones

| Initiative | Milestone | Target date | Owner | Status |
|-----------|-----------|-------------|-------|--------|

---

Render hints passed to the `xlsx` skill:
- One row per initiative; never break into multiple rows per initiative.
- Dates: ISO 8601.
