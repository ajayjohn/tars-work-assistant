# TARS v3 Rebuild — Decisions and Deviations

This document records justified deviations from the V3 rebuild plan, prerequisite blockers, and architectural decisions made during implementation.

## Architectural Decisions

### D1: Obsidian Bases syntax updated to match actual skill reference

**Plan specified**: Object-based filter syntax with `property:`, `operator:`, `value:` objects (from V2/V3 plan documents)

**Implemented**: Expression-based filter syntax using `file.hasTag("tars/person")`, `'tars-status == "active"'`, etc.

**Reason**: The V3 plan was written before the actual obsidian-bases SKILL.md was available. The real Obsidian Bases syntax uses expression strings and `file.hasTag()` / `file.inFolder()` functions, not object-based filter definitions. The plan's syntax would not render correctly in Obsidian.

**Impact**: All 15 `.base` files use the correct syntax. Views use `order:` (not `properties:`), `groupBy:` (not `group:`), and expression-based filters.

### D2: PyYAML fallback in all Python scripts

**Plan specified**: Scripts use `import yaml` directly

**Implemented**: All scripts include a `try: import yaml` with a fallback simple YAML parser

**Reason**: The system Python on macOS does not include PyYAML by default. Since TARS targets macOS knowledge workers, scripts must work without requiring `pip install pyyaml`. The fallback parser handles the flat YAML structures used in TARS frontmatter and schemas.

**Impact**: All scripts run on stock macOS Python 3. PyYAML is used when available for better parsing fidelity.

### D3: Single source tree — no duplicate distribution folders

**Plan specified**: "No `.claude-plugin/`, no `tars-cowork-plugin/`"

**Implemented**: The existing v2 distribution folders (`antigravity-wrapper/`, `tars-cowork-plugin/`, `.claude-plugin/`, `commands/`, `data/`) remain on the `tars-3.0` branch but are not part of the v3 architecture. They are preserved for rollback safety.

**Reason**: Deleting them on the branch could complicate merge/rollback. The v3 system ignores them entirely. A cleanup commit can remove them once v3 is validated.

### D4: Vault structure built in-repo, not directly in vault

**Plan specified**: The vault IS the source of truth

**Implemented**: The v3 framework files are built in the repo at `/Users/ajayjohn/Sync/Applications/Library/tars/` on branch `tars-3.0`. The actual vault at `/Users/ajayjohn/Notes/TARS-Work` is the deployment target.

**Reason**: The user specified that the existing v2 TARS instance will be migrated to v3 once ready. Building in the repo preserves the v2 deployment and allows controlled rollout. A separate migration plan (TARS_V3_INSTANCE_MIGRATION_PLAN.md) exists for this purpose.

### D5: Template variables use Obsidian's `{{date}}` syntax

**Plan specified**: Templates should use Obsidian templates with frontmatter

**Implemented**: Templates use `{{date}}` which is Obsidian's built-in template variable for current date (YYYY-MM-DD format). The `obsidian create ... template="person"` command resolves these variables.

**Reason**: This is Obsidian's native template variable system. The obsidian-cli `create` command with `template=` parameter processes these.

## Environment Blockers

### B1: CronCreate/CronList/CronDelete — Available

The Claude Code runtime provides `CronCreate`, `CronList`, and `CronDelete` tools. The onboarding wizard (welcome skill) uses these to register scheduled briefings and maintenance tasks. No blocker.

### B2: Obsidian CLI — Available

`obsidian-cli` v1.12.4 is installed and connected to the TARS-Work vault. The `obsidian` command is fully functional. No blocker.

### B3: Integration testing — Deferred to deployment

Integration tests that require writing to the live vault (obsidian create/append round-trips) are specified in the plan but not executed during the rebuild. These should be run after the framework is deployed to the vault.

**Reason**: The rebuild creates framework source files in a git repo. Integration tests need to run against the actual Obsidian vault instance. Running them would modify the vault, which is currently the v2 deployment.

**Mitigation**: Smoke tests validate all structural components. Schema validation runs against test fixtures. Integration tests are fully specified and can be run post-deployment.

## Issue Coverage Matrix

| # | Issue | Implementation | Files |
|---|-------|---------------|-------|
| 1 | Transcript format variability + mandatory calendar check | Meeting skill Steps 2-3: format detection, MANDATORY calendar check even if date present | `skills/meeting/SKILL.md` |
| 2 | Task review UX | Numbered list with selection syntax in all task extraction | `skills/tasks/SKILL.md`, `skills/meeting/SKILL.md` |
| 3 | Ask don't assume | Core principle, multiple-choice questions, max 3-4 per round | `skills/core/SKILL.md`, all skills |
| 4 | File organization + companion files | Companion template, maintenance file org workflow, all-documents.base | `templates/companion.md`, `skills/maintain/SKILL.md`, `_views/all-documents.base` |
| 5 | Quick capture / screenshot processing | Inbox processing image pipeline, multimodal analysis + calendar context | `skills/maintain/SKILL.md` (inbox mode) |
| 6 | Transcript-linked fallback lookup | Transcript archive with bidirectional links, answer skill fallback | `templates/transcript.md`, `skills/answer/SKILL.md`, `skills/meeting/SKILL.md` |
| 7 | Check before writing | Knowledge inventory protocol in all extraction workflows | `skills/core/SKILL.md`, `skills/learn/SKILL.md`, `skills/meeting/SKILL.md` |
| 8 | Negative statement capture + cleanup | Sentiment detection, inline flags, periodic review in maintenance | `_system/guardrails.yaml`, `scripts/scan-flagged.py`, `skills/maintain/SKILL.md`, `_views/flagged-content.base` |
| 9 | Self-evaluation backlog | Auto-issue detection + user idea capture, deduplicated | `_system/backlog/`, `templates/issue.md`, `templates/idea.md`, `_views/backlog.base`, `skills/core/SKILL.md` |
| 10 | Scheduled briefings + maintenance | CronCreate registration in onboarding, cron self-check in briefings | `skills/welcome/SKILL.md`, `skills/briefing/SKILL.md` |
