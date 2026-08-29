"""Configuration-baseline export: what each system is actually set to.

Two registers, both observed at the snapshot:

- SETTINGS — one row per (system, setting) carrying the value the system
  is configured with. This is the shape a real baseline extract takes: a
  row per setting per system, compared line by line against the standard
  the organization states for itself. Ids are natural-key content hashes
  (system + setting), so a value that drifts keeps its id and nothing
  about a row's position encodes whether it was mutated (D-007).
- MFA ENROLMENTS — one row per account holding at least one active
  grant, recording whether that account is enrolled in multi-factor
  authentication and how. Privileged and ordinary accounts alike appear,
  because the criterion is about which of them the stated standard
  covers, not about which rows the export happens to contain.

Clean-data invariants (tested in tests/test_configs_consistency.py):
- every setting value MEETS the stated standard, asserted here at build
  time, so this module can only ever emit a compliant baseline;
- some values deliberately BEAT the standard — 16-character minimum
  passwords where 12 are required, a 10-minute idle timeout where 15 is
  the ceiling. These are the benign look-alikes of D-004: an equality
  comparison against the standard flags every one of them, a
  direction-aware comparison flags none, and a test proves exactly that;
- every privileged account is enrolled in MFA, while a documented share
  of ordinary accounts is not — the standard requires MFA for privileged
  access, so an unenrolled ordinary account is the second benign
  look-alike, and it sits INSIDE the enrolment rule's population rather
  than being filtered out of it (D-013's lesson).

The stated standard itself is enterprise data, not a constant inside a
rule (D-008): it ships on policy.json as `config_standard`, and the
baseline rules refuse when it is absent rather than assuming a default.
"""

from . import dates
from core.canonical import content_hash

PASSWORD_SETTINGS = ("password_history_depth", "password_max_age_days",
                     "password_min_length")
HARDENING_SETTINGS = ("account_lockout_threshold",
                      "session_idle_timeout_minutes")
MFA_SETTINGS = ("mfa_required_for_privileged",
                "mfa_required_for_remote_access")
SETTINGS = tuple(sorted(PASSWORD_SETTINGS + HARDENING_SETTINGS + MFA_SETTINGS))

# Values a compliant system may carry. Repeats weight the draw toward the
# standard itself; the remaining entries sit STRICTER than it, which is
# what gives the clean population its benign look-alikes (D-004).
CLEAN_VALUES = {
    "account_lockout_threshold": (5, 5, 3),
    "mfa_required_for_privileged": (True,),
    "mfa_required_for_remote_access": (True,),
    "password_history_depth": (12, 12, 24),
    "password_max_age_days": (90, 90, 60, 45),
    "password_min_length": (12, 12, 14, 16),
    "session_idle_timeout_minutes": (15, 15, 10),
}

MFA_METHODS = ("authenticator-app", "hardware-token")


def setting_id(system, setting):
    return "C-" + content_hash([system, setting])


def enrolment_id(system, account_id):
    return "M-" + content_hash([system, account_id])


def meets(spec, value):
    """Does `value` satisfy one stated-standard requirement?

    The requirement verbs are data, so a baseline can state a minimum, a
    maximum, or a required enablement without the comparison being
    hard-coded per setting. An unknown verb is not a quiet pass: callers
    check `known_requirement` first and refuse (D-008).
    """
    require, target = spec["require"], spec["value"]
    if require == "enabled":
        return value is target
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    if require == "at_least":
        return value >= target
    if require == "at_most":
        return value <= target
    return False


def known_requirement(spec):
    return spec.get("require") in ("at_least", "at_most", "enabled")


def build_configs(rng, cfg, standard, systems, grants):
    """Returns (settings sorted by config_id, enrolments sorted by id)."""
    settings = []
    for system in sorted(systems):
        for setting in SETTINGS:
            value = rng.choice(CLEAN_VALUES[setting])
            # The generator emits a clean population, always: a value that
            # missed the stated standard here would be an unplanted
            # condition, and the base rate of every planted property is
            # zero by construction (D-009).
            assert meets(standard[setting], value), (system, setting, value)
            settings.append({
                "config_id": setting_id(system, setting),
                "system": system,
                "setting": setting,
                "value": value,
                "observed_at": cfg.snapshot,
            })
    settings.sort(key=lambda s: s["config_id"])

    accounts = {}
    for g in grants:
        if g["status"] != "active":
            continue
        key = (g["system"], g["account_id"])
        rec = accounts.setdefault(key, {
            "system": g["system"],
            "account_id": g["account_id"],
            "account_name": g["account_name"],
            "account_type": g["account_type"],
            "user_id": g["user_id"],
            "privileged": False,
        })
        if g["privileged"]:
            rec["privileged"] = True

    ordered = [accounts[key] for key in sorted(accounts)]
    ordinary = [a for a in ordered if not a["privileged"]]
    n_enrolled = int(round(cfg.ordinary_mfa_enrolment_rate * len(ordinary)))
    enrolled_ordinary = {(a["system"], a["account_id"])
                         for a in rng.sample(ordinary, n_enrolled)}

    enrolments = []
    for a in ordered:
        key = (a["system"], a["account_id"])
        # Privileged access is what the stated standard covers, so every
        # privileged account is enrolled in clean data; ordinary accounts
        # are enrolled at the configured rate and the rest are the benign
        # look-alike a naive "everyone must be enrolled" rule punishes.
        enrolled = a["privileged"] or key in enrolled_ordinary
        row = {
            "enrolment_id": enrolment_id(a["system"], a["account_id"]),
            "system": a["system"],
            "account_id": a["account_id"],
            "account_name": a["account_name"],
            "account_type": a["account_type"],
            "user_id": a["user_id"],
            "privileged": a["privileged"],
            "enrolled": enrolled,
            "method": None,
            "enrolled_date": None,
        }
        if enrolled:
            row["method"] = rng.choice(MFA_METHODS)
            row["enrolled_date"] = dates.add_days(
                cfg.snapshot, -rng.randint(30, 700))
        enrolments.append(row)
    enrolments.sort(key=lambda r: r["enrolment_id"])
    return settings, enrolments
