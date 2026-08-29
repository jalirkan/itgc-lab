import copy
import unittest

from access.engine import run_access_review
from continuous.deltas import age_leads, as_of, compare_snapshots
from core.canonical import canonical_bytes
from core.stats import INCONCLUSIVE
from enterprise import dates
from enterprise.violations import inject
from tests.helpers import default_enterprise

PRIOR_OFFSET = 200  # days before the generated snapshot


def prior_day(ent):
    return dates.add_days(ent["policy"]["snapshot"], -PRIOR_OFFSET)


class AsOfReducer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ent = default_enterprise()
        cls.day = prior_day(cls.ent)
        cls.prior = as_of(cls.ent, cls.day)

    def test_future_records_do_not_exist_yet(self):
        for g in self.prior["iam"]["grants"]:
            self.assertLessEqual(g["granted_date"], self.day)
            self.assertLessEqual(g["last_used_date"], self.day)
            if g["last_certified_date"] is not None:
                self.assertLessEqual(g["last_certified_date"], self.day)
            if g["status"] == "disabled":
                self.assertLessEqual(g["disabled_date"], self.day)
        for t in self.prior["tickets"]["tickets"]:
            self.assertLessEqual(t["created_at"], self.day)
            if t["approved_at"] is not None:
                self.assertLessEqual(t["approved_at"], self.day)
        for d in self.prior["deploys"]["deploys"]:
            self.assertLessEqual(d["deployed_at"], self.day)
        for e in self.prior["roster"]["employees"]:
            self.assertLessEqual(e["hire_date"], self.day)
            for ev in e["history"]:
                self.assertLessEqual(ev["date"], self.day)

    def test_late_disablement_is_still_active_at_prior(self):
        """A grant disabled AFTER the prior day must show as active then."""
        flipped = [
            g["grant_id"] for g in self.ent["iam"]["grants"]
            if g["status"] == "disabled" and g["disabled_date"] > self.day
            and g["granted_date"] <= self.day]
        self.assertTrue(flipped, "fixture never exercises the flip")
        prior_by_id = {g["grant_id"]: g for g in self.prior["iam"]["grants"]}
        for gid in flipped:
            self.assertEqual(prior_by_id[gid]["status"], "active")
            self.assertIsNone(prior_by_id[gid]["disabled_date"])

    def test_termination_after_prior_day_not_yet_visible(self):
        later_terms = [
            e for e in self.ent["roster"]["employees"]
            if e["termination_date"] and e["termination_date"] > self.day
            and e["hire_date"] <= self.day]
        self.assertTrue(later_terms)
        prior_by_id = {e["employee_id"]: e
                       for e in self.prior["roster"]["employees"]}
        for e in later_terms:
            self.assertEqual(prior_by_id[e["employee_id"]]["status"],
                             "active")

    def test_snapshot_field_and_guard(self):
        self.assertEqual(self.prior["policy"]["snapshot"], self.day)
        with self.assertRaises(ValueError):
            as_of(self.ent, dates.add_days(self.ent["policy"]["snapshot"], 1))

    def test_reducer_is_deterministic(self):
        again = as_of(self.ent, self.day)
        for name in ("roster", "iam", "tickets", "deploys", "exceptions",
                     "policy"):
            self.assertEqual(canonical_bytes(again[name]),
                             canonical_bytes(self.prior[name]))


class SnapshotComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean = default_enterprise()
        plan = {"access.sod_conflict": 2, "access.role_mismatch": 2,
                "access.orphan_account": 2}
        cls.planted, cls.manifest = inject(cls.clean, plan, "cont-001")
        cls.prior = as_of(cls.planted, prior_day(cls.planted))
        cls.diff = compare_snapshots(cls.prior, cls.planted)

    def test_window_math(self):
        self.assertEqual(self.diff["window"]["days"], PRIOR_OFFSET)
        self.assertEqual(self.diff["window"]["to"],
                         self.planted["policy"]["snapshot"])

    def test_added_grants_appear_as_new(self):
        """SoD/mismatch plants are granted 20-150 days before the current
        snapshot — inside the 200-day window, so every one must appear in
        the delta's new-grant list."""
        added = set()
        for v in self.manifest["violations"]:
            if v["class"] in ("access.sod_conflict", "access.role_mismatch"):
                added.add(v["refs"].get("added_grant_id")
                          or v["refs"]["grant_ids"][0])
        self.assertEqual(len(added), 4)
        self.assertTrue(added <= set(self.diff["grants"]["new"]))
        by_id = {g["grant_id"]: g for g in self.planted["iam"]["grants"]}
        expected_priv = sorted(
            gid for gid in self.diff["grants"]["new"]
            if by_id[gid]["privileged"])
        self.assertEqual(self.diff["grants"]["new_privileged"], expected_priv)

    def test_new_counts_are_exact(self):
        prior_ids = {g["grant_id"] for g in self.prior["iam"]["grants"]
                     if g["status"] == "active"}
        current_ids = {g["grant_id"] for g in self.planted["iam"]["grants"]
                       if g["status"] == "active"}
        self.assertEqual(self.diff["grants"]["new_n"],
                         len(current_ids - prior_ids))
        self.assertEqual(self.diff["grants"]["removed_n"],
                         len(prior_ids - current_ids))

    def test_terminations_in_window(self):
        expected = [t for t in self.planted["roster"]["terminations"]
                    if t["termination_date"] > prior_day(self.planted)]
        self.assertEqual(self.diff["terminations_in_window"], expected)

    def test_profile_deltas_are_exact_arithmetic(self):
        prof = self.diff["population_profile"]
        for key, delta in prof["delta"].items():
            self.assertEqual(delta, prof["current"][key] - prof["prior"][key],
                             key)
        self.assertIn("/", prof["current"]["privileged_share"])

    def test_comparison_is_deterministic(self):
        again = compare_snapshots(self.prior, self.planted)
        self.assertEqual(canonical_bytes(again), canonical_bytes(self.diff))

    def test_order_guard(self):
        with self.assertRaises(ValueError):
            compare_snapshots(self.planted, self.prior)


class NewlyDormant(unittest.TestCase):
    def test_pinned_newly_dormant_case(self):
        """last_used = prior_day - 80: at the prior snapshot that is 80
        days (not dormant, threshold 90); at the current snapshot it is
        280 days (dormant). Exactly this grant must be newly dormant."""
        ent = copy.deepcopy(default_enterprise())
        day = prior_day(ent)
        target = next(g for g in ent["iam"]["grants"]
                      if g["privileged"] and g["status"] == "active"
                      and g["granted_date"] < dates.add_days(day, -100))
        target["last_used_date"] = dates.add_days(day, -80)
        prior = as_of(ent, day)
        diff = compare_snapshots(prior, ent)
        self.assertIn(target["grant_id"],
                      diff["newly_dormant_privileged"]["ids"])
        # And its dormancy is not retroactive: not dormant at prior.
        prior_target = next(g for g in prior["iam"]["grants"]
                            if g["grant_id"] == target["grant_id"])
        self.assertEqual(
            dates.days_between(prior_target["last_used_date"], day), 80)

    def test_recert_coming_due_pinned_case(self):
        ent = copy.deepcopy(default_enterprise())
        day = prior_day(ent)
        cycle = ent["policy"]["thresholds"]["recert_cycle_days"]
        target = next(g for g in ent["iam"]["grants"]
                      if g["status"] == "active"
                      and g["granted_date"] < dates.add_days(
                          ent["policy"]["snapshot"], -(cycle - 10)))
        target["last_certified_date"] = dates.add_days(
            ent["policy"]["snapshot"], -(cycle - 10))
        diff = compare_snapshots(as_of(ent, day), ent)
        self.assertIn(target["grant_id"],
                      diff["recertification"]["coming_due_ids"])
        self.assertNotIn(target["grant_id"],
                         diff["recertification"]["lapsed_ids"])


class LeadAging(unittest.TestCase):
    def test_exact_new_persisting_resolved_math(self):
        ent = default_enterprise()
        planted, manifest = inject(
            ent, {"access.orphan_account": 2, "access.recert_lapsed": 2},
            "age-001")
        day = prior_day(planted)
        prior_results = run_access_review(as_of(planted, day))
        current_results = run_access_review(planted)
        aging = age_leads(prior_results, current_results, PRIOR_OFFSET)

        self.assertEqual(aging["counts"]["open"],
                         aging["counts"]["new"]
                         + aging["counts"]["persisting"])
        # Every planted lead is open at the current snapshot.
        planted_grants = set()
        for v in manifest["violations"]:
            planted_grants.update(v["refs"]["grant_ids"])
        open_ids = set()
        for lead in aging["open_leads"]:
            open_ids.update(lead["record_ids"])
        self.assertTrue(planted_grants <= open_ids)
        for lead in aging["open_leads"]:
            if lead["status"] == "persisting":
                self.assertEqual(lead["min_age_days"], PRIOR_OFFSET)
            else:
                self.assertEqual(lead["min_age_days"], 0)
        self.assertIn("lower bounds", aging["note"])

    def test_handmade_resolution(self):
        from core.rules import Finding, RuleResult
        mk = lambda rid, gid: RuleResult(
            rule_id=rid, title="t", outcome="exception",
            findings=(Finding(rule_id=rid, record_ids=(gid,), subject="s",
                              rationale="r"),),
            population_n=1, population_desc="d", criterion="c",
            limitations=(), thresholds_used={})
        prior = [mk("R1", "G-a"), mk("R2", "G-b")]
        current = [mk("R1", "G-a")]
        aging = age_leads(prior, current, 30)
        self.assertEqual(aging["counts"],
                         {"open": 1, "new": 0, "persisting": 1,
                          "resolved": 1})
        self.assertEqual(aging["resolved_leads"][0]["record_ids"], ["G-b"])


class ConfigBaselineIsNotTimeTravelled(unittest.TestCase):
    """The configuration baseline carries no history, so an as-of view
    has none either — and the baseline rules must say so rather than
    grade the current settings as if they had been sampled a month ago
    (D-008/D-019)."""

    def test_reduced_export_has_no_configs_artifact(self):
        ent = default_enterprise()
        prior = as_of(ent, dates.add_days(ent["policy"]["snapshot"], -60))
        self.assertNotIn("configs", prior)
        self.assertIn("configs", ent)

    def test_baseline_rules_refuse_on_a_reduced_export(self):
        from baseline.engine import run_baseline_review
        ent = default_enterprise()
        prior = as_of(ent, dates.add_days(ent["policy"]["snapshot"], -60))
        for res in run_baseline_review(prior):
            self.assertEqual(res.outcome, INCONCLUSIVE, res.rule_id)
            self.assertIn("baseline export is absent", res.refusal_reason)


if __name__ == "__main__":
    unittest.main()
