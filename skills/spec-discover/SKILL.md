---
name: spec-discover
description: "Investigate an existing repository for a proposed feature: map actual code paths, reusable components, constraints, and validation commands. Use before design when repository context is missing; do not change application code."
---

# Spec Discover

Read [the shared contract](../spec-workflow/references/contract.md) once. Establish the feature question and inspect relevant repository instructions, manifests, entry points, modules, and tests. Search narrowly; trace a real feature-relevant path from entry point to output/storage when one exists.

Capture observations with file references, existing components to reuse, extension points, compatibility constraints, and actual validation commands. Distinguish discovered commands from executed commands, facts from inferred architecture, and an absent search match from proof of absence. Identify source/test/configuration paths that later need inclusion in validation inputs.

Write discovery.md only if a durable feature report is useful or requested. A discovery-only request does not require spec.json or app edits. For a greenfield project capture confirmed constraints and unresolved foundations without inventing an existing architecture. End with the specific uncertainty resolved and the next design/requirements decision.
