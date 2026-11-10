# Runnable example

The bounded-slug project shows a complete feature contract, design, task plan, source, and five meaningful tests. It ships with **pending tasks and no validation evidence**. Its working implementation is supplied so the whole record-and-check cycle can run without a model or installed agent.

## Run the full example

From the extracted distribution root:

```text
python examples/demo.py --workspace /path/to/new/slug-demo
```

On Windows, use a quoted destination such as `"C:/work/slug-demo"`. The destination must not exist. The command copies the project, runs its tests through the evidence recorder, writes a verification report, records a real completion check, and checks the resulting complete record. It prints the actual evidence IDs, log locations, and final outcome. It leaves the original packaged example unchanged. A failed run preserves its workspace for inspection.

Inspect the copied project:

```text
python /path/to/suite/skills/spec-workflow/scripts/spec_check.py check /path/to/new/slug-demo/specs/bounded-slug --root /path/to/new/slug-demo --complete
```

Read the .spec-evidence logs rather than treating a task state as proof. Change source or requirements and run check again to see older evidence become outdated. Rerun relevant validation before reclaiming completion.

## Run the steps yourself

Copy bounded-slug into a new project directory. From that copy:

```text
python -m unittest discover -s tests -v
python /path/to/suite/skills/spec-workflow/scripts/spec_check.py check specs/bounded-slug --root .
python /path/to/suite/skills/spec-workflow/scripts/spec_check.py record specs/bounded-slug --root . --criteria AC-001 AC-002 AC-003 -- python -m unittest discover -s tests -v
```

Inspect the actual test log. Update T-001 to done and attach the returned evidence ID. Write verification.md from the observed result and register its artifact. Complete T-002 after its report and completion-check outcome are established; the demo script provides a concrete worked sequence. Run check --complete before treating the feature as accepted. The checker does not update task states for you.

## Initialize your own feature

From any terminal, use the installed or extracted helper:

```text
python /path/to/skills/spec-workflow/scripts/spec_project.py init --root /path/to/project --feature invite-users --goal "An owner can invite a teammate" --criterion "A valid invitation creates a pending invitation; an invalid email is rejected" --mode guided --inputs src tests
```

The project must already exist. Omit --inputs if relevant source paths do not exist yet. The helper creates only requirements.md and spec.json in specs/invite-users, with a draft requirement and criterion, no tasks/evidence/approval, and a requirements-only stopping point. Review and refine scope and edge cases before continuing. Existing feature folders and redirected paths are refused; use the appropriate continuation workflow for existing records.
