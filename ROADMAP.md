# TARS Plugin Roadmap

**Version**: 1.5.0 → 2.0.0
**Date**: 2026-02-07
**Author**: AJ + TARS

---

## Current state assessment

TARS v1.5 is a well-architected, production-ready plugin with 28 skills, 23 commands, and a 3-level loading model that keeps session baselines at ~115 tokens. The framework has excellent internal consistency, strong instruction quality (~8.5/10 across skills), and minimal redundancy (~5%, all intentional). The plugin is ready for team distribution.

**Version numbering note**: The current released state of TARS is v1.5.0 (previously labeled v2.0.0). All changes in this roadmap culminate in v2.0.0 as the first major release under the new architecture. Prior versions: v1.0.0 (initial), v1.1.0 (docs), v1.2.0 (Antigravity inlining), v1.3.0 (plugin decomposition), v1.4.0 (protocol-to-skill migration), v1.5.0 (structural compliance rebuild). Phase 0 corrects plugin.json to v1.5.0. After Phase 9, version is bumped to v2.0.0. The implementing agent must update plugin.json, CHANGELOG.md, and ARCHITECTURE.md to reflect this renumbering.

---

## Implementation quick start (for implementing agent)

This section provides the critical context a fresh agent needs before reading the rest of the roadmap.

### Working directory

The plugin has two copies in the workspace:
- **`tars/`** (outer folder): The canonical source. Contains the complete `plugin.json` (with skills/commands arrays), full documentation (ARCHITECTURE.md, CHANGELOG.md, README.md), and all skill/command/reference files. **All roadmap work happens here.**
- **`tars/tars-cowork-plugin/`** (inner folder): A stripped-down distribution copy for Cowork plugin upload. Minimal `plugin.json` (no skills/commands arrays), shorter README, and an Archive.zip. **Do not modify this folder during implementation.** It should be regenerated from the outer folder as a final distribution step after Phase 9 is complete.

### Current directory structure (v1.5.0)

```
tars/
├── .claude-plugin/
│   └── plugin.json                      # Manifest: name, version (2.0.0→rename to 1.5.0), description, license, author, skills[], commands[]
├── .mcp.json                            # Filesystem MCP server configured
├── skills/                              # 28 skills total
│   ├── identity/SKILL.md                # Background (user-invocable: false)
│   ├── communication/SKILL.md           # Background
│   ├── memory-management/SKILL.md       # Background
│   ├── task-management/SKILL.md         # Background
│   ├── decision-frameworks/SKILL.md     # Background
│   ├── clarification/SKILL.md           # Background
│   ├── routing/SKILL.md                 # Background (signal table, auto side-effects)
│   ├── process-meeting/SKILL.md         # Workflow
│   ├── extract-tasks/SKILL.md           # Workflow
│   ├── manage-tasks/SKILL.md            # Workflow
│   ├── extract-memory/SKILL.md          # Workflow
│   ├── extract-wisdom/SKILL.md          # Workflow
│   ├── briefing/SKILL.md               # Workflow (daily/weekly modes)
│   ├── communicate/SKILL.md             # Workflow
│   ├── strategic-analysis/SKILL.md      # Workflow
│   ├── executive-council/SKILL.md       # Workflow
│   ├── validation-council/SKILL.md      # Workflow
│   ├── discovery-mode/SKILL.md          # Workflow
│   ├── create-artifact/SKILL.md         # Workflow
│   ├── performance-report/SKILL.md      # Workflow
│   ├── initiative/SKILL.md              # Workflow (planning/status modes)
│   ├── quick-answer/SKILL.md            # Workflow
│   ├── housekeeping/SKILL.md            # Workflow
│   ├── rebuild-index/SKILL.md           # Workflow
│   ├── setup/SKILL.md                   # System (rename to welcome in v2.0)
│   ├── update/SKILL.md                  # System
│   ├── meeting-processor/SKILL.md       # Composite (chains: process-meeting → extract-tasks → extract-memory)
│   └── deep-analysis/SKILL.md           # Composite (chains: strategic-analysis → validation-council → executive-council)
├── commands/                            # 23 commands, each 3-5 lines YAML frontmatter + skill redirect
│   ├── setup.md, update.md, process-meeting.md, extract-memory.md, extract-tasks.md
│   ├── manage-tasks.md, extract-wisdom.md, daily-briefing.md, weekly-briefing.md
│   ├── communicate.md, strategic-analysis.md, executive-council.md, validation-council.md
│   ├── discovery-mode.md, initiative-planning.md, initiative-status.md
│   ├── create-artifact.md, performance-report.md, quick-answer.md
│   ├── rebuild-index.md, housekeeping.md, meeting-processor.md, deep-analysis.md
├── reference/                           # 5 template files
│   ├── integrations.md                  # Provider-based connector config (currently hardcoded to Eventlink + remindctl)
│   ├── taxonomy.md                      # Memory types, tags, frontmatter templates
│   ├── replacements.md                  # Name normalization (empty template)
│   ├── kpis.md                          # KPI definitions (empty template)
│   └── schedule.md                      # Recurring/one-time scheduled items
├── ARCHITECTURE.md
├── CHANGELOG.md
├── README.md
└── LICENSE
```

### Current plugin.json (v1.5.0 — currently mislabeled as v2.0.0)

```json
{
  "name": "tars",
  "version": "2.0.0",
  "description": "Strategic intelligence framework with native Claude plugin architecture...",
  "license": "Apache-2.0",
  "author": {"name": "Ajay John"},
  "skills": [
    "skills/identity/SKILL.md",
    "skills/communication/SKILL.md",
    ...28 total, each a string path relative to plugin root
  ],
  "commands": [
    "commands/setup.md",
    "commands/update.md",
    ...23 total, each a string path relative to plugin root
  ]
}
```

Fields currently missing that must be added in Phase 0: `author.url`, `repository`, `homepage`, `bugs`, `keywords`, `contributors`. Do not add `author.email`.

### Current YAML frontmatter format (v1.5.0)

Every SKILL.md currently has this frontmatter:

```yaml
---
name: skill-name
description: One-line description used for L1 loading and routing
user-invocable: true|false
---
```

In v2.0, the `help` section is added (see Part I3):

```yaml
---
name: skill-name
description: One-line description for L1 loading and routing
user-invocable: true|false
help:
  purpose: |
    Multi-line explanation of what this skill does.
  use_cases:
    - "When user wants X"
    - "When user needs Y"
  invoke_examples:
    - natural: "Natural language trigger phrase"
    - slash: "/command-name <args>"
  common_questions:
    - q: "Frequently asked question?"
      a: "Answer."
  related_skills: [skill-a, skill-b]
---
```

All `help` fields use block scalars (`|`) for multi-line text and flow sequences (`[a, b]`) for short lists. The `help` section is required on all skills in v2.0.

### 3-level loading model

This is the key architectural pattern that makes skill consolidation token-efficient:

- **L1 (session start)**: Only YAML frontmatter loads (`name` + `description`). Cost: ~4 tokens per skill. With 15 skills: ~60 tokens total. This is why merging 28 skills into 15 reduces session baseline from ~115 to ~60 tokens.
- **L2 (skill triggered)**: Full SKILL.md body loads when the skill is invoked by signal or command. Only one skill typically loads per user turn. Merged skills are larger per file, but only the relevant mode section is followed.
- **L3 (on demand)**: Supporting files within a skill directory (e.g., `meeting-context-query.md`) load only when the skill explicitly references them. If a merged skill exceeds ~500 lines, split into sub-files loaded at L3.

### Skill types

- **Background skills** (`user-invocable: false`): Always-on behavioral constraints that define HOW TARS operates (identity, communication rules, memory patterns, decision frameworks, clarification rules, routing). In v2.0, all 7 merge into a single `skills/core/SKILL.md`.
- **Workflow skills** (`user-invocable: true`): Skills that perform actual work when invoked (meeting processing, task extraction, analysis, briefings, etc.). In v2.0, 19 workflow skills consolidate into ~11 by merging related capabilities.
- **Composite skills** (`user-invocable: true`): Orchestrate chains of workflow skills. In v2.0, composite skills are absorbed into their parent workflow skill as modes.

### Routing table

The routing table lives in `skills/routing/SKILL.md` (v1.5.0) and will move to `skills/core/SKILL.md` (v2.0). It maps natural language signals to skills:

```
Signal pattern                          → Skill invoked
"process meeting", "parse transcript"   → skills/meeting/
"extract tasks", "action items"         → skills/tasks/ (extract mode)
"remember this", "save to memory"       → skills/learn/ (memory mode)
"help with", "how do I", "what can you" → help routing in core skill
```

Skills are also invocable via slash commands, which bypass routing and directly trigger the skill.

---

## Part A: Architecture review findings

### A1. Shareability (resolved)

The plugin contains zero personal work data. All examples use generic placeholders. The single `Account: CSI` reference in `reference/integrations.md` has been changed to `Account: {calendar_account}`. The plugin is safe to share with any team member.

### A2. Architectural simplification

**Verdict: Simplify from 28 skills + 23 commands to ~15 skills + ~11 commands without losing fidelity.**

#### The core problem

The average user will never type `/extract-wisdom` or `/validation-council`. They will say "here's a podcast transcript, pull out the good stuff" or "poke holes in this plan." The current architecture optimizes for power users who memorize commands. It should optimize for natural language users who expect the plugin to figure out what to do.

#### Merge background skills into a single "core" skill

The 7 background skills (identity, communication, memory-management, task-management, decision-frameworks, clarification, routing) are all `user-invocable: false`. They should be merged into a single `skills/core/SKILL.md` (~400 lines, tightened from 550 through de-duplication).

**Communication rules go global**: The communication skill's output formatting rules (BLUF mandate, anti-sycophancy, banned phrases, structural constraints) currently only apply to the communicate workflow. In v2.0, these rules live in the core skill and apply to ALL TARS output, not just communications. Every response from every skill follows these standards.

**Clarification integrates AskUserQuestion**: The clarification section in core.md should instruct TARS to prefer the AskUserQuestion tool (structured UI with multiple-choice options, max 4 questions, 2-4 options each) when running in Cowork mode. Fall back to inline text-based clarification in Claude Code or other environments.

**Proactive learning triggers**: Add a section to core.md that tells TARS to proactively suggest memory extraction when the user corrects a fact, shares context in passing, or when calendar shows new recurring meetings with unknown attendees.

#### Consolidate workflow skills by domain

| Current skills | Proposed merged skill | Modes |
|---|---|---|
| process-meeting + meeting-processor | **meeting** | `auto` (full pipeline with parallel sub-agents) |
| extract-tasks + manage-tasks | **tasks** | `extract` (from any text), `manage` (review/triage) |
| extract-memory + extract-wisdom | **learn** | `memory` (persist facts), `wisdom` (extract from content) |
| strategic-analysis + executive-council + validation-council + deep-analysis + discovery-mode | **think** | `analyze`, `debate`, `stress-test`, `deep` (full chain), `discover` (no-solution) |
| briefing (daily/weekly) | **briefing** | `daily`, `weekly` |
| initiative (planning/status) + performance-report | **initiative** | `plan`, `status`, `performance` |
| housekeeping + rebuild-index + update | **maintain** | `health-check`, `rebuild`, `sync`, `inbox` |
| communicate | **communicate** | standalone |
| create-artifact | **create** | standalone |
| quick-answer | **answer** | standalone |
| setup → **welcome** | **welcome** | standalone (renamed, redesigned) |

#### Token efficiency for merged skills

Merged skills are larger per file, but this does not increase token cost because of the 3-level loading model. Only YAML frontmatter descriptions (~4 tokens per skill) load at session start. The full skill body loads on-demand when triggered. Merging 28 skills into ~15 reduces session baseline from ~115 to ~60 tokens. When a merged skill loads, only the relevant mode section needs to be followed. Skills should use clear mode headers so the LLM can skip irrelevant sections.

#### Memory and task extraction availability

Memory extraction (`/learn`) and task extraction (`/tasks extract`) remain available as standalone slash commands. Users can run these after any conversation, brainstorming session, or on any arbitrary text. They also fire automatically as side-effects of meeting processing and wisdom extraction. The routing table ensures both natural language ("extract the tasks from what we just discussed") and slash commands work.

#### Commands (Option A: slim directory)

Keep a slim commands/ directory with ~11 thin wrappers matching the merged skills. Each is 3-5 lines of YAML frontmatter + redirect. This preserves slash-command discoverability across all environments.

#### Result

| Component | v1.5.0 | v2.0.0 | Change |
|---|---|---|---|
| Background skills | 7 | 1 (core) | -6 files |
| Workflow skills | 19 | 11 | -8 files |
| Composite skills | 2 | 0 (absorbed) | -2 files |
| Commands | 23 | ~11 | -12 files |
| Total skill+command files | 51 | ~26 | ~50% reduction |

### A3. Scripts, sub-agents, and platform features

#### Skills that should become scripts

| Skill operation | Script | What script does | What LLM does |
|---|---|---|---|
| Housekeeping scans | `scripts/health-check.py` | File naming validation, YAML frontmatter checks, index-vs-file diffs, wikilink validation, replacements coverage | Interpret report, recommend fixes |
| Index regeneration | `scripts/rebuild-indexes.py` | Parse frontmatter from all files, generate YAML index tables | Report results |
| Setup scaffolding | `scripts/scaffold.sh` | Create directories, verify integrations, copy templates | Run interactive wizard |
| Update sync | `scripts/sync.py` | Check schedule.md dates, query task tool for overdue, scan orphan tasks | Triage and gap detection |
| Archival sweep | `scripts/archive.py` | Scan staleness scores, move expired content to archive, expire ephemeral lines | Report what was archived |
| Sensitive data scan | `scripts/scan-secrets.py` | Regex scan content against guardrails.yaml patterns, detect secrets/credentials/PII | Present matches to user, offer redact/skip |
| Integration verify | `scripts/verify-integrations.py` | Check each configured integration's health, update status in integrations registry | Report to user |
| Plugin validation | `scripts/validate-plugin.py` | Check plugin structure, YAML frontmatter, cross-references, broken paths | Generate test report |

#### Sub-agent parallelization

Meeting processing: After generating the transcript report (step 1), spawn two parallel sub-agents for task extraction and memory extraction. 30-40% wall-clock improvement.

Deep analysis: After strategic analysis completes, spawn validation-council and executive-council in parallel.

Briefing data gathering: Query calendar, tasks, and memory indexes in parallel via three sub-agents.

Batch inbox processing: Each item in the inbox processed by an independent sub-agent with isolated context.

#### Context compacting

For chained workflows, add explicit guidance to offload intermediate results to files rather than keeping everything in context. Write intermediate outputs to `journal/` or temporary files, then reference the file path in subsequent steps.

#### Skill description optimization

Rewrite all skill YAML descriptions with trigger keywords that match natural language patterns. Budget: ~15,000 characters total, ~15 skills at ~50-100 chars each = well within limits.

---

## Part B: Data architecture overhaul

### B1. Index format and semantic searchability

**Recommendation: Switch to full YAML indexes.** Token savings vs markdown tables are modest (~10%), but the real gains are in editability (no column alignment), parseability (YAML is unambiguous), and extensibility (adding fields doesn't break formatting). Compact/abbreviated formats were evaluated and rejected because users need to edit these files.

Enhanced index structure includes tags searchable at the index level, staleness tier visible for archival filtering, and a consolidated master index (`memory/_index.md`) with a summary line for every entity across all categories, enabling single-file entity lookup.

Enhanced frontmatter adds explicit typed relationships (`reports_to`, `member_of`, `works_on`, etc.) making the knowledge graph queryable without reading prose content.

### B2. Content archival system

Four-tier staleness classification: durable (never auto-archives), seasonal (180 days no-update), transient (90 days no-access), ephemeral (date-based expiry). Ephemeral facts within durable files use `[expires: YYYY-MM-DD]` tags in a clearly marked section. Archive folder at `archive/YYYY-MM/{category}/` with `_archive_index.yaml`. Unarchive available for non-ephemeral content. Normal searches never touch the archive.

### B3. Batch processing inbox

Folder structure: `inbox/pending/`, `inbox/processing/`, `inbox/completed/`, `inbox/failed/`. Users drop files, TARS auto-detects content type and routes to the appropriate skill. Each item processed by isolated sub-agent. Failed items preserved with `.error` companion files. Daily briefing checks inbox and offers to process pending items.

---

## Part C: Platform feature integration

### C1. AskUserQuestion tool

Structured UI for clarification in Cowork mode. 2-4 options per question, max 4 questions per invocation. Core skill's clarification section should prefer this tool over inline text. Limitation: sub-agents cannot use it, so clarification must happen before spawning sub-agents.

### C2. Context compacting

Direct the LLM to offload intermediate results to files proactively. Include a "context management" directive in core skill.

### C3. TodoWrite for progress tracking

Multi-step skills include TodoWrite instructions for real-time user visibility during long-running operations.

### C4. Skill description optimization

Trigger keywords in YAML descriptions for better auto-routing accuracy.

---

## Part D: Integration abstraction layer

### D1. The problem

Different users use different tools. AJ uses Eventlink (local HTTP API) for calendar and remindctl (CLI) for tasks. Others may use Todoist MCP, Microsoft 365 calendar MCP, or other connectors. The framework must be agnostic of which tool is used, avoid placeholders with invalid values, and handle both MCP tools and local CLI/curl utilities uniformly.

### D2. Integration registry design

Replace the current `reference/integrations.md` with a provider-agnostic integration registry. The registry defines integration categories, not specific tools.

#### Registry format

```yaml
# reference/integrations.md

## Calendar
category: calendar
required: true
status: configured
provider: eventlink
type: http-api
operations:
  list_events: "GET {base_url}/events.json?date={date}&offset={offset}&selectCalendar={calendar}"
  create_event: "POST {base_url}/events/create?calendar={calendar}"
config:
  base_url: http://localhost:PORT
  calendar: Calendar
  auth: "Bearer TOKEN"
constraints:
  - Date format MUST be YYYY-MM-DD
  - Use date + offset, never startDate/endDate for fetching
  - Only create events with no attendees

## Tasks
category: tasks
required: true
status: configured
provider: remindctl
type: cli
operations:
  list: "remindctl list {list_name} --json"
  add: 'remindctl add --title "{title}" --list {list} --due {due} --notes "{notes}"'
  complete: "remindctl complete {id}"
  overdue: "remindctl overdue --json"
config:
  lists: [Active, Delegated, Backlog]
constraints:
  - Person-named lists are read-only
  - Only create/edit/delete in Active, Delegated, Backlog

## Project Tracker
category: project_tracker
required: false
status: not_configured
available_providers: [jira-mcp, linear-mcp, github-issues, azure-devops]
note: "Check <mcp_servers> for configured project tracker. If found, use its tools directly."
```

#### Key design principles

**No invalid placeholders**: If an integration is not configured, its status is `not_configured` and no fake URLs/tokens appear. The skill checks status before attempting operations and gracefully skips with a noted gap.

**Provider types**: Three types are supported:
- `http-api`: Local HTTP servers (Eventlink). Invoked via curl.
- `cli`: Command-line tools (remindctl). Invoked via bash.
- `mcp`: MCP servers. Detected from `<mcp_servers>` context at runtime. Invoked via Claude's native MCP tool calling.

**Runtime MCP discovery**: For MCP-based integrations, the skill checks `<mcp_servers>` at runtime to see what's available. If a Todoist MCP is connected, it maps to the `tasks` category. If a Jira MCP is connected, it maps to `project_tracker`. The registry records the mapping after the welcome flow configures it.

**Integration verification script**: `scripts/verify-integrations.py` checks each configured integration's health (curl for HTTP APIs, `which` for CLI tools, `<mcp_servers>` scan for MCPs) and updates the status field. Runs during welcome flow and can be triggered by `/maintain health-check`.

### D3. How skills use integrations

Skills reference integration categories, not specific tools. Example in the briefing skill:

```
Step 1: Query calendar integration
- Read reference/integrations.md, find the calendar section
- If status = configured, execute the list_events operation with today's date
- If status = not_configured, skip and note gap: "Calendar not configured. Run /welcome to set up."
- If status = error, report the specific error
```

This pattern replaces all hardcoded references to `Eventlink` or `remindctl` in skill files. Skills say "query calendar" or "create task," and the integration registry tells them how.

### D4. Welcome flow integration setup

During the welcome flow (see Part E), TARS:
1. Runs `scripts/verify-integrations.py` to detect what's available
2. Asks the user to confirm or configure mandatory integrations (calendar, tasks)
3. Scans `<mcp_servers>` for optional integrations and offers to map them
4. Writes the confirmed configuration to `reference/integrations.md`

---

## Part E: Welcome flow and onboarding

### E1. The problem

The current `/setup` wizard asks 4 rounds of questions (identity, organization, people, context) with up to 3 questions per round. This is too much upfront. Employees may give up or provide incomplete answers. The plugin needs to get users to a "first win" within 5 minutes and continue learning in the background.

### E2. Rename setup → welcome

Rename the `setup` skill to `welcome`. This signals a friendlier, less technical experience. The command becomes `/welcome` instead of `/setup`.

### E3. Progressive onboarding design

Replace the 4-round interrogation with a 3-phase progressive approach:

**Phase 1: Instant setup (0-2 minutes, zero questions if possible)**

1. Run `scripts/scaffold.sh` to create directory structure
2. Run `scripts/verify-integrations.py` to detect available integrations
3. If calendar integration is configured, query it for the user's meetings from the past 2 weeks and upcoming week to auto-discover: the user's name (from calendar owner), recurring meetings, and frequent attendees
4. If task integration is configured, query it for existing tasks to understand the user's current work
5. Only ask what can't be auto-discovered. Use AskUserQuestion with max 2 questions:
   - "What's your role?" (Product Manager / Engineering Lead / Executive / Other) - only if not inferrable from calendar
   - "What does your org focus on?" (Growth / Technical excellence / Ops efficiency / Customer satisfaction) - helps TARS categorize content

**Phase 2: First win + essential context (2-5 minutes)**

After the minimal Phase 1 questions, collect essential profile information and immediately show value. The goal is to balance completeness with speed -- gather what TARS needs to be effective without turning this into an interrogation.

**Essential profile collection** (AskUserQuestion, 2 questions max per round, 2 rounds max):

Round 1 (if not auto-discovered from calendar/tasks):
- "What is your name?" (text input -- skip if calendar owner name was found)
- "What team are you on, and who is your manager?" (text input)

Round 2 (conditional -- only if role suggests management):
- If the user's role is a management/leadership role (inferred from title or Round 1): "Do you manage any teams or direct reports? If so, list them briefly." (text input)
- "What are your current top 1-3 initiatives or focus areas?" (text input)

**Strategic decision on what to collect when:**

| Data point | Phase 1 (auto) | Phase 2 (ask) | Phase 3 (learn) | Rationale |
|---|---|---|---|---|
| Name | Calendar owner | Fallback ask | - | Essential for CLAUDE.md identity |
| Role/title | - | Always ask | - | Shapes all TARS outputs |
| Team | - | Always ask | - | Needed for context from day 1 |
| Manager | - | Always ask | Refine | Critical for comms skill (upstream) |
| Company/industry | - | Always ask | - | Shapes analysis frameworks |
| Direct reports | - | Ask if manager role | Learn from meetings | Avoids assuming everyone manages |
| Teams managed | - | Ask if manager role | Learn from meetings | Same as above |
| Key people | Calendar attendees | - | Enrich from transcripts | Calendar gives 80% coverage |
| Initiatives | - | Ask top 1-3 | Learn from meetings | Anchor for all strategic work |
| Org acronyms | - | - | Learn from usage | Low priority, accumulates naturally |

**Immediate value demonstration** (after profile collection):
- Display snapshot: "Based on your calendar, you have N recurring meetings, interact with N people regularly, and have N upcoming meetings this week"
- Populate `reference/replacements.md` with names found in calendar events
- Create initial `memory/people/` entries from calendar attendees (name, meeting context)
- Create user's own profile entry in `memory/people/` from collected data
- Generate a mini-briefing: "Here's what your week looks like"

This is the "aha moment" -- the user sees TARS already understands their world with minimal input.

**Phase 3: Background learning (day 1-7, no friction)**

TARS continues learning passively over the first week:
- Each session checks for new calendar data and updates people/context
- During conversations, TARS proactively extracts memory when the user mentions organizational facts
- If direct reports or teams managed were not collected in Phase 2, infer from meeting patterns (1:1s with consistent attendees, team meetings the user organizes)
- At the end of day 1, TARS can suggest: "I've learned about N people so far. Want to tell me about your key initiatives?"
- By day 3, offer a maturity check: "Your TARS knows N people and N meetings. Add a few transcripts to unlock strategic insights."
- Proactively ask about org structure gaps: "I see you meet regularly with X, Y, Z. Are they on your team or a different team?"

### E4. Maturity model

Track the growth of the user's TARS instance with a simple progress system stored in `reference/maturity.yaml`:

```yaml
level: 1
stats:
  people: 5
  meetings_processed: 0
  decisions: 0
  initiatives: 0
  transcripts_fed: 0
milestones:
  level_1: {criteria: "Setup complete", achieved: 2026-02-07}
  level_2: {criteria: "10+ people, 5+ meetings processed", achieved: null}
  level_3: {criteria: "20+ people, 15+ meetings, 3+ initiatives", achieved: null}
  level_4: {criteria: "30+ people, 30+ meetings, active archival", achieved: null}
```

The daily briefing includes a one-line maturity status: "TARS maturity: Level 2 (15 people, 8 meetings processed). Next: process 7 more meetings to reach Level 3."

### E5. Sensitive data guardrails

**Critical compliance requirement**: TARS must never store secrets, credentials, or personally identifiable information (PII) that could cause security or privacy violations. This specifically means: SSNs, usernames/passwords, API keys, dates of birth, client secrets, tokens, and similar credential material.

**What is NOT restricted**: Names of individuals, client/company names, deal values, contract dates and terms, locations, meeting content, business context — all of this is legitimate organizational knowledge and should be stored freely in memory.

**Implementation approach: Script-based scanning** (`scripts/scan-secrets.py`). This is handled by a script rather than a prompt because:
- Pattern matching against known secret formats is deterministic — no LLM judgment needed
- Scripts are faster and cheaper than prompt-based scanning (zero token cost)
- Regex patterns for secrets are well-established (SSN format, API key patterns, JWT structure)
- False positive rates can be tuned by editing the patterns file without changing skill logic

**How it works**: Before any content is persisted to memory or journal, the skill invokes `scripts/scan-secrets.py` with the content as input. The script scans for matches against patterns in `reference/guardrails.yaml` and returns a report. If matches are found, the skill presents them to the user with options to redact or skip.

**Configurable per organization**: Add `reference/guardrails.yaml` where admins can define sensitive data patterns:

```yaml
sensitive_data_patterns:
  - type: ssn
    pattern: '\b\d{3}-\d{2}-\d{4}\b'
    label: "Social Security Number"
    action: block
  - type: api_key
    pattern: '(?i)(api[_-]?key|apikey)\s*[:=]\s*\S+'
    label: "API Key"
    action: block
  - type: password
    pattern: '(?i)(password|passwd|pwd)\s*[:=]\s*\S+'
    label: "Password"
    action: block
  - type: bearer_token
    pattern: '(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*'
    label: "Bearer Token"
    action: block
  - type: client_secret
    pattern: '(?i)(client[_-]?secret|secret[_-]?key)\s*[:=]\s*\S+'
    label: "Client Secret"
    action: block
  - type: jwt
    pattern: 'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
    label: "JWT Token"
    action: block
  - type: dob
    pattern: '(?i)(date\s*of\s*birth|dob|born\s*on)\s*[:=]?\s*\d'
    label: "Date of Birth"
    action: warn
  - type: private_key
    pattern: '-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----'
    label: "Private Key"
    action: block
  - type: connection_string
    pattern: '(?i)(mongodb|postgres|mysql|redis)://\S+:\S+@'
    label: "Database Connection String"
    action: block
allowed_data:
  - individual_names
  - client_company_names
  - deal_values_and_terms
  - contract_dates
  - locations
  - meeting_content
  - business_context
```

**Script output format**: The script returns JSON:
```json
{
  "clean": false,
  "matches": [
    {"type": "api_key", "label": "API Key", "line": 14, "action": "block", "snippet": "api_key=sk-...REDACTED"}
  ]
}
```

When matches are found, the skill presents them to the user:
- `block` matches: "This content contains [label] on line [N]. It must be removed before storing."
- `warn` matches: "This content may contain [label] on line [N]. Redact or confirm it's safe."

Decisions are logged to `reference/guardrail-log.yaml` for audit trail.

---

## Part F: Automated housekeeping

### F1. The problem

Users cannot be expected to manually run `/maintain` daily. Housekeeping (archival sweeps, index rebuilds, stale content detection, expired ephemeral fact removal) must happen automatically.

### F2. Simulated scheduling via session-start check

Claude plugins don't have background job runners. The practical solution is a "last-run check" that triggers housekeeping when the first session of the day starts.

**Implementation**: Add a state file `reference/.housekeeping-state.yaml`:

```yaml
last_run: 2026-02-07
last_success: true
run_count: 15
last_archival: 2026-02-06
last_index_rebuild: 2026-02-07
```

The core skill includes a directive: "At the start of every session, check `reference/.housekeeping-state.yaml`. If `last_run` is not today's date, run the housekeeping scripts silently in the background before proceeding with the user's request. Update `last_run` after completion. If the user's request is urgent, defer housekeeping to after the response."

**What runs automatically each day**:
1. `scripts/archive.py` -- expire ephemeral lines, check staleness thresholds, move qualifying files to archive
2. `scripts/health-check.py` -- validate indexes, check for broken wikilinks, flag issues
3. `scripts/sync.py` -- check schedule.md for due items, scan for orphan tasks
4. Check `inbox/pending/` for unprocessed items and report count to user

**What does NOT run automatically** (user-initiated only):
- Full index rebuild (expensive, only when needed)
- Unarchiving content
- Inbox processing (user triggers or confirms)

### F3. Alternative: Cowork shortcut with schedule

The `create-shortcut` skill in Cowork mode supports scheduled execution. Create a shortcut that runs housekeeping daily:

```yaml
name: daily-housekeeping
schedule: "0 8 * * *"  # 8 AM daily
command: "/maintain health-check"
description: "Run daily housekeeping: archival, index check, sync"
```

This is the preferred approach if the user's environment supports Cowork shortcuts with schedules. The session-start check serves as a fallback for environments without scheduling support.

---

## Part G: Enterprise distribution

### G1. The problem

The plugin needs to be hosted on a Git repository (GitHub or Bitbucket) and distributed to employees as an internal enterprise marketplace, with the ability to push updates.

### G2. Repository structure

Restructure the repository to support marketplace distribution:

```
tars/
├── .claude-plugin/
│   ├── plugin.json              # v2.0.0 manifest
│   └── marketplace.json         # Marketplace catalog entry (if this is a marketplace repo)
├── .mcp.json                    # MCP server config
├── skills/                      # All skills
├── commands/                    # Thin wrappers
├── scripts/                     # Automation scripts
├── reference/                   # Template files
├── tests/                       # Validation test suite
│   ├── validate-structure.py    # Plugin structure validation
│   ├── validate-frontmatter.py  # YAML frontmatter checks
│   ├── validate-references.py   # Cross-reference checks
│   ├── validate-routing.py      # Signal table completeness
│   └── run-all.sh               # Test runner
├── .github/
│   └── workflows/
│       ├── validate.yml         # PR validation
│       └── release.yml          # Auto-release on main merge
├── ARCHITECTURE.md
├── CHANGELOG.md
├── README.md
├── ROADMAP.md
└── LICENSE
```

### G3. Installation and updates

**Employee installation**:
```bash
# From Claude Code
claude plugin install github:your-org/tars

# Or add marketplace first
claude plugin marketplace add your-org/tars-marketplace
claude plugin install tars@your-org
```

**Pushing updates**: When changes are merged to `main`, the CI/CD pipeline tags a release and updates the marketplace catalog. Employees pull updates with:
```bash
claude plugin update tars
```

### G4. Plugin manifest for distribution

The `plugin.json` must include fields required for marketplace distribution:

```json
{
  "name": "tars",
  "version": "2.0.0",
  "description": "Strategic intelligence framework with memory, task management, meeting processing, and analysis",
  "author": {"name": "Ajay John", "url": "https://github.com/ajayjohn"},
  "license": "Apache-2.0",
  "repository": "{REPOSITORY_URL}",
  "homepage": "{REPOSITORY_URL}#readme",
  "keywords": ["strategy", "meetings", "tasks", "memory", "analysis"],
  "skills": [...],
  "commands": [...]
}
```

### G5. Versioning strategy

Semantic versioning with change-type classification:
- **Patch** (3.0.x): Bug fixes in skill instructions, script fixes, documentation corrections
- **Minor** (3.x.0): New skill modes, new scripts, new reference templates, non-breaking improvements
- **Major** (x.0.0): Skill merges/splits, data format changes, breaking changes to workspace structure

---

## Part H: Automated testing and CI/CD

### H1. Plugin validation test suite

A set of Python scripts that validate the plugin structure, content, and cross-references. These run locally (pre-commit) and in CI (PR validation).

#### Test categories

| Test | Script | What it checks |
|---|---|---|
| Structure | `tests/validate-structure.py` | plugin.json is valid, all referenced skill/command files exist, directory structure matches spec |
| Frontmatter | `tests/validate-frontmatter.py` | Every SKILL.md has valid YAML frontmatter with required fields (name, description), every command has description |
| Cross-references | `tests/validate-references.py` | All skills listed in plugin.json exist on disk, all commands reference valid skills, routing table signals map to existing skills |
| Routing completeness | `tests/validate-routing.py` | Every workflow skill has at least one signal in the routing table, no orphaned signals (pointing to non-existent skills) |
| Data templates | `tests/validate-templates.py` | Reference files have valid structure, taxonomy.md defines all types used in skills, staleness tiers are documented |
| Script health | `tests/validate-scripts.py` | All scripts in scripts/ are executable, have shebangs, import only stdlib |

#### Dynamic test selection

Tests dynamically scope based on what changed. The test runner reads `git diff` to identify changed files and only runs relevant tests:

```
Changed files                    → Tests triggered
skills/**                        → frontmatter, cross-references, routing
commands/**                      → structure, cross-references
scripts/**                       → script health
reference/**                     → data templates
plugin.json                      → structure, cross-references
CHANGELOG.md                     → (none, documentation only)
```

If `--full` flag is passed, all tests run regardless of changes.

### H2. CI/CD pipeline

#### PR validation workflow (`.github/workflows/validate.yml`)

Runs on every PR that touches plugin files:
1. Checkout code
2. Detect changed files via `git diff`
3. Run relevant test subset
4. Verify version bump in plugin.json if skills or commands changed
5. Check that CHANGELOG.md was updated
6. Report results as PR check

#### Release workflow (`.github/workflows/release.yml`)

Runs on merge to `main`:
1. Run full test suite
2. Extract version from plugin.json
3. Create git tag (`v2.0.0`)
4. Create GitHub release with changelog excerpt
5. Build plugin archive (zip of the plugin directory, excluding tests/ and .github/)
6. Attach archive to GitHub release
7. Update marketplace catalog if applicable

### H3. Documentation auto-update

The CI pipeline includes a documentation step:
1. Generate skill inventory from plugin.json + YAML frontmatter
2. Update README.md skill list and command list sections
3. Update ARCHITECTURE.md with current file counts and structure
4. If docs changed, commit as `docs: auto-update from v{version}`

### H4. Local development workflow

```bash
# Install pre-commit hook
cp tests/pre-commit.sh .git/hooks/pre-commit

# Run tests manually
./tests/run-all.sh

# Run specific test
python tests/validate-frontmatter.py

# Run with full coverage
./tests/run-all.sh --full

# Bump version
python scripts/bump-version.py patch  # or minor, major
```

---

## Part I: Help documentation system

### I1. The problem

Users who install TARS need a way to learn what it can do and how to use it. Questions like "how do I process a meeting?" or "what does the memory system do?" should get immediate, accurate answers without the user needing to read skill source files.

### I2. Approach: Inline help + lightweight reference files

**Option selected: D+ (inline help metadata in each skill + two companion reference files)**

This approach was chosen over a dedicated help skill (creates drift), a monolithic help reference file (hard to maintain), or README-as-help (wrong audience). The key advantages are: help content lives next to implementation (no drift), only relevant help loads (token-efficient), and it scales to any number of skills.

### I3. Inline help metadata in YAML frontmatter

Every skill's SKILL.md gets an expanded YAML frontmatter block with a `help` section:

```yaml
---
name: meeting
description: Process meeting transcripts into structured reports, tasks, and memory updates
help:
  purpose: |
    Takes meeting transcripts and extracts key decisions, action items,
    follow-up topics, and summary points. Creates journal entries and
    updates the knowledge graph with new people and context.
  use_cases:
    - "Processing Zoom/Teams/Google Meet transcript"
    - "Extracting action items from meeting notes"
    - "Building organizational memory from recurring meetings"
  invoke_examples:
    - natural: "Here's a meeting transcript, process it"
    - natural: "Extract the key points from this call"
    - slash: "/meeting <paste transcript>"
  common_questions:
    - q: "What input formats work?"
      a: "Text transcripts, paste from any source. Speaker labels help but aren't required."
    - q: "How long can meetings be?"
      a: "Any length. Transcripts over 60 minutes may be processed in segments."
  related_skills: [tasks, learn, briefing]
---
```

The `help` section loads only when help is requested. During normal routing, only `name` and `description` load at L1 (~4 tokens). The help metadata adds ~50-80 tokens per skill when accessed, far cheaper than loading a centralized help file.

### I4. Companion reference files

**`reference/getting-started.md`** (~60 lines): Onboarding narrative for new users. Not a duplicate of skill help -- this covers the "what do I do first?" question that no individual skill answers. Contents: what is TARS (2 paragraphs), 5-minute quickstart (3 numbered steps pointing to skills), next steps (pointer to `/help` and natural language discovery).

**`reference/workflows.md`** (~80 lines): Common multi-skill patterns. Covers: meeting processing pipeline, weekly review workflow, strategic decision workflow, onboarding a new initiative. Each workflow is 5-8 lines listing the skill sequence with one-line explanations.

### I5. Help routing

The core skill's routing table includes help signals: "how do I", "what does", "help with", "what can you do". When triggered, TARS:
1. If the question is about a specific skill ("how do I process a meeting?"), load that skill's `help` frontmatter section and respond from it
2. If the question is general ("what can you do?"), list all skill names and descriptions (already loaded at L1) and point to `reference/getting-started.md`
3. If the question is about a workflow ("how do I do a weekly review?"), reference `reference/workflows.md`

No dedicated help skill is needed. The core skill handles help routing as one of its functions.

---

## Part J: Framework catalog for leadership adoption

### J1. Purpose

A standalone document designed to convince teams and leadership to adopt TARS. Not a technical manual -- a sales document that covers what TARS does, how it works under the hood, and why it's worth adopting. This document is the primary artifact for driving enterprise adoption.

### J2. Document: `CATALOG.md`

Create `CATALOG.md` at the plugin root. Structure:

**Section 1: Executive summary** (~200 words)
- What TARS is in one sentence
- The 3 core problems it solves (context loss, meeting follow-through, strategic rigor)
- Time savings estimate (e.g., "saves 3-5 hours/week per knowledge worker")

**Section 2: Capability overview** (~500 words, organized by user workflow)
- Morning routine: daily briefing pulls calendar, tasks, people context automatically
- Meeting processing: paste a transcript, get structured report + action items + memory updates in one step
- Strategic thinking: multi-persona debate (CPO/CTO council), adversarial stress-testing, Tree of Thoughts analysis
- Task management: extract accountable tasks from any conversation, automatic follow-up tracking
- Communications: stakeholder-aware drafting with tone adaptation and empathy audit
- Knowledge capture: wisdom extraction from articles, podcasts, and conversations
- Initiative management: planning, status reporting, KPI tracking

**Section 3: Under the hood** (~400 words)
- Memory architecture: persistent knowledge graph with 7 entity categories, wikilink connectivity, index-first search, durability-tested entries
- Archival system: 4-tier staleness classification (durable/seasonal/transient/ephemeral), automatic expiry of ephemeral facts, archive with unarchive capability
- Integration abstraction: provider-agnostic registry supporting any calendar, task, or project management tool via MCP, CLI, or HTTP API
- Token efficiency: 3-level loading model keeps session baseline at ~60 tokens. Full skill logic loads on-demand only
- Quality controls: BLUF mandate, anti-sycophancy, banned phrases, source attribution with confidence tiers, sensitive data guardrails (secrets/credentials/PII blocked via script-based scanning)
- Automated maintenance: daily housekeeping runs automatically (index validation, stale content detection, archive sweeps)

**Section 4: Natural language interface** (~200 words)
- Users don't need to memorize commands -- describe what you need and TARS routes to the right workflow
- Example interactions showing natural language → skill routing
- Slash commands available for power users who prefer explicit invocation

**Section 5: Security and compliance** (~200 words)
- No secrets, credentials, or PII stored (automated script-based scanning with configurable patterns)
- All data stays in the user's workspace (no cloud sync, no external API calls for data storage)
- Audit trail for guardrail decisions
- Apache 2.0 license

**Section 6: Getting started** (~100 words)
- Installation command
- Welcome flow takes 5 minutes
- First value within the first session
- Link to full documentation

### J3. Tone and format

Written for a mixed audience of technical leaders and non-technical executives. Avoids jargon where possible. Uses concrete examples over abstract descriptions. Includes a "day in the life" narrative showing how a product manager uses TARS across a typical workday.

---

## Part K: Plugin manifest and authorship protection

### K1. Expanded plugin.json

The plugin.json manifest must be expanded with all supported fields to establish authorship, enable distribution, and create a traceable attribution chain. In Phase 0, version is set to `1.5.0`; it is bumped to `2.0.0` only in Phase 9. The final v2.0.0 plugin.json should look like:

```json
{
  "name": "tars",
  "version": "2.0.0",
  "description": "Strategic intelligence framework with memory, task management, meeting processing, strategic analysis, and stakeholder communications. Turns Claude into a persistent, context-aware executive assistant.",
  "author": {
    "name": "Ajay John",
    "url": "https://github.com/ajayjohn"
  },
  "license": "Apache-2.0",
  "repository": "{REPOSITORY_URL}",
  "homepage": "{REPOSITORY_URL}#readme",
  "bugs": {
    "url": "{REPOSITORY_URL}/issues"
  },
  "keywords": [
    "strategy",
    "meetings",
    "tasks",
    "memory",
    "analysis",
    "briefings",
    "knowledge-graph",
    "executive-assistant",
    "claude-plugin"
  ],
  "contributors": [],
  "skills": ["..."],
  "commands": ["..."]
}
```

**Note for implementing agent**: All `{REPOSITORY_URL}` placeholders must remain as-is. AJ will replace them with the actual repository URL before publishing. The author name and URL (`https://github.com/ajayjohn`) are confirmed and should be preserved exactly. Do not add an email field to the author object.

### K2. Additional attribution files

**`LICENSE` file**: Verify Apache 2.0 license file exists at plugin root with correct copyright line: `Copyright 2026 Ajay John`. If missing or incomplete, create it with the full Apache 2.0 text.

**Copyright header in key files**: Add a comment block at the top of ARCHITECTURE.md, README.md, and CATALOG.md:
```
<!-- Copyright 2026 Ajay John. Licensed under Apache 2.0. See LICENSE. -->
```

**`NOTICE` file** (Apache 2.0 convention): Create `NOTICE` at plugin root:
```
TARS - Strategic Intelligence Framework for Claude
Copyright 2026 Ajay John

This product includes software developed by Ajay John (https://github.com/ajayjohn).
```

### K3. Marketplace entry

If the plugin is distributed via a marketplace, create `.claude-plugin/marketplace.json`:

```json
{
  "category": "productivity",
  "tags": ["enterprise", "strategy", "meetings", "knowledge-management"],
  "source": {
    "source": "url",
    "url": "{REPOSITORY_URL}.git"
  }
}
```

---

## Implementation phases

### Phase 0: Versioning, manifest, and attribution (30 minutes)

No dependencies. Must be done first to establish the correct version baseline. **After Phase 0, plugin.json version is `1.5.0`. After Phase 9 (final phase), version is bumped to `2.0.0` as the culminating release.**

1. Update `plugin.json` version from `2.0.0` to `1.5.0` (correcting the mislabeled version — the current state is v1.5.0, not v2.0.0)
2. Expand `plugin.json` with all fields specified in Part K1: author url (no email), repository, homepage, bugs, keywords, contributors
3. Update `CHANGELOG.md`: rename current "v2.0.0" entry to "v1.5.0", rename "v1.4.0" entry appropriately, add v2.0.0 placeholder for the upcoming release
4. Update `ARCHITECTURE.md` version references from v2.0.0 to v1.5.0
5. Verify `LICENSE` file exists with correct Apache 2.0 text and copyright line: `Copyright 2026 Ajay John`
6. Create `NOTICE` file at plugin root per Apache 2.0 convention (see Part K2)
7. Add copyright headers to ARCHITECTURE.md and README.md (see Part K2)
8. Create `.claude-plugin/marketplace.json` with category and source fields (see Part K3)

### Phase 1: Foundation and quick wins (1-2 hours)

Depends on: Phase 0 (version baseline must be correct).

1. ~~Fix `Account: CSI` in reference/integrations.md~~ (done)
2. Add proactive learning triggers to the routing/identity skill
3. Add AskUserQuestion reference to clarification skill
4. Add TodoWrite progress tracking instructions to multi-step skills (meeting-processor, deep-analysis)
5. Add context management directive ("offload intermediate results to files") to composite skills

### Phase 2: Script extraction (3-5 hours)

Depends on: nothing (can run parallel with Phase 1).

1. Write `scripts/health-check.py` (naming validation, frontmatter checks, index sync, wikilink detection, replacements coverage)
2. Write `scripts/rebuild-indexes.py` (parse frontmatter, generate YAML indexes)
3. Write `scripts/scaffold.sh` (directory creation, integration verification, template copying)
4. Write `scripts/sync.py` (schedule.md date checking, task tool overdue queries, orphan task scanning)
5. Write `scripts/archive.py` (staleness scanning, file moves, archive index updates, ephemeral line expiry)
6. Write `scripts/verify-integrations.py` (check each configured integration's health, update status)
7. Write `scripts/scan-secrets.py` (regex scan content against reference/guardrails.yaml patterns, return JSON report of matches with type, label, line number, action). Reads patterns from guardrails.yaml, accepts content via stdin or file path argument. Returns `{"clean": true}` or `{"clean": false, "matches": [...]}`.
8. Update these skills to invoke scripts and interpret results: `housekeeping` (invokes health-check.py, archive.py), `rebuild-index` (invokes rebuild-indexes.py), `setup` (invokes scaffold.sh, verify-integrations.py), `update` (invokes sync.py). Each skill should call the script via Bash, then interpret the output and present findings to the user.

### Phase 3: Data architecture (3-5 hours)

Depends on: Phase 2 (scripts/rebuild-indexes.py needed to generate new format).

1. Design and implement YAML-based index format (replace pipe-delimited tables)
2. Add `staleness` field to taxonomy.md and all frontmatter templates
3. Add `relationships` section to memory file frontmatter templates
4. Create consolidated master index (`memory/_index.md` with all entities)
5. Add ephemeral fact sections with `[expires:]` tags to person file template
6. Create `archive/` folder structure and `_archive_index.yaml`
7. Create `inbox/` folder structure (pending, processing, completed, failed)
8. Update `scripts/rebuild-indexes.py` to generate new YAML format
9. Update taxonomy.md with staleness tiers, relationship types, and new folder documentation
10. Create `reference/guardrails.yaml` with sensitive data patterns (secrets, credentials, PII) per Part E5 specification
11. Create `reference/maturity.yaml` template for onboarding progress tracking
12. Create `reference/.housekeeping-state.yaml` for automated maintenance tracking
13. Create `reference/getting-started.md` (~60 lines, onboarding narrative for new users, see Part I4)
14. Create `reference/workflows.md` (~80 lines, common multi-skill workflow patterns, see Part I4)

### Phase 4: Integration abstraction (2-3 hours)

Depends on: Phase 3 (data architecture must be stable).

1. Redesign `reference/integrations.md` as provider-agnostic registry with category/status/provider/type/operations/config/constraints format (see Part D2 for full registry schema)
2. Remove all hardcoded Eventlink and remindctl references from these skill files and replace with category-based references ("query calendar integration", "create task via task integration"): `briefing`, `process-meeting`, `manage-tasks`, `extract-tasks`, `initiative`, `update`, `setup`, `housekeeping`, `identity`, `routing`. Search all SKILL.md files for "Eventlink", "remindctl", "eventlink", "curl.*localhost" to catch any missed references.
3. Add MCP discovery logic: skills check `<mcp_servers>` at runtime for MCP-based integrations
4. Write `scripts/verify-integrations.py` to check health of each configured integration (curl for HTTP APIs, `which` for CLI tools, `<mcp_servers>` scan for MCPs)
5. Update integration registry documentation in taxonomy.md

### Phase 5: Skill consolidation (5-8 hours)

Depends on: Phase 4 (integration abstraction must be done so merged skills reference categories, not tools).

1. Create `skills/core/SKILL.md`: merge these 7 background skills into one file: `identity/SKILL.md`, `communication/SKILL.md`, `memory-management/SKILL.md`, `task-management/SKILL.md`, `decision-frameworks/SKILL.md`, `clarification/SKILL.md`, `routing/SKILL.md`. Add: global communication rules (BLUF, anti-sycophancy, banned phrases apply to ALL outputs), AskUserQuestion integration, proactive learning triggers, context management directive, sensitive data guardrails (invoke `scripts/scan-secrets.py` before persisting content, patterns from `reference/guardrails.yaml`), session-start housekeeping check directive (reference `reference/.housekeeping-state.yaml`), integration abstraction usage pattern (reference `reference/integrations.md` by category). Delete the 7 original skill directories after merge.
2. Create `skills/meeting/SKILL.md`: merge process-meeting + meeting-processor, add sub-agent parallelization, add inbox integration
3. Create `skills/tasks/SKILL.md`: merge extract-tasks + manage-tasks, ensure standalone extract mode
4. Create `skills/learn/SKILL.md`: merge extract-memory + extract-wisdom, ensure standalone memory extraction from conversation
5. Create `skills/think/SKILL.md`: merge 5 analysis skills, add sub-agent parallelization
6. Create `skills/briefing/SKILL.md`: add sub-agent data gathering, add inbox check, add archive report, add maturity status line
7. Create `skills/initiative/SKILL.md`: merge initiative + performance-report
8. Create `skills/maintain/SKILL.md`: merge housekeeping + rebuild-index + update, add archival sweep mode, add inbox processing mode, invoke scripts
9. Create `skills/welcome/SKILL.md` (replaces `skills/setup/SKILL.md` — delete setup after creating welcome). Redesign as progressive welcome flow with 3 internal phases:
   - **Welcome Phase 1 (instant setup, 0-2 min)**: Run `scripts/scaffold.sh` to create directories. Run `scripts/verify-integrations.py` to detect available integrations. If calendar configured, query past 2 weeks + upcoming week to auto-discover user's name, recurring meetings, frequent attendees. If tasks configured, query for existing tasks. Use AskUserQuestion with max 2 questions (role, org focus) — skip if inferrable from calendar data.
   - **Welcome Phase 2 (first win + essential profile, 2-5 min)**: Collect essential profile data using AskUserQuestion (max 2 questions per round, max 2 rounds). Round 1: name (skip if auto-discovered), team + manager. Round 2 (conditional on management role): direct reports/teams managed, top 1-3 initiatives. Then immediately demonstrate value: display calendar snapshot, populate `reference/replacements.md` with discovered names, create `memory/people/` entries from calendar attendees, create user's own profile entry, generate mini-briefing.
   - **Welcome Phase 3 (background learning, days 1-7)**: Add directives for passive learning: check for new calendar data each session, proactively extract memory when user corrects facts or shares context, infer org structure from meeting patterns (1:1s, team meetings), suggest filling gaps at end of day 1 and day 3.
10. Keep standalone: `skills/communicate/SKILL.md`, `skills/create/SKILL.md`, `skills/answer/SKILL.md`
11. Reduce commands/ from 23 to ~11 thin wrappers matching merged skills (including `/welcome` replacing `/setup`)
12. Update plugin.json with new skill and command references (version stays at `1.5.0` — bump to `2.0.0` happens in Phase 9)
13. Optimize all skill YAML descriptions for auto-triggering keywords
14. Add `help` section to every skill's YAML frontmatter (see Part I3 for schema: purpose, use_cases, invoke_examples, common_questions, related_skills). Each skill needs 5-10 lines of help metadata.
15. Add help routing signals to the core skill's routing table ("how do I", "what does", "help with", "what can you do") per Part I5

### Phase 6: Sub-agent optimization (3-5 hours)

Depends on: Phase 5 (merged skills must be in place).

1. Implement parallel sub-agents in meeting skill (task extraction || memory extraction)
2. Implement parallel sub-agents in think skill deep mode (validation || executive council)
3. Implement parallel sub-agents in briefing skill (calendar || tasks || memory)
4. Implement batch inbox processing with isolated sub-agents per item
5. Add TodoWrite progress tracking to all parallelized workflows
6. Document sub-agent input/output contracts in each skill

### Phase 7: Automated housekeeping (1-2 hours)

Depends on: Phase 5 (core skill and maintain skill must exist).

1. Add session-start housekeeping check logic to core skill (check `.housekeeping-state.yaml`, trigger if not run today)
2. Define what runs automatically vs user-initiated in maintain skill
3. Create Cowork shortcut for scheduled daily housekeeping (if environment supports it)
4. Test that housekeeping runs silently on first session of the day without disrupting user flow

### Phase 8: Testing and CI/CD (3-5 hours)

Depends on: Phase 7 (all implementation complete).

1. Write `tests/validate-structure.py` (plugin.json validity, file existence, directory structure)
2. Write `tests/validate-frontmatter.py` (YAML frontmatter on all skills and commands)
3. Write `tests/validate-references.py` (plugin.json ↔ disk, command ↔ skill, routing ↔ skill)
4. Write `tests/validate-routing.py` (every workflow skill has signals, no orphaned signals)
5. Write `tests/validate-templates.py` (reference file structure, taxonomy completeness)
6. Write `tests/validate-scripts.py` (scripts executable, stdlib-only imports)
7. Write `tests/run-all.sh` (test runner with `--full` flag and dynamic git-diff-based test selection)
8. Write `scripts/bump-version.py` (semantic versioning with major/minor/patch)
9. Create `.github/workflows/validate.yml` (PR validation with dynamic test selection and version check)
10. Create `.github/workflows/release.yml` (auto-tag, GitHub release, build archive, update marketplace)
11. Create `tests/pre-commit.sh` (local pre-commit hook for developers)
12. Add documentation auto-update step to release workflow

### Phase 9: Final testing, documentation, and catalog (3-4 hours)

Depends on: Phase 8 (test suite and CI/CD must be in place).

**Testing:**
1. Run full test suite against completed plugin (`./tests/run-all.sh --full`)
2. Test every natural language signal against the routing table
3. Test every slash command
4. Test welcome flow end-to-end (new user, progressive onboarding with profile collection, first win)
5. Test inbox processing with 3+ mixed items (transcript, email, article)
6. Test integration abstraction with different provider configurations
7. Test housekeeping auto-trigger on session start
8. Test archival: create ephemeral content, verify expiry, verify unarchive
9. Verify communication rules apply to all skill outputs
10. Verify sensitive data guardrails trigger correctly: test with content containing fake SSN, API key, JWT, password — confirm script detects and blocks. Test with content containing client names, deal values, contract terms — confirm these pass through freely.
11. Test help system: ask "how do I process a meeting?", "what can you do?", "help with tasks" and verify accurate responses from inline help metadata
12. Verify all skill `help` frontmatter sections are complete and accurate against actual skill behavior

**Documentation:**
13. Update ARCHITECTURE.md with v2.0 design decisions, new file structure, integration abstraction, help system, version history correction
14. Update README.md with simplified skill list, natural language examples, onboarding guide, help system reference
15. Update CHANGELOG.md: finalize v2.0.0 release notes covering all changes from v1.5.0
16. Create `CATALOG.md` at plugin root per Part J2 specification: executive summary, capability overview (7 workflow areas), under-the-hood architecture (memory, archival, integrations, token efficiency, quality controls, automated maintenance), natural language interface, security and compliance, getting started. Include "day in the life" narrative. Tone: mixed technical/executive audience per Part J3.
17. Verify `NOTICE` file, copyright headers, and `marketplace.json` are all present and correct
18. Verify plugin.json has all expanded fields (author url, repository, homepage, bugs, keywords — no email) per Part K1
19. Bump `plugin.json` version from `1.5.0` to `2.0.0` — this is the final release version
20. Create initial GitHub release with plugin archive (tag: `v2.0.0`)

---

## Risk assessment

| Risk | Mitigation |
|---|---|
| Merged skills become too long for effective LLM processing | Mode sections clearly delineated with headers. If a skill exceeds ~500 lines, split into sub-files loaded via L3. |
| Slash command removal confuses existing users | Option A preserves slash commands via thin wrappers with aliases in descriptions. |
| Scripts introduce dependencies | All scripts use Python standard library only. No pip installs. |
| Sub-agents increase complexity | Each sub-agent has documented input/output contracts. Failures don't crash main workflow. |
| Integration abstraction adds indirection | Skills reference categories with clear fallback logic. If integration unavailable, skip and note gap. |
| Welcome flow misses important context | Phase 3 (background learning) catches what Phase 1 misses. Progressive profiling ensures completeness over time. |
| Sensitive data guardrails produce false positives | Script-based regex scanning has predictable behavior. Patterns in guardrails.yaml are tunable. Only secrets/credentials/PII are blocked — business data (names, deals, contracts) passes freely. |
| Automated housekeeping disrupts user flow | Housekeeping deferred if user's request is urgent. Runs silently. Errors logged, not surfaced unless critical. |
| CI/CD pipeline blocks legitimate changes | Dynamic test selection reduces false blocks. `--full` flag for comprehensive checks. Clear error messages with fix suggestions. |
| Enterprise distribution version conflicts | Semantic versioning with clear major/minor/patch rules. CI enforces version bump on changes. |
| Help metadata drifts from skill behavior | Help lives in the same YAML frontmatter as the skill. Phase 9 includes verification step. Tests can validate help section presence. |
| Catalog overpromises capabilities | Catalog written after all implementation phases, reflecting actual v2.0 capabilities. Reviewed as part of Phase 9. |
| Welcome flow still asks too many questions | Strict 2-question-per-round limit, max 2 rounds. Manager/reportee questions conditional on role. Background learning catches the rest. |

---

## Success metrics

| Metric | v1.5.0 baseline | v2.0.0 target |
|---|---|---|
| Total skill files | 28 | ~15 |
| Total command files | 23 | ~11 |
| Session baseline tokens | ~115 | ~60 |
| Meeting processing wall-clock | Sequential | 30-40% faster |
| Housekeeping accuracy | LLM-dependent | Script-deterministic |
| Natural language routing accuracy | Good | Better (keyword-optimized descriptions) |
| New user onboarding | 4 rounds of questions, 10+ min | 2 questions, first win in 5 min |
| Stale content in active indexes | Grows unbounded | Auto-archived by staleness tier |
| Batch processing capability | One at a time, manual | Drop files, process all, isolated context |
| Communication quality consistency | Only in /communicate | All outputs follow BLUF + style rules |
| Index format editability | Pipe tables (alignment breaks) | YAML (editor-friendly) |
| Integration coupling | Hardcoded to Eventlink + remindctl | Provider-agnostic, any calendar/task tool |
| Sensitive data compliance | Manual vigilance | Script-based scanning blocks secrets/credentials/PII with audit trail |
| Maintenance burden on user | Must remember to run /update | Auto-triggers daily on session start |
| Plugin distribution | Manual file sharing | Git-based marketplace with auto-updates |
| Plugin validation | Manual review | Automated test suite with CI/CD |
| Time to first value (new user) | 10+ minutes after setup | Under 5 minutes |
| User help access | Read source files or README | Inline help metadata, natural language queries |
| Leadership adoption artifact | None | CATALOG.md with executive summary + capabilities |
| Authorship attribution | Name-only in plugin.json | Full author info, NOTICE, copyright headers, marketplace entry |
| Profile completeness at setup | Manual 4-round interrogation | Auto-discover + 2-round targeted questions, background learning |
