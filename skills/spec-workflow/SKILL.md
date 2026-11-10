---
name: spec-workflow
description: "Coordinate substantial software feature work through requirements, technical design, implementation tasks, and acceptance verification. Use for building multi-step features or continuing managed spec work; use individual stages for stage-only requests and keep trivial fixes lightweight."
---

# Spec Workflow

Read [the shared contract](references/contract.md) once, then inspect repository instructions, existing feature records, and the relevant implementation.

Choose the smallest useful workflow. For substantial or uncertain feature work, maintain requirements, design, tasks, and acceptance evidence. For a localized low-impact change, use concise acceptance checks and the repository's normal verification; do not create a document hierarchy merely because this skill was selected. Preserve existing project formats.

Determine the requested endpoint and review mode from the user's request. In autonomous mode continue within scope; in guided mode complete the requested stage and stop for its review. A stage-only request never authorizes later stages. Record task-specific pauses with pause_after_task.

Read only the next relevant sibling skill: spec-discover for missing repository context; spec-requirements for behavior; spec-design for approach; spec-plan for dependencies; spec-implement for code; spec-verify for acceptance. Use spec-change for changed intent and spec-resume for uncertain handoff state. Read the sibling file before applying it; if missing, report the incomplete installation.

For managed records, consult [record commands](references/records.md) and [the worked example](references/example.md). Resolve contradictions before implementation. Update the canonical JSON at meaningful milestones, run structural checks after metadata changes, and finish authorized delivery with actual acceptance evidence plus check --complete. A green checker alone is not a feature acceptance decision.

For a new managed feature, [the initializer](scripts/spec_project.py) can create draft requirements and a consistent record from the user's goal and first acceptance criterion. Use `init --root <project> --feature <slug> --goal <text> --criterion <text>`; then refine the actual requirements. It stops at the requirements stage and protects existing feature folders. Resume existing work rather than initializing over it.
