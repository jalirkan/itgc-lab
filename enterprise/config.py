"""Generator configuration and policy constants.

The policy thresholds are emitted as enterprise data (policy.json) rather
than hard-coded into rules: a rule reads the enterprise's own policy and
refuses to run without the threshold it needs (DECISIONS.md D-008, per lab
D-011 / toolkit D-020).
"""

from dataclasses import dataclass, asdict

GENERATOR_VERSION = "0.1.0"


@dataclass(frozen=True)
class GenConfig:
    seed: str = "itgc-001"
    snapshot: str = "2026-06-30"     # as-of date for every export
    months: int = 18                 # window length ending at snapshot
    employees: int = 150             # headcount at window start
    joiner_rate: float = 0.18        # share of start headcount hired in window
    leaver_rate: float = 0.10        # share terminated in window
    mover_rate: float = 0.08         # share transferred in window
    # Benign look-alikes, mandatory in clean data (DECISIONS.md D-004):
    rehires: int = 2                 # terminated then rehired inside window
    sanctioned_exceptions: int = 3   # off-matrix grants with register entries
    proper_emergencies: int = 3      # weekend emergencies with post-hoc review
    open_recent_tickets: int = 4     # approved, not yet deployed, not stale
    tickets_per_month: int = 12
    service_accounts_per_system: int = 2
    shared_accounts_per_system: int = 1

    def to_dict(self):
        return asdict(self)


THRESHOLDS = {
    "termination_grace_days": 3,     # account disablement SLA after termination
    "transfer_cleanup_days": 14,     # old-function grant removal SLA after move
    "dormant_privileged_days": 90,   # privileged last-use staleness bar
    "recert_cycle_days": 365,        # access recertification cycle
    "emergency_review_days": 5,      # post-hoc review SLA for emergency changes
    "stale_ticket_days": 30,         # approved-but-undeployed review age
}
