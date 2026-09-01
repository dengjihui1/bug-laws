from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .schema import migrate_report_payload, validate_report_payload


def _github_url(repository: str, number: str) -> str:
    return f"https://api.github.com/repos/{repository}/issues/{number}"


def _fetch_json(url: str, timeout: float = 10.0) -> tuple[dict[str, Any] | None, str | None]:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "bug-laws-evidence-enricher/0.2"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
        return json.loads(raw), hashlib.sha256(raw).hexdigest()
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None, None


def _snapshot(url: str, payload: dict[str, Any], response_hash: str, retrieved_at: str) -> dict[str, Any]:
    return {
        "url": url,
        "retrieved_at_utc": retrieved_at,
        "source_type": "github_issue_or_pr",
        "immutable_revision": f"response-sha256:{response_hash}",
        "response_sha256": response_hash,
        "title": payload.get("title"),
        "state": payload.get("state"),
        "body_excerpt": str(payload.get("body") or "")[:1000],
        "labels": [label.get("name") for label in payload.get("labels", []) if isinstance(label, dict) and label.get("name")],
    }


def enrich_report_payload(payload: dict[str, Any], repository: str, *, timeout: float = 10.0) -> dict[str, Any]:
    """Return a copy with optional GitHub snapshots; never changes original evidence."""
    enriched = migrate_report_payload(payload)
    retrieved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for law in enriched["laws"]:
        for evidence in law.get("evidence", []):
            snapshots: list[dict[str, Any]] = []
            failures: list[dict[str, Any]] = []
            for number in evidence.get("issue_refs", []):
                url = _github_url(repository, str(number))
                data, response_hash = _fetch_json(url, timeout)
                if data is None or response_hash is None:
                    failures.append({"url": url, "retrieved_at_utc": retrieved_at, "source_type": "github_issue_or_pr", "error": "fetch_failed"})
                else:
                    snapshots.append(_snapshot(url, data, response_hash, retrieved_at))
            evidence["external_evidence"] = snapshots
            if failures:
                evidence["external_evidence_failures"] = failures
    validate_report_payload(enriched)
    return enriched


def enrich_report(input_path: str | Path, output_path: str | Path, repository: str, *, timeout: float = 10.0) -> Path:
    input_file = Path(input_path)
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    result = enrich_report_payload(payload, repository, timeout=timeout)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_file
