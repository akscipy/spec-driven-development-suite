# Usage guide

## Choose the work and stopping point

Describe the outcome in normal language. The assistant can select a matching skill; explicit invocation is available as `/spec-workflow` in Claude Code or `$spec-workflow` in Codex. See [installation](README.md) for both hosts.

| Request | Relevant stage |
| --- | --- |
| Build a substantial feature through acceptance verification | spec-workflow |
| Understand the current code before proposing changes | spec-discover |
| Define behavior and acceptance checks | spec-requirements |
| Design an implementation against existing requirements | spec-design |
| Turn the design into dependency-ordered work | spec-plan |
| Implement the planned changes | spec-implement |
| Verify behavior against acceptance criteria | spec-verify |
| Review specs or implementation conformance | spec-review |
| Assess and propagate a requirement change | spec-change |
| Reconcile and continue interrupted work | spec-resume |
| Maintain project guidance | spec-steering |
| Set up development-event checks | spec-hooks |

These are examples, not fixed phrases. A stage-only request ends at that stage. Small fixes can stay lightweight. Skill selection depends on the request, descriptions, model, and available context.

## Review modes

In guided mode, specify the stages you want to review. The assistant prepares that stage and records it as awaiting review before continuing. In autonomous mode it proceeds within the requested scope, surfacing consequential questions and validation gaps. Agent readiness and actual user approval are separate states.

Examples:

> Prepare requirements and a technical design. Let me review both before implementation.

> Continue this feature through implementation and acceptance checks. Preserve unrelated changes.

> Review the existing specs for contradictions. Report findings without editing them.

## Feature records

requirements.md owns intended behavior and acceptance conditions. design.md owns technical decisions. tasks.md explains implementation scope and rationale. spec.json owns identifiers, dependencies, mutable states, review boundaries, and evidence references. verification.md summarizes observed results and remaining gaps.

Use the [initializer](README.md#start-a-feature-record) to create a draft feature, or preserve the repository's established format. Read the [record format](skills/spec-workflow/references/records.md) when using managed checks.

## Changes and handoffs

Ask for impact analysis before implementing a material change in intent. Preserve existing identifiers and history; reopen work that no longer meets its outcome. When resuming, reconcile records with actual code and evidence rather than relying on a checked box. Source/specification changes invalidate affected local snapshots conservatively and require current checks before claiming completion.

## Project guidance

When requested, merge a concise note into the host's project guidance file: CLAUDE.md for Claude Code or AGENTS.md for Codex. Preserve existing instructions and scoped conventions. A useful note identifies source/test locations, real validation commands, feature-record location, and when to use the whole workflow or an individual stage. The installer does not edit these files.

## Development checks

Event checks need a real runner such as a Git hook or CI job. Use the read-only checker for automatic structural checks. Command recording executes an explicitly selected check; consult [security and data handling](SECURITY.md) before configuring automation.

## Recovery

Use the installation status and rollback commands in README.md for installed files. For interrupted evidence recording, inspect the retained lock, temporary record, and output before recovery. The exact recovery procedure is in [recording instructions](skills/spec-workflow/references/records.md).
