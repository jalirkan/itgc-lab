import unittest

from enterprise import dates
from enterprise.tickets import in_freeze
from tests.helpers import default_enterprise


class TicketConsistency(unittest.TestCase):
    """Clean change-management invariants (generator correctness, D-002)."""

    def setUp(self):
        self.ent = default_enterprise()
        self.snapshot = self.ent["policy"]["snapshot"]
        self.thresholds = self.ent["policy"]["thresholds"]
        self.freezes = self.ent["policy"]["freeze_windows"]
        self.tickets = {t["ticket_id"]: t for t in self.ent["tickets"]["tickets"]}
        self.deploys = self.ent["deploys"]["deploys"]
        self.deploy_by_ticket = {d["ticket_id"]: d for d in self.deploys}

    def test_ids_unique(self):
        self.assertEqual(len(self.tickets), len(self.ent["tickets"]["tickets"]))
        dids = [d["deploy_id"] for d in self.deploys]
        self.assertEqual(len(dids), len(set(dids)))

    def test_every_deploy_has_a_ticket(self):
        for d in self.deploys:
            self.assertIn(d["ticket_id"], self.tickets, d["deploy_id"])

    def test_routine_changes_approved_before_deploy(self):
        for d in self.deploys:
            t = self.tickets[d["ticket_id"]]
            if t["change_type"] == "emergency":
                continue
            self.assertIsNotNone(t["approved_at"])
            self.assertGreaterEqual(t["approved_at"], t["created_at"])
            self.assertGreaterEqual(d["deployed_at"], t["approved_at"])
            self.assertFalse(dates.is_weekend(d["deployed_at"]), d["deploy_id"])

    def test_approver_never_developer(self):
        for t in self.tickets.values():
            if t["approver_id"] is not None:
                self.assertNotEqual(
                    t["approver_id"], t["developer_id"], t["ticket_id"])

    def test_no_clean_deploy_inside_freeze(self):
        for d in self.deploys:
            self.assertFalse(
                in_freeze(d["deployed_at"], self.freezes), d["deploy_id"])

    def test_emergencies_carry_post_hoc_review(self):
        sla = self.thresholds["emergency_review_days"]
        emergencies = [t for t in self.tickets.values()
                       if t["change_type"] == "emergency"]
        self.assertTrue(emergencies)
        for t in emergencies:
            d = self.deploy_by_ticket[t["ticket_id"]]
            self.assertIsNotNone(t["post_review_at"])
            self.assertIsNotNone(t["post_review_by"])
            self.assertNotEqual(t["post_review_by"], t["developer_id"])
            self.assertGreater(t["post_review_at"], d["deployed_at"])
            self.assertLessEqual(
                dates.days_between(d["deployed_at"], t["post_review_at"]), sla)

    def test_undeployed_tickets_are_recent(self):
        stale = self.thresholds["stale_ticket_days"]
        for t in self.tickets.values():
            if t["ticket_id"] in self.deploy_by_ticket:
                continue
            self.assertEqual(t["status"], "approved")
            self.assertLess(
                dates.days_between(t["approved_at"], self.snapshot), stale,
                t["ticket_id"])

    def test_all_dates_within_window(self):
        window_start = self.ent["policy"]["window_start"]
        for t in self.tickets.values():
            self.assertGreaterEqual(t["created_at"], window_start)
            self.assertLessEqual(t["created_at"], self.snapshot)
        for d in self.deploys:
            self.assertLessEqual(d["deployed_at"], self.snapshot)


if __name__ == "__main__":
    unittest.main()
