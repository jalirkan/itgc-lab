"""Clean-population invariants and benign pins for the config baseline.

The generator emits a compliant baseline, always (D-009): every recorded
value meets the stated standard and every privileged account is enrolled
in MFA. What makes the resulting precision mean anything is the two
benign look-alikes this module pins (D-004) — settings configured
STRICTER than the standard, and ordinary accounts deliberately not
enrolled — plus the executable proof that a naive implementation
false-positives on exactly those, and only those.
"""

import unittest

from enterprise import catalogs
from enterprise.baseline import (CLEAN_VALUES, HARDENING_SETTINGS,
                                 MFA_SETTINGS, PASSWORD_SETTINGS, SETTINGS,
                                 meets, setting_id)
from enterprise.config import CONFIG_STANDARD
from tests.helpers import default_config, default_enterprise


class ExportShape(unittest.TestCase):
    def setUp(self):
        self.ent = default_enterprise()
        self.settings = self.ent["configs"]["settings"]
        self.enrolments = self.ent["configs"]["mfa_enrolments"]

    def test_one_row_per_system_and_setting(self):
        systems = catalogs.org()["systems"]
        self.assertEqual(len(self.settings), len(systems) * len(SETTINGS))
        pairs = {(s["system"], s["setting"]) for s in self.settings}
        self.assertEqual(len(pairs), len(self.settings))
        self.assertEqual({s["system"] for s in self.settings}, set(systems))

    def test_ids_are_natural_keys_and_canonically_ordered(self):
        for row in self.settings:
            self.assertEqual(row["config_id"],
                             setting_id(row["system"], row["setting"]))
        order = [s["config_id"] for s in self.settings]
        self.assertEqual(order, sorted(order))
        m_order = [e["enrolment_id"] for e in self.enrolments]
        self.assertEqual(m_order, sorted(m_order))

    def test_every_setting_is_observed_at_the_snapshot(self):
        for row in self.settings:
            self.assertEqual(row["observed_at"],
                             self.ent["policy"]["snapshot"])

    def test_standard_ships_with_the_population(self):
        stated = self.ent["policy"]["config_standard"]
        self.assertEqual(set(stated), set(SETTINGS))
        self.assertEqual(stated, CONFIG_STANDARD)
        for spec in stated.values():
            self.assertIn(spec["require"],
                          ("at_least", "at_most", "enabled"))

    def test_enrolment_register_covers_every_active_account(self):
        active = {(g["system"], g["account_id"])
                  for g in self.ent["iam"]["grants"]
                  if g["status"] == "active"}
        register = {(e["system"], e["account_id"]) for e in self.enrolments}
        self.assertEqual(register, active)

    def test_register_privilege_flag_matches_the_access_export(self):
        privileged = {(g["system"], g["account_id"])
                      for g in self.ent["iam"]["grants"]
                      if g["status"] == "active" and g["privileged"]}
        flagged = {(e["system"], e["account_id"]) for e in self.enrolments
                   if e["privileged"]}
        self.assertEqual(flagged, privileged)


class CleanInvariants(unittest.TestCase):
    """Base rate zero: the generator can only emit a compliant baseline."""

    def setUp(self):
        self.ent = default_enterprise()
        self.standard = self.ent["policy"]["config_standard"]

    def test_every_recorded_value_meets_the_stated_standard(self):
        off = [(s["system"], s["setting"], s["value"])
               for s in self.ent["configs"]["settings"]
               if not meets(self.standard[s["setting"]], s["value"])]
        self.assertEqual(off, [])

    def test_every_privileged_account_is_enrolled(self):
        gaps = [e["enrolment_id"] for e in self.ent["configs"]["mfa_enrolments"]
                if e["privileged"] and not e["enrolled"]]
        self.assertEqual(gaps, [])

    def test_enrolled_rows_carry_a_method_and_a_date(self):
        for e in self.ent["configs"]["mfa_enrolments"]:
            if e["enrolled"]:
                self.assertIn(e["method"],
                              ("authenticator-app", "hardware-token"))
                self.assertIsNotNone(e["enrolled_date"])
                self.assertLessEqual(e["enrolled_date"],
                                     self.ent["policy"]["snapshot"])
            else:
                self.assertIsNone(e["method"])
                self.assertIsNone(e["enrolled_date"])


class BenignLookAlikes(unittest.TestCase):
    """Mandatory in clean data (D-004): without them, a baseline rule
    scoring precision 1.0 has beaten nothing."""

    def setUp(self):
        self.cfg = default_config()
        self.ent = default_enterprise()

    def test_some_systems_are_configured_stricter_than_the_standard(self):
        stricter = [s for s in self.ent["configs"]["settings"]
                    if s["value"] != CONFIG_STANDARD[s["setting"]]["value"]]
        self.assertTrue(stricter,
                        "no setting beats the stated standard: the "
                        "equality-comparison trap has gone dead")
        # Every one of them still MEETS the standard — that is the point.
        for row in stricter:
            self.assertTrue(meets(CONFIG_STANDARD[row["setting"]],
                                  row["value"]), row)

    def test_the_clean_value_table_can_only_produce_compliant_values(self):
        for setting, values in CLEAN_VALUES.items():
            for value in values:
                self.assertTrue(meets(CONFIG_STANDARD[setting], value),
                                (setting, value))

    def test_ordinary_accounts_are_unenrolled_at_the_configured_rate(self):
        register = self.ent["configs"]["mfa_enrolments"]
        ordinary = [e for e in register if not e["privileged"]]
        expected_enrolled = int(round(
            self.cfg.ordinary_mfa_enrolment_rate * len(ordinary)))
        enrolled = [e for e in ordinary if e["enrolled"]]
        self.assertEqual(len(enrolled), expected_enrolled)
        self.assertGreater(len(ordinary) - expected_enrolled, 0,
                           "no ordinary account is unenrolled: the "
                           "enrol-everyone trap has gone dead")


class NaiveImplementationsTripTheTraps(unittest.TestCase):
    """Executable proof that both look-alikes are load-bearing, in the
    same shape as the access engine's rehire trap (D-014, toolkit D-017).
    If either of these stops misfiring, the clean population has stopped
    tempting anyone and the baseline precision claim is hollow."""

    def setUp(self):
        self.ent = default_enterprise()
        from baseline.engine import run_baseline_review
        self.results = {r.rule_id: r for r in run_baseline_review(self.ent)}

    def test_equality_comparison_false_positives_on_stricter_settings(self):
        naive_fps = {
            s["config_id"] for s in self.ent["configs"]["settings"]
            if s["value"] != CONFIG_STANDARD[s["setting"]]["value"]}
        self.assertTrue(naive_fps,
                        "an equality check against the standard no longer "
                        "misfires on this population")
        # The real rules, on the same data, flag nothing at all.
        flagged = set()
        for rule_id in ("CFG-PWD", "CFG-HARD", "CFG-MFA"):
            self.assertEqual(len(self.results[rule_id].findings), 0, rule_id)
            for f in self.results[rule_id].findings:
                flagged.update(f.record_ids)
        self.assertEqual(flagged & naive_fps, set())
        # And every naive false positive is a setting configured STRICTER
        # than the standard — nothing else is in that set.
        for row in self.ent["configs"]["settings"]:
            if row["config_id"] in naive_fps:
                self.assertTrue(meets(CONFIG_STANDARD[row["setting"]],
                                      row["value"]), row)

    def test_enrol_everyone_check_false_positives_on_ordinary_accounts(self):
        register = self.ent["configs"]["mfa_enrolments"]
        naive_fps = {e["enrolment_id"] for e in register if not e["enrolled"]}
        self.assertTrue(naive_fps,
                        "an enrol-everyone check no longer misfires on "
                        "this population")
        res = self.results["CFG-ENRL"]
        self.assertEqual(len(res.findings), 0)
        # The naive check's misfires are ordinary accounts, every one:
        # the stated standard requires MFA for privileged access only.
        by_id = {e["enrolment_id"]: e for e in register}
        self.assertEqual({by_id[i]["privileged"] for i in naive_fps},
                         {False})
        # And they sit INSIDE the rule's population rather than being
        # filtered out of it (D-013): a look-alike outside every
        # population proves nothing.
        self.assertEqual(res.population_n, len(register))


class SettingRosterIsPartitioned(unittest.TestCase):
    def test_every_setting_belongs_to_exactly_one_rule(self):
        groups = (PASSWORD_SETTINGS, HARDENING_SETTINGS, MFA_SETTINGS)
        flat = [name for group in groups for name in group]
        self.assertEqual(sorted(flat), sorted(SETTINGS))
        self.assertEqual(len(flat), len(set(flat)))


if __name__ == "__main__":
    unittest.main()
