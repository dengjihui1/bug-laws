# Three-minute reproducible demo

The demo is local and does not require an account, hosted service, or API key.

## 0:00–0:30 — scan

```text
python -m buglaws scan . --output /tmp/buglaws-report --label local/demo --limit 80
```

Open `BUG_LAWS.md`, `bug-laws.json`, and `index.html`. Every candidate shows a
title, structured fields, commit/file evidence, AST symbols where available,
test state, and an explanation of clustering.

## 0:30–1:30 — review without policy mutation

```text
python -m buglaws review init --input /tmp/buglaws-report/bug-laws.json --output /tmp/review.json
python -m buglaws review visual --input /tmp/review.json --output /tmp/review.html
```

Inspect the HTML, download decisions, and apply a decision only through the
separate review store. Generated reports and source files remain untouched.

## 1:30–2:15 — compare and enrich optionally

```text
python -m buglaws diff --old /tmp/old.json --new /tmp/buglaws-report/bug-laws.json --output /tmp/diff.json
python -m buglaws enrich --input /tmp/buglaws-report/bug-laws.json --output /tmp/enriched.json --repository pallets/flask
```

The second command is the only network step and records response hashes and
failures. Issue/PR text is corroboration, not law truth.

## 2:15–3:00 — inspect quality boundaries

```text
python -m buglaws benchmark . --output /tmp/benchmark.json --repeat 3 --cache-dir /tmp/buglaws-cache
python -m buglaws protection --input /tmp/reviewer.jsonl --output /tmp/protection.jsonl
```

Finish by showing that automated quality numbers remain labelled as proxies and
that no command writes into the scanned source repository.
