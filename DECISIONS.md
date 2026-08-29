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

## D-015 · 2026-07-27 · The prior month is derived, not regenerated
Re-running the generator with an earlier snapshot would produce a
DIFFERENT organization (every draw shifts), so continuous mode gets its
pair from one generated enterprise plus an `as_of(ent, day)` reducer that
rebuilds the export the same org would have shown earlier: later events
have not happened, usage/certification caps at the day, approvals dated
later are absent. Two modelling assumptions are stated in the docstring
rather than buried (steady usage; certification reverts to the
provisioning date when the later cert has not happened yet). A consequence
kept deliberately: an as-of view can catch the org MID-SLA — a mover
inside the cleanup window shows residual access — so intermediate-date
rule runs may carry leads the month-end view resolves. That is fidelity,
and lead aging treats it correctly: pair-based ages are LOWER bounds
(persisting = at least the window old), and the output says so. All
deltas, aging counts, and drift-profile numbers are exact census facts
stated with their populations — no intervals, because nothing is inferred
(lab's exact-counts discipline; D-005 attaches intervals to inference
only).

## D-016 · 2026-07-27 · Framework references: verified ids, original words, honest domains
Control identifiers were checked against public framework indexes on
2026-07-27 (ISO/IEC 27001:2022 Annex A titles confirmed via a full
published control list — which caught that A.8.2 is Privileged access
rights, not configuration management; NIST CSF 2.0 subcategory wording
confirmed; COBIT 2019 practice ids cross-referenced). Catalogs store the
id plus an ORIGINAL one-liner, enforced structurally per toolkit D-025:
a 220-character cap and a quoted-span scan, both with companion tests
proving they fire on simulated pastes. Catalogs are partial and say so
(toolkit D-026); a mapping asserts evidence RELEVANCE, never control
satisfaction, and cannot exist without a written rationale (toolkit
D-027); coverage prints each mapped rule's outcome next to the control
and lists unmapped catalog controls rather than omitting them.

Deviation from PLAN, recorded: PLAN asked for "CISA Domain 5 topic tags"
on every rule, but the ISACA outline (as transcribed and verified in the
author's own study system) puts change management in Domain 4A and
release management in 3B. Tags follow the outline, not the project's
framing — mis-tagged study material would be worse than none. Access
rules carry 5A; change rules carry 4A (CHG-FRZ also 3B). Enforced by
test.

## D-017 · 2026-07-27 · Renderer guards: leads-vocabulary, n-on-every-rate, offline HTML
Per lab D-024 and toolkit D-029/D-030, one block model renders to
Markdown and standalone HTML (embedded CSS, no external fetches — and no
percent signs in the stylesheet, adopting the JE lab's lesson where the
scanner flagged its own `width: 100%`). Both renderers refuse documents
containing conclusory determinations OR incident language ("breach",
"compromised", "attacker", "incident" — an access anomaly is an audit
exception, not an incident declaration, extending D-003), with the 13
planted-class identifiers allowlisted verbatim: ground truth may name
what it planted; prose may not conclude it. Any rendered line with a
percent sign must carry n. Companion tests prove every guard fires, in
paragraphs and inside table cells. The guard drew blood during
development: CHG-STAL's own criterion said "control failure" and was
reworded — which is the guard working, recorded here so nobody weakens
it to admit convenient phrasing later. Findings and scope limitations
render in separate lead-sheet sections (toolkit D-032), and workpapers
carry no wall-clock timestamps (lab D-019).

## D-018 · 2026-07-27 · The example regenerates; its README is written by code
`python cli.py example` rebuilds examples/run-001 in independent stages
(generate → review → card → continuous → readme), with the example's
parameters living in cli.py as code. Bulk exports (~11 MB) are gitignored
— pure functions of the seed — while the manifest, findings, workpaper
pack, card, continuous artifacts, and the run README stay committed. Two
tests keep the committed artifacts honest (per lab D-026 and toolkit
D-034): the manifest must regenerate byte-identically from the example
parameters, and the run README's figures must match the artifacts it
describes, because that README is GENERATED from them, never hand-typed.

Scale notes, recorded rather than fudged: PLAN estimated "~40,000 grants"
at 5,000 employees; the coherent org this generator produces yields
23,545 (after adding directory and mail as universal systems for
realism). The README states actuals. The card grades rules on
standard-size populations across 5 seeds — 7 per class, giving the
35-pooled minimum from D-014 — while the large enterprise demonstrates
the same engines at scale in one committed run. Injector pool
construction was made index-backed after the 5,000-employee run exposed
an O(employees × grants) scan; selection order is unchanged and the
whole suite plus byte-identity tests pin that.

## D-019 · 2026-08-28 · Config baseline: the stated standard is the criterion, and the comparison is data
PLAN's stretch item asked for password/MFA snapshots checked against
stated policy. Three choices made it gradeable rather than merely
plausible.

First, the STANDARD ships as enterprise data (`policy.config_standard`),
carrying a requirement VERB next to each value — `at_least`, `at_most`,
`enabled`. Direction had to be data, not code, because the interesting
benign look-alike here is a system configured STRICTER than required (a
16-character password minimum where 12 is stated). An equality check
flags every one of them; a direction-aware check flags none, and a test
proves exactly that misfire, in the shape D-014 used for the rehire trap.
The second look-alike is the ordinary account with no MFA enrolment: the
standard requires MFA for privileged access, so those rows are outside
the criterion, not exceptions to it — and per D-013 they sit INSIDE
CFG-ENRL's population rather than being filtered out of it, because a
temptation nobody is exposed to proves nothing. A missing standard, an
absent export, and a requirement verb this code cannot interpret all
refuse (D-008: missing configuration means refuse, not assume).

Second, CFG-ENRL reads the STATED standard rather than the system's own
MFA switch when deciding whether enrolment is required. Reading the
switch was the obvious implementation and would have let one planted
class mask another — a system whose `mfa_required_for_privileged` had
drifted off would have excused every unenrolled account on it, so
`config.mfa_not_enforced` would have silently suppressed
`config.mfa_enrolment_gap` whenever the two landed on the same system.
It is also the wrong audit criterion: the standard the organization
states is what the population is measured against, and the system's own
setting is evidence about that standard, not a substitute for it.
CFG-MFA owns the switch, CFG-ENRL owns the population, and a test forces
every switch off and asserts the enrolment population is unchanged.

Third, the four planted classes are MUTATIONS of rows the clean
generator already emitted, so every planted record keeps its natural-key
id (D-007) and a test asserts the planted and clean exports carry
identical id lists in identical order, with exactly the manifest's rows
differing. Ground truth is the mutated ROW — `config_ids` /
`enrolment_ids` — never the system it sits on: a manifest naming a
system would grade every setting on that system as a free catch, which
is the whole-population failure D-012 exists to prevent. Class pools
were sized before the roster was fixed: seven settings per system across
six systems gives 18 password rows, 12 hardening rows, 12 MFA-enforcement
rows, and 123 privileged accounts, so the card's 7-per-class-per-seed
plan has a real pool for every class rather than a floor that had to be
lowered to fit.

Recorded rather than smoothed over: adding CFG-ENRL to ISO A.8.2 changed
what a threshold-wipe leaves established there. A.8.2 used to render
inconclusive when ACC-DORM refused; CFG-ENRL, which also evidences it,
needs no scalar threshold and still runs, so the control now renders
no-exceptions-noted. The refusal
test moved to A.6.5, which ACC-TERM evidences alone, and the A.8.2
behaviour is asserted explicitly instead of quietly dropped.

CISA tags straddle two domains for the first time and say why: the
settings these rules read are configuration items (4A, whose verified
topic label literally names Configuration Management), and every one of
those settings governs authentication or access (5A). CFG-ENRL examines
an identity population rather than a configuration item and carries 5A
alone; the test asserts that split per rule rather than per prefix.

Framework identifiers, with the provenance stated honestly: three ISO/IEC
27001:2022 Annex A controls were added — A.5.17 (Authentication
information), A.8.5 (Secure authentication), A.8.9 (Configuration
management). They come from the same published Annex A control list
D-016 worked from. They were added unverified — this lab is offline by
design, so the check could not be run from inside it — and
`identifiers_checked` on controls.json recorded the second date
separately rather than letting the new ids inherit the old verification.

**Verified 2026-08-28, from outside the lab.** All three titles confirmed
against two independent public Annex A indexes: A.5.17 Authentication
information, A.8.5 Secure authentication, A.8.9 Configuration management
— the last new in the 2022 revision, which is consistent with a
configuration-baseline control having no 2013 ancestor. The ids stand as
written and `identifiers_checked` now says so. Worth noting the shape of
this: a claim marked unverified rather than assumed is a claim somebody
can later close, and this one was closed the same day. Nothing else was
added: COBIT and NIST mappings reuse ids already verified in D-016.

The continuous mode deliberately gains nothing. A baseline observed only
at the snapshot has no history to reduce, so `as_of` emits no `configs`
artifact and the baseline rules refuse on a reduced export rather than
carrying today's settings backwards — an absence that reports itself
instead of manufacturing evidence for a date nobody sampled.
