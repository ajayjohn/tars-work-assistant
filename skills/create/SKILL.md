---
name: create
description: Generate presentation-grade decks, narratives, and speeches with audience adaptation
user-invocable: true
help:
  purpose: |-
    Generate presentation-grade decks, narratives, speeches, and thought leadership content with audience adaptation.
  use_cases:
    - "Create a deck for [topic]"
    - "Write a speech for [event]"
    - "Draft a narrative for the board"
  scope: presentations,decks,speeches,narratives,content
---

# /create — vault-grounded content orchestrator

`/create` is the TARS orchestrator for presentation-grade artifacts: decks, narratives, speeches, dashboards, memos. TARS owns content structuring, vault grounding, brand pointer, companion notes, telemetry, and filing. **Office rendering delegates to Anthropic's first-party skills** (`pptx`, `docx`, `xlsx`, `pdf`, `web-artifacts-builder`). TARS ships zero office-format libraries (no `python-pptx`, `openpyxl`, `python-docx`, `weasyprint`, `markdown-it-py`, `matplotlib`). See PRD §3.1b, §8.10, §26.4.

Vault reads/writes use `mcp__tars_vault__*` tools (see `skills/core/SKILL.md`). Data-source integrations (KPI, analytics, design, project tracker, documentation) resolve via `mcp__tars_vault__resolve_capability(capability=…)`.

---

## Pipeline overview

| Step | Name | Purpose |
|------|------|---------|
| 0 | Capability probe | Detect which Anthropic rendering skills are available this session |
| 1 | Intake | Topic, audience, format, key messages, constraints |
| 2 | Brand auto-load | Resolve active brand file (`tars-brand: true`) for the rendering prompt |
| 3 | Context gathering | Initiatives, products, decisions, people, integration data |
| 4 | Format selection | Markdown only, or markdown + one/more Anthropic-rendered formats |
| 5 | Content-first draft | Structured markdown outline, saved + reviewed once |
| 6 | Review & approve | User confirms outline before render spend |
| 7 | Delegate render | Invoke chosen Anthropic skill(s) with brand pointer |
| 8 | Verify + companion | Confirm file exists, write `.md` companion per §26.13 |
| 9 | Telemetry | Emit `artifact_generated` |

---

## Step 0: Capability probe (session-cached)

On first `/create` invocation per session, detect which Anthropic first-party skills are available in this Claude Code install. Check the skill roster surfaced in `<system-reminder>` blocks or ask the host via the standard skill list — do not attempt to load or probe the skill programmatically.

| Skill | Output format | Needed when |
|-------|---------------|-------------|
| `pptx` | `.pptx` | User requests a deck beyond Marp markdown |
| `docx` | `.docx` | User requests Word output |
| `xlsx` | `.xlsx` | User requests a spreadsheet |
| `pdf` | `.pdf` | User requests PDF output |
| `web-artifacts-builder` | HTML | User requests HTML / browser-renderable presentation |

Cache the detection result for the rest of the session. If a requested skill is missing, inform the user once with:
> "Anthropic's `<skill>` skill isn't available in this Claude Code install. Install it (it usually auto-bundles) or I can produce markdown / Marp output for now."

Fallback policy when a requested renderer is missing: produce markdown outline + (if a deck was requested) Marp-syntax markdown slides, and note the gap in the output.

---

## Step 1: Intake

Gather or infer:

- **Topic**: what is this about?
- **Audience**: board / exec / team / industry conference / specific stakeholder.
- **Format family**: deck, narrative / memo, speech, spreadsheet / dashboard.
- **Output file formats** (Step 4 re-confirms): markdown only, or markdown plus one-or-more of pptx / docx / xlsx / pdf / html / Marp.
- **Key messages**: what must be conveyed?
- **Time constraints**: deck length, reading time, speaking time.
- **Event type** (if applicable): conference talk, board meeting, all-hands, customer pitch.

If critical intake info is missing, apply the clarification protocol (batched multiple-choice, max 3–4 per round).

---

## Step 2: Brand auto-load (MANDATORY when non-markdown output requested)

Resolve the active brand guidelines file. Passed as a path pointer to the rendering skill in Step 7 — **TARS never theme-renders programmatically.**

1. `mcp__tars_vault__read_note(file="config")` → check frontmatter `tars-active-brand`.
2. If present, resolve the pointed file and verify it has `tars-brand: true`.
3. If absent, search: `mcp__tars_vault__search_by_tag(tag="tars/brand")`, filter results where frontmatter `tars-brand: true`.
   - Zero hits → proceed without brand (render skill uses its default styling); note "no brand applied" in output.
   - One hit → use it. Offer to cache: `update_frontmatter(file="config", property="tars-active-brand", value=<filename>)`.
   - Multiple hits → list numbered, ask which to use this round + whether to cache.
4. Carry the resolved path (vault-relative) forward to Step 7 as `brand_file`.

See `templates/brand-guidelines.md` for the content shape that a brand file should follow.

---

## Step 3: Context gathering

Load relevant context via vault MCP tools. `.base` views replace `_index.md` files in v3.

- Initiatives: `search_by_tag(tag="tars/initiative", limit=20)` + targeted `read_note` for those referenced.
- Products:   `search_by_tag(tag="tars/product", limit=20)` + targeted `read_note`.
- Decisions:  `search_by_tag(tag="tars/decision", query="<topic keywords>", limit=10)`.
- People:     `read_note(file="<stakeholder name>")` for audience-specific adaptation.
- Contexts:   `semantic_search(scope="contexts", query=…)` when prose-heavy; otherwise `search_by_tag` + targeted reads.
- Journal:    recent via `search_by_tag(tag="tars/journal", frontmatter={"tars-date__gte": …})`.

### Data-backed claims (if content references metrics / KPIs / usage / design)

Resolve capabilities before invoking their tools:

```
data_wh   = mcp__tars_vault__resolve_capability(capability="data-warehouse")
analytics = mcp__tars_vault__resolve_capability(capability="analytics")
tracker   = mcp__tars_vault__resolve_capability(capability="project-tracker")
design    = mcp__tars_vault__resolve_capability(capability="design")
docs      = mcp__tars_vault__resolve_capability(capability="documentation")
```

Skill degrades gracefully if any capability is `unavailable`. Record which data sources were used — they feed `tars-source-data` on the companion note (§26.13).

---

## Step 4: Format selection

Ask the user, gated on Step 0 capabilities:

```
Target output — pick one or more:
  1. Markdown only (always available, fastest)
  2. PowerPoint deck (.pptx)          [via anthropic pptx]
  3. Word document (.docx)            [via anthropic docx]
  4. Excel workbook (.xlsx)           [via anthropic xlsx]
  5. PDF (.pdf)                        [via anthropic pdf]
  6. HTML presentation                  [via anthropic web-artifacts-builder]
  7. Marp-syntax markdown slides        [always available; user renders locally]

Multiple allowed (e.g. "1+2" for markdown + pptx).
```

Grey-out / mark unavailable any option whose corresponding Anthropic skill failed the Step 0 probe. Default is markdown (#1).

---

## Step 5: Content-first draft

Generate a structured markdown outline. Template starters live in `templates/office/`:

| Template | Shape |
|----------|-------|
| `deck-executive.md` | Title / exec summary / 5–10 content slides / appendix |
| `deck-narrative.md` | Amazon six-pager style |
| `deck-technical-review.md` | Background / options / recommendation / open questions |
| `spreadsheet-kpi-dashboard.md` | Tabular outline (sheets, columns, sample rows) |
| `spreadsheet-roadmap.md` | Swimlane grid of initiatives × time |
| `doc-decision-memo.md` | BLUF / context / options / recommendation |
| `doc-project-status.md` | Health / milestones / risks / asks |
| `html-board-update.md` | Single-page narrative with charts |

Populate the chosen outline with vault data. Per-slide / per-section structure:

```markdown
## Slide 1: Title
**Key points:** …
**Speaker notes:** …
**Suggested visual:** …
```

Save the outline:

```
mcp__tars_vault__create_note(
  path="journal/YYYY-MM/YYYY-MM-DD-<slug>.md",
  name="YYYY-MM-DD <Artifact Title>",
  frontmatter={
    "tags": ["tars/journal"],
    "tars-date": "YYYY-MM-DD",
    "tars-title": "<title>",
    "tars-type": "deck | narrative | speech | spreadsheet",
    "tars-audience": "Board | Conference | Team | <Stakeholder Name>",
    "tars-topic": "<primary topic>",
    "tars-initiatives": ["[[Related Initiative]]"],
    "tars-output-formats": ["markdown", "pptx"],
    "tars-brand-applied": "<brand-file-stem or 'none'>",
    "tars-created": "YYYY-MM-DD"
  },
  body=<content outline markdown>
)
```

---

## Step 6: Review & approve

Present the outline (or a BLUF summary of it, if >50 slides / sections) and ask:

```
Proceed with render? (Review is free; render takes seconds-to-minutes per format.)
  - "render" — proceed with all formats selected in Step 4
  - "render pptx" — render a specific format only
  - "edit <slide|section> N" — revise before render
  - "markdown only" — stop here, keep only the outline
```

If only markdown was selected in Step 4, this step is a display-and-confirm, no render follows.

---

## Step 7: Delegate render (non-markdown formats)

Invoke the chosen Anthropic skill(s) via the Claude Code skill-invocation mechanism. One invocation per format. Canonical prompt template:

```
I need the <pptx|docx|xlsx|pdf|web-artifacts-builder> skill to render the following content.

Content outline:     <vault-relative path to the markdown saved in Step 5>
Output path:         contexts/artifacts/YYYY-MM/<slug>.<ext>
Brand guidelines:    <brand_file path from Step 2, or "none" if no brand>
Data sources used:   <list from Step 3>
Vault context:       TARS executive-assistant vault; match the executive-grade tone
                     described in the brand file (if any)
Companion note:      DO NOT create a companion .md — TARS will handle that after
                     you complete.

Proceed.
```

Wait for each render to complete. Do not fire them in parallel unless explicitly requested — parallel invocations complicate companion-note ordering.

Note on brand: TARS passes the brand file **path**, not rendered theme artifacts. The rendering skill reads the file and applies the brand (LLM-driven). This is simpler, more flexible, and works for any brand + format.

---

## Step 8: Verify + companion

For each rendered output:

1. Verify the output file exists at the declared path (`mcp__tars_vault__read_note` equivalent or filesystem probe via the rendering skill's own report).
2. Compute file size + SHA-256 (render skill should report; if not, request).
3. Create the companion `.md` per §26.13 contract:

```
mcp__tars_vault__create_note(
  path="contexts/artifacts/YYYY-MM/<slug>.md",
  name="<slug>.<ext>",
  frontmatter={
    "tags": ["tars/companion"],
    "tars-companion-of": "<slug>.<ext>",
    "tars-original-file": "<slug>.<ext>",
    "tars-original-type": "pptx | docx | xlsx | pdf | html",
    "tars-generated-by": "anthropic-skill:<pptx|docx|xlsx|pdf|web-artifacts-builder>",
    "tars-orchestrated-by": "tars-create v3.1.0",
    "tars-generated-at": "<ISO 8601>",
    "tars-brand-applied": "<brand-file-stem or 'none'>",
    "tars-source-initiative": "[[<initiative>]]",
    "tars-source-data": [
      {"capability": "data-warehouse", "server": "<resolved>", "query": "<query>"},
      {"capability": "analytics",       "server": "<resolved>", "path": "<path>"}
    ],
    "tars-file-size": "<bytes>",
    "tars-sha256": "<hex>",
    "tars-created": "YYYY-MM-DD",
    "tars-modified": "YYYY-MM-DD",
    "tars-summary": "<1-paragraph narrative of what's in the artifact>"
  },
  body=<structure summary: slide list / section list / sheet list>
)
```

The companion note is discoverable via `_views/all-documents.base`.

---

## Step 9: Telemetry

Emit one event per rendered artifact:

```json
{
  "event": "artifact_generated",
  "skill": "create",
  "type": "deck|narrative|speech|spreadsheet|dashboard",
  "format": "pptx|docx|xlsx|pdf|html|markdown|marp",
  "renderer": "anthropic-skill:<name>|tars-markdown",
  "brand_applied": true,
  "data_sources": ["data-warehouse", "analytics"],
  "outcome": "success|partial|error"
}
```

Emit `skill_invoked` + `skill_completed` at pipeline boundaries per §26.11.

---

## Audience adaptation (applied at Step 5)

| Audience type | Adaptation |
|---------------|------------|
| **Upstream** (Board, CEO, CPO) | BLUF, ROI focus, concise, strategic framing |
| **Downstream** (Team) | Context-rich, motivating, clear RASCI |
| **External** (Conference, partners) | Thought leadership, industry framing, no internal jargon |

See `skills/communicate/SKILL.md` for the full Empathy Audit + RASCI rules when the artifact contains stakeholder language.

---

## Review pass (applied at Step 6)

Strategic analysis light:

- Are claims supported by known data (memory / contexts / integrations)?
- Is messaging consistent with known initiatives and decisions?
- Are there political sensitivities? (check stakeholder profiles)
- Would the CTO or CPO object to anything? (quick mental validation)

---

## Context budget

| Resource | Budget |
|----------|--------|
| Memory | up to 5 targeted files (stakeholders + initiatives + decisions) |
| Contexts | up to 3 reference documents |
| Journal | current month recent entries for freshness (≤2) |
| Integrations | parallel capability resolution; skip unavailable ones silently |

---

## Absolute constraints

1. NEVER generate office output without understanding the audience.
2. NEVER skip the content-first / review-before-render step (Step 5 + Step 6).
3. NEVER apply brand programmatically — always pass brand as a file pointer to the rendering skill.
4. NEVER build or reintroduce a TARS office MCP (§3.1b, §26.4).
5. NEVER skip the companion-note creation (§26.13 is mandatory).
6. NEVER use banned phrases from `skills/communicate/`.
7. ALWAYS save outline first under `journal/YYYY-MM/` before invoking any render.
8. ALWAYS save rendered artifacts under `contexts/artifacts/YYYY-MM/`.
9. ALWAYS emit `artifact_generated` telemetry per rendered output.
