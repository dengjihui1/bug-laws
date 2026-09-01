from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def grade_evidence(evidence: dict[str, Any]) -> tuple[str, str]:
    """Return a conservative static test-protection grade and rationale."""
    test_files = evidence.get("test_files", [])
    signals = [str(signal) for signal in evidence.get("signals", [])]
    symbols = [str(symbol) for symbol in evidence.get("changed_symbols", [])]
    if test_files and symbols:
        symbol_names = {symbol.rsplit("::", 1)[-1].lower() for symbol in symbols}
        test_text = " ".join(signals).lower()
        if any(name and name in test_text for name in symbol_names):
            return "B", "changed-symbol name is present in test evidence; static linkage only"
    if test_files:
        return "C", "a test file changed in the commit; direct behavior linkage is unknown"
    return "U", "no inspectable regression-test linkage in supplied evidence"


def grade_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in items:
        grade_pairs = [grade_evidence(evidence) for evidence in item.get("evidence", [])]
        grades = [grade for grade, _ in grade_pairs]
        grade = "B" if "B" in grades else "C" if "C" in grades else "U"
        result.append({"sample_id": item.get("sample_id"), "law_id": item.get("law_id"), "protection_grade": grade, "evidence": [{"grade": value[0], "rationale": value[1]} for value in grade_pairs], "replay_available": False})
    return sorted(result, key=lambda item: str(item.get("sample_id", "")))


def write_grades(input_path: str | Path, output_path: str | Path) -> Path:
    items = [json.loads(line) for line in Path(input_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in grade_items(items)), encoding="utf-8")
    return output
