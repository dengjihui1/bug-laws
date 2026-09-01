from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schema import migrate_report_payload


REVIEW_SCHEMA_VERSION = "accepted-laws-v1"
VERDICTS = {"PENDING", "ACCEPT", "EDIT", "REJECT", "UNSCORABLE"}


def _read(path: str | Path) -> tuple[dict[str, Any], str]:
    raw = Path(path).read_bytes()
    return migrate_report_payload(json.loads(raw)), hashlib.sha256(raw).hexdigest()


def create_review_store(report_path: str | Path) -> dict[str, Any]:
    report, report_hash = _read(report_path)
    return {
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "source_report": str(report_path),
        "source_report_sha256": report_hash,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "entries": [
            {
                "repository": report.get("repository"),
                "law_id": law["law_id"],
                "original_title": law.get("title", ""),
                "verdict": "PENDING",
                "edited_title": "",
                "rationale": "",
                "reviewer": "",
                "reviewed_at_utc": None,
                "evidence": law.get("evidence", []),
                "source_report_sha256": report_hash,
            }
            for law in sorted(report.get("laws", []), key=lambda item: str(item.get("law_id", "")))
        ],
    }


def write_review_store(store: dict[str, Any], output: str | Path) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def decide(store_path: str | Path, sample_id: str, verdict: str, *, reviewer: str, rationale: str = "", edited_title: str = "") -> Path:
    if verdict not in VERDICTS - {"PENDING"}:
        raise ValueError(f"unsupported verdict: {verdict}")
    target = Path(store_path)
    store = json.loads(target.read_text(encoding="utf-8"))
    matches = [entry for entry in store.get("entries", []) if entry.get("law_id") == sample_id or entry.get("sample_id") == sample_id]
    if len(matches) != 1:
        raise ValueError(f"review item not found or not unique: {sample_id}")
    entry = matches[0]
    if verdict == "EDIT" and not edited_title.strip():
        raise ValueError("EDIT requires --edited-title")
    entry.update({"verdict": verdict, "edited_title": edited_title, "rationale": rationale, "reviewer": reviewer, "reviewed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
    return write_review_store(store, target)


def export_accepted(store_path: str | Path, output: str | Path) -> Path:
    store = json.loads(Path(store_path).read_text(encoding="utf-8"))
    accepted = []
    for entry in store.get("entries", []):
        if entry.get("verdict") in {"ACCEPT", "EDIT"}:
            accepted.append({"law_id": entry["law_id"], "repository": entry.get("repository"), "title": entry.get("edited_title") or entry.get("original_title", ""), "original_title": entry.get("original_title", ""), "verdict": entry["verdict"], "rationale": entry.get("rationale", ""), "reviewer": entry.get("reviewer", ""), "reviewed_at_utc": entry.get("reviewed_at_utc"), "source_report_sha256": entry.get("source_report_sha256"), "evidence": entry.get("evidence", [])})
    payload = {"accepted_laws_schema_version": REVIEW_SCHEMA_VERSION, "source_report_sha256": store.get("source_report_sha256"), "laws": accepted}
    return write_review_store(payload, output)
