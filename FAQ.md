# Frequently asked questions

### What does the suite do?

It connects requirements, technical decisions, tasks, and acceptance evidence so teams can inspect progress and continue work with context.

### Which coding assistant should I select during installation?

Use `--agent codex` or `--agent claude`. Select project or user scope as shown in the [README](README.md). Use `--destination` for a custom or existing installation path. [Compatibility](COMPATIBILITY.md) lists directory layouts and plugin details.

### Do I need to name a skill every time?

No. The assistant can select a matching skill from a normal request. Name a skill explicitly when you want to direct a particular stage. The [usage guide](GUIDE.md) provides examples for both assistants.

### Does every change need a specification folder?

No. Small corrections can use focused checks. Substantial features and existing managed work can use persistent records. A stage-only request ends at that stage.

### What do I need to run it?

An assistant that supports the Agent Skills format, plus Python 3.10+ for suite tools. Projects retain their own runtime and test dependencies. The [working example](examples/README.md) runs with the Python standard library.

### How do I start without writing JSON manually?

Use the feature starter command in the [README](README.md#start-a-feature-record). Supply the feature name, goal, and first acceptance criterion. It creates draft requirements and a consistent starting record while preserving existing work.

### Does it replace engineering review?

No. The checker validates record structure and local evidence freshness. Engineers still review requirement quality, test adequacy, security, and release readiness under their project's processes.

### Where is project data stored?

Suite tools write local project records and validation logs. Review logs before sharing and follow the project's information-handling rules. See [security and data handling](SECURITY.md).

### How do I update, restore, or remove it?

Use the same installation destination or assistant/scope selectors with the commands in the [README](README.md#update-restore-or-remove). Local edits are detected before changes; backups support recovery. Project feature records are retained.

### What results have been measured?

Tool checks, workflow exercises, selection results, and comparison methods are recorded in the [validation report](docs/RELEASE-REPORT.md). The available comparison showed equal correctness on one task; speed and cost improvements have not been established.
