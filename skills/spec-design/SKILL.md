---
name: spec-design
description: "Design an implementation for feature requirements, grounded in repository architecture, interfaces, compatibility, failure behavior, and verification. Use for technical design rather than inventing product requirements."
---

# Spec Design

Read [the shared contract](../spec-workflow/references/contract.md) once. Inspect requirements and actual relevant code. When behavior is underspecified, capture agreed behavior or resolve the consequential gap before designing around it.

Write design.md with the chosen approach, affected component responsibilities, changed input/output contracts, and relevant state/data flows. Explain meaningful alternatives where a real tradeoff exists. Address error handling, compatibility, migration/rollback, or trust boundaries where the change requires them. Name observed files separately from proposed files; reuse project conventions rather than adding services or dependencies by habit.

Map active requirements to design elements and verification methods. Challenge feasibility: the design must fit actual installed technology, consumers, and deployment constraints. Record unresolved choices with their practical consequences.

For managed records update design.requirements and the design artifact using [the record format](../spec-workflow/references/records.md). On revisions mark affected artifacts stale and reopen invalidated work as pending or blocked, never a stale task state. Run structural validation once ready. A design-only request ends here without application edits.
