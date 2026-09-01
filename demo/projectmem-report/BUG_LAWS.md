# Bug Laws

> Candidate engineering laws recovered from `github.com/riponcm/projectmem`.
> Every law is evidence-linked and requires human review before becoming project policy.

## Scan summary

- Commits seen: `21`
- Fix candidates inspected: `4`
- Candidate laws: `3`
- Repeated laws: `1`
- Fixes without test changes: `0`

## LAW-001 — Fix operation must close target without clearing newer active issue

- Confidence: `93%` — candidate law, human review required
- Recurrence: `2` fix commit(s)
- Test protection: `2` protected / `0` unprotected
- Affected files: `src/projectmem/cli.py`, `src/projectmem/commands/fix.py`, `src/projectmem/mcp_server.py`

### Evidence

- `b5e7edd385` (2026-06-19): fix: allow fixing a specific issue
  - Source: `src/projectmem/cli.py`, `src/projectmem/commands/fix.py`, `src/projectmem/mcp_server.py`
  - Tests: `tests/test_log.py`
  - Signals: `guard:if issue_id is None:`, `guard:if not cleaned:`, `guard:if cleaned.isdigit():`, `guard:if requested_issue_id is not None:`
- `f83f827d0c` (2026-06-19): fix: allow fixing a specific issue (#2)
  - Source: `src/projectmem/cli.py`, `src/projectmem/commands/fix.py`, `src/projectmem/mcp_server.py`
  - Tests: `tests/test_log.py`
  - Signals: `guard:if issue_id is None:`, `guard:if not cleaned:`, `guard:if cleaned.isdigit():`, `guard:if requested_issue_id is not None:`

## LAW-002 — Brief console helpers are cp1252 safe

- Confidence: `95%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/projectmem/commands/brief.py`, `src/projectmem/commands/precheck.py`

### Evidence

- `ac7881a8e5` (2026-06-19): fix: make console output encoding-safe (#5)
  - Source: `src/projectmem/commands/brief.py`, `src/projectmem/commands/precheck.py`
  - Tests: `tests/test_v014_features.py`
  - Signals: `guard:except UnicodeEncodeError:`, `guard:if "utf" in encoding:`, `guard:except UnicodeEncodeError:`, `guard:if "utf" in encoding:`

## LAW-003 — Git helpers must detach stdin and keep timeouts

- Confidence: `95%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/projectmem/commands/context.py`, `src/projectmem/commands/precheck.py`, `src/projectmem/staleness.py`, `src/projectmem/storage.py`

### Evidence

- `d259d0b852` (2026-06-19): fix: harden MCP git helpers against stdio hangs (#4)
  - Source: `src/projectmem/commands/context.py`, `src/projectmem/commands/precheck.py`, `src/projectmem/staleness.py`, `src/projectmem/storage.py`
  - Tests: `tests/test_hooks_path.py`, `tests/test_mcp_server.py`, `tests/test_v014_features.py`
  - Signals: `guard:except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):`, `guard:if not bash:`, `guard:except (OSError, subprocess.TimeoutExpired) as exc:`, `guard:if result.returncode != 0:`
