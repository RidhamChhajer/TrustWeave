import pytest

from trust.normalization import Baselines, normalize_snapshot, normalize_handshake_latency


def test_normalization_boundaries_and_missing():
    assert [normalize_handshake_latency(x, 50) for x in (50, 100, 200, None)] == [100, 80, 0, 50]
    baseline = Baselines(peer_ip="127.0.0.1")
    good = {"handshake_ms": 50, "rtt_ms": 50, "variation_ms": 5, "peer_ip": "127.0.0.1",
            "timing_ms": 100, "establishments": 1}
    assert set(normalize_snapshot(good, baseline).values()) == {100}
    assert set(normalize_snapshot({}, baseline).values()) == {50}
    assert normalize_snapshot({**good, "peer_ip": "127.0.0.2", "timing_ms": 1}, baseline)["timing"] == 0
    with pytest.raises(ValueError):
        normalize_handshake_latency(float("nan"), 50)
