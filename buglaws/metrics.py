from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _wilson(successes: int, total: int) -> dict[str, float | None]:
    if total == 0:
        return {"estimate": None, "lower_95": None, "upper_95": None}
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return {"estimate": p, "lower_95": max(0.0, centre - margin), "upper_95": min(1.0, centre + margin)}


def _rates(labels: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(label["verdict"] for label in labels)
    scorable = len(labels) - counts["UNSCORABLE"]
    useful = counts["ACCEPT"] + counts["EDIT"]
    severe = sum(
        label["verdict"] == "REJECT"
        and (label.get("grounding") == 0 or "WRONG_CAUSALITY" in label.get("error_tags", []))
        for label in labels
    )
    full_grounding = sum(label.get("grounding") == 2 for label in labels)
    return {
        "n": len(labels),
        "counts": dict(sorted(counts.items())),
        "useful_rate": {**_wilson(useful, scorable), "successes": useful, "scorable": scorable},
        "severe_false_law_rate": {**_wilson(severe, scorable), "successes": severe, "scorable": scorable},
        "unscorable_rate": {**_wilson(counts["UNSCORABLE"], len(labels)), "successes": counts["UNSCORABLE"], "total": len(labels)},
        "grounding_full_rate": {**_wilson(full_grounding, len(labels)), "successes": full_grounding, "total": len(labels)},
        "mean_scores": {
            key: (sum(int(label[key]) for label in labels) / len(labels) if labels else None)
            for key in ("grounding", "abstraction", "scope", "usefulness", "title_quality")
        },
    }


def _kappa(first: list[str], second: list[str]) -> float | None:
    if len(first) != len(second) or not first:
        return None
    n = len(first)
    observed = sum(a == b for a, b in zip(first, second, strict=True)) / n
    categories = set(first) | set(second)
    expected = sum(first.count(category) * second.count(category) for category in categories) / (n * n)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def _protection_confusion(labels: list[dict[str, Any]], corpus: dict[str, dict[str, Any]]) -> dict[str, int]:
    matrix: Counter[tuple[str, str]] = Counter()
    for label in labels:
        item = corpus.get(label.get("sample_id"))
        if not item:
            continue
        expected = "PROTECTED" if item.get("protected_fixes", 0) else "UNPROTECTED"
        matrix[(expected, label.get("protection", "UNKNOWN"))] += 1
    return {f"{expected}->{observed}": count for (expected, observed), count in sorted(matrix.items())}


def _group_rates(labels: list[dict[str, Any]], corpus: dict[str, dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        item = corpus.get(label.get("sample_id"))
        if not item:
            continue
        groups[f"repository:{item['repository']}"].append(label)
        confidence_bucket = item.get("confidence_bucket")
        if confidence_bucket is None and isinstance(item.get("stratum"), list) and len(item["stratum"]) > 1:
            confidence_bucket = item["stratum"][1]
        groups[f"confidence_bucket:{confidence_bucket or 'unknown'}"].append(label)
    return {key: _rates(value) for key, value in sorted(groups.items())}


def calculate_metrics(
    primary: Iterable[dict[str, Any]],
    secondary: Iterable[dict[str, Any]],
    corpus_items: Iterable[dict[str, Any]],
    baselines: dict[str, Iterable[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    primary_list = list(primary)
    secondary_list = list(secondary)
    corpus = {item["sample_id"]: item for item in corpus_items}
    second_by_id = {item.get("sample_id"): item for item in secondary_list}
    overlap_primary = [item for item in primary_list if item.get("sample_id") in second_by_id]
    overlap_secondary = [second_by_id[item["sample_id"]] for item in overlap_primary]
    useful_primary = _rates(primary_list)
    result: dict[str, Any] = {
        "metrics_version": "metrics-v1",
        "execution_profile": "automated/public-evidence",
        "human_validity": "NOT ASSESSED",
        "primary": useful_primary,
        "secondary": _rates(secondary_list),
        "by_group": _group_rates(primary_list, corpus),
        "independent_pass_agreement": {
            "overlap": len(overlap_primary),
            "verdict_exact_agreement": sum(a["verdict"] == b["verdict"] for a, b in zip(overlap_primary, overlap_secondary, strict=True)),
            "verdict_agreement_rate": _wilson(sum(a["verdict"] == b["verdict"] for a, b in zip(overlap_primary, overlap_secondary, strict=True)), len(overlap_primary)),
            "kappa": _kappa([item["verdict"] for item in overlap_primary], [item["verdict"] for item in overlap_secondary]),
            "label": "independent-pass agreement; not human Cohen's kappa",
        },
        "test_protection_confusion_primary_against_0_1_proxy": _protection_confusion(primary_list, corpus),
        "cluster_purity": {"status": "NOT ASSESSED", "reason": "No independent cluster labels are present in the automated proxy corpus."},
        "baselines": {},
        "error_tags": dict(sorted(Counter(tag for label in primary_list for tag in label.get("error_tags", [])).items())),
    }
    for name, labels in (baselines or {}).items():
        summary = _rates(list(labels))
        baseline_useful = summary["useful_rate"]["estimate"]
        primary_useful = useful_primary["useful_rate"]["estimate"]
        summary["usefulness_delta_vs_primary"] = primary_useful - baseline_useful if primary_useful is not None and baseline_useful is not None else None
        result["baselines"][name] = summary
    return result


def write_metrics(
    primary_path: Path | str,
    secondary_path: Path | str,
    corpus_path: Path | str,
    output_path: Path | str,
    baseline_paths: dict[str, Path | str] | None = None,
) -> Path:
    result = calculate_metrics(
        read_jsonl(primary_path),
        read_jsonl(secondary_path),
        read_jsonl(corpus_path),
        {name: read_jsonl(path) for name, path in (baseline_paths or {}).items()},
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output
