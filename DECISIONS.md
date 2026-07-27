# Decision Ledger

Append as you go. Cite sibling decisions (toolkit = ../ai-audit-toolkit,
lab = ../audit-automation-lab) by number when adopting them.

## D-001 · 2026-07-27 · Synthetic data only, forever
No real employer or client export enters this repo in any form — not
anonymized, not restructured, not "just the schema". The enterprise generator
is the only data source. (Per lab D-001; the stakes are higher here because
access data is inherently sensitive.)

## D-002 · 2026-07-27 · Planted truth grades every detector
Every rule is scored against populations whose violations are known by
construction, via a manifest the detectors can never see positionally.
(Per lab D-002/D-009/D-010.)

## D-003 · 2026-07-27 · Leads, not conclusions — and not security verdicts
Findings are leads for auditor follow-up. Renderer guard rejects conclusory
determinations; additionally rejects incident language ("breach",
"compromised") — an access anomaly is an audit exception, not an incident
declaration. (Extends lab D-003.)

## D-004 · 2026-07-27 · Benign look-alikes are mandatory in clean data
Rehires, sanctioned cross-functional grants with recorded exceptions, and
properly-reviewed emergency changes exist in the clean population so that
precision numbers mean something. (Per lab D-008.)

## D-005 · 2026-07-27 · Inherited uncertainty + inapplicability discipline
Measurements with Wilson intervals enforced at construction; three-outcome
decisions against the interval; rules may refuse with a reason and refusal
renders inconclusive, never pass. (Per toolkit D-008/D-011, lab D-011/D-015.)

## D-006 · 2026-07-27 · Determinism is canonical bytes + string-seeded streams
One pinned JSON encoding (sorted keys, tight separators, ASCII, NaN rejected,
LF file endings) with a known-vector test; "same seed → same enterprise" is
asserted as byte equality of written files, verified across processes and
under a changed PYTHONHASHSEED. Every component draws from its own
`Random("{seed}/{stream}")` — CPython hashes str seeds via SHA-512, stable
across platforms — with first draws pinned by test. (Per toolkit D-009, lab
D-007; re-implemented in core/, no cross-repo imports.)

## D-007 · 2026-07-27 · No positional artifacts, via natural-key ids
Lab D-009 hid plants by merge-then-shuffle before issuing sequential ids.
This repo reaches the same guarantee differently: every record id is a
content hash of its natural key (employee identity, account × role × grant
date, ticket coordinates), so mutations preserve ids, planted additions get
format-identical ids that interleave under canonical sorting, and no id
encodes sequence position at all. The injector draws only from
"{seed}/violations" (per lab D-010) and works on a deep copy: tests assert
the clean population is byte-identical with or without an injection run, and
that planted grants neither lead, trail, nor cluster in the sorted export.
The manifest remains the only record of ground truth (D-002).

## D-008 · 2026-07-27 · The world is snapshot-dated; policy is data
No generator or injector code path reads the wall clock — the enterprise is
a pure function of (config, committed data files, code version), which is
what makes regeneration byte-identical (per lab D-019's no-timestamp
identity). Control thresholds (termination grace, transfer cleanup, dormancy,
recert cycle, emergency-review SLA, stale-ticket age) ship as an enterprise
artifact (policy.json), not as constants inside rules: Phase 1+ rules read
the population's own policy and refuse when a threshold is absent (per lab
D-011 / toolkit D-020 — a missing configuration means refuse, not assume).
Freeze windows are likewise data, derived as quarter-end spans.

## D-009 · 2026-07-27 · Plants are single-property; base rates are zero
Each planted class introduces exactly the property its manifest note claims
and no other (a reactivated terminated account gets a fresh certification so
it cannot double as a recert lapse; planted ghost deploys land on business
days outside freezes). Where overlap is intrinsic — an added SoD role is
usually also off-matrix — the manifest note names it. Tests re-derive every
property independently: each manifest entry must exhibit its property in the
planted data (per lab D-010's property tests), and the same predicates must
find ZERO records in clean data, next to the benign look-alikes that sit
deliberately adjacent (D-004). That zero base rate is what makes Phase 3
precision numbers attributable to rules, not to generator noise.
