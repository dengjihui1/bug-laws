from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

from .analyze import analyze_repository


def run_benchmark(
    repository: str | Path,
    *,
    repeat: int = 3,
    limit: int = 200,
    since: str | None = None,
    min_confidence: float = 0.50,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    if repeat < 1:
        raise ValueError("repeat must be positive")
    cache = Path(cache_dir) if cache_dir else None
    timings: list[float] = []
    law_counts: list[int] = []
    for _ in range(repeat):
        started = time.perf_counter()
        report = analyze_repository(repository, since=since, limit=limit, min_confidence=min_confidence, cache_dir=cache)
        timings.append(time.perf_counter() - started)
        law_counts.append(len(report.laws))
    return {
        "benchmark_version": "benchmark-v1",
        "repository": str(repository),
        "repeat": repeat,
        "limit": limit,
        "since": since,
        "min_confidence": min_confidence,
        "cache_enabled": cache is not None,
        "seconds": {"runs": [round(value, 6) for value in timings], "median": round(statistics.median(timings), 6), "min": round(min(timings), 6), "max": round(max(timings), 6)},
        "law_counts": law_counts,
    }


def write_benchmark(output: str | Path, **kwargs: Any) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(run_benchmark(**kwargs), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
