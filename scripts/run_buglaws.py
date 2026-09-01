"""Run the bundled Bug Laws CLI without requiring a global installation.

This is the Skill-facing launcher. It deliberately delegates all behavior to
the tested ``buglaws.cli`` entrypoint so the Skill and the Python package cannot
drift into separate implementations.
"""

from __future__ import annotations

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from buglaws.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
