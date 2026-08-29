# ITGC Monitoring Lab

Third of a trilogy: [ai-audit-toolkit](https://github.com/jalirkan/ai-audit-toolkit) audits AI systems,
[audit-automation-lab](https://github.com/jalirkan/audit-automation-lab) automates financial-statement
audit procedures — this lab automates **IT general controls** testing, the
day-to-day substance of IT audit: user access reviews, segregation of duties,
change management, and configuration baselines. Demonstrated entirely on synthetic enterprise data and
graded against planted ground truth, so the lab's own detection rates are
measured, never asserted.

**The thesis:** access reviews are the most repetitive, most sampled, most
quietly-botched procedure in IT audit. A quarterly review that eyeballs 40 of
9,000 access grants is theater; software can reconcile all 9,000 against the
HR roster and the SoD matrix every night — but only earns trust by publishing
its recall and false-positive rates against populations where the violations
are known by construction.

## Quick start

Python 3.10+, standard library only, no install, no network.

```
python -m unittest discover -s tests -t .      # the full suite
python cli.py generate --seed demo --out /tmp/demo --plant-all 2
python cli.py review --dir /tmp/demo --out /tmp/demo-review
python cli.py reportcard --out /tmp/demo-card  # 5 seeds x 7 per class
python cli.py continuous --dir /tmp/demo --prior-days 30 --out /tmp/demo-cont
python cli.py example                          # rebuild examples/run-001
```

## What it is

- **Synthetic enterprise generator** — deterministic, string-seeded
  per-stream RNGs; an HR roster with joiners/movers/leavers/rehires, IAM
  exports consistent with that roster by construction, change tickets and a
  deploy log with freeze windows, an authorization matrix, an SoD matrix, an
  exceptions register, and a policy artifact carrying every threshold. Same
  seed, same bytes — verified across processes.
- **Planted-violation injector** — 17 violation classes on an isolated RNG
  stream; the manifest is the only ground truth; ids carry no positional
  artifact; each plant introduces exactly one property.
- **Access-review engine** — terminated-but-active (rehire-safe), orphaned
  accounts, dormant privileged access, role-vs-matrix mismatches honoring
  recorded exceptions (with expiry), SoD toxic pairs, service/shared account
  ownership, recertification staleness.
- **Change-management engine** — deployed without approval, self-approval,
  emergency changes without timely independent review, deploys with no
  ticket, freeze-window deploys, stale approved tickets (review leads).
- **Config-baseline engine** — each system's recorded password policy,
  lockout and session hardening, and MFA enforcement settings compared
  against the standard the organization states for itself (which ships as
  enterprise data, with its comparison direction, not as constants in a
  rule), plus MFA enrolment of every privileged account. A system
  configured stricter than the standard passes; a stated standard that is
  missing, or a requirement this code cannot interpret, refuses.
- **Detection report card** — per-class recall (any-rule and designed-rule),
  record-level precision, clean-population false positives per 10k, pooled
  across seeds, Wilson intervals everywhere, three-outcome decisions; thin
  pools render inconclusive rather than a hollow 100%.
- **Continuous mode** — an as-of reducer derives the prior month from the
  same enterprise; census deltas, newly dormant privileged access, lead
  aging with lower-bound honesty, recert lapse/coming-due tracking.
- **Workpapers** — per-rule workpapers, an engagement lead sheet separating
  exceptions from scope limitations, coverage against COBIT 2019 /
  ISO 27001:2022 / NIST CSF 2.0 (control ids + original one-line summaries,
  verified 2026-07-27; the three configuration controls added 2026-08-28
  carry their own provenance note in DECISIONS.md D-019), CISA outline
  tags (Domain 5A for access, 4A/3B for change, 4A+5A for the baseline
  rules), rendered as Markdown and self-contained HTML whose renderer
  rejects conclusory and incident language.

## Measured, not asserted (examples/run-001)

From the committed example run — regenerate it with `python cli.py example`:

- 5,900-employee roster, 23,545 grants, 703 tickets, 68 planted conditions;
  every one flagged in that single run, with the statistical claim carried
  by the card, not the anecdote.
- Report card at 5 seeds × 7 per class (35 pooled per class, the smallest
  pool whose perfect Wilson lower bound clears the 0.9 floor): all 17
  classes pass.
- Precision 770/770 flagged records planted (95% Wilson 99.5%–100.0%,
  n=770); clean-population flags 0 of 3,660 access records, 0 of 2,118
  change records, and 0 of 2,944 baseline records (upper bounds 10.5,
  18.1, and 13.0 per 10k respectively).
- Precision 1.0 is earned, not free: the clean population deliberately
  contains rehires, sanctioned cross-matrix exceptions, properly-reviewed
  weekend emergencies, systems configured stricter than the stated
  standard, and ordinary accounts with no MFA enrolment. Three tests prove
  the traps are live — a naive termination join false-positives on exactly
  the rehires, an equality check against the standard on exactly the
  stricter settings, and an enrol-everyone check on exactly the ordinary
  accounts.

## Principles

Inherited deliberately from both siblings (see DECISIONS.md, which cites
their ledgers by number): stdlib-only Python, offline and deterministic
(seeds everywhere, no wall clock in any artifact), synthetic data only —
never a real export from any employer system in any form — uncertainty
mandatory on every inferential rate, exact census counts stated with their
populations, three outcomes (pass / exception / inconclusive), findings are
leads for auditor judgment, and no copyrighted framework text (ids and
original summaries only).

*Educational/professional tooling on synthetic data; not production security
software.*
