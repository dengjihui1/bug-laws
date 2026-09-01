# Bug Laws

> Every bug fix writes a law. Most repositories forget to publish it.

Project roadmap, validation protocol, task pool, risks, and maintenance handoff instructions live in [`project-management/`](project-management/README.md).

Bug Laws is a Python-first repository archaeology tool. It reads bug-fix and revert history, recovers candidate engineering invariants, groups repeated violations, and shows which fixes changed no regression tests.

The output is an evidence wall, not an automatically written policy file. Every candidate law links back to commits, affected files, test changes, and patch signals. A maintainer must accept, edit, or reject it before it becomes project guidance.

## The result

One local repository goes in:

```text
buglaws scan ../my-python-project --since "2 years ago"
```

Three inspectable artifacts come out:

```text
.buglaws-report/
├── BUG_LAWS.md      evidence report for maintainers and agents
├── bug-laws.json    machine-readable candidate laws
└── index.html       self-contained visual law wall
```

A law looks like this:

```text
LAW-004  Cache key must include tenant id
Evidence confidence: 86% — human review required
Recurrence: 3 fixes in 14 months
Protection: 1 fix changed tests; 2 did not
Evidence: commit hashes, issue references, files, guards, test names
```

## Why this is different

- Git documents what changed. Bug Laws asks what invariant the failure proved.
- Memory tools record new failures after installation. Bug Laws excavates the history a repository already has.
- Code review tools inspect the current diff. Bug Laws looks for rules that the project has violated repeatedly.
- Documentation drift tools keep declared facts current. Bug Laws discovers candidate facts that were never declared.

## Quick start

Requirements: Python 3.11+ and Git.

```text
python -m pip install -e .
buglaws scan /path/to/python/repository
```

Without installation, run from this repository:

```text
python -m buglaws scan /path/to/python/repository --output ./report
python -m buglaws sample --report ./report/bug-laws.json --output ./annotation-sample --seed 20260901 --total 75
```

Useful options:

```text
--since "2025-01-01"       limit Git history
--limit 100                cap fix candidates inspected
--min-confidence 0.60      require stronger evidence signals (default: 0.50)
--output ./report          choose artifact directory
--label github.com/org/repo hide the local path in a public report
```

## Skill package

This repository is also a standard Skill package: the root [`SKILL.md`](SKILL.md)
defines the evidence-first workflow, and [`agents/openai.yaml`](agents/openai.yaml)
provides the discoverable UI metadata. That makes the project usable in two
ways: install the Python CLI for deterministic repository analysis, or install
the repository as the `bug-laws` Skill and invoke the workflow with a short prompt.

The shortest portfolio demo is:

```text
Use $bug-laws to scan this public Python repository, build a public-safe law
wall, and trace one recurrent candidate back to its commits and tests.
```

The Skill never turns machine-recovered candidates into project policy. It
creates a reviewable artifact set—Markdown, JSON, and a self-contained HTML
wall—while preserving the original report and source repository.

See [`references/showcase-workflow.md`](references/showcase-workflow.md) for a
promotion-ready demo narrative and [`references/evidence-contract.md`](references/evidence-contract.md)
for the claim boundary.

## What version 0.1 actually does

1. Reads non-merge Git history.
2. Selects commit subjects containing fix, bug, hotfix, regression, revert, correct, or prevent.
3. Keeps candidates that changed Python source files.
4. Extracts issue references, changed tests, added test names, and added guards.
5. Infers a conservative candidate title.
6. Groups candidates with overlapping law language and affected modules.
7. Reports recurrence and fixes that did not change tests.

No network, account, API key, repository write, or telemetry is required. Scanning is read-only; only the chosen report directory is written.

Two real generated examples are checked into `demo/`: a small scan of projectmem and a larger five-year scan of Click. They use `--label` so public artifacts do not expose local filesystem paths.

## Honest boundaries

- A commit message is not ground truth. Candidate laws are explicitly labelled for human review.
- Version 0.1 supports Python evidence only.
- Report JSON is versioned as `report-v1`; `review`, `diff`, `benchmark`,
  `calibrate`, and opt-in `enrich` commands keep extracted evidence separate
  from review decisions.
- A test-file change is a proxy for regression protection, not proof of adequate coverage.
- Squashed or vague histories contain less recoverable evidence.
- Similarity clustering is lexical and intentionally conservative.
- The tool does not modify source code, tests, agent instructions, or Git history.

## Evaluation contract

The project should not expand to more languages until it passes all three checks:

1. At least 70% of 30 sampled laws are accepted or lightly edited by maintainers.
2. Every displayed law has inspectable commit and file evidence.
3. Three unrelated Python repositories each yield at least ten useful, non-duplicate candidate laws.

Kill the project if maintainer acceptance remains below 60%, or if generated laws merely paraphrase commit subjects without recovering useful invariants.

## Development

```text
python -m unittest discover -s tests -v
python -m buglaws --help
```

## License

MIT
