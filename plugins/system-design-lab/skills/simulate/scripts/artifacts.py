"""Render derived learning artifacts from committed records without remote assets."""

from __future__ import annotations

import html
import base64
import hashlib
import json
import math
from pathlib import Path
import re

AXES = ("problem_framing", "system_modeling", "trade_off_reasoning",
        "failure_reasoning", "verification_thinking", "adaptive_reasoning")
PROVENANCE = ("documented_principle", "fictional_scenario_fact", "user_assumption",
              "hypothetical_consequence", "tool_measured", "unknown")


def md(value):
    text = html.escape(str(value), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", text)


def mermaid_label(value):
    # Encode punctuation, control characters, and Unicode as Mermaid numeric entities.
    return "".join(c if c.isascii() and (c.isalnum() or c == " ") else "#" + str(ord(c)) + ";" for c in value)


def mermaid(architecture):
    lines = ["flowchart LR"]
    ids = {c["id"]: "n" + str(i) for i, c in enumerate(architecture["components"])}
    if not ids:
        lines.append('  %% No architecture has been recorded.')
    for component in architecture["components"]:
        lines.append('  ' + ids[component["id"]] + '["' + mermaid_label(component["label"]) + '"]')
    for edge in architecture["connections"]:
        label = '|"' + mermaid_label(edge["label"]) + '"|' if edge["label"] else ""
        lines.append("  " + ids[edge["source"]] + " -->" + label + " " + ids[edge["target"]])
    return "\n".join(lines) + "\n"


def architecture_lines(architecture):
    lines = []
    labels = {c["id"]: c["label"] for c in architecture["components"]}
    for component in architecture["components"]:
        lines.append("- " + md(component["id"]) + ": " + md(component["label"]) + " (" + md(component["kind"]) + ")")
    for edge in architecture["connections"]:
        lines.append("- " + md(labels[edge["source"]]) + " → " + md(labels[edge["target"]]) + ": " + md(edge["label"]))
    for operation in architecture["operations"]:
        lines.append("- Operation " + md(operation["id"]) + ": " + md(operation["description"]) + "; " + " → ".join(md(labels[s]) for s in operation["steps"]))
    return lines or ["No architecture recorded."]


def journal(state):
    lines = ["# Decision Journal", "", "Session: " + md(state["session_id"]),
             "Canonical revision: " + str(state["revision"]), "", state["scenario"]["notice"],
             "", "This file is derived from session.json. It does not contain an inferred transcript.",
             "", "## Initial design", ""]
    history = state["world"]["design_history"]
    lines.extend(architecture_lines(history[0]["architecture"]) if history else ["No initial design recorded."])
    lines += ["", "## Decisions", ""]
    for decision in state["world"]["decisions"]:
        lines += ["### " + md(decision["id"]) + " — " + md(decision["status"]), "",
                  "Event: " + md(decision["event_id"]), "",
                  "Decision: " + md(decision["summary"]), "", "Rationale: " + md(decision["rationale"]),
                  "", "Alternatives: " + ("; ".join(md(a) for a in decision["alternatives"]) or "None recorded."),
                  "", "Potential risks: " + ("; ".join(md(r) for r in decision["risks"]) or "None recorded."), ""]
    lines += ["## Design revision history", ""]
    for revision in history:
        lines += ["### Design revision " + str(revision["design_revision"]), "",
                  "Event: " + md(revision["event_id"]), "Reason: " + md(revision["reason"]), ""]
        lines.extend(architecture_lines(revision["architecture"]))
        lines.append("")
    lines += ["## Assumptions, requirements, risks, and open questions", ""]
    for note in state["world"]["notes"]:
        lines += ["- " + md(note["id"]) + " [" + md(note["category"]) + "; " + md(note["provenance"]) +
                  "; " + md(note["status"]) + "] " + md(note["text"]) + " (" + md(note["event_id"]) + ")"]
        if "resolution" in note:
            lines += ["  Resolution: " + md(note["resolution"]["resolution"]) + " [" +
                      md(note["resolution"]["provenance"]) + "; " + md(note["resolved_by"]) + "]"]
    lines += ["", "## Canonical event timeline", ""]
    for event in state["events"]:
        lines += ["### " + md(event["event_id"]) + " — " + md(event["type"]), "",
                  "Revision " + str(event["revision"]) + " · " + md(event["timestamp"]), "",
                  md(json.dumps(event["payload"], ensure_ascii=True, sort_keys=True)), ""]
    return "\n".join(lines) + "\n"


def report(state):
    learning, world = state["learning"], state["world"]
    template = Path(__file__).resolve().parents[1] / "assets" / "report-template.md"
    intro = template.read_text(encoding="utf-8").format(
        session_id=md(state["session_id"]), scenario=md(state["scenario"]["title"]),
        mode=md(learning["mode"]), completion=learning["completion"] or "in-progress",
        revision=state["revision"], timestamp=md(state["updated_at"]))
    lines = [intro, "## Problem and recorded requirements", "", md(state["scenario"]["brief"]), ""]
    for fact in state["scenario"]["known_constraints"]:
        lines.append("- [fictional_scenario_fact; " + md(fact["id"]) + "] " + md(fact["text"]))
    for fact in state["scenario"]["revealable_facts"]:
        if fact["id"] in world["revealed_facts"]:
            event = next(e for e in state["events"] if e["type"] == "scenario_fact_revealed" and e["payload"]["fact_id"] == fact["id"])
            lines.append("- [revealed fictional_scenario_fact; " + md(event["event_id"]) + "] " + md(fact["text"]))
    lines += ["", "## Current architecture", ""] + architecture_lines(world["architecture"])
    lines += ["", "See architecture.mmd and journal.md for the initial design and every recorded revision.",
              "", "## Qualitative reflection", "",
              "Ratings are fallible model-authored interpretations of recorded evidence, not deterministic competency scores.", ""]
    for axis in AXES:
        assessments = [a for a in learning["assessments"] if a["axis"] == axis]
        prompted = [p for p in learning["prompts"] if p["axis"] == axis]
        assessment = assessments[-1] if assessments else None
        rating = assessment["rating"] if assessment else ("not-observed" if prompted else "not-assessed")
        lines += ["### " + axis.replace("_", " ").title(), "", "Status: " + rating, ""]
        if assessment:
            lines += ["Evidence: " + (", ".join(md(e) for e in assessment["evidence_ids"]) or "None cited."),
                      "", md(assessment["explanation"]), "", "Assessment event: " + md(assessment["event_id"]), ""]
        else:
            lines += ["No qualitative assessment was recorded." if prompted else "The learner was not invited to demonstrate this axis; it is excluded from assessment.", ""]
    lines += ["## Dilemmas", ""]
    for dilemma in world["dilemmas"]:
        lines += ["- " + md(dilemma["dilemma_id"]) + " [hypothetical_consequence; " + md(dilemma["status"]) + "; " + md(dilemma["event_id"]) + "] " + md(dilemma["prompt"])]
        if dilemma.get("response"):
            lines += ["  Recorded learner response (" + md(dilemma["closed_by"]) + "): " + md(dilemma["response"])]
    if not world["dilemmas"]:
        lines.append("No dilemma was encountered. Infer no additional experience beyond recorded evidence.")
    lines += ["", "## Learner reflection", ""]
    for reflection in learning["reflections"]:
        lines += ["- " + md(reflection["event_id"]) + ": " + md(reflection["text"])]
    if not learning["reflections"]:
        lines.append("No explicit reflection was recorded.")
    lines += ["", "## Evidence and provenance", ""]
    for provenance in PROVENANCE:
        lines += ["### " + provenance.replace("_", " ").title(), ""]
        notes = [n for n in world["notes"] if n["provenance"] == provenance]
        if provenance == "documented_principle":
            lines.append("Source summaries below support general principles, not the fictional workload's correctness.")
        elif provenance == "fictional_scenario_fact":
            lines.append("The business brief and revealed constraints are invented exercise inputs.")
        elif provenance == "hypothetical_consequence":
            lines.append("Every scenario dilemma above is a conditional exercise, not an observed failure.")
        elif provenance == "tool_measured":
            lines.append("No tool-measured results recorded." if not notes else "Recorded tool outputs follow. Provenance metadata cannot independently prove an external experiment ran.")
        elif not notes:
            lines.append("None recorded.")
        for note in notes:
            lines += ["- " + md(note["id"]) + " (" + md(note["event_id"]) + "; " + md(note["status"]) + "): " + md(note["text"])]
            if note.get("source_ids"):
                linked = [source for source in state["scenario"]["sources"] if source["id"] in note["source_ids"]]
                lines.append("  References: " + ", ".join("[" + source["id"] + "](<" + source["url"] + ">)" for source in linked))
            if "evidence" in note:
                for key, value in note["evidence"].items():
                    lines.append("  " + key.title() + ": " + md(value))
        lines.append("")
    lines += ["## Unresolved claims and verification", ""]
    open_notes = [n for n in world["notes"] if n["status"] == "open"]
    for note in open_notes:
        lines += ["- " + md(note["id"]) + " [" + md(note["category"]) + "; " + md(note["provenance"]) + "]: " + md(note["text"])]
    if not open_notes:
        lines.append("No open notes were recorded; this does not establish that the design has no unresolved risks.")
    lines += ["", "Verification proposals are plans until explicitly executed and their tool output recorded.",
              "", "## Sources and further reading", ""]
    for source in state["scenario"]["sources"]:
        lines += ["- " + source["id"] + ": [" + md(source["title"]) + "](<" + source["url"] + ">) — " + md(source["principle"])]
    lines += ["", "## Learning transfer", "", md(state["scenario"]["transfer_prompt"]), "",
              "This is an optional practice question. No transfer benefit has been established by this report.", ""]
    return "\n".join(lines)


def escape(value):
    return html.escape(str(value), quote=True)


def graph_svg(architecture, graph_id):
    components = architecture["components"]
    if not components:
        return "<p>No architecture recorded.</p>"
    columns = min(3, len(components))
    rows = math.ceil(len(components) / columns)
    width, height = columns * 270, rows * 135 + 30
    positions = {c["id"]: ((i % columns) * 270 + 20, (i // columns) * 135 + 20) for i, c in enumerate(components)}
    marker = "arrow-" + str(graph_id)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Declared architecture connections">',
             f'<defs><marker id="{marker}" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#637b9f"/></marker></defs>']
    for edge in architecture["connections"]:
        x1, y1 = positions[edge["source"]]
        x2, y2 = positions[edge["target"]]
        parts.append(f'<path d="M{x1+115},{y1+80} L{x2+115},{y2}" stroke="#637b9f" fill="none" marker-end="url(#{marker})"/>')
    for component in components:
        x, y = positions[component["id"]]
        parts += [f'<g><title>{escape(component["label"])}</title><rect x="{x}" y="{y}" width="230" height="80" rx="10" fill="#eaf1fa" stroke="#637b9f"/>',
                  f'<text x="{x+12}" y="{y+30}" fill="#152944">{escape(component["label"][:26])}</text>',
                  f'<text x="{x+12}" y="{y+57}" fill="#445d80">{escape(component["kind"])}</text></g>']
    return "".join(parts) + "</svg>"


def architecture_html(architecture, graph_id=0):
    labels = {c["id"]: c["label"] for c in architecture["components"]}
    parts = [graph_svg(architecture, graph_id), "<h3>Components</h3><ul>"]
    for component in architecture["components"]:
        parts.append("<li>" + escape(component["label"]) + " (" + escape(component["kind"]) + ")</li>")
    parts.append("</ul><h3>Connections</h3><ul>")
    for edge in architecture["connections"]:
        parts.append("<li>" + escape(labels[edge["source"]]) + " → " + escape(labels[edge["target"]]) + ": " + escape(edge["label"]) + "</li>")
    parts.append("</ul><h3>Declared operations</h3><ul>")
    for operation in architecture["operations"]:
        parts.append("<li>" + escape(operation["description"]) + ": " + " → ".join(escape(labels[s]) for s in operation["steps"]) + "</li>")
    return "".join(parts) + "</ul>"


def diff_html(previous, current):
    parts = ["<h3>Changes from the previous design revision</h3><ul>"]
    for key, title in (("components", "Component"), ("connections", "Connection"), ("operations", "Operation")):
        before = {json.dumps(item, sort_keys=True) for item in previous[key]}
        after = {json.dumps(item, sort_keys=True) for item in current[key]}
        for item in sorted(after - before):
            parts.append("<li>" + title + " added or changed: " + escape(item) + "</li>")
        for item in sorted(before - after):
            parts.append("<li>" + title + " removed or replaced: " + escape(item) + "</li>")
    return "".join(parts) + "</ul>"


STYLE = """
body{font:16px/1.6 system-ui,sans-serif;margin:auto;padding:2rem;max-width:1100px;color:#182e49;background:#f7f9fc}
h1,h2,h3{line-height:1.3}section,article{background:white;border:1px solid #dbe3ee;border-radius:12px;padding:1.2rem;margin:1rem 0}
select,button{font:inherit;padding:.4rem}label{display:block}svg{width:100%;max-height:650px}li{overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf2f8;padding:.8rem}small{color:#445d80}.notice{border-left:4px solid #637b9f;padding-left:1rem}
[hidden]{display:none!important}summary{cursor:pointer}a{color:#1c5aab}:focus-visible{outline:3px solid #d27a00}
@media(max-width:600px){body{padding:1rem}}
"""
SCRIPT = """
const selector = document.getElementById('revision');
if (selector) {
  selector.addEventListener('change', () => {
    document.querySelectorAll('[data-revision]').forEach(panel => {
      panel.hidden = panel.dataset.revision !== selector.value;
    });
  });
}
"""


def interactive_html(state):
    world = state["world"]
    script_hash = base64.b64encode(hashlib.sha256(SCRIPT.encode("utf-8")).digest()).decode("ascii")
    style_hash = base64.b64encode(hashlib.sha256(STYLE.encode("utf-8")).digest()).decode("ascii")
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'sha256-' + script_hash + '\'; style-src \'sha256-' + style_hash + '\'; img-src \'none\'; connect-src \'none\'; base-uri \'none\'; form-action \'none\'">',
             '<title>System Design Lab — Local Session</title><style>' + STYLE + '</style></head><body>',
             '<h1>System Design Lab</h1><p>Session ' + escape(state["session_id"]) + '; canonical revision ' + str(state["revision"]) + '</p>',
             '<p class="notice">' + escape(state["scenario"]["notice"]) + '</p>',
             '<p>Local reading view. Selecting a revision changes this view only. It does not change Claude conversation or session state. No measured performance is implied.</p>',
             '<section><h2>Current architecture and design revision history</h2>']
    history = world["design_history"]
    if not history:
        parts.append(architecture_html(world["architecture"]))
    else:
        parts.append('<label for="revision">View design revision</label><select id="revision">')
        for item in history:
            revision = item["design_revision"]
            selected = ' selected' if revision == world["design_revision"] else ''
            parts.append(f'<option value="{revision}"{selected}>Revision {revision}</option>')
        parts.append('</select>')
        previous = {"components": [], "connections": [], "operations": []}
        for item in history:
            revision = item["design_revision"]
            hidden = '' if revision == world["design_revision"] else ' hidden'
            parts.append(f'<article data-revision="{revision}"{hidden}><h3>Design revision {revision}</h3>')
            parts += ['<p>Event ' + escape(item["event_id"]) + ': ' + escape(item["reason"]) + '</p>',
                      architecture_html(item["architecture"], revision), diff_html(previous, item["architecture"]), '</article>']
            previous = item["architecture"]
    parts.append('</section><section><h2>Decision timeline</h2>')
    for event in state["events"]:
        parts.append('<details><summary>' + escape(event["event_id"]) + ' · ' + escape(event["type"]) +
                     ' · revision ' + str(event["revision"]) + '</summary><pre>' +
                     escape(json.dumps(event["payload"], ensure_ascii=True, indent=2)) + '</pre></details>')
    parts.append('</section><section><h2>Active and explored dilemmas</h2><ul>')
    for dilemma in world["dilemmas"]:
        parts.append('<li>' + escape(dilemma["dilemma_id"]) + ' (' + escape(dilemma["status"]) +
                     '; hypothetical_consequence): ' + escape(dilemma["prompt"]) +
                     '<p>Recorded response: ' + escape(dilemma.get("response", "None recorded.")) + '</p></li>')
    parts.append('</ul></section><section><h2>Assumptions, risks, and open questions</h2><ul>')
    for note in world["notes"]:
        parts.append('<li>' + escape(note["id"]) + ' [' + escape(note["category"]) + '; ' +
                     escape(note["provenance"]) + '; ' + escape(note["status"]) + ']: ' + escape(note["text"]))
        if "resolution" in note:
            parts.append('<p>Resolution: ' + escape(note["resolution"]["resolution"]) + ' [' + escape(note["resolution"]["provenance"]) + ']</p>')
        parts.append('</li>')
    parts.append('</ul></section><section><h2>Fictional scenario constraints</h2><ul>')
    for fact in state["scenario"]["known_constraints"] + state["scenario"]["revealable_facts"]:
        if fact in state["scenario"]["known_constraints"] or fact["id"] in world["revealed_facts"]:
            parts.append('<li>[fictional_scenario_fact] ' + escape(fact["text"]) + '</li>')
    parts.append('</ul></section><script>' + SCRIPT + '</script></body></html>')
    return "".join(parts)


def write_artifacts(directory, state, atomic_write):
    outputs = {"events.jsonl": "".join(json.dumps(e, ensure_ascii=True, allow_nan=False) + "\n" for e in state["events"]),
               "journal.md": journal(state), "architecture.mmd": mermaid(state["world"]["architecture"]),
               "architecture.html": interactive_html(state)}
    if state["learning"]["phase"] == "completed":
        outputs["reflection.md"] = report(state)
    paths = {}
    for filename, content in outputs.items():
        atomic_write(directory / filename, content)
        paths[filename] = str(directory / filename)
    return paths
