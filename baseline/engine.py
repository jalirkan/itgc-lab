"""Config-baseline engine: shared view over an enterprise + rule runner.

The view carries the two things a baseline rule reconciles — the observed
configuration registers and the STATED standard they are checked against
— and nothing else. The standard is read from the population's own policy
artifact (D-008): a rule that cannot find it refuses, so a baseline is
never graded against a default this organization never stated.
"""

from core.rules import run_rules


class BaselineView:
    """Read-only view over the configuration baseline and its standard."""

    def __init__(self, ent):
        self.ent = ent
        self.snapshot = ent["policy"]["snapshot"]
        self.thresholds = ent["policy"].get("thresholds", {})
        self.standard = ent["policy"].get("config_standard") or {}
        configs = ent.get("configs") or {}
        self.has_export = "configs" in ent
        self.settings = configs.get("settings", [])
        self.enrolments = configs.get("mfa_enrolments", [])

    def requirement(self, setting):
        """The stated requirement for one setting, or None if unstated."""
        return self.standard.get(setting)

    def settings_named(self, names):
        wanted = set(names)
        return [s for s in self.settings if s["setting"] in wanted]


def run_baseline_review(ent):
    """Run every baseline rule; returns a list of RuleResult in rule order."""
    from baseline.rules import BASELINE_RULES
    return run_rules(BASELINE_RULES, BaselineView(ent))
