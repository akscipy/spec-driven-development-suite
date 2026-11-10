# Worked feature: bounded ASCII slugs

This illustrates a coherent spec rather than prescribing a stack. Adapt paths and behavior to the repository.

## requirements.md
```markdown
# Bounded slugs
### R-001: Produce a bounded ASCII slug
Convert ASCII letters to lowercase, replace runs of non-ASCII-alphanumeric characters with one hyphen, trim edge hyphens, and truncate to max_length with no trailing hyphen. Reject max_length below 1 with ValueError. Unicode transliteration is excluded.
### AC-001 (R-001)
slugify(" Hello, WORLD!! ", 80) returns "hello-world"; empty input returns "".
### AC-002 (R-001)
slugify("hello world", 6) returns "hello"; max_length=0 raises ValueError.
```

## design.md
Keep normalization in the existing src/slugs.py function. Normalize before truncation, then trim any trailing separator introduced by truncation. Validate the bound before processing. R-001 is exercised by input/output tests for both ACs; no persistence or migration is needed. Reuse the repository's test runner.

## tasks.md
```markdown
# Bounded slug tasks
## T-001: Implement bounded normalization
Update src/slugs.py and focused tests in tests. Cover empty input, repeated punctuation, truncation on a separator, and an invalid bound.
```

## spec.json at planning
```json
{
  "schema_version": 2,
  "feature": "bounded-slug",
  "mode": "autonomous",
  "stage": "plan",
  "stop_after": "verify",
  "next_action": "Implement T-001, then record its tests",
  "blockers": [],
  "decisions": [
    "Confirmed: ASCII-only slug output; assumption: no transliteration"
  ],
  "artifacts": {
    "requirements": {
      "path": "specs/bounded-slug/requirements.md",
      "status": "ready"
    },
    "design": {
      "path": "specs/bounded-slug/design.md",
      "status": "ready"
    },
    "tasks": {
      "path": "specs/bounded-slug/tasks.md",
      "status": "ready"
    }
  },
  "requirements": [
    {
      "id": "R-001",
      "status": "active"
    }
  ],
  "criteria": [
    {
      "id": "AC-001",
      "status": "active",
      "requirements": [
        "R-001"
      ]
    },
    {
      "id": "AC-002",
      "status": "active",
      "requirements": [
        "R-001"
      ]
    }
  ],
  "design": {
    "requirements": [
      "R-001"
    ]
  },
  "tasks": [
    {
      "id": "T-001",
      "state": "pending",
      "depends_on": [],
      "requirements": [
        "R-001"
      ],
      "criteria": [
        "AC-001",
        "AC-002"
      ],
      "done_when": "Slug normalizes separators and respects the length bound; focused tests pass",
      "evidence": []
    }
  ],
  "inputs": [
    "src",
    "tests"
  ],
  "evidence": []
}
```

Before implementation run check. While implementing set T-001 in-progress. Run the selected tests using record --criteria AC-001 AC-002. Inspect the actual results, then set T-001 done and reference the returned E ID. Add verification.md and its artifact record, summarizing observed results and gaps. Run check --complete. If max_length semantics change, preserve IDs, update prose/design/tasks, reopen work, and recapture evidence; the changed snapshot makes previous results outdated.
