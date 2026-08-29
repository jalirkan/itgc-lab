"""Planted-violation injector. The manifest is the ONLY ground truth.

Discipline adopted from the siblings (DECISIONS.md D-002/D-007/D-009/D-010):

- Own RNG stream ("{seed}/violations"): planting can never reshuffle the
  clean population, and clean generation is byte-identical whether or not
  an injection ever happens (lab D-010). inject() works on a deep copy.
- No positional artifacts (lab D-009): mutations preserve natural-key ids;
  additions derive ids exactly the way the generator does, so planted
  records are format-identical and interleave under canonical sorting.
  Nothing marks a planted record except the manifest.
- Single-property plants: each plant introduces the property its class
  names and avoids collateral properties (e.g. a reactivated terminated
  account gets a fresh certification so it cannot double as a recert
  lapse). Where overlap is intrinsic — an added SoD role is usually also
  off-matrix — the manifest note says so.
- Benign look-alikes are protected: sanctioned-exception grants are never
  mutated, emergency/stale plants are additions so the documented benign
  populations survive injection intact, and the configuration classes
  never touch a setting configured stricter than the standard or an
  ordinary account's enrolment row.
"""

import copy

from . import catalogs, dates, roster
from .baseline import (HARDENING_SETTINGS, MFA_SETTINGS, PASSWORD_SETTINGS,
                       meets)
from .iam import _account_id, _grant_id, _mk_grant  # same id derivations
from .tickets import _deploy_id, _mk_ticket, _ticket_id, _weighted_system, in_freeze
from core import rng as rngmod
from core.canonical import SCHEMA_VERSION, content_hash

INJECTOR_VERSION = "0.1.0"


class InjectionError(ValueError):
    pass


ACCESS_CLASSES = (
    "access.terminated_active",
    "access.orphan_account",
    "access.dormant_privileged",
    "access.role_mismatch",
    "access.sod_conflict",
    "access.service_account_no_owner",
    "access.recert_lapsed",
)
CHANGE_CLASSES = (
    "change.missing_approval",
    "change.self_approval",
    "change.emergency_no_review",
    "change.deploy_without_ticket",
    "change.freeze_violation",
    "change.stale_ticket",
)
CONFIG_CLASSES = (
    "config.password_policy_drift",
    "config.hardening_drift",
    "config.mfa_not_enforced",
    "config.mfa_enrolment_gap",
)
CLASSES = ACCESS_CLASSES + CHANGE_CLASSES + CONFIG_CLASSES


def _protected_grant_ids(ent):
    """Grants backing the sanctioned-exception benign look-alike."""
    keys = {(x["user_id"], x["system"], x["role"])
            for x in ent["exceptions"]["exceptions"]}
    return {g["grant_id"] for g in ent["iam"]["grants"]
            if (g["user_id"], g["system"], g["role"]) in keys}


def _employees_by_id(ent):
    return {e["employee_id"]: e for e in ent["roster"]["employees"]}


def _rehired_ids(ent):
    """Employees carrying a rehire event — the D-004 benign look-alike."""
    return {e["employee_id"] for e in ent["roster"]["employees"]
            if any(ev["event"] == "rehire" for ev in e["history"])}


def _sysadmin_ids(ent):
    return sorted(
        e["employee_id"] for e in ent["roster"]["employees"]
        if roster.current_function(e) == "system-administrator")


def _pick(rng, pool, cls, needed_msg="eligible targets"):
    if not pool:
        raise InjectionError(
            "{0}: no {1} remain in the population".format(cls, needed_msg))
    return rng.choice(pool)


class _Ctx:
    def __init__(self, ent, rng):
        self.ent = ent
        self.rng = rng
        self.snapshot = ent["policy"]["snapshot"]
        self.window_start = ent["policy"]["window_start"]
        self.thresholds = ent["policy"]["thresholds"]
        self.freezes = ent["policy"]["freeze_windows"]
        self.used_grants = set(_protected_grant_ids(ent))
        self.used_tickets = set()
        self.used_users = set()
        self.used_configs = set()
        self.used_enrolments = set()
        self.standard = ent["policy"]["config_standard"]
        self.rehired = _rehired_ids(ent)
        self.emps = _employees_by_id(ent)
        self.matrix = catalogs.authorization_matrix()
        self.sod_pairs = catalogs.sod_matrix()["pairs"]
        # Indexes: pool construction is O(population) with these, and the
        # single-pass build keeps selection order deterministic.
        self._grants_by_user = {}
        for g in self.grants:
            if g["user_id"] is not None:
                self._grants_by_user.setdefault(g["user_id"], []).append(g)
        self._deploy_by_ticket = {d["ticket_id"]: d for d in self.deploys}

    @property
    def grants(self):
        return self.ent["iam"]["grants"]

    @property
    def tickets(self):
        return self.ent["tickets"]["tickets"]

    @property
    def deploys(self):
        return self.ent["deploys"]["deploys"]

    @property
    def settings(self):
        return self.ent["configs"]["settings"]

    @property
    def enrolments(self):
        return self.ent["configs"]["mfa_enrolments"]

    def register_grant(self, g):
        if g["user_id"] is not None:
            self._grants_by_user.setdefault(g["user_id"], []).append(g)

    def register_deploy(self, d):
        self._deploy_by_ticket[d["ticket_id"]] = d

    def user_grants(self, eid):
        return self._grants_by_user.get(eid, [])

    def deploy_of(self, ticket_id):
        return self._deploy_by_ticket.get(ticket_id)

    def held_roles(self, eid):
        return {"{0}:{1}".format(g["system"], g["role"])
                for g in self.user_grants(eid) if g["status"] == "active"}

    def mutable_deployed_tickets(self):
        return [t for t in self.tickets
                if t["ticket_id"] not in self.used_tickets
                and t["change_type"] in ("standard", "normal")
                and t["status"] == "closed"
                and self.deploy_of(t["ticket_id"]) is not None]


# --- access plants -------------------------------------------------------

def _plant_terminated_active(ctx):
    grace = ctx.thresholds["termination_grace_days"]
    pool = []
    for eid in sorted(ctx.emps):
        if eid in ctx.used_users:
            continue
        emp = ctx.emps[eid]
        seg = roster.latest_stint(emp)
        if seg["closed_by"] != "termination":
            continue
        if dates.days_between(seg["end"], ctx.snapshot) <= grace + 5:
            continue
        cands = [g for g in ctx.user_grants(eid)
                 if g["status"] == "disabled"
                 and not g["privileged"] and g["grant_id"] not in ctx.used_grants]
        if cands:
            pool.append((eid, sorted(c["grant_id"] for c in cands)[0]))
    eid, gid = _pick(ctx.rng, pool, "access.terminated_active",
                     "terminated employees with disabled grants")
    g = next(x for x in ctx.grants if x["grant_id"] == gid)
    g["status"] = "active"
    g["disabled_date"] = None
    # Fresh certification so the plant cannot double as a recert lapse.
    cert = dates.add_days(ctx.snapshot, -ctx.rng.randint(30, 200))
    g["last_certified_date"] = max(g["granted_date"], cert)
    ctx.used_grants.add(gid)
    ctx.used_users.add(eid)
    term = roster.latest_stint(ctx.emps[eid])["end"]
    return {
        "refs": {"grant_ids": [gid], "user_id": eid},
        "note": "Planted: account remains active {0} days after the "
                "{1} termination (grace {2} days).".format(
                    dates.days_between(term, ctx.snapshot), term, grace),
    }


def _plant_orphan_account(ctx):
    known = set(ctx.emps)
    fake = "E-" + content_hash(["orphan", ctx.rng.random()])
    while fake in known:
        fake = "E-" + content_hash([fake])
    system = "crm"
    granted = dates.add_days(
        ctx.window_start,
        ctx.rng.randint(30, dates.days_between(ctx.window_start, ctx.snapshot) - 40))
    g = _mk_grant(system, _account_id(system, fake), "crm-user", granted,
                  ctx.rng.choice(_sysadmin_ids(ctx.ent)),
                  account_type="user", user_id=fake, seq=0)
    g["last_used_date"] = dates.add_days(ctx.snapshot, -ctx.rng.randint(1, 45))
    # Certified within the cycle: the only planted property is the missing
    # roster identity, not a recert lapse.
    g["last_certified_date"] = max(
        granted, dates.add_days(ctx.snapshot, -ctx.rng.randint(30, 200)))
    ctx.grants.append(g)
    ctx.grants.sort(key=lambda x: x["grant_id"])
    ctx.register_grant(g)
    ctx.used_grants.add(g["grant_id"])
    return {
        "refs": {"grant_ids": [g["grant_id"]], "user_id": fake},
        "note": "Planted: active account whose user id appears nowhere in "
                "the HR roster (never employed).",
    }


def _plant_dormant_privileged(ctx):
    days = ctx.thresholds["dormant_privileged_days"]
    stale_by = days + ctx.rng.randint(30, 120)
    pool = [g["grant_id"] for g in ctx.grants
            if g["privileged"] and g["status"] == "active"
            and g["grant_id"] not in ctx.used_grants
            and (g["user_id"] is None or g["user_id"] not in ctx.used_users)
            and dates.days_between(g["granted_date"], ctx.snapshot) > stale_by + 10]
    gid = _pick(ctx.rng, sorted(pool), "access.dormant_privileged",
                "long-standing active privileged grants")
    g = next(x for x in ctx.grants if x["grant_id"] == gid)
    g["last_used_date"] = dates.add_days(ctx.snapshot, -stale_by)
    ctx.used_grants.add(gid)
    if g["user_id"]:
        ctx.used_users.add(g["user_id"])
    return {
        "refs": {"grant_ids": [gid], "user_id": g["user_id"]},
        "note": "Planted: privileged role unused for {0} days against a "
                "{1}-day dormancy threshold.".format(stale_by, days),
    }


def _mismatch_candidates(ctx, eid):
    emp = ctx.emps[eid]
    function = roster.current_function(emp)
    if function is None:
        return []
    allowed = set(ctx.matrix[function])
    held = ctx.held_roles(eid)
    toxic_with_held = set()
    for p in ctx.sod_pairs:
        if p["a"] in held:
            toxic_with_held.add(p["b"])
        if p["b"] in held:
            toxic_with_held.add(p["a"])
    out = []
    for sr in catalogs.all_system_roles():
        system, role = sr.split(":")
        if sr in allowed or sr in held or sr in toxic_with_held:
            continue
        if catalogs.is_privileged(system, role):
            continue
        out.append(sr)
    return out


def _add_role_grant(ctx, eid, sys_role, seq):
    system, role = sys_role.split(":")
    granted = dates.add_days(ctx.snapshot, -ctx.rng.randint(20, 150))
    g = _mk_grant(system, _account_id(system, eid), role, granted,
                  ctx.rng.choice(_sysadmin_ids(ctx.ent)),
                  account_type="user", user_id=eid, seq=seq)
    g["last_used_date"] = dates.add_days(ctx.snapshot, -ctx.rng.randint(1, 30))
    g["last_certified_date"] = granted
    ctx.grants.append(g)
    ctx.grants.sort(key=lambda x: x["grant_id"])
    ctx.register_grant(g)
    ctx.used_grants.add(g["grant_id"])
    ctx.used_users.add(eid)
    return g


def _plant_role_mismatch(ctx):
    exception_users = {x["user_id"] for x in ctx.ent["exceptions"]["exceptions"]}
    pool = []
    for eid in sorted(ctx.emps):
        if eid in ctx.used_users or eid in exception_users:
            continue
        if ctx.emps[eid]["status"] != "active":
            continue
        cands = _mismatch_candidates(ctx, eid)
        if cands:
            pool.append((eid, cands))
    eid, cands = _pick(ctx.rng, pool, "access.role_mismatch",
                       "active employees with assignable off-matrix roles")
    sys_role = ctx.rng.choice(cands)
    g = _add_role_grant(ctx, eid, sys_role, seq=70)
    function = roster.current_function(ctx.emps[eid])
    return {
        "refs": {"grant_ids": [g["grant_id"]], "user_id": eid},
        "note": "Planted: role {0} sits outside the authorization matrix "
                "for job function {1}, with no recorded exception.".format(
                    sys_role, function),
    }


def _plant_sod_conflict(ctx):
    exception_users = {x["user_id"] for x in ctx.ent["exceptions"]["exceptions"]}
    pool = []
    for eid in sorted(ctx.emps):
        if eid in ctx.used_users or eid in exception_users:
            continue
        if ctx.emps[eid]["status"] != "active":
            continue
        held = ctx.held_roles(eid)
        for p in ctx.sod_pairs:
            if p["a"] in held and p["b"] not in held:
                pool.append((eid, p["b"], p))
            elif p["b"] in held and p["a"] not in held:
                pool.append((eid, p["a"], p))
    eid, missing, pair = _pick(ctx.rng, pool, "access.sod_conflict",
                               "employees holding one side of a toxic pair")
    held_half = pair["a"] if missing == pair["b"] else pair["b"]
    g = _add_role_grant(ctx, eid, missing, seq=80)
    # The violation is the PAIR: the manifest names every constituent
    # grant, so flagging the pre-existing half is correct detection, not a
    # false positive (per lab D-019's pair-originals rule).
    counterpart_ids = sorted(
        x["grant_id"] for x in ctx.user_grants(eid)
        if x["status"] == "active"
        and "{0}:{1}".format(x["system"], x["role"]) == held_half)
    return {
        "refs": {"grant_ids": sorted([g["grant_id"]] + counterpart_ids),
                 "added_grant_id": g["grant_id"], "user_id": eid},
        "note": "Planted: added grant completes the toxic combination "
                "{0} + {1} ({2}) Constituent ids include the pre-existing "
                "half; the added role is typically also outside the "
                "holder's matrix. Designed detector: the SoD rule.".format(
                    pair["a"], pair["b"], pair["conflict"]),
    }


def _plant_service_account_no_owner(ctx):
    pool = sorted(g["grant_id"] for g in ctx.grants
                  if g["account_type"] in ("service", "shared")
                  and g["owner_id"] is not None
                  and g["grant_id"] not in ctx.used_grants)
    gid = _pick(ctx.rng, pool, "access.service_account_no_owner",
                "owned service or shared accounts")
    g = next(x for x in ctx.grants if x["grant_id"] == gid)
    g["owner_id"] = None
    ctx.used_grants.add(gid)
    return {
        "refs": {"grant_ids": [gid], "account_id": g["account_id"]},
        "note": "Planted: {0} account {1} carries no recorded owner."
                .format(g["account_type"], g["account_name"]),
    }


def _plant_recert_lapsed(ctx):
    cycle = ctx.thresholds["recert_cycle_days"]
    overdue = cycle + ctx.rng.randint(30, 180)
    pool = sorted(
        g["grant_id"] for g in ctx.grants
        if g["status"] == "active" and g["account_type"] == "user"
        and g["grant_id"] not in ctx.used_grants
        and g["user_id"] not in ctx.used_users
        and dates.days_between(g["granted_date"], ctx.snapshot) > overdue + 10)
    gid = _pick(ctx.rng, pool, "access.recert_lapsed",
                "long-standing active grants")
    g = next(x for x in ctx.grants if x["grant_id"] == gid)
    g["last_certified_date"] = dates.add_days(ctx.snapshot, -overdue)
    ctx.used_grants.add(gid)
    ctx.used_users.add(g["user_id"])
    return {
        "refs": {"grant_ids": [gid], "user_id": g["user_id"]},
        "note": "Planted: last recertification {0} days before the snapshot "
                "against a {1}-day cycle.".format(overdue, cycle),
    }


# --- change plants -------------------------------------------------------

def _plant_missing_approval(ctx):
    pool = sorted(t["ticket_id"] for t in ctx.mutable_deployed_tickets())
    tid = _pick(ctx.rng, pool, "change.missing_approval", "deployed tickets")
    t = next(x for x in ctx.tickets if x["ticket_id"] == tid)
    t["approver_id"] = None
    t["approved_at"] = None
    ctx.used_tickets.add(tid)
    return {
        "refs": {"ticket_id": tid,
                 "deploy_id": ctx.deploy_of(tid)["deploy_id"]},
        "note": "Planted: change was deployed with no approval recorded "
                "on the ticket.",
    }


def _plant_self_approval(ctx):
    pool = sorted(t["ticket_id"] for t in ctx.mutable_deployed_tickets())
    tid = _pick(ctx.rng, pool, "change.self_approval", "deployed tickets")
    t = next(x for x in ctx.tickets if x["ticket_id"] == tid)
    t["approver_id"] = t["developer_id"]
    ctx.used_tickets.add(tid)
    return {
        "refs": {"ticket_id": tid,
                 "deploy_id": ctx.deploy_of(tid)["deploy_id"]},
        "note": "Planted: the developer of the change is recorded as its "
                "approver (segregation-of-duties condition).",
    }


def _emergency_days_taken(ctx):
    return {ctx.deploy_of(t["ticket_id"])["deployed_at"]
            for t in ctx.tickets
            if t["change_type"] == "emergency"
            and ctx.deploy_of(t["ticket_id"]) is not None}


def _developer_ids(ctx):
    return sorted(
        e["employee_id"] for e in ctx.ent["roster"]["employees"]
        if roster.current_function(e) in ("software-developer", "devops-engineer"))


def _plant_emergency_no_review(ctx):
    taken = _emergency_days_taken(ctx)
    days = [s for s in dates.saturdays(dates.add_days(ctx.window_start, 7),
                                       dates.add_days(ctx.snapshot, -10))
            if not in_freeze(s, ctx.freezes) and s not in taken]
    day = _pick(ctx.rng, days, "change.emergency_no_review",
                "free weekend days")
    system = _weighted_system(ctx.rng)
    developer = ctx.rng.choice(_developer_ids(ctx))
    approvers = sorted(
        e["employee_id"] for e in ctx.ent["roster"]["employees"]
        if roster.current_function(e) in
        ("controller", "qa-analyst", "system-administrator", "security-analyst")
        and e["employee_id"] != developer)
    tid = _ticket_id(system, day, developer, "planted-emergency")
    t = _mk_ticket(tid, system, "emergency", "closed", developer, developer,
                   ctx.rng.choice(approvers), day, dates.add_days(day, 1))
    ctx.tickets.append(t)
    ctx.tickets.sort(key=lambda x: x["ticket_id"])
    d = {"deploy_id": _deploy_id(tid, system), "system": system,
         "ticket_id": tid, "deployed_by": developer, "deployed_at": day}
    ctx.deploys.append(d)
    ctx.deploys.sort(key=lambda x: x["deploy_id"])
    ctx.register_deploy(d)
    ctx.used_tickets.add(tid)
    return {
        "refs": {"ticket_id": tid, "deploy_id": d["deploy_id"]},
        "note": "Planted: emergency change deployed {0} with no post-hoc "
                "review recorded within the {1}-day window.".format(
                    day, ctx.thresholds["emergency_review_days"]),
    }


def _plant_deploy_without_ticket(ctx):
    known = {t["ticket_id"] for t in ctx.tickets}
    fake = "CHG-" + content_hash(["ghost", ctx.rng.random()])
    while fake in known:
        fake = "CHG-" + content_hash([fake])
    system = _weighted_system(ctx.rng)
    span = dates.days_between(ctx.window_start, ctx.snapshot)
    day = dates.next_business_day(
        dates.add_days(ctx.window_start, ctx.rng.randint(20, span - 20)))
    while in_freeze(day, ctx.freezes):
        day = dates.next_business_day(dates.add_days(day, 1))
    d = {"deploy_id": _deploy_id(fake, system), "system": system,
         "ticket_id": fake, "deployed_by": ctx.rng.choice(_developer_ids(ctx)),
         "deployed_at": day}
    ctx.deploys.append(d)
    ctx.deploys.sort(key=lambda x: x["deploy_id"])
    ctx.register_deploy(d)
    return {
        "refs": {"deploy_id": d["deploy_id"], "ticket_id": fake},
        "note": "Planted: deploy-log entry references a change ticket that "
                "does not exist in the ticket system.",
    }


def _plant_freeze_violation(ctx):
    pairs = []
    for t in ctx.mutable_deployed_tickets():
        for f in ctx.freezes:
            if f["end"] <= ctx.snapshot and t["approved_at"] < f["start"]:
                pairs.append((t["ticket_id"], f["start"]))
                break
    tid, f_start = _pick(ctx.rng, sorted(pairs), "change.freeze_violation",
                         "deployed tickets approved before a freeze")
    d = ctx.deploy_of(tid)
    d["deployed_at"] = dates.add_days(f_start, ctx.rng.randint(0, 2))
    ctx.used_tickets.add(tid)
    return {
        "refs": {"ticket_id": tid, "deploy_id": d["deploy_id"]},
        "note": "Planted: deployment date falls inside the change freeze "
                "beginning {0}.".format(f_start),
    }


def _plant_stale_ticket(ctx):
    stale = ctx.thresholds["stale_ticket_days"]
    age = stale + ctx.rng.randint(10, 60)
    created = dates.add_days(ctx.snapshot, -age)
    system = _weighted_system(ctx.rng)
    developer = ctx.rng.choice(_developer_ids(ctx))
    approvers = sorted(
        e["employee_id"] for e in ctx.ent["roster"]["employees"]
        if roster.current_function(e) in
        ("controller", "qa-analyst", "system-administrator", "security-analyst")
        and e["employee_id"] != developer)
    tid = _ticket_id(system, created, developer, "planted-stale")
    t = _mk_ticket(tid, system, "normal", "approved", developer, developer,
                   ctx.rng.choice(approvers), created,
                   dates.add_days(created, ctx.rng.randint(1, 3)))
    ctx.tickets.append(t)
    ctx.tickets.sort(key=lambda x: x["ticket_id"])
    ctx.used_tickets.add(tid)
    return {
        "refs": {"ticket_id": tid},
        "note": "Planted: ticket approved {0} days before the snapshot and "
                "never deployed (stale threshold {1} days). Review lead, "
                "not a control failure by itself.".format(age, stale),
    }


# --- config-baseline plants ----------------------------------------------
#
# All four are MUTATIONS of rows the clean generator already emitted, so
# every planted record keeps its natural-key id and nothing about a row's
# position in the canonical ordering betrays that it was touched (D-007).
# Each introduces exactly one property: a drifted setting value does not
# also change what the standard states, and an enrolment gap does not
# touch the account's grants. The MFA register is built from the CLEAN
# population and injection deliberately does not backfill it, so accounts
# that planted grants create have no register row; no rule reconciles
# register completeness against the access export, so that leaves no
# signal for any rule to pick up (CFG-ENRL's limitations say so).

_DRIFT_VALUES = {
    "account_lockout_threshold": (10, 25, 50),
    "password_history_depth": (0, 3, 5),
    "password_max_age_days": (180, 270, 365),
    "password_min_length": (6, 8, 10),
    "session_idle_timeout_minutes": (60, 240, 480),
}


def _drift_a_setting(cls, names, needed_msg):
    """Build a planter that moves one recorded setting to a value the
    stated standard rejects. The two numeric-drift classes differ only in
    which settings they own, so they share this body: a divergence in how
    they read the standard would be a divergence in ground truth."""

    def plant(ctx):
        pool = sorted(s["config_id"] for s in ctx.settings
                      if s["setting"] in names
                      and s["config_id"] not in ctx.used_configs)
        cid = _pick(ctx.rng, pool, cls, needed_msg)
        row = next(s for s in ctx.settings if s["config_id"] == cid)
        spec = ctx.standard[row["setting"]]
        drifted = ctx.rng.choice(_DRIFT_VALUES[row["setting"]])
        if meets(spec, drifted):
            # A "planted" value that still satisfies the standard would
            # be an entry the manifest claims and the data does not
            # exhibit — louder to fail here than to grade it later.
            raise InjectionError(
                "{0}: drifted value {1} for {2} still meets the stated "
                "standard".format(cls, drifted, row["setting"]))
        was = row["value"]
        row["value"] = drifted
        ctx.used_configs.add(cid)
        return {
            "refs": {"config_ids": [cid], "system": row["system"],
                     "setting": row["setting"]},
            "note": "Planted: {0} on {1} recorded as {2} (was {3}), "
                    "against a stated standard of {4} {5}.".format(
                        row["setting"], row["system"], drifted, was,
                        spec["require"], spec["value"]),
        }

    return plant


_plant_password_policy_drift = _drift_a_setting(
    "config.password_policy_drift", PASSWORD_SETTINGS,
    "password-policy settings")
_plant_hardening_drift = _drift_a_setting(
    "config.hardening_drift", HARDENING_SETTINGS,
    "lockout or session settings")


def _plant_mfa_not_enforced(ctx):
    pool = sorted(s["config_id"] for s in ctx.settings
                  if s["setting"] in MFA_SETTINGS
                  and s["value"] is True
                  and s["config_id"] not in ctx.used_configs)
    cid = _pick(ctx.rng, pool, "config.mfa_not_enforced",
                "enabled MFA enforcement settings")
    row = next(s for s in ctx.settings if s["config_id"] == cid)
    row["value"] = False
    ctx.used_configs.add(cid)
    return {
        "refs": {"config_ids": [cid], "system": row["system"],
                 "setting": row["setting"]},
        "note": "Planted: {0} on {1} recorded as not enabled, against a "
                "stated standard that requires it. The enrolment "
                "population is unaffected: CFG-ENRL reads the stated "
                "standard, not this switch.".format(
                    row["setting"], row["system"]),
    }


def _plant_mfa_enrolment_gap(ctx):
    # Rehires are excluded structurally rather than by luck: a benign
    # look-alike that a plant has been laid on top of is no longer clean
    # evidence about anything (D-004).
    pool = sorted(e["enrolment_id"] for e in ctx.enrolments
                  if e["privileged"] and e["enrolled"]
                  and e["enrolment_id"] not in ctx.used_enrolments
                  and e["user_id"] not in ctx.used_users
                  and e["user_id"] not in ctx.rehired)
    eid = _pick(ctx.rng, pool, "config.mfa_enrolment_gap",
                "enrolled privileged accounts")
    row = next(e for e in ctx.enrolments if e["enrolment_id"] == eid)
    row["enrolled"] = False
    row["method"] = None
    row["enrolled_date"] = None
    ctx.used_enrolments.add(eid)
    if row["user_id"]:
        ctx.used_users.add(row["user_id"])
    subject = row["account_name"] or row["user_id"]
    return {
        "refs": {"enrolment_ids": [eid], "system": row["system"],
                 "account_id": row["account_id"],
                 "user_id": row["user_id"]},
        "note": "Planted: privileged account {0} on {1} carries no "
                "multi-factor enrolment. The account's grants are "
                "untouched; only the enrolment register changes.".format(
                    subject, row["system"]),
    }


_PLANTERS = {
    "access.terminated_active": _plant_terminated_active,
    "access.orphan_account": _plant_orphan_account,
    "access.dormant_privileged": _plant_dormant_privileged,
    "access.role_mismatch": _plant_role_mismatch,
    "access.sod_conflict": _plant_sod_conflict,
    "access.service_account_no_owner": _plant_service_account_no_owner,
    "access.recert_lapsed": _plant_recert_lapsed,
    "change.missing_approval": _plant_missing_approval,
    "change.self_approval": _plant_self_approval,
    "change.emergency_no_review": _plant_emergency_no_review,
    "change.deploy_without_ticket": _plant_deploy_without_ticket,
    "change.freeze_violation": _plant_freeze_violation,
    "change.stale_ticket": _plant_stale_ticket,
    "config.password_policy_drift": _plant_password_policy_drift,
    "config.hardening_drift": _plant_hardening_drift,
    "config.mfa_not_enforced": _plant_mfa_not_enforced,
    "config.mfa_enrolment_gap": _plant_mfa_enrolment_gap,
}


def inject(enterprise, plan, seed):
    """Apply `plan` ({class: count}) to a deep copy of `enterprise`.

    Returns (planted_enterprise, manifest). The input is never mutated.
    """
    unknown = sorted(set(plan) - set(_PLANTERS))
    if unknown:
        raise InjectionError("unknown violation class(es): " + ", ".join(unknown))
    planted = copy.deepcopy(enterprise)
    rng = rngmod.stream(seed, "violations")
    ctx = _Ctx(planted, rng)
    violations = []
    for cls in sorted(plan):
        count = plan[cls]
        if count < 0:
            raise InjectionError("negative count for " + cls)
        for i in range(count):
            entry = _PLANTERS[cls](ctx)
            entry["violation_id"] = "V-" + content_hash([cls, i, entry["refs"]])
            entry["class"] = cls
            violations.append(entry)
    violations.sort(key=lambda v: v["violation_id"])
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "manifest",
        "injector_version": INJECTOR_VERSION,
        "seed": seed,
        "enterprise_seed": enterprise["policy"]["seed"],
        "plan": {k: plan[k] for k in sorted(plan)},
        "violations": violations,
    }
    planted["manifest"] = manifest
    return planted, manifest
