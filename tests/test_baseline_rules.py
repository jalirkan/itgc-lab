"""The four configuration-baseline rules, each against data that trips it
and data that must not.

Same shape as tests/test_access_rules.py: a clean population passes every
rule with a non-empty examined population, each planted class is caught by
the rule designed for it, and every refusal path renders inconclusive with
its reason recorded rather than a pass (D-005/D-008/D-011).
"""

import copy
import unittest

from baseline.engine import BaselineView, run_baseline_review
from baseline.rules import BASELINE_RULES
from core.stats import EXCEPTION, INCONCLUSIVE, PASS
from enterprise.violations import CLASSES, inject
from tests.helpers import default_enterprise

FULL_PLAN = {cls: 2 for cls in CLASSES}
SEED = "cfg-001"


def results_by_id(ent):
    return {r.rule_id: r for r in run_baseline_review(ent)}


def manifest_ids(manifest, cls, key):
    out = set()
    for v in manifest["violations"]:
        if v["class"] == cls:
            out.update(v["refs"].get(key, []))
    return out


class CleanPopulationPasses(unittest.TestCase):
    def test_all_rules_pass_with_nonzero_populations(self):
        for rid, res in results_by_id(default_enterprise()).items():
            self.assertEqual(res.outcome, PASS, (rid, res.refusal_reason))
            self.assertEqual(len(res.findings), 0, rid)
            self.assertGreater(res.population_n, 0, rid)
            self.assertIsNone(res.refusal_reason, rid)

    def test_populations_partition_the_settings_export(self):
        ent = default_enterprise()
        results = results_by_id(ent)
        setting_pop = sum(results[rid].population_n
                          for rid in ("CFG-PWD", "CFG-HARD", "CFG-MFA"))
        self.assertEqual(setting_pop, len(ent["configs"]["settings"]))
        self.assertEqual(results["CFG-ENRL"].population_n,
                         len(ent["configs"]["mfa_enrolments"]))


class PlantedConditionsAreCaught(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean = default_enterprise()
        cls.planted, cls.manifest = inject(cls.clean, FULL_PLAN, SEED)
        cls.results = results_by_id(cls.planted)

    def _flagged(self, rid):
        out = set()
        for f in self.results[rid].findings:
            out.update(f.record_ids)
        return out

    def test_designed_rule_catches_each_config_class(self):
        for rid, cls_name, key in [
            ("CFG-PWD", "config.password_policy_drift", "config_ids"),
            ("CFG-HARD", "config.hardening_drift", "config_ids"),
            ("CFG-MFA", "config.mfa_not_enforced", "config_ids"),
            ("CFG-ENRL", "config.mfa_enrolment_gap", "enrolment_ids"),
        ]:
            planted = manifest_ids(self.manifest, cls_name, key)
            self.assertEqual(len(planted), 2, cls_name)
            self.assertEqual(self.results[rid].outcome, EXCEPTION, rid)
            self.assertTrue(planted <= self._flagged(rid),
                            "{0} missed {1}".format(rid, cls_name))

    def test_no_rule_flags_a_record_it_was_not_planted_to_find(self):
        """Record-level precision on this planted population, checked
        here as well as on the card: everything flagged is named by the
        manifest, so the clean rows around the plants stay clean."""
        planted = set()
        for key in ("config_ids", "enrolment_ids"):
            for v in self.manifest["violations"]:
                planted.update(v["refs"].get(key, []))
        flagged = set()
        for res in self.results.values():
            for f in res.findings:
                flagged.update(f.record_ids)
        self.assertTrue(flagged)
        self.assertEqual(flagged - planted, set())

    def test_enforcement_drift_does_not_excuse_the_enrolment_population(self):
        """CFG-ENRL reads the STATED standard, not the per-system switch
        (D-019). A system whose MFA requirement has drifted off must not
        take its own accounts out of scope — otherwise one planted class
        would silently mask another."""
        off_systems = {v["refs"]["system"]
                       for v in self.manifest["violations"]
                       if v["class"] == "config.mfa_not_enforced"}
        self.assertTrue(off_systems)
        ent = copy.deepcopy(self.planted)
        # Force every system's privileged-MFA switch off, then re-plant
        # nothing: the enrolment rule must still examine every row and
        # still flag exactly the planted gaps.
        for row in ent["configs"]["settings"]:
            if row["setting"] == "mfa_required_for_privileged":
                row["value"] = False
        res = results_by_id(ent)["CFG-ENRL"]
        self.assertEqual(res.outcome, EXCEPTION)
        self.assertEqual(res.population_n,
                         len(ent["configs"]["mfa_enrolments"]))
        flagged = set()
        for f in res.findings:
            flagged.update(f.record_ids)
        self.assertEqual(
            flagged,
            manifest_ids(self.manifest, "config.mfa_enrolment_gap",
                         "enrolment_ids"))


class StricterThanRequiredIsNotALead(unittest.TestCase):
    """The direction in the stated standard is what the rules compare
    against; a system tightened beyond it satisfies the standard."""

    def test_tightening_every_numeric_setting_flags_nothing(self):
        ent = copy.deepcopy(default_enterprise())
        tightened = {"password_min_length": 32, "password_history_depth": 50,
                     "password_max_age_days": 1,
                     "account_lockout_threshold": 1,
                     "session_idle_timeout_minutes": 1}
        for row in ent["configs"]["settings"]:
            if row["setting"] in tightened:
                row["value"] = tightened[row["setting"]]
        for rid in ("CFG-PWD", "CFG-HARD"):
            res = results_by_id(ent)[rid]
            self.assertEqual(res.outcome, PASS, rid)

    def test_loosening_by_one_is_a_lead(self):
        """The comparison is not a courtesy margin: one unit past the
        stated ceiling or below the stated floor is a lead."""
        ent = copy.deepcopy(default_enterprise())
        target = next(r for r in ent["configs"]["settings"]
                      if r["setting"] == "password_min_length")
        target["value"] = 11
        res = results_by_id(ent)["CFG-PWD"]
        self.assertEqual(res.outcome, EXCEPTION)
        self.assertEqual([f.record_ids for f in res.findings],
                         [(target["config_id"],)])
        self.assertIn("at least 12", res.findings[0].rationale)


class RefusalsRenderInconclusive(unittest.TestCase):
    def _view_outcomes(self, ent):
        from core.rules import run_rules
        return {r.rule_id: r for r in run_rules(BASELINE_RULES,
                                                BaselineView(ent))}

    def test_missing_stated_standard_refuses_every_rule(self):
        ent = copy.deepcopy(default_enterprise())
        del ent["policy"]["config_standard"]
        for rid, res in self._view_outcomes(ent).items():
            self.assertEqual(res.outcome, INCONCLUSIVE, rid)
            self.assertIn("stated configuration standard is absent",
                          res.refusal_reason)

    def test_missing_configs_export_refuses_every_rule(self):
        ent = copy.deepcopy(default_enterprise())
        del ent["configs"]
        for rid, res in self._view_outcomes(ent).items():
            self.assertEqual(res.outcome, INCONCLUSIVE, rid)
            self.assertIn("baseline export is absent", res.refusal_reason)

    def test_empty_population_refuses_rather_than_passes(self):
        ent = copy.deepcopy(default_enterprise())
        ent["configs"]["settings"] = []
        ent["configs"]["mfa_enrolments"] = []
        for rid, res in self._view_outcomes(ent).items():
            self.assertEqual(res.outcome, INCONCLUSIVE, rid)
            self.assertIn("nothing was examined", res.refusal_reason)

    def test_uninterpretable_requirement_refuses(self):
        ent = copy.deepcopy(default_enterprise())
        ent["policy"]["config_standard"]["password_min_length"] = {
            "require": "roughly", "value": 12}
        res = self._view_outcomes(ent)["CFG-PWD"]
        self.assertEqual(res.outcome, INCONCLUSIVE)
        self.assertIn("cannot interpret", res.refusal_reason)
        # The rules that do not read that setting still run.
        self.assertEqual(self._view_outcomes(ent)["CFG-MFA"].outcome, PASS)

    def test_standard_that_does_not_require_mfa_makes_enrolment_moot(self):
        """Inapplicability is an outcome (D-005): if the organization's
        own standard does not require MFA for privileged access, this
        procedure has no criterion — and says so instead of passing."""
        ent = copy.deepcopy(default_enterprise())
        ent["policy"]["config_standard"]["mfa_required_for_privileged"] = {
            "require": "enabled", "value": False}
        res = self._view_outcomes(ent)["CFG-ENRL"]
        self.assertEqual(res.outcome, INCONCLUSIVE)
        self.assertIn("does not require MFA", res.refusal_reason)

    def test_setting_absent_from_the_standard_is_a_coverage_lead(self):
        """The same shape ACC-AUTH uses for a job function missing from
        the authorization matrix: unstated is not a pass."""
        ent = copy.deepcopy(default_enterprise())
        del ent["policy"]["config_standard"]["password_max_age_days"]
        res = self._view_outcomes(ent)["CFG-PWD"]
        self.assertEqual(res.outcome, EXCEPTION)
        self.assertTrue(res.findings)
        for f in res.findings:
            self.assertTrue(f.detail.get("standard_gap"))
            self.assertIn("states no requirement", f.rationale)


class ResultContract(unittest.TestCase):
    def test_results_are_deterministic_and_complete(self):
        a = [r.to_dict() for r in run_baseline_review(default_enterprise())]
        b = [r.to_dict() for r in run_baseline_review(default_enterprise())]
        self.assertEqual(a, b)
        self.assertEqual([r["rule_id"] for r in a],
                         [rule.rule_id for rule in BASELINE_RULES])
        for r in a:
            self.assertTrue(r["criterion"])
            self.assertTrue(r["population_desc"])
            self.assertTrue(r["limitations"])
            # The applied slice of the stated standard is echoed, so a
            # workpaper says what it measured against (D-008).
            self.assertTrue(r["thresholds_used"])

    def test_findings_carry_reviewable_rationales(self):
        planted, _ = inject(default_enterprise(), FULL_PLAN, SEED)
        for res in run_baseline_review(planted):
            for f in res.findings:
                self.assertTrue(f.rationale)
                self.assertTrue(f.record_ids)
                self.assertEqual(res.rule_id, f.rule_id)
                self.assertTrue(f.subject)


if __name__ == "__main__":
    unittest.main()
