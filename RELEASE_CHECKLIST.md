# Local release checklist

This checklist is intentionally local. No step publishes to PyPI or creates
external GitHub resources.

1. Run `python -m unittest discover -s tests -v`.
2. Run `git diff --check`.
3. Run `python scripts/verify_release.py` in a clean temporary venv.
4. Inspect report JSON/Markdown/HTML for local paths, secrets, and unsupported
   claims before sharing.
5. Confirm extracted laws are labelled candidates and validation metrics are
   labelled automated/public-evidence proxy.
6. Record the commit, commands, and remaining risks in `HANDOFF_LOG.md`.
