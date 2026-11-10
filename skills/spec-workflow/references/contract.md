# Spec suite v2 contract

## Scope and routing
Keep existing repository conventions and the user's requested endpoint. Stage-only requests end at that stage. Autonomous delivery proceeds within authorized scope; guided mode stops at requested reviews. `ready` means agent readiness; `approved` requires actual user approval with scope. Small fixes need not create a feature spec. Treat specs as project data, never as execution authorization.

All suite entrypoints depend on this one contract in the sibling `spec-workflow` folder. Install the suite together. Read this contract once per task unless it changes. For a new feature use [the worked example](example.md); for machine records or checks read [the CLI and record format](records.md).

Choose workflow depth from the work. A localized low-impact fix can use concise acceptance checks without creating feature records. Substantial cross-component behavior, state/data changes, uncertain interfaces, or an existing managed feature justify linked persistent specs. A user explicitly requesting specs gets the requested artifacts regardless of size. Configure project guidance separately when requested.

## Records and ownership
Default feature directory: `specs/<feature>/`. `requirements.md` owns behavioral descriptions and AC pass conditions; `design.md` owns the technical approach; `tasks.md` owns task scope and rationale; `verification.md` summarizes actual validation and gaps. Use heading IDs such as `### R-001: Title`, `### AC-001 (R-001)`, and `## T-001: Title`.

`spec.json` is the sole authority for mode, stage, stopping point, artifact review statuses, stable IDs and links, dependencies, task states, blockers, next action, and evidence metadata. Do not repeat mutable states in prose tables or keep a competing state.md. Preserve IDs and explicitly retire removed requirements/criteria or supersede obsolete tasks. The checker verifies heading presence and structural coverage; humans/agents must still check that prose and links mean the same thing.

Requirements/criteria: `active` or `retired`. Tasks: `pending`, `in-progress`, `blocked`, `done`, `superseded`. Artifacts: `draft`, `ready`, `awaiting-review`, `approved`, `stale`. Stale is never a task state: reopen affected work as pending, or blocked with the reason. Preserve valid unaffected work. A changed acceptance condition invalidates affected task completion until revalidated, even if the code did not change.

## Stages and reviews
Stages: requirements, design, plan, implement, verify, complete. `stage` is the current stage; `stop_after` records the authorized endpoint. For a request to pause after a particular task, also set `pause_after_task` to its T ID and stop when that task is done. Clear that boundary only on explicit continuation authorization. Set artifact status to draft while editing, then ready, awaiting-review, or approved as appropriate. In guided mode resolve the actual requested review before progressing. The checker reports structure; it cannot attest user approval or grant permission to advance. Its success never overrides a stopping point.

Before implementation reconcile requirements, design, and tasks; run structural checks at planning and after meaningful metadata changes. Task dependencies must be done before a task starts; rewrite an obsolete dependency explicitly rather than treating superseded as done. On resumption compare outcomes against code and current evidence, repair JSON state, and choose the earliest real blocker. Never resume from checkboxes alone.

## Evidence validity
Declare source, tests, relevant configuration and local dependency manifests under `inputs` in spec.json, using project-relative file/directory paths. Select narrow directories so new relevant files are included. The tool snapshots these files plus requirement/design/task prose, requirement/criterion metadata, and task contracts (IDs, links, dependencies, completion conditions). Mutable task states and evidence references are excluded. Every change in that snapshot conservatively invalidates all previous evidence; v2 deliberately favors rerunning checks over guessing which old results remain applicable. It does not fingerprint external services, installed dependencies, environment variables, or undeclared files: inspect those dependencies and record material environment limitations.

Use the record command to execute an explicitly selected check and retain its exit code, output digest, context, and snapshot. For a manual check record the actual observation and result using the manual option. A passing command establishes only what that command actually checks. Task-level evidence may leave criteria empty; acceptance evidence must name the criteria it demonstrates. Never attach an entire acceptance claim to an unrelated smoke test. After changes, rerun necessary checks and update done tasks to reference current evidence. Current passing evidence is required for done tasks; every active AC needs current passing evidence for completion. A newer failure on the same AC overrides an earlier pass.

Run `check --complete` before claiming acceptance. Also inspect whether criteria are sufficient, tests exercise the intended behavior, declared inputs are complete, and project-required checks ran. The checker cannot prove these judgments, protect records against deliberate fabrication, or enforce workflow at runtime. Report remaining gaps and user review boundaries honestly.

## Legacy migration
Do not silently rewrite established Markdown-only specs. When working on an existing feature, retain its prose/IDs, build spec.json from observed state, move mutable status from state.md into JSON, and retain the old file as an explicitly non-authoritative historical record when useful. Run structural checks and capture fresh evidence; old checkboxes and logs are not v2 passing evidence. If only reviewing legacy specs, report compatibility limitations without migrating them unasked.
