# Validation record — v0.1

Date: 2026-10-15 (Asia/Seoul). Local interpreter: CPython 3.10.19 already installed
on the development host. The default python3 is 3.9.6; commands below were run
using the installed Python 3.10 interpreter explicitly. No dependencies were installed.

| Check | Actual result | Boundary |
|---|---|---|
| `python3.10 -m unittest discover -s tests -v` | PASS: 41 tests | Local deterministic behavior only |
| `python3.10 tests/smoke_session.py` | PASS: 22 events, 2 design revisions, completed report | Real CLI subprocesses, synthetic learner input; no LLM |
| Marketplace/manifest JSON, names, Skill frontmatter, bundled paths | PASS in unit tests | Not official Claude validation |
| Approved protocol/catalog copies | PASS in unit tests | Exact bytes, no packaging drift |
| PostgreSQL, linked Redis, queue, and unfamiliar architecture paths | PASS in unit tests | Declared-structure consistency |
| Atomic write before/after rename, derived recovery, corrupt canonical refusal | PASS in unit tests | Injected interruptions on local filesystem |
| Traversal, symlink directory/output/change-file, existing session protection | PASS in unit tests | Not adversarial cross-process filesystem racing |
| HTML/Markdown/Mermaid injection escaping | PASS in unit tests | Unsafe strings and parsed HTML structure |
| HTML revision selection JavaScript | PASS in Node v25.2.1 VM with a minimal DOM stub | Not a real browser integration test |
| CSP hashes match emitted script/style bytes | PASS in a local parser/hash check | Browser enforcement not tested here |
| Runtime static execution audit | PASS: no eval/exec/compile/dynamic import calls | Static check of bundled Python scripts |
| Publication file/secret-pattern audit | PASS: 22 eligible files; no matching keys, sessions, symlinks, caches, or local configuration | Pattern-based review, not a universal secret detector |
| GitHub Actions on commit cf39a689ae9fba451e529d10c629c22478263084 | PASS: Python 3.10, 3.12, and 3.13 jobs; unit suite and CLI smoke successful in all three | Remote Linux verification; no Claude CLI tests |
| `claude plugin validate ./plugins/system-design-lab` | NOT RUN: command unavailable (exit 127) | No Claude CLI installed |
| `claude plugin validate .` | NOT RUN: command unavailable (exit 127) | No Claude CLI installed |
| `claude --plugin-dir ./plugins/system-design-lab` and live skill dialogue | NOT RUN | Claude CLI/authenticated conversation unavailable |
| Clean marketplace install | NOT RUN | Must be tested in a user's Claude environment |
| Human non-leading dialogue/source accuracy/A-B learning evaluation | NOT RUN | See tests/manual-evals.md |
| Browser layout, accessibility, actual local-file CSP behavior, Mermaid viewer | NOT RUN | Manual review remains |

The first suite run had one failure: excessive Markdown escaping made an event ID
hard to search. It was corrected and rerun successfully. Additional recovery and
security regressions brought the suite to 41 passing tests. No unresolved test
failure is knowingly left in the local suite.

## Reproduce local verification

Use Python 3.10+ available to your shell:

```sh
python3 -m unittest discover -s tests -v
python3 tests/smoke_session.py
```

The smoke test normally uses a disposable directory and deletes its synthetic
records when finished. For inspection, explicitly choose a dedicated empty folder:

```sh
mkdir smoke-practice
python3 tests/smoke_session.py --workspace ./smoke-practice
```

Do not commit generated sessions. This path checks local state, decisions, a
PostgreSQL-relevant dilemma, revision, pause/resume, artifact files, and reflection.
It is not a transcript of `/system-design-lab:simulate` or proof of educational benefit.

## Release checks

Before push, review the exact staged file list and run a secret-pattern/file audit.
Use only the authorized repository and normal fast-forward push. GitHub Actions
configuration exists for Python 3.10/3.12/3.13. All three jobs' unit and smoke steps
passed in [the observed remote run](https://github.com/aleatorik/system-design-lab/actions/runs/38606145670)
on commit cf39a689ae9fba451e529d10c629c22478263084. This is separate from local testing
and does not establish live Claude integration. Documentation-only follow-up commits
do not change the runtime tested by that run.

The implementation commit is f27b557. A subsequent owner commit, cf39a68, updates
README to declare MIT and adds an ignore entry; it is preserved. No LICENSE file
exists in the tracked tree. Confirming and adding the complete intended license,
fresh installation, real Claude conversation, browser review, and user evaluations
remain release follow-ups. The owner README change is not overwritten.
