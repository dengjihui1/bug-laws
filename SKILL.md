---
name: bug-laws
description: Recover evidence-linked candidate engineering laws from a Python repository's Git bug-fix history, with provenance, recurrence, test-protection signals, review artifacts, and honest quality boundaries. Use for repository archaeology, onboarding knowledge, repeated-failure discovery, or evidence-backed engineering guidance; not for generic linting or automatic source-code changes.
metadata:
  short-description: Mine Git history for evidence-backed engineering laws
---

# Bug Laws

Use this skill when the user wants to discover the implicit engineering rules a
Python project has learned through bugs, regressions, hotfixes, or reverts. The
deliverable is a review-ready evidence wall, not an AI-authored policy file.

## Non-negotiable contract

- Treat every extracted law as a **candidate** until an explicitly recorded
  review decision accepts or edits it.
- Keep commit hashes, affected files, changed symbols, test signals, and any
  public issue/PR corroboration attached to the candidate. Never present a
  title without inspectable provenance.
- The default path is local, read-only, keyless, and network-free. Only run
  `enrich` when the user explicitly wants public GitHub issue/PR corroboration.
- Write only to the user-selected report/review output directory. Do not edit
  source code, tests, Git history, `AGENTS.md`, or repository policy files.
- A changed test file is a protection signal, not proof that the test catches
  the bug. Static grades and automated/public-evidence measurements are proxies;
  never call them human review, maintainer acceptance, or user research.

## Default workflow

1. Confirm that the target is a local Git repository and identify a sensible
   public label. For a shareable artifact, always use `--label` so local paths
   do not enter the report.
2. Scan a bounded history with the CLI. Start with the target repository's
   default branch and choose `--since`/`--limit` when the history is large.
3. Inspect all three outputs: `BUG_LAWS.md` for reading, `index.html` for the
   visual evidence wall, and `bug-laws.json` for machine-readable provenance.
4. If the user asks for stronger context, run optional `enrich` to fetch only
   linked public GitHub issue/PR records. Preserve the original JSON and report
   retrieval time, source URL, response hash, and failures.
5. If a decision is needed, initialize a separate review store, use the visual
   review page or terminal decisions, then export only explicitly accepted or
   edited laws. Never overwrite the extracted report.
6. For comparisons or quality claims, use `diff`, `benchmark`, `protection`,
   `calibrate`, `audit`, or `study` only for the question they measure. Include
   the scope, repository revision, command, and whether the result is human or
   automated proxy evidence.

Read [references/commands.md](references/commands.md) for the command recipes.
Read [references/showcase-workflow.md](references/showcase-workflow.md) when
the goal is a public portfolio/demo artifact. Read
[references/evidence-contract.md](references/evidence-contract.md) before
writing conclusions, summaries, CV bullets, or research claims.

## Invocation examples

The package can be used after `pip install -e .` or directly with
`python -m buglaws` from this repository. If the CLI is not installed, use the
bundled launcher `python <skill-root>/scripts/run_buglaws.py`; it loads the
tested engine shipped inside this Skill without a global install.

```text
Use $bug-laws to mine this Python repository's bug-fix history and create a
public-safe evidence report. Keep all laws labelled as candidates.
```

```text
Use $bug-laws to compare the latest report with the previous report and explain
which candidate laws are new, changed, resolved, or resurfaced.
```

When the user asks for a tool-ready summary, provide a concise summary plus
links to the evidence artifacts and the accepted-law export, if one exists.
Do not silently turn candidate laws into standing instructions.
