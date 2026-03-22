---
tags:
  - tars/system
tars-created: 2026-03-21
---

# Alias Registry

This file handles context-dependent name disambiguation. For simple aliases, use the `aliases` property directly on entity notes (Obsidian resolves these natively).

This registry is for cases where:
- The same short name maps to multiple people (e.g., "Dan" → Dan Rivera or Dan Chen)
- Team or product abbreviations need canonical resolution
- Context determines which entity is meant

## Ambiguous Names

| Short Name | Default Resolution | Context Override |
|-----------|-------------------|-----------------|
| <!-- Example: Dan | [[Dan Rivera]] | infrastructure → [[Dan Chen]] --> |

## Team Abbreviations

| Abbreviation | Canonical |
|-------------|-----------|
| <!-- Example: eng | Engineering --> |

## Product Abbreviations

| Abbreviation | Canonical |
|-------------|-----------|
| <!-- Example: DP | [[Data Platform]] --> |

## Resolution Protocol

When encountering a name:

1. **Check Obsidian aliases** (Layer 1): `obsidian search query="[name]" limit=5`
2. **Check this registry** (Layer 2): Look for direct match, apply context override if applicable
3. **Search fallback** (Layer 3): `obsidian search query="[name]" limit=5` — present matches to user
4. **Ask user** (Layer 4): If still ambiguous, present multiple-choice:
   ```
   Who is '[name]' in this context?
     1. [Person A] (role/team)
     2. [Person B] (role/team)
     3. Someone new — I'll provide details
   ```
5. **After resolution**: Add confirmed new aliases to this registry and to the entity's `aliases` property
