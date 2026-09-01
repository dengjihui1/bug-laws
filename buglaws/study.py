from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_QUERIES = ("redirect", "cache", "encoding", "flag", "callback")


def run_onboarding_proxy(items: Iterable[dict[str, Any]], queries: Iterable[str] = DEFAULT_QUERIES) -> dict[str, Any]:
    records = list(items)
    cases = []
    for query in queries:
        token = query.lower()
        subject_hits = 0
        law_context_hits = 0
        for item in records:
            evidence = item.get("evidence", [])
            subject_text = " ".join(str(entry.get("subject", "")) for entry in evidence).lower()
            context_text = " ".join([str(item.get("title", "")), subject_text, " ".join(str(path) for entry in evidence for path in entry.get("source_files", []))]).lower()
            subject_hits += token in subject_text
            law_context_hits += token in context_text
        cases.append({"query": query, "items": len(records), "subject_only_hits": subject_hits, "law_context_hits": law_context_hits, "delta": law_context_hits - subject_hits})
    return {"study_version": "onboarding-proxy-v1", "execution_profile": "deterministic lexical proxy", "human_validity": "NOT ASSESSED", "n": len(records), "queries": cases, "interpretation": "retrieval proxy only; no human onboarding time, task success, or agent-behavior claim"}


def write_study(input_path: str | Path, output_path: str | Path) -> Path:
    items = [json.loads(line) for line in Path(input_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(run_onboarding_proxy(items), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output
