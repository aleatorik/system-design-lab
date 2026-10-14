# State schema and CLI v0.1

Python 3.10+; standard library only. One writer per session. No server or runtime
network access. Commands print JSON on success, errors to stderr with exit code 2.
Use the quoted `${CLAUDE_PLUGIN_ROOT}/skills/simulate/scripts/session_cli.py` path
from SKILL.md. Every command requires `--workspace`; every command except init
requires `--session`. Workspace must already exist and be user-authorized.

## Commands

| Command | Additional arguments | Behavior |
|---|---|---|
| init | `--ack-workspace`, optional `--session`, `--scenario coupon-flash-sale`, `--mode guided\|challenge`, `--length short\|standard`, `--experience unspecified\|beginner\|intermediate\|experienced` | Exclusive new session, phase setup, revision 0 |
| status | none | Validate and return canonical state including events |
| apply | `--change-file PATH` | Validate and commit one structured event; regenerate artifacts |
| eligible | none | Return unvisited, matching dilemmas in stress_test and generic fallback |
| render | none | Regenerate derived files from canonical records without changing state |
| report | none | Require finished session, regenerate artifacts including reflection |

Report status is computed; there is no caller-provided `--partial` flag.
`session_finished` is the only route to phase completed. It works from any phase
and while paused. Full completion requires a current design, an explored dilemma,
reflection phase, explicit learner reflection, and no active dilemma. Otherwise partial.

## Canonical file

`session.json` contains schema_version 1, session_id, a validated scenario snapshot,
created_at/updated_at (UTC), canonical revision, learning, world, and events.
Scenario snapshot pins the exercise to the session's version, even after an update.
The learning object stores mode, length, experience, phase, pause status, completion,
prompts, responses, reflections, and assessments. The world object stores architecture,
design_revision, immutable design_history, decisions, notes, revealed facts, active
dilemma, and dilemma history. Architecture changes and canonical event revisions
use distinct counters.

On load, replay the canonical events and require equality with the stored projection.
The first event is session_started at revision 0. Other events increment revision by 1.
Events have event_id, expected_revision, revision, timestamp, type, payload.
Derived JSONL is a chronological projection, not a separately committed source.

## Change envelope

Use a new stable event ID for each action and current canonical revision:

```json
{
  "event_id": "evt-frame-001",
  "expected_revision": 0,
  "type": "phase_changed",
  "payload": {"phase": "problem_framing"}
}
```

Change files must be inside the chosen practice workspace. Prefer unique names in
the session directory, such as `change-evt-frame-001.json`; do not overwrite one
that may contain a different action. Unknown envelope or payload keys are rejected.
An identical duplicate ID/envelope returns duplicate=true without incrementing;
reuse with different content fails. On conflict, reload; never guess a revision.

## Event payloads

All fields below are required unless marked optional. IDs match
`[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}`; strings are bounded to 20,000 characters.
Empty alternatives/risks lists are valid. Store actual learner reasoning only.

| Type | Payload |
|---|---|
| phase_changed | phase |
| session_paused / session_resumed | empty object |
| learning_prompt | axis, prompt |
| learner_response | prompt_id (event ID), response |
| decision_recorded | id, summary, rationale, alternatives (text list), risks (text list); optional architecture, supersedes (active decision ID) |
| decision_retracted | decision_id, reason; restore_revision required for an architectural decision, optional otherwise |
| note_recorded | id, category, text, provenance; optional source_ids, evidence |
| note_resolved | note_id, resolution, provenance (user_assumption, hypothetical_consequence, or unknown) |
| scenario_fact_revealed | fact_id from revealable_facts |
| dilemma_presented | dilemma_id; optional replay (boolean, only for explicitly requested replay) |
| dilemma_closed | dilemma_id, outcome (explored or skipped), response (can be empty only if skipped) |
| reflection_recorded | text |
| assessment_recorded | axis, rating, evidence_ids, explanation |
| session_finished | reason |

Phases: setup → problem_framing → design → stress_test → reflection.
Additional transitions: design → problem_framing/reflection, stress_test → design,
problem_framing → reflection, reflection → design. Pause is an independent flag.
Completed sessions cannot be changed; exact duplicate events can still be retried.

An architecture has exactly components, connections, operations:

```json
{
  "components": [
    {"id": "api", "label": "Coupon API", "kind": "service"},
    {"id": "db", "label": "PostgreSQL", "kind": "postgresql"}
  ],
  "connections": [{"source": "api", "target": "db", "label": "Issue coupon"}],
  "operations": [{"id": "issue", "description": "Atomic issuance transaction",
                  "purpose": "issuance", "steps": ["api", "db"]}]
}
```

Kinds: client, service, postgresql, redis, queue, other. Kinds are declared metadata,
not inferred from names. Operation purpose: issuance, reservation_then_persist,
lookup, other. Set reservation_then_persist only when the learner explicitly describes
that behavior. All connections and ordered steps reference declared component IDs.
No technology or missing connection is added by the renderer. An initial hypothesis
requires at least one component; the model still asks about an unassessable proposal.

Restore checkpoints by appending a new revision; never erase a previous graph.
Checkpoint 0 is the empty pre-design architecture. An empty restoration leaves
stress_test for design and blocks dilemmas until a new hypothesis is recorded.
Retraction does not automatically reactivate previously superseded decisions;
record an explicit new decision if the learner reaffirms one.

## Notes, provenance, and assessment

Categories: requirement, assumption, risk, open_question, verification, claim.
Provenance: documented_principle, fictional_scenario_fact, user_assumption,
hypothetical_consequence, tool_measured, unknown. Documented principles require
source_ids from the scenario pack. Scenario facts must exactly match known/revealed
scenario text; changed requirements remain explicit user assumptions or hypotheses.
Resolving a note preserves its text and provenance and adds a separate resolution.

tool_measured requires evidence with nonempty tool, command, output, scope.
The runtime records supplied evidence but cannot authenticate an external run.
The conversational agent must verify the tool actually ran before using this label.
No simulated load test or benchmark is executed by this plugin.

Axes: problem_framing, system_modeling, trade_off_reasoning, failure_reasoning,
verification_thinking, adaptive_reasoning. Assessments are model-authored, allowed
only in reflection, with real learner event references; positive ratings need evidence.
An axis without a recorded invitation can only be not-assessed. A skipped dilemma
cannot serve as positive learner evidence. See evaluation-rubric.md for qualitative limits.

## Persistence and recovery

Only session.json is authoritative. Write a unique same-directory temporary file,
flush/fsync it, then os.replace; directory fsync is attempted on POSIX. Orphaned temp
files are ignored. A pre-rename interruption retains the old state; a post-rename
interruption retains the new state. These guarantees assume local filesystem rename
semantics, not arbitrary network filesystems or all hardware failures.
Derived files are regenerated individually; they are not simultaneously atomic.
If rendering fails after commit, apply returns committed=true and an explicit warning.
Use status then render to recover. Do not replay with a new event ID.
Corrupt canonical data or replay mismatch fails closed; never restore a stale JSONL
or guess missing events. Keep the file for manual inspection. An interrupted init
directory is protected; choose a new session ID instead of deleting it automatically.

Reject traversal and every symlink in workspace, session, change-input, and output
paths. Do not store sessions inside the installed plugin. This is not a sandbox
against a malicious local process racing filesystem changes. v0.1 supports one
writer, not concurrent compare-and-swap guarantees. Canonical files are limited
to 16 MiB; permission/file errors are surfaced without deleting existing data.
