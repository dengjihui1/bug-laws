from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def calibrate_confidence(provenance: Iterable[dict[str, Any]], labels: Iterable[dict[str, Any]]) -> dict[str, Any]:
    label_by_id = {item.get("sample_id"): item for item in labels}
    groups: dict[str, list[tuple[float, int, bool]]] = defaultdict(list)
    for item in provenance:
        label = label_by_id.get(item.get("sample_id"))
        if not label:
            continue
        raw = float(item.get("confidence", 0.0))
        useful = label.get("verdict") in {"ACCEPT", "EDIT"}
        bucket = "high" if raw >= 0.85 else "medium" if raw >= 0.65 else "near_threshold" if raw >= 0.50 else "below_threshold"
        groups[bucket].append((raw, int(useful), label.get("verdict") == "UNSCORABLE"))

    bins: dict[str, Any] = {}
    total = 0
    weighted_error = 0.0
    brier_sum = 0.0
    for bucket in sorted(groups):
        values = groups[bucket]
        n = len(values)
        useful = sum(value[1] for value in values)
        mean_raw = sum(value[0] for value in values) / n
        observed = useful / n
        calibrated = (useful + 1) / (n + 2)
        bins[bucket] = {
            "n": n,
            "mean_raw_confidence": round(mean_raw, 4),
            "useful_count": useful,
            "unscorable_count": sum(value[2] for value in values),
            "observed_useful_rate": round(observed, 4),
            "laplace_smoothed_rate": round(calibrated, 4),
            "sufficient_for_lookup": n >= 10,
        }
        total += n
        weighted_error += abs(mean_raw - observed) * n
        brier_sum += sum((value[0] - value[1]) ** 2 for value in values)
    return {
        "calibration_version": "calibration-v1",
        "execution_profile": "model-assisted/public-evidence proxy",
        "human_validity": "NOT ASSESSED",
        "n": total,
        "bins": bins,
        "expected_calibration_error": round(weighted_error / total, 4) if total else None,
        "brier_score": round(brier_sum / total, 4) if total else None,
        "policy": "diagnostic only; default confidence and threshold are unchanged",
    }


def write_calibration(provenance_path: str | Path, labels_path: str | Path, output_path: str | Path) -> Path:
    result = calibrate_confidence(read_jsonl(provenance_path), read_jsonl(labels_path))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output
