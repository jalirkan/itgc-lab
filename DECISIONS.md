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

## D-010 · 2026-07-27 · Stats core: Wilson from the formula, attribute rule at both poles
Implements D-005 structurally (per toolkit D-008/D-011/D-012, lab D-015):
`Measurement.proportion()` is the only constructor and refuses to exist
without interval, method, confidence, and n; `render()` always includes n;
n=0 renders "not tested", never "0%"; boundary counts pin their bound to
exactly 0.0 or 1.0. z comes from `statistics.NormalDist.inv_cdf`, computed,
not transcribed (lab D-005's formulas-not-tables), and pinned by test.
`decide()` compares the interval to the threshold with three outcomes;
`min_sample` gates only the pass. The zero-tolerance switch to attribute
sampling applies at BOTH poles — threshold 0.0 when lower is better and
1.0 when higher is better — because a perfection floor on recall has the
same pathology toolkit D-012 fixed for leak rates: no finite sample's
Wilson interval reaches the boundary.

## D-011 · 2026-07-27 · One rule base owns the outcome logic
`core/rules.py` gives both engines the same contract: a rule declares its
population, criterion, limitations, required thresholds, and the planted
classes it is designed for; the base class computes the outcome, so no rule
can invent a fourth outcome or turn a refusal into a pass. Census framing
throughout (lab D-014, toolkit D-031): findings are exact facts about a
fully-examined population, with population_n on the result. Refusal cases —
missing threshold (per toolkit D-020: missing config means refuse, not
default), empty population (nothing examined is not evidence the control
operated), absent artifact — all render inconclusive with the reason
recorded. The rehire trap is tested from the roster's own termination
report: ACC-TERM evaluates the LATEST stint, and a test asserts rehired
employees are never among its subjects.

## D-012 · 2026-07-27 · The manifest names every constituent record
Found by the first precision test: the SoD rule correctly implicates both
grants of a toxic pair, but the manifest initially listed only the added
one, which would have graded the pre-existing half as a false positive.
Per lab D-019 (pair originals count as planted), a manifest entry now
carries ALL constituent record ids — for SoD, the added grant plus the
counterpart half — with `added_grant_id` kept separately for provenance.
Ground truth describes the violation, not the edit.

## D-013 · 2026-07-27 · Emergency semantics are split across two rules
"Approved after deployment" is the EXPECTED shape of an emergency change,
and the same shape is a deficiency for a normal one — so CHG-APPR flags
absent approval for everything but post-dated approval only for
non-emergencies, while CHG-EMER owns the emergency-specific criterion
(post-hoc review present, timely, and not by the developer). This is the
same scoping lesson as lab D-012 (period-end means the reporting period,
not every month-end): the documented benign pressure — weekend emergencies
with proper review, D-004 — must sit inside some rule's population and
still not be flagged, or precision claims are hollow. Stale approved-but-
undeployed tickets render explicitly as review leads, not control
exceptions, and the rationale text says so.

## D-014 · 2026-07-27 · Card definitions pinned; precision 1.0 must be earned, and is explained
Report-card definitions live in one docstring, are restated in output, and
are locked by a hand-computed test (per lab D-019): detected = any rule
flags any constituent id (designed-rule recall alongside); precision is
record-level on planted populations; FP rates come from clean populations
where every flag is by construction false (D-009), per 10k records. Pools
span seeds with per-seed rows shown; thin pools decide INCONCLUSIVE (lab
D-020), and the default plan is sized so 5 seeds × 7 = 35 pooled is the
smallest all-caught pool whose Wilson lower bound clears the 0.9 floor —
one seed fewer and perfection is still inconclusive, asserted by test.

Unlike the JE lab (lab D-020 reports precision 0.36 as a feature), correct
ITGC rules SHOULD score precision 1.0 on this data: these are deterministic
reconciliations, not fuzzy screens, and the clean world is consistent by
construction. What keeps 1.0 from being hollow is that the benign
look-alikes punish wrong implementations, not correct ones — a test runs a
NAIVE flat-termination join against clean data and proves it false-positives
on exactly the rehires (toolkit D-017: limitations kept in executable form).
The card is also the regression detector (lab D-021): a test removes
ACC-DORM and the dormant class drives to an exception while intact classes
stay caught. No composite score; overall outcome by precedence (toolkit
D-016). No wall-clock timestamps; identity is seeds + config echo.
