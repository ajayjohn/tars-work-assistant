<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS

Knowledge work assistant plugin for Claude Code and Claude Cowork. TARS turns Claude into a persistent, context-aware executive assistant that remembers your organization, manages your work, processes meetings, captures knowledge, and helps you think strategically.

Built for leaders, operators, and teams who want AI that adapts to their business, not the other way around. TARS learns your people, your initiatives, your decisions—and stays grounded in your workspace.

## Installation

```bash
claude plugin install ./tars
```

Then run `/welcome` in your workspace for the progressive onboarding wizard.

## What TARS does

**Memory system**: Persistent knowledge graph of people, initiatives, decisions, products, vendors, and competitors. Wikilink-connected with durability-tested entries. Provider-agnostic integrations sync with your tools.

**Task management**: Accountable task extraction and lifecycle. Active/backlog/completed with date resolution and duplicate detection.

**Meeting processing**: Full pipeline from transcript to structured report, journal entry, tasks, and memory updates.

**Briefings**: Daily and weekly briefings pulling from calendar, tasks, and people context.

**Strategic analysis**: Multi-method thinking (Tree of Thoughts, debate, stress-testing, deep understanding).

**Communications**: Stakeholder-aware drafting with upstream/downstream modes and RASCI enforcement.

**Knowledge capture**: Extract durable insights and wisdom from meetings, documents, and conversations. Durability-tested entries that actually stay useful.

**Initiative management**: Plan, track, and report on initiatives with KPIs and health checks.

**Workspace maintenance**: Health checks, syncs, index rebuilds, and automated housekeeping.

---

## Natural language interface

You don't need to memorize commands. Tell TARS what you need in plain language:

- "Here's a meeting transcript, process it" → Meeting skill (full pipeline)
- "What's on my plate today?" → Daily briefing
- "Poke holes in this plan" → Stress-test mode (Think skill)
- "Remember that Sarah reports to Mike" → Learn skill (memory mode)
- "Draft an email to the VP about the Q3 delay" → Communicate skill
- "What do I know about Project Atlas?" → Answer skill (fast lookup)

TARS routes your request to the right skill and runs it end-to-end.

---

## Commands (11)

| Command | Purpose |
|---------|---------|
| `/welcome` | Progressive onboarding wizard (3-phase setup) |
| `/meeting` | Process meeting transcript (full pipeline: report → tasks → memory) |
| `/briefing` | Daily or weekly briefing (calendar + tasks + people context) |
| `/tasks` | Extract or manage tasks (extract mode or triage mode) |
| `/learn` | Persist memory or extract wisdom (memory mode or wisdom mode) |
| `/think` | Strategic analysis, debate, stress-test, deep dive (5 analysis modes) |
| `/initiative` | Plan, status, or performance report (3 initiative modes) |
| `/maintain` | Health check, sync, rebuild, inbox (workspace maintenance) |
| `/communicate` | Draft stakeholder communications (upstream or downstream) |
| `/create` | Generate decks, narratives, speeches (presentation-grade content) |
| `/answer` | Fast factual lookup (search hierarchy with sources) |

---

## Skills (12)

Skills contain workflow logic and fire based on command routing. Metadata loads at session start (~48 tokens). Full skill logic loads on-demand.

### Background (1)

| Skill | Purpose |
|-------|---------|
| Core | Identity, routing, communication rules, memory/task protocols, decision frameworks, clarification |

### Workflow (11)

| Skill | Modes | Purpose |
|-------|-------|---------|
| Meeting | auto | Full pipeline: transcript → report → tasks → memory |
| Tasks | extract, manage | Extract accountable tasks or review/triage existing |
| Learn | memory, wisdom | Persist durable insights or extract from content |
| Think | analyze, debate, stress-test, deep, discover | Strategic analysis engine (5 modes) |
| Briefing | daily, weekly | Calendar + tasks + people context |
| Initiative | plan, status, performance | Initiative lifecycle management |
| Maintain | health, sync, rebuild, inbox | Workspace maintenance |
| Welcome | - | Progressive 3-phase onboarding |
| Communicate | upstream, downstream | Stakeholder communications |
| Create | - | Presentation-grade content |
| Answer | - | Fast factual lookups |

---

## Workspace structure (created by `/welcome`)

```
your-project/
├── CLAUDE.md                    # Root config with your identity
├── memory/
│   ├── _index.md
│   ├── people/                  # Stakeholder profiles
│   ├── initiatives/             # Project/initiative knowledge
│   ├── decisions/               # Key decisions and rationale
│   ├── products/                # Product knowledge
│   ├── vendors/                 # Vendor relationships
│   ├── competitors/             # Competitive intelligence
│   └── organizational-context/
├── journal/
│   └── YYYY-MM/                 # Meeting reports, briefings, wisdom
├── contexts/
│   ├── products/                # Deep product documentation
│   └── artifacts/               # Generated decks, narratives, speeches
└── reference/
    ├── replacements.md          # Name normalization mappings
    ├── taxonomy.md              # Tags, types, frontmatter templates
    ├── kpis.md                  # Team/initiative metrics
    ├── schedule.md              # Recurring/one-time scheduled items
    └── integrations.md          # Integration config and query patterns
```

---

## Key concepts

**Index-first**: Every search reads `_index.md` before opening individual files. Scales to hundreds of memory entries.

**Durability test**: Memory additions must pass 4 criteria (lookup value, signal, durability, behavior change). Most inputs produce zero memory additions.

**Accountability test**: Tasks must be concrete, have a clear owner, and be verifiable. "Synergize on the roadmap" fails.

**Wikilinks**: All entity references use `[[Entity Name]]` syntax for graph connectivity.

**Name normalization**: `reference/replacements.md` maps variations to canonical names. "Mick" becomes "Michael Rodriguez."

**Provider-agnostic integrations**: TARS integrates with your tools (calendar, task systems, Slack, email) through abstracted query patterns in `reference/integrations.md`. Not locked into one platform.

**4-tier archival**: Entries move through 4 states (active, warm, cool, archived) with automated housekeeping. Keeps memory fresh without manual cleanup.

**Sensitive data guardrails**: Flags PII, financial, and security-sensitive entries. Blocks accidental exposure in briefings and comms.

**Automated housekeeping**: `/maintain` detects stale tasks, orphaned memory entries, duplicate wikilinks, and index drift.

**Help system**: Ask TARS "what can you do?" or "how do I process a meeting?" Inline help metadata provides accurate answers without opening docs.

**Token efficiency**: v2.0 loads only metadata at session start (~48 tokens baseline). Full skill logic loads on-demand when commands execute.

---

## Getting help

Ask TARS directly:
- "What can you do?"
- "How do I process a meeting?"
- "What's the difference between `/think` and `/think stress-test`?"

TARS answers from inline help metadata. For deeper reference material, see `reference/getting-started.md` and `reference/workflows.md`.

---

## Origin: Why the Name TARS?

The inspiration comes directly from one of my favorite movies, *Interstellar* by Christopher Nolan. TARS is a robot from the movie that plays a crucial role in the storyline. I named this assistant TARS because ultimately, I want it to be a partner that is robust, reliable and brings a distinct perspective to your work, just like TARS did in the movie.

---

## License

PolyForm Noncommercial 1.0.0. See `LICENSE`.

> **Note**: Commercial use requires prior permission. Please contact the author for commercial licensing.

Users must preserve the attribution notices in the `NOTICE` file when distributing this work.
