from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .schema import REPORT_SCHEMA_VERSION


@dataclass(slots=True)
class FixUnit:
    unit_id: str
    source_files: list[str]
    test_files: list[str]
    signals: list[str]
    changed_symbols: list[str]


@dataclass(slots=True)
class CommitEvidence:
    commit: str
    date: str
    subject: str
    issue_refs: list[str]
    source_files: list[str]
    test_files: list[str]
    signals: list[str]
    candidate_title: str
    confidence: float
    changed_symbols: list[str] = field(default_factory=list)
    units: list[FixUnit] = field(default_factory=list)

    @property
    def has_regression_test(self) -> bool:
        return bool(self.test_files or any(signal.startswith("test:") for signal in self.signals))


@dataclass(slots=True)
class StructuredLaw:
    """Evidence-indexed structure behind a rendered candidate title.

    The values are deliberately conservative: semantic fields inferred from
    prose are marked provisional and point back to the commit hashes that
    supplied the evidence. This makes it possible for later review tooling to
    edit a field without losing the original candidate or its provenance.
    """

    subject: str
    constraint: str
    condition: str | None
    failure: str | None
    scope: list[str]
    evidence_strength: str
    field_evidence: dict[str, list[str]] = field(default_factory=dict)
    provisional_fields: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Law:
    law_id: str
    title: str
    confidence: float
    evidence: list[CommitEvidence] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    structured: StructuredLaw | None = None
    cluster_explanation: dict[str, Any] = field(default_factory=dict)

    @property
    def recurrence(self) -> int:
        return len(self.evidence)

    @property
    def protected_fixes(self) -> int:
        return sum(item.has_regression_test for item in self.evidence)

    @property
    def unprotected_fixes(self) -> int:
        return self.recurrence - self.protected_fixes


@dataclass(slots=True)
class Report:
    repository: str
    generated_at: str
    since: str | None
    commits_seen: int
    candidate_commits: int
    laws: list[Law]
    schema_version: str = REPORT_SCHEMA_VERSION

    @property
    def repeated_laws(self) -> int:
        return sum(law.recurrence > 1 for law in self.laws)

    @property
    def fixes_without_tests(self) -> int:
        return sum(law.unprotected_fixes for law in self.laws)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["summary"] = {
            "law_count": len(self.laws),
            "repeated_laws": self.repeated_laws,
            "fixes_without_tests": self.fixes_without_tests,
        }
        for law, law_payload in zip(self.laws, payload["laws"], strict=True):
            law_payload["recurrence"] = law.recurrence
            law_payload["protected_fixes"] = law.protected_fixes
            law_payload["unprotected_fixes"] = law.unprotected_fixes
        return payload
