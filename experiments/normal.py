"""Phase 18: stable context across twelve independently established sessions."""
from experiments.controller import sample
from experiments.runner import execute


def trace():
    return [dict(kind="normal", raw=sample(), anomaly=False, new_session=i > 0) for i in range(12)]


if __name__ == "__main__":
    result = execute(trace(), "artifacts/normal.json")
    rows = result["rows"]
    assert rows[0]["reason"] == "new_relationship"
    assert all(r["trigger_ns"] is None and r["delivered"] for r in rows[1:])
    assert rows[-1]["score"] > 95
    print("NORMAL_ACCEPTANCE_PASSED: one required bootstrap verification; zero unnecessary verifications")
