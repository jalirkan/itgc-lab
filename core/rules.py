"""Rule framework shared by the access and change engines.

Framing (adopted in DECISIONS.md D-003/D-005; lab D-011/D-014, toolkit
D-031):

- Every rule is a COMPLETE EXAMINATION of its declared population — no
  sampling, so flag counts are census facts stated with their population
  size, never projections.
- Findings are LEADS for auditor follow-up, each carrying a per-finding
  rationale specific enough to review without re-deriving the analytic.
- Three outcomes: "pass" (ran, nothing noted), "exception" (ran, leads
  raised), "inconclusive" (the rule REFUSED to run — missing threshold,
  empty population, absent artifact — with the reason recorded). Refusal
  never renders as pass, and a missing configuration means refuse, not
  assume a default.
"""

from dataclasses import dataclass, field

from core.stats import EXCEPTION, INCONCLUSIVE, PASS


@dataclass(frozen=True)
class Finding:
    rule_id: str
    record_ids: tuple
    subject: str
    rationale: str
    detail: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "record_ids": list(self.record_ids),
            "subject": self.subject,
            "rationale": self.rationale,
            "detail": dict(self.detail),
        }


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    title: str
    outcome: str
    findings: tuple
    population_n: int
    population_desc: str
    criterion: str
    limitations: tuple
    thresholds_used: dict
    refusal_reason: str = None

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "outcome": self.outcome,
            "findings": [f.to_dict() for f in self.findings],
            "population_n": self.population_n,
            "population_desc": self.population_desc,
            "criterion": self.criterion,
            "limitations": list(self.limitations),
            "thresholds_used": dict(self.thresholds_used),
            "refusal_reason": self.refusal_reason,
        }


class Rule:
    """Subclasses set the class attributes and implement population() and
    find(). run() owns the outcome logic so no rule can invent a fourth
    outcome or turn a refusal into a pass."""

    rule_id = None
    title = None
    criterion = None
    population_desc = None
    limitations = ()
    required_thresholds = ()
    designed_for = ()          # planted violation classes this rule targets

    def extra_applicable(self, view):
        """Return a refusal reason string, or None. Override as needed."""
        return None

    def population(self, view):
        raise NotImplementedError

    def find(self, view, population):
        raise NotImplementedError

    def _thresholds_used(self, view):
        return {name: view.thresholds[name] for name in self.required_thresholds}

    def _refuse(self, reason, thresholds_used=None):
        return RuleResult(
            rule_id=self.rule_id, title=self.title, outcome=INCONCLUSIVE,
            findings=(), population_n=0,
            population_desc=self.population_desc, criterion=self.criterion,
            limitations=tuple(self.limitations),
            thresholds_used=thresholds_used or {},
            refusal_reason=reason,
        )

    def run(self, view):
        missing = [t for t in self.required_thresholds
                   if t not in view.thresholds]
        if missing:
            return self._refuse(
                "policy threshold(s) absent: {0} — refusing rather than "
                "assuming a default".format(", ".join(sorted(missing))))
        reason = self.extra_applicable(view)
        if reason:
            return self._refuse(reason, self._thresholds_used(view))
        pop = self.population(view)
        if not pop:
            return self._refuse(
                "population is empty: {0} — nothing was examined, which is "
                "not evidence the control operated".format(self.population_desc),
                self._thresholds_used(view))
        findings = tuple(self.find(view, pop))
        return RuleResult(
            rule_id=self.rule_id, title=self.title,
            outcome=EXCEPTION if findings else PASS,
            findings=findings, population_n=len(pop),
            population_desc=self.population_desc, criterion=self.criterion,
            limitations=tuple(self.limitations),
            thresholds_used=self._thresholds_used(view),
            refusal_reason=None,
        )


def run_rules(rules, view):
    return [rule.run(view) for rule in rules]
