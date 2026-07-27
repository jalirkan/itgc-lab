import unittest

from core.canonical import canonical_bytes
from core.stats import EXCEPTION, INCONCLUSIVE, wilson_interval
from reportcard.card import (
    DEFAULT_N_SEEDS, DEFAULT_PLAN, DEFAULT_RECALL_FLOOR, _constituent_ids,
    build_report_card,
)

SMALL_PLAN = {"access.orphan_account": 1, "change.stale_ticket": 1}


class Definitions(unittest.TestCase):
    """Hand-computed locks on the definitions that decide every number
    (per lab D-019)."""

    def test_constituent_ids(self):
        self.assertEqual(
            _constituent_ids({"grant_ids": ["G-1", "G-2"], "user_id": "E-9"}),
            {"G-1", "G-2"})
        self.assertEqual(
            _constituent_ids({"ticket_id": "CHG-1", "deploy_id": "DPL-1"}),
            {"CHG-1", "DPL-1"})
        self.assertEqual(_constituent_ids({"user_id": "E-9"}), set())

    def test_hand_computed_single_seed_card(self):
        card = build_report_card(base_seed="itgc-hand", n_seeds=1,
                                 plan=SMALL_PLAN)
        by_cls = {c["class"]: c for c in card["classes"]}
        orphan = by_cls["access.orphan_account"]
        stale = by_cls["change.stale_ticket"]
        for c in (orphan, stale):
            self.assertEqual(c["planted"], 1)
            self.assertEqual(c["caught_any"], 1)
            self.assertEqual(c["caught_designed"], 1)
            # 1/1 pooled cannot clear a 0.9 floor: thin pools say so.
            self.assertEqual(c["decision"]["outcome"], INCONCLUSIVE)
        # Two planted records flagged, nothing else: precision 2/2.
        self.assertEqual(card["precision"]["numerator"], 2)
        self.assertEqual(card["precision"]["n"], 2)
        self.assertEqual(card["clean_false_positives"]["access"]["numerator"], 0)
        self.assertEqual(card["clean_false_positives"]["change"]["numerator"], 0)
        self.assertIn("n=", card["precision"]["rendered"])

    def test_default_plan_is_sized_for_the_floor(self):
        pooled = DEFAULT_N_SEEDS * DEFAULT_PLAN["access.orphan_account"]
        self.assertGreaterEqual(pooled, 35)
        self.assertGreater(wilson_interval(pooled, pooled)[0],
                           DEFAULT_RECALL_FLOOR)
        # One seed fewer and a perfect record would NOT clear the floor —
        # the sizing is deliberate, not slack (lab D-020).
        thinner = (DEFAULT_N_SEEDS - 1) * DEFAULT_PLAN["access.orphan_account"]
        self.assertLess(wilson_interval(thinner, thinner)[0],
                        DEFAULT_RECALL_FLOOR)


class TwoSeedCard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = build_report_card(base_seed="itgc-rc", n_seeds=2)

    def test_every_class_fully_caught_but_inconclusive_on_thin_pools(self):
        for c in self.card["classes"]:
            self.assertEqual(c["caught_any"], c["planted"], c["class"])
            self.assertEqual(c["caught_designed"], c["planted"], c["class"])
            self.assertEqual(c["planted"], 14, c["class"])
            # 14/14 pooled: Wilson lower bound ~0.78 — the truthful outcome
            # against a 0.9 floor is inconclusive, not a paraded 100%.
            self.assertEqual(c["decision"]["outcome"], INCONCLUSIVE, c["class"])
            self.assertTrue(c["per_seed_stable"], c["class"])
            self.assertEqual(len(c["per_seed"]), 2)

    def test_precision_and_clean_fp(self):
        p = self.card["precision"]
        self.assertEqual(p["numerator"], p["n"])
        self.assertGreater(p["n"], 0)
        for engine in ("access", "change"):
            fp = self.card["clean_false_positives"][engine]
            self.assertEqual(fp["numerator"], 0)
            self.assertGreater(fp["n"], 0)
            self.assertIn("per 10k", fp["per_10k"]["rendered"])
            # Even a zero has an upper bound: no bare rates (D-005).
            self.assertGreater(fp["interval"][1], 0.0)

    def test_no_composite_score_anywhere(self):
        self.assertNotIn("score", self.card)
        self.assertNotIn("composite", self.card)
        self.assertIn(self.card["overall_outcome"],
                      (INCONCLUSIVE, EXCEPTION, "pass"))
        self.assertIn("no composite score", self.card["overall_note"])

    def test_identity_echoes_everything_needed_to_rerun(self):
        ident = self.card["identity"]
        self.assertEqual(ident["seeds"], ["itgc-rc-001", "itgc-rc-002"])
        self.assertEqual(ident["plan"], {k: DEFAULT_PLAN[k]
                                         for k in sorted(DEFAULT_PLAN)})
        self.assertIn("ACC-TERM", ident["access_rules"])
        self.assertIn("CHG-FRZ", ident["change_rules"])


class BrokenRuleRegression(unittest.TestCase):
    """The card is the regression detector (per lab D-021): remove the
    only rule designed for a class and the card must drive that class to
    an exception, while intact classes stay caught."""

    def test_disabling_dormancy_rule_shows_up_as_exception(self):
        from access.rules import ACCESS_RULES
        broken = tuple(r for r in ACCESS_RULES if r.rule_id != "ACC-DORM")
        card = build_report_card(
            base_seed="itgc-broken", n_seeds=2,
            plan={"access.dormant_privileged": 3, "access.orphan_account": 3},
            access_rules=broken)
        by_cls = {c["class"]: c for c in card["classes"]}
        dormant = by_cls["access.dormant_privileged"]
        self.assertEqual(dormant["caught_any"], 0)
        self.assertEqual(dormant["decision"]["outcome"], EXCEPTION)
        intact = by_cls["access.orphan_account"]
        self.assertEqual(intact["caught_any"], intact["planted"])
        self.assertEqual(card["overall_outcome"], EXCEPTION)
        self.assertEqual(card["identity"]["access_rules"],
                         [r.rule_id for r in broken])


class CardDeterminism(unittest.TestCase):
    def test_same_inputs_same_bytes(self):
        a = build_report_card(base_seed="itgc-det", n_seeds=1,
                              plan=SMALL_PLAN)
        b = build_report_card(base_seed="itgc-det", n_seeds=1,
                              plan=SMALL_PLAN)
        self.assertEqual(canonical_bytes(a), canonical_bytes(b))


if __name__ == "__main__":
    unittest.main()
