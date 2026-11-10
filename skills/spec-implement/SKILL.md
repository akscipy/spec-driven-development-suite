---
name: spec-implement
description: "Implement or continue an existing feature task plan, respecting dependencies and acceptance criteria while recording actual validation and progress. Use for authorized code changes against managed specs."
---

# Spec Implement

Read [the shared contract](../spec-workflow/references/contract.md) once. Reconcile requirements, design, task records, working-tree changes, and the latest user request before edits. Preserve unrelated user work.

Select a pending task whose dependencies are done, mark it in-progress, and implement the coherent outcome within its scope. Use existing architecture; avoid deferred features or opportunistic refactors. A routine implementation discovery may update design detail; a changed product contract requires spec-change analysis before dependent work.

Run appropriate project checks using the [evidence recorder](../spec-workflow/references/records.md). Task checks may leave criteria empty; acceptance evidence names only criteria genuinely demonstrated by that command. Inspect actual output before attaching an E ID. Mark done only with the intended outcome and current passing task evidence. Record blocked checks honestly.

Update JSON at milestones and honor requested task/stage pauses. Later source/spec/task-contract changes invalidate old snapshots: refresh evidence before relying on earlier done claims. Continue ready authorized tasks, not an indefinite retry loop on the same unexplained failure. Commits are optional unless requested or required by repository guidance. Finish authorized feature delivery through spec-verify; do not claim acceptance merely because tasks are checked done.
