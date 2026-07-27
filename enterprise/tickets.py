"""Change tickets and deploy log, clean by construction.

Clean-data invariants (tested):
- every deploy-log entry references an existing ticket;
- standard/normal changes: approval precedes deployment, approver is
  neither the developer nor the requester;
- emergency changes may be approved after deployment but carry a post-hoc
  review within the SLA — the properly-handled weekend emergency is a
  mandatory benign look-alike (DECISIONS.md D-004);
- no clean deploy lands inside a freeze window;
- every approved ticket is either deployed or younger than the stale
  threshold (the open-recent benign population).
"""

from . import dates, roster
from core.canonical import content_hash

SYSTEM_WEIGHTS = [("deploy", 40), ("erp", 25), ("crm", 20), ("hris", 15)]

SUMMARIES = {
    "crm": "Scheduled CRM configuration update",
    "deploy": "Scheduled pipeline release",
    "erp": "Scheduled ERP maintenance change",
    "hris": "Scheduled HR platform update",
}

# Routine tickets stop this many days before the snapshot so that approval,
# deployment, weekend shifts, and freeze dodging can never spill past it.
ROUTINE_CUTOFF_DAYS = 25


def freeze_windows(window_start, snapshot):
    return [
        {"start": dates.add_days(qe, -2), "end": qe,
         "reason": "Quarter-end change freeze"}
        for qe in dates.quarter_ends(window_start, snapshot)
    ]


def in_freeze(iso_day, freezes):
    return any(f["start"] <= iso_day <= f["end"] for f in freezes)


def _ticket_id(system, created, requester, k):
    return "CHG-" + content_hash([system, created, requester, k])


def _deploy_id(ticket_id, system):
    return "DPL-" + content_hash([ticket_id, system])


def _weighted_system(rng):
    total = sum(w for _, w in SYSTEM_WEIGHTS)
    pick = rng.uniform(0, total)
    acc = 0.0
    for system, w in SYSTEM_WEIGHTS:
        acc += w
        if pick <= acc:
            return system
    return SYSTEM_WEIGHTS[-1][0]


def _mk_ticket(tid, system, change_type, status, requester, developer,
               approver, created, approved):
    return {
        "ticket_id": tid,
        "system": system,
        "change_type": change_type,
        "summary": "{0} ({1})".format(SUMMARIES[system], tid[-6:]),
        "status": status,
        "requester_id": requester,
        "developer_id": developer,
        "approver_id": approver,
        "created_at": created,
        "approved_at": approved,
        "post_review_by": None,
        "post_review_at": None,
    }


def build_tickets(rng, cfg, thresholds, employees):
    """Returns (tickets sorted by id, deploys sorted by id, freeze windows)."""
    snapshot = cfg.snapshot
    window_start = dates.months_back(snapshot, cfg.months)
    freezes = freeze_windows(window_start, snapshot)
    review_sla = thresholds["emergency_review_days"]
    stale_days = thresholds["stale_ticket_days"]

    developers = sorted(
        e["employee_id"] for e in employees
        if roster.current_function(e) in ("software-developer", "devops-engineer")
        and e["hire_date"] < window_start
    )
    approver_pool = sorted(
        e["employee_id"] for e in employees
        if roster.current_function(e) in
        ("controller", "qa-analyst", "system-administrator", "security-analyst")
        and e["hire_date"] < window_start
    )
    by_id = {e["employee_id"]: e for e in employees}
    all_ids = sorted(by_id)

    def requester_at(day):
        pool = [eid for eid in all_ids if roster.is_active_at(by_id[eid], day)]
        return rng.choice(pool)

    tickets, deploys = [], []
    k = 0

    # --- routine pipeline: created early enough to complete by snapshot ---
    routine_last = dates.add_days(snapshot, -ROUTINE_CUTOFF_DAYS)
    for m_start in dates.month_starts(window_start, snapshot):
        for _ in range(cfg.tickets_per_month):
            k += 1
            created = dates.add_days(m_start, rng.randint(0, 25))
            if created < window_start or created > routine_last:
                continue
            system = _weighted_system(rng)
            developer = rng.choice(developers)
            approver = rng.choice([a for a in approver_pool if a != developer])
            requester = requester_at(created)
            approved = dates.add_days(created, rng.randint(1, 5))
            deployed = dates.next_business_day(
                dates.add_days(approved, rng.randint(0, 3)))
            while in_freeze(deployed, freezes):
                deployed = dates.next_business_day(dates.add_days(deployed, 1))
            change_type = "standard" if rng.random() < 0.6 else "normal"
            tid = _ticket_id(system, created, requester, k)
            tickets.append(_mk_ticket(tid, system, change_type, "closed",
                                      requester, developer, approver,
                                      created, approved))
            deploys.append({
                "deploy_id": _deploy_id(tid, system),
                "system": system,
                "ticket_id": tid,
                "deployed_by": developer,
                "deployed_at": deployed,
            })

    # --- benign: approved, not yet deployed, younger than the stale bar ---
    for _ in range(cfg.open_recent_tickets):
        k += 1
        created = dates.add_days(snapshot, -rng.randint(3, stale_days - 5))
        system = _weighted_system(rng)
        developer = rng.choice(developers)
        approver = rng.choice([a for a in approver_pool if a != developer])
        tid = _ticket_id(system, created, developer, k)
        tickets.append(_mk_ticket(tid, system, "normal", "approved",
                                  developer, developer, approver,
                                  created, dates.add_days(created, 1)))

    # --- benign: weekend emergency changes WITH proper post-hoc review ---
    weekend_days = [
        s for s in dates.saturdays(dates.add_days(window_start, 7),
                                   dates.add_days(snapshot, -10))
        if not in_freeze(s, freezes)
    ]
    picked = rng.sample(weekend_days, cfg.proper_emergencies)
    for day in sorted(picked):
        k += 1
        system = _weighted_system(rng)
        developer = rng.choice(developers)
        approver = rng.choice([a for a in approver_pool if a != developer])
        reviewer = rng.choice(
            [a for a in approver_pool if a not in (developer, approver)])
        tid = _ticket_id(system, day, developer, k)
        t = _mk_ticket(tid, system, "emergency", "closed", developer,
                       developer, approver, day,
                       dates.add_days(day, 1))          # approved post-deploy
        t["post_review_by"] = reviewer
        t["post_review_at"] = dates.add_days(day, rng.randint(2, review_sla - 1))
        tickets.append(t)
        deploys.append({
            "deploy_id": _deploy_id(tid, system),
            "system": system,
            "ticket_id": tid,
            "deployed_by": developer,
            "deployed_at": day,                          # Saturday, on purpose
        })

    tickets.sort(key=lambda t: t["ticket_id"])
    deploys.sort(key=lambda d: d["deploy_id"])
    return tickets, deploys, freezes
