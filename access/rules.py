"""The seven access-review rules.

Each rule declares its population, criterion, and limitations as data, and
emits findings whose rationale is specific enough to review without
re-deriving the analytic (lab D-014). Findings are leads, never
determinations (D-003): the language here names conditions — remains
active, no recorded owner, outside the matrix — and leaves conclusions to
the reviewer. Refusals (missing threshold, empty population, absent
roster) render inconclusive, never pass (D-005/D-008).
"""

from core.rules import Finding, Rule
from enterprise import dates


def _days(earlier, later):
    return dates.days_between(earlier, later)


class TerminatedButActive(Rule):
    rule_id = "ACC-TERM"
    title = "Terminated employees with active access"
    criterion = ("An account is a lead when its holder's latest employment "
                 "stint ended in termination more than the grace period "
                 "before the snapshot and the grant is still active.")
    population_desc = ("All active user-account grants held by employees "
                       "present in the HR roster, as of the snapshot "
                       "(complete examination, no sampling).")
    limitations = (
        "Relies on roster completeness: a termination missing from HR data "
        "is invisible to this reconciliation.",
        "Evaluates the latest employment stint, so rehired employees are "
        "not flagged for earlier terminations; a data feed that drops "
        "rehire events would change results.",
        "Grant status is taken from the IAM export; actual authentication "
        "activity is not examined.",
    )
    required_thresholds = ("termination_grace_days",)
    designed_for = ("access.terminated_active",)

    def population(self, view):
        return [g for g in view.active_grants()
                if g["account_type"] == "user" and view.in_roster(g["user_id"])]

    def find(self, view, population):
        grace = view.thresholds["termination_grace_days"]
        out = []
        for g in population:
            seg = view.latest_stint(g["user_id"])
            if seg["closed_by"] != "termination":
                continue
            days = _days(seg["end"], view.snapshot)
            if days > grace:
                out.append(Finding(
                    rule_id=self.rule_id,
                    record_ids=(g["grant_id"],),
                    subject=g["user_id"],
                    rationale=("Account remains active {0} days after the "
                               "{1} termination; the disablement SLA is {2} "
                               "days.".format(days, seg["end"], grace)),
                    detail={"system": g["system"], "role": g["role"],
                            "termination_date": seg["end"],
                            "days_since_termination": days,
                            "grace_days": grace},
                ))
        return out


class OrphanedAccounts(Rule):
    rule_id = "ACC-ORPH"
    title = "Accounts with no corresponding employee"
    criterion = ("An active user account is a lead when its user id does "
                 "not appear anywhere in the HR roster for the period.")
    population_desc = ("All active user-account grants in the IAM export, "
                       "reconciled against the full HR roster (complete "
                       "examination).")
    limitations = (
        "Reconciliation is by user id: an account mapped to the wrong "
        "employee id would not be flagged here.",
        "Contractors or system identities absent from the HR feed by design "
        "would appear as leads; the reviewer disposes of them with the "
        "population owner.",
    )
    designed_for = ("access.orphan_account",)

    def extra_applicable(self, view):
        if not view.employees:
            return ("HR roster is empty — reconciliation against the "
                    "roster is impossible")
        return None

    def population(self, view):
        return [g for g in view.active_grants() if g["account_type"] == "user"]

    def find(self, view, population):
        out = []
        for g in population:
            if not view.in_roster(g["user_id"]):
                out.append(Finding(
                    rule_id=self.rule_id,
                    record_ids=(g["grant_id"],),
                    subject=g["user_id"],
                    rationale=("Active {0} account is assigned to user id "
                               "{1}, which does not appear in the HR roster "
                               "for the period.".format(g["system"],
                                                        g["user_id"])),
                    detail={"system": g["system"], "role": g["role"],
                            "granted_date": g["granted_date"],
                            "granted_by": g["granted_by"]},
                ))
        return out


class DormantPrivileged(Rule):
    rule_id = "ACC-DORM"
    title = "Dormant privileged access"
    criterion = ("A privileged grant is a lead when its last recorded use "
                 "is older than the dormancy threshold, or when no use is "
                 "recorded at all.")
    population_desc = ("All active grants carrying a privileged role, "
                       "across user, service, and shared accounts "
                       "(complete examination).")
    limitations = (
        "Last-used dates come from the IAM export, not from authentication "
        "logs; usage the export does not capture is invisible.",
        "Dormancy is a staleness screen: legitimate break-glass access can "
        "be dormant by design, which is a matter for the reviewer.",
    )
    required_thresholds = ("dormant_privileged_days",)
    designed_for = ("access.dormant_privileged",)

    def population(self, view):
        return [g for g in view.active_grants() if g["privileged"]]

    def find(self, view, population):
        threshold = view.thresholds["dormant_privileged_days"]
        out = []
        for g in population:
            subject = g["user_id"] or g["account_name"]
            if g["last_used_date"] is None:
                out.append(Finding(
                    rule_id=self.rule_id, record_ids=(g["grant_id"],),
                    subject=subject,
                    rationale=("Privileged role {0} on {1} has no recorded "
                               "use; the dormancy threshold is {2} days."
                               .format(g["role"], g["system"], threshold)),
                    detail={"system": g["system"], "role": g["role"],
                            "last_used_date": None,
                            "threshold_days": threshold},
                ))
                continue
            days = _days(g["last_used_date"], view.snapshot)
            if days > threshold:
                out.append(Finding(
                    rule_id=self.rule_id, record_ids=(g["grant_id"],),
                    subject=subject,
                    rationale=("Privileged role {0} on {1} last used {2} "
                               "days before the snapshot; the dormancy "
                               "threshold is {3} days.".format(
                                   g["role"], g["system"], days, threshold)),
                    detail={"system": g["system"], "role": g["role"],
                            "last_used_date": g["last_used_date"],
                            "days_unused": days,
                            "threshold_days": threshold},
                ))
        return out


class RoleAuthorizationMismatch(Rule):
    rule_id = "ACC-AUTH"
    title = "Roles outside the authorization matrix"
    criterion = ("An active grant is a lead when its role is not authorized "
                 "for the holder's current job function and no unexpired "
                 "recorded exception covers it.")
    population_desc = ("All active user-account grants held by roster "
                       "employees whose employment stint is open at the "
                       "snapshot (complete examination).")
    limitations = (
        "The matrix is evaluated against the holder's job function at the "
        "snapshot; access that was proper under a prior function appears "
        "here once the function changes.",
        "Recorded exceptions are honored at face value; whether an "
        "exception SHOULD have been granted is a reviewer judgment.",
        "A job function absent from the matrix yields a coverage lead for "
        "every grant its holders carry, not a pass.",
    )
    # SoD plants are usually ALSO off-matrix and will surface here too, but
    # the designed detector for that class is ACC-SOD (manifest notes say so).
    designed_for = ("access.role_mismatch",)

    def extra_applicable(self, view):
        if not view.matrix:
            return "authorization matrix is empty — no criterion to apply"
        return None

    def population(self, view):
        return [g for g in view.active_grants()
                if g["account_type"] == "user"
                and view.in_roster(g["user_id"])
                and view.current_function(g["user_id"]) is not None]

    def find(self, view, population):
        out = []
        for g in population:
            uid = g["user_id"]
            function = view.current_function(uid)
            sys_role = "{0}:{1}".format(g["system"], g["role"])
            if function not in view.matrix:
                out.append(Finding(
                    rule_id=self.rule_id, record_ids=(g["grant_id"],),
                    subject=uid,
                    rationale=("Job function {0} does not appear in the "
                               "authorization matrix, so role {1} cannot be "
                               "evaluated as authorized (matrix coverage "
                               "lead).".format(function, sys_role)),
                    detail={"job_function": function, "role": sys_role,
                            "matrix_gap": True},
                ))
                continue
            if sys_role in view.matrix[function]:
                continue
            if view.exception_for(uid, g["system"], g["role"]) is not None:
                continue
            expired = view.expired_exception_for(uid, g["system"], g["role"])
            if expired:
                rationale = ("Role {0} is outside the authorization matrix "
                             "for job function {1}; the recorded exception "
                             "expired {2}.".format(sys_role, function, expired))
            else:
                rationale = ("Role {0} is outside the authorization matrix "
                             "for job function {1}, and no recorded "
                             "exception applies.".format(sys_role, function))
            out.append(Finding(
                rule_id=self.rule_id, record_ids=(g["grant_id"],),
                subject=uid, rationale=rationale,
                detail={"job_function": function, "role": sys_role,
                        "expired_exception": expired},
            ))
        return out


class ToxicCombinations(Rule):
    rule_id = "ACC-SOD"
    title = "Segregation-of-duties toxic combinations"
    criterion = ("A user is a lead when their active grants include both "
                 "sides of a pair the SoD matrix declares conflicting.")
    population_desc = ("All roster employees holding at least one active "
                       "grant, each evaluated against every SoD pair "
                       "(complete examination at the user level).")
    limitations = (
        "Only pairs declared in the SoD matrix are evaluated; conflicts "
        "the matrix does not name are not screened.",
        "The register of cross-functional exceptions does not waive SoD "
        "conflicts here: compensating controls are a reviewer judgment "
        "outside this data.",
        "Conflicts across separate accounts of the same person in "
        "different systems are matched by employee id only.",
    )
    designed_for = ("access.sod_conflict",)

    def extra_applicable(self, view):
        if not view.sod_pairs:
            return "SoD matrix declares no pairs — no criterion to apply"
        return None

    def population(self, view):
        held = {}
        for g in view.active_grants():
            if g["account_type"] == "user" and view.in_roster(g["user_id"]):
                held.setdefault(g["user_id"], []).append(g)
        return sorted(held.items())

    def find(self, view, population):
        out = []
        for uid, grants in population:
            by_role = {}
            for g in grants:
                by_role.setdefault(
                    "{0}:{1}".format(g["system"], g["role"]), []).append(g)
            for pair in view.sod_pairs:
                if pair["a"] in by_role and pair["b"] in by_role:
                    ids = tuple(sorted(
                        g["grant_id"]
                        for sr in (pair["a"], pair["b"])
                        for g in by_role[sr]))
                    out.append(Finding(
                        rule_id=self.rule_id, record_ids=ids, subject=uid,
                        rationale=("User holds both {0} and {1}. {2}"
                                   .format(pair["a"], pair["b"],
                                           pair["conflict"])),
                        detail={"pair": [pair["a"], pair["b"]],
                                "conflict": pair["conflict"]},
                    ))
        return out


class ServiceAccountHygiene(Rule):
    rule_id = "ACC-SVC"
    title = "Service and shared account ownership"
    criterion = ("A service or shared account is a lead when it has no "
                 "recorded owner, or its owner is not an active employee.")
    population_desc = ("All active grants on service and shared accounts "
                       "(complete examination).")
    limitations = (
        "Ownership is the only hygiene attribute in this export; password "
        "rotation, vaulting, and interactive-logon restrictions are not "
        "visible here.",
    )
    designed_for = ("access.service_account_no_owner",)

    def population(self, view):
        return [g for g in view.active_grants()
                if g["account_type"] in ("service", "shared")]

    def find(self, view, population):
        out = []
        for g in population:
            owner = g["owner_id"]
            if owner is None:
                rationale = ("{0} account {1} has no recorded owner."
                             .format(g["account_type"].capitalize(),
                                     g["account_name"]))
                detail = {"owner_id": None}
            elif not view.in_roster(owner):
                rationale = ("{0} account {1} lists owner {2}, who does not "
                             "appear in the HR roster.".format(
                                 g["account_type"].capitalize(),
                                 g["account_name"], owner))
                detail = {"owner_id": owner, "owner_in_roster": False}
            elif view.latest_stint(owner)["end"] is not None:
                rationale = ("{0} account {1} lists owner {2}, whose "
                             "employment ended {3}.".format(
                                 g["account_type"].capitalize(),
                                 g["account_name"], owner,
                                 view.latest_stint(owner)["end"]))
                detail = {"owner_id": owner,
                          "owner_end": view.latest_stint(owner)["end"]}
            else:
                continue
            out.append(Finding(
                rule_id=self.rule_id, record_ids=(g["grant_id"],),
                subject=g["account_name"], rationale=rationale,
                detail=dict(detail, system=g["system"], role=g["role"]),
            ))
        return out


class RecertificationStaleness(Rule):
    rule_id = "ACC-CERT"
    title = "Access recertification staleness"
    criterion = ("An active grant is a lead when its last recertification "
                 "is older than the recertification cycle, or missing.")
    population_desc = ("All active grants across user, service, and shared "
                       "accounts (complete examination).")
    limitations = (
        "Certification dates attest that a review was recorded, not that "
        "it was substantive.",
    )
    required_thresholds = ("recert_cycle_days",)
    designed_for = ("access.recert_lapsed",)

    def population(self, view):
        return view.active_grants()

    def find(self, view, population):
        cycle = view.thresholds["recert_cycle_days"]
        out = []
        for g in population:
            subject = g["user_id"] or g["account_name"]
            if g["last_certified_date"] is None:
                out.append(Finding(
                    rule_id=self.rule_id, record_ids=(g["grant_id"],),
                    subject=subject,
                    rationale=("Grant of {0} on {1} carries no recorded "
                               "recertification; the cycle is {2} days."
                               .format(g["role"], g["system"], cycle)),
                    detail={"system": g["system"], "role": g["role"],
                            "last_certified_date": None,
                            "cycle_days": cycle},
                ))
                continue
            days = _days(g["last_certified_date"], view.snapshot)
            if days > cycle:
                out.append(Finding(
                    rule_id=self.rule_id, record_ids=(g["grant_id"],),
                    subject=subject,
                    rationale=("Grant of {0} on {1} was last recertified "
                               "{2} days before the snapshot; the cycle is "
                               "{3} days.".format(g["role"], g["system"],
                                                  days, cycle)),
                    detail={"system": g["system"], "role": g["role"],
                            "last_certified_date": g["last_certified_date"],
                            "days_since_certification": days,
                            "cycle_days": cycle},
                ))
        return out


ACCESS_RULES = (
    TerminatedButActive(),
    OrphanedAccounts(),
    DormantPrivileged(),
    RoleAuthorizationMismatch(),
    ToxicCombinations(),
    ServiceAccountHygiene(),
    RecertificationStaleness(),
)
