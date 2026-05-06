# tars-vault MCP server

Validated write interface for the TARS Markdown workspace. It writes files directly,
enforces the `tars-` frontmatter convention, chunks large appends at 40KB boundaries,
runs wikilink validation, and exposes integration-registry resolution.

Status: active MCP server used by TARS skills.

## Run

```
python -m tars_vault --vault /path/to/workspace
```

Environment variables:

| Var | Meaning |
|-----|---------|
| `TARS_VAULT_PATH` | absolute path to the TARS Markdown workspace (required if `--vault` omitted) |
| `TARS_IN_HOOK` | recursion guard set by hooks |
| `TARS_DISABLE_TELEMETRY` | disable telemetry emission |

## Tools

- `create_note`, `append_note`, `write_note_from_content`
- `update_frontmatter`, `search_by_tag`, `read_note`
- `archive_note`, `move_note`, `classify_file`, `detect_near_duplicates`
- `resolve_capability`, `refresh_integrations`
- `scan_secrets`, `fts_search`, `semantic_search`, `rerank`
