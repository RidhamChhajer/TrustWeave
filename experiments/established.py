"""Compare cold/established windows without setting trust or verification flags."""
from experiments.normal import trace as warmup
from experiments.controller import sample
from experiments.runner import execute


def trace():
    return warmup() + [dict(kind="established", raw=sample(), anomaly=False, new_session=True)
                       for _ in range(8)] + [dict(kind="sudden_drop", raw=sample("sudden_drop"), anomaly=True)]


if __name__ == "__main__":
    rows = execute(trace(), "artifacts/established.json")["rows"]
    cold, established = rows[:8], rows[12:20]
    cold_count = sum(r["trigger_ns"] is not None for r in cold)
    established_count = sum(r["trigger_ns"] is not None for r in established)
    assert cold_count == 1 and established_count == 0
    assert all(r["before"] > 95 and r["delivered"] for r in established)
    assert rows[-1]["action"] == "VERIFY_IMMEDIATELY" and rows[-1]["score"] > 50
    print(f"ESTABLISHED_ACCEPTANCE_PASSED: cold={cold_count}/8, established={established_count}/8 verifications; sudden-drop protection retained")
