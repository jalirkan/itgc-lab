import unittest

from enterprise import dates, roster
from tests.helpers import default_config, default_enterprise


class RosterLifecycle(unittest.TestCase):
    def setUp(self):
        self.cfg = default_config()
        self.ent = default_enterprise()
        self.employees = self.ent["roster"]["employees"]
        self.terminations = self.ent["roster"]["terminations"]

    def test_headcount(self):
        expected = self.cfg.employees + round(
            self.cfg.employees * self.cfg.joiner_rate)
        self.assertEqual(len(self.employees), expected)
        self.assertEqual(
            len({e["employee_id"] for e in self.employees}), expected)

    def test_lifecycle_counts(self):
        leavers = round(self.cfg.employees * self.cfg.leaver_rate)
        movers = round(self.cfg.employees * self.cfg.mover_rate)
        self.assertEqual(len(self.terminations), leavers)
        rehired = [e for e in self.employees
                   if any(ev["event"] == "rehire" for ev in e["history"])]
        moved = [e for e in self.employees
                 if any(ev["event"] == "transfer" for ev in e["history"])]
        self.assertEqual(len(rehired), self.cfg.rehires)
        self.assertEqual(len(moved), movers)

    def test_history_is_coherent(self):
        window_start = self.ent["policy"]["window_start"]
        for emp in self.employees:
            hist = emp["history"]
            self.assertEqual(hist[0]["event"], "hire")
            self.assertEqual(hist[0]["date"], emp["hire_date"])
            for a, b in zip(hist, hist[1:]):
                self.assertLess(a["date"], b["date"])
            prev = None
            for ev in hist:
                if ev["event"] == "rehire":
                    self.assertEqual(prev["event"], "termination")
                if ev["event"] == "transfer":
                    self.assertNotEqual(
                        prev["job_function"], ev["job_function"])
                prev = ev
            seg = roster.latest_stint(emp)
            if emp["status"] == "active":
                self.assertIsNone(seg["end"])
                self.assertIsNone(emp["termination_date"])
            else:
                self.assertEqual(seg["closed_by"], "termination")
                self.assertEqual(emp["termination_date"], seg["end"])
                self.assertLess(
                    emp["termination_date"], self.ent["policy"]["snapshot"])
                self.assertGreater(emp["termination_date"], window_start)

    def test_guaranteed_functions_cover_window(self):
        window_start = self.ent["policy"]["window_start"]
        for function, minimum in (("system-administrator", 2),
                                  ("qa-analyst", 2), ("controller", 1),
                                  ("software-developer", 3)):
            holders = [
                e for e in self.employees
                if roster.current_function(e) == function
                and e["hire_date"] < window_start
                and all(ev["event"] != "termination" for ev in e["history"])
            ]
            self.assertGreaterEqual(len(holders), minimum, function)

    def test_termination_report_includes_rehires(self):
        """The flat termination list deliberately contains rehired employees:
        that is the benign trap for naive terminated-but-active joins."""
        rehired_ids = {
            e["employee_id"] for e in self.employees
            if any(ev["event"] == "rehire" for ev in e["history"])}
        listed = {t["employee_id"] for t in self.terminations}
        self.assertTrue(rehired_ids <= listed)
        for emp in self.employees:
            if emp["employee_id"] in rehired_ids:
                self.assertEqual(emp["status"], "active")
                self.assertTrue(roster.is_active_at(
                    emp, self.ent["policy"]["snapshot"]))

    def test_active_status_matches_stints(self):
        snapshot = self.ent["policy"]["snapshot"]
        for emp in self.employees:
            self.assertEqual(
                emp["status"] == "active",
                roster.is_active_at(emp, snapshot),
            )

    def test_dates_inside_window_bounds(self):
        window_start = self.ent["policy"]["window_start"]
        months_back = dates.months_back(
            self.ent["policy"]["snapshot"], self.cfg.months)
        self.assertEqual(window_start, months_back)


if __name__ == "__main__":
    unittest.main()
