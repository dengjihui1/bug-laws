from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from buglaws.replay import replay_commit
from buglaws.visual_review import render_review_html


class VisualReplayTest(unittest.TestCase):
    def test_visual_review_contains_evidence_and_download_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = root / "store.json"
            store.write_text(json.dumps({"entries": [{"law_id": "LAW-1", "original_title": "Keep x", "evidence": [{"commit": "abc", "subject": "fix", "source_files": ["x.py"]}]}]}), encoding="utf-8")
            output = root / "review.html"
            render_review_html(store, output)
            text = output.read_text(encoding="utf-8")
            self.assertIn("Download decisions JSON", text)
            self.assertIn("abc", text)

    def test_replay_grades_before_failure_after_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.com"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
            (root / "state.txt").write_text("bad\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "initial"], check=True)
            (root / "state.txt").write_text("good\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "fix"], check=True)
            commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            result = replay_commit(root, commit, [sys.executable, "-c", "import pathlib,sys; sys.exit(0 if pathlib.Path('state.txt').read_text().strip() == 'good' else 1)"])
            self.assertEqual(result["grade"], "A")


if __name__ == "__main__":
    unittest.main()
