"""HR roster with joiner / mover / leaver / rehire lifecycle.

Employees carry a full `history` of events; flat convenience fields
(status, termination_date) describe the LATEST employment stint at the
snapshot. The export also includes a flat `terminations` list — the
period termination report an access review would actually join against —
and rehired employees appear in it deliberately: a rehire is the
documented benign look-alike for the terminated-but-active condition
(DECISIONS.md D-004; lab D-008). Correct logic must use the latest stint,
and Phase 1's rule is tested on exactly that trap.
"""

from . import dates
from .names import FIRST, LAST
from core.canonical import content_hash


def _employee_id(rng, taken, full_name, hire_date, seq):
    eid = "E-" + content_hash([full_name, hire_date, seq, rng.random()])
    while eid in taken:  # vanishing probability; loop for determinism anyway
        eid = "E-" + content_hash([eid])
    return eid


def _mk_employee(rng, taken, seq, department, function, hire_date):
    name = "{0} {1}".format(rng.choice(FIRST), rng.choice(LAST))
    eid = _employee_id(rng, taken, name, hire_date, seq)
    taken.add(eid)
    return {
        "employee_id": eid,
        "full_name": name,
        "hire_date": hire_date,
        "history": [
            {
                "date": hire_date,
                "event": "hire",
                "department": department,
                "job_function": function,
            }
        ],
    }


def _dept_of(org_data, function):
    for dept, spec in sorted(org_data["departments"].items()):
        if function in spec["functions"]:
            return dept
    raise ValueError("unknown function: " + function)


def _weighted_department(rng, org_data):
    depts = sorted(org_data["departments"].items())
    total = sum(spec["weight"] for _, spec in depts)
    pick = rng.uniform(0, total)
    acc = 0.0
    for dept, spec in depts:
        acc += spec["weight"]
        if pick <= acc:
            return dept, spec
    return depts[-1]


def segments(employee):
    """Employment stints derived from history.

    Returns a list of dicts {start, end (None if open), department,
    job_function}; a transfer closes one segment and opens the next, a
    termination closes, a rehire opens.
    """
    segs = []
    current = None
    for ev in employee["history"]:
        kind = ev["event"]
        if kind in ("hire", "rehire"):
            current = {
                "start": ev["date"],
                "end": None,
                "department": ev["department"],
                "job_function": ev["job_function"],
                "closed_by": None,
            }
            segs.append(current)
        elif kind == "transfer":
            current["end"] = ev["date"]
            current["closed_by"] = "transfer"
            current = {
                "start": ev["date"],
                "end": None,
                "department": ev["department"],
                "job_function": ev["job_function"],
                "closed_by": None,
            }
            segs.append(current)
        elif kind == "termination":
            current["end"] = ev["date"]
            current["closed_by"] = "termination"
            current = None
    return segs


def latest_stint(employee):
    return segments(employee)[-1]


def is_active_at(employee, iso_day):
    for seg in segments(employee):
        if seg["start"] <= iso_day and (seg["end"] is None or seg["end"] > iso_day):
            return True
    return False


def current_function(employee):
    """Function of the open stint, or None if terminated."""
    seg = latest_stint(employee)
    return None if seg["end"] is not None else seg["job_function"]


def build_roster(rng, cfg, org_data):
    """Returns (employees sorted by id, terminations list)."""
    window_start = dates.months_back(cfg.snapshot, cfg.months)
    taken = set()
    employees = []
    seq = 0

    def hire_pre_window():
        return dates.add_days(window_start, -rng.randint(30, 365 * 8))

    # Guaranteed functions: never terminated, hired before the window, so
    # grantor/approver pools exist across the whole period.
    guaranteed_ids = set()
    for function, count in sorted(org_data["guaranteed_functions"].items()):
        for _ in range(count):
            seq += 1
            emp = _mk_employee(
                rng, taken, seq, _dept_of(org_data, function), function,
                hire_pre_window(),
            )
            guaranteed_ids.add(emp["employee_id"])
            employees.append(emp)

    # Base fill to configured start headcount.
    while len(employees) < cfg.employees:
        seq += 1
        dept, spec = _weighted_department(rng, org_data)
        function = rng.choice(sorted(spec["functions"]))
        employees.append(_mk_employee(rng, taken, seq, dept, function, hire_pre_window()))

    # Joiners during the window (hired at least 15 days before snapshot).
    joiner_span = dates.days_between(window_start, cfg.snapshot) - 15
    for _ in range(round(cfg.employees * cfg.joiner_rate)):
        seq += 1
        dept, spec = _weighted_department(rng, org_data)
        function = rng.choice(sorted(spec["functions"]))
        hire = dates.add_days(window_start, rng.randint(0, joiner_span))
        employees.append(_mk_employee(rng, taken, seq, dept, function, hire))

    employees.sort(key=lambda e: e["employee_id"])

    # Leavers: from non-guaranteed employees hired before the window.
    base_pool = [
        e for e in employees
        if e["employee_id"] not in guaranteed_ids and e["hire_date"] < window_start
    ]
    n_leavers = round(cfg.employees * cfg.leaver_rate)
    leavers = rng.sample(base_pool, n_leavers)
    leavers.sort(key=lambda e: e["employee_id"])
    term_low = dates.add_days(window_start, 30)
    term_span = dates.days_between(term_low, dates.add_days(cfg.snapshot, -10))
    for emp in leavers:
        term = dates.add_days(term_low, rng.randint(0, term_span))
        seg = latest_stint(emp)
        emp["history"].append({
            "date": term,
            "event": "termination",
            "department": seg["department"],
            "job_function": seg["job_function"],
        })

    # Rehires: earliest-terminated leavers with room for a 30-40 day gap
    # come back in the same function. They stay in the terminations list.
    eligible = [
        e for e in leavers
        if dates.days_between(latest_stint(e)["end"], cfg.snapshot) >= 75
    ]
    eligible.sort(key=lambda e: (latest_stint(e)["end"], e["employee_id"]))
    for emp in eligible[: cfg.rehires]:
        seg = latest_stint(emp)
        back = dates.add_days(seg["end"], rng.randint(30, 40))
        emp["history"].append({
            "date": back,
            "event": "rehire",
            "department": seg["department"],
            "job_function": seg["job_function"],
        })

    # Movers: active, non-guaranteed, not leavers; one transfer mid-window.
    leaver_ids = {e["employee_id"] for e in leavers}
    mover_pool = [
        e for e in employees
        if e["employee_id"] not in guaranteed_ids
        and e["employee_id"] not in leaver_ids
        and e["hire_date"] < window_start
    ]
    movers = rng.sample(mover_pool, round(cfg.employees * cfg.mover_rate))
    movers.sort(key=lambda e: e["employee_id"])
    move_low = dates.add_days(window_start, 20)
    move_span = dates.days_between(move_low, dates.add_days(cfg.snapshot, -25))
    all_functions = sorted(
        f for _, spec in sorted(org_data["departments"].items())
        for f in spec["functions"]
    )
    for emp in movers:
        seg = latest_stint(emp)
        choices = [f for f in all_functions if f != seg["job_function"]]
        new_function = rng.choice(choices)
        emp["history"].append({
            "date": dates.add_days(move_low, rng.randint(0, move_span)),
            "event": "transfer",
            "department": _dept_of(org_data, new_function),
            "job_function": new_function,
        })

    # Finalize convenience fields + flat termination report.
    terminations = []
    for emp in employees:
        emp["history"].sort(key=lambda ev: (ev["date"], ev["event"]))
        seg = latest_stint(emp)
        emp["department"] = seg["department"]
        emp["job_function"] = seg["job_function"]
        emp["status"] = "terminated" if seg["end"] is not None else "active"
        emp["termination_date"] = seg["end"] if seg["closed_by"] == "termination" else None
        for ev in emp["history"]:
            if ev["event"] == "termination":
                terminations.append({
                    "employee_id": emp["employee_id"],
                    "termination_date": ev["date"],
                    "department": ev["department"],
                    "job_function": ev["job_function"],
                })
    terminations.sort(key=lambda t: (t["termination_date"], t["employee_id"]))
    return employees, terminations
