from __future__ import annotations

import unittest

from buglaws.study import run_onboarding_proxy


class StudyTest(unittest.TestCase):
    def test_proxy_is_explicitly_not_a_human_study(self) -> None:
        result = run_onboarding_proxy([{"title": "Redirect behavior", "evidence": [{"subject": "fix redirect", "source_files": ["sessions.py"]}]}], ["redirect"])
        self.assertEqual(result["human_validity"], "NOT ASSESSED")
        self.assertEqual(result["queries"][0]["delta"], 0)


if __name__ == "__main__":
    unittest.main()
