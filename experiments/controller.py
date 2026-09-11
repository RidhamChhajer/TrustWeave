"""Deterministic metadata perturbations, independent of cryptographic transport."""

NORMAL = dict(handshake_ms=50.0, rtt_ms=50.0, variation_ms=10.0,
              timing_ms=100.0, peer_ip="127.0.0.1", establishments=1.0)
KINDS = ("normal", "latency", "variance", "continuity", "timing", "renegotiation", "gradual", "sudden_drop")


def sample(kind="normal", severity=1.0):
    if kind not in KINDS or not 0 <= severity <= 1:
        raise ValueError("invalid controlled scenario")
    raw = dict(NORMAL)
    factor = 1 + 4 * severity
    if kind in {"latency", "gradual", "sudden_drop"}:
        raw["handshake_ms"] *= factor
        raw["rtt_ms"] *= factor
    if kind in {"variance", "gradual", "sudden_drop"}:
        raw["variation_ms"] *= factor
    if kind in {"continuity", "sudden_drop"} and severity:
        raw["peer_ip"] = "192.0.2.1"  # documentation address, never contacted
    if kind in {"timing", "gradual", "sudden_drop"}:
        raw["timing_ms"] *= factor
    if kind in {"renegotiation", "gradual", "sudden_drop"}:
        raw["establishments"] += 7 * severity
    return raw
