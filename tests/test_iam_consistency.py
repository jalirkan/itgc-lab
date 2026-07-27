import unittest

from enterprise import catalogs, dates, roster
from tests.helpers import default_enterprise


class IamConsistency(unittest.TestCase):
    """Clean-data invariants: the IAM export must be consistent with the
    roster BY CONSTRUCTION. Any failure here is a generator bug, because
    violations exist only via the injector (D-002)."""

    def setUp(self):
        self.ent = default_enterprise()
        self.snapshot = self.ent["policy"]["snapshot"]
        self.thresholds = self.ent["policy"]["thresholds"]
        self.grants = self.ent["iam"]["grants"]
        self.by_id = {e["employee_id"]: e
                      for e in self.ent["roster"]["employees"]}
        self.matrix = catalogs.authorization_matrix()
        self.register = {(x["user_id"], x["system"], x["role"])
                         for x in self.ent["exceptions"]["exceptions"]}

    def test_ids_unique_and_accounts_consistent(self):
        gids = [g["grant_id"] for g in self.grants]
        self.assertEqual(len(gids), len(set(gids)))
        seen = {}
        for g in self.grants:
            if g["account_type"] == "user":
                key = (g["system"], g["user_id"])
                seen.setdefault(key, set()).add(g["account_id"])
        for key, accounts in seen.items():
            self.assertEqual(len(accounts), 1, key)

    def test_every_user_grant_belongs_to_roster(self):
        for g in self.grants:
            if g["account_type"] == "user":
                self.assertIn(g["user_id"], self.by_id, g["grant_id"])
            else:
                self.assertIsNone(g["user_id"])
                self.assertIn(g["owner_id"], self.by_id, g["grant_id"])
                owner = self.by_id[g["owner_id"]]
                self.assertEqual(owner["status"], "active")

    def test_no_terminated_employee_keeps_active_access(self):
        grace = self.thresholds["termination_grace_days"]
        for g in self.grants:
            if g["account_type"] != "user":
                continue
            emp = self.by_id[g["user_id"]]
            seg = roster.latest_stint(emp)
            if seg["closed_by"] == "termination":
                self.assertEqual(g["status"], "disabled", g["grant_id"])
                self.assertIsNotNone(g["disabled_date"])
                self.assertLessEqual(
                    dates.days_between(seg["end"], g["disabled_date"]),
                    grace,
                    "disablement outside grace for " + g["grant_id"],
                )

    def test_active_grants_only_for_active_employees(self):
        for g in self.grants:
            if g["account_type"] == "user" and g["status"] == "active":
                self.assertTrue(
                    roster.is_active_at(self.by_id[g["user_id"]], self.snapshot),
                    g["grant_id"])

    def test_mover_residual_access_cleaned_up(self):
        cleanup = self.thresholds["transfer_cleanup_days"]
        for emp in self.by_id.values():
            segs = roster.segments(emp)
            for seg in segs:
                if seg["closed_by"] != "transfer":
                    continue
                for g in self.grants:
                    if (g["user_id"] == emp["employee_id"]
                            and g["granted_date"] >= seg["start"]
                            and g["granted_date"] <= seg["end"]
                            and g["status"] == "disabled"
                            and g["disabled_date"] is not None
                            and g["disabled_date"] >= seg["end"]):
                        self.assertLessEqual(
                            dates.days_between(seg["end"], g["disabled_date"]),
                            cleanup)

    def test_active_roles_authorized_or_excepted(self):
        for g in self.grants:
            if g["account_type"] != "user" or g["status"] != "active":
                continue
            emp = self.by_id[g["user_id"]]
            function = roster.current_function(emp)
            self.assertIsNotNone(function, g["grant_id"])
            sys_role = "{0}:{1}".format(g["system"], g["role"])
            if sys_role in self.matrix[function]:
                continue
            self.assertIn(
                (g["user_id"], g["system"], g["role"]), self.register,
                "unauthorized clean grant " + g["grant_id"])

    def test_usage_and_certification_windows(self):
        dormant = self.thresholds["dormant_privileged_days"]
        cycle = self.thresholds["recert_cycle_days"]
        for g in self.grants:
            self.assertIsNotNone(g["last_used_date"])
            self.assertGreaterEqual(g["last_used_date"], g["granted_date"])
            self.assertLessEqual(g["last_used_date"], self.snapshot)
            if g["status"] == "active":
                self.assertIsNotNone(g["last_certified_date"])
                self.assertLess(
                    dates.days_between(g["last_certified_date"], self.snapshot),
                    cycle, g["grant_id"])
                self.assertGreaterEqual(
                    g["last_certified_date"], g["granted_date"])
                if g["privileged"]:
                    self.assertLess(
                        dates.days_between(g["last_used_date"], self.snapshot),
                        dormant, g["grant_id"])
            else:
                self.assertIsNotNone(g["disabled_date"])
                self.assertGreaterEqual(g["disabled_date"], g["granted_date"])

    def test_privileged_flag_matches_catalog(self):
        for g in self.grants:
            self.assertEqual(
                g["privileged"], catalogs.is_privileged(g["system"], g["role"]))

    def test_exception_register_is_coherent(self):
        for x in self.ent["exceptions"]["exceptions"]:
            self.assertIn(x["user_id"], self.by_id)
            self.assertIn(x["approved_by"], self.by_id)
            self.assertNotEqual(x["approved_by"], x["user_id"])
            self.assertGreater(x["expires_at"], self.snapshot)
            backing = [
                g for g in self.grants
                if g["user_id"] == x["user_id"] and g["system"] == x["system"]
                and g["role"] == x["role"] and g["status"] == "active"]
            self.assertEqual(len(backing), 1)


if __name__ == "__main__":
    unittest.main()
