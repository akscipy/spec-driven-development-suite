# Spec-Driven Development Suite

## Connect requirements, implementation, and verification

A reusable workflow package for AI-assisted software delivery. Give delivery teams a shared workflow for defining features, reviewing technical decisions, planning tasks, implementing changes, and checking the results. Project records preserve context across changes and handoffs.

### What teams can do

| Team need | Capability |
| --- | --- |
| Agree on the outcome | Define scope and observable acceptance checks |
| Review the approach | Connect technical decisions to requirements |
| Coordinate delivery | Plan tasks with dependencies and completion checks |
| Continue interrupted work | Reconcile recorded progress with the actual implementation |
| Inspect quality | Keep passed, failed, blocked, and untested results distinct |

Twelve focused skills cover the complete workflow and individual stages. Use normal-language requests or name a stage directly. Choose guided reviews or execution within an agreed scope. Keep small fixes lightweight and follow existing project conventions.

### Where it helps

| Delivery situation | How the suite helps |
| --- | --- |
| A feature starts with an unclear request | Turns the request into agreed scope and observable acceptance checks |
| A requirement changes during development | Identifies affected decisions, tasks, and checks |
| Work moves between developers or to testers | Keeps the intended behavior, progress, and recorded results together |
| A team returns to interrupted work | Reconciles the saved plan with the current code and remaining work |
| A reviewer needs to assess completion | Connects completion claims to current checks and highlights gaps |

Use the suite alongside existing engineering and delivery practices. Teams retain their project conventions, review decisions, and release controls.

### Start with a working example

Install for Codex or Claude Code, run the included demonstration, or create a draft feature with the starter command. The suite includes source, tests, a feature-record schema, and local tools for validation and evidence recording.

Suite tools require Python 3.10+ with the standard library. Each project retains its own runtime and test requirements.

### Validation

The tool checks recorded 95 passes and four environment-related skips. A separate selection study recorded the expected choice or non-use in all 36 requests. Versions, methods, environments, and coverage are documented in the [validation report](docs/RELEASE-REPORT.md).

### Get started

1. Follow the [installation instructions](README.md).
2. Run the [working example](examples/README.md).
3. Ask the assistant for the feature or stage you need.

For a team walkthrough, use the [demonstration guide](DEMO.md). Common setup and operating questions are answered in the [FAQ](FAQ.md).
