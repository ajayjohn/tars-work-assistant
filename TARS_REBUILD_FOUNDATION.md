# TARS rebuild foundation


## Executive summary


TARS exists to solve a simple but expensive problem: knowledge work is continuous, but most AI interactions are stateless. The framework tries to turn Claude from a one-off responder into a persistent operating layer for a knowledge worker's day. It combines organizational memory, task accountability, meeting processing, briefings, strategic reasoning, communication support, and maintenance into one system.


The key idea is not "chat with an AI." The key idea is "give the AI a durable workspace, rules for what deserves to be remembered, rules for what deserves to become a task, and workflows that turn raw inputs into structured outputs."


For an Obsidian rebuild, the right move is to preserve TARS's operating model, not every literal implementation detail. The durable value is in the abstractions:


- persistent memory over time
- structured journal outputs
- integration-aware workflow orchestration
- explicit reasoning and accountability protocols
- maintenance and trust mechanisms


The current repo is strong conceptually, but uneven operationally. Some parts are well-specified and testable, while others remain prompt-defined, duplicated, or in migration. A rebuild should keep the conceptual architecture and replace brittle mechanics with Obsidian-native implementations.


## What TARS is really trying to be


TARS is best understood as a knowledge work operating system built on top of Claude.


It is trying to give a knowledge worker:


- a memory layer for people, initiatives, decisions, products, vendors, and organizational context
- an execution layer for tasks, follow-through, and due dates
- a reflection layer for analysis, debate, and decision quality
- a communication layer for stakeholder-aware drafting
- an intake layer for meetings, articles, notes, and inbox material
- a maintenance layer that keeps the workspace healthy without constant manual care


The repo repeatedly frames TARS as a persistent executive assistant rather than a prompt library. That is the central design thesis.


## The core gaps TARS aims to fill for a knowledge worker


| Gap | What the gap looks like in real work | How TARS tries to fill it |
|-----|--------------------------------------|----------------------------|
| Context loss | People ask for the same information repeatedly. Decisions lose their rationale. Relationship details are forgotten. | Persistent memory files, entity indexes, name normalization, and retrieval-first workflows |
| Meeting follow-through | Meetings create decisions and action items, but ownership and context scatter immediately afterward. | Meeting pipeline that turns transcript -> journal -> tasks -> memory |
| Fragmented systems | Calendar, tasks, notes, docs, and org knowledge live in different places and do not talk to each other. | Provider-agnostic integration layer plus a unified workspace model |
| Weak strategic rigor | Teams jump to solutions, under-test assumptions, and let politics or recency drive decisions. | Think skill modes: analysis, validation, executive council, deep analysis, discovery |
| Communication mismatch | The same update lands badly with executives, peers, and direct reports. | Stakeholder-aware drafting, empathy audit, and RASCI enforcement |
| Knowledge decay | Articles, podcasts, transcripts, and conversations produce insights that are never retained. | Learn skill for durable memory extraction and wisdom capture |
| Initiative drift | Big efforts lose structure, KPI visibility, and historical continuity. | Initiative planning, status, and performance reporting |
| Workspace entropy | Indexes drift, names get inconsistent, archive-worthy content accumulates, inboxes pile up. | Maintain skill, scripts, state files, and housekeeping |
| Trust and safety | AI systems over-store, mis-name, or expose sensitive information. | Durability test, accountability test, index-first lookup, secret scanning, guarded persistence |


## How TARS is structured today


TARS is a layered system.


| Layer | Role in the framework | Main artifacts |
|------|------------------------|----------------|
| Behavioral core | Defines identity, routing, communication rules, memory protocol, task protocol, and clarification rules | `skills/core/SKILL.md` |
| Workflow skills | Domain workflows users actually invoke | `skills/*/SKILL.md`, `commands/*.md` |
| Reference model | Shared configuration, taxonomy, replacements, KPIs, schedule, integrations, guardrails, workflows | `reference/*` |
| Workspace state | User-specific persistent data | `memory/`, `journal/`, `contexts/`, `inbox/`, `archive/`, `CLAUDE.md` |
| Deterministic operations | Repeatable scripts for scaffolding, validation, indexing, sync, archive, secret scan, updates | `scripts/*` |
| Quality gates | Validation scripts for docs, frontmatter, routing, templates, scripts, and structure | `tests/*` |
| Distribution layer | Plugin packaging and mirrored copies for Claude environments | `.claude-plugin/`, `tars-cowork-plugin/`, `build-plugin.sh` |


The intended user loop is:


1. Ingest raw work input.
2. Normalize names and resolve context.
3. Decide what becomes memory, what becomes a task, and what becomes journal output.
4. Persist it in a searchable structure.
5. Retrieve it later for briefings, answers, analysis, and communication.
6. Run maintenance so the system stays usable over time.


## Capability inventory


This section is the most important rebuild input. Each capability is listed with what it does, why it matters, how it works now, whether it belongs in the Obsidian rebuild, and how it should be implemented there.


### Foundational platform capabilities


| Capability | What it does now | Why it helps the knowledge worker | How it works now | Obsidian rebuild applicability | Recommended Obsidian implementation |
|-----------|------------------|-----------------------------------|------------------|-------------------------------|-------------------------------------|
| Natural-language routing | Maps user intent to the correct workflow skill | Lets the user ask for work in plain language instead of memorizing commands | Signal table in `skills/core/SKILL.md`, thin slash-command wrappers in `commands/` | Keep | Implement as an intent router over Obsidian commands, chat actions, and contextual suggestions |
| Core operating rules | Enforces BLUF, anti-sycophancy, clarification rules, source priorities, and shared constraints | Makes the assistant consistent and trustworthy across workflows | Centralized in `skills/core/SKILL.md` | Keep | Preserve as system-level policies and app logic, not just prompt text |
| Memory graph and taxonomy | Organizes knowledge into people, initiatives, decisions, products, vendors, competitors, and organizational context | Gives the worker durable continuity about people, projects, and prior decisions | Markdown files plus taxonomy in `reference/taxonomy.md` and indexes in `memory/*/_index.md` | Keep | Keep the entity model; use frontmatter, links, and Obsidian-native metadata queries |
| Index-first retrieval | Forces the system to consult indexes before opening full files | Keeps retrieval scalable and focused as the vault grows | Defined in multiple skills, supported by `rebuild-indexes.py` | Keep conceptually | Replace manual index files where possible with generated indexes, cached metadata, or Dataview-style query layers |
| Name normalization | Maps nicknames, abbreviations, and variants to canonical names | Prevents memory fragmentation and task duplication | `reference/replacements.md` plus required pre-processing in most skills | Keep | Store canonical aliases in a dedicated note or settings-backed registry, surfaced in UI for correction |
| Name resolution protocol | Resolves ambiguous or unknown names using context before asking the user | Prevents bad memory writes and broken links | Defined in `skills/core/SKILL.md`; often uses calendar attendees and memory indexes | Keep | Implement a resolver service that suggests matches from vault entities, attendees, and aliases before prompting |
| Durability test | Filters whether something deserves memory persistence | Stops the system from becoming a noisy event log | Four-part test in core and learn skills | Keep | Make this a first-class save-to-memory gate in the UI and agent logic |
| Accountability test | Filters whether something deserves task creation | Prevents vague wishes from becoming fake tasks | Defined in core and tasks/meeting/learn pipelines | Keep | Make task extraction reviewable, with explicit owner, due date, and done-state requirements |
| Provider-agnostic integrations | Abstracts calendar and task providers behind categories rather than vendor names | Avoids lock-in and keeps workflows portable | `reference/integrations.md`, MCP-first guidance, script validation | Keep | Implement adapter interfaces for calendar, tasks, project tracker, and docs; settings choose the adapter |
| Journal persistence | Saves workflow outputs into durable time-based records | Creates an auditable history of meetings, briefings, analyses, and learning | Most workflows write to `journal/YYYY-MM/` | Keep | Keep journal output as Obsidian notes with type-based templates and backlinks |
| Visible progress tracking | Shows progress for long workflows | Reduces user anxiety during multi-step automation | Prompt-level TodoWrite instructions in skills | Keep | Replace with a native job status panel, task queue, or progress notifications |
| Parallel workflow orchestration | Splits independent subtasks into parallel workers | Shortens wall-clock time for complex workflows | Prompt-defined sub-agents in meeting, briefing, think, and maintain | Keep conceptually | Rebuild as async job orchestration rather than prompt-only sub-agents |
| Locking and write coordination | Prevents concurrent memory writes from colliding | Protects data integrity in multi-step flows | `.lock` file convention described in core | Keep | Replace with an internal write queue or transaction manager for vault writes |
| Help metadata | Provides inline help without loading all workflow detail | Makes the system self-teaching | YAML frontmatter in each skill | Keep | Store per-command help metadata in plugin manifests or command definitions |
| Maturity tracking | Tracks how far the system has been hydrated with real context | Gives the user a sense of progress and missing depth | `reference/maturity.yaml`, surfaced in briefing | Optional but useful | Keep as onboarding telemetry and encouragement, but avoid making it feel gamified for its own sake |


### User-facing workflow capabilities


| Capability | What it does now | Why it helps the knowledge worker | How it works now | Obsidian rebuild applicability | Recommended Obsidian implementation |
|-----------|------------------|-----------------------------------|------------------|-------------------------------|-------------------------------------|
| Answer / fast lookup | Answers schedule, task, people, initiative, and context questions quickly | Gives instant recall without forcing the user to search manually | `skills/answer/SKILL.md`, source hierarchy: memory -> tasks -> journal -> contexts -> MCP/web | Keep | Build a fast retrieval layer over vault metadata plus configured integrations |
| Daily briefing | Produces a morning orientation snapshot | Reduces context-switching cost at the start of the day | `skills/briefing/SKILL.md`, calendar + tasks + memory + schedule + housekeeping state | Keep | Make this a flagship dashboard/note view in Obsidian, not just a chat response |
| Weekly briefing | Produces a planning and review briefing for the week | Helps the worker step back from the daily grind and reorient strategically | Same skill, weekly mode, adds last-week review and upcoming-week planning | Keep | Keep as a generated weekly note with cross-links to meetings, tasks, and initiatives |
| Meeting processing | Converts transcript or notes into a structured journal entry, tasks, and memory updates | Solves the highest-value workflow in the system: meeting follow-through | `skills/meeting/SKILL.md`, with calendar enrichment and parallel task/memory extraction | Keep, high priority | Rebuild as a guided pipeline with transcript import, reviewable outputs, and one-click save actions |
| Task extraction | Extracts tasks from freeform input | Captures commitments wherever they appear | `skills/tasks/SKILL.md`, extract mode, duplicate checks, placement logic, verification | Keep | Implement extraction review UI with dedupe suggestions and task-system sync |
| Task management | Shows current tasks and supports completion, reprioritization, and pruning | Gives the assistant a real execution surface, not just note capture | Same skill, manage mode | Keep | Integrate with task adapters and optionally Obsidian Tasks or external systems |
| Memory extraction | Saves durable facts from conversation or user correction | Keeps relationship, org, and decision memory current | `skills/learn/SKILL.md`, memory mode | Keep | Make "save to memory" an explicit, reviewable action with suggested destination and aliases |
| Wisdom extraction | Extracts reusable insights from articles, podcasts, and learning material | Converts passive reading into retained knowledge | Learn skill, wisdom mode, with journal output plus memory/task side effects | Keep | Implement as note-to-note distillation with optional memory/task creation |
| Strategic analysis | Performs structured analysis with frameworks, branches, constraints, and synthesis | Improves decision quality beyond gut feel | `skills/think/SKILL.md`, Mode A | Keep | Keep as a premium workflow; output should be a note with assumptions, risks, and recommendation |
| Validation council | Stress-tests an idea from hostile angles | Surfaces risks early, before execution or stakeholder exposure | Think Mode B with CFO/CTO/competitor/customer critiques | Keep | Implement as an optional "challenge this" mode on any initiative or proposal note |
| Executive council | Simulates a CPO/CTO-style debate | Helps the user model internal organizational conflict and trade-offs | Think Mode C plus `skills/think/manifesto.md` | Keep conceptually | Keep the pattern, but let persona packs be configurable rather than hardcoded |
| Deep analysis chain | Orchestrates strategy + validation + executive debate | Produces the strongest strategic output in the framework | Think Mode D with saved intermediate files and parallel sub-agents | Keep | Rebuild as a chained workflow with intermediate note artifacts and resumable stages |
| Discovery mode | Refuses to solve too early and instead maps context and unknowns | Protects the user from premature solutioning | Think Mode E | Keep | Make this an explicit "discovery-first" mode for messy problems, especially in planning and strategy |
| Initiative planning | Scopes new initiatives, milestones, dependencies, risks, and effort profile | Gives large efforts structure early | `skills/initiative/SKILL.md`, planning mode | Keep | Represent initiatives as first-class notes with linked milestones, stakeholders, and decisions |
| Initiative status | Summarizes health, blockers, progress, and recent decisions | Keeps active work legible | Initiative status mode using memory, project tracker, and journal inputs | Keep | Implement as a generated initiative status note or view |
| Initiative performance | Generates KPI-driven trend reports | Adds evidence and accountability to initiative review | Initiative performance mode plus `reference/kpis.md` | Keep, later phase | Build once data adapters and KPI definitions exist; not first-release critical |
| Stakeholder communication drafting | Drafts audience-aware communications and enforces empathy and RASCI | Helps the worker communicate clearly across levels | `skills/communicate/SKILL.md` plus stakeholder memory | Keep | Integrate with note-based drafts and optional outbound connectors; keep empathy/RASCI checks |
| Text refinement | Refines raw text without changing intent | Provides lightweight editing support without requiring full workflow context | `skills/communicate/text-refinement.md` | Keep | Useful as a standalone editor command inside Obsidian |
| Artifact creation | Produces decks, narratives, and speeches | Extends TARS from operations into executive storytelling | `skills/create/SKILL.md` | Keep, but later | Implement after the core memory + briefing + meeting loops are solid |
| Welcome / onboarding | Scaffolds workspace, integrations, and initial organizational context | Makes the system usable without manual setup drudgery | `skills/welcome/SKILL.md` plus `scripts/scaffold.sh` and integration checks | Keep, high priority | Replace prompt-heavy onboarding with a proper setup wizard and vault migration flow |


### Operational and governance capabilities


| Capability | What it does now | Why it helps the knowledge worker | How it works now | Obsidian rebuild applicability | Recommended Obsidian implementation |
|-----------|------------------|-----------------------------------|------------------|-------------------------------|-------------------------------------|
| Health check | Scans for naming, frontmatter, index, link, and replacements issues | Prevents the workspace from silently degrading | `skills/maintain/SKILL.md`, `scripts/health-check.py` | Keep | Implement as a vault diagnostic report with actionable fixes |
| Sync | Checks schedules, tasks, and memory gaps | Keeps the vault aligned with current work reality | `skills/maintain/SKILL.md`, `scripts/sync.py` | Keep | Build as a synchronization service with review queue, not a hidden side effect |
| Rebuild indexes | Regenerates index files from actual content | Recovers from drift and supports retrieval performance | `scripts/rebuild-indexes.py` | Keep conceptually | Prefer generated caches or metadata views over hand-maintained index notes |
| Inbox processing | Batch-processes mixed raw inputs | Gives the user a low-friction intake funnel | Maintain inbox mode with pending/processing/completed/failed queues | Keep, high priority | Obsidian should have an inbox folder plus a processing queue UI and per-item review |
| Reference-file update | Migrates workspace templates while preserving user data | Lets the framework evolve without destroying local knowledge | `scripts/update-reference.py` and maintain update mode | Keep | Rebuild as a plugin migration engine for templates, settings, and note schemas |
| Automatic housekeeping | Runs archive, health, and sync checks regularly | Reduces maintenance burden and keeps the system trustworthy | Core session-start logic plus `.housekeeping-state.yaml` | Keep | Use scheduled/background jobs and vault-open hooks, with quiet notifications |
| 4-tier archival | Distinguishes durable, seasonal, transient, and ephemeral information | Keeps the active knowledge base relevant without losing history | `reference/taxonomy.md`, `scripts/archive.py` | Keep | Preserve the concept, but implement it as metadata-driven lifecycle management in notes |
| Sensitive-data guardrails | Scans for secrets and PII before persistence | Reduces accidental harmful storage | `reference/guardrails.yaml`, `scripts/scan-secrets.py` | Keep, high priority | Enforce pre-save scanning and user review for risky content |
| Testing and validation | Checks docs, routing, frontmatter, references, templates, scripts, and structure | Increases framework reliability and maintainability | `tests/*`, GitHub workflows | Keep | Obsidian rebuild should keep schema validation, migration tests, and vault fixture tests |
| Packaging and distribution | Packages the framework for Claude environments | Makes the framework installable and updatable | `.claude-plugin/`, `tars-cowork-plugin/`, `build-plugin.sh` | Redesign | Replace duplicate trees with a single source of truth and generated build artifacts |


## What is strongest in the current framework


- The framework has a clear thesis. It is not a bag of disconnected prompts.
- The memory and task gates are strong. The durability test and accountability test are among the most valuable ideas in the repo.
- The meeting workflow is the highest-value automation in the system and is specified in enough detail to rebuild with confidence.
- The system treats journal output as a first-class artifact, which is exactly right for Obsidian.
- The integration abstraction is strategically correct. A rebuild should not be tied to one task manager or calendar.
- The framework understands that trust comes from constraints, not just capability. Name normalization, wikilink verification, task verification, and source priorities all contribute to that.
- Maintenance is treated as product functionality, not as a hidden developer concern. That is unusual and valuable.


## What one live deployment demonstrates in practice


This workspace is useful because it shows the framework under real load rather than idealized usage. The numbers matter less than the shape of adoption, but they are still telling: roughly 96 journal files, 145 indexed memory entities, 40 decision notes, 44 context files, and an actively used transcript inbox over a relatively short period.


The important lesson is that the framework did not succeed or fail uniformly. It became very strong in some loops, somewhat useful in others, and clearly weak in a few places that the rebuild should not gloss over.


### What clearly worked in real usage


- **Meeting processing became the center of gravity.** This deployment contains 51 `meeting` journal notes, and many of them use a repeatable shape: updates, concerns, decisions, and action items. In practice, this is the most successful part of TARS because it matches a real pain point and produces artifacts the user actually wants to keep.
- **The journal-to-memory loop sometimes completed end to end.** `journal/2026-03/2026-03-18-meeting-primary-fi-cohort.md` produced a clean downstream decision artifact in `memory/decisions/2026-03-18-primary-fi-dbi-design.md`. Person and initiative memory also show real updates from live conversations, for example `memory/people/hilary-okitia.md` and `memory/initiatives/external-tool-integration.md`.
- **The memory graph created real continuity.** A vault with 68 people, 22 initiatives, and 40 decisions is already enough to materially improve meeting prep, briefing quality, and follow-up conversations. This validates the core memory model.
- **Uncertainty was sometimes handled correctly instead of being papered over.** `journal/2026-02/2026-02-23-meeting-dbi-prototype-walkthrough.md` explicitly includes an `Unverified Wikilinks` section. `journal/2026-03/2026-03-18-daily-briefing.md` explicitly flags people who are "not in memory index." That behavior is worth preserving because it increases trust.
- **Briefings were valuable when upstream context existed.** `journal/2026-03/2026-03-18-daily-briefing.md` is a strong example of TARS doing what it is supposed to do: fusing schedule, people context, task pressure, and initiative risk into one actionable output.


### What partly worked, but did not fully operationalize


- **Briefings were useful but not habitual in the same way meetings were.** The workspace has only 3 daily briefings and 5 weekly briefings over the same period. That suggests briefings are genuinely valuable, but not yet frictionless or embedded enough to become a default behavior.
- **Artifact and strategy support were clearly used, but mostly as note generation.** The `contexts/artifacts/` tree shows real value in deck prep, narrative shaping, and strategic thinking. But the loop is mostly note creation, not a tightly integrated operating cycle.
- **Memory freshness was mixed.** Some active people and initiatives were updated quickly; others kept appearing in later journals without their memory files being refreshed. In practice, "save to memory" happened enough to be helpful, but not enough to be consistently trustworthy.


### What did not really land in practical use


- **The task system did not become a trustworthy local control plane.** The journal contains 119 unchecked task checkboxes, but the workspace does not preserve a durable, inspectable local audit trail of task creation and verification. The notes clearly surfaced tasks; they did not reliably prove that the tasks were created, synced, deduped, or completed.
- **Maintenance existed conceptually more than operationally.** `reference/schedule.md` is empty, and `reference/.housekeeping-state.yaml` shows only one maintenance run as of 2026-03-18. The framework could describe hygiene, but it was not keeping itself healthy continuously.
- **Schema discipline degraded under real usage.** Journal notes use overlapping types such as `meeting`, `briefing-weekly`, `briefing-daily`, `journal`, `1:1`, `planning-meeting`, `strategic-review`, and `team-meeting`. `journal/2026-03/2026-03-05-meeting-hilary-aj-1on1.md` is a concrete example of drift: it is clearly a meeting note, but its `type` is `journal`, and its `source_file` metadata is mislabeled.
- **Name normalization helped, but write-time enforcement was too weak.** Real notes still contain noncanonical or unresolved links such as `[[Jeremy]]`, `[[Dan]]`, `[[Duke]]`, `[[MCP Initiative]]`, `[[Build FI Model Project]]`, and `[[Product Management Team]]`. This is a practical warning that alias management cannot live only in a replacement table.
- **Source hygiene became inconsistent over time.** Some notes point to `inbox/completed/...`, some to `inbox/processing/...`, some use `source: inbox`, some `source: transcript`, and some `source_file:`. The pipeline still worked for the user, but it was operating more by convention than by strong schema.


### Practical rebuild implications from this deployment


- Optimize first for the meeting -> journal -> memory loop. That is where the strongest real adoption happened.
- Treat task verification as a first-class product feature, not a promised side effect. If the user cannot inspect what was created and confirm sync state, the task loop will stay second-class.
- Put schema enforcement, alias resolution, and link validation in the application layer. Real usage will drift faster than documentation can keep up.
- Make maintenance ambient, low-friction, and reviewable. Users will not run manual hygiene often enough to prevent entropy.
- Prefer explicit unresolved states over silent bad links or guessed entities. The live deployment shows that this improves trust.
- Measure success by closed loops, not generated notes. A polished note without a verified downstream effect is only a partial success.


These examples should inform the rebuild as product lessons, not as implementation quirks to copy literally. The point is not to rebuild one person's vault. The point is to preserve the parts of TARS that held up under real work and redesign the parts that only worked when the prompts were followed perfectly.


## The critical weaknesses and inconsistencies in the current repo


These are important because they show which parts of TARS are durable ideas and which parts should not be copied blindly.


### 1. The framework is conceptually stronger than its current implementation


Much of TARS is defined in prompt protocols rather than in deterministic code. That means:


- the workflows are rich, but many guarantees are social or prompt-level rather than enforced in application logic
- side effects are specified in detail, but not all are mechanically implemented
- concurrency, locking, and verification are often described rather than systemically enforced


For the rebuild, treat the prompt protocols as product requirements, not as the final implementation.


### 2. There is source-of-truth drift across duplicated trees


The repo contains multiple copies of the framework:


- root `skills/`, `commands/`, `reference/`
- packaged `.claude-plugin/`
- `tars-cowork-plugin/`
- older compatibility material in `antigravity-wrapper/`


The copies have diverged. For example:


- root skills and `.claude-plugin/skills` are not fully in sync
- root `reference/workflows.md` is newer than `.claude-plugin/reference/workflows.md`
- build packaging is present, but the packaged copy is not consistently regenerated


This makes it unclear which version is canonical. A rebuild should enforce one source tree and generate everything else.


### 3. Documentation and implementation are still mid-migration


Important inconsistencies are visible in the repo:


- `skills/core/SKILL.md` still references `/bootstrap`, which no longer exists
- `README.md`, `ARCHITECTURE.md`, and the scripts disagree in places about index formats and workflow details
- the welcome flow is described as a simplified progressive onboarding, but the actual skill still contains a fairly large interview flow
- some packaged files contain newer housekeeping logic than the root copies


This means the repo is partially documenting the intended future state, not only the present state.


### 4. Integration migration is incomplete


The framework positions itself as MCP-first and provider-agnostic, but implementation still carries legacy assumptions.


Examples:


- `GETTING-STARTED.md` and the skills emphasize MCP servers
- `scripts/scaffold.sh` still checks `remindctl` and Eventlink-style URLs
- integration verification is only partially aligned with the MCP-first story


This suggests that the integration abstraction is the right direction, but the migration is not fully complete. The rebuild should finish the abstraction instead of preserving legacy provider assumptions.


### 5. The plugin manifest is under-specified relative to the repo


`.claude-plugin/plugin.json` contains only minimal metadata and does not list skills or commands. This is enough for some packaging uses, but the validation scripts flag the gap and it weakens discoverability and consistency.


For a rebuild, the manifest should be authoritative and machine-complete.


### 6. The test runner is not portable on the target platform


`tests/run-all.sh` uses Bash associative arrays and fails under macOS's default Bash 3.2. That is a practical operational issue, not just a cosmetic one.


This matters because TARS is clearly intended for macOS-heavy knowledge workers, and task/calendar examples in the repo reinforce that. A rebuild should avoid environment assumptions that break the local toolchain.


### 7. Licensing is internally inconsistent


The repo currently presents conflicting license signals:


- `LICENSE` is PolyForm Noncommercial 1.0.0
- `README.md` points to PolyForm Noncommercial
- `ARCHITECTURE.md` header says Apache 2.0
- `CATALOG.md` claims Apache 2.0 in its security section
- `.claude-plugin/plugin.json` says `"license": "Apache-2.0"`


This is a significant governance issue. A rebuild must resolve licensing and distribution terms before broader adoption.


### 8. The index story is conceptually right but mechanically noisy


The system is right to insist on structured retrieval, but the current mechanics are mixed:


- older docs and templates still show markdown tables
- scripts like `rebuild-indexes.py` now generate YAML-style indexes
- skills still refer to indexes in a way that assumes consistent formatting


In Obsidian, this should become a cleaner metadata-query layer rather than a manually curated index-note burden.


### 9. Some guarantees are written down but not globally enforced


Examples:


- secret scanning exists, but not every content-ingestion path clearly invokes it
- auto-updates and housekeeping behavior differ between root and packaged core copies
- task verification is well described, but still depends on the workflow following the prompt precisely


The rebuild should move critical guarantees into deterministic pre-save and post-write hooks.


## What absolutely should survive the rebuild


These are the most valuable parts of TARS and should be treated as non-negotiable design principles.


- The memory model: people, initiatives, decisions, products, vendors, competitors, organizational context
- The durability test for memory
- The accountability test for tasks
- Meeting processing as a first-class end-to-end pipeline
- Daily and weekly briefings as first-class outputs
- Journal-first persistence of meaningful outputs
- Provider-agnostic integration architecture
- Name normalization and ambiguity resolution
- Strategic thinking modes that explicitly challenge assumptions
- Stakeholder-aware communication support
- Workspace maintenance, archival, and health diagnostics
- Guardrails around sensitive data and bad persistence


## What should be redesigned, not copied


- Prompt-only sub-agent orchestration should become real async workflow execution
- Manual or duplicated index files should become generated or query-backed structures
- Duplicate distribution trees should collapse into one canonical source tree
- Session-start housekeeping logic should become a scheduled/background service with reliable notifications
- `.lock` file conventions should become proper write coordination inside the plugin
- Template updates should become migration logic, not mostly textual merges
- Slash commands should be optional; command palette actions, note actions, and contextual UI should do most of the work in Obsidian


## Obsidian rebuild recommendations by layer


### 1. Data model


Use Obsidian notes as the durable source of truth, with frontmatter schemas for:


- people
- initiatives
- decisions
- products
- vendors
- competitors
- organizational context
- meetings
- briefings
- wisdom notes
- generated artifacts


Prefer backlinks, frontmatter, and generated views over hand-maintained tables.


### 2. Retrieval model


Keep index-first as a principle, but implement it as:


- cached metadata registry
- frontmatter queries
- alias map
- link graph traversal


Do not require users to maintain index notes manually unless they want human-readable registry notes for browsing.


### 3. Workflow engine


Build the main flows as explicit jobs:


- process meeting
- generate daily briefing
- generate weekly briefing
- extract memory
- extract tasks
- analyze decision
- process inbox


Each job should have:


- input
- intermediate state
- reviewable outputs
- success/failure status
- resumability


### 4. Integration layer


Treat calendar, tasks, docs, and project trackers as adapters. The workflow layer should only know categories and capabilities, not vendor names.


### 5. Review surfaces


Any workflow that creates or mutates durable state should have a review step for:


- memory additions
- task creation
- name resolution
- risky guardrail flags
- archive actions


This is especially important in Obsidian, where the vault is the long-term source of truth.


### 6. Maintenance layer


Build diagnostics and maintenance directly into the plugin:


- health scan
- stale content review
- broken link/entity review
- alias coverage review
- inbox queue review
- migration status


Maintenance should feel like part of the product, not a developer-only tool.


## Suggested rebuild priorities


### Phase 1: Must-have foundation


- vault schema and entity model
- onboarding wizard
- memory save/retrieve flows
- name normalization and resolution
- daily briefing
- meeting processing
- task extraction and sync
- journal outputs
- health diagnostics


### Phase 2: High-value expansion


- weekly briefing
- inbox processing
- strategic analysis modes
- stakeholder communication drafting
- archival lifecycle
- background housekeeping


### Phase 3: Advanced and enterprise features


- initiative performance and KPI reporting
- artifact generation
- richer multi-provider adapter ecosystem
- migration engine for templates and schemas
- deeper compliance and audit surfaces


## Bottom line for the rebuild


TARS is valuable because it recognizes that a knowledge worker's problem is not "I need better answers." The real problem is "I need continuity, structure, follow-through, and strategic rigor across time."


The rebuild should therefore preserve TARS as:


- a persistence system
- a workflow system
- a reasoning system
- a maintenance system


It should not preserve TARS as:


- a pile of duplicated plugin folders
- a prompt-only orchestration scheme
- a manually synchronized index ecosystem
- a partially migrated integration layer


If rebuilt well for Obsidian, TARS can become stronger than the current framework because Obsidian is naturally aligned with its best ideas: durable notes, links, metadata, historical journaling, and user-owned knowledge.


## Evidence reviewed


Primary sources consulted in this repo:


- `README.md`
- `ARCHITECTURE.md`
- `GETTING-STARTED.md`
- `CATALOG.md`
- `CHANGELOG.md`
- `skills/core/SKILL.md`
- `skills/meeting/SKILL.md`
- `skills/tasks/SKILL.md`
- `skills/learn/SKILL.md`
- `skills/briefing/SKILL.md`
- `skills/answer/SKILL.md`
- `skills/think/SKILL.md`
- `skills/think/manifesto.md`
- `skills/initiative/SKILL.md`
- `skills/communicate/SKILL.md`
- `skills/communicate/text-refinement.md`
- `skills/create/SKILL.md`
- `skills/welcome/SKILL.md`
- `skills/maintain/SKILL.md`
- `reference/integrations.md`
- `reference/taxonomy.md`
- `reference/workflows.md`
- `reference/guardrails.yaml`
- `reference/maturity.yaml`
- `reference/.housekeeping-state.yaml`
- `scripts/scaffold.sh`
- `scripts/health-check.py`
- `scripts/rebuild-indexes.py`
- `scripts/sync.py`
- `scripts/archive.py`
- `scripts/scan-secrets.py`
- `scripts/update-reference.py`
- `scripts/verify-integrations.py`
- `tests/validate-docs.py`
- `tests/validate-references.py`
- `tests/validate-routing.py`
- `tests/validate-scripts.py`


Repository observations that materially informed the critique:


- root source and `.claude-plugin/` copies have drifted
- `tests/run-all.sh --full` fails on macOS Bash 3.2 because it uses associative arrays
- license signals conflict across `LICENSE`, docs, and plugin metadata


Live workspace observations that materially informed the critique:


- `memory/_index.md`
- `reference/replacements.md`
- `reference/schedule.md`
- `reference/.housekeeping-state.yaml`
- `journal/2026-03/2026-03-18-daily-briefing.md`
- `journal/2026-03/2026-03-18-meeting-hilary-aj-1on1.md`
- `journal/2026-03/2026-03-18-meeting-primary-fi-cohort.md`
- `journal/2026-03/2026-03-05-meeting-hilary-aj-1on1.md`
- `journal/2026-03/2026-03-02-weekly-briefing.md`
- `journal/2026-02/2026-02-11-transcript-analysis.md`
- `journal/2026-02/2026-02-23-meeting-dbi-prototype-walkthrough.md`
- `journal/2026-03/2026-03-10-csi-data-ai-onsite-day1.md`
- `memory/initiatives/tars.md`
- `memory/initiatives/external-tool-integration.md`
- `memory/people/alison-slowes.md`
- `memory/people/hilary-okitia.md`
- `memory/people/nick-meyer.md`
- `memory/decisions/2026-03-18-primary-fi-dbi-design.md`
- representative files in `inbox/completed/`




