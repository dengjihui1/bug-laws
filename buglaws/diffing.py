from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .schema import migrate_report_payload


def _fingerprint(law: dict[str, Any]) -> str:
    value = {"title": law.get("title"), "evidence": [(item.get("commit"), item.get("source_files", [])) for item in law.get("evidence", [])]}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def diff_reports(old_path: str | Path, new_path: str | Path) -> dict[str, Any]:
    old = migrate_report_payload(json.loads(Path(old_path).read_text(encoding="utf-8")))
    new = migrate_report_payload(json.loads(Path(new_path).read_text(encoding="utf-8")))
    old_map = {(old.get("repository"), law.get("law_id")): law for law in old.get("laws", [])}
    new_map = {(new.get("repository"), law.get("law_id")): law for law in new.get("laws", [])}
    new_items = [{"repository": key[0], "law_id": key[1], "title": law.get("title")} for key, law in new_map.items() if key not in old_map]
    resolved = [{"repository": key[0], "law_id": key[1], "title": law.get("title")} for key, law in old_map.items() if key not in new_map]
    changed = [{"repository": key[0], "law_id": key[1], "old_title": old_map[key].get("title"), "new_title": new_map[key].get("title")} for key in sorted(old_map.keys() & new_map.keys()) if _fingerprint(old_map[key]) != _fingerprint(new_map[key])]
    return {"diff_version": "report-diff-v1", "identity": "repository + law_id", "old_schema_version": old.get("schema_version"), "new_schema_version": new.get("schema_version"), "new": new_items, "changed": changed, "resolved": resolved, "resurfaced": [], "counts": {"new": len(new_items), "changed": len(changed), "resolved": len(resolved), "resurfaced": 0}}


def write_diff(old_path: str | Path, new_path: str | Path, output: str | Path) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(diff_reports(old_path, new_path), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
