import re
import unittest

from core.canonical import canonical_bytes
from enterprise import catalogs, dates, generator, roster
from enterprise.tickets import in_freeze
from enterprise.violations import CLASSES, InjectionError, inject
from tests.helpers import default_config, default_enterprise

FULL_PLAN = {cls: 2 for cls in CLASSES}
SEED = "plant-001"


def _by(items, key):
    return {x[key]: x for x in items}


class _World:
    """Independent re-derivation of every planted property, used both to
    verify manifests (each plant exhibits its claimed property, lab D-010)
    and to scan clean data (base rate of every violation property is zero)."""

    def __init__(self, ent):
        self.ent = ent
        self.snapshot = ent["policy"]["snapshot"]
        self.t = ent["policy"]["thresholds"]
        self.grants = _by(ent["iam"]["grants"], "grant_id")
        self.emps = _by(ent["roster"]["employees"], "employee_id")
        self.tickets = _by(ent["tickets"]["tickets"], "ticket_id")
        self.deploys = _by(ent["deploys"]["deploys"], "deploy_id")
        self.deploy_by_ticket = {d["ticket_id"]: d
                                 for d in ent["deploys"]["deploys"]}
        self.matrix = catalogs.authorization_matrix()
        self.register = {(x["user_id"], x["system"], x["role"])
                         for x in ent["exceptions"]["exceptions"]}
        self.freezes = ent["policy"]["freeze_windows"]
        self.sod = catalogs.sod_matrix()["pairs"]

    def held(self, eid):
        return {"{0}:{1}".format(g["system"], g["role"])
                for g in self.grants.values()
                if g["user_id"] == eid and g["status"] == "active"}

    # -- property predicates, one per class --------------------------------
    def terminated_active(self, g):
        if g["account_type"] != "user" or g["status"] != "active":
            return False
        emp = self.emps.get(g["user_id"])
        if emp is None:
            return False
        seg = roster.latest_stint(emp)
        return (seg["closed_by"] == "termination"
                and dates.days_between(seg["end"], self.snapshot)
                > self.t["termination_grace_days"])

    def orphan(self, g):
        return (g["account_type"] == "user" and g["status"] == "active"
                and g["user_id"] not in self.emps)

    def dormant_privileged(self, g):
        return (g["privileged"] and g["status"] == "active"
                and dates.days_between(g["last_used_date"], self.snapshot)
                > self.t["dormant_privileged_days"])

    def role_mismatch(self, g):
        if (g["account_type"] != "user" or g["status"] != "active"
                or g["user_id"] not in self.emps):
            return False
        function = roster.current_function(self.emps[g["user_id"]])
        if function is None:
            return False
        sys_role = "{0}:{1}".format(g["system"], g["role"])
        if sys_role in self.matrix[function]:
            return False
        return (g["user_id"], g["system"], g["role"]) not in self.register

    def sod_conflict_users(self):
        out = set()
        for eid in self.emps:
            held = self.held(eid)
            for p in self.sod:
                if p["a"] in held and p["b"] in held:
                    out.add(eid)
        return out

    def unowned_special(self, g):
        return (g["account_type"] in ("service", "shared")
                and g["owner_id"] is None)

    def recert_lapsed(self, g):
        return (g["status"] == "active" and g["account_type"] == "user"
                and g["user_id"] in self.emps
                and dates.days_between(g["last_certified_date"], self.snapshot)
                > self.t["recert_cycle_days"])

    def missing_approval(self, t):
        return (t["ticket_id"] in self.deploy_by_ticket
                and t["approved_at"] is None)

    def self_approval(self, t):
        return (t["approver_id"] is not None
                and t["approver_id"] == t["developer_id"])

    def emergency_no_review(self, t):
        if t["change_type"] != "emergency":
            return False
        d = self.deploy_by_ticket.get(t["ticket_id"])
        if d is None:
            return False
        if t["post_review_at"] is None:
            return True
        return (dates.days_between(d["deployed_at"], t["post_review_at"])
                > self.t["emergency_review_days"])

    def ghost_deploy(self, d):
        return d["ticket_id"] not in self.tickets

    def freeze_deploy(self, d):
        return in_freeze(d["deployed_at"], self.freezes)

    def stale_ticket(self, t):
        return (t["ticket_id"] not in self.deploy_by_ticket
                and t["approved_at"] is not None
                and dates.days_between(t["approved_at"], self.snapshot)
                > self.t["stale_ticket_days"])


class CleanBaseRates(unittest.TestCase):
    def test_every_violation_property_is_absent_in_clean_data(self):
        w = _World(default_enterprise())
        grants = w.grants.values()
        tickets = w.tickets.values()
        deploys = w.deploys.values()
        self.assertEqual([g["grant_id"] for g in grants
                          if w.terminated_active(g)], [])
        self.assertEqual([g["grant_id"] for g in grants if w.orphan(g)], [])
        self.assertEqual([g["grant_id"] for g in grants
                          if w.dormant_privileged(g)], [])
        self.assertEqual([g["grant_id"] for g in grants
                          if w.role_mismatch(g)], [])
        self.assertEqual(w.sod_conflict_users(), set())
        self.assertEqual([g["grant_id"] for g in grants
                          if w.unowned_special(g)], [])
        self.assertEqual([g["grant_id"] for g in grants
                          if w.recert_lapsed(g)], [])
        self.assertEqual([t["ticket_id"] for t in tickets
                          if w.missing_approval(t)], [])
        self.assertEqual([t["ticket_id"] for t in tickets
                          if w.self_approval(t)], [])
        self.assertEqual([t["ticket_id"] for t in tickets
                          if w.emergency_no_review(t)], [])
        self.assertEqual([d["deploy_id"] for d in deploys
                          if w.ghost_deploy(d)], [])
        self.assertEqual([d["deploy_id"] for d in deploys
                          if w.freeze_deploy(d)], [])
        self.assertEqual([t["ticket_id"] for t in tickets
                          if w.stale_ticket(t)], [])


class InjectorContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean = default_enterprise()
        cls.before = {name: canonical_bytes(cls.clean[name])
                      for name in generator.ARTIFACTS}
        cls.planted, cls.manifest = inject(cls.clean, FULL_PLAN, SEED)
        cls.world = _World(cls.planted)

    def test_input_never_mutated_and_clean_regenerates_identically(self):
        for name in generator.ARTIFACTS:
            self.assertEqual(
                canonical_bytes(self.clean[name]), self.before[name],
                name + " mutated by inject()")
        regen = generator.generate(default_config())
        for name in generator.ARTIFACTS:
            self.assertEqual(
                canonical_bytes(regen[name]), self.before[name],
                name + " differs when regenerated after injection")

    def test_manifest_shape_and_counts(self):
        self.assertEqual(self.manifest["plan"], FULL_PLAN)
        self.assertEqual(len(self.manifest["violations"]),
                         sum(FULL_PLAN.values()))
        vids = [v["violation_id"] for v in self.manifest["violations"]]
        self.assertEqual(len(vids), len(set(vids)))
        per_class = {}
        for v in self.manifest["violations"]:
            per_class[v["class"]] = per_class.get(v["class"], 0) + 1
        self.assertEqual(per_class, FULL_PLAN)
        for v in self.manifest["violations"]:
            self.assertTrue(v["note"])

    def test_each_plant_exhibits_its_claimed_property(self):
        w = self.world
        for v in self.manifest["violations"]:
            cls_name = v["class"]
            refs = v["refs"]
            if cls_name == "access.terminated_active":
                self.assertTrue(w.terminated_active(
                    w.grants[refs["grant_ids"][0]]), v)
            elif cls_name == "access.orphan_account":
                self.assertTrue(w.orphan(w.grants[refs["grant_ids"][0]]), v)
            elif cls_name == "access.dormant_privileged":
                self.assertTrue(w.dormant_privileged(
                    w.grants[refs["grant_ids"][0]]), v)
            elif cls_name == "access.role_mismatch":
                self.assertTrue(w.role_mismatch(
                    w.grants[refs["grant_ids"][0]]), v)
            elif cls_name == "access.sod_conflict":
                self.assertIn(refs["user_id"], w.sod_conflict_users(), v)
            elif cls_name == "access.service_account_no_owner":
                self.assertTrue(w.unowned_special(
                    w.grants[refs["grant_ids"][0]]), v)
            elif cls_name == "access.recert_lapsed":
                self.assertTrue(w.recert_lapsed(
                    w.grants[refs["grant_ids"][0]]), v)
            elif cls_name == "change.missing_approval":
                self.assertTrue(w.missing_approval(
                    w.tickets[refs["ticket_id"]]), v)
            elif cls_name == "change.self_approval":
                self.assertTrue(w.self_approval(
                    w.tickets[refs["ticket_id"]]), v)
            elif cls_name == "change.emergency_no_review":
                self.assertTrue(w.emergency_no_review(
                    w.tickets[refs["ticket_id"]]), v)
            elif cls_name == "change.deploy_without_ticket":
                self.assertTrue(w.ghost_deploy(
                    w.deploys[refs["deploy_id"]]), v)
            elif cls_name == "change.freeze_violation":
                self.assertTrue(w.freeze_deploy(
                    w.deploys[refs["deploy_id"]]), v)
            elif cls_name == "change.stale_ticket":
                self.assertTrue(w.stale_ticket(
                    w.tickets[refs["ticket_id"]]), v)
            else:
                self.fail("untested class " + cls_name)

    def test_no_positional_artifacts(self):
        gid_re = re.compile(r"^G-[0-9a-f]{10}$")
        for g in self.planted["iam"]["grants"]:
            self.assertTrue(gid_re.match(g["grant_id"]), g["grant_id"])
        planted_gids = set()
        for v in self.manifest["violations"]:
            planted_gids.update(v["refs"].get("grant_ids", []))
        order = [g["grant_id"] for g in self.planted["iam"]["grants"]]
        self.assertEqual(order, sorted(order))
        idx = sorted(order.index(g) for g in planted_gids if g in order)
        # Planted grants must interleave with clean ones, not sit in a
        # block at either end of the canonical ordering (lab D-009).
        self.assertGreater(idx[0], 0)
        self.assertLess(idx[-1], len(order) - 1)
        spread = idx[-1] - idx[0] + 1
        self.assertGreater(spread, len(idx),
                           "planted grants form a contiguous block")

    def test_deterministic_and_seed_sensitive(self):
        p2, m2 = inject(self.clean, FULL_PLAN, SEED)
        self.assertEqual(canonical_bytes(m2), canonical_bytes(self.manifest))
        for name in generator.ARTIFACTS:
            self.assertEqual(canonical_bytes(p2[name]),
                             canonical_bytes(self.planted[name]))
        _, m3 = inject(self.clean, FULL_PLAN, "plant-002")
        self.assertNotEqual(canonical_bytes(m3), canonical_bytes(self.manifest))

    def test_benign_look_alikes_survive_injection(self):
        clean_w = _World(self.clean)
        # Sanctioned-exception grants are untouched, byte for byte.
        for (uid, system, role) in clean_w.register:
            before = [g for g in self.clean["iam"]["grants"]
                      if (g["user_id"], g["system"], g["role"])
                      == (uid, system, role)]
            after = [g for g in self.planted["iam"]["grants"]
                     if (g["user_id"], g["system"], g["role"])
                     == (uid, system, role)]
            self.assertEqual(before, after)
        # Clean emergencies keep their reviews.
        for t in self.clean["tickets"]["tickets"]:
            if t["change_type"] == "emergency":
                kept = next(x for x in self.planted["tickets"]["tickets"]
                            if x["ticket_id"] == t["ticket_id"])
                self.assertEqual(t, kept)
        # Rehired employees are never violation targets.
        rehired = {e["employee_id"]
                   for e in self.clean["roster"]["employees"]
                   if any(ev["event"] == "rehire" for ev in e["history"])}
        for v in self.manifest["violations"]:
            self.assertNotIn(v["refs"].get("user_id"), rehired, v)

    def test_errors(self):
        with self.assertRaises(InjectionError):
            inject(self.clean, {"access.unknown_thing": 1}, SEED)
        with self.assertRaises(InjectionError):
            inject(self.clean, {"access.terminated_active": 500}, SEED)
        with self.assertRaises(InjectionError):
            inject(self.clean, {"access.orphan_account": -1}, SEED)


if __name__ == "__main__":
    unittest.main()
