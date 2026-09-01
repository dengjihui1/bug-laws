from __future__ import annotations

from copy import deepcopy
from typing import Any


REPORT_SCHEMA_VERSION = "report-v1"
LEGACY_REPORT_SCHEMA_VERSION = "report-v0"


class ReportSchemaError(ValueError):
    pass


def migrate_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a 0.1 report payload without inventing missing evidence."""
    if not isinstance(payload, dict):
        raise ReportSchemaError("report payload must be an object")
    migrated = deepcopy(payload)
    version = migrated.get("schema_version", LEGACY_REPORT_SCHEMA_VERSION)
    if version == LEGACY_REPORT_SCHEMA_VERSION:
        migrated["schema_version"] = REPORT_SCHEMA_VERSION
        for law in migrated.get("laws", []):
            law.setdefault("structured", None)
            law.setdefault("cluster_explanation", {})
    elif version != REPORT_SCHEMA_VERSION:
        raise ReportSchemaError(f"unsupported report schema: {version}")
    validate_report_payload(migrated)
    return migrated


def validate_report_payload(payload: dict[str, Any]) -> None:
    required = {"schema_version", "repository", "generated_at", "laws", "summary"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ReportSchemaError(f"missing report fields: {', '.join(missing)}")
    if payload["schema_version"] != REPORT_SCHEMA_VERSION:
        raise ReportSchemaError(f"expected {REPORT_SCHEMA_VERSION}")
    if not isinstance(payload["laws"], list):
        raise ReportSchemaError("report laws must be a list")
    for index, law in enumerate(payload["laws"]):
        if not isinstance(law, dict):
            raise ReportSchemaError(f"law {index} must be an object")
        for key in ("law_id", "title", "confidence", "evidence", "affected_files"):
            if key not in law:
                raise ReportSchemaError(f"law {index} missing {key}")
