---
name: spec-requirements
description: "Define or refine feature requirements, scope, and testable acceptance criteria from a request. Use when desired behavior needs clarification before design, including requirements-only requests."
---

# Spec Requirements

Read [the shared contract](../spec-workflow/references/contract.md) once. Ground behavior in the request, current code, existing specs, and relevant discovery.

Write requirements.md with the user outcome, scope, exclusions, stable R IDs, and AC IDs linked to requirements. Each criterion needs a trigger or starting state and an observable pass condition that distinguishes correct from plausible incorrect behavior. Include meaningful boundary/error cases; include quantitative performance, permissions, accessibility, or data constraints only when the feature depends on them. Do not turn guessed thresholds or technologies into commitments.

Resolve material ambiguity using repository evidence before asking. Keep low-risk assumptions explicit; surface conflicts that affect scope or acceptance. Use [the skeleton](assets/requirements.md) when helpful, not as boilerplate to preserve unchanged.

For substantial managed work, create/update spec.json using [the record format](../spec-workflow/references/records.md) and [worked example](../spec-workflow/references/example.md). Register IDs and links, mode, endpoint, requirements artifact status, and next action. No tasks or runtime evidence need be invented yet. Prose-only requests can stay prose-only. In guided mode mark awaiting-review and stop; otherwise ready is agent readiness, not user approval.

For a new feature, use [the initializer](../spec-workflow/scripts/spec_project.py) with the user's goal and a concrete first criterion when useful. It creates draft records; add the remaining behavior, scope and edge cases before marking requirements ready or awaiting review. Existing specs should be revised in place.
