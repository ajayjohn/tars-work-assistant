#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/.claude-plugin"

echo "Building TARS plugin for marketplace..."

# Step 1: Validate
echo "Step 1: Validating plugin structure..."
python3 "$SCRIPT_DIR/validate-plugin.py"
if [ $? -ne 0 ]; then
    echo "❌ Validation failed. Fix errors first."
    exit 1
fi

# Step 2: Sync files
echo "Step 2: Syncing files to .claude-plugin/..."
rsync -av --delete "$REPO_ROOT/skills/" "$PLUGIN_DIR/skills/"
rsync -av --delete "$REPO_ROOT/commands/" "$PLUGIN_DIR/commands/"
rsync -av --delete "$REPO_ROOT/reference/" "$PLUGIN_DIR/reference/"
cp "$REPO_ROOT/.mcp.json" "$PLUGIN_DIR/.mcp.json"

echo "✓ Files synced (marketplace.json stays at root only)"

# Step 3: Re-validate
echo "Step 3: Re-validating..."
python3 "$SCRIPT_DIR/validate-plugin.py"

echo ""
echo "✓ Plugin build complete!"
echo ""
echo "Next steps:"
echo "1. git add .claude-plugin/ && git commit -m 'Update plugin distribution'"
echo "2. git push"
echo "3. Test marketplace installation"
