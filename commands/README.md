---
description: Command-to-skill mapping reference
---

# TARS slash commands

Each slash command in this folder is a thin wrapper around a skill under
the repo's `skills/` tree. The wrapper's sole job is to point Claude Code
at the skill's `SKILL.md`; all pipeline logic lives in the skill.

## Mapping

| Command | Skill | Purpose |
|---------|-------|---------|
| `/answer` | [skills/answer/](../skills/answer/SKILL.md) | Fast lookup with full-text + semantic fallback |
| `/briefing` | [skills/briefing/](../skills/briefing/SKILL.md) | Daily / weekly briefing |
| `/communicate` | [skills/communicate/](../skills/communicate/SKILL.md) | Stakeholder drafting with RASCI |
| `/create` | [skills/create/](../skills/create/SKILL.md) | Office output via Anthropic rendering skills |
| `/initiative` | [skills/initiative/](../skills/initiative/SKILL.md) | Initiative plan / status / performance |
| `/learn` | [skills/learn/](../skills/learn/SKILL.md) | Memory save or wisdom extraction |
| `/lint` | [skills/lint/](../skills/lint/SKILL.md) | Vault lint — deterministic + LLM checks |
| `/maintain` | [skills/maintain/](../skills/maintain/SKILL.md) | Inbox / sync / archive sweep |
| `/meeting` | [skills/meeting/](../skills/meeting/SKILL.md) | Meeting transcript pipeline |
| `/tasks` | [skills/tasks/](../skills/tasks/SKILL.md) | Task extraction / manage |
| `/think` | [skills/think/](../skills/think/SKILL.md) | Strategic analysis (modes A–E) |
| `/welcome` | [skills/welcome/](../skills/welcome/SKILL.md) | First-run onboarding |

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
