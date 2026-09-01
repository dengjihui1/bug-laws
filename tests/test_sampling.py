from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from buglaws.sample import sample_reports, write_sample_dataset


def report(repository: str, laws: list[dict]) -> dict:
    return {
        "repository": repository,
        "generated_at": "2026-09-01T00:00:00+00:00",
        "since": None,
        "commits_seen": 100,
        "candidate_commits": len(laws),
        "laws": laws,
        "summary": {"law_count": len(laws), "repeated_laws": 0, "fixes_without_tests": 0},
    }


def law(law_id: str, confidence: float, *, recurrence: int = 1, gap: bool = False, source: str = "src/app.py") -> dict:
    return {
        "law_id": law_id,
        "title": f"Law {law_id}",
        "confidence": confidence,
        "evidence": [
            {
                "commit": f"{law_id:0>2}" * 20,
                "date": "2026-01-01T00:00:00+00:00",
                "subject": "fix: preserve behavior",
                "issue_refs": [law_id],
                "source_files": [source],
                "test_files": [] if gap else ["tests/test_app.py"],
                "signals": [],
                "candidate_title": f"Law {law_id}",
                "confidence": confidence,
            }
            for _ in range(recurrence)
        ],
        "affected_files": [source],
        "recurrence": recurrence,
        "protected_fixes": 0 if gap else recurrence,
        "unprotected_fixes": recurrence if gap else 0,
    }


class SamplingTest(unittest.TestCase):
    def test_same_seed_is_order_independent_and_uses_stable_ids(self) -> None:
        reports = [
            report("repo-a", [law("LAW-1", 0.90), law("LAW-2", 0.70, recurrence=2)]),
            report("repo-b", [law("LAW-1", 0.55, gap=True)]),
        ]
        first = sample_reports(reports, seed=42, total=2)
        reversed_reports = [dict(reports[1], laws=list(reversed(reports[1]["laws"]))), dict(reports[0], laws=list(reversed(reports[0]["laws"]))) ]
        second = sample_reports(reversed_reports, seed=42, total=2)
        self.assertEqual([item["sample_id"] for item in first.reviewer_items], [item["sample_id"] for item in second.reviewer_items])
        self.assertEqual(len({item["sample_id"] for item in first.reviewer_items}), 2)
        self.assertNotIn("confidence", first.reviewer_items[0])
        self.assertNotIn("stratum", first.reviewer_items[0])

    def test_small_buckets_and_insufficient_total_are_handled(self) -> None:
        reports = [report("repo", [law("LAW-1", 0.90), law("LAW-2", 0.55, gap=True)])]
        sampled = sample_reports(reports, seed=1, total=10)
        self.assertEqual(len(sampled.reviewer_items), 2)
        self.assertEqual(sampled.manifest["selected_count"], 2)
        self.assertIn("high", sampled.manifest["counts"]["confidence_bucket"])
        self.assertIn("near_threshold", sampled.manifest["counts"]["confidence_bucket"])

    def test_duplicate_law_ids_across_repositories_do_not_collide(self) -> None:
        reports = [
            report("repo-a", [law("LAW-1", 0.90)]),
            report("repo-b", [law("LAW-1", 0.90)]),
        ]
        sampled = sample_reports(reports, seed=2, total=10)
        self.assertEqual(len({item["sample_id"] for item in sampled.reviewer_items}), 2)
        self.assertEqual({item["repository"] for item in sampled.reviewer_items}, {"repo-a", "repo-b"})

    def test_absolute_paths_are_redacted_in_reviewer_view(self) -> None:
        reports = [report("repo", [law("LAW-1", 0.90, source=r"C:\Users\secret\repo\src\app.py")])]
        sampled = sample_reports(reports, seed=3, total=1)
        serialized = json.dumps(sampled.reviewer_items)
        self.assertNotIn("C:\\Users", serialized)
        self.assertNotIn("secret", serialized)
        self.assertIn("<local-path-redacted>", serialized)
        self.assertNotIn("secret", json.dumps(sampled.provenance_items))

    def test_write_preserves_source_reports_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "report.json"
            payload = report("repo", [law("LAW-1", 0.90)])
            source.write_text(json.dumps(payload), encoding="utf-8")
            before = source.read_bytes()
            output = root / "sample"
            paths = write_sample_dataset([source], output, seed=9, total=1)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual({path.name for path in paths}, {"reviewer.jsonl", "provenance.jsonl", "manifest.json"})
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["seed"], 9)
            self.assertEqual(manifest["selected_count"], 1)


if __name__ == "__main__":
    unittest.main()
