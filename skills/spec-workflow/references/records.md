# Machine records and CLI

## Authority and paths
Use spec.json alongside feature prose. Read [the worked example](example.md) for a complete record and the [formal schema](../assets/spec.schema.json) for editor/integration validation. schema_version is 2. Paths in artifacts, inputs, and command logs are relative to the project root supplied to --root. Use explicit project and feature paths, not the skill directory as the project root. Install all sibling skills together; the checker is in spec-workflow/scripts/spec_check.py. Python 3.10+ and the standard library are sufficient. Unknown core fields are rejected; put project-specific metadata in the optional extensions object.

## Record fields

For a new feature, the bundled `scripts/spec_project.py init` helper creates requirements.md and spec.json from a supplied goal and acceptance criterion. Existing files are preserved; records begin at the requirements stage with draft status. The helper uses this same checker to validate the initial structure. Continue by refining requirements and selecting the next authorized stage.

- feature: stable feature slug; mode: guided/autonomous; stage: requirements/design/plan/implement/verify/complete; stop_after: requirements through verify.
- next_action: concrete next step; blockers and decisions: string arrays, distinguishing confirmed decisions from assumptions in their wording. Optional pause_after_task: null or an existing T ID; record a task-specific stopping request here and clear it only after continuation authorization. An active pause boundary blocks completion checks.
- artifacts: requirements/design/tasks/verification objects with path and status. approved additionally needs approval recording the actual user statement and scope. Record only artifacts that exist. Requirements exist from the first stage, design from design, tasks from plan; verification is required at completion.
- requirements: id and active/retired status. criteria: id, active/retired status, requirements array.
- design: requirements array, listing the IDs addressed by design prose.
- tasks: id, state, depends_on IDs, requirements IDs, criteria IDs, done_when string, evidence IDs. Link at least one R or AC per active task. Superseded dependencies must be rewritten before starting dependents.
- inputs: project-relative files/directories needed to validate behavior. Empty inputs are allowed with a warning during prose-only planning, but completion requires declared validation inputs. Include source, tests, configuration, local dependency manifests and relevant data. Directory inputs include newly added files and omit .git and standard Python caches. Do not include the feature folder or a parent containing it; requirement/design/task prose and task contracts are automatically included. Do not use symlinks escaping the project. For documentation-only implementation, declare the actual target documentation files outside the feature records.
- evidence: array managed by record. Each record has stable E ID, criteria, kind, outcome, snapshot hashes, recording time, environment context, and either command/exit/log/digest or a manual observation. Retain old records as history. Task-only evidence may have an empty criteria array. Newer evidence for an AC supersedes older attempts for completion.

## Read-only check
```
python <skill-root>/spec-workflow/scripts/spec_check.py check <feature-folder> --root <project-root>
python <skill-root>/spec-workflow/scripts/spec_check.py check <feature-folder> --root <project-root> --complete
```
Structural check returns 0 when valid, 1 for validation findings, 2 for unreadable records or tool errors. --complete additionally requires finished tasks, ready/approved artifacts, no blockers, and current passing evidence for every active AC. Historical outdated evidence is a warning; a done task relying on it is an error. No recorded command is executed by check.

Add --json to check for structured diagnostics, including read/tool errors (exit 2). Argument parsing errors still follow normal CLI stderr behavior. The bundled shape validator implements the schema vocabulary actually used by the shipped schema; it is not a general-purpose JSON Schema engine.

## Execute and capture a check
```
python <checker> record <feature-folder> --root <project-root> --criteria AC-001 AC-002 -- python -m unittest discover -s tests
```
The -- delimiter is required for command recording. The command after it is executed directly with project root as cwd, without a shell. Unknown tool options are errors, never inferred executable names. Choose a command authorized by the task. Default timeout is 60 seconds; set --timeout when needed. Exit 0 records pass, a nonzero exit records fail, timeout or launch failure records blocked. Inputs changing during the run produce blocked evidence. A record invocation returns 0 only for a passing result and otherwise 1 (invalid arguments/records may return 2). Raw output is retained under the feature's .spec-evidence folder: avoid commands that print credentials. The tool does not edit task states or attach evidence IDs for you; update task references explicitly after inspecting results. The newest referenced task evidence must be current and passing; do not keep selecting an old pass after a later linked failure.

For actual manual observations:
```
python <checker> record <feature-folder> --root <project-root> --criteria AC-003 --manual "Observed the named behavior in the stated environment" --outcome pass
```
Record prints the E ID/result and, for command checks, the project-relative log location. Read that log before attaching acceptance claims. Manual records are attestations. Do not use them to bypass a failed command or unavailable runtime observation. External environment facts are not automatically fingerprinted. Check their continued validity when resuming.

## Interrupted or concurrent recording

Recording uses an exclusive .spec-record.lock and atomic .spec-record.tmp replacement. Do not edit spec.json while a record command is running. If another editor changes it, recording returns exit 2, preserves those edits, and retains the command output for reconciliation rather than overwriting the record.

After an interrupted process, inspect the lock's PID, check that no recording process is still running, and back up the feature record/logs. Inspect a remaining temporary file against spec.json before manually recovering or removing it. Remove a stale lock only after confirming no active recording. Orphaned logs are retained and their E IDs are not reused; a later valid record can capture a fresh check. Do not automatically delete lock files in hooks or treat an uncommitted log as passing evidence.

## Verification limits

This is a consistency and local evidence-freshness checker, not a semantic verifier, sandbox, approval system, or tamper-proof audit log. Coverage links and approval text are declarations, not proof. It cannot know an undeclared dependency changed or whether a green test actually exercises the linked criterion. No automatic code execution occurs during check.
