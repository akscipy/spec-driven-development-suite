---
name: spec-steering
description: "Create or refine project-specific guidance for a requested spec-driven workflow, grounded in repository conventions and validation commands. Use for project guidance such as AGENTS.md or CLAUDE.md."
---

# Spec Steering

Read [the shared contract](../spec-workflow/references/contract.md) once. Inspect existing scoped guidance, manifests/CI, architecture docs, and representative code before proposing durable rules.

Capture only facts that change future decisions: product boundary, architecture constraints, source/test locations, real command syntax, spec location, and meaningful completion expectations. Label commands not actually run. Keep feature decisions in their own records.

When requested, narrowly merge guidance into the active host's project guidance file (for example AGENTS.md or CLAUDE.md) while preserving other instructions and nested scope. A concise routing note can prefer spec-workflow for substantial features, individual skills for stage-only work, and lightweight treatment of trivial changes. Apply guidance only to the requested project scope.

For v2 records document spec.json as mutable-state authority and link the central checker rather than copying its contract. Preserve the user's selected review mode; keep review requirements and invocation settings aligned with the request. Proposal-only requests return reviewable text without applying it. Report exact file/scope and material unverified assumptions.
