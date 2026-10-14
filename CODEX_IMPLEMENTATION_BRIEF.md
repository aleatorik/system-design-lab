# Codex Implementation Brief — System Design Lab v0.1

> Paste this document into Codex in VS Code, **after opening a new empty folder** for the project. Attach or copy the companion files `README.md`, `docs/SIMULATION_PROTOCOL_v0.1.md`, and `docs/SOURCE_CATALOG.md` into that folder first. Do not pretend any implementation exists before creating and testing it.

## Role

Act as a senior software engineer implementing a small, safe, maintainable **Claude Code plugin**, not a hosted application. Follow the companion **Simulation Protocol v0.1** as the product and behavioral contract. Implement an MVP that another developer can clone, inspect, install, and practice with.

## Objective

Implement a local-first conversational system-design practice plugin named `system-design-lab` with one manual-invocation Skill `/system-design-lab:simulate`, one well-developed fictional `coupon-flash-sale` scenario, deterministic session-state validation, decision journal, Mermaid + standalone HTML visualization, and qualitative reflection reports. Distribution must use a GitHub-hostable Claude Code plugin marketplace as described in official documentation.

**Do not develop a Next.js app, API backend, database, Docker stack, MCP server, complex multi-agent orchestration, or subscriptions.** Keep first-use setup and runtime dependencies minimal.

## Context and priority order

1. Read `docs/SIMULATION_PROTOCOL_v0.1.md` fully.
2. Read `docs/SOURCE_CATALOG.md`; do not fabricate source claims.
3. Read `README.md`; keep its intended user experience and honest limitations.
4. Prefer official references if a plugin syntax has changed:
   - https://code.claude.com/docs/en/plugins/create
   - https://code.claude.com/docs/en/plugin-marketplaces
   - https://code.claude.com/docs/en/skills
5. Where instructions are ambiguous, choose the simplest correct secure behavior; document the decision in `docs/IMPLEMENTATION_NOTES.md` and continue. Ask for confirmation only where essential to safety or public repository ownership.

## Deliverable repository structure

```text
.
├── .claude-plugin/marketplace.json
├── plugins/system-design-lab/
│   ├── .claude-plugin/plugin.json
│   └── skills/simulate/
│       ├── SKILL.md
│       ├── references/simulation-protocol.md
│       ├── references/evaluation-rubric.md
│       ├── references/state-schema.md
│       ├── scenarios/coupon-flash-sale.json
│       ├── scripts/session_cli.py
│       └── assets/report-template.md
├── tests/
│   ├── test_session_cli.py
│   └── fixtures/
├── docs/
│   ├── SIMULATION_PROTOCOL_v0.1.md
│   ├── SOURCE_CATALOG.md
│   └── IMPLEMENTATION_NOTES.md
├── README.md
├── .gitignore
└── LICENSE (only after license choice is confirmed)
```

You may add small supporting modules *inside* the plugin if essential for clarity, but avoid unnecessary abstraction. Do not create dummy modules to satisfy the tree.

## Phase A — Plugin packaging

- Marketplace file at repository root `.claude-plugin/marketplace.json`:
  - `name`: `system-design-lab-marketplace`
  - `owner`: use maintainer placeholder until explicitly provided; do not invent the author's identity.
  - `plugins`: a single item `name: system-design-lab`, `source: ./plugins/system-design-lab`.
- Plugin manifest at `plugins/system-design-lab/.claude-plugin/plugin.json`:
  - `name: system-design-lab`; concise description, `version: 0.1.0`, valid metadata.
- Skill frontmatter:

```yaml
---
name: simulate
description: Run an interactive educational software system-design simulation with design decisions, evidence-grounded dilemmas, and reflection.
disable-model-invocation: true
---
```

- One Skill only; no shared global hooks. Skill refers to files using resolvable paths inside the installed plugin, not the developer's repo root.
- Explicit start via `/system-design-lab:simulate`.
- Avoid absolute paths to the developer machine. For runtime script location, use documented skill/plugin path substitution or instructions enabling the agent to resolve the installed skill directory. Verify this in a real Claude Code environment rather than hardcoding a speculative path.
- Keep `SKILL.md` concise (ideally <= 200 lines) and put detailed rules in `references/`.

## Phase B — Educational protocol behavior

Use the six phases and four protocol decisions verbatim in meaning, not necessarily in wording. Specific acceptance cases:

- First turn is a friendly, short briefing with the required fictional nature notice, written-directory notice, and **one** question.
- Never claim learner's architecture is wrong solely for omitting Redis, Kafka, microservices, or a queue.
- When learner asks a clarifying question, reveal a defined scenario fact if available, otherwise say it is undefined and ask whether to assume a value.
- Ask for reasoning before teaching the answer; offer `none/nudge/focused/explanation` hint levels.
- When a user chooses PostgreSQL-only, do not activate a Redis/DB inconsistency event.
- When a user chooses Redis + Postgres with a reservation-then-persist path, a cross-store failure dilemma becomes *eligible*. State explicitly that it is hypothetical.
- If a novel architecture doesn't match a known branch, continue using generic invariants, state ownership, failure boundaries and validation questions.
- Handle pause/resume, inspect assumptions, finish early, compare alternatives, and explicit revision without losing the journal.
- Cite source-backed engineering principles accurately, link external documents as references only; don't scrape sources at runtime.

## Phase C — Python standard-library persistence + validation

Implement `session_cli.py` with `argparse`, `json`, `pathlib`, `tempfile` or `os.replace`, `uuid`, `datetime` and `unittest` only. No `pip` install.

Required commands (small justified variations allowed): `init`, `status`, `apply`, `eligible`, `render`, `report`.

`apply` receives a JSON change file; it must NOT interpret prompts, evaluate arbitrary expressions, or write paths outside the session workspace. Use a strict allowlist of change types and fields. Bind operations to the current revision. Validate state transitions, event prerequisites, one-active-dilemma rule and immutable event IDs.

Crash consistency matters: a snapshot and append-only event journal cannot be made atomic with a single rename. Define the journal as the recoverable source of truth (or use a single canonical atomic state file plus regenerable derived event material). Implement a recovery/reconciliation approach and test it. Do not claim crash-proof persistence without evidence.

Avoid overwriting sessions, prevent traversal and symlink escape, and be honest about v0.1's single-writer boundary. Confirm filesystem destination before initializing. Use a `--workspace` argument so plugin cache is never used for learner session data.

**Provenance field:** `documented_principle | fictional_scenario_fact | user_assumption | hypothetical_consequence | tool_measured | unknown`. For v0.1, `tool_measured` must never be set for performance characteristics unless a real measuring tool has been run and its output is recorded. Validate against the enum.

For CLI outputs, prefer concise JSON to stdout and human-readable errors to stderr, with non-zero exit codes on failure. Never swallow file errors or silently corrupt state.

## Phase D — Scenario and source grounding

Create `coupon-flash-sale.json` from the protocol, with explicit business assumptions and several optional scenario facts to reveal. Put **only short original paraphrases** of the engineering principles in the scenario; link to references in source catalog. Use the facts as sources for Socratic probes, not as an answer key that forces one architecture. Data-driven event preconditions must be checked by the script, not only by the Skill's prose.

Document how a new scenario can be added safely without arbitrary script execution.

## Phase E — Educational artifacts

Generate on every confirmed design revision:

- `journal.md` with event-linked decision summary and rationale.
- `architecture.mmd` showing only declared architecture components and connections. Escape/quote unsafe Mermaid labels correctly; if input is ambiguous, render a neutral placeholder rather than guessing.
- `architecture.html`: a standalone offline HTML/CSS/JS file showing current components, design revision history and the last dilemma. No CDN, tracking, fonts, inline execution of untrusted user text, or remote scripts. Use escaped text/textContent for user-controlled values. Provide accessible headings and sensible keyboard navigation. A responsive timeline + simple boxes/arrows is enough; no framework required.
- `reflection.md` with qualitative evidence-linked feedback, open assumptions and cited next-reading links. Do not fabricate transcript quotes, scores, throughput or benchmark numbers. If no behavior was observed, mark `not-observed` / `not-assessed`.

A successful render step must tell user where each output is written and how to open it. Visual HTML is read-only with respect to Claude Code chat; no false promise of live bidirectional communication.

## Phase F — Tests and validation

Implement Python `unittest` covering at least:

1. marketplace and manifest parse as JSON, names match paths/skill names;
2. valid setup and valid/invalid phase progression, pause, resume, partial finish;
3. no stress-test before any assessable design hypothesis;
4. Redis branch excluded for PostgreSQL-only state and included only for a matching two-store operation;
5. unknown architecture gracefully uses generic fallback without unrelated incident claim;
6. event IDs unique; revisions monotonic; duplicate `apply` rejected/idempotent;
7. no writes outside workspace or through malicious path/symlink;
8. simulated persistence interruption followed by clean recovery;
9. report mirrors real stored events and doesn't invent decisions;
10. HTML injection attempts rendered as text, not executed;
11. correct, stable provenance labels in event data;
12. source catalog links refer to primary documents and are not presented as evidence for a hypothetical measured outcome.

Add a `tests/manual-evals.md` describing:
- at least six complete example learner paths, including invalid assumptions and surprising decisions;
- what a reviewer should inspect;
- A/B comparison with ordinary Claude chat;
- failure criteria (invented metrics, misleading source claims, lost decisions, overleading questions).

If Claude Code executable is available locally, run the actual `claude plugin validate .` and a clean-path `claude --plugin-dir ./plugins/system-design-lab` smoke test. If absent, report **not run** and include exact manual instructions; do not claim it passed. Python unit tests must be executed and their results summarized.

## Phase G — Public README and packaging

Preserve the English README's mission, plain-chat comparison, limitations, licensing caution and end-user walkthrough. After implementing, update its status from *in progress* only for features actually tested. Fill repo owner placeholder **only after the user tells you the target GitHub owner**; do not invent or publish a URL. Provide install commands:

```bash
claude plugin marketplace add OWNER/system-design-lab
claude plugin install system-design-lab@system-design-lab-marketplace
```

And actual invocation in Claude Code:

```text
/system-design-lab:simulate
```

Add a short `Troubleshooting` section (plugin not found, Python unavailable, cannot write workspace, no HTML preview) and a local development test procedure. Add `.gitignore` for `.system-design-lab/`, caches and Python build artifacts. Propose an open-source license but do not invent legal ownership or redistribute third-party article content.

## Execution plan

1. Inspect repo and documentation, list tasks briefly.
2. Implement smallest valid plugin scaffold and JSON scenario.
3. Implement validated session CLI with tests; run tests.
4. Implement Skill content and examples; check its paths, questions and fallback logic.
5. Add outputs, safe HTML renderer and associated tests.
6. Finish README and developer notes.
7. Validate plugin and walkthrough where tools allow.
8. Deliver an **implementation report** with file list, tests run, what remains unverified, notable trade-offs and exact manual steps for the user to test with Claude Code.

**Definition of done:** A new developer can follow the README to install the published plugin, invoke `/system-design-lab:simulate`, explore one realistic fictional coupon scenario using at least two valid architecture paths, save and resume a session, see coherent local artifacts, and receive a factual, evidence-linked reflection without confusing LLM hypotheses with measured system behavior. If clean-install integration could not be tested, explicitly label the milestone as *implementation complete, installation unverified* rather than fully done.
