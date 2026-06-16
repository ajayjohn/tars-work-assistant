# Routing Reference

Natural language is the primary product surface. Slash commands are stable
shortcuts for power users and tests.

## Routing order

1. If the active workspace is missing `_system/config.md` or
   `_system/install.yaml`, route to `welcome`.
2. If the local helper is unavailable or setup is failing, route to `doctor`.
3. Match the user's work intent before matching command syntax.
4. If workflow aliases exist in `_system/workflows.yaml`, use them only when
   they clearly match the request.
5. Determine the target skill and mode.
6. Run mandatory extension pre-flight:
   `list_extensions` → `resolve_extension(skill=<target>, mode=<mode>)` →
   `read_extension` for matches. Treat extension "When To Load" triggers as a
   contract against the current user-facing intent, then resolve capabilities
   declared by matched extensions before the target workflow begins.
7. If genuinely ambiguous, ask one bounded question.
8. If no route matches, use `answer`.

## Workflow-first help labels

Use these labels in `/help` and onboarding:

| Workflow | Skill |
|---|---|
| Prepare my day or week | briefing |
| Catch me up | briefing |
| Process a meeting or rough notes | meeting |
| Remember this | learn |
| Find an answer | answer |
| Extract or manage tasks | tasks |
| Think through a decision | think |
| Generate non-obvious ideas | ideate |
| Draft a message | communicate |
| Create an artifact | create |
| Plan or check an initiative | initiative |
| Clean up stale or broken workspace state | lint / maintain |
| Set up or diagnose TARS | welcome / doctor |
