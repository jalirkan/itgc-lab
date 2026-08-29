# Build Plan — ITGC Monitoring Lab

Phased roadmap for mostly-autonomous execution. Each phase ends with passing
tests and a commit. Before any code, read BOTH sibling decision ledgers end to
end — `../ai-audit-toolkit/DECISIONS.md` and
`../audit-automation-lab/DECISIONS.md`. They solved this repo's shared
problems (uncertainty enforcement, canonical determinism, planted-truth
grading, leads-not-conclusions language, inapplicability as an outcome).
**Borrow decisions, not code** — re-implement cleanly, cite the sibling
decision numbers in this repo's DECISIONS.md when adopting one.

## Conventions

- Python stdlib only; unit tests per module; `python -m unittest discover -s
  tests -t .` green before every commit; deterministic seeds everywhere
  (string-seeded per-stream RNGs, per lab D-007/D-010).
- Synthetic data only, forever. Nothing resembling a real employer export.
- Every rate is a Measurement with interval + n; three-outcome decisions.
- Framework text: COBIT / ISO 27001 / NIST CSF referenced by control ID with
  original one-line summaries only. CISA Domain 5 topic tags likewise original.
- Renderer language guard: leads, indicators, exceptions — never conclusory
  security verdicts ("breach", "compromised") as determinations.

## Architecture

```
itgc-lab/
  enterprise/    synthetic org: roster, IAM exports, tickets, deploy log, configs
  enterprise/violations.py   planted-violation injector + manifest (ground truth)
  access/        access-review rule engine
  change/        change-management rule engine
  core/          measurement/decision stats, canonical encoding (re-implemented)
  reportcard/    recall/precision vs manifest, multi-seed, intervals
  continuous/    snapshot deltas, exception aging, recert tracking
  frameworks/    control-ID summaries + rule→control map + Domain 5 tags
  report/        workpapers, lead sheet, report card render (md + html)
  cli.py         generate · review · reportcard · continuous · report
  tests/
```

## Phase 0 — Synthetic enterprise
- Roster: employees with hire/transfer/termination dates, departments, job
  functions; movers keep history. IAM export: per-system grants (role, granted
  date, last-used date, grantor) that are CONSISTENT with the roster by
  construction. Ticket log: changes with requester/approver/deployer/dates.
  Authorization matrix: job function → allowed roles (data file).
- Injector with its own RNG stream and a manifest naming every planted
  violation and why (per lab D-009/D-010: no positional artifacts, clean
  population byte-identical with or without plants).
- The clean population contains documented benign look-alikes (per lab D-008):
  a rehire (looks terminated-but-active without date care), sanctioned
  cross-functional grants with recorded exceptions, weekend emergency changes
  WITH proper post-approval. Base rates pinned by test.
- Tests: same seed → byte-identical exports; consistency invariants (no grant
  to never-employed user in clean data); benign base rates pinned.

## Phase 1 — Access-review engine
- Rules (each: population, criterion, per-finding rationale, limitations,
  `applicable()` refusal per lab D-011): terminated-but-active (with grace
  window), never-employed/orphaned, dormant privileged (last-used vs
  threshold), role-vs-function mismatch against the matrix (recorded
  exceptions honored), toxic combinations from an SoD matrix data file,
  shared/service account policy checks, recert staleness.
- Tests: each rule against a fixture that triggers and one that doesn't;
  the rehire benign case must NOT trigger the terminated rule.

## Phase 2 — Change-management engine
- Rules: approval missing, approver==developer (SoD), emergency change
  without post-hoc review within N days, deploy-log entries with no matching
  ticket (reconciliation), ticket without deploy (stale/undeployed —
  review lead, not violation), change during freeze windows.
- Tests: as Phase 1, including the benign proper-emergency case.

## Phase 3 — Detection report card
- Recall per planted class, precision, FP per 10k grants/tickets, pooled
  across ≥5 seeds with per-seed stability; Wilson intervals; inconclusive on
  thin pools. A deliberately broken rule must show degraded recall (report
  card catches regressions).

## Phase 4 — Continuous mode
- Monthly snapshot pairs: delta review (new grants, new privileged, newly
  dormant), exception aging (how long has each open lead existed), recert
  cycle tracking, population drift profile.
- Tests: planted month-over-month deltas detected; aging math exact.

## Phase 5 — Frameworks + workpapers
- Control catalog data files (original summaries; rule→control map; Domain 5
  topic tags per rule), coverage report naming unmapped controls.
- Workpapers per rule + engagement lead sheet + report card, md + standalone
  html; language guard test; every percentage carries n.

## Phase 6 — CLI + end-to-end example
- `cli.py` commands wired; `examples/run-001/`: a ~5,000-employee,
  ~40,000-grant, 18-month enterprise with ~50 planted violations across
  classes — committed manifest, findings, workpaper pack, report card
  (large raw exports gitignored, regenerated byte-identically from seed).
- README quick-start updated with real output.

## Stretch
- ~~Config-baseline checks (password/MFA policy snapshots vs stated
  policy).~~ Done: baseline engine, four planted classes, DECISIONS.md
  D-019.
- Cross-system correlation (same human, different account ids — matching as a
  labelled lexical screen).
- Optional LLM explainer, adapter-gated as in the toolkit: narrative summaries
  of findings, never detection.

## Definition of done (v1)
One command generates a coherent synthetic enterprise with planted
violations; one command runs both engines and emits workpapers, lead sheet,
and a report card demonstrating stated recall per class with intervals; the
continuous mode diffs two months and ages exceptions. Everything offline,
deterministic, reviewable.
