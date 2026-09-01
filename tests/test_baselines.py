from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from buglaws.baselines import build_baselines, write_baselines


def item(sample_id: str) -> dict:
    return {
        "sample_id": sample_id,
        "repository": "private-local-name",
        "law_id": "LAW-1",
        "title": "Cache keys must include tenant identity",
        "evidence": [{
            "subject": "fix: prevent cross-tenant cache collisions (#12)",
            "signals": ["test:test_cache_key_includes_tenant_id", "guard:assert tenant_id"],
            "source_files": ["src/cache.py"],
            "test_files": ["tests/test_cache.py"],
        }],
    }


class BaselineTest(unittest.TestCase):
    def test_baselines_use_expected_text(self) -> None:
        forms = build_baselines([item("S-1")], seed=1)
        self.assertEqual(forms["commit_subject"][0]["title"], "fix: prevent cross-tenant cache collisions (#12)")
        self.assertEqual(forms["test_name"][0]["title"], "Test cache key includes tenant id")
        self.assertEqual(forms["bug_laws_0_1"][0]["title"], "Cache keys must include tenant identity")
        self.assertNotIn("sample_id", forms["commit_subject"][0])

    def test_order_and_form_ids_are_deterministic(self) -> None:
        values = [item("S-2"), item("S-1")]
        first = build_baselines(values, seed=9)
        second = build_baselines(list(reversed(values)), seed=9)
        self.assertEqual(first, second)

    def test_write_creates_three_blinded_forms(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "reviewer.jsonl"
            source.write_text("\n".join(json.dumps(item(f"S-{i}")) for i in range(2)) + "\n", encoding="utf-8")
            output = Path(directory) / "baselines"
            paths = write_baselines(source, output, seed=10)
            self.assertEqual({path.name for path in paths}, {"commit_subject.jsonl", "test_name.jsonl", "bug_laws_0_1.jsonl", "mapping.jsonl", "manifest.json"})
            content = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.name.endswith(".jsonl"))
            self.assertNotIn("private-local-name", content)
            self.assertNotIn("baseline_type", output.joinpath("commit_subject.jsonl").read_text(encoding="utf-8"))
            self.assertNotIn("_source_sample_id", output.joinpath("commit_subject.jsonl").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
