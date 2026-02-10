# Getting Started with TARS

Your knowledge work assistant that remembers your people, manages your work, and helps you think strategically.

## Table of Contents
- [Quick Start (5 minutes)](#quick-start)
- [Your First Workflows](#your-first-workflows)
- [Building Habits](#building-habits)
- [Common Questions](#common-questions)
- [Getting Help](#getting-help)
- [Next Steps](#next-steps)

## Quick Start

### 0. Choose Your Workspace (IMPORTANT - Do This First!)

**Before installing TARS**, choose or create an empty folder that will serve as your TARS workspace. This is where TARS stores its persistent knowledge base.

**Recommended folder structure:**
```
~/Documents/TARS-Workspace/     # or any location you prefer
├── memory/                     # TARS's brain - people, initiatives, decisions
├── journal/                    # Daily entries and meeting notes
├── contexts/                   # Strategic context files
├── reference/                  # Configuration and integrations
└── .mcp.json                   # MCP server configuration (optional)
```

**Why a dedicated workspace folder?**
- **Persistence**: TARS's memory and knowledge base live here permanently
- **Portability**: Move or backup your TARS brain by copying this folder
- **Organization**: Keeps all TARS data separate from other projects
- **Safety**: TARS won't accidentally modify files in other directories

**Setup your workspace:**

**For Claude Code users**:
- Create an empty folder for TARS: `mkdir ~/Documents/TARS-Workspace`
- Navigate to it: `cd ~/Documents/TARS-Workspace`
- Keep this as your working directory whenever using TARS

**For Claude Cowork users**:
- Create an empty folder for TARS
- Open it as your Workspace in Cowork settings
- This becomes your default workspace for TARS interactions

### 1. Installation

Getting TARS up and running is straightforward. If you've previously installed TARS and are encountering issues, clearing the cache first can resolve many common problems:

**If Re-installing (clear cache first):**
```bash
rm -rf ~/.claude/plugins/cache/tars ~/.claude/plugins/cache/TARS
# Then restart Claude Desktop/Cowork before reinstalling
```

**From Marketplace (recommended for most users):**
1. Open Cowork → Settings → Marketplaces
2. Add: `https://github.com/ajayjohn/tars-work-assistant`
3. Install TARS plugin
4. Restart Claude Cowork

**Manual Installation (for Claude Code power users):**
```bash
claude plugin install /path/to/tars
```

### 2. Initial Setup (3 minutes)

Run: `/welcome` or simply say "Set up TARS"

TARS will initiate a brief Q&A session. This isn't just about collecting information; it's about building TARS's understanding of your professional world. The more context TARS has about your role, your organization, and your key relationships, the better it can serve you as a proactive and intelligent assistant. Think of this as the critical first step in "hydrating" TARS with the foundational knowledge it needs to truly become your co-pilot.

During this setup, TARS will:
- Create the essential workspace structure (memory/, journal/, contexts/)
- Guide you through setting up essential integrations (e.g., calendar, task manager)
- Learn about you: your name, role, company, and important people in your network
- Create initial memory entries to begin building its knowledge graph

**Pro tip**: Have your integration details (like calendar or task server URLs/API keys) ready before starting the setup to streamline the process.

### 2.5. Essential Integrations (Calendar & Tasks)

TARS works best when connected to your calendar and task manager. These integrations are **mandatory for core features** like daily briefings, meeting processing, and schedule awareness.

#### Why Calendar and Tasks Matter

**Without calendar integration:**
- No daily/weekly briefings with schedule awareness
- No meeting attendee context or calendar lookups
- No "When did I last meet X?" queries
- Limited meeting processing (transcript-only, no attendee list)

**Without tasks integration:**
- No automatic action item creation from meetings
- No task tracking in briefings
- No task triage or prioritization
- Manual task management only

#### Recommended Setup: MCP Servers (v2.1+)

TARS uses the Model Context Protocol (MCP) for integrations. MCP servers provide standardized access to external tools.

**Calendar Options:**
- **Apple Calendar** (via `@modelcontextprotocol/server-apple-calendar`)
- **Google Calendar** (via `@modelcontextprotocol/server-google-calendar`)
- **Microsoft 365 Calendar** (via `@modelcontextprotocol/server-microsoft-365`)

**Tasks Options:**
- **Apple Reminders** (via `@modelcontextprotocol/server-apple-reminders`)
- **Todoist** (via `@modelcontextprotocol/server-todoist`)
- **TickTick** (via `@modelcontextprotocol/server-ticktick`)
- **Microsoft To-Do** (via `@modelcontextprotocol/server-microsoft-todo`)
- **Linear** (via `@modelcontextprotocol/server-linear` - for engineering teams)

#### Configuration: .mcp.json

MCP servers are configured in a `.mcp.json` file in your workspace root. Here's an example for Apple Calendar and Apple Reminders:

```json
{
  "mcpServers": {
    "apple-calendar": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-apple-calendar"]
    },
    "apple-reminders": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-apple-reminders"]
    }
  }
}
```

**Finding MCP Servers:**
Search for MCP servers in the [MCP marketplace](https://github.com/modelcontextprotocol) or GitHub. Common patterns:
- `@modelcontextprotocol/server-<platform>`
- `mcp-server-<platform>`

**After Configuration:**
1. Restart Claude Cowork/Code to load MCP servers
2. Run `/welcome` to verify integration status
3. Test with "Daily briefing" to confirm calendar and tasks are working

#### What If I Skip This?

TARS will still work with reduced functionality:
- Memory system (people, initiatives, decisions)
- Meeting processing (transcript-only, no calendar context)
- Strategic analysis (think skill)
- Communication drafting

But you'll miss the core value: schedule-aware briefings, automatic task creation, and calendar-integrated workflows.

### 3. Your First Win

Once setup is complete, try these commands to experience TARS's immediate value:

**Daily Briefing**:
```
Daily briefing
```
Receive a concise overview of today's meetings, tasks, and relevant context drawn from TARS's memory.

**Process a Meeting**:
```
Process this meeting: [paste transcript]
```
TARS will intelligently extract action items, key decisions, and update relevant people profiles from your meeting transcript.

**Ask About Schedule**:
```
When did I last meet with Murph?
```
TARS queries your calendar, leveraging its memory to provide context-rich answers.

## Your First Workflows: The TARS Inbox & Batch Processing

TARS is designed to become an indispensable extension of your professional self. To achieve this, it needs a continuous feed of information about your world. This isn't a burden; it's an easy habit to build, particularly with the power of the **TARS Inbox**.

The Inbox is your primary gateway for feeding raw, unstructured information into TARS. Think of it as a smart staging area where you can dump meeting notes, emails, articles, or any other professional collateral. TARS then processes these inputs, automatically identifying and categorizing key information:

-   **Task Extraction**: Automatically pulls out actionable items and adds them to your task manager.
-   **Decision Recording**: Identifies significant decisions made and stores them in memory, linked to relevant initiatives or people.
-   **Profile Updates**: Enriches profiles of people you interact with, noting preferences, reporting structures, or key projects.
-   **Delegated Items**: Flags tasks or actions that have been delegated to others.
-   **Contextual Linking**: Connects new information to existing memory entries, building a richer, more interconnected knowledge graph.

This batch processing capability via the Inbox makes feeding TARS context incredibly efficient. Instead of meticulously entering data, you simply provide the raw material, and TARS does the heavy lifting, turning information into actionable intelligence.

**Analogy**: Imagine bringing a new, highly capable teammate up to speed. You wouldn't make them manually input every detail. Instead, you'd provide them with documents, meeting recordings, and discussions, trusting them to synthesize that information and identify what's critical. The TARS Inbox functions similarly, allowing you to "onboard" TARS with the context it needs to become an active, contributing partner.

### Essential Habits for Hydrating TARS

To maximize TARS's value, integrate these simple workflows into your daily routine. These are the habits that keep TARS well-fed and capable of delivering unparalleled insights:

1.  **The Daily Briefing (2 min/day)**
    *   **When**: First thing in the morning.
    *   **What**: `Daily briefing`
    *   **Why**: Start your day grounded in your schedule, priorities, and relevant context. TARS surfaces what you need to know *before* your first meeting.

2.  **Meeting Processing via Inbox (5 min/meeting)**
    *   **When**: Immediately after important meetings.
    *   **What**: Feed meeting transcripts (e.g., from Otter.ai, Fireflies, or Grain) directly into the TARS Inbox.
    *   **Why**: Capture action items, decisions, and people insights while fresh. TARS handles the parsing, ensuring no critical detail is lost and your memory is updated automatically. This is zero-manual-note-taking, context compounding at its best.

3.  **Inbox for Strategic Collateral (variable time)**
    *   **When**: Whenever you encounter valuable information—whitepapers, help documentation, competitor analyses, internal memos.
    *   **What**: Drop the content (or summaries/links) into the TARS Inbox.
    *   **Why**: TARS processes this, extracting key concepts, linking them to initiatives, and enriching its understanding of your strategic landscape. This ensures TARS has the same foundational knowledge you would expect from a seasoned colleague.

4.  **Proactive Memory Updates (1 min/occurrence)**
    *   **When**: Any time new information emerges that refines TARS's understanding (e.g., someone corrects you, a project scope changes, a reporting line shifts).
    *   **What**: `Remember that [fact]`
    *   **Examples**:
        *   "Remember that Murph now reports to Brand"
        *   "Remember that Project Lazarus moved to Q3"
        *   "Remember that Brand prefers tables in updates"
    *   **Why**: Keeps TARS's memory current, ensuring its insights are always accurate and relevant.

5.  **Weekly Reviews (15 min/week)**
    *   **When**: Monday morning or Friday afternoon.
    *   **What**: `Weekly briefing` + review tasks and priorities within TARS.
    *   **Why**: Gain a strategic overview of your week, identify blockers, and ensure your efforts align with broader goals. TARS helps you see the forest, not just the trees.

### Leveraging TARS with Adequate Context

Once TARS is regularly fed with information through these habits, its capabilities expand dramatically, moving beyond basic scheduling and task management. With a rich understanding of your professional world, TARS can proactively assist you in numerous ways:

-   **Strategic Analysis**: `Help me stress test this plan: [describe plan]`. TARS can apply frameworks like pre-mortem analysis or red team critique, leveraging its memory of past decisions and organizational context to uncover blind spots.
-   **Communication Drafting**: `Draft an email to [[Joseph Cooper]] about the [[DBI Phase 1]] roadmap update`. TARS will tailor the communication, referencing relevant decisions, initiatives, and even Daniel's known preferences.
-   **Decision Support**: `Summarize the pros and cons of [[Project Lazarus]] based on our discussions and past decisions`. TARS synthesizes information from various sources to provide a balanced perspective.
-   **New Team Member Onboarding**: Export relevant sections of TARS's memory to quickly bring a new hire up to speed on key people, projects, and organizational context.
-   **Meeting Preparation**: Beyond the daily briefing, TARS can provide deeper dives into meeting topics, surfacing related documents, people profiles, and historical discussions relevant to the agenda.
-   **Vendor Management**: `What's our relationship history with [[Vendor X]]?`. TARS can pull up past interactions, contracts, and relevant performance notes from its memory.

By embracing these habits, you transform TARS from a simple tool into a dynamic, intelligent partner that scales with your career, providing the context you wish you had in every meeting and maintaining the institutional memory that often gets lost in the day-to-day.

## Common Questions

### "Do I need to memorize commands?"
No. TARS uses natural language routing. Just talk naturally:
- "What's my schedule?" → Briefing skill
- "Help me think through this decision" → Think skill
- "Remember that Murph leads product" → Learn skill

Slash commands (`/briefing`, `/meeting`) are optional shortcuts.

### "How do I know what TARS can do?"
Ask TARS: "What can you do?", "How do I process a meeting?", "Help with tasks"

### "What if TARS doesn't have calendar access?"
1. Create or update `.mcp.json` in your workspace root with a calendar MCP server (see "Essential Integrations" section above)
2. Restart Claude Cowork/Code to load the MCP server
3. Run `/welcome` to verify the integration
4. Test with "What's on my calendar today?"

If you see "Calendar not configured" errors, check:
- `.mcp.json` exists and has valid JSON syntax
- MCP server package is available (e.g., run `npx -y @modelcontextprotocol/server-apple-calendar` without errors)
- You've restarted Claude after adding the MCP server

See `reference/integrations.md` and the "Essential Integrations" section for detailed examples.

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
→ Add calendar MCP server to `.mcp.json` (see "Essential Integrations" section above)
→ Restart Claude Cowork/Code to load the MCP server
→ Run `/welcome` to verify integration status
→ Test with "What's on my calendar today?"
→ Check `reference/integrations.md` for detailed platform-specific examples

**"Tasks aren't being created"**:
→ Add task/reminders MCP server to `.mcp.json` (see "Essential Integrations" section above)
→ Restart Claude Cowork/Code to load the MCP server
→ Verify with "List my tasks" or "What's on my plate?"
→ Check accountability test: concrete task + specific owner + verifiable outcome
→ See `reference/integrations.md` for platform options

**"Memory entries aren't showing up"**:
→ Run `/maintain health` to check indexes
→ Ensure `_index.md` files up to date

**"Daily briefing missing calendar events"**:
→ Verify calendar MCP server status
→ Check date resolution (TARS resolves "tomorrow" to YYYY-MM-DD)
→ Test MCP server: "What's on my calendar today?"

## Next Steps

1.  **Run Setup**: `/welcome` (3 minutes)
2.  **First Briefing**: "Daily briefing" (test the flow)
3.  **Process a Meeting**: "Process this meeting: [paste transcript]" (via the Inbox for optimal results)
4.  **Review Reference Docs**:
    *   `reference/integrations.md` (MCP setup)
    *   `reference/taxonomy.md` (memory structure)
    *   `CATALOG.md` (full feature list)
5.  **Build the Habit**: Set daily reminder for morning briefings and incorporate meeting processing into your routine.

**Pro tip**: Start small. Use daily briefings for 2 weeks before adding meeting processing and other inputs. Let habits compound to unlock TARS's full potential.