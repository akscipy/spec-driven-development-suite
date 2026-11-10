# Quality checks

## Review areas

| Area | Checks |
| --- | --- |
| Skills | Clear task matching, appropriate workflow depth, stage boundaries, and connected records |
| Feature records | Valid fields, stable IDs, complete links, feasible task dependencies, and consistent state |
| Evidence | Current source/specification snapshots, retained failed checks, and clear manual observations |
| Recording | Interrupted writes, concurrent edits, command arguments, and output paths |
| Installation | File ownership, local-edit detection, update backups, removal, rollback, and unrelated-file preservation |
| Distribution | Required resources, matching versions, archive contents, file hashes, and repeatable builds |
| Documentation | Installation, usage, recovery, supported environments, examples, and measured limits |

## Validation method

Use automated tests for deterministic tool behavior and separate agent sessions for workflow checks. Keep evaluator tests outside solver projects. Report executed checks separately from planned checks, and preserve failed results as evidence.

## Design

The twelve skill entrypoints share one workflow contract. Individual stages can be used separately. Persistent feature records suit substantial work; localized fixes can use concise acceptance checks. Evidence snapshots invalidate older results when declared inputs or specification contracts change.

The tools use the Python standard library. Installation tracks owned files and preserves local changes. Checks validate structure and local evidence freshness; they do not establish whether acceptance criteria are sufficient or whether a test genuinely demonstrates its linked requirement.

## Results

See [the validation report](RELEASE-REPORT.md) for executed checks, findings, corrections, and coverage limits.
