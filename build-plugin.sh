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

# Create minimal plugin.json using Python (all values derived from source)
python3 << 'PYTHON_SCRIPT'
import json

# Read source plugin.json - single source of truth
with open('.claude-plugin/plugin.json', 'r') as f:
    source = json.load(f)

# Create minimal version for Cowork (auto-discovers skills/commands from directory)
# Only include fields that Cowork needs - everything else is derived from source
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

print(f"✓ Created minimal plugin.json (v{minimal['version']})")
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