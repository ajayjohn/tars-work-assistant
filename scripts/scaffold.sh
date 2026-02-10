#!/usr/bin/env bash
# TARS workspace scaffolding script.
#
# Creates the directory structure for a TARS workspace.
# Verifies integration availability (remindctl, Eventlink).
# Copies reference templates from the plugin source.
#
# Usage: scaffold.sh <workspace_path> [plugin_path]
#   workspace_path: Where to create the workspace (required)
#   plugin_path:    Path to the TARS plugin source (default: script's parent dir)
#
# Output: JSON report of created directories and integration status.

set -euo pipefail

WORKSPACE="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="${2:-$(dirname "$SCRIPT_DIR")}"

# ─── Create directories ───────────────────────────────────────────

DIRS=(
    "memory/people"
    "memory/vendors"
    "memory/competitors"
    "memory/products"
    "memory/initiatives"
    "memory/decisions"
    "memory/organizational-context"
    "journal"
    "contexts/products"
    "contexts/artifacts"
    "reference"
    "inbox/pending"
    "inbox/processing"
    "inbox/completed"
    "inbox/failed"
)

created=0
existed=0

for dir in "${DIRS[@]}"; do
    target="$WORKSPACE/$dir"
    if [ ! -d "$target" ]; then
        mkdir -p "$target"
        ((created++))
    else
        ((existed++))
    fi
done

# ─── Copy reference templates ─────────────────────────────────────

templates_copied=0
TEMPLATES=(
    "reference/taxonomy.md"
    "reference/replacements.md"
    "reference/kpis.md"
    "reference/integrations.md"
    "reference/schedule.md"
)

for tmpl in "${TEMPLATES[@]}"; do
    src="$PLUGIN_DIR/$tmpl"
    dst="$WORKSPACE/$tmpl"
    if [ -f "$src" ] && [ ! -f "$dst" ]; then
        cp "$src" "$dst"
        ((templates_copied++))
    fi
done

# ─── Create empty indexes if missing ─────────────────────────────

MEMORY_CATS=("people" "vendors" "competitors" "products" "initiatives" "decisions" "organizational-context")

indexes_created=0
for cat in "${MEMORY_CATS[@]}"; do
    idx="$WORKSPACE/memory/$cat/_index.md"
    if [ ! -f "$idx" ]; then
        display_name=$(echo "$cat" | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')
        cat > "$idx" << INDEXEOF
# ${display_name} index

| Name | Aliases | File | Summary | Updated |
|------|---------|------|---------|---------|
INDEXEOF
        ((indexes_created++))
    fi
done

# Master memory index
if [ ! -f "$WORKSPACE/memory/_index.md" ]; then
    cat > "$WORKSPACE/memory/_index.md" << 'MASTEREOF'
# Memory index

| Category | Path | Count |
|----------|------|-------|
| People | memory/people/ | 0 |
| Initiatives | memory/initiatives/ | 0 |
| Decisions | memory/decisions/ | 0 |
| Products | memory/products/ | 0 |
| Vendors | memory/vendors/ | 0 |
| Competitors | memory/competitors/ | 0 |
| Organizational Context | memory/organizational-context/ | 0 |
MASTEREOF
    ((indexes_created++))
fi

# Contexts indexes
if [ ! -f "$WORKSPACE/contexts/products/_index.md" ]; then
    cat > "$WORKSPACE/contexts/products/_index.md" << 'EOF'
# Product specifications index

| Name | Status | Owner | Summary | Updated |
|------|--------|-------|---------|---------|
EOF
    ((indexes_created++))
fi

if [ ! -f "$WORKSPACE/contexts/artifacts/_index.md" ]; then
    cat > "$WORKSPACE/contexts/artifacts/_index.md" << 'EOF'
# Artifacts index

| Name | Type | Created | Source | Summary |
|------|------|---------|--------|---------|
EOF
    ((indexes_created++))
fi

# ─── Verify integrations ─────────────────────────────────────────

remindctl_status="not_found"
if command -v remindctl &> /dev/null; then
    if remindctl list Active --json &> /dev/null; then
        remindctl_status="configured"
    else
        remindctl_status="found_but_error"
    fi
fi

eventlink_status="not_found"
# Try to read Eventlink config from integrations.md
if [ -f "$WORKSPACE/reference/integrations.md" ]; then
    # Extract base URL - look for localhost:PORT pattern
    eventlink_url=$(grep -oP 'http://localhost:\d+' "$WORKSPACE/reference/integrations.md" 2>/dev/null | head -1)
    if [ -n "$eventlink_url" ]; then
        # Try a quick health check
        if curl -s --max-time 3 "$eventlink_url/events.json?date=$(date +%Y-%m-%d)&offset=1" &> /dev/null; then
            eventlink_status="configured"
        else
            eventlink_status="found_but_unreachable"
        fi
    fi
fi

# ─── Output JSON report ──────────────────────────────────────────

cat << JSONEOF
{
  "workspace": "$WORKSPACE",
  "directories": {
    "created": $created,
    "existed": $existed,
    "total": $(( created + existed ))
  },
  "templates": {
    "copied": $templates_copied
  },
  "indexes": {
    "created": $indexes_created
  },
  "integrations": {
    "remindctl": "$remindctl_status",
    "eventlink": "$eventlink_status"
  }
}
JSONEOF
