from dataclasses import dataclass
from datetime import datetime, timezone
import math


@dataclass(frozen=True)
class TriggerPolicy:
    high: float = 80
    low: float = 50
    sudden_drop: float = 10

    def __post_init__(self):
        if not 0 <= self.low < self.high <= 100 or not 0 < self.sudden_drop <= 100:
            raise ValueError("invalid trigger thresholds")


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    score: float
    delta: float
    threshold: float | None
    timestamp: str

    @property
    def requires_verification(self):
        return self.action in {"VERIFY", "VERIFY_IMMEDIATELY"}


def decide(score, delta, *, verified, restricted=False, policy=TriggerPolicy()):
    if not math.isfinite(score) or not 0 <= score <= 100 or not math.isfinite(delta) or not -100 <= delta <= 100:
        raise ValueError("invalid trust state")
    if restricted:
        action, reason, threshold = "RESTRICT", "verification_failed", None
    elif delta <= -policy.sudden_drop:
        action, reason, threshold = "VERIFY_IMMEDIATELY", "sudden_drop", -policy.sudden_drop
    elif not verified:
        action, reason, threshold = "VERIFY", "new_relationship", None
    elif score < policy.low:
        action, reason, threshold = "VERIFY", "low_trust", policy.low
    elif score >= policy.high:
        action, reason, threshold = "CONTINUE", "trusted", policy.high
    else:
        action, reason, threshold = "MONITOR", "normal", policy.low
    return Decision(action, reason, score, delta, threshold, datetime.now(timezone.utc).isoformat())
