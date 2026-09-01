# Public showcase workflow

Use this mode when the user wants Bug Laws to demonstrate engineering,
research, and product judgment in a portfolio or application.

## The story to demonstrate

Bug Laws turns a repository's forgotten bug-fix history into a navigable,
evidence-linked “law wall.” The distinctive point is not that software writes
rules; it is that every candidate is traceable to a concrete fix, can expose
recurrence and test-protection signals, and stays separate from source-policy
mutation until someone makes an explicit decision.

Show this sequence:

1. Run a bounded scan on a public Python repository with `--label`.
2. Open the Markdown report, JSON provenance, and self-contained HTML wall.
3. Pick one recurrent candidate and trace its commits, files, symbols, and test
   signals.
4. Show a separate review store and an accepted-law export without changing the
   scanned repository.
5. If useful, compare two report revisions or add optional public issue/PR
   corroboration.
6. End with the limitations and the exact reproduction command.

## Portfolio-ready artifact set

Keep these together in a shareable directory:

- `BUG_LAWS.md` — human-readable narrative;
- `bug-laws.json` — inspectable machine contract;
- `index.html` — zero-build visual evidence wall;
- `accepted-laws.json` — only if explicit review decisions exist;
- `README` or a short case-study note with command, revision, scope, and
  limitations.

Never commit reports containing private local paths, secrets, private repository
identity, or unlabelled automated metrics. The checked-in `demo/` reports are
fixtures and examples, not endorsements by the scanned projects.

## Strong but honest positioning

Good positioning emphasizes the combination of repository archaeology,
provenance, deterministic clustering, review separation, and reproducibility.
Do not claim that the tool “understands the codebase” or “discovers project truth,”
maintainer acceptance, or user-study success unless the corresponding evidence
actually exists.
