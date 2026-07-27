"""Access-review engine: shared view over an enterprise + rule runner."""

from core.rules import run_rules
from enterprise import catalogs, roster


class AccessView:
    """Read-only, precomputed joins the access rules share."""

    def __init__(self, ent):
        self.ent = ent
        self.snapshot = ent["policy"]["snapshot"]
        self.thresholds = ent["policy"].get("thresholds", {})
        self.grants = ent["iam"]["grants"]
        self.employees = ent["roster"]["employees"]
        self.by_id = {e["employee_id"]: e for e in self.employees}
        self.matrix = catalogs.authorization_matrix()
        self.sod_pairs = catalogs.sod_matrix()["pairs"]
        self._stints = {e["employee_id"]: roster.latest_stint(e)
                        for e in self.employees}
        self._functions = {e["employee_id"]: roster.current_function(e)
                           for e in self.employees}
        # exception register: (user, system, role) -> expiry date
        self.register = {}
        for x in ent["exceptions"]["exceptions"]:
            self.register[(x["user_id"], x["system"], x["role"])] = x["expires_at"]

    def latest_stint(self, eid):
        return self._stints[eid]

    def current_function(self, eid):
        return self._functions[eid]

    def in_roster(self, eid):
        return eid in self.by_id

    def active_grants(self):
        return [g for g in self.grants if g["status"] == "active"]

    def exception_for(self, uid, system, role):
        """Unexpired register entry, or None."""
        expiry = self.register.get((uid, system, role))
        if expiry is None:
            return None
        return expiry if expiry >= self.snapshot else None

    def expired_exception_for(self, uid, system, role):
        expiry = self.register.get((uid, system, role))
        if expiry is not None and expiry < self.snapshot:
            return expiry
        return None


def run_access_review(ent):
    """Run every access rule; returns a list of RuleResult in rule order."""
    from access.rules import ACCESS_RULES
    return run_rules(ACCESS_RULES, AccessView(ent))
