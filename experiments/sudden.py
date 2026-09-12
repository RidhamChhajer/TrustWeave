"""Phase 20: independent delta trigger above the absolute low-trust threshold."""
from experiments.controller import sample
from experiments.normal import trace as warmup
from experiments.runner import execute


def trace():
    return warmup() + [dict(kind="sudden_drop", raw=sample("sudden_drop"), anomaly=True)] + [
        dict(kind="recovery", raw=sample(), anomaly=False) for _ in range(6)]


def validate(result):
    anomaly = result["rows"][12]
    assert anomaly["score"] > result["policies"]["trigger"]["low"]
    assert anomaly["delta"] <= -result["policies"]["trigger"]["sudden_drop"]
    assert anomaly["action"] == "VERIFY_IMMEDIATELY" and anomaly["reason"] == "sudden_drop"
    assert anomaly["outcome"] == "SUCCESS" and anomaly["delivered"]
    assert anomaly["session_id"] != anomaly["resulting_session_id"]
    assert result["rows"][-1]["after"] > anomaly["after"]
    return anomaly


if __name__ == "__main__":
    anomaly = validate(execute(trace(), "artifacts/sudden.json"))
    print(f"SUDDEN_ACCEPTANCE_PASSED: score={anomaly['score']:.4f} delta={anomaly['delta']:.4f}; immediate verification above 50")
