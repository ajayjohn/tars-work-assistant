---
description: Deterministic first-run TARS workspace setup and context gathering
argument-hint: "[--continue-setup | --enable-obsidian | --disable-obsidian | --relocate | --change-persona]"
---

# /welcome

## Protocol

Read and follow `skills/welcome/SKILL.md`.

If the skill file is not available, do **not** improvise a generic workspace.
Follow this fallback contract instead:

1. Explain that TARS stores all state in one portable Markdown workspace.
2. Ask for:
   - workspace location
   - name
   - role/title
   - company/team
   - first use case
   - persona
   - Claude-first vs Obsidian browsing mode
3. Call `mcp__tars_vault__scaffold_workspace` exactly once.
4. Verify `index.md`, `_system/install.yaml`, `_system/config.md`, `memory/`,
   and `inbox/pending/` before saying setup is complete.
5. If the scaffold tool is unavailable or verification fails, stop and show the
   reason. Do not create files or folders manually.

Hard rules:

- The inbox is the `inbox/pending/` folder, not `INBOX.md` or `inbox.md`.
- Durable memory records live under `memory/people/`, `memory/initiatives/`,
  `memory/decisions/`, and related `memory/` subfolders.
- Never create root files named `MEMORY.md`, `PEOPLE.md`, `INITIATIVES.md`, or
  `INBOX.md`.
- Never create generic folders named `calendar/`, `notes/`, `people/`,
  `projects/`, `research/`, or `knowledge/`.
- Do not recommend namespaced command syntax. Slash commands are optional;
  natural language works.
