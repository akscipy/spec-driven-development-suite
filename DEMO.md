# Demonstration

## See a complete feature and its evidence

Allocate 15 minutes for the walkthrough. Actual execution time varies with the environment and discussion. Use a new disposable destination and keep client data and credentials out of the example.

### 1. Run the example

From the extracted package:

```text
python examples/demo.py --workspace "/path/to/new-demo-folder"
```

The example copies a small Python project, runs real behavior tests, records their result, links the evidence to its task, and checks completion. Open its requirements, design, task plan, JSON record and output log to see how they connect. See [the example instructions](examples/README.md) for individual commands.

### 2. Install into a project

Choose the active coding assistant:

```text
python tools/distribute.py install --agent claude --scope project --project "/path/to/project" --dry-run
python tools/distribute.py install --agent claude --scope project --project "/path/to/project"
```

Use `--agent codex` for Codex. Open a fresh assistant session and confirm the skills are visible.

### 3. Request a feature stage

> Draft requirements and acceptance checks for a maximum-length option in our slug helper. Preserve existing callers, remove trailing separators after truncation, and reject invalid bounds. Stop for my review before design or implementation.

Show the intended outcome, assumptions and review boundary. Skill names are not required in this request. For explicit selection use `/spec-requirements` in Claude Code or `$spec-requirements` in Codex.

### 4. Review and implement

Once the requirements are reviewed:

> Prepare the technical design and an ordered task plan. Stop before implementation.

After that review:

> Implement the agreed plan, run the relevant checks, and record acceptance evidence. Report failed, blocked or untested behavior.

Inspect actual source changes and check output. The structural completion check supports the review; sufficient criteria and meaningful tests still need engineering judgment.

### 5. Demonstrate continuity

Ask for impact analysis of a changed requirement, or resume in a fresh chat using the repository records. Show the affected tasks and evidence that need refreshing. Close with what was requested, what changed, which checks ran, and what remains unresolved.

Discuss whether the records make scope, handover, and completion easier to review in the team's own work. Use the recorded checks to assess the demonstration; measure any delivery-time or cost benefit separately.

Share the [product brief](PRODUCT-BRIEF.md), [setup instructions](README.md), and [validation report](docs/RELEASE-REPORT.md) for follow-up.
