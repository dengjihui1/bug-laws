from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from buglaws.analyze import analyze_repository
from buglaws.render import write_report
from buglaws.schema import REPORT_SCHEMA_VERSION, ReportSchemaError, migrate_report_payload
from buglaws.git_history import read_history


def run(repository: Path, *args: str) -> None:
    result = subprocess.run(
        [*args],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)


class BugLawsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name)
        run(self.repository, "git", "init", "-q")
        run(self.repository, "git", "config", "user.email", "fixture@example.com")
        run(self.repository, "git", "config", "user.name", "Fixture Author")
        self._write("cache.py", "def cache_key(resource):\n    return resource\n")
        self._write("tests/test_cache.py", "def test_cache_key():\n    assert True\n")
        self._commit("initial implementation")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write(self, path: str, content: str) -> None:
        target = self.repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def _commit(self, message: str) -> None:
        run(self.repository, "git", "add", ".")
        run(self.repository, "git", "commit", "-q", "-m", message)

    def _add_history(self) -> None:
        self._write(
            "cache.py",
            "def cache_key(resource, tenant_id):\n    assert tenant_id\n    return f'{tenant_id}:{resource}'\n",
        )
        self._write(
            "tests/test_cache.py",
            "def test_cache_key_includes_tenant_id():\n    assert True\n",
        )
        self._commit("fix: prevent cross-tenant cache collisions #12")

        self._write(
            "cache.py",
            "def cache_key(resource, tenant_id):\n    if tenant_id is None:\n        raise ValueError('tenant required')\n    return f'{tenant_id}:{resource}'\n",
        )
        self._commit("fix: cache key includes tenant id on fallback path #18")

        self._write("README.md", "Documentation only\n")
        self._commit("docs: explain cache keys")

    def test_recovers_evidence_and_test_gap(self) -> None:
        self._add_history()
        report = analyze_repository(self.repository)
        self.assertEqual(report.commits_seen, 4)
        self.assertEqual(report.candidate_commits, 2)
        self.assertTrue(report.laws)
        self.assertGreaterEqual(report.fixes_without_tests, 1)
        self.assertTrue(any("tenant" in law.title.lower() for law in report.laws))
        self.assertTrue(any(item.issue_refs for law in report.laws for item in law.evidence))
        self.assertTrue(any("cache.py::cache_key" in item.changed_symbols for law in report.laws for item in law.evidence))
        self.assertTrue(all(law.structured for law in report.laws))
        for law in report.laws:
            assert law.structured is not None
            self.assertEqual(law.structured.scope, law.affected_files)
            self.assertTrue(all(commit in {item.commit for item in law.evidence} for refs in law.structured.field_evidence.values() for commit in refs))
            self.assertEqual(law.cluster_explanation["method"], "complete_link_agglomerative")
            self.assertEqual(set(law.cluster_explanation["member_commits"]), {item.commit for item in law.evidence})
            self.assertTrue(all(unit.unit_id.startswith(item.commit[:12]) for item in law.evidence for unit in item.units))

    def test_writes_three_inspectable_artifacts(self) -> None:
        self._add_history()
        report = analyze_repository(self.repository)
        output = self.repository / "report"
        paths = write_report(report, output)
        self.assertEqual({path.name for path in paths}, {"BUG_LAWS.md", "bug-laws.json", "index.html"})
        payload = json.loads((output / "bug-laws.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["summary"]["law_count"], len(report.laws))
        self.assertIn("structured", payload["laws"][0])
        self.assertEqual(payload["schema_version"], REPORT_SCHEMA_VERSION)
        html = (output / "index.html").read_text(encoding="utf-8")
        self.assertIn("Evidence, not authority", html)
        self.assertTrue(all(not line.endswith((" ", "\t")) for line in html.splitlines()))

    def test_legacy_report_migrates_without_inventing_structure(self) -> None:
        legacy = {"repository": "repo", "generated_at": "now", "laws": [], "summary": {}}
        migrated = migrate_report_payload(legacy)
        self.assertEqual(migrated["schema_version"], REPORT_SCHEMA_VERSION)
        with self.assertRaises(ReportSchemaError):
            migrate_report_payload({**legacy, "schema_version": "report-v99"})

    def test_ignores_non_python_bug_fixes(self) -> None:
        self._write("app.js", "throw new Error('fixed')\n")
        self._commit("fix: javascript-only failure")
        self._write("cache.py", "def cache_key(resource):\n    return resource.strip()\n")
        self._commit("v0.2.0 release: docs + hook path fix + packaging")
        report = analyze_repository(self.repository)
        self.assertEqual(report.commits_seen, 3)
        self.assertEqual(report.candidate_commits, 1)
        self.assertEqual(report.laws, [])

    def test_history_cache_is_reused_and_isolated_by_head(self) -> None:
        cache = self.repository / "cache"
        first = read_history(self.repository, cache_dir=cache)
        second = read_history(self.repository, cache_dir=cache)
        self.assertEqual(first, second)
        self.assertEqual(len(list(cache.glob("history-*.json"))), 1)
        self._write("README.md", "new\n")
        self._commit("docs: update readme")
        read_history(self.repository, cache_dir=cache)
        self.assertEqual(len(list(cache.glob("history-*.json"))), 2)


if __name__ == "__main__":
    unittest.main()
