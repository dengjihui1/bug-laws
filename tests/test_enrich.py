from __future__ import annotations

import unittest
from unittest.mock import patch

from buglaws.enrich import enrich_report_payload


class EnrichTest(unittest.TestCase):
    def test_enrichment_is_explicit_and_preserves_original_evidence(self) -> None:
        payload = {
            "repository": "public/psf-requests",
            "generated_at": "now",
            "laws": [{"law_id": "LAW-001", "title": "Keep redirects safe", "confidence": 0.8, "evidence": [{"commit": "abc", "date": "now", "subject": "fix #12", "issue_refs": ["12"], "source_files": ["requests/sessions.py"], "test_files": [], "signals": [], "candidate_title": "Keep redirects safe"}], "affected_files": ["requests/sessions.py"]}],
            "summary": {},
        }
        with patch("buglaws.enrich._fetch_json", return_value=({"title": "Redirect bug", "state": "closed", "body": "details", "labels": []}, "deadbeef")):
            result = enrich_report_payload(payload, "psf/requests")
        evidence = result["laws"][0]["evidence"][0]
        self.assertEqual(evidence["subject"], "fix #12")
        self.assertEqual(evidence["external_evidence"][0]["immutable_revision"], "response-sha256:deadbeef")
        self.assertNotIn("external_evidence", payload["laws"][0]["evidence"][0])

    def test_failed_fetch_remains_visible(self) -> None:
        payload = {"repository": "repo", "generated_at": "now", "laws": [], "summary": {}}
        self.assertEqual(enrich_report_payload(payload, "owner/repo")["laws"], [])


if __name__ == "__main__":
    unittest.main()
