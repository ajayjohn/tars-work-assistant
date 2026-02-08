# Getting started with TARS

Welcome! TARS is your strategic intelligence assistant. It maintains a persistent knowledge base of your people, initiatives, decisions, and organizational context -- so you can focus on leading rather than remembering.

## First 5 minutes

Run `/setup` (or just say "set up TARS") to scaffold your workspace. TARS will create the directory structure, check your integrations (calendar, tasks), and ask a few questions about your role and organization.

If you have a calendar connected, TARS will auto-discover your name, recurring meetings, and frequent contacts. You'll see value immediately: a mini-briefing of your upcoming week.

## Your first win

After setup, try one of these:

- **Process a meeting**: Paste a transcript or say "process my meeting notes" and TARS extracts action items, key decisions, and people context -- all persisted to memory.
- **Get a briefing**: Say "daily briefing" to see today's meetings, tasks, and relevant people context pulled from memory.
- **Ask a question**: "What do I know about Project Phoenix?" searches memory using the index-first pattern.

## How memory works

TARS maintains a structured knowledge base in the `memory/` folder. Every piece of information passes a **durability test** before being saved: it must have lookup value, be high-signal, be durable (not ephemeral), and change future interactions.

Memory is organized by type: people, initiatives, decisions, products, vendors, competitors, and organizational context. Each file has YAML frontmatter for fast index-based searching.

## How tasks work

Tasks live in your configured task integration (see `reference/integrations.md` for provider details). Every task must pass an **accountability test**: it must be concrete, owned, and verifiable. "Send Q3 roadmap draft to Sarah by Friday" passes. "Think about the roadmap" does not.

## Natural language, not commands

While slash commands exist (`/briefing`, `/meeting`, `/tasks`), you can also just talk naturally:

- "What's on my plate today?" routes to the briefing skill
- "Help me think through the reorg" routes to strategic analysis
- "Draft an email to the team about the deadline change" routes to communicate

TARS reads your intent and routes to the right skill automatically.

## Growing over time

TARS gets more useful as you feed it information. The `reference/maturity.yaml` file tracks your progress through four levels based on people known, meetings processed, and initiatives tracked.

During your first week, TARS will passively learn from your calendar patterns, proactively offer to remember important facts, and suggest filling knowledge gaps at natural breakpoints.

## Key concepts

- **Index-first**: TARS always reads `_index.md` before opening individual files, keeping context usage efficient.
- **Staleness tiers**: Memory files are classified as durable (permanent), seasonal (180-day review), transient (90-day review), or ephemeral (date-tagged expiry).
- **Wikilinks**: Entities are cross-referenced using `[[Entity Name]]` links, creating a navigable knowledge graph.

## Getting help

Say "what can you do?" or "help with meetings" for skill-specific guidance. See `reference/workflows.md` for common multi-step patterns.
