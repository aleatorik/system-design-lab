# Implementation notes — v0.1

## Implemented decisions

- One manually invoked Claude Code skill, one plugin, one fictional coupon scenario.
  Names and relative marketplace source match the public installation commands.
  `${CLAUDE_PLUGIN_ROOT}` resolves bundled scripts without repository assumptions.
  No broad allowed-tools grant, hooks, agent delegation, or MCP server is installed.
  Official plugin, marketplace, and skills pages were reviewed on 2026-10-15.
- Python 3.10+ standard library only. The host's default python3 is 3.9.6; an
  existing managed CPython 3.10.19 interpreter is used for local verification.
  No system dependency or CLI was installed. Claude Code is absent from PATH.
- Learning phase/pause/observations are separate from the declared architecture,
  decision history, notes, and dilemma world. Canonical revision and design revision
  are distinct. Structural validation never certifies an architecture's correctness.
- `session.json` is the single authoritative, atomic snapshot including all events.
  Loading replays events and checks equality with the snapshot. Derived JSONL,
  Markdown, Mermaid, and HTML are individually replaced and recoverable with render.
  This adopts the explicitly permitted canonical-file variation of the proposal,
  avoiding false claims of atomic snapshot plus journal commits.
- Replay revalidates explicit, allowlisted event types, payloads, phase transitions,
  dilemma prerequisites, unique identifiers, learner evidence, and provenance.
  Exact duplicate events are idempotent; changed content under an old ID is rejected.
- Session initialization never reuses an existing directory. A partially initialized
  directory is protected. Paths reject traversal and every symlink, including links
  remaining inside the workspace. Change inputs must be in the chosen workspace.
  Session storage is forbidden inside the installed plugin tree. Output files use
  private permissions. No supplied shell command, predicate, or learner string runs.
- The scenario is snapshotted into each session; later plugin edits do not silently
  change that session's facts or event prerequisites. Unsupported schema/scenario
  versions fail closed; migrations are future work.
- Redis gap eligibility requires Redis and PostgreSQL plus an explicit
  `reservation_then_persist` operation with ordered Redis → PostgreSQL steps.
  A cache, mere component presence, or reverse sequence does not qualify.
  Queue backlog requires a declared queue. Generic invariant/retry/policy/admission
  dilemmas and fallback questions accommodate unfamiliar designs.
- Supersession/retraction changes the current decision projection, preserving all
  event payloads and architecture snapshots. Undo appends a restored revision,
  including checkpoint 0 for the empty pre-design state. Superseded decisions are
  not automatically reactivated; re-affirmation is explicit.
- HTML contains escaped text, bundled static CSS/JS, SVG component boxes, a revision
  selector, revision differences, and expandable events. No JSON is interpolated
  into executable JavaScript. CSP permits only the hashes of bundled script/style.
  No CDN, remote resource, telemetry, or bidirectional
  chat integration. Mermaid uses synthetic IDs and numeric entities for unsafe labels.
- Report ratings are explicit model-authored assessments with recorded invitations
  and learner event IDs. Rendering does not synthesize judgments. Uninvited axes
  are not-assessed; invited axes without a saved assessment say not-observed and
  explain the absence. Tool-measured notes require tool, command, output, scope;
  the runtime cannot authenticate supplied external measurements.
- Installed protocol and source catalog are exact copies of the approved documents;
  tests prevent drift. The state schema documents concrete deviations from their
  illustrative schema/CLI. Public links are passive references; no runtime scraping.
- No license is added because the owner has not selected one. Repository publication
  is authorized, but an explicit license is still needed for reuse permissions.

## Scope and persistence limits

Single writer per session. A revision recheck helps detect stale state but is not
a cross-process lock or atomic multi-writer compare-and-swap. No guarantee against
malicious local filesystem races, all hardware failures, or non-local rename behavior.
Local pre/post-rename interruption and derived-artifact recovery are tested. Invalid
canonical files are not replaced by stale derived logs. Orphaned temp files are ignored,
not automatically deleted. A 16 MiB canonical limit keeps v0.1 bounded.

Qualitative design feedback, relevance of evidence, one-question pacing, and factual
source attribution still depend on the model and require manual evaluation. Deterministic
guards constrain stored state; they cannot prevent all misleading conversational text.
No benchmark, database, infrastructure experiment, or production deployment is run.

## Verification record

- First unit-test run: 37 tests, 36 passed; one report-ID escaping failure corrected.
- Final verification results are recorded in docs/VALIDATION.md after execution.
- Claude plugin validation, clean marketplace installation, interactive Claude skill
  smoke testing, and human learning evaluations: NOT RUN here (Claude CLI unavailable).
- GitHub Actions is provided; remote CI results must be observed before claiming PASS.

## Repository continuity

The initial workspace contained four approved documents and a .DS_Store, with no
Git repository. The authorized remote returned no refs on inspection. Existing
planning documents are preserved; README is updated to the implemented behavior.
User session data, credentials, caches, and .DS_Store are excluded from version control.

Completed: scaffold, scenario, validated runtime, skill, artifact renderers, regression
tests, public documentation, CI configuration. Remaining release checks are live Claude
integration, browser review, human behavioral evaluations, and owner license selection.
