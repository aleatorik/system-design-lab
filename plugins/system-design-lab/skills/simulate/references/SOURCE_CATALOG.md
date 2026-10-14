# System Design Lab — Research Source Catalog v0.1

**Verified against publicly reachable source pages:** 2026-10-14.  
**Scope:** curated *primary sources* for original educational scenario writing, not a mirror of third-party incident reports. This catalog records **why a source is relevant**; it does not establish the truth of an invented exercise.

## Required disclaimer for all scenario packs

> All scenarios are fictional educational exercises inspired by documented engineering principles and selected public case studies. A source may support a general failure mode or design trade-off without demonstrating that it happened in the fictional environment. We do not claim to reproduce any company's architecture, incidents, or performance results.

## Source classification

- **Actual incident report (I):** a first-party postmortem describing a real event in a specific organization. Facts apply to the documented incident only.
- **First-party engineering case study (C):** an organization describes its engineering approach or observed trade-offs; not necessarily an incident.
- **Vendor engineering guidance (G):** design advice backed by the authoring company; may have technology-specific assumptions.
- **Official implementation reference (D):** authoritative semantics of a particular technology, not a proof of an entire system's behavior.
- **Methodology and practice reference (M):** methods for review, questioning, testing, or evidence-based learning.

## Curated sources

| ID | Type | Owner / link | Grounded insight | Possible fictional exercise (not a claim about original system) |
|---|---|---|---|---|
| S01 | C | [Shopify Engineering — Surviving Flashes of High-Write Traffic, Part I](https://shopify.engineering/surviving-flashes-of-high-write-traffic-using-scriptable-load-balancers-part-i) | A first-party account of managing very high checkout demand, queueing and customer experience trade-offs. | High-traffic coupon release; graceful admission control; fairness versus waiting time. |
| S02 | G | [Stripe Engineering — Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency) | Ambiguous network outcomes, request deduplication, safe retries and jitter. | Client retries a coupon or purchase operation after losing response. |
| S03 | G | [Amazon Builders' Library — Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | Idempotency contracts across multi-step workflows; retry safety requires deliberate server behavior. | A timed-out reservation command may already have succeeded. |
| S04 | G | [Amazon Builders' Library — Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Retrying can amplify load; timeouts/backoff/jitter must be reasoned about as a system. | Spike turns into retry storm while a dependency is degraded. |
| S05 | D | [PostgreSQL — Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html) | Scope, duration and interaction of locks, including row-level locks. | Compare atomic DB stock update, lock contention and transaction boundaries. |
| S06 | D | [PostgreSQL — Data consistency checks at application level](https://www.postgresql.org/docs/current/applevel-consistency.html) | Techniques for preserving consistency under concurrent updates and their limitations. | Learner identifies which operation must be atomic and what invariant to enforce. |
| S07 | D | [Redis — Transactions](https://redis.io/docs/latest/develop/using-commands/transactions/) | Serialization and transaction behavior of Redis commands; scripts as an option. | Local counter/reservation operation versus cross-store persistence gap. |
| S08 | I | [GitHub Engineering — October 21 post-incident analysis (2018)](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/) | Network partition, database replication topology, recovery choices and prioritization of data integrity. | A *different fictional* multi-region product faces divergent data and difficult recovery trade-offs. |
| S09 | I | [Cloudflare — Details of the outage on July 2, 2019](https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/) | Rule rollout, unexpected CPU exhaustion and operational response; one rule can have system-wide consequences. | A hypothetical dynamic validation rule triggers broad performance degradation. |
| S10 | G | [Stripe Engineering — Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters) | Rate limiting strategies and protecting availability under abnormal demand. | Compare admission control, fairness, retry policies and product UX. |
| S11 | M | [AWS — Well-Architected Framework Review](https://docs.aws.amazon.com/wellarchitected/latest/userguide/wa-framework-review.html) | Preparation, review and improvement around architecture trade-offs and workload context. | Compose non-leading review questions and follow-up evidence. |
| S12 | M | [AWS — Workload and scope](https://docs.aws.amazon.com/wellarchitected/latest/userguide/workload-and-scope.html) | Assess boundaries, dependencies and impact before selecting technology. | Initial problem-framing checkpoints. |
| S13 | M | [Anthropic — Skill Creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | Iterate with representative tasks, human feedback and with/without-skill comparisons. | Build behavioral evaluations for consistent simulation protocol. |

## MVP source-to-scenario map

**Scenario:** `coupon-flash-sale` — fictional startup promotion, 1,000 coupons, assumed 10,000 RPS peak. These numbers are **invented exercise assumptions**, not figures taken from Shopify or Stripe.

| Dilemma | Sources | Supported principle | Fabricated exercise component |
|---|---|---|---|
| Admission control at promotion launch | S01, S10 | Demand spikes can require traffic-shaping and UX choices. | Coupon sale, user segmentation and estimated peak load. |
| Concurrent issuance / data integrity | S05, S06, S07 | Distinct storage systems offer specific atomicity/locking behaviors. | Inventory size, fairness and invented user arrival pattern. |
| Response loss and retries | S02, S03, S04 | A response may be lost after server-side success; retries need designed guarantees. | User reports timeout after hypothetical coupon reservation. |
| Redis-to-PostgreSQL persistence gap | S05, S07, S03 | Each system's local guarantees alone do not establish an atomic cross-store transaction. | A fictitious failure between Redis reservation and DB recording. |
| Growth beyond initial design | S11, S12 | Review architecture against evolving business priorities and dependencies. | New team size, deadline and changed rules. |

**Important caveat:** S07 does not itself document a Redis/PostgreSQL production incident. The Redis-to-DB incident is a **hypothetical cross-system consistency exercise**, not a real-world incident attributed to Redis, Shopify, or any other company.

## Example scenario metadata and citation policy

```json
{
  "id": "ambiguous-retry",
  "provenance": "hypothetical_consequence",
  "premise": "A client may have lost the reply after a successful server commit",
  "premise_sources": ["S02", "S03"],
  "scenario_specific_outcome": "not_measured",
  "prompt": "Suppose the client times out after the server has committed a coupon. What happens if it retries?"
}
```

- Cite stable canonical URLs, issuer, title and publication year when available. Record when they were checked.
- Cite precisely: do not imply a source verified a fictional metric, a simulated outcome, or another company's implementation.
- Treat authors' recommendations as advice; describe constraints and alternatives.
- Write original educational prompts and summaries; link to originals rather than copying full text, diagrams, or licensed code.
- For every new scenario, maintain at least one primary reference for each material **documented** technical assertion; facts about a made-up company are labeled scenario assumptions.
- Do not retrieve or refresh websites automatically during a simulation. Updating this catalog is an explicit maintainer action with source review.

## Intake checklist for future sources

- [ ] Original publisher or primary maintainer; URL accessible and relevant.
- [ ] Source type accurately labeled (incident/case/guidance/docs/methodology).
- [ ] Exact claim and scope documented; vendor recommendation not generalized blindly.
- [ ] Fictional business details explicitly separated from reported facts.
- [ ] Diverse possible designs and user-level learning prompts recorded.
- [ ] No copied proprietary diagrams or large excerpts.
- [ ] At least one adversarial review question created ("In what conditions would this lesson not apply?").
