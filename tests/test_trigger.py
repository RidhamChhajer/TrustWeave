from verification.trigger_engine import decide


def test_trigger_independent_drop_and_fail_closed():
    for score, delta, expected in [(90, -2, "CONTINUE"), (60, -2, "MONITOR"),
                                    (40, -2, "VERIFY"), (71, -22, "VERIFY_IMMEDIATELY"), (80, -10, "VERIFY_IMMEDIATELY")]:
        assert decide(score, delta, verified=True).action == expected
    assert decide(99, 0, verified=False).requires_verification
    assert decide(99, 0, verified=True, restricted=True).action == "RESTRICT"
