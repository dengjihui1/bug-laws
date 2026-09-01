from __future__ import annotations

import unittest

from buglaws.protection import grade_evidence


class ProtectionTest(unittest.TestCase):
    def test_static_grade_is_conservative(self) -> None:
        self.assertEqual(grade_evidence({"test_files": ["tests/test_api.py"], "changed_symbols": ["api.py::parse"], "signals": ["test:test_parse"]})[0], "B")
        self.assertEqual(grade_evidence({"test_files": ["tests/test_api.py"], "changed_symbols": ["api.py::parse"], "signals": ["test:test_other"]})[0], "C")
        self.assertEqual(grade_evidence({"test_files": [], "changed_symbols": [], "signals": []})[0], "U")


if __name__ == "__main__":
    unittest.main()
