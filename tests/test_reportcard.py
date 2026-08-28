import unittest

from core.canonical import canonical_bytes
from core.stats import EXCEPTION, INCONCLUSIVE, wilson_interval
from enterprise.violations import CLASSES
from reportcard.card import (
    DEFAULT_N_SEEDS, DEFAULT_PLAN, DEFAULT_RECALL_FLOOR, _constituent_ids,
    _designed_rules, build_report_card,
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


class BrokenRuleRegressionEveryClass(unittest.TestCase):
    """D-014's regression check extended from one class to all thirteen:
    every planted class names exactly one designed rule, and a battery
    missing that rule must drive exactly that class to an exception while
    every other class stays fully caught. The one documented exception is
    access.sod_conflict, whose overlap with ACC-AUTH is intrinsic (D-009):
    its regression rides designed-rule recall instead — see the last test."""

    # Full plan at 2 per class, one seed: a missed class pools 0/2, whose
    # Wilson upper bound (~0.66) sits decisively below the 0.9 floor, so
    # EXCEPTION needs no larger pool — and thirteen broken-battery cards
    # stay under half a second of suite time.
    PLAN = {cls: 2 for cls in CLASSES}

    @classmethod
    def _card_without(cls, rule_id):
        from access.rules import ACCESS_RULES
        from change.rules import CHANGE_RULES
        return build_report_card(
            base_seed="itgc-break", n_seeds=1, plan=cls.PLAN,
            access_rules=tuple(r for r in ACCESS_RULES
                               if r.rule_id != rule_id),
            change_rules=tuple(r for r in CHANGE_RULES
                               if r.rule_id != rule_id))

    def _assert_break_flips_only(self, target, rule_id):
        card = self._card_without(rule_id)
        by_cls = {c["class"]: c for c in card["classes"]}
        broken = by_cls[target]
        # The card records that nothing claims the class any more, and
        # that nothing caught it — designed-rule or otherwise.
        self.assertEqual(broken["designed_rules"], [])
        self.assertEqual(broken["caught_any"], 0)
        self.assertEqual(broken["caught_designed"], 0)
        self.assertEqual(broken["decision"]["outcome"], EXCEPTION)
        # Exactly that class: every intact class stays fully caught, and
        # the target's is the only exception decision on the card.
        for cls_name, c in by_cls.items():
            if cls_name != target:
                self.assertEqual(c["caught_any"], c["planted"],
                                 "{0} after removing {1}".format(cls_name,
                                                                 rule_id))
        self.assertEqual(card["outcome_counts"][EXCEPTION], 1)
        self.assertEqual(card["overall_outcome"], EXCEPTION)
        # The identity echo shows the battery the card actually graded.
        self.assertNotIn(rule_id, card["identity"]["access_rules"]
                         + card["identity"]["change_rules"])

    def test_designed_rule_map_is_one_to_one(self):
        # The premise of breaking THE rule for a class: every planted
        # class names exactly one designed rule, and none is unclaimed.
        from access.rules import ACCESS_RULES
        from change.rules import CHANGE_RULES
        designed = _designed_rules(ACCESS_RULES + CHANGE_RULES)
        self.assertEqual(set(designed), set(CLASSES))
        for cls_name, rule_ids in designed.items():
            self.assertEqual(len(rule_ids), 1, cls_name)

    def test_terminated_active_flips_when_acc_term_is_removed(self):
        self._assert_break_flips_only("access.terminated_active", "ACC-TERM")

    def test_orphan_account_flips_when_acc_orph_is_removed(self):
        self._assert_break_flips_only("access.orphan_account", "ACC-ORPH")

    def test_dormant_privileged_flips_when_acc_dorm_is_removed(self):
        self._assert_break_flips_only("access.dormant_privileged", "ACC-DORM")

    def test_role_mismatch_flips_when_acc_auth_is_removed(self):
        self._assert_break_flips_only("access.role_mismatch", "ACC-AUTH")

    def test_service_account_flips_when_acc_svc_is_removed(self):
        self._assert_break_flips_only("access.service_account_no_owner",
                                      "ACC-SVC")

    def test_recert_lapsed_flips_when_acc_cert_is_removed(self):
        self._assert_break_flips_only("access.recert_lapsed", "ACC-CERT")

    def test_missing_approval_flips_when_chg_appr_is_removed(self):
        self._assert_break_flips_only("change.missing_approval", "CHG-APPR")

    def test_self_approval_flips_when_chg_self_is_removed(self):
        self._assert_break_flips_only("change.self_approval", "CHG-SELF")

    def test_emergency_review_flips_when_chg_emer_is_removed(self):
        self._assert_break_flips_only("change.emergency_no_review",
                                      "CHG-EMER")

    def test_ghost_deploy_flips_when_chg_tick_is_removed(self):
        self._assert_break_flips_only("change.deploy_without_ticket",
                                      "CHG-TICK")

    def test_freeze_violation_flips_when_chg_frz_is_removed(self):
        self._assert_break_flips_only("change.freeze_violation", "CHG-FRZ")

    def test_stale_ticket_flips_when_chg_stal_is_removed(self):
        self._assert_break_flips_only("change.stale_ticket", "CHG-STAL")

    def test_sod_regression_rides_designed_recall_not_any_rule(self):
        # The one class where the flip cannot be total: an added SoD role
        # is usually also off-matrix (D-009 names the overlap), so with
        # ACC-SOD removed ACC-AUTH still surfaces the added grant — and
        # because the manifest names every constituent id (D-012), that
        # counts as any-rule detection, not a false positive. At this
        # pinned seed the overlap holds for every plant; "usually" is
        # exactly why the class cannot join the strict flip above. The
        # regression is still visible: designed-rule recall collapses to
        # zero while any-rule recall stays intact.
        card = self._card_without("ACC-SOD")
        by_cls = {c["class"]: c for c in card["classes"]}
        sod = by_cls["access.sod_conflict"]
        self.assertEqual(sod["designed_rules"], [])
        self.assertEqual(sod["caught_designed"], 0)
        self.assertEqual(sod["caught_any"], sod["planted"])
        # No class decides an exception: the any-rule card genuinely does
        # not flip here, which is why this class is documented rather
        # than forced into the pattern above.
        self.assertEqual(card["outcome_counts"][EXCEPTION], 0)
        self.assertNotEqual(card["overall_outcome"], EXCEPTION)
        for cls_name, c in by_cls.items():
            self.assertEqual(c["caught_any"], c["planted"], cls_name)


class CardDeterminism(unittest.TestCase):
    def test_same_inputs_same_bytes(self):
        a = build_report_card(base_seed="itgc-det", n_seeds=1,
                              plan=SMALL_PLAN)
        b = build_report_card(base_seed="itgc-det", n_seeds=1,
                              plan=SMALL_PLAN)
        self.assertEqual(canonical_bytes(a), canonical_bytes(b))


if __name__ == "__main__":
    unittest.main()
