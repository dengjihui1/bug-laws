from __future__ import annotations

import hashlib
import json
import random
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


class SamplingError(ValueError):
    """Raised when report inputs cannot form a valid sampling dataset."""


@dataclass(frozen=True)
class SampledDataset:
    reviewer_items: list[dict[str, Any]]
    provenance_items: list[dict[str, Any]]
    manifest: dict[str, Any]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _confidence_bucket(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.65:
        return "medium"
    if confidence >= 0.50:
        return "near_threshold"
    return "below_threshold"


def _recurrence_bucket(recurrence: int) -> str:
    return "recurrent" if recurrence > 1 else "singleton"


def _test_gap_state(law: dict[str, Any]) -> str:
    protected = int(law.get("protected_fixes", 0) or 0)
    unprotected = int(law.get("unprotected_fixes", 0) or 0)
    if protected and unprotected:
        return "mixed"
    if unprotected:
        return "apparent_gap"
    if protected:
        return "protected"
    return "unknown"


def _sanitize_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    if re.match(r"^(?:[A-Za-z]:/|//|/|~[/])", normalized):
        return "<local-path-redacted>"
    return normalized.lstrip("./")


def _sanitize_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    allowed = ("commit", "date", "subject", "issue_refs", "source_files", "test_files", "signals", "candidate_title", "changed_symbols", "units")
    result: dict[str, Any] = {}
    for key in allowed:
        value = evidence.get(key, [] if key.endswith("s") else "")
        if key in {"source_files", "test_files"}:
            result[key] = [_sanitize_path(str(item)) for item in value]
        elif key == "units":
            result[key] = [
                {
                    **unit,
                    "source_files": [_sanitize_path(str(path)) for path in unit.get("source_files", [])],
                    "test_files": [_sanitize_path(str(path)) for path in unit.get("test_files", [])],
                }
                for unit in value
            ]
        else:
            result[key] = value
    return result


def _sanitized_law(law: dict[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in law.items() if key not in {"evidence", "source_label", "stratum"}}
    result["evidence"] = [_sanitize_evidence(evidence) for evidence in law.get("evidence", [])]
    return result


def _stable_id(repository: str, law_id: str) -> str:
    identity = json.dumps({"law_id": law_id, "repository": repository}, sort_keys=True, separators=(",", ":"))
    return "S-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def _load_report(source: Path | str | dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    if isinstance(source, dict):
        raw = json.dumps(source, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return source, _sha256_bytes(raw), "inline-report.json"
    path = Path(source)
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("laws"), list):
        raise SamplingError(f"report must be an object with a laws list: {path}")
    return payload, _sha256_bytes(raw), path.name


def _git_commit() -> str:
    repository = Path(__file__).resolve().parent.parent
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _candidate_records(reports: Iterable[Path | str | dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    report_metadata: list[dict[str, Any]] = []
    for source in reports:
        payload, report_hash, source_label = _load_report(source)
        repository = str(payload.get("repository") or "<unlabelled-repository>")
        laws = payload["laws"]
        report_metadata.append({"source": source_label, "repository": repository, "report_sha256": report_hash, "law_count": len(laws)})
        for law in laws:
            if not isinstance(law, dict) or not law.get("law_id"):
                raise SamplingError(f"every law must be an object with law_id: {source_label}")
            law_id = str(law["law_id"])
            key = (repository, law_id)
            record = {
                "sample_id": _stable_id(repository, law_id),
                "repository": repository,
                "law_id": law_id,
                "title": str(law.get("title", "")),
                "confidence": float(law.get("confidence", 0.0)),
                "recurrence": int(law.get("recurrence", len(law.get("evidence", [])))),
                "protected_fixes": int(law.get("protected_fixes", 0) or 0),
                "unprotected_fixes": int(law.get("unprotected_fixes", 0) or 0),
                "evidence": law.get("evidence", []),
                "report_sha256": report_hash,
                "source_label": source_label,
            }
            # Duplicate logical laws are resolved by a stable report hash, never by input order.
            previous = candidates.get(key)
            if previous is None or (record["report_sha256"], record["source_label"]) < (previous["report_sha256"], previous["source_label"]):
                candidates[key] = record
    return list(candidates.values()), report_metadata


def sample_reports(reports: Iterable[Path | str | dict[str, Any]], *, seed: int, total: int) -> SampledDataset:
    if total < 1:
        raise SamplingError("total must be positive")
    candidates, report_metadata = _candidate_records(reports)
    if not candidates:
        raise SamplingError("at least one candidate law is required")
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        stratum = (
            candidate["repository"],
            _confidence_bucket(candidate["confidence"]),
            _recurrence_bucket(candidate["recurrence"]),
            _test_gap_state(candidate),
        )
        candidate["stratum"] = stratum
        groups[stratum].append(candidate)
    for key, items in groups.items():
        items.sort(key=lambda item: item["sample_id"])
        random.Random(f"{seed}:{key}").shuffle(items)

    selected: list[dict[str, Any]] = []
    ordered_keys = sorted(groups)
    while len(selected) < min(total, len(candidates)):
        progressed = False
        for key in ordered_keys:
            if groups[key]:
                selected.append(groups[key].pop(0))
                progressed = True
                if len(selected) == total:
                    break
        if not progressed:
            break

    reviewer_items: list[dict[str, Any]] = []
    provenance_items: list[dict[str, Any]] = []
    for item in selected:
        reviewer_items.append(
            {
                "sample_id": item["sample_id"],
                "repository": item["repository"],
                "law_id": item["law_id"],
                "title": item["title"],
                "recurrence": item["recurrence"],
                "protected_fixes": item["protected_fixes"],
                "unprotected_fixes": item["unprotected_fixes"],
                "evidence": [_sanitize_evidence(evidence) for evidence in item["evidence"]],
            }
        )
        provenance_items.append(
            {
                "sample_id": item["sample_id"],
                "repository": item["repository"],
                "law_id": item["law_id"],
                "title": item["title"],
                "confidence": item["confidence"],
                "stratum": list(item["stratum"]),
                "recurrence": item["recurrence"],
                "test_gap_state": _test_gap_state(item),
                "report_sha256": item["report_sha256"],
                "source_label": item["source_label"],
                "law": _sanitized_law(item),
            }
        )

    manifest = {
        "manifest_version": "annotation-dataset-v1",
        "protocol_version": "annotation-v1",
        "seed": seed,
        "requested_count": total,
        "selected_count": len(selected),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tool_commit": _git_commit(),
        "inputs": report_metadata,
        "counts": {
            "repository": dict(sorted(Counter(item["repository"] for item in selected).items())),
            "confidence_bucket": dict(sorted(Counter(item["stratum"][1] for item in selected).items())),
            "recurrence_bucket": dict(sorted(Counter(item["stratum"][2] for item in selected).items())),
            "test_gap_state": dict(sorted(Counter(_test_gap_state(item) for item in selected).items())),
        },
        "reviewer_view": {
            "excludes": ["confidence", "stratum", "ranking", "source_path", "report_hash"],
            "stable_order": "sample_id ascending",
        },
    }
    reviewer_items.sort(key=lambda item: item["sample_id"])
    provenance_items.sort(key=lambda item: item["sample_id"])
    return SampledDataset(reviewer_items, provenance_items, manifest)


def _jsonl(items: Iterable[dict[str, Any]]) -> str:
    return "".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for item in items)


def write_sample_dataset(
    reports: Iterable[Path | str | dict[str, Any]], output: Path | str, *, seed: int, total: int
) -> list[Path]:
    dataset = sample_reports(reports, seed=seed, total=total)
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    reviewer = output_path / "reviewer.jsonl"
    provenance = output_path / "provenance.jsonl"
    manifest = output_path / "manifest.json"
    reviewer.write_text(_jsonl(dataset.reviewer_items), encoding="utf-8")
    provenance.write_text(_jsonl(dataset.provenance_items), encoding="utf-8")
    dataset.manifest["artifacts"] = {
        "reviewer.jsonl": {"sha256": _sha256_bytes(reviewer.read_bytes()), "records": len(dataset.reviewer_items)},
        "provenance.jsonl": {"sha256": _sha256_bytes(provenance.read_bytes()), "records": len(dataset.provenance_items)},
    }
    manifest.write_text(json.dumps(dataset.manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return [reviewer, provenance, manifest]
