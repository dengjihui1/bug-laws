from __future__ import annotations

import hashlib
import json
import random
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


BASELINE_VERSION = "baseline-v1"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_commit() -> str:
    repository = Path(__file__).resolve().parent.parent
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _humanize_test_signal(signal: str) -> str:
    value = re.sub(r"^test:", "", signal).strip().replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value[:1].upper() + value[1:] if value else ""


def _first_evidence(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence", [])
    return evidence[0] if evidence else {}


def _first_test_name(item: dict[str, Any]) -> str:
    for evidence in item.get("evidence", []):
        for signal in evidence.get("signals", []):
            if str(signal).startswith("test:"):
                return _humanize_test_signal(str(signal))
    return ""


def _form_id(seed: int, baseline_type: str, sample_id: str) -> str:
    value = f"{seed}:{baseline_type}:{sample_id}".encode("utf-8")
    return "F-" + hashlib.sha256(value).hexdigest()[:20]


def _evidence_copy(item: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(evidence) for evidence in item.get("evidence", [])]


def build_baselines(items: Iterable[dict[str, Any]], *, seed: int) -> dict[str, list[dict[str, Any]]]:
    output = {"commit_subject": [], "test_name": [], "bug_laws_0_1": []}
    for item in items:
        first = _first_evidence(item)
        source = _evidence_copy(item)
        common = {"sample_id": item["sample_id"], "evidence": source}
        output["commit_subject"].append({**common, "title": str(first.get("subject", ""))})
        output["test_name"].append({**common, "title": _first_test_name(item)})
        output["bug_laws_0_1"].append({**common, "title": str(item.get("title", ""))})
    for baseline_type, forms in output.items():
        forms.sort(key=lambda form: form["sample_id"])
        random.Random(f"{seed}:{baseline_type}").shuffle(forms)
        for form in forms:
            sample_id = form["sample_id"]
            form["form_id"] = _form_id(seed, baseline_type, form["sample_id"])
            form.pop("sample_id", None)
            form["_source_sample_id"] = sample_id
    return output


def write_baselines(input_path: Path | str, output_directory: Path | str, *, seed: int) -> list[Path]:
    source = Path(input_path)
    source_bytes = source.read_bytes()
    items = [json.loads(line) for line in source_bytes.decode("utf-8").splitlines() if line.strip()]
    baselines = build_baselines(items, seed=seed)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    mapping: list[dict[str, str]] = []
    for baseline_type, forms in baselines.items():
        path = output / f"{baseline_type}.jsonl"
        public_forms = [{key: value for key, value in form.items() if key != "_source_sample_id"} for form in forms]
        path.write_text("".join(json.dumps(form, ensure_ascii=False, sort_keys=True) + "\n" for form in public_forms), encoding="utf-8")
        paths.append(path)
        for form in forms:
            mapping.append({"form_id": form["form_id"], "sample_id": form.pop("_source_sample_id"), "baseline_type": baseline_type})
    mapping_path = output / "mapping.jsonl"
    mapping_path.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in sorted(mapping, key=lambda item: item["form_id"])), encoding="utf-8")
    paths.append(mapping_path)
    manifest = {
        "artifact_version": BASELINE_VERSION,
        "seed": seed,
        "source_corpus": source.name,
        "source_corpus_sha256": _sha256_bytes(source_bytes),
        "tool_commit": _git_commit(),
        "source_record_count": len(items),
        "baseline_types": list(baselines),
        "records_per_baseline": {key: len(value) for key, value in baselines.items()},
        "reviewer_view": {"excludes": ["sample_id", "repository", "law_id", "confidence", "ranking", "baseline_type"]},
        "mapping_note": "mapping.jsonl is evaluator metadata and is not part of the reviewer packet; the three baseline forms omit sample_id, repository, law_id, and baseline_type.",
    }
    manifest_path = output / "manifest.json"
    manifest["artifacts"] = {
        path.name: {"sha256": _sha256_bytes(path.read_bytes()), "records": len(baselines[path.stem]) if path.stem in baselines else None}
        for path in paths
        if path.name != "mapping.jsonl"
    }
    manifest["artifacts"]["mapping.jsonl"] = {"sha256": _sha256_bytes(mapping_path.read_bytes()), "records": len(mapping)}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths.append(manifest_path)
    return paths
