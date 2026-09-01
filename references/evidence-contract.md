# Evidence and claim contract

## What a candidate must carry

Every displayed candidate should retain:

1. a stable law ID and candidate title;
2. the source repository label and revision;
3. one or more commit hashes;
4. affected source files and, where available, changed Python symbols;
5. test-file/name and patch signals;
6. recurrence and clustering explanation when applicable;
7. confidence plus its observable signals;
8. an explicit review state or the absence of a review decision.

The title is a compact hypothesis inferred from evidence. It is not a direct
quote from a maintainer and should not be written as settled project policy.

## Safe language

Prefer:

- “Bug Laws recovered this candidate from commits X and Y.”
- “The report shows a static test-protection signal/grade C.”
- “Public issue/PR context corroborates the failure description.”
- “This is an automated/public-evidence proxy result.”

Avoid:

- “The project truth is …”
- “The maintainer accepted …” without a recorded maintainer decision.
- “The test proves the fix” when only a test-file change was observed.
- “Validated by users/humans” when the artifact contains automated or static proxy
  labels.

## Release and research boundary

Use the repository's `CURRENT_STATE.md`, `ROADMAP.md`, and validation reports
as the source of truth for current gates and metrics. The present project has a
passed evidence gate (`G1-E`) but standard human-validity and external
publication gates remain distinct. A polished report or a high score does not
erase that boundary.

For a public portfolio, show both the useful artifact and the limitation: a
candidate law, its evidence chain, the review state, and the exact
reproduction command.
