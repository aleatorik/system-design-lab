# Evidence-aware qualitative reflection

Each axis is an observation about this exercise, not a score of real-world competence.
Use only the latest recorded assessment per axis in the report; retain all earlier
assessments in the canonical event history. Do not create evidence to fill a report.

| Axis | What to look for in actual learner statements |
|---|---|
| Problem framing | Clarifies business goals, uncertain constraints, and what issuance means |
| System modeling | Explains state ownership, data flow, dependencies, and atomic boundaries |
| Trade-off reasoning | Compares alternatives against operating and business constraints |
| Failure reasoning | Predicts a relevant failure path and explains recovery or its unknowns |
| Verification thinking | Proposes an observable/test that could falsify a claim |
| Adaptive reasoning | Revises or explicitly defends a decision after new conditions, with reasons |

Ratings: demonstrated, partially-demonstrated, not-observed, not-assessed.
Record `learning_prompt` for an axis when asking the learner to demonstrate it.
Record the real reply as `learner_response`, linked to that prompt. Assess only
observed behavior. Use not-assessed when no relevant opportunity was offered;
use not-observed when an opportunity produced no observable reasoning.
A positive assessment must cite one or more learner event IDs: learner_response,
decision_recorded, an explored dilemma_closed, or reflection_recorded.
Never use the assistant's dilemma prompt as evidence of the learner's ability.

Explain why the cited evidence supports the rating and what remains uncertain.
Suggested verification and risk notes are unexecuted plans and hypotheses, not
measurements. User assumptions remain assumptions even if the validator accepts them.
The validator checks IDs, provenance structure, invitations, and transitions; it
cannot verify the semantic relevance of an assessment or correctness of a design.

No recorded assessment means no model judgment should be invented by rendering.
Uninvited axes default to not-assessed; invited axes without a saved assessment
default to not-observed with an explicit notice that no assessment was recorded.
Do not silently infer demonstrated skills from the presence of a database or queue.

Full completion requires an initial/current design, at least one explored dilemma,
and an explicit reflection. Early ending remains partial. Short and challenge mode
can still finish at any time. Skipped/invalidated dilemmas remain historical and
should not be presented as explored failure reasoning.

When discussing sources, use brief original summaries and primary links. Distinguish
documented principles, fictional scenario facts, user assumptions, hypothetical
consequences, tool-measured results with recorded output, and unknown claims.
Never claim measured performance, actual company incidents in this exercise, or
proven educational benefit. An optional transfer response is a practice observation.
