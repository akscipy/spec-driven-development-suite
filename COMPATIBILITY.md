# Compatibility and migration

## Assistant setup

The shared skills use the Agent Skills format: a directory containing SKILL.md with name/description metadata, supporting references, and local scripts. The complete suite keeps twelve sibling skill folders together.

| Host | Project directory | User directory | Project guidance | Explicit invocation |
| --- | --- | --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | CLAUDE.md | `/spec-workflow` |
| Codex | `.agents/skills/` | `~/.agents/skills/` | AGENTS.md | `$spec-workflow` |

Sources: [Claude Code skills](https://code.claude.com/docs/en/skills) and [Codex skills](https://learn.chatgpt.com/docs/build-skills). Organizational host settings may control skill discovery and tool access. Local installations apply to the machine and execution environment where they are made.

`--agent` and `--scope` select the documented directory. `--destination` supports custom directories, including existing installations in `~/.codex/skills`. Do not combine these selectors. Avoid duplicate installation scopes unless you understand the host's precedence rules. Installation leaves project guidance files unchanged.

## Runtime

Suite tools require Python 3.10+ and the standard library. Projects retain their own runtime/test dependencies. Examples use the Python standard library. Validation has been executed on Windows 11 with Python 3.12.10; JavaScript exercises used Node 24.22.1. The supplied CI configuration covers Windows/Linux and multiple Python versions; executed results are listed in the validation report.

Assistant behavior studies in the evidence report identify the model environment used. Host-directory and package-format checks are separate from model-driven workflow checks.

## Plugin layouts

The package includes a root plugin.json plus Codex and Claude Code compatibility descriptors. All refer to the same skills/ directory. The [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference) and [OpenAI plugin guide](https://developers.openai.com/plugins/build/plugins) describe host plugin layouts. The local installer is the direct setup path documented in README.md; publishing a marketplace entry is a separate distribution action.

Plugin-loaded skills use the host's plugin namespace. For example, Claude Code uses `/spec-driven-development-suite:spec-workflow` for this plugin; the standalone directory installation uses `/spec-workflow` as shown in README.md.

## Versions and existing installations

Release 0.4.3 uses feature record schema version 2. Existing legitimate version-2 feature records remain valid. The schema's existing identifier is retained so integrations can continue to reference it. Put project-specific record fields under extensions.

Previous releases used the package name codex-spec-suite. Managed update and rollback preserve their ownership records and backups. Hidden installation inventory/backup/lock filenames retain that prefix for compatibility; the product identity and release archive are Spec-Driven Development Suite. Use the original destination when updating an existing installation.

Older manually copied installations without ownership metadata are unmanaged. Back up the exact suite folders, compare local edits, move the known old folders out of the destination, then install. Do not delete the entire user skills directory. Other skills and project feature records must remain intact.

## Record migration

Do not migrate merely to read or review a feature. For ongoing work that needs managed records, preserve IDs and prose, create spec.json from observed state, retain any old state.md as history, declare real validation inputs, and capture fresh evidence. Historical task checkboxes or approvals do not establish current runtime acceptance.

## Builds and local changes

Builds use fixed metadata and ordering for byte-identical output on the same Python/zlib toolchain. Cross-toolchain compressed byte identity is not asserted. The installer detects local changes and refuses to overwrite them; reconcile customized copies before updating. Backups and documented rollback support recovery.
