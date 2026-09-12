from experiments.evaluation import summarize


def test_episode_and_session_denominators():
    rows = [dict(tick=i, anomaly=i in (1, 2), session_id=str(i), trigger_ns=3_000_000 if i==2 else None,
                 injection_ns=i*1_000_000, reason="low_trust" if i==2 else "trusted",
                 before=90, score=60, after=75, verification_ms=1 if i==2 else None,
                 key_action="REESTABLISH_KEY" if i==2 else "KEEP_CURRENT_KEY") for i in range(4)]
    summary = summarize(dict(rows=rows, audit=[dict(event_type="SESSION_STARTED", session_id=str(i)) for i in range(5)]))
    assert summary["verifications_per_tls_session"] == 0.2
    assert summary["controlled_episode_detection_rate"] == 1
    assert summary["episode_trigger_delay_observations"] == [1]
    assert summary["episode_trigger_latency_ms"] == [2]
    assert summary["false_verifications_per_normal_session"] == 0
