#!/usr/bin/env python3
"""Single-writer, standard-library session runtime; validates records, not designs."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
import uuid

SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parents[1]
AXES = ("problem_framing", "system_modeling", "trade_off_reasoning",
        "failure_reasoning", "verification_thinking", "adaptive_reasoning")
PHASES = {"setup", "problem_framing", "design", "stress_test", "reflection", "completed"}
TRANSITIONS = {"setup": {"problem_framing"}, "problem_framing": {"design", "reflection"},
               "design": {"problem_framing", "stress_test", "reflection"},
               "stress_test": {"design", "reflection"}, "reflection": {"design"},
               "completed": set()}
PROVENANCE = {"documented_principle", "fictional_scenario_fact", "user_assumption",
              "hypothetical_consequence", "tool_measured", "unknown"}
RATINGS = {"demonstrated", "partially-demonstrated", "not-observed", "not-assessed"}
KINDS = {"client", "service", "postgresql", "redis", "queue", "other"}
ID_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z")
MAX_BYTES = 16 * 1024 * 1024


class ValidationError(ValueError):
    """A record or destination violates the session contract."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), "Expected a JSON object.")
    require(set(required) <= set(value) <= set(required) | set(optional),
            "Missing required fields or unsupported fields: " + str(sorted(value)))


def identifier(value):
    require(isinstance(value, str) and ID_PATTERN.fullmatch(value), "Invalid identifier.")
    return value


def string(value, allow_empty=False):
    require(isinstance(value, str) and len(value) <= 20000 and
            (allow_empty or bool(value.strip())), "Expected bounded nonempty text.")
    return value


def array(value):
    require(isinstance(value, list) and len(value) <= 1000, "Expected a bounded list.")
    return value


def strings(value):
    for item in array(value):
        string(item)


def integer(value):
    require(type(value) is int and value >= 0, "Expected a nonnegative integer.")


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_path(path):
    """Reject traversal and every symlink, including a symlink within the workspace."""
    path = Path(path).expanduser()
    require(".." not in path.parts, "Path traversal is not allowed.")
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        require(not part.is_symlink(), "Symlink paths are not allowed: " + str(part))
    return path


def workspace_path(value):
    root = safe_path(value)
    require(root.is_dir(), "Workspace must be an existing directory.")
    require(root != PLUGIN_ROOT and PLUGIN_ROOT not in root.parents,
            "Session data cannot be stored inside the plugin installation.")
    require(root != Path(root.anchor), "Choose a dedicated practice directory.")
    return root


def session_path(workspace, session_id):
    root = workspace_path(workspace)
    identifier(session_id)
    return safe_path(root / ".system-design-lab" / "sessions" / session_id)


def read_json(path):
    path = safe_path(path)
    require(path.is_file() and path.stat().st_size <= MAX_BYTES,
            "JSON input is missing, not a regular file, or too large.")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def reject_constant(value):
        raise ValidationError("Non-finite JSON number: " + value)
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeError, RecursionError) as exc:
        raise ValidationError("Invalid JSON; canonical state is never replaced by derived files: " + str(exc)) from exc


def atomic_write(path, content):
    """Flush a new same-directory file, then replace the destination atomically."""
    path = safe_path(path)
    require(path.parent.is_dir(), "Output directory is missing.")
    require(not path.exists() or path.is_file(), "Output destination is not a file.")
    temp = safe_path(path.parent / ("." + path.name + "." + uuid.uuid4().hex + ".tmp"))
    fd = os.open(str(temp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        safe_path(path)
        os.replace(temp, path)
        if os.name == "posix":
            directory_fd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        # A killed process may leave a temp file; readers never treat it as committed.
        if temp.exists():
            temp.unlink()


def json_text(value):
    return json.dumps(value, ensure_ascii=True, indent=2, allow_nan=False) + "\n"


def validate_architecture(architecture):
    fields(architecture, {"components", "connections", "operations"})
    ids = set()
    for component in array(architecture["components"]):
        fields(component, {"id", "label", "kind"})
        cid = identifier(component["id"])
        require(cid not in ids, "Duplicate component identifier.")
        ids.add(cid)
        string(component["label"])
        require(component["kind"] in KINDS, "Unknown component kind; use other for novel technology.")
    for edge in array(architecture["connections"]):
        fields(edge, {"source", "target", "label"})
        require(edge["source"] in ids and edge["target"] in ids, "Connection references an undeclared component.")
        string(edge["label"], allow_empty=True)
    operation_ids = set()
    for operation in array(architecture["operations"]):
        fields(operation, {"id", "description", "steps", "purpose"})
        oid = identifier(operation["id"])
        require(oid not in operation_ids, "Duplicate operation identifier.")
        operation_ids.add(oid)
        string(operation["description"])
        require(operation["purpose"] in {"issuance", "reservation_then_persist", "lookup", "other"},
                "Unknown operation purpose.")
        require(bool(array(operation["steps"])) and all(s in ids for s in operation["steps"]),
                "Operation steps must reference declared components.")


def validate_scenario(scenario):
    fields(scenario, {"id", "version", "title", "notice", "brief", "known_constraints",
                      "revealable_facts", "invariants", "learning_topics", "fallback",
                      "transfer_prompt", "dilemmas", "sources"})
    require(scenario["id"] == "coupon-flash-sale" and scenario["version"] == "0.1",
            "Unsupported scenario or version.")
    for key in ("title", "notice", "brief", "fallback", "transfer_prompt"):
        string(scenario[key])
    strings(scenario["invariants"])
    strings(scenario["learning_topics"])
    source_ids = set()
    for source in array(scenario["sources"]):
        fields(source, {"id", "title", "url", "principle"})
        identifier(source["id"])
        require(source["id"] not in source_ids, "Duplicate source.")
        source_ids.add(source["id"])
        for key in ("title", "url", "principle"):
            string(source[key])
        require(source["url"].startswith("https://") and not any(c.isspace() for c in source["url"]),
                "Sources must use HTTPS links.")
    fact_ids = set()
    for fact in array(scenario["known_constraints"]) + array(scenario["revealable_facts"]):
        fields(fact, {"id", "text", "provenance"})
        identifier(fact["id"])
        require(fact["id"] not in fact_ids, "Duplicate scenario fact.")
        fact_ids.add(fact["id"])
        string(fact["text"])
        require(fact["provenance"] == "fictional_scenario_fact", "Scenario facts must be labeled fictional.")
    dilemma_ids = set()
    for dilemma in array(scenario["dilemmas"]):
        fields(dilemma, {"id", "preconditions", "provenance", "prompt", "sources", "topics"})
        identifier(dilemma["id"])
        require(dilemma["id"] not in dilemma_ids, "Duplicate dilemma.")
        dilemma_ids.add(dilemma["id"])
        string(dilemma["prompt"])
        require(dilemma["provenance"] == "hypothetical_consequence", "Dilemmas must be hypothetical.")
        require(all(s in source_ids for s in array(dilemma["sources"])), "Unknown dilemma source.")
        strings(dilemma["topics"])
        fields(dilemma["preconditions"], {"kinds", "ordered_steps"})
        for values in dilemma["preconditions"].values():
            require(all(k in KINDS for k in array(values)), "Unsupported predicate; expressions are not executed.")


def initial_state(session_id, scenario, config, timestamp):
    identifier(session_id)
    validate_scenario(scenario)
    fields(config, {"mode", "length", "experience"})
    require(config["mode"] in {"guided", "challenge"}, "Unknown learning mode.")
    require(config["length"] in {"short", "standard"}, "Unknown session length.")
    require(config["experience"] in {"unspecified", "beginner", "intermediate", "experienced"},
            "Unknown experience level.")
    return {"schema_version": 1, "session_id": session_id, "scenario": copy.deepcopy(scenario),
            "created_at": timestamp, "updated_at": timestamp, "revision": 0,
            "learning": {**config, "phase": "setup", "paused": False, "completion": None,
                         "prompts": [], "responses": [], "reflections": [], "assessments": []},
            "world": {"architecture": {"components": [], "connections": [], "operations": []},
                      "design_revision": 0, "design_history": [], "decisions": [], "notes": [],
                      "revealed_facts": [], "active_dilemma": None, "dilemmas": []},
            "events": []}


def dilemma_matches(state, dilemma):
    architecture = state["world"]["architecture"]
    kinds = {c["id"]: c["kind"] for c in architecture["components"]}
    predicates = dilemma["preconditions"]
    if not set(predicates["kinds"]) <= set(kinds.values()):
        return False
    order = predicates["ordered_steps"]
    if not order:
        return True
    for operation in architecture["operations"]:
        if operation["purpose"] != "reservation_then_persist":
            continue
        cursor = 0
        for step in operation["steps"]:
            if kinds[step] == order[cursor]:
                cursor += 1
                if cursor == len(order):
                    return True
    return False


def eligible(state):
    learning, world = state["learning"], state["world"]
    visited = {d["dilemma_id"] for d in world["dilemmas"]}
    ready = (learning["phase"] == "stress_test" and not learning["paused"] and
             bool(world["architecture"]["components"]) and not world["active_dilemma"])
    candidates = [d for d in state["scenario"]["dilemmas"]
                  if ready and d["id"] not in visited and dilemma_matches(state, d)]
    return {"revision": state["revision"], "eligible": candidates,
            "fallback": state["scenario"]["fallback"],
            "note": "Eligibility checks declared structure only; no failure has been observed or measured."}


def revise_architecture(state, architecture, event, reason, allow_empty=False):
    validate_architecture(architecture)
    require(allow_empty or bool(architecture["components"]), "A design hypothesis must contain declared components.")
    world = state["world"]
    world["design_revision"] += 1
    world["architecture"] = copy.deepcopy(architecture)
    world["design_history"].append({"design_revision": world["design_revision"],
                                    "event_id": event["event_id"], "reason": reason,
                                    "architecture": copy.deepcopy(architecture)})
    if world["active_dilemma"]:
        current = next(d for d in state["scenario"]["dilemmas"] if d["id"] == world["active_dilemma"])
        if not dilemma_matches(state, current):
            world["dilemmas"][-1]["status"] = "invalidated_by_revision"
            world["dilemmas"][-1]["closed_by"] = event["event_id"]
            world["active_dilemma"] = None


def reduce_event(state, event):
    """Validate one allowlisted event and update a private, uncommitted copy."""
    fields(event, {"event_id", "expected_revision", "revision", "timestamp", "type", "payload"})
    identifier(event["event_id"])
    integer(event["expected_revision"])
    integer(event["revision"])
    string(event["timestamp"])
    require(event["expected_revision"] == state["revision"] and
            event["revision"] == state["revision"] + 1, "Revision conflict; reload status before applying.")
    require(not any(e["event_id"] == event["event_id"] for e in state["events"]), "Duplicate event identifier.")
    kind, payload = event["type"], event["payload"]
    learning, world = state["learning"], state["world"]
    phase = learning["phase"]
    require(phase != "completed", "Completed sessions are immutable; create a new session.")
    require(not learning["paused"] or kind in {"session_resumed", "session_finished"},
            "Session is paused; resume before recording changes.")

    if kind == "phase_changed":
        fields(payload, {"phase"})
        destination = payload["phase"]
        require(destination in PHASES and destination in TRANSITIONS[phase], "Invalid learning phase transition.")
        if destination == "stress_test":
            require(bool(world["architecture"]["components"]), "Record a design hypothesis before stress testing.")
        learning["phase"] = destination
    elif kind == "session_paused":
        fields(payload, set())
        require(not learning["paused"], "Session is already paused.")
        learning["paused"] = True
    elif kind == "session_resumed":
        fields(payload, set())
        require(learning["paused"], "Session is not paused.")
        learning["paused"] = False
    elif kind == "learning_prompt":
        fields(payload, {"axis", "prompt"})
        require(payload["axis"] in AXES, "Unknown reflection axis.")
        string(payload["prompt"])
        learning["prompts"].append({**payload, "event_id": event["event_id"]})
    elif kind == "learner_response":
        fields(payload, {"prompt_id", "response"})
        require(any(p["event_id"] == payload["prompt_id"] for p in learning["prompts"]), "Unknown prompt reference.")
        string(payload["response"])
        learning["responses"].append({**payload, "event_id": event["event_id"]})
    elif kind == "decision_recorded":
        fields(payload, {"id", "summary", "rationale", "alternatives", "risks"}, {"architecture", "supersedes"})
        identifier(payload["id"])
        require(not any(d["id"] == payload["id"] for d in world["decisions"]), "Decision identifier already exists.")
        require(phase in {"design", "stress_test", "reflection"}, "Decisions require the design phase or later.")
        string(payload["summary"])
        string(payload["rationale"])
        strings(payload["alternatives"])
        strings(payload["risks"])
        if "supersedes" in payload:
            previous = next((d for d in world["decisions"] if d["id"] == payload["supersedes"]), None)
            require(previous is not None and previous["status"] == "active", "Superseded decision must be active.")
            previous["status"] = "superseded"
        if "architecture" in payload:
            revise_architecture(state, payload["architecture"], event, payload["rationale"])
        world["decisions"].append({**copy.deepcopy(payload), "event_id": event["event_id"], "status": "active"})
    elif kind == "decision_retracted":
        fields(payload, {"decision_id", "reason"}, {"restore_revision"})
        string(payload["reason"])
        decision = next((d for d in world["decisions"] if d["id"] == payload["decision_id"]), None)
        require(decision is not None and decision["status"] == "active", "Only an active decision can be retracted.")
        require("architecture" not in decision or "restore_revision" in payload,
                "Retracting an architectural decision requires an explicit restore revision.")
        if "restore_revision" in payload:
            integer(payload["restore_revision"])
            history = next((h for h in world["design_history"] if h["design_revision"] == payload["restore_revision"]), None)
            require(history is not None or payload["restore_revision"] == 0, "Unknown design checkpoint.")
            restored = history["architecture"] if history else {"components": [], "connections": [], "operations": []}
            revise_architecture(state, restored, event, payload["reason"], allow_empty=True)
            if not restored["components"] and learning["phase"] == "stress_test":
                learning["phase"] = "design"
                if world["active_dilemma"]:
                    world["dilemmas"][-1].update(status="invalidated_by_revision", closed_by=event["event_id"])
                    world["active_dilemma"] = None
        decision["status"] = "retracted"
    elif kind == "note_recorded":
        fields(payload, {"id", "category", "text", "provenance"}, {"source_ids", "evidence"})
        identifier(payload["id"])
        require(not any(n["id"] == payload["id"] for n in world["notes"]), "Note identifier already exists.")
        require(payload["category"] in {"requirement", "assumption", "risk", "open_question", "verification", "claim"}, "Unknown note category.")
        string(payload["text"])
        require(payload["provenance"] in PROVENANCE, "Unknown evidence provenance.")
        sources = payload.get("source_ids", [])
        require(all(s in {s["id"] for s in state["scenario"]["sources"]} for s in array(sources)), "Unknown source reference.")
        if payload["provenance"] == "documented_principle":
            require(bool(sources), "Documented principles need source identifiers; relevance remains a human judgment.")
        if payload["provenance"] == "fictional_scenario_fact":
            facts = state["scenario"]["known_constraints"] + [f for f in state["scenario"]["revealable_facts"] if f["id"] in world["revealed_facts"]]
            require(any(f["text"] == payload["text"] for f in facts), "Only known or revealed scenario text may be labeled a scenario fact.")
        if payload["provenance"] == "tool_measured":
            evidence = payload.get("evidence")
            fields(evidence, {"tool", "command", "output", "scope"})
            for value in evidence.values():
                string(value)
        elif "evidence" in payload:
            raise ValidationError("Tool output evidence is reserved for tool_measured records.")
        world["notes"].append({**copy.deepcopy(payload), "event_id": event["event_id"], "status": "open"})
    elif kind == "note_resolved":
        fields(payload, {"note_id", "resolution", "provenance"})
        string(payload["resolution"])
        require(payload["provenance"] in {"user_assumption", "hypothetical_consequence", "unknown"}, "Resolution is an unverified explanation, not measured proof.")
        note = next((n for n in world["notes"] if n["id"] == payload["note_id"]), None)
        require(note is not None and note["status"] == "open", "Unknown or already resolved note.")
        note.update(status="resolved", resolution=copy.deepcopy(payload), resolved_by=event["event_id"])
    elif kind == "scenario_fact_revealed":
        fields(payload, {"fact_id"})
        require(any(f["id"] == payload["fact_id"] for f in state["scenario"]["revealable_facts"]), "Unknown scenario fact.")
        require(payload["fact_id"] not in world["revealed_facts"], "Fact was already revealed.")
        world["revealed_facts"].append(payload["fact_id"])
    elif kind == "dilemma_presented":
        fields(payload, {"dilemma_id"}, {"replay"})
        require(type(payload.get("replay", False)) is bool, "Replay must be a boolean.")
        require(phase == "stress_test" and world["architecture"]["components"] and not world["active_dilemma"], "Dilemma requires a design, stress_test, and no active dilemma.")
        dilemma = next((d for d in state["scenario"]["dilemmas"] if d["id"] == payload["dilemma_id"]), None)
        require(dilemma is not None and dilemma_matches(state, dilemma), "Dilemma prerequisites do not match the declared design.")
        require(payload.get("replay", False) or not any(d["dilemma_id"] == payload["dilemma_id"] for d in world["dilemmas"]), "Dilemma already visited; explicit replay is required.")
        world["active_dilemma"] = dilemma["id"]
        world["dilemmas"].append({"dilemma_id": dilemma["id"], "event_id": event["event_id"],
                                  "design_revision": world["design_revision"], "status": "active",
                                  "provenance": "hypothetical_consequence", "prompt": dilemma["prompt"]})
    elif kind == "dilemma_closed":
        fields(payload, {"dilemma_id", "outcome", "response"})
        require(payload["dilemma_id"] == world["active_dilemma"] and world["active_dilemma"] is not None,
                "Only the active dilemma can be closed.")
        require(payload["outcome"] in {"explored", "skipped"}, "Unknown dilemma outcome.")
        string(payload["response"], allow_empty=payload["outcome"] == "skipped")
        world["dilemmas"][-1].update(status=payload["outcome"], response=payload["response"], closed_by=event["event_id"])
        world["active_dilemma"] = None
    elif kind == "reflection_recorded":
        fields(payload, {"text"})
        require(phase == "reflection", "Record reflection in the reflection phase.")
        string(payload["text"])
        learning["reflections"].append({**payload, "event_id": event["event_id"]})
    elif kind == "assessment_recorded":
        fields(payload, {"axis", "rating", "evidence_ids", "explanation"})
        require(phase == "reflection", "Assess only during reflection.")
        require(payload["axis"] in AXES and payload["rating"] in RATINGS, "Unknown axis or rating.")
        string(payload["explanation"])
        prompted = any(p["axis"] == payload["axis"] for p in learning["prompts"])
        if payload["rating"] != "not-assessed":
            require(prompted, "Do not assess an axis the learner was not invited to demonstrate.")
        evidence = array(payload["evidence_ids"])
        learner_events = {e["event_id"] for e in state["events"] if e["type"] in
                          {"learner_response", "decision_recorded", "reflection_recorded"} or
                          (e["type"] == "dilemma_closed" and e["payload"]["outcome"] == "explored")}
        require(all(e in learner_events for e in evidence), "Assessments must reference recorded learner evidence.")
        if payload["rating"] in {"demonstrated", "partially-demonstrated"}:
            require(bool(evidence), "Positive assessments need learner event evidence.")
        learning["assessments"].append({**copy.deepcopy(payload), "event_id": event["event_id"]})
    elif kind == "session_finished":
        fields(payload, {"reason"})
        string(payload["reason"])
        complete = (phase == "reflection" and bool(world["architecture"]["components"]) and
                    any(d["status"] == "explored" for d in world["dilemmas"]) and
                    bool(learning["reflections"]) and not world["active_dilemma"])
        learning.update(phase="completed", completion="completed" if complete else "partial", paused=False)
        if world["active_dilemma"]:
            world["dilemmas"][-1].update(status="ended_early", closed_by=event["event_id"])
            world["active_dilemma"] = None
    else:
        raise ValidationError("Unsupported event type: " + str(kind))
    state["revision"] = event["revision"]
    state["updated_at"] = event["timestamp"]
    state["events"].append(copy.deepcopy(event))


def validate_state(state):
    fields(state, {"schema_version", "session_id", "scenario", "created_at", "updated_at",
                   "revision", "learning", "world", "events"})
    require(type(state["schema_version"]) is int and state["schema_version"] == 1, "Unsupported state schema.")
    integer(state["revision"])
    require(isinstance(state["events"], list) and bool(state["events"]), "Missing canonical event history.")
    started = state["events"][0]
    fields(started, {"event_id", "expected_revision", "revision", "timestamp", "type", "payload"})
    identifier(started["event_id"])
    integer(started["expected_revision"])
    integer(started["revision"])
    string(started["timestamp"])
    require(started["type"] == "session_started" and started["revision"] == 0 and
            started["expected_revision"] == 0, "Invalid session start event.")
    rebuilt = initial_state(state["session_id"], state["scenario"], started["payload"], started["timestamp"])
    rebuilt["events"].append(copy.deepcopy(started))
    for event in state["events"][1:]:
        reduce_event(rebuilt, event)
    require(json.dumps(rebuilt, sort_keys=True, allow_nan=False) ==
            json.dumps(state, sort_keys=True, allow_nan=False),
            "Canonical snapshot and event history disagree; refusing unsafe recovery.")


def load(workspace, session_id):
    state = read_json(session_path(workspace, session_id) / "session.json")
    validate_state(state)
    require(state["session_id"] == session_id, "Session identity mismatch.")
    return state


def save(directory, state):
    validate_state(state)
    content = json_text(state)
    require(len(content.encode("utf-8")) <= MAX_BYTES, "Session exceeds the v0.1 size limit.")
    atomic_write(directory / "session.json", content)


def render(workspace, session_id, state=None):
    # Import only the bundled, code-reviewed renderer, never a session-supplied module.
    from artifacts import write_artifacts
    state = load(workspace, session_id) if state is None else state
    return write_artifacts(session_path(workspace, session_id), state, atomic_write)


def commit_result(workspace, session_id, state, duplicate=False):
    result = {"session_id": session_id, "revision": state["revision"], "duplicate": duplicate,
              "committed": True, "completion": state["learning"]["completion"]}
    try:
        result["artifacts"] = render(workspace, session_id, state)
    except (OSError, ValidationError) as exc:
        result["warning"] = "Canonical state committed. Derived artifacts are incomplete; run render to recover: " + str(exc)
    return result


def init(workspace, session_id=None, mode="guided", length="standard", experience="unspecified", ack=False):
    require(ack, "Confirm the chosen practice destination with --ack-workspace.")
    session_id = session_id or "sim-" + uuid.uuid4().hex[:12]
    directory = session_path(workspace, session_id)
    require(not directory.exists(), "Session already exists; use status/resume or a new identifier.")
    scenario = read_json(SKILL_ROOT / "scenarios" / "coupon-flash-sale.json")
    config = {"mode": mode, "length": length, "experience": experience}
    timestamp = now()
    state = initial_state(session_id, scenario, config, timestamp)
    state["events"].append({"event_id": "evt-start", "expected_revision": 0, "revision": 0,
                            "timestamp": timestamp, "type": "session_started", "payload": config})
    # Exclusive mkdir also protects an interrupted init that has no canonical file yet.
    directory.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.mkdir(mode=0o700)
    save(directory, state)
    return commit_result(workspace, session_id, state)


def apply(workspace, session_id, change):
    fields(change, {"event_id", "expected_revision", "type", "payload"})
    identifier(change["event_id"])
    integer(change["expected_revision"])
    state = load(workspace, session_id)
    previous = next((e for e in state["events"] if e["event_id"] == change["event_id"]), None)
    if previous:
        require(all(previous[k] == change[k] for k in change), "Event identifier reused with different content.")
        return commit_result(workspace, session_id, state, duplicate=True)
    updated = copy.deepcopy(state)
    event = {**copy.deepcopy(change), "revision": state["revision"] + 1, "timestamp": now()}
    reduce_event(updated, event)
    # Detect a stale writer again immediately before commit; this is not a multi-writer lock.
    require(load(workspace, session_id)["revision"] == state["revision"], "Revision changed before commit.")
    save(session_path(workspace, session_id), updated)
    return commit_result(workspace, session_id, updated)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "status", "apply", "eligible", "render", "report"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--workspace", required=True, help="Existing, chosen practice directory.")
        sub.add_argument("--session", required=command != "init")
        if command == "init":
            sub.add_argument("--scenario", choices=["coupon-flash-sale"], default="coupon-flash-sale")
            sub.add_argument("--mode", choices=["guided", "challenge"], default="guided")
            sub.add_argument("--length", choices=["short", "standard"], default="standard")
            sub.add_argument("--experience", choices=["unspecified", "beginner", "intermediate", "experienced"], default="unspecified")
            sub.add_argument("--ack-workspace", action="store_true")
        if command == "apply":
            sub.add_argument("--change-file", required=True, help="JSON file inside the practice workspace.")
    args = parser.parse_args(argv)
    try:
        require(sys.version_info >= (3, 10), "Python 3.10+ is required; select a supported interpreter.")
        if args.command == "init":
            result = init(args.workspace, args.session, args.mode, args.length, args.experience, args.ack_workspace)
        elif args.command == "apply":
            root = workspace_path(args.workspace)
            change_file = safe_path(args.change_file)
            require(root in change_file.parents, "Change file must be inside the practice workspace.")
            result = apply(args.workspace, args.session, read_json(change_file))
        elif args.command == "status":
            result = load(args.workspace, args.session)
        elif args.command == "eligible":
            result = eligible(load(args.workspace, args.session))
        else:
            state = load(args.workspace, args.session)
            if args.command == "report":
                require(state["learning"]["phase"] == "completed", "Finish the session with apply before generating its report.")
            result = {"session_id": args.session, "revision": state["revision"],
                      "artifacts": render(args.workspace, args.session, state)}
        print(json_text(result), end="")
        return 0
    except (ValidationError, OSError, TypeError, KeyError, RecursionError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
