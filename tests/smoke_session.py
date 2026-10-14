"""Exercise the complete local CLI path without an LLM or external service."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/system-design-lab/skills/simulate/scripts/session_cli.py"


def smoke(workspace):
    session_id = "sim-smoke"
    def run(command, *arguments):
        result = subprocess.run([sys.executable, str(SCRIPT), command, "--workspace", str(workspace),
                                 "--session", session_id, *arguments], text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        return json.loads(result.stdout)
    initialized = run("init", "--ack-workspace")
    revision = initialized["revision"]
    count = 0
    def apply(kind, payload):
        nonlocal revision, count
        count += 1
        change_file = workspace / ("change-" + str(count) + ".json")
        change_file.write_text(json.dumps({"event_id": "evt-smoke-" + str(count),
                                         "expected_revision": revision, "type": kind, "payload": payload}), encoding="utf-8")
        result = run("apply", "--change-file", str(change_file))
        if result.get("warning"):
            raise RuntimeError(result["warning"])
        revision = result["revision"]
        return "evt-smoke-" + str(count)
    apply("phase_changed", {"phase": "problem_framing"})
    prompt = apply("learning_prompt", {"axis": "problem_framing", "prompt": "What counts as issued?"})
    framing = apply("learner_response", {"prompt_id": prompt, "response": "I need to distinguish a temporary reservation from a durable grant."})
    apply("scenario_fact_revealed", {"fact_id": "issuance"})
    apply("scenario_fact_revealed", {"fact_id": "user-limit"})
    apply("phase_changed", {"phase": "design"})
    architecture = {"components": [{"id": "api", "label": "Coupon API", "kind": "service"},
                                   {"id": "db", "label": "PostgreSQL", "kind": "postgresql"}],
                    "connections": [{"source": "api", "target": "db", "label": "Atomic grant"}],
                    "operations": [{"id": "issue", "description": "Conditional stock update and unique user grant",
                                    "purpose": "issuance", "steps": ["api", "db"]}]}
    apply("decision_recorded", {"id": "dec-initial", "summary": "PostgreSQL owns stock and grants",
                                "rationale": "Keep the consistency boundary in one transaction", "alternatives": ["Separate reservation store"],
                                "risks": ["Contention must be tested"], "architecture": architecture})
    apply("phase_changed", {"phase": "stress_test"})
    candidates = {item["id"] for item in run("eligible")["eligible"]}
    if "redis-db-gap" in candidates or "ambiguous-retry" not in candidates:
        raise RuntimeError("Unexpected PostgreSQL-only eligibility")
    apply("dilemma_presented", {"dilemma_id": "ambiguous-retry"})
    failure = apply("dilemma_closed", {"dilemma_id": "ambiguous-retry", "outcome": "explored",
                                       "response": "Use a stable request identifier and durable result lookup after response loss."})
    architecture["operations"][0]["description"] += "; persist a stable idempotency key and outcome"
    apply("decision_recorded", {"id": "dec-retry", "summary": "Persist request identity and outcome",
                                "rationale": "A timeout does not establish that the transaction failed", "alternatives": [],
                                "risks": ["Retention policy remains an assumption"], "architecture": architecture,
                                "supersedes": "dec-initial"})
    apply("note_recorded", {"id": "key-retention", "category": "open_question", "text": "How long should request identity remain lookupable?", "provenance": "unknown"})
    apply("session_paused", {})
    if not run("status")["learning"]["paused"]:
        raise RuntimeError("Pause was not persisted")
    apply("session_resumed", {})
    rendered = run("render")
    apply("phase_changed", {"phase": "reflection"})
    prompt = apply("learning_prompt", {"axis": "verification_thinking", "prompt": "What test would falsify retry safety?"})
    verification = apply("learner_response", {"prompt_id": prompt, "response": "Drop the response after commit, then retry the same identity and compare durable grants."})
    apply("reflection_recorded", {"text": "I separated a response outcome from a committed operation; contention and key retention remain unverified."})
    for axis, evidence, explanation in (("problem_framing", framing, "Identified the issuance boundary before choosing storage."),
                                        ("verification_thinking", verification, "Proposed a falsifiable response-loss test, not an executed result.")):
        apply("assessment_recorded", {"axis": axis, "rating": "demonstrated", "evidence_ids": [evidence], "explanation": explanation})
    apply("session_finished", {"reason": "Finish the recorded exercise"})
    final = run("report")
    state = run("status")
    directory = workspace / ".system-design-lab/sessions" / session_id
    journal = (directory / "journal.md").read_text(encoding="utf-8")
    report = (directory / "reflection.md").read_text(encoding="utf-8")
    assert state["learning"]["completion"] == "completed"
    assert len(state["world"]["design_history"]) == 2
    assert all(decision in journal for decision in ("dec-initial", "dec-retry"))
    assert "No tool-measured results recorded." in report
    assert verification in report and "Status: completed" in report
    assert all(Path(path).is_file() for path in final["artifacts"].values())
    return {"status": "PASS", "scope": "Local CLI smoke; no Claude conversation was run",
            "events": len(state["events"]), "design_revisions": state["world"]["design_revision"],
            "completion": state["learning"]["completion"], "artifacts": list(final["artifacts"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", help="Optional existing, dedicated directory for inspecting the smoke artifacts.")
    args = parser.parse_args()
    if args.workspace:
        result = smoke(Path(args.workspace).resolve(strict=True))
    else:
        with tempfile.TemporaryDirectory(prefix="system-design-lab-smoke-") as directory:
            result = smoke(Path(directory).resolve())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
