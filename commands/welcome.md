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
   - persona
   - Claude-first vs Obsidian browsing mode
3. Use the bundled local TARS helper to create the workspace. Internally this
   means `mcp__tars_vault__scaffold_workspace` exactly once.
4. Verify `index.md`, `_system/install.yaml`, `_system/config.md`, `memory/`,
   and `inbox/pending/` before saying setup is complete.
5. If the local helper is unavailable or verification fails, stop. Do not create
   files or folders manually. Use this user-facing recovery text:

   > I can't safely finish TARS setup because the local TARS helper is not connected.
   >
   > This helper creates and checks the workspace in the background. This is not
   > an Obsidian, calendar, task, email, or Slack issue. Those integrations are optional.
   >
   > Please make sure the TARS plugin is enabled, restart Claude, and run `/doctor`
   > or ask "check my TARS install." Then run `/welcome` again.

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
