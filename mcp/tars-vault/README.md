# tars-vault MCP server

Validated write interface for the TARS Obsidian vault. Wraps `obsidian-cli`, enforces
the `tars-` frontmatter convention, chunks large appends at 40KB boundaries, runs
auto-wikilink, and exposes integration-registry resolution.

Status: **skeleton (Phase 1a/1b)**. Tool implementations land in later phases.

## Run

```
python -m tars_vault --vault /path/to/vault
```

Environment variables:

| Var | Meaning |
|-----|---------|
| `TARS_VAULT_PATH` | absolute path to the Obsidian vault (required if `--vault` omitted) |
| `TARS_OBSIDIAN_CLI` | override the `obsidian` binary path |
| `TARS_IN_HOOK` | recursion guard set by hooks |
| `TARS_DISABLE_TELEMETRY` | disable telemetry emission |

## Tools (Phase 1a registers names only; full implementations in later phases)

- `create_note`, `append_note`, `write_note_from_content`
- `update_frontmatter`, `search_by_tag`, `read_note`
- `archive_note`, `move_note`, `classify_file`, `detect_near_duplicates`
- `resolve_capability`, `refresh_integrations`
- `scan_secrets`, `fts_search`, `semantic_search`, `rerank`
