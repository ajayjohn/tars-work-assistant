# TARS Build System Documentation

## Overview

TARS uses a **source-based build system** where the GitHub repository contains the complete plugin specification, but the Cowork distribution uses a minimal configuration that relies on auto-discovery.

The repository is also configured as a **marketplace**, allowing users to subscribe and receive automatic updates when new versions are pushed to GitHub.

## Key Principle

**Single Source of Truth**: `.claude-plugin/plugin.json` in the repository root contains the complete plugin specification. All build processes derive values from this file.

## Why Minimal Distribution?

Cowork **auto-discovers** skills and commands from the directory structure. Including explicit `skills` and `commands` arrays in the distribution `plugin.json` **breaks** plugin loading.

**Repository version** (with arrays):
```json
{
  "name": "tars",
  "version": "2.0.0",
  "skills": ["skills/core/SKILL.md", ...],
  "commands": ["commands/welcome.md", ...]
}
```

**Distribution version** (minimal, auto-discovery):
```json
{
  "name": "tars",
  "version": "2.0.0",
  "description": "...",
  "author": {...},
  "license": "Apache-2.0"
}
```

## Build Processes

### 1. Local Build (`build-plugin.sh`)

**Purpose**: Create a Cowork-installable plugin in `tars-cowork-plugin/`

**Usage**:
```bash
./build-plugin.sh
```

**What it does**:
1. Reads `.claude-plugin/plugin.json` (source)
2. Extracts: name, version, description, author, license
3. Copies: skills/, commands/, scripts/, reference/, LICENSE, .mcp.json
4. Generates minimal `plugin.json` in distribution
5. Creates `Archive.zip`

**Output**: `tars-cowork-plugin/` folder ready for Cowork installation

### 2. Git Pre-Push Hook (`.git/hooks/pre-push`)

**Purpose**: Automatically rebuild distribution before pushing to GitHub

**Trigger**: Runs automatically on `git push`

**What it does**:
1. Runs `./build-plugin.sh`
2. If build fails, aborts the push
3. If build succeeds, continues with push

**Note**: The `tars-cowork-plugin/` folder is gitignored, so only source files are pushed.

### 3. GitHub Actions Release (`.github/workflows/release.yml`)

**Purpose**: Create official plugin releases on GitHub

**Trigger**:
- Manual workflow dispatch
- Push to `main` branch that changes `.claude-plugin/plugin.json`

**What it does**:
1. Runs test suite (`tests/run-all.sh --full`)
2. Extracts version from source `plugin.json`
3. Checks if tag already exists (skip if yes)
4. Creates temporary build directory
5. **Generates minimal plugin.json** (same logic as local build)
6. Creates `tars-vX.Y.Z.zip` with Cowork-compatible structure
7. Extracts changelog for release notes
8. Creates git tag (`vX.Y.Z`)
9. Creates GitHub release with archive

**Output**: GitHub release with downloadable `tars-vX.Y.Z.zip`

## File Structure

### Repository (GitHub)
```
tars/
├── .claude-plugin/
│   └── plugin.json          # SOURCE OF TRUTH (with arrays)
├── .github/workflows/
│   └── release.yml           # CI/CD for releases
├── .git/hooks/
│   └── pre-push             # Auto-rebuild before push
├── skills/                   # 12 skill definitions
├── commands/                 # 11 command definitions
├── scripts/                  # Utility scripts
├── reference/                # Reference files
├── tests/                    # Test suite
├── build-plugin.sh          # Local build script
├── .gitignore               # Ignores tars-cowork-plugin/
└── ...
```

### Distribution (Cowork)
```
tars-cowork-plugin/
├── .claude-plugin/
│   └── plugin.json          # MINIMAL (no arrays)
├── skills/                   # Copied from source
├── commands/                 # Copied from source
├── scripts/                  # Copied from source
├── reference/                # Copied from source
├── Archive.zip              # Compressed distribution
├── LICENSE
├── .mcp.json
└── README.md
```

## Updating the Plugin

### To change version, description, or metadata:

1. Edit `.claude-plugin/plugin.json` (repository root)
2. Update `CHANGELOG.md` with release notes
3. Commit changes
4. Push to GitHub

```bash
# Pre-push hook automatically rebuilds tars-cowork-plugin/
git add .claude-plugin/plugin.json CHANGELOG.md
git commit -m "Bump version to 2.1.0"
git push origin main

# GitHub Actions automatically creates release if version changed
```

### To test local build:

```bash
./build-plugin.sh
# Installs tars-cowork-plugin/ in Cowork to test
```

## Troubleshooting

### Plugin installs but shows no skills

**Cause**: Distribution `plugin.json` has `skills` or `commands` arrays

**Fix**: Rebuild using `./build-plugin.sh` (already fixed)

### GitHub release has wrong plugin.json

**Cause**: Old workflow zipped source files directly

**Fix**: Workflow now creates minimal version (already fixed)

### Build script breaks after editing source

**Cause**: Python parsing failed or source JSON malformed

**Fix**: Validate `.claude-plugin/plugin.json` is valid JSON:
```bash
python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"
```

## Version Bumping

Use the provided script:
```bash
python3 scripts/bump-version.py 2.1.0
# Updates plugin.json, creates git tag, updates changelog
```

## Marketplace Configuration

### What is `marketplace.json`?

The `.claude-plugin/marketplace.json` file defines this repository as a Cowork marketplace. Users can subscribe to the marketplace URL and receive automatic plugin updates.

**Location**: `.claude-plugin/marketplace.json` (NOT in the repository root)

**Structure**:
```json
{
  "name": "TARS Marketplace",
  "description": "...",
  "plugins": [
    {
      "name": "tars",
      "version": "2.0.0",  // Synced from plugin.json
      "source": {
        "type": "git",
        "url": "https://github.com/ajayjohn/tars-work-assistant.git"
      }
    }
  ]
}
```

### Version Synchronization

The version in `.claude-plugin/marketplace.json` is **automatically synced** from `.claude-plugin/plugin.json`:

- **Local build**: `./build-plugin.sh` syncs marketplace version
- **GitHub Actions**: Release workflow syncs and commits marketplace.json
- **Single source of truth**: Only edit version in `.claude-plugin/plugin.json`
- **Important**: marketplace.json always lives in `.claude-plugin/` alongside plugin.json

### How Users Subscribe

1. Open **Cowork → Settings → Marketplaces**
2. Click **"Add Marketplace"**
3. Enter: `https://github.com/ajayjohn/tars-work-assistant`
4. TARS appears in plugin list with automatic updates

When you push a new version to GitHub, subscribed users receive update notifications.

## Summary

- **Repository**: Full specification (documentation + validation) + marketplace
- **Distribution**: Minimal config (runtime compatibility)
- **Build**: Automated via script, pre-push hook, and CI/CD
- **Source**: `.claude-plugin/plugin.json` is the single source of truth
- **Marketplace**: `.claude-plugin/marketplace.json` automatically synced from plugin.json
