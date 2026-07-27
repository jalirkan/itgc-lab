import unittest

from enterprise import catalogs, dates, roster
from tests.helpers import default_config, default_enterprise


class BenignLookAlikes(unittest.TestCase):
    """The clean population must contain the documented benign look-alikes
    (D-004, per lab D-008) — otherwise precision is 1.0 by construction and
    demonstrates nothing. Base rates are pinned to the config."""

    def setUp(self):
        self.cfg = default_config()
        self.ent = default_enterprise()
        self.snapshot = self.ent["policy"]["snapshot"]
        self.grants = self.ent["iam"]["grants"]
        self.by_id = {e["employee_id"]: e
                      for e in self.ent["roster"]["employees"]}

    def test_rehires_look_terminated_but_active(self):
        rehired = [e for e in self.by_id.values()
                   if any(ev["event"] == "rehire" for ev in e["history"])]
        self.assertEqual(len(rehired), self.cfg.rehires)
        terminated_ids = {t["employee_id"]
                          for t in self.ent["roster"]["terminations"]}
        for emp in rehired:
            eid = emp["employee_id"]
            # The naive join: appears in the termination report...
            self.assertIn(eid, terminated_ids)
            # ...and holds active access at the snapshot.
            active = [g for g in self.grants
                      if g["user_id"] == eid and g["status"] == "active"]
            self.assertTrue(active, eid)
            # But the latest stint is open: not a violation.
            self.assertIsNone(roster.latest_stint(emp)["end"])

    def test_sanctioned_cross_functional_grants(self):
        register = self.ent["exceptions"]["exceptions"]
        self.assertEqual(len(register), self.cfg.sanctioned_exceptions)
        matrix = catalogs.authorization_matrix()
        for x in register:
            emp = self.by_id[x["user_id"]]
            function = roster.current_function(emp)
            sys_role = "{0}:{1}".format(x["system"], x["role"])
            self.assertNotIn(sys_role, matrix[function],
                             "exception grant must sit outside the matrix")

    def test_proper_weekend_emergencies(self):
        tickets = {t["ticket_id"]: t for t in self.ent["tickets"]["tickets"]}
        weekend_deploys = [d for d in self.ent["deploys"]["deploys"]
                           if dates.is_weekend(d["deployed_at"])]
        self.assertEqual(len(weekend_deploys), self.cfg.proper_emergencies)
        for d in weekend_deploys:
            t = tickets[d["ticket_id"]]
            self.assertEqual(t["change_type"], "emergency")
            self.assertIsNotNone(t["post_review_at"])
            # Approval postdates deployment: looks like a change without
            # prior approval unless the rule respects emergency handling.
            self.assertGreater(t["approved_at"], d["deployed_at"])

    def test_open_recent_tickets(self):
        deployed = {d["ticket_id"] for d in self.ent["deploys"]["deploys"]}
        stale = self.ent["policy"]["thresholds"]["stale_ticket_days"]
        open_tickets = [t for t in self.ent["tickets"]["tickets"]
                        if t["ticket_id"] not in deployed]
        self.assertEqual(len(open_tickets), self.cfg.open_recent_tickets)
        for t in open_tickets:
            self.assertLess(
                dates.days_between(t["approved_at"], self.snapshot), stale)

    def test_service_and_shared_accounts_owned(self):
        svc = [g for g in self.grants if g["account_type"] in ("service", "shared")]
        systems = len(catalogs.org()["systems"])
        expected = systems * (self.cfg.service_accounts_per_system
                              + self.cfg.shared_accounts_per_system)
        self.assertEqual(len(svc), expected)
        for g in svc:
            self.assertIsNotNone(g["owner_id"])


if __name__ == "__main__":
    unittest.main()
