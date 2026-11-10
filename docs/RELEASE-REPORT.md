# Validation and coverage

Recorded on 2026-11-09. Tool results cover version 0.4.0; the model-driven studies below identify their own versions. Versions 0.4.1, 0.4.2 and 0.4.3 update documentation and package metadata. The feature-record format remains version 2.

## Automated checks

`python -m unittest discover -s tests` completed 99 cases: **95 passed, four skipped, no failures**. The skipped cases require permission to create filesystem links that was unavailable to the test account.

| Category | Cases |
| --- | ---: |
| Record schema, consistency and evidence handling | 55 |
| Installation, updates, rollback and distribution | 26 |
| Feature starter and runnable example | 16 |
| Acceptance-evaluation tools | 2 |

Checks cover invalid records, missing links, dependency cycles, stale evidence, newer failed results, modified logs, command failures and timeouts, interrupted/concurrent writes, unsafe paths, overwrite protection, installation recovery, and repeatable archive builds. The install/use/remove/reinstall test confirms that starting a feature does not leave cache files that block reinstallation.

All twelve skills passed the skill-format validator. Package checks verified required files, matching versions, file hashes, local links, and exclusion of generated output. Tests were also run from an extracted archive. A Windows/Linux CI configuration is included; the recorded execution environment is Windows 11, Python 3.12.10, and Node 24.22.1.

## Documentation release checks

Version 0.4.1 repeated the 26 installation/distribution cases: 25 passed and one filesystem-link case was skipped by the test account. Package metadata, local document links, and the customer-facing wording were also rechecked. Versions 0.4.2 and 0.4.3 repeated these checks with the same result: 25 passed and one filesystem-link case skipped. Local documentation links and anchors were checked again. Skills, tool behavior, and record format are unchanged.

## Setup and starter checks

| Check | Result |
| --- | --- |
| Codex and Claude Code user/project directory selection | All four layouts resolved correctly |
| Update from the earlier package identity | Files and backup history preserved; rollback restored the prior version |
| Feature starter | Created valid draft records; rejected existing features and unsafe paths |
| Working example | Five behavior tests passed; test and completion-check evidence recorded; no completion warnings |
| Extracted-package first use | Installation, status, example and installed starter commands succeeded |
| Remove and reinstall after actual use | Reinstalled without manual cleanup; project records preserved |

The first-use session read the extracted package instructions and used a project-local Claude Code skill directory. It exercised local setup and suite tools, without launching an assistant model session.

## Automatic selection study

Version 0.3.0 was exercised in 36 fresh agent sessions:

| Request group | Observed result |
| --- | --- |
| Relevant work across all twelve skill areas | 24/24 expected selections |
| Small or unrelated work | 12/12 correctly left the suite unused |
| Requested scope and stopping boundaries | 36/36 file/state checks passed |

Each request family had two wordings. Seven project cases used JavaScript; the remaining project cases used Python. Requests did not name a skill or provide its location. Skill use was recorded by the agents and checked against reported file reads and observable changes. Three answer-only cases needed a reporting follow-up. The study used one model environment. Detailed results are in [selection results](../benchmarks/selection-results.json).

## Model-driven feature exercises

Earlier version-0.3.0 exercises covered guided review, partial implementation, fresh-session resumption, changed requirements, false completion, and a complete API/CLI feature. That managed feature passed 20 project tests and 12 separate acceptance checks. Deliberately broken behavior failed acceptance; restored behavior passed after fresh checks.

## Comparison study

Three configurations completed the same JavaScript task in fresh sessions: ordinary coding, natural-language skill discovery, and explicit workflow use. All three passed the same eight independent acceptance groups. There was one task and one run per configuration. Speed, cost, and broader correctness improvements were not established. Model/usage telemetry unavailable to the evaluator was not estimated.

See [the protocol](../benchmarks/PROTOCOL.md), [comparison results](../benchmarks/results.json), and [feature results](../benchmarks/onboarding-result.json) for methods and recorded outcomes.

## Interpretation

The checker establishes structural consistency and freshness for declared local inputs. Requirement quality, meaningful test coverage, approval authenticity, and external environment assumptions require engineering judgment. The recorded local studies do not measure all models, operating systems, repositories, or team settings. Hooks and release controls follow the target project's configuration.
