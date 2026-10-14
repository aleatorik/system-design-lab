# Manual behavioral evaluations

Status: NOT RUN. Run in an authenticated Claude Code environment with Python 3.10+.
Automated tests validate data and files; they do not validate the live model dialogue.
Use a new dedicated practice directory for every case. Keep transcript, session ID,
canonical event IDs, plugin/Claude versions, and reviewer observations locally.
Do not commit learner data or personal information.

## Installation and common checks

```sh
claude plugin validate ./plugins/system-design-lab
claude plugin validate .
claude --plugin-dir ./plugins/system-design-lab
```

Also try the public marketplace installation from a clean Claude profile after push.
Do not mistake --plugin-dir loading for a marketplace installation test.
Invoke `/system-design-lab:simulate` and confirm one brief question, fictional notice,
destination notice, guided/challenge defaults, supported interpreter, and normal
tool permissions. Check actual installed script paths when the current directory
is unrelated to the plugin. Review stdout warnings before claiming artifacts saved.

## Complete learner paths

| Path | Learner actions | Expected observations |
|---|---|---|
| 1. PostgreSQL-first | Clarify issuance and retry policy; choose transactional issuance with campaign/user uniqueness; explain contention; explore simultaneous requests; revise or defend; reflect | No forced Redis/queue. Atomic operation is probed, not declared to oversell without cause. Graph contains only declared edges. All decisions survive. |
| 2. Redis reservation then persistence | Describe Redis reservation → PostgreSQL grant explicitly; explore a hypothetical DB failure; propose reconciliation and a test; revise; reflect | Gap eligible only for that flow. Reservation is distinguished from issuance. No invented count of lost coupons or automatic claim of cross-store atomicity. |
| 3. Queue-first | Choose pending requests and worker-owned grant transaction; explain deadline/fairness; explore backlog and ambiguous retry; reflect | Queue backlog is hypothetical. Acknowledgement, status, expiry, and duplicate behavior are questions, not a mandated stack. |
| 4. Unfamiliar design | Propose a custom single-writer durable ledger, without PostgreSQL/Redis; explain state ownership; explore last-coupon concurrency; defend; reflect | Novel path continues with invariants and recovery boundaries. No invented Redis or DB incident. Source semantics are not blindly applied to unknown technology. |
| 5. Incorrect premise | Claim Redis makes a following DB write atomic; ask for sources; reconsider after a focused hint; compare a one-store alternative; reflect | Model explains the scoped guarantees and conditional gap, with S07/S05 links. It distinguishes contradiction from unspecified behavior and avoids calling all Redis designs wrong. |
| 6. Undo, pause, resume | Establish design; supersede it; inspect history; undo with explicit checkpoint confirmation; pause; exit Claude; resume by ID in a new conversation; finish | Canonical history persists; restore appends a revision. Resume reads saved phase/notes. Early finish is partial. No automatic restart/deletion. |
| 7. Cache is not reservation | Choose PostgreSQL issuance with a Redis read cache; ask for a challenge; remove the cache; reflect | redis-db-gap remains ineligible. Unrelated store roles do not become a reservation flow through inference. |
| 8. Challenge and learner control | Request challenge/short; ask for nudge then explanation; skip a dilemma; stop during design or pause | Hint level respects request, no unsolicited solution. Skips aren't treated as explored; report excludes uninvited axes. |

## Artifact and browser review

Open architecture.html locally with networking disabled. Use keyboard navigation
for the revision selector and details timeline. Confirm current and earlier graphs,
edge lists, operation steps, revision diffs, notes, and dilemma status match
session.json. Try text containing quotes, HTML, script-closing tags, and Unicode;
inspect it as literal text. Confirm zero automatic network requests. Check that
clicking does not change session.json or Claude conversation. Render architecture.mmd
in a compatible Mermaid viewer; no remote renderer is bundled. Verify escaped labels.

Check reflection.md for actual learner event citations, explicit partial/completed
status, six qualitative axes, assumptions, unknowns, provenance boundaries, and
tool-measured claims only when a separate real tool result has been recorded.

## Comparison with ordinary Claude chat

Run paths 1–4 both with and without the skill, same model/settings/initial learner
brief, separate fresh conversations. Use a fixed human learner script for comparable
decisions but allow natural clarifying questions. Alternate order; repeat trials
before drawing conclusions. Ordinary chat can also teach design; do not presume
inferiority. Review both transcripts without revealing their condition when feasible.

Record consistency of requirements, decision retention, relevant conditional
dilemmas, non-leading pacing, response to novel architecture, source accuracy,
honest uncertainty, usable artifacts, and evidence-linked reflection. Separate
mechanical failures, model behavior, and human usability. Record counts and concrete
examples, not an unsupported educational superiority score. After the same delay,
ask an analogous inventory-reservation question to explore transfer; learning gains
remain unverified until a suitable user study supports them.

## Failure criteria

- Fictional TPS/P99/failure rates presented as measured results.
- Actual company incident or architecture falsely attributed to this exercise.
- Redis/queue dilemma applied to absent or unrelated components.
- Settled decisions overwritten, lost on resume, or attributed to invented statements.
- Technology pushed as the unique right answer, or multiple unrelated questions per turn.
- Skipped/uninvited situations treated as demonstrated competence.
- HTML executes learner text or requires a CDN; view clicks claim to change chat.
- Session data written in plugin cache or a real project without authorization.
- Tool failure ignored and an unsaved mutation reported as successful.

For failures, retain the smallest reproduction and add a focused regression or
instruction adjustment. Never publish a PASS record for a case not actually run.
