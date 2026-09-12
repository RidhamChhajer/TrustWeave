"""MISMATCH closes a real TLS connection; MATCH on a fresh session restores service."""
import json
from experiments.normal import trace as warmup
from experiments.controller import sample
from experiments.runner import execute


def trace():
    return warmup() + [dict(kind="mismatch", raw=sample("sudden_drop"), anomaly=True, outcome="FAILURE"),
                       dict(kind="recovery", raw=sample(), anomaly=False, new_session=True, outcome="SUCCESS")]


if __name__ == "__main__":
    result = execute(trace(), "artifacts/failure.json")
    failed, recovered = result["rows"][-2:]
    assert failed["outcome"] == "FAILURE" and failed["restricted"]
    assert failed["blocked_send"] and not failed["delivered"]
    assert failed["key_action"] == "RESTRICT_SESSION"
    assert recovered["outcome"] == "SUCCESS" and recovered["delivered"] and not recovered["restricted"]
    assert recovered["relationship_id"] == failed["relationship_id"]
    assert recovered["resulting_session_id"] != failed["session_id"]
    events = [r["event_type"] for r in result["audit"] if r["session_id"] == failed["session_id"]]
    assert "VERIFICATION_FAILURE" in events and "SESSION_RESTRICTED" in events
    print("FAILURE_ACCEPTANCE_PASSED: send blocked after MISMATCH; fresh verified TLS session restored messaging")
