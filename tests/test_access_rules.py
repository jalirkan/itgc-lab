import copy
import unittest

from access.engine import AccessView, run_access_review
from access.rules import ACCESS_RULES
from core.stats import EXCEPTION, INCONCLUSIVE, PASS
from enterprise.violations import CLASSES, inject
from tests.helpers import default_enterprise

FULL_PLAN = {cls: 2 for cls in CLASSES}
SEED = "plant-001"

RULE_BY_ID = {r.rule_id: r for r in ACCESS_RULES}


def results_by_id(ent):
    return {r.rule_id: r for r in run_access_review(ent)}


def manifest_ids(manifest, cls, key="grant_ids"):
    out = set()
    for v in manifest["violations"]:
        if v["class"] == cls:
            out.update(v["refs"].get(key, []))
    return out


class CleanPopulationPasses(unittest.TestCase):
    """Zero findings on clean data — the benign look-alikes (rehires,
    sanctioned exceptions) must not trip anything (D-004/D-009)."""

    def test_all_rules_pass_with_nonzero_populations(self):
        for rid, res in results_by_id(default_enterprise()).items():
            self.assertEqual(res.outcome, PASS, (rid, res.refusal_reason))
            self.assertEqual(len(res.findings), 0, rid)
            self.assertGreater(res.population_n, 0, rid)
            self.assertIsNone(res.refusal_reason, rid)


class PlantedViolationsAreCaught(unittest.TestCase):
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

    def test_designed_rule_catches_each_access_class(self):
        for rid, cls_name in [
            ("ACC-TERM", "access.terminated_active"),
            ("ACC-ORPH", "access.orphan_account"),
            ("ACC-DORM", "access.dormant_privileged"),
            ("ACC-AUTH", "access.role_mismatch"),
            ("ACC-SVC", "access.service_account_no_owner"),
            ("ACC-CERT", "access.recert_lapsed"),
        ]:
            planted = manifest_ids(self.manifest, cls_name)
            self.assertEqual(len(planted), 2, cls_name)
            self.assertEqual(self.results[rid].outcome, EXCEPTION, rid)
            self.assertTrue(planted <= self._flagged(rid),
                            "{0} missed {1}".format(rid, cls_name))

    def test_sod_rule_catches_planted_conflicts(self):
        planted_users = {v["refs"]["user_id"]
                         for v in self.manifest["violations"]
                         if v["class"] == "access.sod_conflict"}
        flagged_users = {f.subject for f in self.results["ACC-SOD"].findings}
        self.assertEqual(planted_users, flagged_users)
        planted_grants = manifest_ids(self.manifest, "access.sod_conflict")
        self.assertTrue(planted_grants <= self._flagged("ACC-SOD"))

    def test_no_stray_findings_beyond_plants(self):
        """Every access finding on planted data traces to a manifest entry
        (entry-level precision 1.0 here; the injected world contains no
        accidental violations)."""
        all_planted = set()
        for v in self.manifest["violations"]:
            all_planted.update(v["refs"].get("grant_ids", []))
        for rid in ("ACC-TERM", "ACC-ORPH", "ACC-DORM", "ACC-AUTH",
                    "ACC-SOD", "ACC-SVC", "ACC-CERT"):
            stray = self._flagged(rid) - all_planted
            self.assertEqual(stray, set(), rid)

    def test_rehires_never_flagged_as_terminated(self):
        """The trap: rehired employees appear in the termination report AND
        hold active access. The rule must use the latest stint."""
        rehired = {e["employee_id"]
                   for e in self.planted["roster"]["employees"]
                   if any(ev["event"] == "rehire" for ev in e["history"])}
        self.assertTrue(rehired)
        term_subjects = {f.subject for f in self.results["ACC-TERM"].findings}
        self.assertEqual(rehired & term_subjects, set())

    def test_sanctioned_exceptions_honored(self):
        register_keys = {(x["user_id"], x["system"], x["role"])
                         for x in self.planted["exceptions"]["exceptions"]}
        self.assertTrue(register_keys)
        for f in self.results["ACC-AUTH"].findings:
            key = (f.subject, f.detail["role"].split(":")[0],
                   f.detail["role"].split(":")[1])
            self.assertNotIn(key, register_keys)


class ExpiredExceptions(unittest.TestCase):
    def test_expired_register_entry_no_longer_covers(self):
        ent = copy.deepcopy(default_enterprise())
        x = ent["exceptions"]["exceptions"][0]
        x["expires_at"] = "2026-06-01"  # before the 2026-06-30 snapshot
        res = results_by_id(ent)["ACC-AUTH"]
        self.assertEqual(res.outcome, EXCEPTION)
        flagged = {f.subject for f in res.findings}
        self.assertIn(x["user_id"], flagged)
        the_finding = next(f for f in res.findings if f.subject == x["user_id"])
        self.assertIn("expired", the_finding.rationale)


class RefusalsAreInconclusive(unittest.TestCase):
    """A rule that cannot run says so — never a silent pass (D-005/D-008,
    per lab D-011 and toolkit D-020)."""

    def test_missing_threshold_refuses(self):
        ent = copy.deepcopy(default_enterprise())
        del ent["policy"]["thresholds"]["dormant_privileged_days"]
        res = results_by_id(ent)["ACC-DORM"]
        self.assertEqual(res.outcome, INCONCLUSIVE)
        self.assertIn("dormant_privileged_days", res.refusal_reason)
        self.assertEqual(len(res.findings), 0)

    def test_empty_population_refuses(self):
        ent = copy.deepcopy(default_enterprise())
        ent["iam"]["grants"] = [g for g in ent["iam"]["grants"]
                                if g["account_type"] == "user"]
        res = results_by_id(ent)["ACC-SVC"]
        self.assertEqual(res.outcome, INCONCLUSIVE)
        self.assertIn("population is empty", res.refusal_reason)

    def test_empty_roster_refuses_reconciliation(self):
        ent = copy.deepcopy(default_enterprise())
        ent["roster"]["employees"] = []
        res = results_by_id(ent)["ACC-ORPH"]
        self.assertEqual(res.outcome, INCONCLUSIVE)
        self.assertIn("roster", res.refusal_reason.lower())

    def test_refusal_never_passes_anywhere(self):
        ent = copy.deepcopy(default_enterprise())
        ent["policy"]["thresholds"] = {}
        for res in run_access_review(ent):
            self.assertIn(res.outcome, (PASS, EXCEPTION, INCONCLUSIVE))
            if res.refusal_reason is not None:
                self.assertEqual(res.outcome, INCONCLUSIVE, res.rule_id)


class ResultContract(unittest.TestCase):
    def test_results_are_deterministic_and_complete(self):
        a = [r.to_dict() for r in run_access_review(default_enterprise())]
        b = [r.to_dict() for r in run_access_review(default_enterprise())]
        self.assertEqual(a, b)
        self.assertEqual([r["rule_id"] for r in a],
                         [rule.rule_id for rule in ACCESS_RULES])
        for r in a:
            self.assertTrue(r["criterion"])
            self.assertTrue(r["population_desc"])
            self.assertTrue(r["limitations"])

    def test_findings_carry_reviewable_rationales(self):
        planted, _ = inject(default_enterprise(), FULL_PLAN, SEED)
        for res in run_access_review(planted):
            for f in res.findings:
                self.assertTrue(f.rationale)
                self.assertTrue(f.record_ids)
                self.assertIn(res.rule_id, f.rule_id)


if __name__ == "__main__":
    unittest.main()
