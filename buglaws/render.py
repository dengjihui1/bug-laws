from __future__ import annotations

import html
import json
from pathlib import Path

from .models import Law, Report
from .schema import validate_report_payload


def write_report(report: Report, output_directory: str | Path) -> list[Path]:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "bug-laws.json"
    markdown_path = output / "BUG_LAWS.md"
    html_path = output / "index.html"
    payload = report.to_dict()
    validate_report_payload(payload)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    return [markdown_path, json_path, html_path]


def _law_markdown(law: Law) -> list[str]:
    lines = [
        f"## {law.law_id} — {law.title}",
        "",
        f"- Confidence: `{law.confidence:.0%}` — candidate law, human review required",
        f"- Recurrence: `{law.recurrence}` fix commit(s)",
        f"- Test protection: `{law.protected_fixes}` protected / `{law.unprotected_fixes}` unprotected",
        f"- Affected files: {', '.join(f'`{path}`' for path in law.affected_files)}",
        "",
        "### Structured candidate",
        "",
        f"- Subject: `{law.structured.subject}`" if law.structured else "- Structured candidate: unavailable",
        f"- Constraint: `{law.structured.constraint}`" if law.structured else "",
        f"- Condition: `{law.structured.condition}`" if law.structured and law.structured.condition else "- Condition: `unspecified`",
        f"- Evidence strength: `{law.structured.evidence_strength}`; provisional fields: {', '.join(f'`{field}`' for field in law.structured.provisional_fields) or '`none`'}" if law.structured else "",
        f"- Cluster: `{law.cluster_explanation.get('method', 'unknown')}`; minimum pairwise similarity: `{law.cluster_explanation.get('pairwise_min_similarity', 'unknown')}`" if law.cluster_explanation else "",
        "",
        "### Evidence",
        "",
    ]
    for item in law.evidence:
        lines.extend(
            [
                f"- `{item.commit[:10]}` ({item.date[:10]}): {item.subject}",
                f"  - Source: {', '.join(f'`{path}`' for path in item.source_files)}",
                f"  - Tests: {', '.join(f'`{path}`' for path in item.test_files) if item.test_files else '**missing in this fix**'}",
            ]
        )
        if item.changed_symbols:
            lines.append(f"  - Changed symbols: {', '.join(f'`{symbol}`' for symbol in item.changed_symbols)}")
        if item.units:
            lines.append(f"  - Evidence units: {', '.join(f'`{unit.unit_id}`' for unit in item.units)}")
        if item.signals:
            lines.append(f"  - Signals: {', '.join(f'`{signal}`' for signal in item.signals[:4])}")
    lines.append("")
    return lines


def render_markdown(report: Report) -> str:
    lines = [
        "# Bug Laws",
        "",
        f"> Candidate engineering laws recovered from `{report.repository}`.",
        "> Every law is evidence-linked and requires human review before becoming project policy.",
        "",
        "## Scan summary",
        "",
        f"- Commits seen: `{report.commits_seen}`",
        f"- Fix candidates inspected: `{report.candidate_commits}`",
        f"- Candidate laws: `{len(report.laws)}`",
        f"- Repeated laws: `{report.repeated_laws}`",
        f"- Fixes without test changes: `{report.fixes_without_tests}`",
        "",
    ]
    for law in report.laws:
        lines.extend(_law_markdown(law))
    return "\n".join(lines).rstrip() + "\n"


def _law_card(law: Law) -> str:
    evidence = []
    for item in law.evidence:
        test_state = "protected" if item.has_regression_test else "test gap"
        evidence.append(
            f"""
            <li>
              <div class="commit"><code>{html.escape(item.commit[:10])}</code><span>{html.escape(item.date[:10])}</span><b class="{test_state.replace(' ', '-')}">{test_state}</b></div>
              <p>{html.escape(item.subject)}</p>
              <small>{html.escape(', '.join(item.source_files))}</small>
            </li>
            """
        )
    confidence = int(law.confidence * 100)
    files = "".join(f"<span>{html.escape(path)}</span>" for path in law.affected_files)
    repeated = "repeated" if law.recurrence > 1 else "single"
    return f"""
    <article class="law-card {repeated}">
      <header><code>{law.law_id}</code><div class="confidence">{confidence}% evidence confidence</div></header>
      <h2>{html.escape(law.title)}</h2>
      <div class="metrics">
        <div><strong>{law.recurrence}</strong><span>fixes</span></div>
        <div><strong>{law.protected_fixes}</strong><span>protected</span></div>
        <div><strong>{law.unprotected_fixes}</strong><span>test gaps</span></div>
      </div>
      <div class="files">{files}</div>
      <details><summary>Inspect evidence</summary><ul>{''.join(evidence)}</ul></details>
    </article>
    """


def render_html(report: Report) -> str:
    cards = "".join(_law_card(law) for law in report.laws)
    empty = "<p class='empty'>No candidate laws met the current evidence threshold.</p>" if not cards else ""
    rendered = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bug Laws</title>
<style>
:root{{--ink:#17211b;--paper:#f4f0e6;--card:#fffdf7;--red:#ba3f32;--green:#2e6a4f;--line:#d8d0bf}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}}
main{{max-width:1120px;margin:auto;padding:64px 24px 96px}}.eyebrow{{font:700 12px/1.2 ui-monospace,monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--red)}}
h1{{font:800 clamp(48px,8vw,96px)/.95 Georgia,serif;margin:12px 0 20px;letter-spacing:-.05em}}.thesis{{max-width:760px;font-size:20px;color:#455048}}
.summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin:40px 0}}
.summary div{{background:var(--card);padding:20px}}.summary strong{{font:800 28px/1 ui-monospace,monospace;display:block}}.summary span{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#657068}}
.notice{{border-left:4px solid var(--red);padding:12px 16px;background:#fff8e8;margin-bottom:32px}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
.law-card{{background:var(--card);border:1px solid var(--line);padding:24px;box-shadow:0 8px 30px #3d33230b}}.law-card.repeated{{border-top:5px solid var(--red)}}
.law-card header{{display:flex;justify-content:space-between;gap:16px;font:700 12px/1.2 ui-monospace,monospace;color:var(--red)}}.confidence{{color:#6a746d}}
.law-card h2{{font:700 25px/1.15 Georgia,serif;min-height:58px;margin:18px 0}}.metrics{{display:grid;grid-template-columns:repeat(3,1fr);border-block:1px solid var(--line)}}
.metrics div{{padding:14px 4px}}.metrics strong{{display:block;font:800 22px/1 ui-monospace,monospace}}.metrics span{{font-size:11px;text-transform:uppercase;color:#6a746d}}
.files{{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0}}.files span{{font:11px ui-monospace,monospace;background:#eee8dc;padding:5px 7px}}
details summary{{cursor:pointer;font-weight:700}}ul{{padding-left:18px}}li{{margin:14px 0}}li p{{margin:6px 0}}small{{color:#6a746d}}.commit{{display:flex;gap:10px;align-items:center}}
.commit span{{color:#6a746d}}.commit b{{margin-left:auto;font-size:10px;text-transform:uppercase;padding:3px 6px}}.protected{{color:var(--green);background:#e1f0e6}}.test-gap{{color:var(--red);background:#f8dfd8}}
footer{{margin-top:48px;color:#6a746d;font-size:13px}}.empty{{padding:48px;background:var(--card)}}
@media(max-width:760px){{.summary,.grid{{grid-template-columns:1fr 1fr}}}}@media(max-width:520px){{.summary,.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body><main>
  <div class="eyebrow">Repository archaeology / candidate policy</div>
  <h1>Bug Laws</h1>
  <p class="thesis">Every bug fix writes a law. This report recovers candidate engineering invariants from history and shows which ones still lack regression-test protection.</p>
  <section class="summary">
    <div><strong>{len(report.laws)}</strong><span>candidate laws</span></div>
    <div><strong>{report.repeated_laws}</strong><span>repeated laws</span></div>
    <div><strong>{report.fixes_without_tests}</strong><span>test gaps</span></div>
    <div><strong>{report.candidate_commits}</strong><span>fixes inspected</span></div>
  </section>
  <p class="notice"><strong>Evidence, not authority.</strong> These are machine-recovered candidate laws. Accept, edit, or reject them before turning them into project policy.</p>
  <section class="grid">{cards}</section>{empty}
  <footer>Repository: {html.escape(report.repository)} · Generated {html.escape(report.generated_at)}</footer>
</main></body></html>"""
    return "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"
