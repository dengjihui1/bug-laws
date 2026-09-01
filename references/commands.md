# Command recipes

Run these commands from the Bug Laws repository after `python -m pip install -e
.`. The same commands work with `python -m buglaws` when the current directory
is this repository. When the package is installed only as a Skill, replace
`python -m buglaws` with `python <skill-root>/scripts/run_buglaws.py`.

## Scan a repository

```text
python -m buglaws scan /path/to/repository \
  --output ./buglaws-showcase \
  --label github.com/OWNER/REPOSITORY \
  --since "2 years ago" \
  --limit 200
```

Use a repository label for anything that may be shared. The scan is read-only
with respect to the target repository and produces `BUG_LAWS.md`,
`bug-laws.json`, and `index.html` in the output directory.

Useful tuning controls:

- `--min-confidence 0.60` raises the evidence threshold; it does not make a
  candidate true.
- `--cache-dir ./cache` enables a local history cache keyed by repository,
  revision, and scan parameters.
- `--since` and `--limit` make a large history reproducible and reviewable.

## Optional public corroboration

```text
python -m buglaws enrich \
  --input ./buglaws-showcase/bug-laws.json \
  --output ./buglaws-showcase/bug-laws-enriched.json \
  --repository OWNER/REPOSITORY
```

This is the only network step in the normal workflow. It is bounded and keeps
the original report untouched. Issue/PR text corroborates a candidate; it is
not proof of the law.

## Review without mutating the repository

```text
python -m buglaws review init \
  --input ./buglaws-showcase/bug-laws.json \
  --output ./buglaws-showcase/review.json

python -m buglaws review visual \
  --input ./buglaws-showcase/review.json \
  --output ./buglaws-showcase/review.html

python -m buglaws review decide \
  --store ./buglaws-showcase/review.json \
  --law-id LAW-001 \
  --verdict ACCEPT \
  --reviewer local-reviewer \
  --rationale "Evidence shows the same invariant in two fixes."

python -m buglaws review export \
  --store ./buglaws-showcase/review.json \
  --output ./buglaws-showcase/accepted-laws.json
```

Only `ACCEPT` and `EDIT` decisions are exported. The source report and target
repository remain unchanged.

## Comparisons and diagnostics

```text
python -m buglaws diff --old ./old/bug-laws.json --new ./new/bug-laws.json --output ./diff.json
python -m buglaws benchmark /path/to/repository --output ./benchmark.json --repeat 3
python -m buglaws protection --input ./reviewer.jsonl --output ./protection.jsonl
```

For `audit`, `baseline`, `metrics`, `calibrate`, and `study`, read the
repository's research-track protocol first. Those commands produce
automated/public-evidence or static proxies unless an external protocol
explicitly supplies human labels.
