<!-- Copyright 2026 Ajay John. Licensed under PolyForm Noncommercial 1.0.0. See LICENSE. -->

# TARS Extension Architecture

Status: design proposal for review.

This document defines a general extension model for TARS. The goal is to let
TARS use provider-specific tools, MCPs, templates, and workflow playbooks while
keeping the core framework vendor-agnostic and preventing plugin/workspace path
confusion.

## Goals

- Keep core TARS skills canonical and provider-agnostic.
- Let default commands such as `/maintain`, `/meeting`, `/briefing`, `/answer`,
  and `/create` discover relevant extensions without the user naming them.
- Support installable extensions distributed from the TARS GitHub repository.
- Support workspace extensions created or edited by the user.
- Let Claude build a workspace extension from vendor docs or tool specs when the
  user asks.
- Prevent any command from assuming plugin skills live in the workspace or
  extensions live in the plugin install path.
- Keep all persistence and side effects under the existing review gates and
  `tars-vault` write discipline.

## Non-goals

- Extensions are not peer replacements for core TARS skills.
- Extensions do not get automatic workspace write privileges.
- Extensions do not add slash commands in the first version.
- Extensions do not alter the core router directly.
- Extensions are not loaded from arbitrary paths.

## Core Idea

TARS should treat extensions as subordinate capability modules loaded by core
skills at explicit extension points.

Core skills still own workflow authority:

- `maintain` owns inbox, sync, archive, gaps, and review queues.
- `meeting` owns meeting ingestion and durable meeting persistence.
- `create` owns artifact planning, review, and companion-note creation.
- `answer` owns retrieval ordering and evidence standards.
- `briefing` owns schedule, tasks, memory, and re-entry synthesis.

Extensions provide provider-specific or domain-specific instructions that a core
skill may consult after it has already selected the workflow.

## Path Model

TARS must distinguish three roots at all times.

| Root | Meaning | Example contents |
|---|---|---|
| Plugin root | Installed TARS framework package | `skills/`, `commands/`, `mcp/tars-vault/`, hooks |
| Workspace root | User's local Markdown workspace | `memory/`, `journal/`, `_system/`, `extensions/` |
| Runtime cwd | Current Claude session folder | May equal workspace root, but must not be trusted by itself |

The active workspace root is the path recorded in `_system/install.yaml` as
`workspace_path`. TARS should never search the local machine to guess this
path after setup.

Claude exposes the current plugin install location through
`${CLAUDE_PLUGIN_ROOT}`. TARS may use this environment variable only for core
framework files such as hooks, command wrappers, scripts, and the local helper.
The plugin root is dynamic across Claude starts and must not be treated as
extension state.

Neither root should be inferred from the other.

Recommended extension locations:

```text
# Installed into the user's workspace and controlled by the user.
<workspace-root>/extensions/

# Runtime registry and enablement state.
<workspace-root>/_system/extensions.yaml
```

Rules:

- Core skills are loaded only from `<plugin-root>/skills/`.
- Extensions are loaded only from `<workspace-root>/extensions/`.
- Extension state is stored only in `<workspace-root>/_system/extensions.yaml`.
- The TARS GitHub repository may host curated extensions, but installing one
  copies it into the workspace extension root.
- Plugin releases must not rely on runtime extensions living under the plugin
  root.
- Workspace writes still go through `mcp__tars_vault__*`.
- Extension discovery must fail closed if workspace path resolution is
  ambiguous or mismatched.

## Extension Types

### Provider Adapter

Provider adapters translate a broad TARS capability into provider-specific tool
usage.

Examples:

- `meeting-recording.demo`
- `meeting-recording.fireflies`
- `calendar.google`
- `tasks.todoist`
- `documentation.confluence`

Provider adapters may describe:

- tool detection signals
- required and optional MCP tools
- argument conventions
- API limitations
- review-queue shape
- degradation behavior
- safety constraints

Provider adapters must not:

- bypass capability resolution
- bypass review gates
- directly write workspace files
- rename, create, update, or delete external provider data unless the core skill
  explicitly requested that side effect and the user approved it

### Workflow Extension

Workflow extensions add domain-specific playbooks under an existing core skill.

Examples:

- `maintain.inbox.meeting-notes-enrichment`
- `meeting.sales-discovery`
- `briefing.exec-weekly-review`
- `answer.customer-escalation-research`

Workflow extensions may add classification rules, review checklist items, and
specialized extraction guidance. They do not replace the parent workflow.

### Output Template Pack

Template packs add structures that `/create`, `/communicate`, or `/meeting` can
use when generating reviewed output.

Examples:

- board memo pack
- customer escalation pack
- product launch pack
- incident postmortem pack

Template packs may include markdown templates, style guidance, and companion
frontmatter defaults. Rendered artifacts still follow `/create`'s core review
and filing flow.

### Retrieval Pack

Retrieval packs provide scoped search bundles for domains that need consistent
evidence gathering.

Examples:

- customer health lookup
- release readiness lookup
- hiring-loop lookup

Retrieval packs describe which workspace tags, folders, capabilities, and
external sources are relevant. They do not change the global retrieval order
unless the parent core skill adopts the pack for the current request.

### Validation Pack

Validation packs add checks that `/lint` or `/maintain weekly` can surface as
review items.

Examples:

- CRM note completeness
- launch checklist drift
- support escalation hygiene

Validation packs produce findings. They do not auto-fix.

## Extension Manifest

Each extension directory should contain `extension.yaml`.

Example:

```yaml
id: meeting-recording.demo
name: Demo Meeting Recording Adapter
version: "1.0.0"
tars_extension_version: "1"
type: provider-adapter
status: enabled

capabilities:
  - meeting-recording

applies_to:
  skills:
    - maintain
    - meeting
  modes:
    - inbox
    - sync

provider:
  name: demo-recording
  detection:
    server_name_patterns:
      - "demo-recording"
    tool_name_patterns:
      - "list_meetings"
      - "get_transcript"
      - "get_meeting_assets"

entrypoints:
  instructions: instructions.md
  tool_contract: tool-contract.yaml
  review_schema: review-schema.yaml

safety:
  requires_review: true
  may_write_workspace: false
  may_mutate_external_provider: false
```

Required fields:

- `id`
- `name`
- `version`
- `tars_extension_version`
- `type`
- `capabilities`
- `applies_to`
- `entrypoints.instructions`
- `safety.requires_review`

The manifest is intentionally small. Extension-specific details belong in
referenced files so TARS can load only the relevant pieces.

## Registry

`_system/extensions.yaml` is the workspace-local registry. It records enabled
extensions and install provenance.

Example:

```yaml
version: "1"
extensions:
  meeting-recording.demo:
    enabled: true
    source: catalog
    root: workspace
    path: extensions/provider-adapters/meeting-recording.demo
    installed_version: "1.0.0"
  meeting-recording.fireflies:
    enabled: true
    source: local
    root: workspace
    path: extensions/provider-adapters/meeting-recording.fireflies
    installed_version: "0.1.0"
```

The registry stores workspace-relative paths only. It must never store
plugin-root paths as extension paths.

## Loading Order

Core skills load extensions only after selecting the parent workflow.

Recommended order:

1. Load the core skill and mode reference.
2. Resolve broad capability with `mcp__tars_vault__resolve_capability`.
3. Ask the extension resolver for enabled extensions matching:
   - skill
   - mode
   - capability
   - detected provider/tool shape
4. If multiple enabled workspace extensions match, apply the conflict rules.
5. Load the extension's `instructions.md`.
6. Apply extension guidance under the parent skill's non-negotiables.
7. Surface review output through the parent skill's normal review queue.

Extensions should be invisible in normal user interaction unless:

- an extension is missing and the workflow cannot proceed,
- an extension has ambiguous provider matches,
- an extension requests a side effect requiring approval,
- or the user asks to inspect/manage extensions.

## Resolver Contract

The local helper exposes extension-aware tools:

- `list_extensions`
- `resolve_extension`
- `read_extension`
- `validate_extension`
- `install_extension`
- `scaffold_extension`

These tools are owned by `tars-vault` because path safety is the central risk.
Skills should not manually walk plugin and workspace extension folders.

`resolve_extension` should return only metadata plus safe relative entrypoint
references. `read_extension` should read a single approved file from one
resolved extension id.

## Creating Extensions On The Fly

When the user asks Claude to build an extension:

1. Core TARS routes to a future extension-authoring workflow.
2. Claude reads the provided tool specs or vendor docs.
3. Claude scaffolds a workspace extension under
   `<workspace-root>/extensions/<type>/<provider-or-domain>/`.
4. Claude writes an `extension.yaml`, `instructions.md`, and any optional
   contract files.
5. TARS validates the manifest and path boundaries.
6. The extension is disabled by default if validation has warnings, enabled if
   validation is clean and the user approves.
7. TARS records it in `_system/extensions.yaml`.

The first version can implement authoring as a `/maintain` or `/welcome`
subflow. A later version may add a dedicated extension command.

## Extension Catalog

The TARS GitHub repository can host reviewed extension sources under:

```text
extensions/
  provider-adapters/
  workflow/
  templates/
  retrieval/
  validators/
```

These are catalog sources, not plugin-runtime extensions. Installing one copies
or syncs it into `<workspace-root>/extensions/` and records it in
`_system/extensions.yaml`. Users can customize an installed extension in the
workspace, or install a second extension with a different id.

## Conflict Rules

| Conflict | Resolution |
|---|---|
| Same extension id installed twice in the workspace registry | Validation fails until one registry entry is disabled or removed |
| Two enabled workspace extensions match same provider with same confidence | Ask user to choose once and persist preference |
| Extension requests side effect disallowed by parent skill | Parent skill wins; side effect is blocked |
| Extension references a missing MCP tool | Degrade and surface missing capability |
| Extension path escapes allowed root | Validation fails |
| Extension tries to redefine a core command | Validation fails |
| Extension tries to replace a core skill | Validation fails |

## Review Queue Shape

Extensions should emit structured proposals, not final mutations.

Generic proposal fields:

```yaml
extension_id: meeting-recording.demo
parent_skill: maintain
mode: inbox
proposal_type: external_enrichment
confidence: high
source_refs: []
proposed_changes: []
requires_user_choice: false
blocked_by: []
manual_steps: []
```

The parent skill decides how to display, approve, persist, or discard the
proposal.

## Migration Plan

Phase 1: Architecture and registry

- Done: add this architecture.
- Done: add workspace-only extension path conventions.
- Done: add `_system/extensions.yaml` seed in new workspaces.
- Done: add extension directory validation.

Phase 2: Resolver

- Done: add `tars-vault` tools for listing, resolving, reading, validating,
  scaffolding, and installing extensions.
- Done: ensure resolver responses include root type: `workspace`.
- Done: add tests proving extension registry paths are workspace-relative and
  plugin-root paths are rejected.

Phase 3: Core skill integration

- Update `maintain`, `meeting`, `create`, `answer`, `briefing`, and `lint` to
  load extensions through explicit extension points.
- Keep extension loading behind mode-specific references to protect baseline
  context size.

Phase 4: Authoring workflow

- Add extension scaffolding and validation.
- Let users build workspace extensions from vendor specs or tool docs.
- Keep generated extensions disabled until validation and approval pass.

Phase 5: Catalog installation

- Publish first catalog extensions from the repository.
- Add catalog docs and release validation.
- Add install/update semantics that copy catalog extensions into the workspace.

## First Pilot

The first pilot should be a provider adapter under `meeting-recording`. It
should prove:

- provider-specific tools can be used without core skill vendor coupling,
- default commands discover the adapter automatically,
- output is review-only,
- workspace and plugin roots never collide,
- catalog-installed extensions behave the same as locally authored extensions.

A meeting-recording provider adapter is a good pilot after the extension
foundation exists, but this architecture should remain provider-neutral.
