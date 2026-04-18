---
tags:
  - tars/context
  - tars/brand
tars-brand: true
tars-brand-name: "{{brand_name}}"
tars-summary: >
  Brand guidelines for {{brand_name}}. Colors, typography, voice, layout conventions,
  logo usage. Applied by /create and /communicate when authoring artifacts and
  stakeholder communications. Delegate rendering to the chosen Anthropic skill
  (pptx/docx/xlsx/pdf/web-artifacts-builder); this file is the source of truth
  for brand application.
tars-created: {{date}}
tars-modified: {{date}}
---

# {{brand_name}} brand guidelines

## Colors

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Primary |  |  | Title bars, headers, primary CTAs |
| Secondary |  |  | Accents, hover, secondary CTAs |
| Background |  |  | Slide / page background |
| Text |  |  | Body text |
| Muted |  |  | Captions, metadata |

## Typography

| Role | Font family | Weight | Size guidance |
|------|-------------|--------|---------------|
| Titles |  |  |  |
| Headings |  |  |  |
| Body |  |  |  |
| Caption |  |  |  |

## Logo usage

- Primary mark:
- Monochrome mark:
- Minimum clear space:
- Minimum display size:
- Do NOT: stretch, rotate, or alter colors.

## Voice

| Attribute | Guidance |
|-----------|----------|
| Tone |  |
| Reading level |  |
| Person (we / I / it) |  |
| Banned words / phrases |  |

## Layout conventions

- Slide aspect ratio:
- Margins:
- Title bar height:
- Footer content (if any):
- Table / chart defaults:

## Accessibility

- Minimum contrast ratio:
- Color-blindness considerations:
- Alt-text policy:

---

## Notes for rendering skills

When `/create` delegates to Anthropic's `pptx` / `docx` / `xlsx` / `pdf` /
`web-artifacts-builder` skills, it passes this file path in the instruction
prompt. The rendering skill reads this file and applies the brand.

TARS does not theme programmatically. All brand application is LLM-driven by the
rendering skill, so keep this document prose-clear rather than machine-parsed.
