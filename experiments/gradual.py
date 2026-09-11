"""Phase 19: predeclared small severity increments, without score manipulation."""
from experiments.controller import sample
from experiments.normal import trace as warmup
from experiments.runner import execute


def trace():
    return warmup() + [dict(kind="gradual", raw=sample("gradual", i / 30), anomaly=True,
                            new_session=True) for i in range(1, 31)]


if __name__ == "__main__":
    result = execute(trace(), "artifacts/gradual.json")
    degraded = result["rows"][12:]
    first = next(r for r in degraded if r["trigger_ns"] is not None)
    assert first["reason"] == "low_trust" and first["score"] < 50
    assert all(r["delta"] > -10 for r in degraded[:first["tick"] - 12 + 1])
    print(f"GRADUAL_ACCEPTANCE_PASSED: first trigger tick={first['tick']} score={first['score']:.4f} delta={first['delta']:.4f}")
