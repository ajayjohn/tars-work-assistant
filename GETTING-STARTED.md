# Getting Started with TARS

Your knowledge work assistant that remembers your people, manages your work, and helps you think strategically.

## Table of Contents
- [Quick Start (5 minutes)](#quick-start)
- [Your First Workflows](#your-first-workflows)
- [Building Habits](#building-habits)
- [Maturity Progression](#maturity-progression)
- [Key Concepts](#key-concepts)
- [Getting Help](#getting-help)

## Quick Start

### 1. Installation

From Marketplace:
1. Open Cowork → Settings → Marketplaces
2. Add: `https://github.com/ajayjohn/tars-work-assistant`
3. Install TARS plugin
4. Restart

Manual (Claude Code):
```bash
claude plugin install /path/to/tars
```

### 2. Initial Setup (3 minutes)

Run: `/welcome` or say "Set up TARS"

TARS will:
- Create workspace structure (memory/, journal/, contexts/)
- Guide MCP setup (calendar, tasks)
- Learn about you (name, role, company, key people)
- Create initial memory entries

**Pro tip**: Have your MCP servers ready before setup.

### 3. Your First Win

Try after setup:

**Daily Briefing**:
```
Daily briefing
```
See today's meetings, tasks, context.

**Process a Meeting**:
```
Process this meeting: [paste transcript]
```
Extracts action items, decisions, people context.

**Ask About Schedule**:
```
When did I last meet with Sarah?
```
Queries calendar with memory context.

## Your First Workflows

### Workflow 1: Morning Routine (2 minutes)

**Every morning**:
```
What's my day look like?
```

TARS shows:
- Today's meetings with participant profiles
- Active tasks due today or soon
- Relevant context for key discussions

**Why this matters**: Start every day grounded in context.

### Workflow 2: Meeting Processing (5 min/meeting)

**After important meetings**:
```
Process this meeting: [paste transcript]
```

TARS automatically:
1. Extracts action items → Creates tasks
2. Identifies decisions → Saves to memory
3. Captures people insights → Updates profiles
4. Generates report → Saves to journal

**Why this matters**: Zero manual note-taking. Context compounds.

### Workflow 3: Strategic Analysis (10-20 minutes)

**Before major decisions**:
```
Help me stress test this plan: [describe plan]
```

TARS applies:
- Pre-mortem analysis
- Second-order thinking
- Red team critique

**Why this matters**: Catches blind spots early.

### Workflow 4: Weekly Planning (15 minutes)

**Every Monday or Friday**:
```
Weekly briefing
```

TARS shows:
- Week's meetings with context
- Tasks grouped by initiative
- Overdue items
- Recommended priorities

**Why this matters**: See the forest, not just trees.

## Building Habits

### Habit 1: Daily Briefings (2 min/day)

**When**: First thing morning
**What**: `Daily briefing`
**Why**: Clarity and context

**Progression**:
- Week 1: Check meetings and tasks
- Week 2: Notice participant context from memory
- Week 3: See past decisions surface
- Month 2: Daily briefings = strategic anchor

### Habit 2: Meeting Processing (5 min/meeting)

**When**: Right after important meetings
**What**: `Process this meeting: [transcript]`
**Why**: Captures decisions and actions while fresh

**Progression**:
- Week 1: Process 1-2 key meetings
- Week 2: Process all 1-on-1s and planning
- Month 1: Process every meeting with action items
- Month 2: TARS auto-detects duplicates and conflicts

**Pro tip**: Use Otter.ai, Fireflies, or Grain for auto-transcripts.

### Habit 3: Proactive Memory Updates (1 min/occurrence)

**When**: Someone corrects you or shares new context
**What**: `Remember that [fact]`
**Why**: Keeps memory current

**Examples**:
- "Remember that Sarah now reports to Mike"
- "Remember that Project Atlas moved to Q3"
- "Remember that Daniel prefers tables in updates"

**Progression**:
- Week 1: TARS prompts after detecting corrections
- Week 2: You naturally say "remember that..."
- Month 1: Memory = institutional knowledge base
- Month 3: Team asks for memory exports

### Habit 4: Weekly Reviews (15 min/week)

**When**: Monday morning or Friday afternoon
**What**: `Weekly briefing` + task review
**Why**: Strategic work doesn't get buried

**Progression**:
- Week 1: Just run weekly briefing
- Week 2: Review and close completed tasks
- Month 1: Identify patterns (blockers, overcommitments)
- Quarter 1: Optimize calendar and commitments

## Maturity Progression

### Level 0: Setup (Day 1)
**Duration**: 1 session

**Activities**:
- Run `/welcome`
- Connect calendar and task MCP servers
- Add 5-10 key people

**Value Unlocked**:
- Basic schedule awareness
- Task creation and tracking

### Level 1: Active User (Weeks 1-2)
**Duration**: 2 weeks daily use

**Activities**:
- Daily briefings
- Process 2-3 meetings/week
- Occasional task extraction

**Milestones**:
- 10+ people in memory
- 5+ meetings processed
- 20+ tasks created

**Value Unlocked**:
- Context-aware briefings
- Automatic action item extraction
- People profiles populate

### Level 2: Power User (Weeks 3-8)
**Duration**: 1-2 months consistent use

**Activities**:
- Daily briefings with memory cross-references
- Process all important meetings
- Weekly reviews
- Strategic analysis (occasional)

**Milestones**:
- 30+ people in memory
- 20+ meetings processed
- 5+ initiatives tracked
- Memory graph connects (wikilinks)

**Value Unlocked**:
- Memory surfaces context automatically
- Task duplicate detection works
- Strategic analysis uses workspace context
- Communications know stakeholder preferences

### Level 3: Expert (Months 3-6)
**Duration**: 3+ months sustained use

**Activities**:
- TARS = daily interface to work context
- Memory updates = second nature
- Strategic analysis = planning workflow
- Weekly initiative reviews

**Milestones**:
- 50+ people in memory
- 50+ meetings processed
- 10+ initiatives tracked
- Dense knowledge graph (100+ wikilinks)
- Archive/housekeeping automatic

**Value Unlocked**:
- TARS knows your org as well as you do
- Onboard new team members with memory exports
- Strategic planning uses decision history
- Communications stakeholder-optimized by default
- Institutional knowledge preserved and searchable

### Level 4: Organization-Wide (Months 6+)
**Duration**: Long-term commitment

**Activities**:
- Multiple team members use TARS
- Shared memory exports for cross-team context
- Initiative tracking = team habit
- Strategic frameworks = standard practice

**Milestones**:
- 100+ people in memory
- 200+ meetings processed
- Team-wide memory conventions
- Org-wide tool integrations

**Value Unlocked**:
- Organizational memory system
- Cross-functional context sharing
- Leadership decision framework consistency
- New hire onboarding accelerates 2-3x

## Key Concepts

### Index-First Search
Every search reads `_index.md` files first. Keeps TARS fast even with hundreds of memory entries.

**For you**: More memory = better context, not slower performance.

### Durability Test for Memory
Before persisting ANY insight, TARS asks:
1. Useful for lookup next week/month?
2. High-signal and broadly applicable?
3. Durable (not transient)?
4. Changes future interactions?

If ANY answer is "No", insight discarded.

**For you**: Memory stays clean. No noise. Only what matters.

### Accountability Test for Tasks
Before creating ANY task, TARS checks:
1. Concrete? (Not "think about" or "consider")
2. Clear owner?
3. Verifiable? (Will we know when done?)

**For you**: Task list stays actionable. No vague wishes.

### Wikilinks for Graph Connectivity
All entity references use `[[Entity Name]]` syntax. Creates navigable knowledge graph.

**For you**: Context is connected. View a person → see linked initiatives, decisions, meetings.

### Provider-Agnostic Integrations
TARS doesn't lock you into one platform. Calendar and tasks abstracted in `reference/integrations.md`.

**For you**: Switch from Apple Calendar to Google Calendar without changing workflows.

## Common Questions

### "Do I need to memorize commands?"
No. TARS uses natural language routing. Just talk naturally:
- "What's my schedule?" → Briefing skill
- "Help me think through this decision" → Think skill
- "Remember that Sarah leads product" → Learn skill

Slash commands (`/briefing`, `/meeting`) are optional shortcuts.

### "How do I know what TARS can do?"
Ask TARS: "What can you do?", "How do I process a meeting?", "Help with tasks"

### "What if TARS doesn't have calendar access?"
Check `reference/integrations.md` Calendar section. Run `/welcome` to reconfigure. TARS works with Apple Calendar, Google Calendar, Microsoft 365 via MCP servers.

### "Can I use TARS without calendar/tasks?"
Yes, reduced functionality. TARS still provides:
- Meeting processing from transcripts
- Strategic analysis
- Memory system for people/initiatives
- Communications drafting

You won't get schedule-aware briefings or automatic task creation.

### "How do I back up my workspace?"
Your entire workspace is in your project directory:
```
your-project/
├── CLAUDE.md
├── memory/
├── journal/
├── contexts/
└── reference/
```

Back up this folder like any other project (Git, cloud sync, etc.).

### "Can multiple people share a TARS workspace?"
Not recommended. TARS is for individual use. For team coordination:
- Each person has their own TARS workspace
- Export memory entries to share context
- Use shared tools (Confluence, Notion) for team-wide knowledge

## Getting Help

### In-Session Help
Ask TARS: "What can you do?", "Help with meetings", "How do I process a transcript?"

### Documentation
- **GETTING-STARTED.md**: This guide
- **CATALOG.md**: Full feature catalog with examples
- **ARCHITECTURE.md**: System design and philosophy
- **CHANGELOG.md**: Version history
- **reference/integrations.md**: MCP server setup

### Troubleshooting

**"Calendar not configured"**:
→ Run `/welcome` to set up calendar MCP server
→ Check `reference/integrations.md` for configuration examples
→ Verify MCP server path in `.mcp.json`

**"Tasks aren't being created"**:
→ Check accountability test (concrete + owner + verifiable)
→ Verify task MCP server in `reference/integrations.md`
→ Test MCP server connection

**"Memory entries aren't showing up"**:
→ Run `/maintain health` to check indexes
→ Ensure `_index.md` files up to date

**"Daily briefing missing calendar events"**:
→ Verify calendar MCP server status
→ Check date resolution (TARS resolves "tomorrow" to YYYY-MM-DD)
→ Test MCP server: "What's on my calendar today?"

## Next Steps

1. **Run Setup**: `/welcome` (3 minutes)
2. **First Briefing**: "Daily briefing" (test the flow)
3. **Process a Meeting**: "Process this meeting: [paste transcript]"
4. **Review Reference Docs**:
   - `reference/integrations.md` (MCP setup)
   - `reference/taxonomy.md` (memory structure)
   - `CATALOG.md` (full feature list)
5. **Build the Habit**: Set daily reminder for morning briefings

**Pro tip**: Start small. Use daily briefings for 2 weeks before adding meeting processing. Let habits compound.

## What Makes TARS Different

**Not a chatbot**: Persistent intelligence layer. Context compounds over time.

**Not a task manager**: Integrates with YOUR task system. Doesn't replace it.

**Not a note-taking tool**: Extracts durable insights, not verbatim notes.

**Not generic AI**: Learns your organization, people, frameworks. Adapts to you.

**TARS is**: Your strategic intelligence layer. The context you wish you had in every meeting. The institutional memory that scales with your career.

## License

TARS is licensed under PolyForm Noncommercial 1.0.0. See `LICENSE` for details.

Commercial use requires prior permission.

## Origin: Why TARS?

Named after the robot from Christopher Nolan's *Interstellar*. Just like the movie's TARS, this assistant is designed to be a robust, reliable partner that brings a distinct perspective to your work.
