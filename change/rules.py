"""The six change-management rules.

Same contract as the access rules: census populations, per-finding
rationales, three outcomes, refusal on missing configuration. The
properly-handled weekend emergency — deployed Saturday, approved Sunday,
reviewed within the SLA — is a documented benign look-alike (D-004) and
must never surface here; the rules therefore distinguish "no prior
approval" (expected for emergencies, covered by post-hoc review) from "no
approval at all".
"""

from core.rules import Finding, Rule
from enterprise import dates
from enterprise.tickets import in_freeze


class MissingApproval(Rule):
    rule_id = "CHG-APPR"
    title = "Deployed changes without approval"
    criterion = ("A deployed change is a lead when no approval is recorded "
                 "at all, or — for non-emergency changes — when the "
                 "recorded approval postdates the deployment.")
    population_desc = ("All change tickets with at least one matching "
                       "deploy-log entry (complete examination).")
    limitations = (
        "Approval is evidenced by ticket fields only; an approval given "
        "out-of-band and never recorded is indistinguishable from none.",
        "Emergency changes are expected to be approved after deployment; "
        "their post-hoc review is examined by CHG-EMER, not here.",
    )
    designed_for = ("change.missing_approval",)

    def population(self, view):
        return view.deployed_tickets()

    def find(self, view, population):
        out = []
        for t in population:
            deploys = view.deploys_of(t["ticket_id"])
            first_deploy = min(d["deployed_at"] for d in deploys)
            deploy_ids = tuple(sorted(d["deploy_id"] for d in deploys))
            if t["approved_at"] is None or t["approver_id"] is None:
                out.append(Finding(
                    rule_id=self.rule_id,
                    record_ids=(t["ticket_id"],) + deploy_ids,
                    subject=t["ticket_id"],
                    rationale=("Change {0} on {1} was deployed {2} with no "
                               "approval recorded on the ticket.".format(
                                   t["ticket_id"], t["system"], first_deploy)),
                    detail={"system": t["system"],
                            "change_type": t["change_type"],
                            "deployed_at": first_deploy},
                ))
            elif (t["change_type"] != "emergency"
                    and t["approved_at"] > first_deploy):
                out.append(Finding(
                    rule_id=self.rule_id,
                    record_ids=(t["ticket_id"],) + deploy_ids,
                    subject=t["ticket_id"],
                    rationale=("Non-emergency change {0} was deployed {1} "
                               "but approved {2}, after deployment.".format(
                                   t["ticket_id"], first_deploy,
                                   t["approved_at"])),
                    detail={"system": t["system"],
                            "approved_at": t["approved_at"],
                            "deployed_at": first_deploy},
                ))
        return out


class SelfApproval(Rule):
    rule_id = "CHG-SELF"
    title = "Changes approved by their own developer"
    criterion = ("A ticket is a lead when the recorded approver is the "
                 "same person as the recorded developer.")
    population_desc = ("All change tickets carrying both a developer and "
                       "an approver (complete examination).")
    limitations = (
        "Identity is matched on employee id; the same human behind two "
        "ids would not be caught here.",
        "Requester/approver overlap is not screened — the segregation "
        "examined is develop-versus-approve.",
    )
    designed_for = ("change.self_approval",)

    def population(self, view):
        return [t for t in view.tickets
                if t["developer_id"] is not None
                and t["approver_id"] is not None]

    def find(self, view, population):
        out = []
        for t in population:
            if t["approver_id"] == t["developer_id"]:
                deploy_ids = tuple(sorted(
                    d["deploy_id"] for d in view.deploys_of(t["ticket_id"])))
                out.append(Finding(
                    rule_id=self.rule_id,
                    record_ids=(t["ticket_id"],) + deploy_ids,
                    subject=t["ticket_id"],
                    rationale=("Change {0} on {1} records {2} as both "
                               "developer and approver.".format(
                                   t["ticket_id"], t["system"],
                                   t["developer_id"])),
                    detail={"system": t["system"],
                            "developer_id": t["developer_id"]},
                ))
        return out


class EmergencyReview(Rule):
    rule_id = "CHG-EMER"
    title = "Emergency changes without timely post-hoc review"
    criterion = ("A deployed emergency change is a lead when no post-hoc "
                 "review is recorded, when the review falls outside the "
                 "SLA window after deployment, or when the reviewer is the "
                 "developer.")
    population_desc = ("All emergency change tickets with a matching "
                       "deploy-log entry (complete examination).")
    limitations = (
        "The review is evidenced by two ticket fields; its substance is "
        "not examined.",
        "Properly-reviewed emergencies deployed on weekends are expected "
        "and are not leads.",
    )
    required_thresholds = ("emergency_review_days",)
    designed_for = ("change.emergency_no_review",)

    def population(self, view):
        return [t for t in view.deployed_tickets()
                if t["change_type"] == "emergency"]

    def find(self, view, population):
        sla = view.thresholds["emergency_review_days"]
        out = []
        for t in population:
            deploys = view.deploys_of(t["ticket_id"])
            first_deploy = min(d["deployed_at"] for d in deploys)
            deploy_ids = tuple(sorted(d["deploy_id"] for d in deploys))
            problem = None
            detail = {"system": t["system"], "deployed_at": first_deploy,
                      "sla_days": sla}
            if t["post_review_at"] is None or t["post_review_by"] is None:
                problem = ("no post-hoc review is recorded within the "
                           "{0}-day window".format(sla))
                detail["post_review_at"] = None
            elif dates.days_between(first_deploy, t["post_review_at"]) > sla:
                late = dates.days_between(first_deploy, t["post_review_at"])
                problem = ("the post-hoc review is dated {0} days after "
                           "deployment against a {1}-day window"
                           .format(late, sla))
                detail["post_review_at"] = t["post_review_at"]
                detail["days_to_review"] = late
            elif t["post_review_by"] == t["developer_id"]:
                problem = ("the post-hoc review was recorded by the "
                           "developer of the change")
                detail["post_review_by"] = t["post_review_by"]
            if problem:
                out.append(Finding(
                    rule_id=self.rule_id,
                    record_ids=(t["ticket_id"],) + deploy_ids,
                    subject=t["ticket_id"],
                    rationale=("Emergency change {0} on {1} was deployed "
                               "{2}, and {3}.".format(
                                   t["ticket_id"], t["system"],
                                   first_deploy, problem)),
                    detail=detail,
                ))
        return out


class DeployWithoutTicket(Rule):
    rule_id = "CHG-TICK"
    title = "Deploy-log entries with no matching ticket"
    criterion = ("A deploy-log entry is a lead when it references no "
                 "ticket, or references a ticket id that does not exist "
                 "in the ticket system.")
    population_desc = ("All deploy-log entries, reconciled against the "
                       "full ticket export (complete examination).")
    limitations = (
        "Reconciliation is by ticket id: a deploy attached to the WRONG "
        "ticket reconciles cleanly and is not caught here.",
    )
    designed_for = ("change.deploy_without_ticket",)

    def population(self, view):
        return view.deploys

    def find(self, view, population):
        out = []
        for d in population:
            tid = d["ticket_id"]
            if tid is not None and tid in view.ticket_by_id:
                continue
            if tid is None:
                why = "references no change ticket"
            else:
                why = ("references ticket id {0}, which does not exist in "
                       "the ticket system".format(tid))
            out.append(Finding(
                rule_id=self.rule_id,
                record_ids=(d["deploy_id"],),
                subject=d["deploy_id"],
                rationale=("Deployment to {0} on {1} by {2} {3}.".format(
                    d["system"], d["deployed_at"], d["deployed_by"], why)),
                detail={"system": d["system"],
                        "deployed_at": d["deployed_at"],
                        "ticket_ref": tid},
            ))
        return out


class FreezeViolation(Rule):
    rule_id = "CHG-FRZ"
    title = "Deployments inside change-freeze windows"
    criterion = ("A deploy-log entry is a lead when its deployment date "
                 "falls inside a declared change-freeze window.")
    population_desc = ("All deploy-log entries, tested against every "
                       "declared freeze window (complete examination).")
    limitations = (
        "Freeze windows are taken from policy data; ad-hoc freezes "
        "announced elsewhere are invisible.",
        "No exemption mechanism exists in this data: an authorized "
        "in-freeze deployment would still surface as a lead for the "
        "reviewer to dispose of.",
    )
    designed_for = ("change.freeze_violation",)

    def extra_applicable(self, view):
        if view.freezes is None:
            return ("policy declares no freeze_windows artifact — nothing "
                    "to test against")
        if not view.freezes:
            return ("freeze window list is empty — no freeze periods are "
                    "declared for this window")
        return None

    def population(self, view):
        return view.deploys

    def find(self, view, population):
        out = []
        for d in population:
            if not in_freeze(d["deployed_at"], view.freezes):
                continue
            window = next(f for f in view.freezes
                          if f["start"] <= d["deployed_at"] <= f["end"])
            record_ids = (d["deploy_id"],)
            if d["ticket_id"] in view.ticket_by_id:
                record_ids = (d["ticket_id"], d["deploy_id"])
            out.append(Finding(
                rule_id=self.rule_id,
                record_ids=record_ids,
                subject=d["deploy_id"],
                rationale=("Deployment to {0} on {1} falls inside the "
                           "freeze window {2} to {3} ({4}).".format(
                               d["system"], d["deployed_at"],
                               window["start"], window["end"],
                               window["reason"])),
                detail={"system": d["system"],
                        "deployed_at": d["deployed_at"],
                        "freeze_start": window["start"],
                        "freeze_end": window["end"]},
            ))
        return out


class StaleTickets(Rule):
    rule_id = "CHG-STAL"
    title = "Approved changes never deployed"
    criterion = ("An approved, undeployed ticket is a REVIEW LEAD — a "
                 "recordkeeping question, not by itself an exception — "
                 "once its approval is older than the staleness threshold.")
    population_desc = ("All change tickets with an approval recorded and "
                       "no matching deploy-log entry (complete "
                       "examination).")
    limitations = (
        "An aged open ticket may be legitimately deferred work; this rule "
        "measures recordkeeping hygiene, and the lead sheet carries it as "
        "a review item rather than an exception to a control.",
    )
    required_thresholds = ("stale_ticket_days",)
    designed_for = ("change.stale_ticket",)

    def population(self, view):
        return [t for t in view.tickets
                if t["approved_at"] is not None
                and not view.deploys_of(t["ticket_id"])]

    def find(self, view, population):
        threshold = view.thresholds["stale_ticket_days"]
        out = []
        for t in population:
            age = dates.days_between(t["approved_at"], view.snapshot)
            if age > threshold:
                out.append(Finding(
                    rule_id=self.rule_id,
                    record_ids=(t["ticket_id"],),
                    subject=t["ticket_id"],
                    rationale=("Change {0} on {1} was approved {2} days "
                               "before the snapshot and has no deployment "
                               "record; the staleness threshold is {3} "
                               "days. Review lead: confirm disposition "
                               "with the change owner.".format(
                                   t["ticket_id"], t["system"], age,
                                   threshold)),
                    detail={"system": t["system"],
                            "approved_at": t["approved_at"],
                            "age_days": age,
                            "threshold_days": threshold},
                ))
        return out


CHANGE_RULES = (
    MissingApproval(),
    SelfApproval(),
    EmergencyReview(),
    DeployWithoutTicket(),
    FreezeViolation(),
    StaleTickets(),
)
