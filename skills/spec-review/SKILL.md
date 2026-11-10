---
name: spec-review
description: "Review feature specs or spec-conformance for contradictions, missing acceptance coverage, and material implementation risks. Use for an explicitly requested spec/conformance review; general code review need not use this workflow."
---

# Spec Review

Read [the shared contract](../spec-workflow/references/contract.md) once. Establish whether the review covers documents, implementation conformance, or both. Inspect actual relevant artifacts/code, not just task summaries.

For managed records run the [read-only structural checker](../spec-workflow/references/records.md), then assess what it cannot: sufficient observable criteria, grounded design choices, compatible contracts, useful task decomposition, and whether recorded tests demonstrate the intended outcomes. For legacy specs report findings without forcing migration.

Prioritize concrete defects with a triggering scenario, impact, file/line or stable-ID reference, evidence, and a correction direction. Label uncertainty. Omit style preferences and speculative concerns without a credible failure path. Separate structural findings from behavioral findings and state material review limits.

A review-only request leaves specs/code unchanged; write review.md only if a persistent report is requested or useful within scope. If fixes are separately authorized, recheck affected acceptance behavior and distinguish resolved findings from open ones. If no actionable findings remain, say so without implying exhaustive correctness.
