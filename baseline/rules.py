"""The four configuration-baseline rules.

Same contract as the access and change rules (D-011): declared census
populations, per-finding rationales specific enough to review without
re-deriving the analytic, three outcomes, and refusal — never a pass —
when the configuration these rules need is absent.

What is deliberately NOT hard-coded here is the standard itself. Each
rule reads `policy.config_standard` and compares the observed value using
the requirement verb that travels with it, so:

- a system configured STRICTER than the standard (a 16-character password
  minimum where 12 is required) meets it and raises nothing. That is the
  benign look-alike of D-004, and it sits inside these populations rather
  than beside them: an equality comparison would flag every one of them,
  which is the wrong implementation the clean population exists to punish;
- a setting the standard says nothing about yields a COVERAGE lead, not a
  pass and not a quiet skip — the same shape ACC-AUTH uses for a job
  function missing from the authorization matrix;
- an unknown requirement verb is a refusal (D-008: a configuration this
  code cannot interpret means refuse, not guess a direction).

CFG-ENRL reads the STATED STANDARD rather than the per-system MFA switch
when deciding whether enrolment is required. Reading the switch would
make one planted class silently mask another — a system whose MFA
requirement had drifted off would excuse every unenrolled account on it —
and the audit criterion is the standard the organization states, with the
system's own setting being evidence about that standard, not a substitute
for it. CFG-MFA owns the switch; CFG-ENRL owns the population.
"""

from core.rules import Finding, Rule
from enterprise.baseline import (HARDENING_SETTINGS, MFA_SETTINGS,
                                 PASSWORD_SETTINGS, known_requirement, meets)

_VERB_TEXT = {"at_least": "at least", "at_most": "at most",
              "enabled": "set to"}


def _stated(spec):
    """The stated requirement, rendered for a rationale or a workpaper."""
    return "{0} {1}".format(_VERB_TEXT.get(spec["require"], spec["require"]),
                            spec["value"])


class _SettingBaselineRule(Rule):
    """Shared body for the rules that compare recorded setting values
    against the stated standard. Subclasses name the settings they own;
    the population, the comparison, and the coverage lead are identical,
    so the three cannot drift apart in how they read the standard."""

    settings = ()

    def extra_applicable(self, view):
        if not view.has_export:
            return ("configuration baseline export is absent from this "
                    "enterprise — there is nothing to compare")
        if not view.standard:
            return ("the stated configuration standard is absent from the "
                    "policy artifact — refusing rather than grading this "
                    "population against a default it never stated")
        unknown = sorted(
            name for name in self.settings
            if view.requirement(name) is not None
            and not known_requirement(view.requirement(name)))
        if unknown:
            return ("the stated standard uses a requirement this procedure "
                    "cannot interpret for: {0} — refusing rather than "
                    "guessing a direction".format(", ".join(unknown)))
        return None

    def _thresholds_used(self, view):
        """The applied slice of the stated standard, rendered for the
        workpaper. Overridden because these rules are configured by the
        standard rather than by a scalar policy threshold; the base class
        still owns every outcome."""
        out = {}
        for name in self.settings:
            spec = getattr(view, "standard", {}).get(name)
            if spec and known_requirement(spec):
                out[name] = _stated(spec)
        return out

    def population(self, view):
        return view.settings_named(self.settings)

    def find(self, view, population):
        out = []
        for row in population:
            spec = view.requirement(row["setting"])
            if spec is None:
                out.append(Finding(
                    rule_id=self.rule_id,
                    record_ids=(row["config_id"],),
                    subject=row["system"],
                    rationale=("Setting {0} on {1} is recorded as {2}, but "
                               "the stated standard states no requirement "
                               "for it, so it cannot be evaluated (standard "
                               "coverage lead).".format(
                                   row["setting"], row["system"],
                                   row["value"])),
                    detail={"setting": row["setting"], "value": row["value"],
                            "standard_gap": True},
                ))
                continue
            if meets(spec, row["value"]):
                continue
            out.append(Finding(
                rule_id=self.rule_id,
                record_ids=(row["config_id"],),
                subject=row["system"],
                rationale=("Setting {0} on {1} is recorded as {2}; the "
                           "stated standard requires {3}.".format(
                               row["setting"], row["system"], row["value"],
                               _stated(spec))),
                detail={"setting": row["setting"], "value": row["value"],
                        "stated_requirement": _stated(spec),
                        "observed_at": row["observed_at"]},
            ))
        return out


class PasswordPolicyBaseline(_SettingBaselineRule):
    rule_id = "CFG-PWD"
    title = "Password policy against the stated standard"
    criterion = ("A recorded password-policy setting is a lead when its "
                 "observed value does not satisfy the stated standard's "
                 "requirement for that setting — a minimum length or "
                 "history depth, a maximum age — or when the standard "
                 "states no requirement for it.")
    population_desc = ("All recorded password-policy settings across every "
                       "system in the configuration baseline (complete "
                       "examination).")
    limitations = (
        "The baseline records the value each system reports; whether the "
        "setting is actually applied to every account on that system is "
        "not visible in this export.",
        "A value stricter than the stated standard satisfies it here. "
        "Whether an unusually strict setting is workable in practice is a "
        "matter for the reviewer, not a lead.",
        "Only settings present in the baseline are examined; a system that "
        "reports no password policy at all would be a completeness gap in "
        "the export rather than a lead here.",
    )
    settings = PASSWORD_SETTINGS
    designed_for = ("config.password_policy_drift",)


class HardeningBaseline(_SettingBaselineRule):
    rule_id = "CFG-HARD"
    title = "Lockout and session hardening against the stated standard"
    criterion = ("A recorded lockout or session setting is a lead when its "
                 "observed value exceeds the maximum the stated standard "
                 "allows, or when the standard states no requirement for "
                 "it.")
    population_desc = ("All recorded account-lockout and session-timeout "
                       "settings across every system in the configuration "
                       "baseline (complete examination).")
    limitations = (
        "Lockout thresholds and idle timeouts are read from the baseline "
        "export; enforcement behaviour is not tested here.",
        "A single ceiling is applied to every system. Where a system "
        "carries a documented tighter or looser requirement, that belongs "
        "in the stated standard, not in reviewer memory.",
    )
    settings = HARDENING_SETTINGS
    designed_for = ("config.hardening_drift",)


class MfaEnforcementBaseline(_SettingBaselineRule):
    rule_id = "CFG-MFA"
    title = "Multi-factor authentication enforcement settings"
    criterion = ("A recorded MFA enforcement setting is a lead when the "
                 "stated standard requires it to be enabled and the system "
                 "reports it as not enabled, or when the standard states "
                 "no requirement for it.")
    population_desc = ("All recorded MFA enforcement settings — privileged "
                       "access and remote access — across every system in "
                       "the configuration baseline (complete examination).")
    limitations = (
        "This procedure examines whether the requirement is switched on, "
        "not which factors are accepted or how they may be bypassed.",
        "Whether accounts are actually enrolled is a separate population "
        "and is examined by CFG-ENRL, not here.",
    )
    settings = MFA_SETTINGS
    designed_for = ("config.mfa_not_enforced",)


class PrivilegedMfaEnrolment(Rule):
    rule_id = "CFG-ENRL"
    title = "MFA enrolment of privileged accounts"
    criterion = ("An enrolment-register row is a lead when the account "
                 "holds active privileged access, the stated standard "
                 "requires multi-factor authentication for privileged "
                 "access, and the register records no enrolment for it.")
    population_desc = ("The complete MFA enrolment register: one row per "
                       "account holding at least one active grant, "
                       "privileged and ordinary alike (complete "
                       "examination).")
    limitations = (
        "Ordinary accounts appear in this population and are not leads: "
        "the stated standard requires MFA for privileged access, so an "
        "unenrolled ordinary account is outside the criterion, not an "
        "exception to it.",
        "Enrolment is evidenced by the register; whether the enrolled "
        "factor is ever challenged at sign-in is not visible here.",
        "Accounts absent from the register are not examined by this "
        "procedure — register completeness against the access export is "
        "not reconciled here.",
    )
    designed_for = ("config.mfa_enrolment_gap",)

    def extra_applicable(self, view):
        if not view.has_export:
            return ("configuration baseline export is absent from this "
                    "enterprise — there is nothing to compare")
        if not view.standard:
            return ("the stated configuration standard is absent from the "
                    "policy artifact — refusing rather than grading this "
                    "population against a default it never stated")
        spec = view.requirement("mfa_required_for_privileged")
        if spec is None:
            return ("the stated standard says nothing about MFA for "
                    "privileged access — there is no criterion to apply")
        if not known_requirement(spec):
            return ("the stated standard uses a requirement this procedure "
                    "cannot interpret for mfa_required_for_privileged — "
                    "refusing rather than guessing a direction")
        if not meets(spec, True):
            return ("the stated standard does not require MFA for "
                    "privileged access, so enrolment is not a criterion "
                    "this population can be measured against")
        return None

    def _thresholds_used(self, view):
        spec = getattr(view, "standard", {}).get("mfa_required_for_privileged")
        if spec and known_requirement(spec):
            return {"mfa_required_for_privileged": _stated(spec)}
        return {}

    def population(self, view):
        return list(view.enrolments)

    def find(self, view, population):
        out = []
        for row in population:
            if not row["privileged"] or row["enrolled"]:
                continue
            subject = (row["account_name"] or row["user_id"]
                       or row["account_id"])
            out.append(Finding(
                rule_id=self.rule_id,
                record_ids=(row["enrolment_id"],),
                subject=subject,
                rationale=("Account {0} on {1} holds privileged access and "
                           "the enrolment register records no "
                           "multi-factor enrolment for it; the stated "
                           "standard requires MFA for privileged "
                           "access.".format(subject, row["system"])),
                detail={"system": row["system"],
                        "account_id": row["account_id"],
                        "account_type": row["account_type"],
                        "user_id": row["user_id"],
                        "enrolled": False},
            ))
        return out


BASELINE_RULES = (
    PasswordPolicyBaseline(),
    HardeningBaseline(),
    MfaEnforcementBaseline(),
    PrivilegedMfaEnrolment(),
)
