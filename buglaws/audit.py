from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .protection import grade_evidence


PROTOCOL_VERSION = "annotation-v1"
AUDIT_VERSION = "automated-proxy-audit-v1"


def _has_test_signal(item: dict[str, Any]) -> bool:
    return any(str(signal).startswith("test:") for signal in item.get("signals", []))


def _has_assertion(item: dict[str, Any]) -> bool:
    return any("guard:assert" in str(signal) for signal in item.get("signals", []))


def _protection(item: dict[str, Any]) -> str:
    evidence = item.get("evidence", [])
    has_test_path = any(evidence_item.get("test_files") for evidence_item in evidence)
    has_test_signal = any(_has_test_signal(evidence_item) or _has_assertion(evidence_item) for evidence_item in evidence)
    if has_test_path and has_test_signal:
        return "PROTECTED"
    if has_test_path:
        return "CHANGED_BUT_UNLINKED"
    return "UNKNOWN"


def _joined_text(item: dict[str, Any]) -> str:
    parts = [str(item.get("title", ""))]
    for evidence in item.get("evidence", []):
        parts.append(str(evidence.get("subject", "")))
        parts.extend(str(signal) for signal in evidence.get("signals", []))
    return " ".join(parts).lower()


def _error_tags(item: dict[str, Any], verdict: str, *, weak_title: bool = False) -> list[str]:
    text = _joined_text(item)
    tags: list[str] = []
    if weak_title:
        tags.append("TEST_NAME_GRAMMAR")
    if any(word in text for word in ("typo", "docstring", "documentation", "docs", "line-too-long", "ruff e501", "black")):
        tags.append("NOT_A_BUG_FIX")
    if "typing" in text or "type error" in text:
        tags.append("IMPLEMENTATION_DETAIL_AS_LAW")
    if verdict == "UNSCORABLE":
        tags.append("INSUFFICIENT_EVIDENCE")
    return tags


def _edited_title(title: str, item: dict[str, Any]) -> str:
    cleaned = title.strip()
    if cleaned.lower().startswith("required behavior:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    if cleaned and any(token in cleaned.lower().split() for token in ("must", "preserve", "prevent", "handle", "support", "ensure", "only")):
        return cleaned
    affected = ", ".join(item.get("evidence", [{}])[0].get("source_files", [])[:2])
    suffix = f" in {affected}" if affected else ""
    return f"Clarify the required behavior for {cleaned or 'this change'}{suffix}."


def audit_item(item: dict[str, Any], *, mode: str) -> dict[str, Any]:
    evidence = item.get("evidence", [])
    text = _joined_text(item)
    has_source = any(evidence_item.get("source_files") for evidence_item in evidence)
    strong_evidence = any(
        evidence_item.get("issue_refs")
        or _has_test_signal(evidence_item)
        or _has_assertion(evidence_item)
        or len(evidence_item.get("signals", [])) >= 2
        for evidence_item in evidence
    )
    weak_title = len(str(item.get("title", "")).split()) < 4 or str(item.get("title", "")).lower().startswith("required behavior:")
    documentation_or_maintenance = any(
        word in text
        for word in ("typo", "docstring", "documentation", "docs", "line-too-long", "ruff e501", "black", "merge stable", "up appveyor", "fixed test execution")
    )
    if not evidence or not has_source or not strong_evidence:
        verdict = "UNSCORABLE"
        rationale = "The automated audit cannot establish the behavior from the supplied evidence package."
    elif documentation_or_maintenance and not any(_has_test_signal(evidence_item) or _has_assertion(evidence_item) for evidence_item in evidence):
        verdict = "REJECT"
        rationale = "The evidence describes documentation, formatting, typing, CI, or maintenance work rather than a reusable behavioral invariant."
    elif mode == "adversarial" and not any(_has_test_signal(evidence_item) or _has_assertion(evidence_item) for evidence_item in evidence) and len(evidence) == 1:
        verdict = "UNSCORABLE"
        rationale = "The adversarial pass requires an inspectable behavioral assertion for a singleton without a regression-test signal."
    elif weak_title or str(item.get("title", "")).lower().startswith("required behavior:"):
        verdict = "EDIT"
        rationale = "The evidence is potentially useful, but the generated title is fragmentary or includes implementation noise and needs semantic repair."
    else:
        verdict = "ACCEPT"
        rationale = "The supplied source, test, and signal evidence supports a bounded reusable behavior at the level available to this proxy audit."

    if verdict == "ACCEPT":
        scores = (2, 2, 2, 2, 2)
    elif verdict == "EDIT":
        scores = (2, 2, 1, 2, 1)
    elif verdict == "REJECT":
        scores = (0, 0, 0, 0, 0)
    else:
        scores = (1, 1, 1, 1, 1)
    return {
        "sample_id": item.get("sample_id") or item.get("form_id"),
        "repository": item.get("repository"),
        "law_id": item.get("law_id"),
        "label_source": AUDIT_VERSION,
        "audit_mode": mode,
        "protocol_version": PROTOCOL_VERSION,
        "verdict": verdict,
        "edited_title": _edited_title(str(item.get("title", "")), item) if verdict == "EDIT" else "",
        "grounding": scores[0],
        "abstraction": scores[1],
        "scope": scores[2],
        "usefulness": scores[3],
        "title_quality": scores[4],
        "protection": _protection(item),
        "protection_grade": _best_protection_grade(evidence),
        "cluster_label": "UNKNOWN",
        "error_tags": _error_tags(item, verdict, weak_title=weak_title),
        "rationale": rationale,
        "review_seconds": 1,
    }


def _best_protection_grade(evidence: list[dict[str, Any]]) -> str:
    grades = [grade_evidence(item)[0] for item in evidence]
    return "B" if "B" in grades else "C" if "C" in grades else "U"


def audit_items(items: Iterable[dict[str, Any]], *, mode: str = "primary") -> list[dict[str, Any]]:
    if mode not in {"primary", "adversarial"}:
        raise ValueError("mode must be primary or adversarial")
    output = [audit_item(item, mode=mode) for item in items]
    return sorted(output, key=lambda item: item["sample_id"])


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_audit(input_path: Path | str, output_path: Path | str, *, mode: str) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    labels = audit_items(read_jsonl(input_path), mode=mode)
    reviewed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    reviewer_id = f"automated-proxy-{mode}"
    for label in labels:
        label["reviewer_id"] = reviewer_id
        label["reviewed_at_utc"] = reviewed_at
    output.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in labels), encoding="utf-8")
    return output
