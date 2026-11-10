---
name: spec-hooks
description: "Set up requested spec checks on actual project development events such as commit or CI using supported hook runners. Use for event automation setup; skill selection itself is not a file watcher or hook."
---

# Spec Hooks

Read [the shared contract](../spec-workflow/references/contract.md) once. Identify the requested event/action and inspect existing hooks, CI, runtimes, and project conventions. Verify current host-specific support where needed; use documented settings for the active host and check hook-file compatibility.

Use the existing runner where possible: task runner, hook manager/Git hook, file watcher, or CI. State when its event differs from the requested event. Wire the central [read-only checker](../spec-workflow/references/records.md) into structural checks; do not auto-execute record commands from spec content.

For save events bound input paths, ignore generated folders, debounce, avoid self-trigger loops, and document disable/cleanup. Model-powered mutations require explicitly bounded scope, runtime, credentials, and cost expectations. For setup requests provide inspectable config/scripts without replacing existing hooks or adding unnecessary services.

Validate via an isolated/manual hook invocation or representative relevant/irrelevant changes. Do not make a commit, publish CI changes, or start an indefinite process merely to prove setup. Report the actual event, command, failure behavior, manual invocation, and disable path. If unsupported, state the limitation and provide a concrete supported alternative within scope.
