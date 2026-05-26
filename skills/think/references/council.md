# Council Reference

Use when the user asks for multiple perspectives, pressure testing, or a
deliberate disagreement pass.

Subagents may explore viewpoints, but each returns bounded JSON:

- `stance`
- `strongest_argument`
- `failure_mode`
- `evidence_needed`
- `recommendation`

The main agent compares the outputs, resolves contradictions, and gives the
user one synthesized view. Subagents do not write workspace state.
