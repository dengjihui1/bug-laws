from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analyze import analyze_repository
from .git_history import GitError
from .render import write_report
from .sample import SamplingError, write_sample_dataset
from .audit import write_audit
from .baselines import write_baselines
from .metrics import write_metrics
from .benchmark import write_benchmark
from .enrich import enrich_report
from .calibrate import write_calibration
from .review import create_review_store, decide, export_accepted, write_review_store
from .diffing import write_diff
from .protection import write_grades
from .visual_review import render_review_html
from .replay import write_replay
from .study import write_study


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="buglaws",
        description="Recover evidence-linked candidate engineering laws from Python bug-fix history.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="scan one local Git repository")
    scan.add_argument("repository", nargs="?", default=".", help="repository path (default: current directory)")
    scan.add_argument("--output", help="report directory (default: <repository>/.buglaws-report)")
    scan.add_argument("--label", help="public repository label shown in reports instead of the local path")
    scan.add_argument("--since", help="Git-compatible date, for example '2 years ago' or '2025-01-01'")
    scan.add_argument("--limit", type=int, default=200, help="maximum fix candidates to inspect")
    scan.add_argument("--min-confidence", type=float, default=0.50, help="candidate evidence threshold, 0 to 1")
    scan.add_argument("--cache-dir", help="optional local history cache directory")
    sample = subparsers.add_parser("sample", help="build a deterministic annotation dataset from report JSON files")
    sample.add_argument("--report", action="append", required=True, help="input bug-laws.json; repeat for multiple reports")
    sample.add_argument("--output", required=True, help="output directory for reviewer/provenance/manifest files")
    sample.add_argument("--seed", type=int, required=True, help="recorded random seed")
    sample.add_argument("--total", type=int, required=True, help="maximum number of laws to sample")
    audit = subparsers.add_parser("audit", help="run a transparent automated proxy audit over reviewer JSONL")
    audit.add_argument("--input", required=True, help="reviewer JSONL input")
    audit.add_argument("--output", required=True, help="JSONL label output")
    audit.add_argument("--mode", choices=("primary", "adversarial"), default="primary")
    baseline = subparsers.add_parser("baseline", help="generate deterministic source-blind baseline forms")
    baseline.add_argument("--input", required=True, help="reviewer JSONL input")
    baseline.add_argument("--output", required=True, help="baseline output directory")
    baseline.add_argument("--seed", type=int, required=True)
    metrics = subparsers.add_parser("metrics", help="calculate validation and baseline metrics")
    metrics.add_argument("--primary", required=True)
    metrics.add_argument("--secondary", required=True)
    metrics.add_argument("--corpus", required=True)
    metrics.add_argument("--output", required=True)
    metrics.add_argument("--baseline", action="append", default=[], help="name=path JSONL; repeat for baselines")
    benchmark = subparsers.add_parser("benchmark", help="measure local scan runtime")
    benchmark.add_argument("repository", nargs="?", default=".")
    benchmark.add_argument("--output", required=True)
    benchmark.add_argument("--repeat", type=int, default=3)
    benchmark.add_argument("--limit", type=int, default=200)
    benchmark.add_argument("--since")
    benchmark.add_argument("--min-confidence", type=float, default=0.50)
    benchmark.add_argument("--cache-dir")
    enrich = subparsers.add_parser("enrich", help="optionally add cached public GitHub issue/PR evidence")
    enrich.add_argument("--input", required=True, help="input bug-laws.json")
    enrich.add_argument("--output", required=True, help="output JSON; source is not overwritten")
    enrich.add_argument("--repository", required=True, help="public owner/repository, for example pallets/flask")
    enrich.add_argument("--timeout", type=float, default=10.0)
    calibrate = subparsers.add_parser("calibrate", help="measure confidence calibration from labelled JSONL")
    calibrate.add_argument("--provenance", required=True)
    calibrate.add_argument("--labels", required=True)
    calibrate.add_argument("--output", required=True)
    review = subparsers.add_parser("review", help="create or update a separate review store")
    review.add_argument("action", choices=("init", "decide", "export", "visual"))
    review.add_argument("--input")
    review.add_argument("--output", required=True)
    review.add_argument("--store")
    review.add_argument("--law-id")
    review.add_argument("--verdict", choices=("ACCEPT", "EDIT", "REJECT", "UNSCORABLE"))
    review.add_argument("--reviewer", default="local-reviewer")
    review.add_argument("--rationale", default="")
    review.add_argument("--edited-title", default="")
    report_diff = subparsers.add_parser("diff", help="compare two versioned report JSON files")
    report_diff.add_argument("--old", required=True)
    report_diff.add_argument("--new", required=True)
    report_diff.add_argument("--output", required=True)
    protection = subparsers.add_parser("protection", help="grade static test-protection evidence")
    protection.add_argument("--input", required=True, help="reviewer JSONL")
    protection.add_argument("--output", required=True, help="grade JSONL")
    replay = subparsers.add_parser("replay", help="run an explicit before/after behavior replay in archives")
    replay.add_argument("repository")
    replay.add_argument("commit")
    replay.add_argument("--command", dest="run_command", nargs="+", required=True)
    replay.add_argument("--output", required=True)
    replay.add_argument("--timeout", type=float, default=60.0)
    study = subparsers.add_parser("study", help="run deterministic onboarding/tool proxy measurements")
    study.add_argument("--input", required=True, help="reviewer JSONL")
    study.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "sample":
        if args.total < 1:
            parser.error("--total must be positive")
        try:
            paths = write_sample_dataset(args.report, args.output, seed=args.seed, total=args.total)
        except (OSError, ValueError, json.JSONDecodeError, SamplingError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        for path in paths:
            print(path)
        return 0
    if args.command == "audit":
        try:
            print(write_audit(args.input, args.output, mode=args.mode))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "baseline":
        try:
            paths = write_baselines(args.input, args.output, seed=args.seed)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        for path in paths:
            print(path)
        return 0
    if args.command == "metrics":
        try:
            baseline_paths = {}
            for value in args.baseline:
                name, separator, path = value.partition("=")
                if not separator or not name or not path:
                    raise ValueError("--baseline must use name=path")
                baseline_paths[name] = path
            print(write_metrics(args.primary, args.secondary, args.corpus, args.output, baseline_paths))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "benchmark":
        if args.repeat < 1 or args.limit < 1 or not 0 <= args.min_confidence <= 1:
            parser.error("benchmark repeat/limit must be positive and min-confidence must be between 0 and 1")
        try:
            print(write_benchmark(args.output, repository=args.repository, repeat=args.repeat, limit=args.limit, since=args.since, min_confidence=args.min_confidence, cache_dir=args.cache_dir))
        except (OSError, ValueError, GitError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "enrich":
        if args.timeout <= 0:
            parser.error("enrich timeout must be positive")
        try:
            print(enrich_report(args.input, args.output, args.repository, timeout=args.timeout))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "calibrate":
        try:
            print(write_calibration(args.provenance, args.labels, args.output))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "review":
        try:
            if args.action == "init":
                if not args.input:
                    parser.error("review init requires --input")
                print(write_review_store(create_review_store(args.input), args.output))
            elif args.action == "decide":
                if not args.store or not args.law_id or not args.verdict:
                    parser.error("review decide requires --store, --law-id, and --verdict")
                print(decide(args.store, args.law_id, args.verdict, reviewer=args.reviewer, rationale=args.rationale, edited_title=args.edited_title))
            else:
                if args.action == "visual":
                    if not args.input:
                        parser.error("review visual requires --input store")
                    print(render_review_html(args.input, args.output))
                elif not args.store:
                    parser.error("review export requires --store")
                else:
                    print(export_accepted(args.store, args.output))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "diff":
        try:
            print(write_diff(args.old, args.new, args.output))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "protection":
        try:
            print(write_grades(args.input, args.output))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "replay":
        if args.timeout <= 0:
            parser.error("replay timeout must be positive")
        try:
            print(write_replay(args.repository, args.commit, args.run_command, args.output, timeout=args.timeout))
        except (OSError, ValueError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "study":
        try:
            print(write_study(args.input, args.output))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"buglaws: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command != "scan":
        parser.error("unknown command")
    if args.limit < 1:
        parser.error("--limit must be positive")
    if not 0 <= args.min_confidence <= 1:
        parser.error("--min-confidence must be between 0 and 1")
    repository = Path(args.repository).resolve()
    output = Path(args.output).resolve() if args.output else repository / ".buglaws-report"
    try:
        report = analyze_repository(
            repository,
            since=args.since,
            limit=args.limit,
            min_confidence=args.min_confidence,
            cache_dir=Path(args.cache_dir).resolve() if args.cache_dir else None,
        )
        if args.label:
            report.repository = args.label
        paths = write_report(report, output)
    except (GitError, OSError) as exc:
        print(f"buglaws: {exc}", file=sys.stderr)
        return 2
    print(
        f"Recovered {len(report.laws)} candidate laws from {report.candidate_commits} fix commits; "
        f"found {report.fixes_without_tests} fixes without test changes."
    )
    for path in paths:
        print(path)
    return 0
