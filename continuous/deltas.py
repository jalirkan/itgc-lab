"""Continuous mode: snapshot pairs, deltas, lead aging, recert tracking.

Two building blocks:

- `as_of(ent, day)` — the time-travel reducer. It rebuilds the export the
  same organization would have produced on an earlier day: roster events
  after `day` have not happened, grants issued later do not exist, a
  disablement dated later has not occurred, approvals and reviews dated
  later are absent, and usage/certification dates are capped at `day`.
  Two modelling assumptions are documented rather than hidden: last use
  as of `day` is `min(last_used, day)` (steady-usage assumption), and a
  certification dated after `day` reverts to the provisioning-date
  certification, the only earlier one this data model records. An as-of
  view can legitimately catch the organization MID-SLA (a mover inside
  the cleanup window shows residual access), so intermediate-date rule
  runs may carry leads that the month-end view resolves — that is
  fidelity, not noise.

  What the reducer deliberately does NOT rebuild is the configuration
  baseline. That export records what each system was observed to be set
  to AT THE SNAPSHOT and carries no history of changes, so there is no
  honest way to say what it read a month earlier; carrying the current
  settings backwards would manufacture evidence that a baseline held on
  a date nobody sampled it. The reduced export therefore has no
  `configs` artifact at all, which makes the baseline rules refuse on it
  (their "export is absent" path) rather than grade a borrowed one — an
  absence that reports itself, per D-008.

- `compare_snapshots(prior, current)` — census deltas between two
  exports: new/removed grants, new privileged access, newly dormant
  privileged access, terminations in the window, recert lapses and
  coming-due, and a population drift profile. Counts are exact census
  facts and are always stated with their populations; nothing here is a
  sampling inference, so nothing here carries an interval (lab's
  exact-counts discipline; intervals attach to inference, D-005).

Lead aging (`age_leads`) matches finding identity across the pair:
persisting leads carry `min_age_days` equal to the pair window — a pair
establishes a LOWER BOUND on age, and the output says so.
"""

import copy

from enterprise import dates

AGING_NOTE = ("Ages from a snapshot pair are lower bounds: a lead present "
              "at both snapshots is at least the window old; its true "
              "first appearance may be earlier.")


# --------------------------------------------------------------------------
# as-of reducer
# --------------------------------------------------------------------------

def _roster_as_of(roster, day):
    employees = []
    terminations = []
    for emp in roster["employees"]:
        if emp["hire_date"] > day:
            continue
        e = copy.deepcopy(emp)
        e["history"] = [ev for ev in e["history"] if ev["date"] <= day]
        seg_end = None
        seg_closed_by = None
        current = None
        for ev in e["history"]:
            if ev["event"] in ("hire", "rehire", "transfer"):
                current = ev
                seg_end = None
                seg_closed_by = None
            elif ev["event"] == "termination":
                seg_end = ev["date"]
                seg_closed_by = "termination"
        e["department"] = current["department"]
        e["job_function"] = current["job_function"]
        e["status"] = "terminated" if seg_closed_by == "termination" else "active"
        e["termination_date"] = seg_end if seg_closed_by == "termination" else None
        employees.append(e)
        for ev in e["history"]:
            if ev["event"] == "termination":
                terminations.append({
                    "employee_id": e["employee_id"],
                    "termination_date": ev["date"],
                    "department": ev["department"],
                    "job_function": ev["job_function"],
                })
    terminations.sort(key=lambda t: (t["termination_date"], t["employee_id"]))
    return {"schema_version": roster["schema_version"], "kind": "roster",
            "employees": employees, "terminations": terminations}


def _grant_as_of(g, day):
    if g["granted_date"] > day:
        return None
    out = copy.deepcopy(g)
    if out["disabled_date"] is not None and out["disabled_date"] <= day:
        out["status"] = "disabled"
    else:
        out["status"] = "active"
        out["disabled_date"] = None
    if out["last_used_date"] is not None:
        out["last_used_date"] = min(out["last_used_date"], day)
    cert = out["last_certified_date"]
    if cert is not None and cert > day:
        # The later certification has not happened yet; the one on record
        # at `day` is the provisioning-date certification (documented
        # modelling assumption).
        out["last_certified_date"] = out["granted_date"]
    return out


def _ticket_as_of(t, day, deployed_by_day):
    if t["created_at"] > day:
        return None
    out = copy.deepcopy(t)
    if out["approved_at"] is not None and out["approved_at"] > day:
        out["approved_at"] = None
        out["approver_id"] = None
    if out["post_review_at"] is not None and out["post_review_at"] > day:
        out["post_review_at"] = None
        out["post_review_by"] = None
    if deployed_by_day:
        out["status"] = "closed"
    elif out["approved_at"] is not None:
        out["status"] = "approved"
    else:
        out["status"] = "open"
    return out


def as_of(ent, day):
    """The export this enterprise would have produced on `day`."""
    if day > ent["policy"]["snapshot"]:
        raise ValueError("as_of day is after the generated snapshot; the "
                         "generator, not a reducer, owns the future")
    reduced = {}
    reduced["roster"] = _roster_as_of(ent["roster"], day)

    grants = []
    for g in ent["iam"]["grants"]:
        r = _grant_as_of(g, day)
        if r is not None:
            grants.append(r)
    reduced["iam"] = {"schema_version": ent["iam"]["schema_version"],
                      "kind": "iam", "grants": grants}

    deploys = [copy.deepcopy(d) for d in ent["deploys"]["deploys"]
               if d["deployed_at"] <= day]
    deployed_tickets = {d["ticket_id"] for d in deploys}
    tickets = []
    for t in ent["tickets"]["tickets"]:
        r = _ticket_as_of(t, day, t["ticket_id"] in deployed_tickets)
        if r is not None:
            tickets.append(r)
    reduced["tickets"] = {"schema_version": ent["tickets"]["schema_version"],
                          "kind": "tickets", "tickets": tickets}
    reduced["deploys"] = {"schema_version": ent["deploys"]["schema_version"],
                          "kind": "deploys", "deploys": deploys}

    # No `configs`: see the module docstring — a baseline observed only
    # at the snapshot cannot be reduced to an earlier day, and refusing
    # is the honest outcome.
    reduced["exceptions"] = {
        "schema_version": ent["exceptions"]["schema_version"],
        "kind": "exceptions",
        "exceptions": [copy.deepcopy(x)
                       for x in ent["exceptions"]["exceptions"]
                       if x["approved_at"] <= day],
    }
    policy = copy.deepcopy(ent["policy"])
    policy["snapshot"] = day
    reduced["policy"] = policy
    return reduced


# --------------------------------------------------------------------------
# snapshot-pair comparison
# --------------------------------------------------------------------------

def _active_grants(ent):
    return {g["grant_id"]: g for g in ent["iam"]["grants"]
            if g["status"] == "active"}


def _dormant_privileged_ids(ent):
    threshold = ent["policy"]["thresholds"]["dormant_privileged_days"]
    day = ent["policy"]["snapshot"]
    out = set()
    for g in ent["iam"]["grants"]:
        if g["status"] != "active" or not g["privileged"]:
            continue
        if (g["last_used_date"] is None
                or dates.days_between(g["last_used_date"], day) > threshold):
            out.add(g["grant_id"])
    return out


def _profile(ent):
    emps = ent["roster"]["employees"]
    grants = ent["iam"]["grants"]
    active = [g for g in grants if g["status"] == "active"]
    privileged = [g for g in active if g["privileged"]]
    per_system = {}
    for g in active:
        per_system[g["system"]] = per_system.get(g["system"], 0) + 1
    return {
        "snapshot": ent["policy"]["snapshot"],
        "employees_total": len(emps),
        "employees_active": sum(1 for e in emps if e["status"] == "active"),
        "grants_total": len(grants),
        "grants_active": len(active),
        "privileged_active": len(privileged),
        "privileged_share": "{0}/{1}".format(len(privileged), len(active)),
        "active_by_system": dict(sorted(per_system.items())),
        "tickets_total": len(ent["tickets"]["tickets"]),
        "deploys_total": len(ent["deploys"]["deploys"]),
    }


def compare_snapshots(prior, current, coming_due_days=30):
    """Census deltas between two exports of the same organization."""
    day_prior = prior["policy"]["snapshot"]
    day_current = current["policy"]["snapshot"]
    if day_prior >= day_current:
        raise ValueError("prior snapshot must predate current snapshot")
    window_days = dates.days_between(day_prior, day_current)

    prior_active = _active_grants(prior)
    current_active = _active_grants(current)

    new_ids = sorted(set(current_active) - set(prior_active))
    removed_ids = sorted(set(prior_active) - set(current_active))
    new_privileged = sorted(gid for gid in new_ids
                            if current_active[gid]["privileged"])

    dormant_prior = _dormant_privileged_ids(prior)
    dormant_current = _dormant_privileged_ids(current)
    newly_dormant = sorted((dormant_current - dormant_prior)
                           & set(current_active))

    terminations = [t for t in current["roster"]["terminations"]
                    if day_prior < t["termination_date"] <= day_current]

    cycle = current["policy"]["thresholds"]["recert_cycle_days"]
    lapsed, coming_due = [], []
    for gid, g in sorted(current_active.items()):
        cert = g["last_certified_date"]
        if cert is None:
            lapsed.append(gid)
            continue
        age = dates.days_between(cert, day_current)
        if age > cycle:
            lapsed.append(gid)
        elif age > cycle - coming_due_days:
            coming_due.append(gid)
    prior_lapsed = []
    for gid, g in sorted(_active_grants(prior).items()):
        cert = g["last_certified_date"]
        if cert is None or dates.days_between(cert, day_prior) > cycle:
            prior_lapsed.append(gid)

    prior_profile = _profile(prior)
    current_profile = _profile(current)
    deltas = {}
    for key in ("employees_total", "employees_active", "grants_total",
                "grants_active", "privileged_active", "tickets_total",
                "deploys_total"):
        deltas[key] = current_profile[key] - prior_profile[key]

    return {
        "window": {"from": day_prior, "to": day_current,
                   "days": window_days},
        "grants": {
            "new": new_ids,
            "new_n": len(new_ids),
            "new_privileged": new_privileged,
            "new_privileged_n": len(new_privileged),
            "removed_or_disabled": removed_ids,
            "removed_n": len(removed_ids),
        },
        "newly_dormant_privileged": {
            "ids": newly_dormant,
            "n": len(newly_dormant),
        },
        "terminations_in_window": terminations,
        "recertification": {
            "cycle_days": cycle,
            "lapsed_ids": lapsed,
            "lapsed_n": len(lapsed),
            "lapsed_prior_n": len(prior_lapsed),
            "coming_due_ids": coming_due,
            "coming_due_n": len(coming_due),
            "coming_due_within_days": coming_due_days,
        },
        "population_profile": {
            "prior": prior_profile,
            "current": current_profile,
            "delta": deltas,
        },
    }


# --------------------------------------------------------------------------
# lead aging across a pair of rule runs
# --------------------------------------------------------------------------

def _finding_key(finding):
    return (finding.rule_id, tuple(finding.record_ids), finding.subject)


def age_leads(prior_results, current_results, window_days):
    """Match finding identity across two rule runs of the same battery.

    Returns open leads labelled new/persisting (persisting leads carry
    min_age_days = window_days, a lower bound by construction) plus the
    leads present before and absent now (resolved).
    """
    prior_keys = {}
    for res in prior_results:
        for f in res.findings:
            prior_keys[_finding_key(f)] = f
    open_leads, resolved = [], []
    seen_current = set()
    for res in current_results:
        for f in res.findings:
            key = _finding_key(f)
            seen_current.add(key)
            persisting = key in prior_keys
            open_leads.append({
                "rule_id": f.rule_id,
                "subject": f.subject,
                "record_ids": list(f.record_ids),
                "status": "persisting" if persisting else "new",
                "min_age_days": window_days if persisting else 0,
                "rationale": f.rationale,
            })
    for key, f in sorted(prior_keys.items()):
        if key not in seen_current:
            resolved.append({
                "rule_id": f.rule_id,
                "subject": f.subject,
                "record_ids": list(f.record_ids),
                "status": "resolved",
            })
    counts = {
        "open": len(open_leads),
        "new": sum(1 for l in open_leads if l["status"] == "new"),
        "persisting": sum(1 for l in open_leads
                          if l["status"] == "persisting"),
        "resolved": len(resolved),
    }
    return {"note": AGING_NOTE, "window_days": window_days,
            "open_leads": open_leads, "resolved_leads": resolved,
            "counts": counts}
