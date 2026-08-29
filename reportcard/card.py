"""Detection report card: rules graded against planted truth.

DEFINITIONS — pinned here, restated in rendered output, and locked by a
hand-computed unit test (per lab D-019; these definitions decide every
number on the card):

- A planted violation is DETECTED (any-rule) when any rule's finding
  flags at least one of the manifest entry's constituent record ids.
- It is DESIGNED-RULE DETECTED when a rule declaring the class in
  `designed_for` does so.
- PRECISION is record-level on the planted population: of the unique
  record ids flagged across all rules, the share that belong to some
  manifest entry. Every constituent of a planted violation counts as
  planted (D-012).
- FALSE-POSITIVE RATES are measured on the CLEAN population, where every
  flagged record id is by construction a false positive (D-009), stated
  per 10,000 population records — grants for the access engine, tickets
  plus deploy-log entries for the change engine, configuration settings
  plus MFA-enrolment rows for the baseline engine.
- Rates POOL across seeds; per-seed rows are reported alongside so a
  pooled number cannot hide an unstable rule. Recall decisions come from
  `decide()` against the interval: thin pools render INCONCLUSIVE rather
  than parading a hollow 100% (per lab D-020).
- No composite score exists, and no wall-clock timestamps appear:
  identity is seeds + config echo (toolkit D-016; lab D-019).
"""

from core.stats import (EXCEPTION, HIGHER_IS_BETTER, INCONCLUSIVE,
                        LOWER_IS_BETTER, PASS, Measurement, decide)
from enterprise import generator
from enterprise.config import GenConfig
from enterprise.violations import CLASSES, inject

CARD_VERSION = "0.1.0"

DEFAULT_N_SEEDS = 5
DEFAULT_RECALL_FLOOR = 0.9
DEFAULT_PLAN = {cls: 7 for cls in CLASSES}
# 5 seeds x 7 = 35 pooled per class: the smallest pool whose all-caught
# Wilson lower bound (0.9011) clears the 0.9 floor. One fewer and a
# perfect record is still INCONCLUSIVE - sized deliberately (lab D-020).

OUTCOME_PRECEDENCE = (EXCEPTION, INCONCLUSIVE, PASS)


def _constituent_ids(refs):
    """Every record id that constitutes one planted violation (D-012).

    Ground truth describes the violation, not the edit: an SoD entry
    carries the pre-existing half of the toxic pair alongside the added
    grant, and a class whose plant is a mutation carries the id of the
    row it mutated. This is the single definition — the card and the
    committed example's README both call it, so the two cannot drift.
    """
    ids = set(refs.get("grant_ids", []))
    ids |= set(refs.get("config_ids", []))
    ids |= set(refs.get("enrolment_ids", []))
    for key in ("ticket_id", "deploy_id"):
        if refs.get(key):
            ids.add(refs[key])
    return ids


def _flagged_by(results):
    """rule_id -> set of flagged record ids; plus the union."""
    per_rule, union = {}, set()
    for res in results:
        ids = set()
        for f in res.findings:
            ids.update(f.record_ids)
        per_rule[res.rule_id] = ids
        union |= ids
    return per_rule, union


def _designed_rules(all_rules):
    out = {}
    for rule in all_rules:
        for cls in rule.designed_for:
            out.setdefault(cls, []).append(rule.rule_id)
    return out


def build_report_card(base_seed="itgc-rc", n_seeds=DEFAULT_N_SEEDS,
                      plan=None, recall_floor=DEFAULT_RECALL_FLOOR,
                      access_rules=None, change_rules=None,
                      baseline_rules=None, config_kwargs=None):
    """Grade the engines across `n_seeds` independently generated
    enterprises. `access_rules`/`change_rules`/`baseline_rules` accept
    rule subsets so a deliberately broken battery can be graded (the
    regression test).
    """
    from access.engine import AccessView
    from access.rules import ACCESS_RULES
    from baseline.engine import BaselineView
    from baseline.rules import BASELINE_RULES
    from change.engine import ChangeView
    from change.rules import CHANGE_RULES
    from core.rules import run_rules

    plan = dict(DEFAULT_PLAN if plan is None else plan)
    access_rules = ACCESS_RULES if access_rules is None else access_rules
    change_rules = CHANGE_RULES if change_rules is None else change_rules
    baseline_rules = (BASELINE_RULES if baseline_rules is None
                      else baseline_rules)
    config_kwargs = config_kwargs or {}
    designed = _designed_rules(tuple(access_rules) + tuple(change_rules)
                               + tuple(baseline_rules))

    per_class = {cls: {"planted": 0, "caught_any": 0, "caught_designed": 0,
                       "per_seed": []}
                 for cls in plan}
    tp = fp_planted = 0
    clean_fp_access = clean_fp_change = clean_fp_baseline = 0
    clean_pop_access = clean_pop_change = clean_pop_baseline = 0
    seeds = []

    for i in range(n_seeds):
        seed = "{0}-{1:03d}".format(base_seed, i + 1)
        seeds.append(seed)
        clean = generator.generate(GenConfig(seed=seed, **config_kwargs))
        planted, manifest = inject(clean, plan, seed)

        results = (run_rules(access_rules, AccessView(planted))
                   + run_rules(change_rules, ChangeView(planted))
                   + run_rules(baseline_rules, BaselineView(planted)))
        per_rule, flagged = _flagged_by(results)

        planted_ids = set()
        for v in manifest["violations"]:
            planted_ids |= _constituent_ids(v["refs"])
        tp += len(flagged & planted_ids)
        fp_planted += len(flagged - planted_ids)

        seed_counts = {cls: [0, 0, 0] for cls in plan}  # planted, any, designed
        for v in manifest["violations"]:
            cls = v["class"]
            ids = _constituent_ids(v["refs"])
            seed_counts[cls][0] += 1
            if ids & flagged:
                seed_counts[cls][1] += 1
            designed_ids = set()
            for rid in designed.get(cls, []):
                designed_ids |= per_rule.get(rid, set())
            if ids & designed_ids:
                seed_counts[cls][2] += 1
        for cls, (n, any_c, des_c) in seed_counts.items():
            agg = per_class[cls]
            agg["planted"] += n
            agg["caught_any"] += any_c
            agg["caught_designed"] += des_c
            agg["per_seed"].append(
                {"seed": seed, "planted": n, "caught_any": any_c,
                 "caught_designed": des_c})

        clean_results_a = run_rules(access_rules, AccessView(clean))
        clean_results_c = run_rules(change_rules, ChangeView(clean))
        clean_results_b = run_rules(baseline_rules, BaselineView(clean))
        _, clean_flagged_a = _flagged_by(clean_results_a)
        _, clean_flagged_c = _flagged_by(clean_results_c)
        _, clean_flagged_b = _flagged_by(clean_results_b)
        clean_fp_access += len(clean_flagged_a)
        clean_fp_change += len(clean_flagged_c)
        clean_fp_baseline += len(clean_flagged_b)
        clean_pop_access += len(clean["iam"]["grants"])
        clean_pop_change += (len(clean["tickets"]["tickets"])
                             + len(clean["deploys"]["deploys"]))
        clean_pop_baseline += (len(clean["configs"]["settings"])
                               + len(clean["configs"]["mfa_enrolments"]))

    classes = []
    for cls in sorted(plan):
        agg = per_class[cls]
        recall_any = Measurement.proportion(
            "recall (any rule): " + cls, agg["caught_any"], agg["planted"],
            direction=HIGHER_IS_BETTER)
        recall_designed = Measurement.proportion(
            "recall (designed rule): " + cls, agg["caught_designed"],
            agg["planted"], direction=HIGHER_IS_BETTER)
        stable = len({(r["planted"], r["caught_any"])
                      for r in agg["per_seed"]}) == 1
        classes.append({
            "class": cls,
            "designed_rules": designed.get(cls, []),
            "planted": agg["planted"],
            "caught_any": agg["caught_any"],
            "caught_designed": agg["caught_designed"],
            "recall_any": recall_any.to_dict(),
            "recall_designed": recall_designed.to_dict(),
            "decision": decide(recall_any, recall_floor).to_dict(),
            "per_seed": agg["per_seed"],
            "per_seed_stable": stable,
        })

    precision = Measurement.proportion(
        "record-level precision on planted populations", tp, tp + fp_planted,
        direction=HIGHER_IS_BETTER)
    fp_access = Measurement.proportion(
        "clean-population false positives (access, per record)",
        clean_fp_access, clean_pop_access, direction=LOWER_IS_BETTER)
    fp_change = Measurement.proportion(
        "clean-population false positives (change, per record)",
        clean_fp_change, clean_pop_change, direction=LOWER_IS_BETTER)
    fp_baseline = Measurement.proportion(
        "clean-population false positives (baseline, per record)",
        clean_fp_baseline, clean_pop_baseline, direction=LOWER_IS_BETTER)

    outcomes = [c["decision"]["outcome"] for c in classes]
    overall = next((o for o in OUTCOME_PRECEDENCE if o in outcomes), PASS)

    return {
        "card_version": CARD_VERSION,
        "definitions": __doc__,
        "identity": {
            "base_seed": base_seed,
            "seeds": seeds,
            "plan": {k: plan[k] for k in sorted(plan)},
            "recall_floor": recall_floor,
            "n_seeds": n_seeds,
            "access_rules": [r.rule_id for r in access_rules],
            "change_rules": [r.rule_id for r in change_rules],
            "baseline_rules": [r.rule_id for r in baseline_rules],
            "config": dict(config_kwargs),
        },
        "classes": classes,
        "precision": precision.to_dict(),
        "clean_false_positives": {
            "access": dict(fp_access.to_dict(),
                           per_10k=_per_10k(fp_access)),
            "change": dict(fp_change.to_dict(),
                           per_10k=_per_10k(fp_change)),
            "baseline": dict(fp_baseline.to_dict(),
                             per_10k=_per_10k(fp_baseline)),
        },
        "outcome_counts": {o: outcomes.count(o)
                           for o in (PASS, EXCEPTION, INCONCLUSIVE)},
        "overall_outcome": overall,
        "overall_note": ("Overall outcome is the worst class outcome by "
                         "precedence exception > inconclusive > pass; "
                         "there is deliberately no composite score."),
    }


def _per_10k(measurement):
    lo, hi = measurement.interval
    return {
        "value": measurement.value * 10000.0,
        "interval": [lo * 10000.0, hi * 10000.0],
        "n": measurement.n,
        "rendered": "{0:.1f} per 10k ({1}% Wilson {2:.1f}-{3:.1f} per 10k, "
                    "n={4})".format(measurement.value * 10000.0,
                                    int(round(measurement.confidence * 100)),
                                    lo * 10000.0, hi * 10000.0,
                                    measurement.n),
    }
