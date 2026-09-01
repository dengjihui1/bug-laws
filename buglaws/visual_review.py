from __future__ import annotations

import html
import json
from pathlib import Path


def render_review_html(store_path: str | Path, output_path: str | Path) -> Path:
    store = json.loads(Path(store_path).read_text(encoding="utf-8"))
    cards = []
    for index, entry in enumerate(store.get("entries", [])):
        evidence = "".join(f"<li><code>{html.escape(str(item.get('commit', ''))[:12])}</code> {html.escape(str(item.get('subject', '')))}<br><small>{html.escape(', '.join(item.get('source_files', [])))}</small></li>" for item in entry.get("evidence", []))
        key = html.escape(str(entry.get("law_id", index)))
        cards.append(f"<article data-law-id='{key}'><h2>{key}</h2><p class='title'>{html.escape(str(entry.get('original_title', '')))}</p><details><summary>Evidence</summary><ul>{evidence}</ul></details><label>Verdict <select class='verdict'><option>PENDING</option><option>ACCEPT</option><option>EDIT</option><option>REJECT</option><option>UNSCORABLE</option></select></label><label>Edited title <input class='edited-title'></label><label>Rationale <textarea class='rationale'></textarea></label></article>")
    rendered = """<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Bug Laws review</title><style>body{font:16px system-ui;max-width:1000px;margin:auto;padding:24px;background:#f5f2ea;color:#17211b}article{background:#fffdf7;border:1px solid #d8d0bf;margin:16px 0;padding:20px}label{display:block;margin:12px 0}input,textarea,select{display:block;width:100%;max-width:700px;padding:8px;margin-top:4px}button{padding:10px 16px;margin:8px 0;cursor:pointer}.title{font-size:20px;font-weight:700}small{color:#657068}</style></head><body><h1>Bug Laws review</h1><p>Local visual review. Generated candidates remain separate from project policy.</p><button id='download'>Download decisions JSON</button><main>""" + "".join(cards) + """</main><script>document.getElementById('download').onclick=()=>{const entries=[...document.querySelectorAll('article')].map(a=>({law_id:a.dataset.lawId,verdict:a.querySelector('.verdict').value,edited_title:a.querySelector('.edited-title').value,rationale:a.querySelector('.rationale').value}));const blob=new Blob([JSON.stringify({review_schema_version:'accepted-laws-v1',entries},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='review-decisions.json';a.click();};</script></body></html>"""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    return target
