from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from buglaws.diffing import diff_reports
from buglaws.review import create_review_store, decide, export_accepted


class ReviewDiffTest(unittest.TestCase):
    def test_review_decision_and_export_preserve_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.json"
            report.write_text(json.dumps({"repository": "repo", "generated_at": "now", "laws": [{"law_id": "LAW-1", "title": "Old", "confidence": 0.8, "evidence": [{"commit": "abc", "source_files": ["x.py"]}], "affected_files": ["x.py"]}], "summary": {}}), encoding="utf-8")
            store_path = root / "review.json"
            store_path.write_text(json.dumps(create_review_store(report)), encoding="utf-8")
            decide(store_path, "LAW-1", "EDIT", reviewer="tester", edited_title="New", rationale="bounded")
            accepted = root / "accepted.json"
            export_accepted(store_path, accepted)
            payload = json.loads(accepted.read_text(encoding="utf-8"))
            self.assertEqual(payload["laws"][0]["title"], "New")
            self.assertEqual(payload["laws"][0]["evidence"][0]["commit"], "abc")

    def test_diff_reports_changed_and_resolved(self) -> None:
        old = {"repository": "repo", "generated_at": "now", "laws": [{"law_id": "LAW-1", "title": "Old", "confidence": 0.8, "affected_files": ["x.py"], "evidence": [{"commit": "abc", "source_files": ["x.py"]}]}, {"law_id": "LAW-2", "title": "Gone", "confidence": 0.8, "affected_files": [], "evidence": []}], "summary": {}}
        new = {"repository": "repo", "generated_at": "now", "laws": [{"law_id": "LAW-1", "title": "New", "confidence": 0.8, "affected_files": ["x.py"], "evidence": [{"commit": "abc", "source_files": ["x.py"]}]}, {"law_id": "LAW-3", "title": "Added", "confidence": 0.8, "affected_files": [], "evidence": []}], "summary": {}}
        result = diff_reports_from_payload(old, new)
        self.assertEqual(result["counts"], {"new": 1, "changed": 1, "resolved": 1, "resurfaced": 0})


def diff_reports_from_payload(old: dict, new: dict) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        old_path, new_path = root / "old.json", root / "new.json"
        old_path.write_text(json.dumps(old), encoding="utf-8")
        new_path.write_text(json.dumps(new), encoding="utf-8")
        return diff_reports(old_path, new_path)


if __name__ == "__main__":
    unittest.main()
