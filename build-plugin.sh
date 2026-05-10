#!/bin/bash
set -e

echo "Building TARS v3 plugin..."

# Clean old build
rm -rf tars-cowork-plugin

# Create v3 distribution structure. The package contains framework assets, not
# a fake user workspace. Runtime folders like _system/ and _views/ are created
# inside the user's selected workspace by /welcome.
mkdir -p tars-cowork-plugin/{skills,commands,scripts,templates,hooks,.claude-plugin,.claude/skills}
mkdir -p tars-cowork-plugin/mcp/tars-vault

# Copy v3 content from source
cp -r skills/* tars-cowork-plugin/skills/
cp -r commands/* tars-cowork-plugin/commands/
cp -r scripts/*.py tars-cowork-plugin/scripts/
cp -r templates/* tars-cowork-plugin/templates/
mkdir -p tars-cowork-plugin/templates/views
cp -r _views/* tars-cowork-plugin/templates/views/
cp -r .claude/skills/* tars-cowork-plugin/.claude/skills/
cp LICENSE CLAUDE.md requirements.txt requirements-search.txt tars-cowork-plugin/
cp .claude-plugin/mcp-servers.json tars-cowork-plugin/.claude-plugin/

# Copy the tars-vault MCP server (required for TARS workspace writes).
# Excludes __pycache__ and tests/ — tests/ ships separately in the repo checkout.
cp -R mcp/tars-vault/. tars-cowork-plugin/mcp/tars-vault/
rm -rf tars-cowork-plugin/mcp/tars-vault/tests
find tars-cowork-plugin/mcp/tars-vault -type d -name '__pycache__' -prune -exec rm -rf {} +

# Copy hooks (plugin auto-registers them via hooks/hooks.json).
cp -R hooks/. tars-cowork-plugin/hooks/
find tars-cowork-plugin/hooks -type d -name '__pycache__' -prune -exec rm -rf {} +

# The packaged plugin ships MCP metadata in two documented places:
# - .claude-plugin/plugin.json inline `mcpServers`.
# - plugin-root .mcp.json using the standard `{"mcpServers": ...}` shape.

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
    "license": source["license"],
    "mcpServers": source["mcpServers"]
}

# Write minimal version for distribution
with open('tars-cowork-plugin/.claude-plugin/plugin.json', 'w') as f:
    json.dump(minimal, f, indent=2)
    f.write('\n')

# Plugin-root .mcp.json uses the standard MCP server configuration shape.
with open('tars-cowork-plugin/.mcp.json', 'w') as f:
    json.dump({"mcpServers": source["mcpServers"]}, f, indent=2)
    f.write('\n')

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
        f.write('\n')

    print(f"✓ Created minimal plugin.json (v{minimal['version']})")
    print(f"✓ Synced .claude-plugin/marketplace.json version to v{source['version']}")
else:
    print(f"✓ Created minimal plugin.json (v{minimal['version']})")
    print(f"⚠ .claude-plugin/marketplace.json not found - skipping sync")
PYTHON_SCRIPT

cp README.md tars-cowork-plugin/README.md

cd tars-cowork-plugin
zip -q -r Archive.zip . -x "*.DS_Store" -x "__pycache__/*"
cd ..

echo "✓ Build complete: $(ls -lh tars-cowork-plugin/Archive.zip | awk '{print $5}')"
