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

# Artifact generation protocol

Generate presentation-grade content: decks, narratives, speeches, thought leadership pieces, panel prep, event session content.

**Architecture (v3.1)**: `/create` is an orchestrator. TARS handles content structuring, vault grounding, brand-pointer, companion-note creation, and filing. Office rendering (`.pptx`, `.docx`, `.xlsx`, `.pdf`, HTML) delegates to **Anthropic's first-party skills** (`pptx`, `docx`, `xlsx`, `pdf`, `web-artifacts-builder`) — never to a TARS-built office MCP. TARS does not bundle `python-pptx`, `openpyxl`, `python-docx`, `weasyprint`, or similar. See PRD §3.1b, §8.10, §26.4. Phase 6 implements the full delegation flow; Phase 2 rewires the vault-interaction plumbing only.

Vault reads/writes use `mcp__tars_vault__*` tools (see `skills/core/SKILL.md`). Data-source integrations (KPI, analytics, design, project tracker, documentation) resolve via `mcp__tars_vault__resolve_capability(capability=…)`. Brand guidelines auto-load via `mcp__tars_vault__search_by_tag(tag="tars/brand")` filtered on `tars-brand: true` (Phase 5 finalizes; Phase 2 accepts user prompt for active brand file).

---

## Step 1: Intake

Gather from user or infer:
- **Topic**: What is this about?
- **Audience**: Who will consume this? (board, industry conference, internal all-hands, specific stakeholder)
- **Format**: Deck / Narrative / Speech
- **Key messages**: What must be conveyed?
- **Time constraints**: Presentation length or reading time
- **Event type**: If applicable (conference, board meeting, team meeting)

If critical intake info is missing, apply clarification protocol.

---

## Step 2: Context gathering

Load relevant context via vault MCP tools (`.base` views replace `_index.md` files in v3):

- Initiatives: `mcp__tars_vault__search_by_tag(tag="tars/initiative", limit=20)` + targeted `read_note` for the ones being referenced.
- Products:   `mcp__tars_vault__search_by_tag(tag="tars/product", limit=20)` + targeted `read_note`.
- Decisions:  `mcp__tars_vault__search_by_tag(tag="tars/decision", query="<topic keywords>", limit=10)`.
- People:     `mcp__tars_vault__read_note(file="<stakeholder name>")` for audience-specific adaptation.
- Contexts:   Phase 4 adds `mcp__tars_vault__semantic_search(scope="contexts", query=…)`; until then `search_by_tag` + targeted reads.
- Journal:    recent entries via `search_by_tag(tag="tars/journal", frontmatter={"tars-date__gte": …})`.

### Data sources (if the content references metrics, KPIs, usage, or design)

Resolve integrations before invoking their tools:
```
data_wh = mcp__tars_vault__resolve_capability(capability="data-warehouse")   # Snowflake / BigQuery / Databricks
analytics = mcp__tars_vault__resolve_capability(capability="analytics")       # Pendo / Amplitude / Mixpanel
tracker  = mcp__tars_vault__resolve_capability(capability="project-tracker") # Jira / Linear / GitHub
design   = mcp__tars_vault__resolve_capability(capability="design")           # Figma
docs     = mcp__tars_vault__resolve_capability(capability="documentation")    # Confluence / Notion / Google Docs
```
Skill degrades gracefully if any capability is unavailable.

---

## Step 3: Format-specific generation

### Deck format

Slide-by-slide outline:
```markdown
## Slide 1: [Title]
**Key points:**
- [Point 1]
- [Point 2]

**Speaker notes:**
[What to say when presenting this slide]

**Suggested visual:**
[Chart type, image concept, or data visualization]
```

Structure: Opening (hook + agenda) -> Body (3-5 key sections) -> Close (summary + call to action)

### Narrative format

Long-form piece with:
- BLUF (opening summary)
- Supporting arguments with data points
- Stakeholder-relevant framing
- Call to action or next steps

Apply stakeholder-comms protocol for audience adaptation (UPSTREAM/DOWNSTREAM/EXTERNAL).

### Speech format

Structured with:
- Opening hook (story, provocative question, or bold statement)
- Key sections with timing guidance (e.g., "~3 min")
- Transitions between sections
- Closing (callback to opening, clear ask, or memorable statement)
- Conversational tone calibrated to audience:
  - Board: formal, data-driven, concise
  - Industry conference: thought-leadership, forward-looking
  - Internal all-hands: authentic, motivating, transparent

---

## Step 4: Audience adaptation

| Audience type | Adaptation |
|---------------|------------|
| **Upstream** (Board, CEO, CPO) | BLUF, ROI focus, concise, strategic framing |
| **Downstream** (Team) | Context-rich, motivating, clear RASCI |
| **External** (Conference, partners) | Thought leadership, industry framing, no internal jargon |

---

## Step 5: Review pass

Strategic analysis light:
- Are claims supported by known data (from memory/contexts)?
- Is messaging consistent with known initiatives and decisions?
- Are there political sensitivities? (Check stakeholder profiles)
- Would the CTO or CPO object to anything? (Quick mental validation)

---

## Output

Save the content outline (markdown) as the canonical review surface, always:

```
mcp__tars_vault__create_note(
  name="YYYY-MM-DD Artifact Title",
  path="contexts/artifacts/YYYY-MM/YYYY-MM-DD-artifact-slug.md",
  frontmatter={
    "tars-date": "YYYY-MM-DD",
    "tars-title": "Artifact Title",
    "tars-type": "deck | narrative | speech",
    "tars-audience": "Board | Conference | Team | <Stakeholder Name>",
    "tars-topic": "Primary topic",
    "tars-initiatives": ["[[Related Initiative]]"],
    "tars-created": "YYYY-MM-DD"
  },
  body="<content outline markdown>"
)
```

### If non-markdown output requested (Phase 6 delegates to Anthropic skills)

Phase 6 implements the full delegation pattern (§8.10): content-first (markdown review), then invoke Anthropic's `pptx` / `docx` / `xlsx` / `pdf` / `web-artifacts-builder` skill with the content outline and brand pointer, then create a companion `.md` via `mcp__tars_vault__create_note` per §26.13. Phase 2 does not ship the office delegation; if the user requests a `.pptx` or similar, inform them the full delegation lands in Phase 6 and produce markdown for now.

Display the artifact to the user and confirm save location.

---

## Context budget
- Memory: Read `_index.md` + up to 5 targeted files
- Contexts: Up to 3 reference documents
- Journal: Current month `_index.md` + up to 2 recent entries for freshness

---

## Absolute constraints

- NEVER generate without understanding the audience
- NEVER skip the review pass
- NEVER use banned phrases from communication skill
- ALWAYS save artifacts to `contexts/artifacts/`
- ALWAYS apply audience-appropriate tone and framing
