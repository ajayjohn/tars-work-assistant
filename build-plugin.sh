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

# Read source plugin.json - single source of truth
with open('.claude-plugin/plugin.json', 'r') as f:
    source = json.load(f)

# Create minimal version for Cowork (auto-discovers skills/commands from directory)
minimal = {
    "name": source["name"],
    "version": source["version"],
    "description": source.get("description", ""),
    "author": source.get("author", {"name": "Ajay John"}),
    "license": source.get("license", "Apache-2.0")
}

# Write minimal version for distribution
with open('tars-cowork-plugin/.claude-plugin/plugin.json', 'w') as f:
    json.dump(minimal, f, indent=2)

# Sync version to marketplace.json
with open('.claude-plugin/marketplace.json', 'r') as f:
    marketplace = json.load(f)

# Update the TARS plugin version in marketplace
for plugin in marketplace.get('plugins', []):
    if plugin['name'] == 'tars':
        plugin['version'] = source['version']
        plugin['description'] = source.get('description', plugin.get('description', ''))
        break

with open('.claude-plugin/marketplace.json', 'w') as f:
    json.dump(marketplace, f, indent=2)

print(f"✓ Created minimal plugin.json (v{minimal['version']})")
print(f"✓ Synced marketplace.json version to v{source['version']}")
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