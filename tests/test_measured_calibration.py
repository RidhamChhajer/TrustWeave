from experiments.measured_calibration import evaluate
from trust.trust_engine import TrustPolicy


def test_first_false_prompt_stops_replay_before_later_anomaly():
    bad = {"handshake_ms": 1000, "rtt_ms": 1000, "variation_ms": 1000,
           "timing_ms": 10000, "peer_ip": "192.0.2.1", "establishments": 8}
    result = evaluate([{"induced": True, "rows": [
        {"raw": bad, "induced": False}, {"raw": bad, "induced": True}]}], TrustPolicy())
    assert result["sessions_with_false_prompt"] == 1
    assert result["sessions_detecting_induced_delay"] == 0


def test_empty_evaluation_has_explicit_zero_denominators():
    result = evaluate([], TrustPolicy())
    assert all(value == 0 for value in result.values())
