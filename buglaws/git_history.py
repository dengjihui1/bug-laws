from __future__ import annotations

import re
import subprocess
import ast
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


FIX_PATTERN = re.compile(
    r"^(?:(?:fix(?:e[ds])?|bug(?:fix)?|hotfix|revert(?:ed|s|ing)?|correct(?:ed|s|ion)?|prevent(?:ed|s|ing)?)(?:\([^)]*\))?\b|.*\bregression\b)",
    re.IGNORECASE,
)
TEST_PATH_PATTERN = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]+\.py$|_test\.py$", re.IGNORECASE)
ISSUE_PATTERN = re.compile(r"(?<![\w])#(\d+)\b")
TEST_FUNCTION_PATTERN = re.compile(r"^\+\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)")
GUARD_PATTERN = re.compile(r"^\+\s*(if\b|elif\b|raise\b|assert\b|except\b|return\b.*\bif\b)")


@dataclass(slots=True)
class RawCommit:
    commit: str
    date: str
    subject: str


@dataclass(slots=True)
class CommitDetails:
    source_files: list[str]
    test_files: list[str]
    signals: list[str]
    issue_refs: list[str]
    changed_symbols: list[str]
    fix_units: list[dict[str, object]]


class GitError(RuntimeError):
    pass


def _run_git(repository: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise GitError(message)
    return result.stdout


def repository_root(repository: Path) -> Path:
    output = _run_git(repository.resolve(), ["rev-parse", "--show-toplevel"]).strip()
    return Path(output).resolve()


def _history_cache_path(repository: Path, since: str | None, cache_dir: Path) -> Path:
    head = _run_git(repository, ["rev-parse", "HEAD"]).strip()
    cache_key = hashlib.sha256(f"history-v1\n{repository.resolve()}\n{head}\n{since or ''}".encode()).hexdigest()[:32]
    return cache_dir / f"history-{cache_key}.json"


def read_history(repository: Path, since: str | None = None, cache_dir: Path | None = None) -> list[RawCommit]:
    cache_path: Path | None = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = _history_cache_path(repository, since, cache_dir)
        if cache_path.exists():
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
                return [RawCommit(**record) for record in payload["records"]]
            except (OSError, KeyError, TypeError, json.JSONDecodeError):
                cache_path.unlink(missing_ok=True)
    args = ["log", "--no-merges", "--format=%H%x1f%aI%x1f%s%x1e"]
    if since:
        args.append(f"--since={since}")
    output = _run_git(repository, args)
    commits: list[RawCommit] = []
    for record in output.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        fields = record.split("\x1f", 2)
        if len(fields) == 3:
            commits.append(RawCommit(*fields))
    if cache_path is not None:
        cache_path.write_text(
            json.dumps({"cache_version": "history-v1", "records": [asdict(commit) for commit in commits]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return commits


def is_fix_candidate(commit: RawCommit) -> bool:
    return bool(FIX_PATTERN.search(commit.subject))


def read_commit_details(repository: Path, commit: RawCommit, patch_limit: int = 80_000) -> CommitDetails:
    names = _run_git(
        repository,
        ["diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit.commit],
    )
    python_files = sorted({line.strip().replace("\\", "/") for line in names.splitlines() if line.strip().endswith(".py")})
    test_files = [path for path in python_files if TEST_PATH_PATTERN.search(path)]
    source_files = [path for path in python_files if path not in test_files]
    if not source_files:
        return CommitDetails([], test_files, [], ISSUE_PATTERN.findall(commit.subject), [], [])

    patch = _run_git(
        repository,
        ["show", "--format=", "--no-ext-diff", "--unified=1", commit.commit, "--", "*.py"],
    )[:patch_limit]
    signals: list[str] = []
    for raw_line in patch.splitlines():
        line = raw_line.strip()
        test_match = TEST_FUNCTION_PATTERN.match(line)
        if test_match:
            signals.append(f"test:{test_match.group(1)}")
        elif GUARD_PATTERN.match(line):
            signals.append(f"guard:{line[1:].strip()[:180]}")
        if len(signals) >= 12:
            break
    changed_symbols = _changed_python_symbols(repository, commit.commit, python_files)
    fix_units = [
        {
            "unit_id": f"{commit.commit[:12]}:{path}",
            "source_files": [path],
            "test_files": test_files,
            "signals": signals,
            "changed_symbols": [symbol for symbol in changed_symbols if symbol.startswith(f"{path}::")],
        }
        for path in source_files
    ]
    return CommitDetails(
        source_files=source_files,
        test_files=test_files,
        signals=signals,
        issue_refs=ISSUE_PATTERN.findall(commit.subject),
        changed_symbols=changed_symbols,
        fix_units=fix_units,
    )


HUNK_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _changed_python_ranges(patch: str) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = {}
    current: str | None = None
    for raw_line in patch.splitlines():
        if raw_line.startswith("+++ b/"):
            current = raw_line[6:]
            ranges.setdefault(current, [])
            continue
        match = HUNK_PATTERN.match(raw_line)
        if match and current is not None:
            start = int(match.group(1))
            count = int(match.group(2) or "1")
            ranges[current].append((start, start + max(count, 1) - 1))
    return ranges


def _node_symbols(tree: ast.AST, path: str) -> list[tuple[str, int, int]]:
    found: list[tuple[str, int, int]] = []

    def walk(node: ast.AST, parents: list[str]) -> None:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            name = "::".join([*parents, node.name])
            start = getattr(node, "lineno", 0)
            end = getattr(node, "end_lineno", start)
            found.append((f"{path}::{name}", start, end))
            parents = [*parents, node.name]
        for child in ast.iter_child_nodes(node):
            walk(child, parents)

    walk(tree, [])
    return found


def _changed_python_symbols(repository: Path, commit: str, python_files: list[str]) -> list[str]:
    """Return AST symbols whose post-commit or pre-commit span was changed.

    This is static evidence only: it identifies the symbol containing a diff
    hunk, without claiming that the symbol explains the bug or that a test
    covers it.
    """
    patch = _run_git(repository, ["show", "--format=", "--no-ext-diff", "--unified=0", commit, "--", "*.py"])
    ranges = _changed_python_ranges(patch)
    symbols: set[str] = set()
    for path in python_files:
        path_ranges = ranges.get(path, [])
        if not path_ranges:
            continue
        for revision in (commit, f"{commit}^"):
            try:
                content = _run_git(repository, ["show", f"{revision}:{path}"])
                tree = ast.parse(content, filename=path)
            except (GitError, SyntaxError):
                continue
            node_lines = _node_symbols(tree, path)
            for name, start, end in node_lines:
                if any(start <= changed_end and end >= changed_start for changed_start, changed_end in path_ranges):
                    symbols.add(name)
    return sorted(symbols)
