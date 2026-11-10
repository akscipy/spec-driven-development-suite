# Comparative and behavioral evaluation protocol

## Questions

Does the suite improve correct outcomes, evidence honesty, and handoff reliability? Does it select suitable stages without imposing excessive documentation? What does it cost in elapsed time and user intervention? These are separate from schema/tool unit-test correctness.

## Comparison study

Prepare three identical isolated JavaScript duration-parser projects with run_benchmark.py. Use fresh agent contexts, the same inherited model/settings, identical user request, and no network/install/commit actions. Configurations:

1. Baseline: explicitly do not read or invoke spec-* skills; ordinary coding capabilities remain available.
2. Natural language: do not name a skill in the request; make candidate skill locations available and observe selection. This is an assisted discovery scenario, not proof of product-level automatic invocation.
3. Explicit: request the candidate spec-workflow skill and follow the same feature request.

Keep evaluator assertions outside solver projects and prohibit access to this harness during work. Score eight independent behavior groups fixed before runs: legacy inputs, compound values, case/whitespace, zero, type rejection, malformed grammar, unit order, and safe integer limits. The harness runs final implementations; solver-written tests cannot redefine these checks. Document any ambiguity before revising test expectations.

Record solver outcome, source hash, tests, scope violations, evidence artifacts, wall time when measured, model identifier if exposed, and unavailable metrics as null. Agent self-reported elapsed time or estimated tokens are not usage evidence. One run per configuration is descriptive, not a statistically reliable performance estimate. Shared-host agents have tool/model knowledge; baseline exclusion is instructed, not a separate host with skill discovery disabled.

## Behavioral release checks

Use independent contexts for stage-only/guided requests and resumption/change work. Include false-done records, absent evidence, multiple feature ambiguity, and lightweight fixes. Observe actual scope and artifact changes; do not infer success from compliance prose. Earlier Python trials are historical evidence, separate from current candidate tests.

## Expanded comparison study

At least six representative task families, three configurations, and three repetitions provide a useful initial 54-run study. Hold repository state, model, settings, budgets, dependencies, and evaluator criteria fixed; randomize run order and report variance/failures. Add real team onboarding and platform/runtime coverage. Track acceptance success, regression rate, unsupported completion claims, scope adherence, appropriate skill selection, elapsed time, user interventions, and token/cost when exposed. Report conclusions only for the tested tasks, models, and environments.
