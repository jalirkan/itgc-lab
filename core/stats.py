"""Measurements, Wilson intervals, and three-outcome decisions.

Re-implements the uncertainty discipline this repo adopted in DECISIONS.md
D-005 (per toolkit D-008/D-011/D-012 and lab D-015), with no cross-repo
imports:

- A proportion cannot exist without its interval, method, confidence, and
  n. `Measurement.proportion()` is the only sanctioned constructor and
  `render()` the only sanctioned display; both always carry n.
- Wilson score intervals, because audit rates cluster at 0 and 1 where the
  normal approximation collapses to zero width. n=0 renders "not tested"
  with interval [0, 1] — never "0%".
- `decide()` compares the INTERVAL to the threshold: pass only when the
  whole interval sits on the acceptable side, exception only when it sits
  entirely on the other, inconclusive when it straddles. `min_sample`
  gates only the pass — real exceptions in a small sample still count.
- A zero-tolerance threshold (0.0 when lower is better, 1.0 when higher
  is better) switches to attribute sampling: any exception is an
  exception; a clean sample passes once n meets the minimum, with the
  interval reported alongside.

Exact census counts are NOT Measurements: 12 flags in 341 grants is a fact
about this population, not an estimate (lab's exact-counts entry, toolkit
D-031). Intervals attach where a number is an inference — report-card
rates across seeds, drift comparisons — and that is what this module is
for.
"""

from dataclasses import dataclass
from statistics import NormalDist

LOWER_IS_BETTER = "lower_is_better"
HIGHER_IS_BETTER = "higher_is_better"

PASS, EXCEPTION, INCONCLUSIVE = "pass", "exception", "inconclusive"

DEFAULT_MIN_SAMPLE = 20


class StatsError(ValueError):
    pass


def z_value(confidence: float) -> float:
    if not 0.5 < confidence < 1.0:
        raise StatsError("confidence must be in (0.5, 1.0)")
    return NormalDist().inv_cdf((1.0 + confidence) / 2.0)


def wilson_interval(k: int, n: int, confidence: float = 0.95):
    """Wilson score interval for k successes in n trials.

    Boundary counts pin their exact bound: k=0 -> lower is exactly 0.0,
    k=n -> upper is exactly 1.0 (no float dust). n=0 -> (0.0, 1.0).
    """
    if n < 0 or k < 0 or k > n:
        raise StatsError("need 0 <= k <= n")
    if n == 0:
        return (0.0, 1.0)
    z = z_value(confidence)
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    half = (z / denom) * ((p * (1.0 - p) / n + z2 / (4.0 * n * n)) ** 0.5)
    lo = 0.0 if k == 0 else max(0.0, center - half)
    hi = 1.0 if k == n else min(1.0, center + half)
    return (lo, hi)


@dataclass(frozen=True)
class Measurement:
    kind: str
    label: str
    numerator: int
    n: int
    value: float          # None-like sentinel not allowed; use is_informative
    interval: tuple
    method: str
    confidence: float
    direction: str

    def __post_init__(self):
        if self.kind != "proportion":
            raise StatsError("only proportion measurements exist here")
        if self.method != "wilson":
            raise StatsError("proportions require the wilson method")
        if not 0.5 < self.confidence < 1.0:
            raise StatsError("confidence must be in (0.5, 1.0)")
        if self.interval is None or len(self.interval) != 2:
            raise StatsError("a rate without an interval is a bug (D-005)")
        if self.n < 0 or self.numerator < 0 or self.numerator > max(self.n, 0):
            raise StatsError("need 0 <= numerator <= n")
        if self.direction not in (LOWER_IS_BETTER, HIGHER_IS_BETTER):
            raise StatsError("direction must be declared on the measurement")

    @classmethod
    def proportion(cls, label, numerator, n, *, direction,
                   confidence=0.95):
        """The only sanctioned constructor for a rate."""
        interval = wilson_interval(numerator, n, confidence)
        value = (numerator / n) if n > 0 else 0.0
        return cls(kind="proportion", label=label, numerator=numerator,
                   n=n, value=value, interval=interval, method="wilson",
                   confidence=confidence, direction=direction)

    @property
    def is_informative(self):
        return self.n > 0

    def render(self) -> str:
        """The only sanctioned display; always includes n (toolkit D-008)."""
        conf = int(round(self.confidence * 100))
        lo, hi = self.interval
        if not self.is_informative:
            return ("{0}: not tested (n=0; {1}% interval 0.0%-100.0%)"
                    .format(self.label, conf))
        return ("{0}: {1}/{2} = {3:.1f}% ({4}% Wilson {5:.1f}%-{6:.1f}%, n={2})"
                .format(self.label, self.numerator, self.n,
                        self.value * 100.0, conf, lo * 100.0, hi * 100.0))

    def to_dict(self):
        return {
            "kind": self.kind, "label": self.label,
            "numerator": self.numerator, "n": self.n, "value": self.value,
            "interval": [self.interval[0], self.interval[1]],
            "method": self.method, "confidence": self.confidence,
            "direction": self.direction, "rendered": self.render(),
        }


@dataclass(frozen=True)
class Decision:
    outcome: str
    reason: str

    def to_dict(self):
        return {"outcome": self.outcome, "reason": self.reason}


def decide(measurement: Measurement, threshold: float,
           min_sample: int = DEFAULT_MIN_SAMPLE) -> Decision:
    """Three outcomes, decided against the interval (toolkit D-011/D-012)."""
    m = measurement
    if not m.is_informative:
        return Decision(INCONCLUSIVE, "not tested: n=0")
    lo, hi = m.interval
    lower_better = m.direction == LOWER_IS_BETTER

    zero_tolerance = (threshold == 0.0 and lower_better) or \
                     (threshold == 1.0 and not lower_better)
    if zero_tolerance:
        bad = m.numerator if lower_better else m.n - m.numerator
        if bad > 0:
            return Decision(EXCEPTION,
                            "zero-tolerance criterion: {0} exception(s) in "
                            "n={1}".format(bad, m.n))
        if m.n < min_sample:
            return Decision(INCONCLUSIVE,
                            "no exceptions in n={0}, below the minimum "
                            "sample of {1} for a clean conclusion"
                            .format(m.n, min_sample))
        return Decision(PASS,
                        "no exceptions noted in n={0} (interval reported "
                        "alongside)".format(m.n))

    if lower_better:
        acceptable, unacceptable = hi <= threshold, lo > threshold
    else:
        acceptable, unacceptable = lo >= threshold, hi < threshold
    if acceptable:
        if m.n < min_sample:
            return Decision(INCONCLUSIVE,
                            "interval clears the threshold but n={0} is "
                            "below the minimum sample of {1}"
                            .format(m.n, min_sample))
        return Decision(PASS, "entire interval on the acceptable side of "
                              "{0:g}".format(threshold))
    if unacceptable:
        return Decision(EXCEPTION, "entire interval on the unacceptable "
                                   "side of {0:g}".format(threshold))
    return Decision(INCONCLUSIVE,
                    "interval straddles {0:g}: this sample cannot answer "
                    "the question".format(threshold))
