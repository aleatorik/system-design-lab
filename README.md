# System Design Lab

**Practice engineering judgment, not memorized architectures.**

## Project Overview

System Design Lab v0.1 is a local Claude Code plugin for conversational system
design practice. You frame a fictional business problem, propose a design,
explain your decisions, explore relevant hypothetical conditions, and reflect.
Your confirmed decisions become a validated local journal and visual history.

**Status:** implementation complete; automated local verification passed.
Claude Code installation and live conversational behavior are **unverified** in
the development environment because the Claude CLI is unavailable. See
[verification results](docs/VALIDATION.md) for the precise boundaries.

Repository: [aleatorik/system-design-lab](https://github.com/aleatorik/system-design-lab).
Primary runtime: Claude Code. Python 3.10+ standard library; no pip dependencies.
Product text and scenarios are English. No multilingual framework is included.

> All scenarios are fictional educational exercises inspired by documented
> real-world engineering problems. They do not reproduce any company's actual
> systems, incidents, or performance measurements. This tool does not replace
> hands-on production experience.

## Why This Exists

Engineers need opportunities to clarify requirements, reason about state and
failure, weigh operating costs, and decide what evidence would change their minds.
Not every role offers repeated exposure to those decisions. This project organizes
practice around the reasoning process rather than a memorized reference architecture.

## What Makes It Different from Normal LLM Chat

Ordinary LLM chat can already support useful system design learning. This plugin
adds structure and durable artifacts; it is not proven superior to general chat.

| Mechanism | Additional practice experience |
|---|---|
| Repeatable learning protocol | A learner-controlled sequence from framing through reflection |
| Scenario-grounded dilemmas | Questions attached to a defined fictional business problem |
| Explicit decision history | Earlier rationale survives changes and a new conversation |
| Conditional scenario branching | Redis/queue conditions require matching declared components and operations |
| Deterministic state validation | Invalid transitions and inconsistent stored events are rejected |
| Progressive disclosure of constraints | Clarifying questions reveal defined facts rather than an initial answer sheet |
| Non-leading Socratic questions | Instructions probe rationale before suggesting alternatives |
| Evidence-aware feedback | Principles, assumptions, hypotheses, and recorded tool results remain distinguishable |
| Architecture visualization | Current and previous declared designs can be inspected locally |
| Reflection and learning transfer | Recorded evidence supports qualitative feedback and an optional analogous problem |

The code enforces structural rules. Question quality, interpretation, and semantic
feedback depend on the model and still require human evaluation. Usability and
learning effects have not been established by user studies. See
[manual evaluations and ordinary-chat comparison](tests/manual-evals.md).

## Learning Philosophy

- Clarify the business problem before selecting technology.
- Explore multiple defensible designs and their constraints.
- Explain why an operation preserves an invariant, not just which tool it uses.
- Distinguish a documented guarantee from an assumption or prediction.
- Revise or defend a decision when conditions change.
- Identify what a real experiment would need to verify.

A PostgreSQL-centered design can be a valid path. Redis, queues, and microservices
are never prerequisites for a good answer. Structural validation of a session
is not proof that the proposed architecture meets its goals.

## How the Simulation Works

1. **Setup:** choose a practice directory; defaults are Coupon Flash Sale, guided,
   standard length, unspecified experience. Challenge and short sessions are available.
2. **Problem framing:** read the initial brief, clarify requirements, and reveal
   relevant fictional facts progressively.
3. **Design:** propose components, connections, ordered operations, rationale,
   assumptions, alternatives, and risks. Ambiguous interpretations are confirmed.
4. **Stress test:** predict what happens under one relevant hypothetical condition.
   The state tool verifies its prerequisites before storing the dilemma.
5. **Adapt:** revise the architecture or explain why the original design still fits.
6. **Reflection:** review recorded evidence, open questions, and verification ideas.

The skill asks one central question at a time. Guided mode offers progressive
help; challenge mode avoids unsolicited solutions. Both allow requested
`nudge`, `focused`, and `explanation` hints. You can inspect history, skip a dilemma,
undo a decision with a confirmed checkpoint, pause, resume, start a new session,
or finish early. Early reports are labeled **partial**.

## Key Features

- One explicitly invoked skill: `/system-design-lab:simulate`.
- Validated events, unique IDs, revision checks, and idempotent duplicate handling.
- Separate learning state and declared design state, with immutable event history.
- Conditional dilemma selection and generic questions for unfamiliar architectures.
- Atomic canonical state, individually recoverable derived files, single-writer scope.
- Decision Journal, Mermaid source, standalone interactive HTML, and Reflection Report.
- Six qualitative reflection axes with learner-event evidence and provenance labels.
- No runtime network calls, telemetry, servers, databases, or package installation.

## Supported Scenario

**Coupon Flash Sale** (`coupon-flash-sale`): a fictional commerce team may issue
at most 1,000 coupons. An assumed peak of 10,000 incoming requests per second is an
invented planning input, **not measured throughput or a capacity guarantee**.

Explore concurrency, consistency, idempotency, safe retries, recovery, admission,
business constraints, trade-offs, and verification. Paths include PostgreSQL-first,
Redis reservation followed by PostgreSQL persistence, queue-based processing,
and custom architectures.

Dilemmas cover last-coupon concurrency, response-loss retries, the Redis-to-DB gap,
queue backlog, admission pressure, and a hypothetical policy change. The Redis gap
requires an explicitly declared reservation-then-persist flow; a Redis cache alone
does not qualify. Every scenario-generated failure is hypothetical.

## Quick Start

Requirements: installed and authenticated [Claude Code](https://code.claude.com/docs/en/overview),
Python **3.10+** available to its terminal, and an authorized writable practice directory.
No separate service, database, Docker, MCP integration, or pip install is needed.

```sh
claude plugin marketplace add aleatorik/system-design-lab
claude plugin install system-design-lab@system-design-lab-marketplace
mkdir system-design-practice
cd system-design-practice
claude
```

In Claude Code:

```text
/system-design-lab:simulate
```

Tell the simulator to use the current dedicated practice directory. It explains
where records will be written. Answer naturally and start by clarifying the business
requirements. To select a mode, say: `Use challenge mode for a short session.`

## Plugin Installation

The repository is the marketplace; the plugin is the `plugins/system-design-lab`
subdirectory. Marketplace ID: `system-design-lab-marketplace`. Plugin ID:
`system-design-lab`. Skill ID: `simulate`. Install commands above match the metadata.

Restart Claude or use `/reload-plugins` if the command is missing from an existing
session. Review plugin code before enabling third-party tools. Ordinary Claude Code
permissions still apply; the skill does not grant broad tool access.

For local development without installation, from a clone:

```sh
git clone https://github.com/aleatorik/system-design-lab.git
cd system-design-lab
claude plugin validate ./plugins/system-design-lab
claude plugin validate .
claude --plugin-dir ./plugins/system-design-lab
```

For an isolated practice directory, pass the **absolute path to the plugin
subdirectory** when starting Claude there. Do not pass the marketplace root as if
it were a single plugin. Bundled skill scripts resolve via the officially documented
`${CLAUDE_PLUGIN_ROOT}` substitution; no developer path is embedded.
See [plugin documentation](https://code.claude.com/docs/en/plugins/create),
[marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), and
[skill paths](https://code.claude.com/docs/en/skills).

## Example Conversation

Illustrative dialogue, **not a transcript of a live Claude validation run**:

```text
SIMULATOR: This is a fictional exercise. Records will be written in your chosen
  practice directory. Which dedicated directory should we use?
YOU: Use this empty folder, guided mode.
SIMULATOR: A small commerce team can issue at most 1,000 coupons. The team assumes
  a possible peak of 10,000 incoming RPS; no capacity has been measured.
  What would you clarify before choosing the architecture?
YOU: What counts as issuance, and is one coupon per user required?
SIMULATOR: Revealed scenario facts: issuance means a durable grant users can
  look up; the initial policy is one per authenticated user per campaign.
  Where should authoritative issuance state live in your initial design?
YOU: PostgreSQL. A transaction should update stock and record a unique user grant.
SIMULATOR: You propose PostgreSQL for authoritative stock and grants.
  Which operation prevents two requests from taking the last coupon?
YOU: A conditional stock update in that transaction; I would test concurrent attempts.
SIMULATOR: Hypothetical stress test: the response is lost after a possible commit.
  How would a retry find or safely establish the outcome?
```

Useful phrases: `Show my assumptions`, `Compare alternatives`, `Give me a nudge`,
`Undo the last decision`, `Pause`, `Resume session sim-...`, `Finish with a report`.
Resume uses stored state; the plugin cannot reconstruct unsaved conversational turns.

## Output Files

```text
<chosen practice directory>/.system-design-lab/sessions/<session-id>/
├── session.json           # authoritative state AND all canonical events
├── events.jsonl           # derived chronological projection
├── journal.md             # decisions, reasons, revisions, notes, event IDs
├── architecture.mmd       # current declared Mermaid graph
├── architecture.html      # offline reading view and revision comparison
├── reflection.md          # completed or partial report after finish
└── change-*.json           # explicit event inputs written by the agent, if used
```

`session.json` is the source of truth. Changes regenerate the journal, JSONL,
Mermaid, and HTML. `reflection.md` is generated after finish. Files contain recorded
learner data only; artifacts do not fabricate missing decisions or measurements.

Open `architecture.html` directly in a local browser. The revision selector and
expandable timeline change the local view only; clicks do not change Claude chat
or canonical state. There is no server, CDN, tracking, or remote JavaScript.
Mermaid source can be rendered in compatible tooling; no Mermaid runtime is bundled.

The reflection covers problem framing, system modeling, trade-off reasoning,
failure reasoning, verification thinking, and adaptive reasoning. Ratings are
`demonstrated`, `partially-demonstrated`, `not-observed`, or `not-assessed`.
Judgments require saved learner evidence and an invitation to demonstrate the axis.
Uninvited axes are excluded. These are fallible exercise observations, not scores.

## Research Sources

The [source catalog](docs/SOURCE_CATALOG.md) records primary sources and the exact
scope of their relevance: Shopify on demand and traffic shaping; Stripe and Amazon
Builders' Library on idempotency and retries; PostgreSQL and Redis documentation
on scoped storage guarantees; AWS Well-Architected on workload review. GitHub and
Cloudflare postmortems are references for future exercises, not implemented replicas.

The installed plugin contains the catalog and brief original summaries with links.
Sources are not scraped during a simulation. A source supporting a principle does
not establish that a fictional failure happened, nor verify a design's performance.
Third-party articles, diagrams, and code are not mirrored.

## Limitations

- Claude dialogue and clean installation are not integration-tested in this environment.
- LLM analysis can be wrong; the validator checks structure and scenario consistency.
- No database runs, load tests, failure injection, or production changes are performed.
- One writer per session; no concurrent-agent or multi-process transaction guarantee.
- Local rename/fsync assumptions; no universal protection against hardware failures,
  malicious local file races, or unusual network filesystems.
- No automatic migration for other scenario/schema versions; canonical state is
  limited to 16 MiB. Corrupt canonical files fail closed instead of guessing recovery.
- Sessions are local; Claude inference still follows your account's service and data
  settings. This is not offline inference or a guarantee of private model processing.
- `tool_measured` records require actual external output, but metadata cannot
  independently authenticate an experiment. The plugin never performs benchmarks.
- No user accounts, cloud storage, payments, analytics, i18n, or hosted web application.
- Educational effectiveness and learning transfer remain unverified.

## Roadmap

- Improve consistency across multiple valid architecture paths.
- Expand repeated tests, adversarial cases, and behavioral evaluations.
- Improve session UX from actual user feedback.
- Add scenarios in other business domains after content review.
- Evaluate whether practice transfers to unfamiliar problems.

These are future work, not completed capabilities. Some evaluation prompts may
remain private; public safety and state regression tests remain available.

## Local Development and Testing

Repository layout:

```text
.claude-plugin/marketplace.json
plugins/system-design-lab/.claude-plugin/plugin.json
plugins/system-design-lab/skills/simulate/
  SKILL.md
  references/             # installed protocol, source catalog, schema, rubric
  scenarios/              # one validated fictional scenario
  scripts/                # session_cli.py and artifacts.py
  assets/                 # report honesty template
tests/                     # unittest and manual behavioral evaluations
docs/                      # approved specifications, notes, validation record
.github/workflows/tests.yml
```

Run with a supported Python interpreter:

```sh
python3 --version
python3 -m unittest discover -s tests -v
python3 tests/smoke_session.py
```

No package installation is necessary. GitHub Actions runs the same suite on
Python 3.10, 3.12, and 3.13. Configuration alone is not a claim that CI has run.

The CLI also works without Claude for mechanical inspection. Run from the clone:

```sh
mkdir practice
python3 plugins/system-design-lab/skills/simulate/scripts/session_cli.py init \
  --workspace ./practice --scenario coupon-flash-sale --ack-workspace
```

Use the returned ID for `status`, `eligible`, `render`, and `report`:

```sh
python3 plugins/system-design-lab/skills/simulate/scripts/session_cli.py status \
  --workspace ./practice --session <returned-session-id>
```

`apply` requires `--change-file` with an explicit event ID, current revision, type,
and payload. Its JSON must be inside the chosen practice workspace. See the
[state schema and event examples](plugins/system-design-lab/skills/simulate/references/state-schema.md).
`report` requires an applied `session_finished` event; it does not finish a session.
[Implementation notes](docs/IMPLEMENTATION_NOTES.md) explain recovery and trade-offs.

## Troubleshooting

| Problem | Action |
|---|---|
| Skill missing | Check marketplace/plugin names, restart Claude or `/reload-plugins`; validate both directories. For local loading, point at the plugin subdirectory. |
| Python too old or unavailable | Run a Python 3.10+ interpreter available to Claude's terminal. On Windows, `py -3` may be appropriate; check its version. The plugin does not install Python. |
| Cannot write workspace | Choose an existing dedicated writable directory, confirm the destination, and keep normal tool approvals. Do not escalate filesystem permissions automatically. |
| Symlink/path rejected | Use a direct directory path without symlinks or `..`. Traversal protection is intentional. |
| Session already exists | Use status/resume or a new session ID. Never overwrite or automatically delete an interrupted session. |
| Revision conflict | Reload status and reconcile the pending event. Do not force a stale write. |
| Duplicate event | Identical envelopes are idempotent. A changed payload needs a new ID after reconsideration. |
| Artifact warning after apply | Canonical state may already be committed. Check status and run render; do not repeat with a new event ID. |
| Write error with uncertain commit | Check status. Retry the identical event envelope if necessary; idempotency prevents a second mutation after a post-rename interruption. |
| Interrupted write | Ignore orphan temp files; read canonical state and regenerate with render. Preserve corrupt canonical data for inspection; stale JSONL is not authoritative. |
| HTML has no terminal preview | Open the returned architecture.html path in a local browser. No browser launch or server is required. |
| Dilemma not eligible | Check current design, operation purpose/order, phase, prior exploration, and active dilemma; do not force an unrelated incident. |

## Contributing / License Status

Focused contributions should preserve learner control, hypothetical framing,
original scenario content, primary-source scope, and deterministic safety tests.
Changes to the installed protocol/source catalog must match the approved copies;
packaging tests detect drift. Adding a scenario requires reviewing its facts,
provenance, declarative predicates, version compatibility, and regression/manual
cases; the v0.1 loader intentionally supports only the coupon scenario.

**License selection is pending.** No MIT or other license has been applied.
The owner must choose an explicit license to clarify public distribution and reuse
permissions. Third-party source links do not grant rights to redistribute those works.
