# Contributing and acceptance criteria

Keep skills focused on decisions they improve. Prefer a narrow fix demonstrated by real use over another universal rule. Preserve stage boundaries, project conventions, and unrelated user changes.

Every behavioral fix should include a minimal reproducer and meaningful regression check. Run `python -m unittest discover -s tests` and `python tools/distribute.py validate`. Check documentation commands from an extracted release, not just a working tree. Build twice and compare archive bytes. Do not bundle backups, local trial repositories, credentials, or machine-specific paths.

For agent evaluations keep evaluator acceptance checks outside the solver's permitted files, record the exact request and starting fixture, and disclose model/configuration availability, wall time, missing usage data, and whether skill invocation was requested or natural. Do not rewrite a failed criterion after seeing the result. Report failures and inconclusive results alongside successes.

Before a release: resolve reproducible correctness findings, exercise install/update/rollback/uninstall with conflicts, run independent agent scenarios, publish an accurate compatibility matrix and release report, version the package, and include checksums. Do not present new CI jobs or unexecuted scenarios as evidence.
