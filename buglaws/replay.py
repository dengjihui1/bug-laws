from __future__ import annotations

import json
import subprocess
import tarfile
import tempfile
import io
import time
from pathlib import Path
from typing import Any


def _archive(repository: Path, revision: str, target: Path) -> None:
    result = subprocess.run(["git", "-C", str(repository), "archive", "--format=tar", revision], check=False, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip() or f"cannot archive {revision}")
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        try:
            archive.extractall(target, filter="data")
        except TypeError:  # Python 3.11 compatibility; git archive paths are repository-relative.
            archive.extractall(target)


def replay_commit(repository: str | Path, commit: str, command: list[str], *, timeout: float = 60.0) -> dict[str, Any]:
    root = Path(repository).resolve()
    with tempfile.TemporaryDirectory(prefix="buglaws-replay-") as directory:
        base = Path(directory)
        before, after = base / "before", base / "after"
        before.mkdir(); after.mkdir()
        try:
            _archive(root, f"{commit}^", before)
            _archive(root, commit, after)
        except ValueError as exc:
            return {"commit": commit, "grade": "U", "reason": str(exc), "replay_available": False}
        results = []
        for label, cwd in (("before", before), ("after", after)):
            started = time.perf_counter()
            try:
                process = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
                results.append({"revision": label, "returncode": process.returncode, "stdout": process.stdout[-4000:], "stderr": process.stderr[-4000:], "seconds": round(time.perf_counter() - started, 4)})
            except subprocess.TimeoutExpired as exc:
                results.append({"revision": label, "returncode": None, "stdout": str(exc.stdout or "")[-4000:], "stderr": str(exc.stderr or "")[-4000:], "timed_out": True})
        before_failed = results[0]["returncode"] not in (0, None)
        after_passed = results[1]["returncode"] == 0
        grade = "A" if before_failed and after_passed else "U"
        return {"commit": commit, "grade": grade, "replay_available": True, "command": command, "results": results}


def write_replay(repository: str | Path, commit: str, command: list[str], output: str | Path, *, timeout: float = 60.0) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(replay_commit(repository, commit, command, timeout=timeout), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
