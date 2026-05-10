---
description: Deterministic first-run TARS workspace setup and context gathering
argument-hint: "[--continue-setup | --enable-obsidian | --disable-obsidian | --relocate | --change-persona]"
---

# /welcome

## Protocol

Use the packaged `skills/welcome/SKILL.md` instructions only if they are
already visible in the plugin context. Do not call any tool just to load them.

Do **not** try to read `skills/welcome/SKILL.md` from the user's workspace with
the TARS helper. The workspace will not contain plugin source files during
fresh setup, and a missing workspace note is not a setup problem.

If the packaged skill file is not available, do **not** mention the missing
skill file to the user and do **not** improvise a generic workspace. Follow this
self-contained fallback contract instead:

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
- Do not recommend `/briefing` as a starter action in a brand-new workspace.
  Briefings become useful after the workspace has memory, meetings, tasks, or
  connected calendar/task integrations.
- Do not end by asking an open-ended "what's on your mind?" question. End by
  guiding the user into the first demo.

When setup succeeds, use this final response shape exactly. Keep it concise:

```markdown
## Workspace Ready

TARS is set up in `{workspace_path}`.

- `index.md`: cheat sheet created
- `memory/`: durable context folders ready
- `inbox/pending/`: drop-zone ready for transcripts, PDFs, reports, email threads, decks, screenshots, exports, and rough notes

Slash commands are optional. You do not need to remember them; natural language works just as well.

| Shortcut | Natural-language example |
|---|---|
| `/maintain inbox` | "Process everything in my inbox" |
| `/meeting` | "Process this meeting transcript" |
| `/learn` | "Remember that Sarah owns onboarding" |
| `/help` | "What can TARS do?" |

### Try this now

Paste or upload a meeting transcript, PDF/report excerpt, email thread, or rough notes. I will preview what TARS can extract into memory candidates, journal notes, and tasks before saving anything.

Or drop files into `inbox/pending/` and say: "process inbox".

You can continue setup later with `/welcome --continue-setup` or by saying "continue TARS setup".

TARS is ready whenever you want to process something.
```
