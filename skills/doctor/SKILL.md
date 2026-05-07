---
name: doctor
description: Check whether TARS is installed correctly and the local helper can read and write the workspace
user-invocable: true
triggers:
  - "/doctor"
  - "check TARS install"
  - "diagnose TARS"
  - "TARS setup is not working"
  - "local TARS helper"
help:
  purpose: |-
    Run a nontechnical install check for the required local TARS helper, workspace path, write permission, and optional search enhancements.
  use_cases:
    - "Check whether TARS is installed correctly"
    - "Recover from a failed welcome setup"
    - "Confirm a moved workspace still works"
  scope: setup,diagnostics,recovery
---

# Doctor: check TARS install

Use this skill when setup fails, TARS cannot write to the workspace, or the user asks whether their install is healthy.

## Step 1: Try the local helper check

Call `mcp__tars_vault__runtime_info` with the active workspace path if known.

If it returns:

- `required_runtime: "ok"`: tell the user the local TARS helper is connected.
- `required_runtime: "error"`: show the recovery block in Step 3.
- `optional_search: "degraded"`: mention that semantic search enhancements are unavailable, but setup and keyword search still work.

Do not treat missing `fastembed` or `sqlite-vec` as setup blockers.

## Step 2: Check workspace consistency

If the helper is connected and a workspace path is known, summarize:

- active workspace path
- whether `_system/install.yaml` exists
- whether the workspace is writable
- whether setup looks complete

Keep the first answer short. Put technical details under `Details` only if needed.

## Step 3: Missing local helper recovery

If `mcp__tars_vault__runtime_info` is unavailable, do not mention raw MCP tool names in the user-facing response. Say:

```markdown
I can't safely finish TARS setup because the local TARS helper is not connected.

This helper creates and checks the workspace in the background. This is not an Obsidian, calendar, task, email, or Slack issue. Those integrations are optional.

Try this:
1. Make sure the TARS plugin is enabled in Claude.
2. Restart Claude so the local helper starts.
3. Run `/doctor` again, or ask "check my TARS install."
4. When the check passes, run `/welcome`.

Details: TARS needs the bundled `tars-vault` helper with Python 3.10+ and the `mcp` package. Semantic search packages are optional and can be added later.
```

If the user is in a code checkout and asks for technical help, suggest:

```bash
python3 scripts/doctor.py --workspace "<path to your TARS workspace>"
```

## Step 4: Closeout

If the check passes, end with:

```markdown
TARS is ready. If this is your first run, use `/welcome`, or just say "set up TARS."
```

If there are warnings only, say setup can continue and name the feature that will be degraded.
