"""Deterministic weighted EMA; never accepts plaintext."""

from dataclasses import dataclass
import math
from trust.anomaly import trust_delta

SIGNALS = ("handshake", "rtt", "continuity", "timing", "renegotiation")


@dataclass(frozen=True)
class TrustPolicy:
    alpha: float = 0.3
    initial_trust: float = 45.0
    weights: tuple[float, ...] = (0.2, 0.2, 0.2, 0.2, 0.2)
    verified_floor: float = 75.0

    def __post_init__(self):
        if not 0 < self.alpha <= 1 or not 0 <= self.initial_trust <= 100:
            raise ValueError("invalid EMA policy")
        if not 0 <= self.verified_floor <= 100:
            raise ValueError("invalid verified trust floor")
        if len(self.weights) != 5 or any(not math.isfinite(w) or w < 0 for w in self.weights):
            raise ValueError("invalid weights")
        if not math.isclose(sum(self.weights), 1.0):
            raise ValueError("weights must sum to one")


@dataclass(frozen=True)
class Assessment:
    previous: float
    current_score: float
    score: float

    @property
    def delta(self):
        return trust_delta(self.score, self.previous)


class TrustEngine:
    def __init__(self, policy=TrustPolicy(), initial=None):
        self.policy = policy
        self.score = policy.initial_trust if initial is None else initial
        if not math.isfinite(self.score) or not 0 <= self.score <= 100:
            raise ValueError("invalid initial trust")

    def assess(self, scores):
        if set(scores) != set(SIGNALS) or any(type(v) not in (float, int) or not math.isfinite(v) or not 0 <= v <= 100 for v in scores.values()):
            raise ValueError("expected five normalized scores")
        current = sum(w * scores[name] for name, w in zip(SIGNALS, self.policy.weights))
        previous = self.score
        self.score = self.policy.alpha * current + (1 - self.policy.alpha) * previous
        return Assessment(previous, current, self.score)
