"""Explainable 0–100 consistency scores, independent of trust history."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Baselines:
    handshake_ms: float = 50.0
    rtt_ms: float = 50.0
    variation_ms: float = 10.0
    timing_ms: float = 100.0
    peer_ip: str | None = None


@dataclass(frozen=True)
class NormalizationPolicy:
    normal_ratio: float = 1.5
    severe_ratio: float = 4.0
    normal_establishments: float = 1.0
    severe_establishments: float = 8.0
    missing_score: float = 50.0

    def __post_init__(self):
        values = (self.normal_ratio, self.severe_ratio, self.normal_establishments,
                  self.severe_establishments, self.missing_score)
        if not all(math.isfinite(x) for x in values) or not (1 <= self.normal_ratio < self.severe_ratio):
            raise ValueError("invalid normalization ratios")
        if not 0 <= self.normal_establishments < self.severe_establishments or not 0 <= self.missing_score <= 100:
            raise ValueError("invalid normalization policy")


def ramp(value, normal, severe, policy):
    if value is None:
        return policy.missing_score
    if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid measurement")
    return max(0.0, min(100.0, 100 * (severe - value) / (severe - normal)))


def relative(value, baseline, policy):
    if not math.isfinite(baseline) or baseline <= 0:
        raise ValueError("baseline must be positive and finite")
    return ramp(None if value is None else value / baseline, policy.normal_ratio, policy.severe_ratio, policy)


def normalize_handshake_latency(value, baseline, policy=NormalizationPolicy()):
    return relative(value, baseline, policy)


def normalize_rtt(latest, variation, baselines=Baselines(), policy=NormalizationPolicy()):
    scores = [relative(latest, baselines.rtt_ms, policy)]
    if variation is not None:
        scores.append(relative(variation, baselines.variation_ms, policy))
    return min(scores)


def normalize_continuity(peer_ip, expected_ip, policy=NormalizationPolicy()):
    if peer_ip is None or expected_ip is None:
        return policy.missing_score
    return 100.0 if peer_ip == expected_ip else 0.0


def normalize_timing(interval, baseline, policy=NormalizationPolicy()):
    if interval is None:
        return policy.missing_score
    if interval < 0 or not math.isfinite(interval) or baseline <= 0:
        raise ValueError("invalid timing")
    # Both unusual bursts and unusual gaps are inconsistent with the baseline.
    ratio = max(interval / baseline, baseline / max(interval, 0.001))
    return ramp(ratio, policy.normal_ratio, policy.severe_ratio, policy)


def normalize_renegotiation(count, policy=NormalizationPolicy()):
    return ramp(count, policy.normal_establishments, policy.severe_establishments, policy)


def normalize_snapshot(raw, baselines=Baselines(), policy=NormalizationPolicy()):
    """Five fixed inputs; absent fields remain visible through the missing policy."""
    return {
        "handshake": normalize_handshake_latency(raw.get("handshake_ms"), baselines.handshake_ms, policy),
        "rtt": normalize_rtt(raw.get("rtt_ms"), raw.get("variation_ms"), baselines, policy),
        "continuity": normalize_continuity(raw.get("peer_ip"), baselines.peer_ip, policy),
        "timing": normalize_timing(raw.get("timing_ms"), baselines.timing_ms, policy),
        "renegotiation": normalize_renegotiation(raw.get("establishments"), policy),
    }
