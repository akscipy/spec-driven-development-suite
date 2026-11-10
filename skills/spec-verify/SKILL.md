---
name: spec-verify
description: "Check implemented behavior against feature acceptance criteria with reproducible tests or observed manual evidence. Use for acceptance verification or auditing a claimed feature completion; distinguish untested gaps from passes."
---

# Spec Verify

Read [the shared contract](../spec-workflow/references/contract.md) once. Read active acceptance criteria, design, tasks, changed implementation, declared inputs, and prior evidence.

Map each active AC to a meaningful test or reproducible manual observation. Run relevant existing tests and repository-required checks. Add targeted tests only when code changes are within scope and the tests add confidence; a read-only audit instead proposes missing checks. Distinguish a defect, a broken test, and an environment limitation. Never weaken criteria/assertions to obtain a green result.

Use [record commands](../spec-workflow/references/records.md) for actual command/manual results. Source inspection or a successful build alone is not runtime acceptance. Verify that declared files include relevant dependencies and that the current environment still matches external assumptions. Manual results require actual observations, not an inference from missing failures.

Write verification.md using [the structure](assets/verification.md), linking results, failures, blocked/untested criteria, and evidence. For managed completion run check --complete, then separately judge semantic coverage and required project checks. A verification-only request reports defects without unrequested fixes. In authorized delivery fix in-scope defects and rerun affected checks. Claim complete acceptance only when all active criteria and required checks have adequate current evidence; otherwise report the exact remaining gaps.
