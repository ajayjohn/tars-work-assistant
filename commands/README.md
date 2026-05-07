---
description: Command-to-skill mapping reference
---

# TARS slash commands

Slash commands are shortcuts, not requirements. TARS routes natural-language
requests to the same skills.

Each slash command in this folder is a thin wrapper around a skill under
the repo's `skills/` tree. The wrapper's sole job is to point Claude Code
at the skill's `SKILL.md`; all pipeline logic lives in the skill.

## Mapping

| Command | Skill | Purpose | Natural-language example |
|---------|-------|---------|--------------------------|
| `/start` | [skills/start/](../skills/start/SKILL.md) | Zero-setup preview | "Show me what TARS can do with this transcript" |
| `/help` | [skills/core/](../skills/core/SKILL.md) | Command and workflow help | "What can TARS do?" |
| `/answer` | [skills/answer/](../skills/answer/SKILL.md) | Fast lookup with full-text + semantic fallback | "What do we know about the platform rewrite?" |
| `/briefing` | [skills/briefing/](../skills/briefing/SKILL.md) | Daily / weekly briefing | "What should I focus on today?" |
| `/communicate` | [skills/communicate/](../skills/communicate/SKILL.md) | Stakeholder drafting with RASCI | "Draft a follow-up to Sam from this call" |
| `/create` | [skills/create/](../skills/create/SKILL.md) | Office output via Anthropic rendering skills | "Turn this into an exec-ready narrative" |
| `/doctor` | [skills/doctor/](../skills/doctor/SKILL.md) | Install and workspace health check | "Check my TARS install" |
| `/initiative` | [skills/initiative/](../skills/initiative/SKILL.md) | Initiative plan / status / performance | "Check the health of the onboarding initiative" |
| `/learn` | [skills/learn/](../skills/learn/SKILL.md) | Memory save or wisdom extraction | "Remember Sarah owns onboarding" |
| `/lint` | [skills/lint/](../skills/lint/SKILL.md) | Workspace lint — deterministic + LLM checks | "Check the workspace for stale or broken items" |
| `/maintain` | [skills/maintain/](../skills/maintain/SKILL.md) | Inbox / sync / archive sweep | "Process everything in my inbox" |
| `/meeting` | [skills/meeting/](../skills/meeting/SKILL.md) | Meeting transcript pipeline | "Process this meeting transcript" |
| `/tasks` | [skills/tasks/](../skills/tasks/SKILL.md) | Task extraction / manage | "Extract the action items from this" |
| `/think` | [skills/think/](../skills/think/SKILL.md) | Strategic analysis (modes A–E) | "Stress-test this roadmap decision" |
| `/welcome` | [skills/welcome/](../skills/welcome/SKILL.md) | First-run and continued setup | "Continue TARS setup" |

## Why wrappers remain

PRD §7.5 proposes retiring these wrappers in favor of Claude Code's
skill auto-registration (`user-invocable: true` in skill frontmatter).
That transition is deferred until auto-registration can be verified
end-to-end on a fresh install — the wrappers are small, stable, and
guarantee slash-command availability today.

## Adding a new command

1. Add a new skill folder under `skills/` containing a `SKILL.md`.
2. Add a matching wrapper file in `commands/` (3 lines of body, following
   the pattern of the existing wrappers in this folder).
3. Update the mapping table above.
