# ITGC Monitoring Lab

Third of a trilogy: [ai-audit-toolkit](../ai-audit-toolkit) audits AI systems,
[audit-automation-lab](../audit-automation-lab) automates financial-statement
audit procedures — this lab automates **IT general controls** testing, the
day-to-day substance of IT audit: user access reviews, segregation of duties,
and change management. Demonstrated entirely on synthetic enterprise data and
graded against planted ground truth, so the lab's own detection rates are
measured, never asserted.

**The thesis:** access reviews are the most repetitive, most sampled, most
quietly-botched procedure in IT audit. A quarterly review that eyeballs 40 of
9,000 access grants is theater; software can reconcile all 9,000 against the
HR roster and the SoD matrix every night — but only earns trust by publishing
its recall and false-positive rates against populations where the violations
are known by construction.

## What it will do (see PLAN.md)

- **Synthetic enterprise generator** — deterministic, seeded fixtures that
  hang together: an HR roster with joiners/movers/leavers over time, IAM
  access exports (users × roles × systems) consistent with that roster, a
  change-ticket log with approvals and deploy records, and config snapshots.
  A planted-violation injector whose manifest is the only ground truth.
- **Access-review engine** — terminated-but-active accounts, orphaned
  accounts, dormant privileged access, role/job-function mismatches against a
  data-driven authorization matrix, toxic-combination SoD conflicts, shared
  and service-account hygiene, recertification staleness.
- **Change-management engine** — changes without approval, developer-approves-
  own-change, emergency changes missing post-hoc review, deploys with no
  ticket (log-vs-ticket reconciliation), change-freeze violations.
- **Detection report card** — recall by planted violation class, precision,
  false positives per 10k grants, across seeds, with Wilson intervals.
- **Continuous mode** — monthly snapshot deltas: new grants since last review,
  exception aging, recert tracking, population drift.
- **Workpapers** — population, procedure, criterion, exceptions, limitations,
  conclusion-as-lead; references to COBIT / ISO 27001 / NIST CSF control IDs
  as original one-line summaries, plus CISA Domain 5 topic tags — this lab
  doubles as study material for its author.

## Principles

Inherited deliberately from both siblings: stdlib-only Python, offline and
deterministic (seeds everywhere), synthetic data only — never a real export
from any employer system in any form — uncertainty mandatory on every rate,
three outcomes (pass / exception / inconclusive), flags are leads for auditor
judgment, and no copyrighted framework text (IDs and original summaries only).

*Educational/professional tooling on synthetic data; not production security
software.*
