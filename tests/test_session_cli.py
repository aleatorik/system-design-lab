"""Mechanical regression tests. These do not evaluate live Claude behavior."""

from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/system-design-lab/skills/simulate"
sys.path.insert(0, str(SKILL / "scripts"))
import session_cli as cli
import artifacts


def architecture(kinds=("postgresql",), linked=False):
    components = [{"id": "client", "label": "Customer", "kind": "client"},
                  {"id": "api", "label": "Coupon API", "kind": "service"}]
    components += [{"id": kind, "label": kind.title(), "kind": kind if kind in cli.KINDS else "other"} for kind in kinds]
    edges = [{"source": "client", "target": "api", "label": "Request coupon"}]
    edges += [{"source": "api", "target": kind, "label": "Declared operation"} for kind in kinds]
    return {"components": components, "connections": edges,
            "operations": [{"id": "issue", "description": "Reserve then persist" if linked else "Process request",
                            "purpose": "reservation_then_persist" if linked else "issuance",
                            "steps": ["api", *kinds]}]}


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name).resolve()
        self.sid = "sim-test"
        cli.init(self.workspace, self.sid, ack=True)
        self.directory = cli.session_path(self.workspace, self.sid)
        self.sequence = 0

    def state(self):
        return cli.load(self.workspace, self.sid)

    def change(self, kind, payload, event_id=None, revision=None):
        self.sequence += 1
        return {"event_id": event_id or "evt-" + str(self.sequence),
                "expected_revision": self.state()["revision"] if revision is None else revision,
                "type": kind, "payload": payload}

    def apply(self, kind, payload, **kwargs):
        return cli.apply(self.workspace, self.sid, self.change(kind, payload, **kwargs))

    def phase(self, phase):
        return self.apply("phase_changed", {"phase": phase})

    def design(self, kinds=("postgresql",), linked=False):
        self.phase("problem_framing")
        self.phase("design")
        self.apply("decision_recorded", {"id": "dec-first", "summary": "Initial design",
                   "rationale": "Small team and explicit state ownership", "alternatives": ["A queue"],
                   "risks": ["Contention is unmeasured"], "architecture": architecture(kinds, linked)})

    def reject(self, kind, payload, **kwargs):
        before = (self.directory / "session.json").read_bytes()
        with self.assertRaises((cli.ValidationError, TypeError)):
            self.apply(kind, payload, **kwargs)
        self.assertEqual(before, (self.directory / "session.json").read_bytes())

    def test_initialization_and_identity(self):
        state = self.state()
        self.assertEqual(state["revision"], 0)
        self.assertEqual(state["learning"]["phase"], "setup")
        self.assertEqual(state["world"]["design_revision"], 0)
        self.assertTrue((self.directory / "architecture.html").exists())
        self.assertEqual(state["events"][0]["type"], "session_started")

    def test_requires_destination_acknowledgment(self):
        with self.assertRaises(cli.ValidationError):
            cli.init(self.workspace, "new")

    def test_existing_session_and_interrupted_init_protected(self):
        with self.assertRaises(cli.ValidationError):
            cli.init(self.workspace, self.sid, ack=True)
        directory = cli.session_path(self.workspace, "incomplete")
        directory.mkdir()
        with self.assertRaises(cli.ValidationError):
            cli.init(self.workspace, "incomplete", ack=True)

    def test_guided_challenge_and_options(self):
        cli.init(self.workspace, "challenge", mode="challenge", length="short", experience="beginner", ack=True)
        self.assertEqual(cli.load(self.workspace, "challenge")["learning"]["mode"], "challenge")
        with self.assertRaises(cli.ValidationError):
            cli.init(self.workspace, "bad", mode="expert", ack=True)
        self.assertFalse(cli.session_path(self.workspace, "bad").exists())

    def test_invalid_phase_and_missing_design(self):
        self.reject("phase_changed", {"phase": "design"})
        self.reject("phase_changed", {"phase": "unknown"})
        self.phase("problem_framing")
        self.phase("design")
        self.reject("phase_changed", {"phase": "stress_test"})
        self.reject("phase_changed", {"phase": "completed"})

    def test_rewind_and_valid_progression(self):
        self.design()
        self.phase("stress_test")
        self.phase("design")
        self.phase("problem_framing")
        self.assertEqual(self.state()["world"]["design_revision"], 1)

    def test_revision_conflict_and_boolean_revision(self):
        self.phase("problem_framing")
        self.reject("phase_changed", {"phase": "design"}, revision=0)
        self.reject("phase_changed", {"phase": "design"}, revision=True)

    def test_duplicate_is_idempotent_and_id_collision_rejected(self):
        change = self.change("phase_changed", {"phase": "problem_framing"})
        cli.apply(self.workspace, self.sid, change)
        result = cli.apply(self.workspace, self.sid, change)
        self.assertTrue(result["duplicate"])
        self.assertEqual(self.state()["revision"], 1)
        different = {**change, "payload": {"phase": "design"}}
        with self.assertRaises(cli.ValidationError):
            cli.apply(self.workspace, self.sid, different)

    def test_unknown_fields_events_and_invalid_edges(self):
        self.reject("execute", {"code": "arbitrary"})
        self.reject("session_paused", {"unexpected": True})
        self.design()
        bad = architecture()
        bad["connections"][0]["target"] = "not-declared"
        self.reject("decision_recorded", {"id": "bad", "summary": "Broken graph", "rationale": "Example",
                   "alternatives": [], "risks": [], "architecture": bad})

    def test_decisions_and_design_history_preserved(self):
        self.design()
        self.apply("decision_recorded", {"id": "dec-second", "summary": "Change admission flow",
                   "rationale": "Allow pending status", "alternatives": [], "risks": [],
                   "architecture": architecture(("queue", "postgresql")), "supersedes": "dec-first"})
        world = self.state()["world"]
        self.assertEqual(len(world["design_history"]), 2)
        self.assertEqual(world["decisions"][0]["status"], "superseded")
        self.assertEqual(world["design_history"][0]["architecture"], architecture())
        self.apply("decision_retracted", {"decision_id": "dec-second", "reason": "Return to previous checkpoint", "restore_revision": 1})
        world = self.state()["world"]
        self.assertEqual(world["design_revision"], 3)
        self.assertEqual(world["architecture"], architecture())
        self.assertEqual(world["decisions"][1]["status"], "retracted")
        self.assertEqual(len(self.state()["events"]), 6)

    def test_architectural_retraction_requires_checkpoint(self):
        self.design()
        self.reject("decision_retracted", {"decision_id": "dec-first", "reason": "Undo"})

    def test_undo_initial_design_retains_history_but_blocks_dilemmas(self):
        self.design()
        self.phase("stress_test")
        self.apply("dilemma_presented", {"dilemma_id": "parallel-requests"})
        self.apply("decision_retracted", {"decision_id": "dec-first", "reason": "Reconsider first proposal", "restore_revision": 0})
        state = self.state()
        self.assertEqual(state["learning"]["phase"], "design")
        self.assertEqual(len(state["world"]["design_history"]), 2)
        self.assertEqual(state["world"]["architecture"]["components"], [])
        self.assertEqual(cli.eligible(state)["eligible"], [])
        self.reject("phase_changed", {"phase": "stress_test"})

    def test_pause_resume_preserves_phase_and_design(self):
        self.design()
        self.apply("session_paused", {})
        self.reject("phase_changed", {"phase": "reflection"})
        self.apply("session_resumed", {})
        self.assertEqual(self.state()["learning"]["phase"], "design")
        self.assertEqual(self.state()["world"]["design_revision"], 1)
        self.reject("session_resumed", {})

    def test_finish_early_partial_and_immutable(self):
        self.apply("session_paused", {})
        self.apply("session_finished", {"reason": "Stop now"})
        self.assertEqual(self.state()["learning"]["completion"], "partial")
        self.assertTrue((self.directory / "reflection.md").exists())
        self.reject("session_resumed", {})

    def test_complete_requires_exploration_and_reflection(self):
        self.design()
        self.phase("stress_test")
        self.apply("dilemma_presented", {"dilemma_id": "ambiguous-retry"})
        self.apply("dilemma_closed", {"dilemma_id": "ambiguous-retry", "outcome": "explored", "response": "Use a stable request identifier and lookup."})
        self.phase("reflection")
        self.apply("reflection_recorded", {"text": "I would verify duplicate requests across a restart."})
        self.apply("session_finished", {"reason": "Complete reflection"})
        self.assertEqual(self.state()["learning"]["completion"], "completed")

    def test_skipped_dilemma_does_not_count_as_explored(self):
        self.design()
        self.phase("stress_test")
        self.apply("dilemma_presented", {"dilemma_id": "parallel-requests"})
        self.apply("dilemma_closed", {"dilemma_id": "parallel-requests", "outcome": "skipped", "response": ""})
        self.phase("reflection")
        self.apply("reflection_recorded", {"text": "Short session"})
        self.apply("session_finished", {"reason": "Finish"})
        self.assertEqual(self.state()["learning"]["completion"], "partial")

    def test_postgresql_branch_excludes_redis_and_queue(self):
        self.design()
        self.phase("stress_test")
        ids = {d["id"] for d in cli.eligible(self.state())["eligible"]}
        self.assertIn("parallel-requests", ids)
        self.assertNotIn("redis-db-gap", ids)
        self.assertNotIn("queue-backlog", ids)
        self.reject("dilemma_presented", {"dilemma_id": "redis-db-gap"})

    def test_redis_linked_issuance_branch(self):
        self.design(("redis", "postgresql"), linked=True)
        self.phase("stress_test")
        self.assertIn("redis-db-gap", {d["id"] for d in cli.eligible(self.state())["eligible"]})
        self.apply("dilemma_presented", {"dilemma_id": "redis-db-gap"})
        self.assertEqual(self.state()["world"]["dilemmas"][0]["provenance"], "hypothetical_consequence")

    def test_redis_cache_or_reverse_flow_not_reservation_gap(self):
        self.design(("redis", "postgresql"), linked=False)
        self.phase("stress_test")
        self.reject("dilemma_presented", {"dilemma_id": "redis-db-gap"})
        self.apply("decision_recorded", {"id": "reverse", "summary": "Reverse order", "rationale": "Persist before reservation",
                   "alternatives": [], "risks": [], "architecture": architecture(("postgresql", "redis"), linked=True)})
        self.reject("dilemma_presented", {"dilemma_id": "redis-db-gap"})

    def test_queue_branch(self):
        self.design(("queue", "postgresql"))
        self.phase("stress_test")
        self.apply("dilemma_presented", {"dilemma_id": "queue-backlog"})
        self.assertEqual(self.state()["world"]["active_dilemma"], "queue-backlog")

    def test_unknown_architecture_fallback(self):
        self.design(("custom-ledger",))
        self.phase("stress_test")
        result = cli.eligible(self.state())
        self.assertIn("authoritative state", result["fallback"])
        self.assertNotIn("redis-db-gap", {d["id"] for d in result["eligible"]})
        self.apply("dilemma_presented", {"dilemma_id": "parallel-requests"})

    def test_one_active_dilemma_replay_and_invalidation(self):
        self.design(("redis", "postgresql"), linked=True)
        self.phase("stress_test")
        self.apply("dilemma_presented", {"dilemma_id": "redis-db-gap"})
        self.reject("dilemma_presented", {"dilemma_id": "parallel-requests"})
        self.apply("decision_recorded", {"id": "remove-redis", "summary": "Use one store", "rationale": "Simplify recovery",
                   "alternatives": [], "risks": [], "architecture": architecture()})
        self.assertIsNone(self.state()["world"]["active_dilemma"])
        self.assertEqual(self.state()["world"]["dilemmas"][0]["status"], "invalidated_by_revision")
        self.apply("dilemma_presented", {"dilemma_id": "parallel-requests"})
        self.apply("dilemma_closed", {"dilemma_id": "parallel-requests", "outcome": "explored", "response": "Test simultaneous conditional updates."})
        self.reject("dilemma_presented", {"dilemma_id": "parallel-requests"})
        self.apply("dilemma_presented", {"dilemma_id": "parallel-requests", "replay": True})

    def test_notes_provenance_resolution_and_facts(self):
        self.apply("note_recorded", {"id": "assumption-1", "category": "assumption", "text": "Pending status is acceptable", "provenance": "user_assumption"})
        self.apply("note_resolved", {"note_id": "assumption-1", "resolution": "We chose to keep this assumption", "provenance": "user_assumption"})
        self.assertEqual(self.state()["world"]["notes"][0]["status"], "resolved")
        self.reject("note_recorded", {"id": "fake", "category": "claim", "text": "10,000 TPS measured", "provenance": "fictional_scenario_fact"})
        self.reject("note_recorded", {"id": "fake", "category": "claim", "text": "10,000 TPS measured", "provenance": "tool_measured"})
        self.reject("note_recorded", {"id": "fake", "category": "claim", "text": "A principle", "provenance": "documented_principle"})
        self.apply("scenario_fact_revealed", {"fact_id": "user-limit"})
        self.reject("scenario_fact_revealed", {"fact_id": "user-limit"})
        self.reject("scenario_fact_revealed", {"fact_id": "undefined"})

    def test_recorded_measurement_requires_complete_output(self):
        self.apply("note_recorded", {"id": "external-result", "category": "claim", "text": "External experiment result, unverified by this runtime",
                   "provenance": "tool_measured", "evidence": {"tool": "external-test", "command": "test command",
                   "output": "one sample", "scope": "one local sample only"}})
        self.apply("session_finished", {"reason": "Partial review"})
        report = (self.directory / "reflection.md").read_text()
        self.assertIn("one local sample only", report)
        self.assertIn("cannot independently prove", report)

    def test_assessments_require_invitation_and_actual_evidence(self):
        self.design()
        self.phase("reflection")
        assessment = {"axis": "failure_reasoning", "rating": "demonstrated", "evidence_ids": ["not-recorded"], "explanation": "Example"}
        self.reject("assessment_recorded", assessment)
        self.apply("learning_prompt", {"axis": "failure_reasoning", "prompt": "What might fail?"})
        prompt_id = self.state()["events"][-1]["event_id"]
        self.apply("learner_response", {"prompt_id": prompt_id, "response": "I would test response loss after commit."})
        evidence_id = self.state()["events"][-1]["event_id"]
        self.reject("assessment_recorded", assessment)
        self.apply("assessment_recorded", {**assessment, "evidence_ids": [evidence_id]})
        self.apply("session_finished", {"reason": "Stop"})
        report = (self.directory / "reflection.md").read_text()
        self.assertIn(evidence_id, report)
        self.assertIn("not-assessed", report)
        self.assertIn("fallible model-authored", report)

    def test_report_consistency_and_no_inferred_transcript(self):
        self.design()
        self.apply("note_recorded", {"id": "open-1", "category": "open_question", "text": "How long should the retry key live?", "provenance": "unknown"})
        self.apply("session_finished", {"reason": "Early stop"})
        report = (self.directory / "reflection.md").read_text()
        self.assertIn("Status: partial", report)
        self.assertIn("No tool-measured results recorded.", report)
        self.assertIn("No dilemma was encountered", report)
        self.assertIn("How long should the retry key live?", report)
        self.assertIn("Initial design", (self.directory / "journal.md").read_text())
        events = [json.loads(line) for line in (self.directory / "events.jsonl").read_text().splitlines()]
        self.assertEqual(events, self.state()["events"])
        self.assertNotIn("Redis", (self.directory / "architecture.mmd").read_text())

    def test_atomic_write_failure_preserves_canonical_state(self):
        before = (self.directory / "session.json").read_bytes()
        change = self.change("phase_changed", {"phase": "problem_framing"})
        with patch.object(cli.os, "replace", side_effect=OSError("Interrupted before rename")):
            with self.assertRaises(OSError):
                cli.apply(self.workspace, self.sid, change)
        self.assertEqual(before, (self.directory / "session.json").read_bytes())
        self.assertEqual(self.state()["revision"], 0)
        cli.apply(self.workspace, self.sid, change)
        self.assertEqual(self.state()["revision"], 1)

    def test_post_commit_render_failure_and_recovery(self):
        with patch.object(cli, "render", side_effect=OSError("Interrupted after canonical commit")):
            result = self.phase("problem_framing")
        self.assertIn("Canonical state committed", result["warning"])
        self.assertEqual(self.state()["revision"], 1)
        (self.directory / "events.jsonl").write_text("broken derived log")
        (self.directory / ".session.json.orphan.tmp").write_text("incomplete")
        cli.render(self.workspace, self.sid)
        self.assertEqual(len((self.directory / "events.jsonl").read_text().splitlines()), 2)
        self.assertEqual(self.state()["revision"], 1)

    def test_interruption_after_rename_can_be_retried_idempotently(self):
        change = self.change("phase_changed", {"phase": "problem_framing"})
        real_replace = cli.os.replace
        def interrupted_replace(source, destination):
            real_replace(source, destination)
            raise OSError("Process interrupted after rename")
        with patch.object(cli.os, "replace", side_effect=interrupted_replace):
            with self.assertRaises(OSError):
                cli.apply(self.workspace, self.sid, change)
        self.assertEqual(self.state()["revision"], 1)
        result = cli.apply(self.workspace, self.sid, change)
        self.assertTrue(result["duplicate"])
        self.assertEqual(self.state()["revision"], 1)

    def test_corrupt_canonical_and_snapshot_drift_refused(self):
        state = self.state()
        state["learning"]["phase"] = "design"
        (self.directory / "session.json").write_text(json.dumps(state))
        with self.assertRaises(cli.ValidationError):
            self.state()
        (self.directory / "session.json").write_text("{truncated")
        with self.assertRaises(cli.ValidationError):
            cli.render(self.workspace, self.sid)

    def test_snapshot_boolean_cannot_impersonate_integer(self):
        self.design()
        state = self.state()
        state["world"]["design_revision"] = True
        (self.directory / "session.json").write_text(json.dumps(state))
        with self.assertRaises(cli.ValidationError):
            self.state()

    def test_path_traversal_and_plugin_cache_rejected(self):
        for bad in ("../escape", "/tmp/escape", "..", "with/slash"):
            with self.assertRaises(cli.ValidationError):
                cli.init(self.workspace, bad, ack=True)
        with self.assertRaises(cli.ValidationError):
            cli.workspace_path(self.workspace / "..")
        with self.assertRaises(cli.ValidationError):
            cli.init(SKILL, "cache-session", ack=True)

    def test_directory_symlink_and_output_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            destination = Path(other).resolve()
            other_workspace = self.workspace / "other-workspace"
            other_workspace.mkdir()
            (other_workspace / ".system-design-lab").symlink_to(destination, target_is_directory=True)
            with self.assertRaises(cli.ValidationError):
                cli.init(other_workspace, "escape", ack=True)
            outside_file = destination / "outside.txt"
            outside_file.write_text("preserve")
            output = self.directory / "architecture.html"
            output.unlink()
            output.symlink_to(outside_file)
            with self.assertRaises(cli.ValidationError):
                cli.render(self.workspace, self.sid)
            self.assertEqual(outside_file.read_text(), "preserve")

    def test_unrelated_workspace_files_untouched(self):
        existing = self.workspace / "app.py"
        existing.write_text("existing application")
        cli.init(self.workspace, "second", ack=True)
        self.phase("problem_framing")
        self.assertEqual(existing.read_text(), "existing application")

    def test_duplicate_json_keys_and_nonfinite_numbers_rejected(self):
        input_file = self.workspace / "change.json"
        for text in ('{"type":"one","type":"two"}', '{"number":NaN}'):
            input_file.write_text(text)
            with self.assertRaises(cli.ValidationError):
                cli.read_json(input_file)

    def test_html_xss_mermaid_and_markdown_escaping(self):
        attack = '</script><script>alert("xss")</script><img src=x onerror=alert(1)> [link](javascript:alert(1)) ```'
        self.design()
        injected = architecture()
        injected["components"][0]["label"] = attack
        injected["connections"][0]["label"] = attack
        self.apply("decision_recorded", {"id": "injection", "summary": attack, "rationale": attack,
                   "alternatives": [], "risks": [], "architecture": injected})
        self.apply("note_recorded", {"id": "unsafe-note", "category": "assumption", "text": attack, "provenance": "user_assumption"})
        self.apply("session_finished", {"reason": "Stop"})
        output = (self.directory / "architecture.html").read_text()
        self.assertNotIn(attack, output)
        self.assertIn("&lt;/script&gt;", output)
        parser = TagCollector()
        parser.feed(output)
        self.assertEqual(parser.tags.count("script"), 1)
        self.assertNotIn("img", parser.tags)
        self.assertNotIn("iframe", parser.tags)
        self.assertFalse(any("src" in attrs or any(k.startswith("on") for k in attrs) for attrs in parser.attributes))
        self.assertNotIn("innerHTML", output)
        self.assertNotIn("fetch(", output)
        self.assertNotIn("unsafe-inline", output)
        self.assertIn("script-src 'sha256-", output)
        ids = [attrs["id"] for attrs in parser.attributes if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        mmd = (self.directory / "architecture.mmd").read_text()
        self.assertNotIn("<script>", mmd)
        self.assertNotIn("```", mmd)
        self.assertIn("#60;", mmd)
        self.assertNotIn("[link](javascript:", (self.directory / "reflection.md").read_text())
        self.assertIn("data-revision=\"2\"", output)

    def test_cli_subprocess_init_status_apply_and_report(self):
        workspace = self.workspace / "with spaces"
        workspace.mkdir()
        def run(*arguments):
            return subprocess.run([sys.executable, str(SKILL / "scripts/session_cli.py"), *arguments],
                                  text=True, capture_output=True, check=False)
        result = run("init", "--workspace", str(workspace), "--session", "cli", "--ack-workspace")
        self.assertEqual(result.returncode, 0, result.stderr)
        change_file = workspace / "change.json"
        change_file.write_text(json.dumps({"event_id": "finish", "expected_revision": 0,
                                          "type": "session_finished", "payload": {"reason": "Smoke"}}))
        for command in ("status", "eligible", "render"):
            result = run(command, "--workspace", str(workspace), "--session", "cli")
            self.assertEqual(result.returncode, 0, result.stderr)
            json.loads(result.stdout)
        result = run("report", "--workspace", str(workspace), "--session", "cli")
        self.assertEqual(result.returncode, 2)
        result = run("apply", "--workspace", str(workspace), "--session", "cli", "--change-file", str(change_file))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = run("report", "--workspace", str(workspace), "--session", "cli")
        self.assertEqual(result.returncode, 0, result.stderr)
        outside = run("apply", "--workspace", str(workspace), "--session", "cli", "--change-file", str(self.workspace / "outside.json"))
        self.assertEqual(outside.returncode, 2)

    def test_cli_change_file_symlink_is_rejected(self):
        outside = self.workspace / "outside.json"
        outside.write_text('{}')
        link = self.directory / "linked-change.json"
        link.symlink_to(outside)
        result = subprocess.run([sys.executable, str(SKILL / "scripts/session_cli.py"), "apply",
                                 "--workspace", str(self.workspace), "--session", self.sid,
                                 "--change-file", str(link)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Symlink", result.stderr)


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.append(dict(attrs))


class PackagingTest(unittest.TestCase):
    def test_plugin_metadata_and_skill(self):
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(marketplace["name"], "system-design-lab-marketplace")
        self.assertEqual(marketplace["owner"]["name"], "aleatorik")
        self.assertEqual(len(marketplace["plugins"]), 1)
        plugin = marketplace["plugins"][0]
        manifest_path = ROOT / plugin["source"] / ".claude-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["name"], plugin["name"])
        self.assertEqual(manifest["version"], "0.1.0")
        skill = (SKILL / "SKILL.md").read_text()
        self.assertTrue(skill.startswith("---\nname: simulate\n"))
        self.assertIn("disable-model-invocation: true", skill)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/simulate/scripts/session_cli.py", skill)
        self.assertNotIn("allowed-tools:", skill)
        self.assertLess(len(skill.splitlines()), 201)
        for reference in re_find_references(skill):
            self.assertTrue((SKILL / reference).is_file(), reference)

    def test_sources_and_protocol_copy(self):
        scenario = cli.read_json(SKILL / "scenarios/coupon-flash-sale.json")
        cli.validate_scenario(scenario)
        catalog = (ROOT / "docs/SOURCE_CATALOG.md").read_text()
        for source in scenario["sources"]:
            self.assertIn(source["url"], catalog)
        self.assertEqual((SKILL / "references/simulation-protocol.md").read_bytes(),
                         (ROOT / "docs/SIMULATION_PROTOCOL_v0.1.md").read_bytes())
        self.assertEqual((SKILL / "references/SOURCE_CATALOG.md").read_bytes(),
                         (ROOT / "docs/SOURCE_CATALOG.md").read_bytes())

    def test_predicates_are_data_not_code(self):
        scenario = cli.read_json(SKILL / "scenarios/coupon-flash-sale.json")
        scenario["dilemmas"][0]["preconditions"]["eval"] = "run code"
        with self.assertRaises(cli.ValidationError):
            cli.validate_scenario(scenario)


def re_find_references(text):
    import re
    return re.findall(r"\]\(((?:references|scenarios|assets)/[^)]+)\)", text)


if __name__ == "__main__":
    unittest.main()
