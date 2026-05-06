---
name: start
description: Zero-setup quick demo. Accept pasted content or a natural request and produce a useful structured artifact in under 5 minutes.
user-invocable: true
triggers:
  - "/start"
  - "try TARS"
  - "show me what TARS can do"
  - "quick demo"
  - first session before /welcome has run
help:
  purpose: |-
    Zero-setup demo flow. Detect what the user pasted, produce one useful structured artifact, save nothing unless the user opts in, then offer setup for compounding value.
  use_cases:
    - "Try TARS without setting it up"
    - "Show me what this can do with a meeting transcript"
    - "Quick test before onboarding"
  scope: demo,onboarding,quick-start,evaluation
---

# Start: zero-setup demo

Use this skill when the user wants to try TARS before committing to setup. The goal is visible value in one interaction, not a tour.

## Step 1: Detect setup state

Check whether `_system/config.md` and `_system/install.yaml` exist.

- If `_system/config.md` is missing, or `tars-user-name` is empty, treat the user as new.
- If `_system/install.yaml` exists, read `workspace_type`, `workspace_path`, `obsidian_enabled`, and `obsidian_vault_path` so the closeout can describe persistence accurately.
- If the user is already set up and pasted content, continue in demo mode only if they explicitly asked for `/start`. Otherwise route to the canonical skill that fits the content.

## Step 2: Intake

If the user pasted content with the command, classify it immediately.

If no content was pasted, ask:

> "Paste anything, a meeting transcript, email thread, design doc, customer call, or sales discovery notes. I'll show you what TARS does with it. Or describe what you want to try and I'll suggest a paste-target."

If the user has nothing handy, offer:

1. Product: `examples/pm-customer-call.md`
2. Engineering: `examples/eng-design-discussion.md`
3. Sales: `examples/sales-discovery-call.md`

## Step 3: Classify content

| Detected content | Preview behavior |
|---|---|
| Speaker labels, timestamps, or Zoom/Teams/Otter/Fireflies headers | Meeting summary, decisions, risks, action items |
| Email thread or Slack-style export | Follow-up draft plus memory candidates |
| RFC, design doc, ADR, or decision memo | Decision summary and durable memory candidates |
| Roadmap, launch, or status doc | Initiative status preview |
| Sales discovery or customer call notes | Call summary plus follow-up email draft |
| Generic notes or prose | Memory candidates and what TARS would remember |

## Step 4: Produce a preview-only artifact

Do not write to the workspace. Do not call mutation tools. Do not create notes. Do not update frontmatter. Default behavior is preview-only.

Produce the most useful artifact inline:

- Meeting or call: summary, decisions, risks, action items, follow-up candidates.
- Email or Slack: concise reply draft, open questions, memory candidates.
- Design or roadmap doc: decision record, assumptions, risks, unresolved questions.
- Generic notes: durable facts, possible people or initiative records, suggested next prompt.

Cap output at about 2,000 words. If the content is large, summarize the visible preview and say that saving can preserve the full artifact after setup.

## Step 5: Close with honest next steps

End with this block, filling in counts from the preview:

```markdown
---

## What just happened

You ran TARS with zero setup. With `/welcome` (about 5 minutes), the same paste can also:
- Save {N_CANDIDATES} memory items so they show up in future `/briefing` and `/answer` results
- Extract {M_TASKS} action items into your TARS task notes, or into an external task system after you connect one
- Link people, decisions, and initiatives across future sessions

TARS starts as a local Markdown workspace in Claude. Obsidian is optional: turn it on later with `/welcome --enable-obsidian` if you want a visual note browser and `.base` views.

## What's next

1. **Set up TARS**: run `/welcome`
2. **See more**: run `/help`
3. **Save this demo**: say "save this" after setup to keep the artifact in your workspace
```

## Step 6: Save on demand

If the user replies "save this" or equivalent:

- If setup is complete, route to `/learn` or the canonical skill that created the preview and ask for confirmation before writing.
- If setup is incomplete, tell the user to run `/welcome` first, then repeat "save this".

Never save by default.
