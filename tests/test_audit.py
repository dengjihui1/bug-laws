from __future__ import annotations

import unittest

from buglaws.audit import audit_item, audit_items


def item(title: str, *, tests: bool = True, signals: list[str] | None = None) -> dict:
    return {
        "sample_id": "S-1",
        "repository": "public/example",
        "law_id": "LAW-1",
        "title": title,
        "evidence": [
            {
                "source_files": ["src/app.py"],
                "test_files": ["tests/test_app.py"] if tests else [],
                "issue_refs": [],
                "signals": signals if signals is not None else ["test:test_app", "guard:assert result == 1"],
                "subject": "fix behavior",
            }
        ],
    }


class AuditTest(unittest.TestCase):
    def test_documentation_change_is_rejected(self) -> None:
        result = audit_item(item("Required behavior: fixed typo in documentation", signals=["guard:if x:", "guard:if y:"]), mode="primary")
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("NOT_A_BUG_FIX", result["error_tags"])

    def test_missing_behavior_is_unscorable(self) -> None:
        result = audit_item(item("The system handles behavior", signals=["guard:if x:"]), mode="adversarial")
        self.assertEqual(result["verdict"], "UNSCORABLE")
        self.assertEqual(result["protection"], "CHANGED_BUT_UNLINKED")

    def test_fragmentary_title_is_edit_with_protection(self) -> None:
        result = audit_item(item("Json decode compatibility"), mode="primary")
        self.assertEqual(result["verdict"], "EDIT")
        self.assertTrue(result["edited_title"])
        self.assertEqual(result["protection"], "PROTECTED")

    def test_output_order_is_stable(self) -> None:
        first = audit_items([item("A"), dict(item("B"), sample_id="S-0")])
        second = audit_items([dict(item("B"), sample_id="S-0"), item("A")])
        self.assertEqual([x["sample_id"] for x in first], [x["sample_id"] for x in second])

    def test_form_id_is_used_for_blinded_baseline_forms(self) -> None:
        baseline = item("Cache key behavior")
        baseline.pop("sample_id")
        baseline["form_id"] = "F-1"
        self.assertEqual(audit_item(baseline, mode="primary")["sample_id"], "F-1")


if __name__ == "__main__":
    unittest.main()
