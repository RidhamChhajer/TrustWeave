"""Combined final demonstration: real TLS, simulated context and OOB answers."""
from experiments.controller import sample
from experiments.failure import trace as failure_trace
from experiments.runner import execute


def trace():
    return failure_trace() + [dict(kind="relearning", raw=sample(), anomaly=False) for _ in range(6)] + [
        dict(kind="repeat_anomaly", raw=sample("sudden_drop"), anomaly=True, outcome="SUCCESS")
    ] + [dict(kind="restored", raw=sample(), anomaly=False) for _ in range(6)]


def validate(result):
    rows = result["rows"]
    checks = {
        "conservative_bootstrap": rows[0]["before"] == 45 and rows[0]["reason"] == "new_relationship",
        "initial_match": rows[0]["outcome"] == "SUCCESS" and rows[0]["delivered"],
        "relationship_learning": rows[11]["after"] > 95,
        "independent_drop_trigger": rows[12]["score"] > 50 and rows[12]["action"] == "VERIFY_IMMEDIATELY",
        "mismatch_blocks_send": rows[12]["outcome"] == "FAILURE" and rows[12]["blocked_send"] and not rows[12]["delivered"],
        "fresh_recovery": rows[13]["outcome"] == "SUCCESS" and rows[13]["delivered"] and rows[13]["resulting_session_id"] != rows[12]["session_id"],
        "repeat_anomaly_match": rows[20]["action"] == "VERIFY_IMMEDIATELY" and rows[20]["outcome"] == "SUCCESS" and rows[20]["score"] > 50,
        "repeat_rekey": rows[20]["key_action"] == "REESTABLISH_KEY" and rows[20]["session_id"] != rows[20]["resulting_session_id"],
        "restored_messaging": all(r["delivered"] and not r["restricted"] for r in rows[21:]) and rows[-1]["after"] > 95,
        "same_relationship": len({r["relationship_id"] for r in rows}) == 1,
    }
    if not all(checks.values()):
        raise RuntimeError("Final demo acceptance failed: " + ", ".join(k for k,v in checks.items() if not v))
    return checks


def main():
    result = execute(trace(), "artifacts/final-demo.json")
    checks = validate(result)
    for name in checks:
        print("PASS " + name)
    print("FINAL_DEMO_SUCCESS: real mutual TLS; simulated metadata/OOB; no message or secret output")


if __name__ == "__main__":
    main()
