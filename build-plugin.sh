#!/bin/bash
set -e

echo "Building TARS v3 plugin..."

# Clean old build
rm -rf tars-cowork-plugin

# Create v3 distribution structure
mkdir -p tars-cowork-plugin/{skills,scripts,templates,_system,_views,.claude-plugin,.claude/skills}

# Copy v3 content from source
cp -r skills/* tars-cowork-plugin/skills/
cp -r scripts/*.py tars-cowork-plugin/scripts/
cp -r templates/* tars-cowork-plugin/templates/
cp -r _system/* tars-cowork-plugin/_system/
cp -r _views/* tars-cowork-plugin/_views/
cp -r .claude/skills/* tars-cowork-plugin/.claude/skills/
cp LICENSE CLAUDE.md tars-cowork-plugin/

# Copy .mcp.json if it exists
[ -f .mcp.json ] && cp .mcp.json tars-cowork-plugin/

# Create minimal plugin.json and sync marketplace.json using Python
python3 << 'PYTHON_SCRIPT'
import json
import os

# Read source plugin.json - single source of truth
with open('.claude-plugin/plugin.json', 'r') as f:
    source = json.load(f)

# Create minimal version for Cowork (auto-discovers skills from directory)
minimal = {
    "name": source["name"],
    "version": source["version"],
    "description": source["description"],
    "author": source["author"],
    "license": source["license"]
}

# Write minimal version for distribution
with open('tars-cowork-plugin/.claude-plugin/plugin.json', 'w') as f:
    json.dump(minimal, f, indent=2)

# Sync version to marketplace.json (always in .claude-plugin/)
marketplace_path = '.claude-plugin/marketplace.json'
if os.path.exists(marketplace_path):
    with open(marketplace_path, 'r') as f:
        marketplace = json.load(f)

    # Update the TARS plugin entry in marketplace
    for plugin in marketplace.get('plugins', []):
        if plugin['name'] == 'tars':
            plugin['version'] = source['version']
            plugin['description'] = source['description']
            break

    with open(marketplace_path, 'w') as f:
        json.dump(marketplace, f, indent=2)

    print(f"✓ Created minimal plugin.json (v{minimal['version']})")
    print(f"✓ Synced .claude-plugin/marketplace.json version to v{source['version']}")
else:
    print(f"✓ Created minimal plugin.json (v{minimal['version']})")
    print(f"⚠ .claude-plugin/marketplace.json not found - skipping sync")
PYTHON_SCRIPT

cat > tars-cowork-plugin/README.md << 'EOF'
# TARS 3.0 — Persistent Executive Assistant for Obsidian

**Obsidian-native knowledge work operating system with memory continuity, meeting processing, task accountability, strategic analysis, and stakeholder communications.**

## Installation
1. Claude Code → Install from marketplace or folder
2. Select: `tars-cowork-plugin/`
3. Run: `/welcome` to set up your vault

## Quick Start
```
/welcome          # Set up vault and integrations
/briefing         # Daily briefing
/meeting          # Process a meeting transcript
/tasks            # Extract or manage tasks
/think "topic"    # Strategic analysis
```

## Requirements
- Obsidian desktop app running
- obsidian-cli installed (`brew install kepano/tap/obsidian-cli`)
- An Obsidian vault for TARS to use

Full docs: https://github.com/ajayjohn/tars-work-assistant
EOF

cd tars-cowork-plugin
zip -q -r Archive.zip . -x "*.DS_Store" -x "__pycache__/*"
cd ..

echo "✓ Build complete: $(ls -lh tars-cowork-plugin/Archive.zip | awk '{print $5}')"
