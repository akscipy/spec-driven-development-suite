---
name: spec-change
description: "Analyze and propagate a change to an established feature spec across requirements, design, tasks, and acceptance evidence. Use for changed intent or material implementation/spec divergence, not routine implementation details."
---

# Spec Change

Read [the shared contract](../spec-workflow/references/contract.md) once. Identify what changed and trace existing R/AC/T links, design contracts, implementation, consumers, data, and validation evidence. Distinguish an implementation defect from a change in desired behavior.

For analysis-only work report proposed changes and impacts, optionally in impact.md; do not silently edit authoritative records. When the change is authorized, update the affected prose/JSON before dependent implementation. Preserve stable IDs, retire removed R/AC IDs, supersede obsolete tasks, and add explicit migration/rework tasks where needed. Preserve history instead of rewriting past outcomes as if they matched the new request.

Reopen invalidated done tasks as pending or blocked, and mark affected downstream artifacts stale. The conservative fingerprint invalidates all evidence when declared inputs, behavior prose, or task contracts change; keep historical records and recapture required checks rather than promising selective reuse. Unaffected task outcomes can be preserved but still need current evidence before completion.

Run the [structural checker](../spec-workflow/references/records.md), check new acceptance coverage, record remaining decisions and next action, and honor the user's review boundaries. Do not reset the entire feature or demand blanket reapproval for a narrow change.
