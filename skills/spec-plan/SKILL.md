---
name: spec-plan
description: "Convert a feature design into executable tasks with dependencies, requirement/acceptance links, and observable completion conditions. Use for implementation planning or revising a managed task plan."
---

# Spec Plan

Read [the shared contract](../spec-workflow/references/contract.md) once. Read requirements, design, repository guidance, and existing task outcomes. Preserve IDs and completed valid work.

For managed work, put task state, dependency IDs, R/AC links, done_when, and evidence references in spec.json. In tasks.md use matching T-ID headings to describe scope, rationale, and intended checks; [the task structure](assets/tasks.md) illustrates the split. Avoid competing status tables.

Choose coherent independently verifiable changes, not one task per code line or one opaque task for a large feature. Prefer an early vertical slice when it tests a significant integration assumption. Plan actual migration, compatibility, docs, and regression work only where needed. Every active AC must have implementation or validation coverage; non-product infrastructure work still needs an explained link to the feature outcome.

Declare narrow source/test/configuration input paths and run the [structural checker](../spec-workflow/references/records.md). Resolve missing IDs, cycles, obsolete dependencies, orphan work, and uncovered criteria before marking the plan ready. Do not mark unimplemented work done. Planning-only requests end with the plan and next action.
