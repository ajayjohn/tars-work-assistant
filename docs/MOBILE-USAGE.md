# Using TARS from mobile (Claude Remote Control)

TARS v3.1 is desktop-first — the vault lives on your Mac, `obsidian-cli` drives Obsidian Desktop, and the `tars-vault` MCP server runs locally. To get mobile access, TARS relies on **Claude Remote Control**: claude.ai/code on your phone controls a live Claude Code session running on your Mac. There are zero framework changes for mobile; this doc exists so you know how to set it up and what to expect.

## What Remote Control does

claude.ai/code on mobile controls a live Claude Code session running on your Mac. You type or speak requests on the phone; TARS runs on the Mac with full vault access; you get the results back on your phone.

## Prerequisites

- Anthropic Pro or Max plan (required for Remote Control).
- Claude Code v2.1.51 or newer on the Mac.
- Your Mac is powered on, awake, and online.
- TARS plugin installed on the Mac; `tars-vault` MCP server reachable; vault open in Obsidian.
- An iOS or Android device signed into the same Anthropic account.

## One-time desktop setup

1. Enable Remote Control in Claude Code settings (Settings → Remote Control → Enable).
2. Install the provided launchd keepalive so the Mac's Claude Code session stays connectable even if you reboot:

   ```bash
   cp scripts/tars-keepalive.plist ~/Library/LaunchAgents/com.tars.keepalive.plist
   launchctl load -w ~/Library/LaunchAgents/com.tars.keepalive.plist
   ```
3. Verify the keepalive is active:

   ```bash
   launchctl list | grep com.tars.keepalive
   ```

   Expect a non-zero PID and exit status 0.
4. Start a Claude Code session, run `/welcome` or `/briefing` to confirm `tars-vault` MCP is reachable, then leave the session idle — Remote Control picks up from there.

## One-time mobile setup

1. Install the Claude app (iOS App Store or Google Play), or open claude.ai/code in Safari / Chrome.
2. Sign in with the same Anthropic account as the Mac.
3. From the app or browser, tap your Mac's active session. Verify the connection by sending a small message ("hello") and seeing the Mac's Claude Code respond.

## Daily use

From the phone, every `/tars:*` skill works exactly as on desktop:

- `/briefing` — full daily briefing, delivered back on phone.
- `/meeting` — paste or dictate a transcript; TARS runs the 14-step pipeline on the Mac.
- `/tasks` — numbered review lists render on the phone; confirm with normal selection syntax (`all`, `1,3`, `all except 4`).
- `/answer` — fast lookup; hybrid retrieval runs on the Mac against the local index.
- `/create` — office output delegates to Anthropic's rendering skills on the Mac; the artifact lands under `contexts/artifacts/YYYY-MM/` on the Mac and a companion note appears in the vault.

Voice input works well for meetings: hit the mic, describe what happened, and hand it off to `/meeting` for the full pipeline.

## Troubleshooting

- **Mac sleeps mid-session.** Check `pmset -g` on the Mac. If sleep kicks in, keep the Mac awake with `caffeinate -imsu &`, or configure Energy Saver to keep the Mac active on AC power.
- **Claude Code crashed.** The launchd keepalive restarts it automatically. If it doesn't, reload: `launchctl unload ~/Library/LaunchAgents/com.tars.keepalive.plist && launchctl load -w ~/Library/LaunchAgents/com.tars.keepalive.plist`.
- **Latency spikes.** Check your Mac's network and Anthropic's status page (`status.anthropic.com`). Remote Control tunnels through Anthropic's infrastructure.
- **Vault shows stale state.** Obsidian sometimes caches. On the Mac, Cmd+R the vault, or run `/lint` to force a re-scan.
- **`tars-vault` MCP not reachable from mobile session.** The MCP server runs on the Mac — confirm `python3 -m tars_vault` starts cleanly with `TARS_VAULT_PATH` set. Mobile doesn't execute the MCP server itself.

## Security considerations

- Remote Control traffic goes through Anthropic's infrastructure. Don't paste secrets (API keys, passwords, personal identifiers) into the mobile chat — session content is logged to your Anthropic account like any other.
- `tars-vault`'s `scan_secrets` pre-write hook still runs on every vault mutation, so accidental paste of a secret into a journal would still be blocked before landing on disk. This is belt-and-braces, not license to get careless.
- The Mac's Obsidian vault is the authoritative store. Remote Control does not create a separate copy on the phone.

## What doesn't work on mobile

- Direct editing of vault files in Obsidian on iOS / Android. The Obsidian mobile app does not participate in the Remote Control flow — you would need a separate sync path (Obsidian Sync, iCloud, etc.) to edit notes directly from mobile Obsidian, outside of TARS.
- Rich `/create` preview. The rendered `.pptx` / `.docx` / `.xlsx` lands on the Mac. Access from mobile requires a sync path (iCloud Drive, OneDrive, Dropbox) pointing at `contexts/artifacts/YYYY-MM/`.
- Offline mode. Remote Control is online-only. When away from a network, TARS is desktop-only.

## When to use Remote Control vs. desktop

Use Remote Control when:
- You're in transit and a thought needs capturing.
- You want to review a briefing during a commute.
- You want to dictate a meeting summary and have TARS ingest it while you walk.

Use desktop when:
- You're processing a long transcript (paste speed matters).
- You're doing strategic work (`/think`, `/initiative`) — full keyboard + bigger screen.
- You're building office artifacts (review the rendered file on the Mac before sharing).
