import asyncio
from experiments.controller import KINDS, sample
from experiments.runner import run_trace


def test_controlled_inputs_and_live_transport():
    assert all(sample(kind) == sample(kind) for kind in KINDS)
    trace = [dict(kind="normal", raw=sample(), anomaly=False)]
    result = asyncio.run(run_trace(trace))
    row = result["rows"][0]
    assert row["reason"] == "new_relationship" and row["delivered"]
    assert row["session_id"] != row["resulting_session_id"]
    assert result["simulated_metadata"] and result["simulated_oob"]
