"""IAM access export, consistent with the roster by construction.

Clean-data invariants (tested in tests/test_iam_consistency.py):
- every user-account grant belongs to a roster employee;
- grants exist per employment segment: active exactly when the segment is
  open at the snapshot, otherwise disabled within the applicable SLA
  (termination grace / transfer cleanup);
- active privileged grants were used within the dormancy threshold;
- every active grant is either authorized by the matrix for the holder's
  current function or covered by a recorded exception (the sanctioned
  cross-functional benign look-alike, DECISIONS.md D-004);
- recertification dates sit inside the recert cycle;
- service and shared accounts always carry a live owner.

The violation injector (violations.py) breaks these invariants one property
at a time, never here: this module only ever emits a clean population.
"""

from . import catalogs, dates, roster
from core.canonical import content_hash

SERVICE_ROLE = {"crm": "crm-user", "deploy": "deploy-exec",
                "dir": "dir-admin", "erp": "erp-admin",
                "hris": "payroll-run", "mail": "mail-admin"}
SHARED_ROLE = {"crm": "crm-user", "deploy": "dev-commit",
               "dir": "user", "erp": "fin-report",
               "hris": "hr-user", "mail": "user"}

# Non-privileged roles offered as sanctioned cross-functional exceptions.
EXCEPTION_ROLES = ["crm:crm-report", "erp:fin-report", "crm:crm-user"]


def _grant_id(system, account_id, role, granted_date, seq):
    return "G-" + content_hash([system, account_id, role, granted_date, seq])


def _account_id(system, key):
    return "A-" + content_hash([system, key])


def _mk_grant(system, account_id, role, granted, granted_by, *, account_type,
              user_id=None, account_name=None, owner_id=None, seq=0):
    return {
        "grant_id": _grant_id(system, account_id, role, granted, seq),
        "system": system,
        "account_id": account_id,
        "account_name": account_name,
        "account_type": account_type,
        "user_id": user_id,
        "owner_id": owner_id,
        "role": role,
        "privileged": catalogs.is_privileged(system, role),
        "granted_date": granted,
        "granted_by": granted_by,
        "last_used_date": None,
        "last_certified_date": None,
        "status": "active",
        "disabled_date": None,
    }


def _cap(iso_s, snapshot):
    return snapshot if iso_s > snapshot else iso_s


def build_iam(rng, cfg, thresholds, employees, matrix):
    """Returns (grants sorted by grant_id, exceptions register)."""
    snapshot = cfg.snapshot
    grace = thresholds["termination_grace_days"]
    cleanup = thresholds["transfer_cleanup_days"]
    dormant = thresholds["dormant_privileged_days"]
    cycle = thresholds["recert_cycle_days"]

    sysadmins = sorted(
        e["employee_id"] for e in employees
        if any(seg["job_function"] == "system-administrator" for seg in roster.segments(e))
        and e["hire_date"] < dates.months_back(snapshot, cfg.months)
        and roster.current_function(e) == "system-administrator"
    )
    grants = []

    def finish_active(g, granted):
        """Usage + certification for a grant open at the snapshot."""
        recent = rng.randint(1, 30) if g["privileged"] else rng.randint(1, 60)
        assert recent < dormant
        used = dates.add_days(snapshot, -recent)
        g["last_used_date"] = max(granted, used)
        cert = dates.add_days(snapshot, -rng.randint(20, cycle - 25))
        g["last_certified_date"] = max(granted, cert)

    # --- user accounts, one per (employee, system), grants per segment ---
    for emp in employees:
        eid = emp["employee_id"]
        for seg in roster.segments(emp):
            granted = _cap(dates.add_days(seg["start"], rng.randint(0, 7)), snapshot)
            for seq, sys_role in enumerate(matrix[seg["job_function"]]):
                system, role = sys_role.split(":")
                account_id = _account_id(system, eid)
                g = _mk_grant(system, account_id, role, granted,
                              rng.choice(sysadmins), account_type="user",
                              user_id=eid, seq=seq)
                if seg["end"] is None:
                    finish_active(g, granted)
                else:
                    sla = grace if seg["closed_by"] == "termination" else cleanup
                    g["status"] = "disabled"
                    g["disabled_date"] = _cap(
                        dates.add_days(seg["end"], rng.randint(0, sla)), snapshot)
                    used = dates.add_days(seg["end"], -rng.randint(0, 10))
                    g["last_used_date"] = max(granted, used)
                    g["last_certified_date"] = granted
                grants.append(g)

    # --- sanctioned cross-functional exceptions (benign look-alike) ---
    exceptions = []
    active = [e for e in employees if e["status"] == "active"
              and e["hire_date"] < dates.months_back(snapshot, cfg.months)]
    active.sort(key=lambda e: e["employee_id"])
    approvers = sorted(
        e["employee_id"] for e in employees
        if roster.current_function(e) in ("controller", "system-administrator")
    )
    chosen = rng.sample(active, cfg.sanctioned_exceptions)
    chosen.sort(key=lambda e: e["employee_id"])
    for emp in chosen:
        held = matrix[roster.current_function(emp)]
        sys_role = next(sr for sr in EXCEPTION_ROLES if sr not in held)
        system, role = sys_role.split(":")
        eid = emp["employee_id"]
        granted = dates.add_days(snapshot, -rng.randint(60, 200))
        g = _mk_grant(system, _account_id(system, eid), role, granted,
                      rng.choice(sysadmins), account_type="user",
                      user_id=eid, seq=90)
        finish_active(g, granted)
        grants.append(g)
        approver = next(a for a in approvers if a != eid)
        exceptions.append({
            "exception_id": "X-" + content_hash([eid, sys_role, granted]),
            "user_id": eid,
            "system": system,
            "role": role,
            "reason": "Documented cross-functional duty requiring temporary "
                      "access outside the standard matrix.",
            "approved_by": approver,
            "approved_at": granted,
            "expires_at": dates.add_days(snapshot, rng.randint(90, 180)),
        })

    # --- service + shared accounts (owned, used, certified in clean data) ---
    owners = sorted(
        e["employee_id"] for e in employees
        if roster.current_function(e) in ("devops-engineer", "system-administrator")
    )
    window_start = dates.months_back(snapshot, cfg.months)
    for system in sorted(SERVICE_ROLE):
        for k in range(cfg.service_accounts_per_system):
            name = "svc-{0}-{1:02d}".format(system, k + 1)
            granted = dates.add_days(window_start, -rng.randint(60, 900))
            g = _mk_grant(system, _account_id(system, name), SERVICE_ROLE[system],
                          granted, rng.choice(sysadmins), account_type="service",
                          account_name=name, owner_id=rng.choice(owners))
            g["last_used_date"] = dates.add_days(snapshot, -rng.randint(0, 3))
            g["last_certified_date"] = dates.add_days(snapshot, -rng.randint(20, cycle - 25))
            grants.append(g)
        for k in range(cfg.shared_accounts_per_system):
            name = "shared-{0}-{1:02d}".format(system, k + 1)
            granted = dates.add_days(window_start, -rng.randint(60, 900))
            g = _mk_grant(system, _account_id(system, name), SHARED_ROLE[system],
                          granted, rng.choice(sysadmins), account_type="shared",
                          account_name=name, owner_id=rng.choice(owners))
            g["last_used_date"] = dates.add_days(snapshot, -rng.randint(0, 14))
            g["last_certified_date"] = dates.add_days(snapshot, -rng.randint(20, cycle - 25))
            grants.append(g)

    grants.sort(key=lambda g: g["grant_id"])
    exceptions.sort(key=lambda x: x["exception_id"])
    return grants, exceptions
