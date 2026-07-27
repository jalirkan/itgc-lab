import copy
import unittest

from change.engine import run_change_review
from change.rules import CHANGE_RULES
from core.stats import EXCEPTION, INCONCLUSIVE, PASS
from enterprise.violations import CLASSES, inject
from tests.helpers import default_enterprise

FULL_PLAN = {cls: 2 for cls in CLASSES}
SEED = "plant-001"


def results_by_id(ent):
    return {r.rule_id: r for r in run_change_review(ent)}


class CleanChangesPass(unittest.TestCase):
    """The properly-reviewed weekend emergencies and the open recent
    tickets are in the clean population precisely to tempt these rules
    (D-004); none of them may surface."""

    def test_all_rules_pass_with_nonzero_populations(self):
        for rid, res in results_by_id(default_enterprise()).items():
            self.assertEqual(res.outcome, PASS, (rid, res.refusal_reason))
            self.assertEqual(len(res.findings), 0, rid)
            self.assertGreater(res.population_n, 0, rid)


class PlantedChangesAreCaught(unittest.TestCase):
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

    def _planted_refs(self, cls_name):
        refs = []
        for v in self.manifest["violations"]:
            if v["class"] == cls_name:
                refs.append(v["refs"])
        self.assertEqual(len(refs), 2, cls_name)
        return refs

    def test_designed_rule_catches_each_change_class(self):
        for rid, cls_name, key in [
            ("CHG-APPR", "change.missing_approval", "ticket_id"),
            ("CHG-SELF", "change.self_approval", "ticket_id"),
            ("CHG-EMER", "change.emergency_no_review", "ticket_id"),
            ("CHG-TICK", "change.deploy_without_ticket", "deploy_id"),
            ("CHG-FRZ", "change.freeze_violation", "deploy_id"),
            ("CHG-STAL", "change.stale_ticket", "ticket_id"),
        ]:
            self.assertEqual(self.results[rid].outcome, EXCEPTION, rid)
            flagged = self._flagged(rid)
            for refs in self._planted_refs(cls_name):
                self.assertIn(refs[key], flagged,
                              "{0} missed {1}".format(rid, cls_name))

    def test_no_stray_findings_beyond_plants(self):
        all_planted = set()
        for v in self.manifest["violations"]:
            for key in ("ticket_id", "deploy_id"):
                if key in v["refs"]:
                    all_planted.add(v["refs"][key])
        for rid in ("CHG-APPR", "CHG-SELF", "CHG-EMER", "CHG-TICK",
                    "CHG-FRZ", "CHG-STAL"):
            stray = self._flagged(rid) - all_planted
            self.assertEqual(stray, set(), rid)

    def test_benign_emergencies_survive_planted_run(self):
        """Clean weekend emergencies (approved after deploy, reviewed in
        time) must not be flagged even while planted emergencies are."""
        clean_emergency_ids = {
            t["ticket_id"] for t in self.clean["tickets"]["tickets"]
            if t["change_type"] == "emergency"}
        self.assertTrue(clean_emergency_ids)
        for rid in ("CHG-APPR", "CHG-EMER", "CHG-SELF"):
            overlap = clean_emergency_ids & self._flagged(rid)
            self.assertEqual(overlap, set(), rid)

    def test_stale_findings_read_as_review_leads(self):
        for f in self.results["CHG-STAL"].findings:
            self.assertIn("Review lead", f.rationale)


class ChangeRefusals(unittest.TestCase):
    def test_missing_threshold_refuses(self):
        ent = copy.deepcopy(default_enterprise())
        del ent["policy"]["thresholds"]["stale_ticket_days"]
        res = results_by_id(ent)["CHG-STAL"]
        self.assertEqual(res.outcome, INCONCLUSIVE)
        self.assertIn("stale_ticket_days", res.refusal_reason)

    def test_absent_freeze_artifact_refuses(self):
        ent = copy.deepcopy(default_enterprise())
        del ent["policy"]["freeze_windows"]
        res = results_by_id(ent)["CHG-FRZ"]
        self.assertEqual(res.outcome, INCONCLUSIVE)
        self.assertIn("freeze", res.refusal_reason.lower())

    def test_empty_freeze_list_refuses(self):
        ent = copy.deepcopy(default_enterprise())
        ent["policy"]["freeze_windows"] = []
        res = results_by_id(ent)["CHG-FRZ"]
        self.assertEqual(res.outcome, INCONCLUSIVE)

    def test_empty_deploy_log_refuses_reconciliation(self):
        ent = copy.deepcopy(default_enterprise())
        ent["deploys"]["deploys"] = []
        by_id = results_by_id(ent)
        self.assertEqual(by_id["CHG-TICK"].outcome, INCONCLUSIVE)
        self.assertEqual(by_id["CHG-FRZ"].outcome, INCONCLUSIVE)
        # With no deploys, every approved ticket is undeployed; the stale
        # rule still runs — most clean tickets were approved long ago.
        self.assertEqual(by_id["CHG-STAL"].outcome, EXCEPTION)


class ChangeResultContract(unittest.TestCase):
    def test_deterministic_and_complete(self):
        a = [r.to_dict() for r in run_change_review(default_enterprise())]
        b = [r.to_dict() for r in run_change_review(default_enterprise())]
        self.assertEqual(a, b)
        self.assertEqual([r["rule_id"] for r in a],
                         [rule.rule_id for rule in CHANGE_RULES])
        for r in a:
            self.assertTrue(r["criterion"])
            self.assertTrue(r["limitations"])


if __name__ == "__main__":
    unittest.main()
