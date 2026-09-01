from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .git_history import is_fix_candidate, read_commit_details, read_history, repository_root
from .models import CommitEvidence, FixUnit, Law, Report, StructuredLaw


PREFIX_PATTERN = re.compile(
    r"^(?:(?:fix|bugfix|hotfix|regression|correct)(?:\([^)]*\))?(?:\s*[:\-]\s*|\s+)|revert\s+)",
    re.IGNORECASE,
)
ISSUE_SUFFIX_PATTERN = re.compile(r"\s*(?:\(|\[)?#\d+(?:\)|\])?\s*$")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "be", "behavior", "by", "correct", "fix", "for", "from", "in", "is", "it",
    "must", "of", "on", "path", "required", "system", "the", "to", "when", "with", "without",
}


def _words(value: str) -> list[str]:
    words = TOKEN_PATTERN.findall(value.lower())
    normalized: list[str] = []
    for word in words:
        if word in STOPWORDS:
            continue
        if len(word) > 5 and word.endswith("ing"):
            word = word[:-3]
        elif len(word) > 4 and word.endswith("ed"):
            word = word[:-2]
        elif len(word) > 4 and word.endswith("s"):
            word = word[:-1]
        normalized.append(word)
    return normalized


def _humanize_test_name(name: str) -> str:
    phrase = name.removeprefix("test_").replace("_", " ")
    phrase = re.sub(r"^fix issue\b", "fix operation", phrase)
    phrase = re.sub(r"^fix command\b", "fix command", phrase)
    verbs = {
        "includes": "include", "include": "include",
        "contains": "contain", "contain": "contain",
        "rejects": "reject", "reject": "reject",
        "requires": "require", "require": "require",
        "prevents": "prevent", "prevent": "prevent",
        "preserves": "preserve", "preserve": "preserve",
        "handles": "handle", "handle": "handle",
        "returns": "return", "return": "return",
        "uses": "use", "use": "use",
        "closes": "close", "close": "close",
        "keeps": "keep", "keep": "keep",
        "detaches": "detach", "detach": "detach",
        "allows": "allow", "allow": "allow",
        "blocks": "block", "block": "block",
    }
    phrase = re.sub(r"\bdoes not\b", "must not", phrase, count=1)
    if "must " not in phrase:
        verb_pattern = r"\b(" + "|".join(sorted(verbs, key=len, reverse=True)) + r")\b"
        phrase = re.sub(verb_pattern, lambda match: f"must {verbs[match.group(1)]}", phrase, count=1)
    return phrase[:1].upper() + phrase[1:]


def infer_title(subject: str, signals: list[str]) -> str:
    test_names = [signal.removeprefix("test:") for signal in signals if signal.startswith("test:")]
    if test_names:
        return _humanize_test_name(test_names[0])

    cleaned = PREFIX_PATTERN.sub("", subject.strip())
    cleaned = ISSUE_SUFFIX_PATTERN.sub("", cleaned).strip(' "\'')
    lowered = cleaned.lower()
    transforms = (
        ("prevent ", lambda rest: f"{rest[:1].upper() + rest[1:]} must be prevented"),
        ("avoid ", lambda rest: f"{rest[:1].upper() + rest[1:]} must be avoided"),
        ("handle ", lambda rest: f"System must handle {rest}"),
        ("ensure ", lambda rest: f"System must ensure {rest}"),
        ("preserve ", lambda rest: f"System must preserve {rest}"),
        ("reject ", lambda rest: f"System must reject {rest}"),
        ("include ", lambda rest: f"System must include {rest}"),
    )
    for prefix, transform in transforms:
        if lowered.startswith(prefix):
            return transform(cleaned[len(prefix):]).rstrip(".")
    if not cleaned:
        return "Bug fix behavior must remain preserved"
    return f"Required behavior: {cleaned[:1].lower() + cleaned[1:]}".rstrip(".")


def confidence_for(details_signals: list[str], test_files: list[str], issue_refs: list[str]) -> float:
    value = 0.45
    if test_files:
        value += 0.18
    if any(signal.startswith("test:") for signal in details_signals):
        value += 0.17
    if any(signal.startswith("guard:") for signal in details_signals):
        value += 0.10
    if issue_refs:
        value += 0.05
    return min(round(value, 2), 0.95)


def _structured_law(title: str, evidence: list[CommitEvidence], affected_files: list[str]) -> StructuredLaw:
    """Create a conservative, provenance-indexed structure from a candidate.

    This is not a second inference engine. It exposes what the existing title
    heuristic already implies and marks semantic prose as provisional. A later
    reviewer/model can replace individual fields while retaining the commit
    anchors in ``field_evidence``.
    """
    lowered = title.lower().rstrip(".")
    if "must not" in lowered:
        constraint = "must_not"
    elif " must " in f" {lowered} ":
        constraint = "must"
    else:
        constraint = "preserve"

    subject = re.sub(r"^system must(?:\s+not)?\s+", "", title, flags=re.IGNORECASE)
    subject = re.sub(r"\s+must(?: not)?\s+(?:be\s+)?(?:preserved|prevented|avoided)\.?$", "", subject, flags=re.IGNORECASE)
    subject = re.sub(r"^required behavior:\s*", "", subject, flags=re.IGNORECASE).strip(" .")
    if not subject:
        subject = title.strip(" .")

    guards = sorted({signal.removeprefix("guard:") for item in evidence for signal in item.signals if signal.startswith("guard:")})
    condition = "; ".join(guards) if guards else None
    commit_ids = [item.commit for item in evidence]
    failure = None
    field_evidence = {
        "subject": commit_ids,
        "constraint": commit_ids,
        "scope": commit_ids,
        "evidence_strength": commit_ids,
    }
    provisional = ["subject", "constraint"]
    if condition is not None:
        field_evidence["condition"] = commit_ids
        provisional.append("condition")
    if failure is not None:
        field_evidence["failure"] = commit_ids
        provisional.append("failure")
    if len(evidence) > 1:
        evidence_strength = "recurrent"
    elif any(item.test_files or any(signal.startswith("test:") for signal in item.signals) for item in evidence):
        evidence_strength = "direct_test"
    elif any(signal.startswith("guard:") for item in evidence for signal in item.signals):
        evidence_strength = "direct_guard"
    else:
        evidence_strength = "single_commit"
    return StructuredLaw(
        subject=subject,
        constraint=constraint,
        condition=condition,
        failure=failure,
        scope=affected_files,
        evidence_strength=evidence_strength,
        field_evidence=field_evidence,
        provisional_fields=provisional,
    )


def _similarity(left: CommitEvidence, right: CommitEvidence) -> float:
    left_words = set(_words(left.candidate_title))
    right_words = set(_words(right.candidate_title))
    if not left_words or not right_words:
        return 0.0
    score = len(left_words & right_words) / len(left_words | right_words)
    left_modules = {Path(path).stem for path in left.source_files}
    right_modules = {Path(path).stem for path in right.source_files}
    if left_modules & right_modules:
        score += 0.10
    left_symbols = set(left.changed_symbols)
    right_symbols = set(right.changed_symbols)
    if left_symbols & right_symbols:
        score += 0.15
    return min(score, 1.0)


def _cluster(evidence: list[CommitEvidence], threshold: float = 0.50) -> list[list[CommitEvidence]]:
    """Cluster with deterministic complete-link agglomeration.

    A candidate can join a cluster only when it is similar to every member.
    The merge score and stable commit-key tie break remove the old
    confidence/order dependence and make the resulting merge explainable.
    """
    clusters: list[list[CommitEvidence]] = [[item] for item in sorted(evidence, key=lambda value: value.commit)]
    while len(clusters) > 1:
        best: tuple[float, tuple[str, ...], int, int] | None = None
        for left_index, left in enumerate(clusters):
            for right_index in range(left_index + 1, len(clusters)):
                right = clusters[right_index]
                score = min(_similarity(a, b) for a in left for b in right)
                key = tuple(sorted([item.commit for item in left + right]))
                candidate = (score, key, left_index, right_index)
                if score >= threshold and (best is None or (score, tuple(reversed(key))) > (best[0], tuple(reversed(best[1])))):
                    best = candidate
        if best is None:
            break
        _, _, left_index, right_index = best
        merged = sorted(clusters[left_index] + clusters[right_index], key=lambda value: value.commit)
        clusters = [cluster for index, cluster in enumerate(clusters) if index not in {left_index, right_index}]
        clusters.append(merged)
        clusters.sort(key=lambda cluster: tuple(item.commit for item in cluster))
    return clusters


def _cluster_explanation(cluster: list[CommitEvidence], threshold: float = 0.50) -> dict[str, object]:
    pairs = [_similarity(left, right) for index, left in enumerate(cluster) for right in cluster[index + 1 :]]
    modules = [set(Path(path).stem for path in item.source_files) for item in cluster]
    symbols = [set(item.changed_symbols) for item in cluster]
    shared_modules = sorted(set.intersection(*modules)) if modules else []
    shared_symbols = sorted(set.intersection(*symbols)) if symbols else []
    return {
        "method": "complete_link_agglomerative",
        "threshold": threshold,
        "member_commits": [item.commit for item in sorted(cluster, key=lambda value: value.commit)],
        "pairwise_min_similarity": round(min(pairs), 3) if pairs else 1.0,
        "shared_source_modules": shared_modules,
        "shared_symbols": shared_symbols,
    }


def analyze_repository(
    repository: str | Path,
    *,
    since: str | None = None,
    limit: int = 200,
    min_confidence: float = 0.50,
    cache_dir: Path | None = None,
) -> Report:
    root = repository_root(Path(repository))
    history = read_history(root, since, cache_dir)
    candidates = [commit for commit in history if is_fix_candidate(commit)][:limit]
    evidence: list[CommitEvidence] = []
    for commit in candidates:
        details = read_commit_details(root, commit)
        if not details.source_files:
            continue
        title = infer_title(commit.subject, details.signals)
        confidence = confidence_for(details.signals, details.test_files, details.issue_refs)
        if confidence < min_confidence:
            continue
        evidence.append(
            CommitEvidence(
                commit=commit.commit,
                date=commit.date,
                subject=commit.subject,
                issue_refs=details.issue_refs,
                source_files=details.source_files,
                test_files=details.test_files,
                signals=details.signals,
                candidate_title=title,
                confidence=confidence,
                changed_symbols=details.changed_symbols,
                units=[FixUnit(**unit) for unit in details.fix_units],
            )
        )

    clusters = _cluster(evidence)
    clusters.sort(
        key=lambda cluster: (len(cluster), max(item.confidence for item in cluster)),
        reverse=True,
    )
    laws: list[Law] = []
    for index, cluster in enumerate(clusters, start=1):
        representative = max(cluster, key=lambda item: (item.confidence, item.commit))
        affected_files = sorted({path for item in cluster for path in item.source_files})
        ordered_evidence = sorted(cluster, key=lambda item: item.date)
        laws.append(
            Law(
                law_id=f"LAW-{index:03d}",
                title=representative.candidate_title,
                confidence=round(sum(item.confidence for item in cluster) / len(cluster), 2),
                evidence=ordered_evidence,
                affected_files=affected_files,
                structured=_structured_law(representative.candidate_title, ordered_evidence, affected_files),
                cluster_explanation=_cluster_explanation(cluster),
            )
        )

    return Report(
        repository=str(root),
        generated_at=datetime.now(timezone.utc).isoformat(),
        since=since,
        commits_seen=len(history),
        candidate_commits=len(candidates),
        laws=laws,
    )
