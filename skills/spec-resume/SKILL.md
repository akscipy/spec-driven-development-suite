---
name: spec-resume
description: "Resume interrupted feature work or report its actual status by reconciling specs, working code, tasks, and validation evidence. Use when continuing a managed feature after a pause or handoff."
---

# Spec Resume

Read [the shared contract](../spec-workflow/references/contract.md) once. Locate the intended feature from context; ask if multiple candidates remain equally plausible rather than arbitrarily editing one.

Read spec.json, feature prose, repository guidance, current changes, relevant commits, and actual logs. Run the [read-only checker](../spec-workflow/references/records.md). Compare claimed done outcomes with code, current acceptance behavior, and evidence freshness. Missing implementation reopens a task; missing evidence leaves it unverified. Do not overwrite user edits to recreate a former plan or restart requirements automatically.

A status-only request reports proposed corrections without mutating state or implementing work. With continuation authorization, reconcile JSON conservatively, preserve valid outcomes, and resume the earliest genuine dependency. Clear a prior task pause only when the new request authorizes continuation. Preserve mode and any still-requested reviews; never infer earlier user approval from ready status.

Use spec-change for new intent, then read the appropriate next stage skill. For legacy records follow the contract's migration procedure only if migration is within scope. Report precise blockers when missing input prevents progress; continue useful independent work when possible.
