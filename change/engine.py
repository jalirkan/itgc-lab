"""Change-management engine: shared view + rule runner."""

from core.rules import run_rules


class ChangeView:
    """Read-only, precomputed joins the change rules share."""

    def __init__(self, ent):
        self.ent = ent
        self.snapshot = ent["policy"]["snapshot"]
        self.thresholds = ent["policy"].get("thresholds", {})
        self.tickets = ent["tickets"]["tickets"]
        self.deploys = ent["deploys"]["deploys"]
        self.freezes = ent["policy"].get("freeze_windows")
        self.ticket_by_id = {t["ticket_id"]: t for t in self.tickets}
        self.deploy_by_ticket = {}
        for d in self.deploys:
            self.deploy_by_ticket.setdefault(d["ticket_id"], []).append(d)

    def deploys_of(self, ticket_id):
        return self.deploy_by_ticket.get(ticket_id, [])

    def deployed_tickets(self):
        return [t for t in self.tickets
                if self.deploy_by_ticket.get(t["ticket_id"])]


def run_change_review(ent):
    from change.rules import CHANGE_RULES
    return run_rules(CHANGE_RULES, ChangeView(ent))
