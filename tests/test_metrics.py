from __future__ import annotations

import unittest

from buglaws.metrics import calculate_metrics


def label(sample_id: str, verdict: str, *, grounding: int = 2) -> dict:
    return {
        "sample_id": sample_id,
        "verdict": verdict,
        "grounding": grounding,
        "abstraction": 2,
        "scope": 2,
        "usefulness": 2 if verdict in {"ACCEPT", "EDIT"} else 0,
        "title_quality": 2,
        "protection": "PROTECTED",
        "error_tags": [],
    }


class MetricsTest(unittest.TestCase):
    def test_rates_and_wilson_interval_use_scorable_denominator(self) -> None:
        primary = [label("S-1", "ACCEPT"), label("S-2", "REJECT", grounding=0), label("S-3", "UNSCORABLE", grounding=1)]
        corpus = [
            {"sample_id": "S-1", "repository": "repo", "confidence_bucket": "high", "protected_fixes": 1},
            {"sample_id": "S-2", "repository": "repo", "confidence_bucket": "high", "protected_fixes": 1},
            {"sample_id": "S-3", "repository": "repo", "confidence_bucket": "near_threshold", "protected_fixes": 0},
        ]
        result = calculate_metrics(primary, primary, corpus)
        self.assertEqual(result["primary"]["useful_rate"]["successes"], 1)
        self.assertEqual(result["primary"]["useful_rate"]["scorable"], 2)
        self.assertEqual(result["primary"]["severe_false_law_rate"]["successes"], 1)
        self.assertEqual(result["model_pass_agreement"]["kappa"], 1.0)

    def test_baseline_delta_and_group_breakdown_are_present(self) -> None:
        corpus = [{"sample_id": "S-1", "repository": "repo-a", "confidence_bucket": "high", "protected_fixes": 1}]
        result = calculate_metrics([label("S-1", "ACCEPT")], [label("S-1", "EDIT")], corpus, {"subject": [label("F-1", "REJECT")]})
        self.assertEqual(result["baselines"]["subject"]["usefulness_delta_vs_primary"], 1.0)
        self.assertIn("repository:repo-a", result["by_group"])
        self.assertEqual(result["human_validity"], "NOT ASSESSED")


if __name__ == "__main__":
    unittest.main()
