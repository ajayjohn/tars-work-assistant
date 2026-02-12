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
- **Apple Calendar (Syncs with local Microsoft Outlook)** (https://github.com/ajayjohn/mcp-server-apple-calendar)

**Tasks Options:**
- **Apple Reminders (Syncs with local Microsoft To-Do)** (https://github.com/ajayjohn/mcp-server-apple-reminders)
- **Todoist** (https://developer.todoist.com/api/v1/#tag/Todoist-MCP)
- **Linear** (https://linear.app/docs/mcp)

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

TARS becomes more valuable as it learns about your work. The **TARS Inbox** is your primary tool for feeding it information efficiently.

### What is the Inbox?

The Inbox is a staging area for raw information—meeting notes, emails, articles, or any professional content. Drop content in, and TARS automatically:

-   **Extracts tasks** and adds them to your task manager
-   **Records decisions** linked to relevant initiatives or people
-   **Updates profiles** with preferences, reporting structures, or key projects
-   **Flags delegated items** for tracking
-   **Links context** to existing memory entries

### How to Use It

**Add content to the inbox:**
1. Drop files or paste content into the `inbox/` folder in your workspace
2. Or simply tell TARS: "Add this to the inbox: [paste content]"

**Process the inbox:**
```
/maintain inbox
```

TARS will batch process all inbox items, extracting insights and updating your knowledge base. Think of it as "onboarding" TARS with the context it needs to be an effective partner.

### Essential Habits

Build these habits to keep TARS effective:

1.  **Daily Briefing** (2 min/day)
    *   **When**: First thing in the morning
    *   **Command**: `Daily briefing`
    *   **Value**: See your schedule, priorities, and relevant context before your first meeting

2.  **Process Meetings** (5 min/meeting)
    *   **When**: After important meetings
    *   **How**: Add transcript to inbox, then run `/maintain inbox`
    *   **Value**: Auto-capture action items, decisions, and people insights

3.  **Feed Strategic Content** (as needed)
    *   **When**: Encounter valuable information (whitepapers, memos, analyses)
    *   **How**: Add to inbox, run `/maintain inbox` when ready
    *   **Value**: Build TARS's strategic context and domain knowledge

4.  **Quick Memory Updates** (1 min/occurrence)
    *   **When**: New information emerges
    *   **Command**: `Remember that [fact]`
    *   **Examples**: "Remember that Murph now reports to Brand" or "Remember that Project Lazarus moved to Q3"
    *   **Value**: Keep TARS's memory current

5.  **Weekly Review** (15 min/week)
    *   **When**: Monday morning or Friday afternoon
    *   **Command**: `Weekly briefing`
    *   **Value**: Strategic overview, identify blockers, align efforts with goals

### What TARS Can Do With Context

With regular information feeding, TARS unlocks advanced capabilities:

-   **Strategic Analysis**: "Help me stress test this plan" - Apply frameworks like pre-mortem analysis
-   **Communication Drafting**: "Draft an email to [[Joseph Cooper]] about [[DBI Phase 1]]" - Tailored to recipient preferences
-   **Decision Support**: "Summarize pros and cons of [[Project Lazarus]]" - Based on past discussions
-   **Meeting Preparation**: Deep dives on topics, surfacing related documents and profiles
-   **Relationship Context**: "What's our history with [[Vendor X]]?" - Pull interactions and contracts

These habits transform TARS into an intelligent partner that maintains institutional memory and provides context when you need it.

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