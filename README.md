# Spec-Driven Development Suite

**A reusable workflow for AI-assisted software delivery.**

Connect requirements, technical decisions, implementation tasks and verification evidence. Keep feature records in the project so teams can review changes, hand over work and resume development with context.

Release **0.4.3**. Twelve focused skills. Suite tools require **Python 3.10+**, with no additional Python packages.

## Quick start

### 1. Install

Select **Code → Download ZIP**, extract the files, and open a terminal in the extracted folder. In VS Code, select **Terminal → New Terminal**. Run the command for your assistant:

| Assistant | Install command |
| --- | --- |
| Codex, including its VS Code extension | `python tools/distribute.py install --agent codex --scope user` |
| Claude Code | `python tools/distribute.py install --agent claude --scope user` |

You need Python 3.10+. Use `python3` instead of `python` if that is your machine's command. For WSL or remote sessions, run installation where the assistant executes. See [detailed installation](#install) for project-only setup and status checks.

### 2. Start a chat

Open the project you want to work on and start a new chat in your coding assistant. Restart the assistant if the skills do not appear.

### 3. Use it

Describe what you need, for example:

> Draft the requirements and acceptance checks for this feature. Stop so I can review them before implementation.

The assistant can choose the relevant skill automatically. To select the full workflow yourself, use `$spec-workflow` in Codex or `/spec-workflow` in Claude Code.

For a complete feature or interrupted work, see [usage examples](#use-it). To run a supplied project first, [try the working example](#try-the-working-example).

## What it helps with

| Delivery situation | How the suite helps |
| --- | --- |
| Starting a feature | Defines scope and observable acceptance checks |
| Planning implementation | Connects technical decisions to ordered tasks |
| Changing a requirement | Identifies affected decisions, tasks and evidence |
| Resuming or handing over work | Reconciles saved progress with the current code |
| Reviewing completion | Links completion claims to current checks and makes gaps visible |

Use the whole workflow or an individual stage. Small changes can stay lightweight. Existing project conventions and release controls still apply.

## Install

### 1. Get the files

Select **Code → Download ZIP** in this repository, extract the ZIP, then open a terminal in the extracted folder. A private repository requires GitHub access.

If you use Git instead:

```text
git clone https://github.com/akscipy/spec-driven-development-suite.git
cd spec-driven-development-suite
```

Check that Python is available:

```text
python --version
```

Use Python 3.10 or later. If your machine uses `python3`, replace `python` with `python3` in the commands below. On Windows, `py -3` is another option. No `pip install` step is required.

### 2. Run one install command

Choose your assistant:

| Assistant | Command for your local projects |
| --- | --- |
| Codex | `python tools/distribute.py install --agent codex --scope user` |
| Claude Code | `python tools/distribute.py install --agent claude --scope user` |

The installer copies all twelve skills into the selected assistant's user skill directory. It detects managed updates and protects unrelated files and local edits. See [compatibility](COMPATIBILITY.md) for directory layouts and existing installations. Actual Claude model behavior is outside the recorded tests.

To install only in one project, use this command instead. Select your assistant and replace the project path:

```text
python tools/distribute.py install --agent codex --scope project --project "/absolute/path/to/project"
```

Windows paths such as `"C:/work/my-project"` are supported. Add `--dry-run` to preview an installation. User installations apply to the local machine and assistant execution environment where they are made.

### 3. Check the installation

```text
python tools/distribute.py status --agent codex --scope user
```

Use `--agent claude` if you installed for Claude Code. For a project installation, use the same `--scope project --project "..."` options used during installation. Open a fresh assistant session so the host can discover the skills.

## Codex in VS Code

The Codex VS Code extension discovers standalone skills from the same Codex skill directories. Follow these steps after getting the suite files:

1. Open the suite folder in VS Code and select **Terminal → New Terminal**.
2. Run the install and status commands:

   ```text
   python tools/distribute.py install --agent codex --scope user
   python tools/distribute.py status --agent codex --scope user
   ```

3. Open the project you want to work on and start a new chat in the Codex extension.
4. Type `$spec-workflow` to select the workflow, or describe the feature in normal language. If the skills do not appear, restart Codex.

This installs all twelve skills under `~/.agents/skills/`. To install only in a project, use `--scope project --project "/absolute/path/to/project"` instead of `--scope user` in both commands. Windows paths such as `"C:/work/my-project"` are supported.

If Codex runs in WSL, a development container or a remote environment, run installation in that environment so the skill files are available there. Use `python3` in place of `python` where required. This suite is a set of skills loaded by the Codex extension, so no additional VS Code extension package is needed.

See [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills) for skill discovery and invocation, and [compatibility](COMPATIBILITY.md#codex-in-vs-code) for setup details and validation scope.

## Use it

Open a project in your assistant and describe the work. Skill names are optional.

**Complete a feature:**

> Build the invitation feature in this repository. Define acceptance checks, prepare the design and task plan, then implement and verify it. Work autonomously within that scope.

**Stop for a review:**

> Draft the requirements and acceptance criteria for this feature. Stop before design or implementation so I can review them.

**Continue interrupted work:**

> Resume this feature from its project records. Check the current code and evidence, then continue the remaining tasks.

The assistant can select relevant skills from their descriptions. For explicit selection, use `$spec-workflow` in Codex or `/spec-workflow` in Claude Code. Skill selection depends on the host, request and available context. See the [usage guide](GUIDE.md) for all twelve stages and review modes.

## Try the working example

Run this from the repository folder. Choose an absolute destination that does not exist:

```text
python examples/demo.py --workspace "/absolute/path/to/new-demo-folder"
```

For Windows, a destination such as `"C:/work/spec-suite-demo"` is supported. The example needs no assistant connection. It copies a small project, runs five real tests, records their output and checks feature completion. The packaged example remains unchanged. See [example instructions](examples/README.md) for the individual steps.

## Start a feature record

The assistant can create records while working on a substantial feature. To create a draft directly, use the starter from the repository folder:

```text
python skills/spec-workflow/scripts/spec_project.py init --root "/absolute/path/to/project" --feature invitation-flow --goal "Invite a person to a workspace" --criterion "A valid invitation creates a pending workspace membership"
```

The project directory must exist. The starter creates draft requirements and a feature record, preserves existing feature files, and stops at requirements. Ask the assistant to refine the draft and continue to the stage you need. See the [example instructions](examples/README.md#initialize-your-own-feature) for validation inputs and review modes.

## Update, restore or remove

Keep the same assistant and installation scope. After downloading or checking out the version you want, rerun the install command to update:

```text
python tools/distribute.py install --agent codex --scope user
python tools/distribute.py rollback --agent codex --scope user --dry-run
python tools/distribute.py uninstall --agent codex --scope user --dry-run
```

Remove `--dry-run` to apply rollback or removal. The installer keeps managed-update backups and detects local edits. Project feature records remain in the project. See [compatibility and migration](COMPATIBILITY.md) for custom and older installation locations.

## Evidence and review

Recorded tool checks completed 99 cases: **95 passed and four environment-related skips**. A separate study recorded **36/36 expected selection outcomes in one model environment**. These results identify specific versions and methods in the [validation report](docs/RELEASE-REPORT.md). They do not establish time or cost savings.

The checker validates record structure and local evidence freshness. Engineers still assess the requirements, test adequacy, security and implemented behavior.

## Documentation

| Resource | Contents |
| --- | --- |
| [Product brief](PRODUCT-BRIEF.md) | Purpose, capabilities and delivery use cases |
| [Presentation materials](docs/presentation/README.md) | Editable deck, PDF and one-page handout |
| [Usage guide](GUIDE.md) | Skill selection, review modes and project records |
| [Feature starter](examples/README.md#initialize-your-own-feature) | Create draft records without writing JSON manually |
| [Team demonstration](DEMO.md) | Walkthrough and assistant requests |
| [FAQ](FAQ.md) | Setup and operating questions |
| [Compatibility](COMPATIBILITY.md) | Host directories, runtime requirements and migration |
| [Security](SECURITY.md) | Command execution and local data handling |
| [Validation report](docs/RELEASE-REPORT.md) | Recorded results, methods and coverage |
| [Contributing](CONTRIBUTING.md) | Development and release checks |
| [Changes](CHANGELOG.md) | Version history |

## Development

```text
python -m unittest discover -s tests
python tools/distribute.py validate
python tools/distribute.py build --output dist
```

The CI configuration runs tests and package checks on Windows and Linux. A configured CI job becomes executed evidence only after it runs successfully. Build output contains a file manifest and a SHA-256 checksum.
