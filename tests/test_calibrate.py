from __future__ import annotations

import unittest

from buglaws.calibrate import calibrate_confidence


class CalibrationTest(unittest.TestCase):
    def test_reports_proxy_calibration_without_changing_policy(self) -> None:
        provenance = [{"sample_id": "a", "confidence": 0.9}, {"sample_id": "b", "confidence": 0.55}]
        labels = [{"sample_id": "a", "verdict": "ACCEPT"}, {"sample_id": "b", "verdict": "UNSCORABLE"}]
        result = calibrate_confidence(provenance, labels)
        self.assertEqual(result["human_validity"], "NOT ASSESSED")
        self.assertEqual(result["n"], 2)
        self.assertEqual(result["bins"]["high"]["observed_useful_rate"], 1.0)
        self.assertIn("unchanged", result["policy"])


if __name__ == "__main__":
    unittest.main()
