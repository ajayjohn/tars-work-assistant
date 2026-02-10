#!/bin/bash
set -e

echo "Building TARS Cowork plugin..."

# Clean old build
rm -rf tars-cowork-plugin

# Create distribution structure
mkdir -p tars-cowork-plugin/{skills,commands,scripts,reference,.claude-plugin}

# Copy all content from source
cp -r skills/* tars-cowork-plugin/skills/
cp -r commands/* tars-cowork-plugin/commands/
cp -r scripts/* tars-cowork-plugin/scripts/
cp -r reference/* tars-cowork-plugin/reference/
cp LICENSE .mcp.json tars-cowork-plugin/

# Create minimal plugin.json and sync marketplace.json using Python
python3 << 'PYTHON_SCRIPT'
import json
import os

# Read source plugin.json - single source of truth
with open('.claude-plugin/plugin.json', 'r') as f:
    source = json.load(f)

# Create minimal version for Cowork (auto-discovers skills/commands from directory)
minimal = {
    "name": source["name"],
    "version": source["version"],
    "description": source["description"],
    "author": source["author"],
    "license": source["license"]
}

# Include displayName if present in source
if "displayName" in source:
    minimal["displayName"] = source["displayName"]

# Write minimal version for distribution
with open('tars-cowork-plugin/.claude-plugin/plugin.json', 'w') as f:
    json.dump(minimal, f, indent=2)

# Sync version to marketplace.json (always in .claude-plugin/)
marketplace_path = '.claude-plugin/marketplace.json'
if os.path.exists(marketplace_path):
    with open(marketplace_path, 'r') as f:
        marketplace = json.load(f)

    # Update the TARS plugin version in marketplace
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
# TARS — Task-Aware Research & Strategy Assistant

**Your executive assistant for strategy, research, communication, and initiatives.**

## Installation
1. Cowork → Settings → Plugins → Install from Folder
2. Select: `tars-cowork-plugin/`
3. Run: `/welcome` to set up workspace

## Quick Start
```
/welcome          # Set up workspace
/briefing today   # Daily briefing
/think "topic"    # Strategic analysis
```

Full docs: https://github.com/ajayjohn/tars-work-assistant
EOF

cd tars-cowork-plugin
zip -q -r Archive.zip . -x "*.DS_Store" -x "__pycache__/*"
cd ..

echo "✓ Build complete: $(ls -lh tars-cowork-plugin/Archive.zip | awk '{print $5}')"