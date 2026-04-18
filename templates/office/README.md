# `templates/office/` — content outlines (not renderers)

These are structural markdown outlines used by `/create`. TARS populates them
with vault data and then either:

1. **Markdown-only output** — returns the populated outline to the user.
2. **Office / HTML output** — passes the populated outline *as a file path* to
   Anthropic's first-party skill (`pptx`, `docx`, `xlsx`, `pdf`,
   `web-artifacts-builder`), which owns the rendering.

TARS never imports `python-pptx`, `openpyxl`, `python-docx`, `weasyprint`,
`markdown-it-py`, or `matplotlib`. See PRD §3.1b and §26.4.

| Template | Shape | Typical renderer |
|----------|-------|-----------------|
| `deck-executive.md` | Title / exec summary / 5–10 content slides / appendix | `pptx` |
| `deck-narrative.md` | Amazon six-pager | `docx` (often) / `pptx` |
| `deck-technical-review.md` | Background / options / recommendation | `pptx` |
| `spreadsheet-kpi-dashboard.md` | Tabular outline, sheets × columns | `xlsx` |
| `spreadsheet-roadmap.md` | Swimlane grid initiatives × time | `xlsx` |
| `doc-decision-memo.md` | BLUF / context / options / recommendation | `docx` |
| `doc-project-status.md` | Health / milestones / risks / asks | `docx` |
| `html-board-update.md` | Single-page narrative + charts | `web-artifacts-builder` |

Each template uses plain markdown with `{{placeholder}}` fields that `/create`
substitutes during Step 5 of its pipeline.
